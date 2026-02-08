#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
健康监控守护进程 - 定期执行健康检查并发送告警
"""
import os
import sys
import signal
import asyncio
from pathlib import Path
from loguru import logger

# 切换到项目根目录
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from src.infrastructure import HealthMonitor, Alerting

class HealthMonitorDaemon:
    """健康监控守护进程"""

    def __init__(self, check_interval: int = 300):
        self.check_interval = check_interval
        self.health_monitor = HealthMonitor()
        self.alerting = Alerting()
        self.running = False
        self.last_alert_status = None

    async def run_check(self):
        """执行健康检查"""
        try:
            logger.info("Running scheduled health check...")
            health_result = await self.health_monitor.check_all()

            logger.info(f"Health check result: {health_result['status']}")
            logger.info(f"Summary: {health_result['summary']}")

            current_status = health_result['status']

            if current_status in ['unhealthy', 'degraded']:
                if self.last_alert_status != current_status:
                    logger.warning(f"System status changed to {current_status}, sending alert...")
                    self.alerting.alert_health_check_failure(health_result)
                    self.last_alert_status = current_status
            elif current_status == 'healthy' and self.last_alert_status in ['unhealthy', 'degraded']:
                logger.info("System recovered to healthy status")
                self.alerting.send_email_alert(
                    subject="系统恢复正常",
                    body="所有健康检查已通过，系统运行正常。",
                    level="info"
                )
                self.last_alert_status = None

        except Exception as e:
            logger.error(f"Health check failed: {e}")

    async def start(self):
        """启动守护进程"""
        self.running = True
        logger.info(f"Health monitor daemon started (check interval: {self.check_interval}s)")

        while self.running:
            try:
                await self.run_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("Health monitor daemon cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health monitor daemon: {e}")
                await asyncio.sleep(60)

    def stop(self):
        """停止守护进程"""
        logger.info("Stopping health monitor daemon...")
        self.running = False
        self.health_monitor.cleanup()


async def main():
    """主函数"""
    daemon = HealthMonitorDaemon(check_interval=300)

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        daemon.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await daemon.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())
