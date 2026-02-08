#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统健康监控模块
"""

import asyncio
import concurrent.futures
import psutil
import aiohttp
from loguru import logger
from datetime import datetime
from openai import AsyncOpenAI
from typing import Dict, Optional, TYPE_CHECKING

from .config_manager import ConfigManager

if TYPE_CHECKING:
    from ..core.database import DatabaseManager
    from ..core.data_repository import DataRepository


class HealthStatus:
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResult:
    """健康检查结果"""
    def __init__(self, name: str, status: str, message: str = "", details: Optional[Dict] = None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }

    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


class HealthMonitor:
    """系统健康监控器"""

    MIN_CHECK_INTERVAL = 30  # Minimum seconds between health checks

    def __init__(self, config_path: str = "config/config.yaml", db_manager: Optional['DatabaseManager'] = None, data_repo: Optional['DataRepository'] = None):
        self.config_path = config_path
        self.db_manager = db_manager
        self.data_repo = data_repo
        self._owns_db_manager = False
        self._last_check_time = 0
        self._cached_result = None

    async def check_database(self) -> HealthCheckResult:
        """检查数据库连接"""
        try:
            if not self.db_manager or not self.data_repo:
                from ..core.database import DatabaseManager
                from ..core.data_repository import DataRepository
                from .config_manager import ConfigManager
                import os
                config_manager = ConfigManager(self.config_path)
                db_path = config_manager.get("database.path", "data/trending.db")
                db_path = os.path.normpath(db_path)
                if '..' in db_path:
                    raise ValueError(f"Invalid database path (directory traversal detected): {db_path}")
                self.db_manager = DatabaseManager(db_path=db_path)
                self.data_repo = DataRepository(self.db_manager)
                self._owns_db_manager = True
                logger.warning("HealthMonitor created its own DatabaseManager - consider injecting dependencies")

            stats = self.data_repo.get_repository_stats()

            if stats['total_repositories'] >= 0:
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection OK",
                    details=stats
                )
            else:
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database returned invalid stats"
                )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}"
            )

    async def check_scraper(self) -> HealthCheckResult:
        """检查爬虫服务（测试 GitHub 可达性）"""
        try:
            url = "https://github.com/trending"
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return HealthCheckResult(
                            name="scraper",
                            status=HealthStatus.HEALTHY,
                            message="GitHub trending page accessible",
                            details={"url": url, "status_code": response.status}
                        )
                    else:
                        return HealthCheckResult(
                            name="scraper",
                            status=HealthStatus.DEGRADED,
                            message=f"GitHub returned status {response.status}",
                            details={"url": url, "status_code": response.status}
                        )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                name="scraper",
                status=HealthStatus.UNHEALTHY,
                message="GitHub trending page timeout"
            )
        except Exception as e:
            logger.error(f"Scraper health check failed: {e}")
            return HealthCheckResult(
                name="scraper",
                status=HealthStatus.UNHEALTHY,
                message=f"Scraper check failed: {str(e)}"
            )

    async def check_ai_models(self) -> HealthCheckResult:
        """检查 AI 模型可用性"""
        try:
            config_manager = ConfigManager.get_instance(self.config_path)
            config = config_manager.get_all()

            ai_config = config.get('ai_models', {})
            enabled_models = ai_config.get('enabled', [])

            model_status = {}
            all_healthy = True

            for model_name in enabled_models:
                if model_name in ['deepseek', 'nvidia']:
                    model_config = ai_config.get(model_name, {})
                    api_key = model_config.get('api_key', '')
                    base_url = model_config.get('base_url', '')

                    if api_key and base_url:
                        client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=10.0)
                        try:
                            models = await client.models.list()
                            if models.data:
                                model_status[model_name] = "healthy"
                            else:
                                model_status[model_name] = "no_models_available"
                                all_healthy = False
                        except Exception as e:
                            logger.warning(f"AI model {model_name} check failed: {e}")
                            model_status[model_name] = f"unhealthy: {str(e)[:50]}"
                            all_healthy = False
                        finally:
                            await client.close()
                    else:
                        model_status[model_name] = "missing_config"
                        all_healthy = False

            if all_healthy:
                return HealthCheckResult(
                    name="ai_models",
                    status=HealthStatus.HEALTHY,
                    message="All AI models accessible",
                    details={"models": model_status}
                )
            elif any("healthy" in status for status in model_status.values()):
                return HealthCheckResult(
                    name="ai_models",
                    status=HealthStatus.DEGRADED,
                    message="Some AI models unavailable",
                    details={"models": model_status}
                )
            else:
                return HealthCheckResult(
                    name="ai_models",
                    status=HealthStatus.UNHEALTHY,
                    message="All AI models unavailable",
                    details={"models": model_status}
                )

        except Exception as e:
            logger.error(f"AI models health check failed: {e}")
            return HealthCheckResult(
                name="ai_models",
                status=HealthStatus.UNHEALTHY,
                message=f"AI models check failed: {str(e)}"
            )

    async def check_email_service(self) -> HealthCheckResult:
        """检查邮件服务（使用线程池避免阻塞）"""
        try:
            config_manager = ConfigManager.get_instance(self.config_path)
            email_config = config_manager.get_email_config()

            smtp_server = email_config.get('smtp_server', '')
            smtp_port = email_config.get('smtp_port', 465)
            sender = email_config.get('sender', '')
            password = email_config.get('password', '')
            use_ssl = email_config.get('use_ssl', True)

            if not all([smtp_server, sender, password]):
                return HealthCheckResult(
                    name="email_service",
                    status=HealthStatus.UNHEALTHY,
                    message="Email configuration incomplete"
                )

            def sync_smtp_check():
                import smtplib
                if use_ssl:
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
                else:
                    server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.login(sender, password)
                server.quit()
                return True

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, sync_smtp_check)

            return HealthCheckResult(
                name="email_service",
                status=HealthStatus.HEALTHY,
                message="Email service accessible",
                details={"smtp_server": smtp_server, "smtp_port": smtp_port}
            )

        except Exception as e:
            logger.error(f"Email service health check failed: {e}")
            return HealthCheckResult(
                name="email_service",
                status=HealthStatus.UNHEALTHY,
                message=f"Email service check failed: {str(e)}"
            )

    async def check_system_resources(self) -> HealthCheckResult:
        """检查系统资源占用"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            }

            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "System resources critically high"
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 80:
                status = HealthStatus.DEGRADED
                message = "System resources elevated"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources normal"

            return HealthCheckResult(
                name="system_resources",
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"System resources check failed: {str(e)}"
            )

    async def check_all(self, force: bool = False) -> Dict:
        """执行所有健康检查（带速率限制缓存）"""
        import time
        current_time = time.time()

        if not force and self._cached_result and (current_time - self._last_check_time) < self.MIN_CHECK_INTERVAL:
            logger.debug(f"Returning cached health check result (age: {current_time - self._last_check_time:.1f}s)")
            return self._cached_result

        logger.info("Starting comprehensive health check...")

        checks = await asyncio.gather(
            self.check_database(),
            self.check_scraper(),
            self.check_ai_models(),
            self.check_email_service(),
            self.check_system_resources(),
            return_exceptions=True
        )

        results = []
        unhealthy_count = 0
        degraded_count = 0

        for check in checks:
            if isinstance(check, Exception):
                logger.error(f"Health check failed with exception: {check}")
                results.append(HealthCheckResult(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=str(check)
                ).to_dict())
                unhealthy_count += 1
            else:
                results.append(check.to_dict())
                if check.status == HealthStatus.UNHEALTHY:
                    unhealthy_count += 1
                elif check.status == HealthStatus.DEGRADED:
                    degraded_count += 1

        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        result = {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": results,
            "summary": {
                "total": len(results),
                "healthy": len([r for r in results if r['status'] == HealthStatus.HEALTHY]),
                "degraded": degraded_count,
                "unhealthy": unhealthy_count
            }
        }

        self._cached_result = result
        self._last_check_time = current_time

        return result

    def cleanup(self):
        """清理资源（仅清理自己创建的连接）"""
        if self._owns_db_manager and self.db_manager:
            self.db_manager.close()
            self.db_manager = None
            self.data_repo = None
            self._owns_db_manager = False
