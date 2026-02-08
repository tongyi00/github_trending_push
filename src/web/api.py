#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FastAPI 应用主入口
"""

import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
import jwt
from typing import Optional
from fastapi import Security

from ..core.database import DatabaseManager
from ..core.data_repository import DataRepository
from ..infrastructure.health_monitor import HealthMonitor
from ..core.trending_push import TrendingPush
from ..infrastructure.scheduler import TrendingScheduler
from ..infrastructure.config_manager import ConfigManager
from ..core.services.trending_service import TrendingService
from ..core.services.stats_service import StatsService
from ..core.services.settings_service import SettingsService
from ..infrastructure.task_manager import BackgroundTaskManager
from ..constants import MAX_BACKGROUND_TASKS
from contextlib import asynccontextmanager

from .routers import trending_router, stats_router, settings_router, tasks_router, analysis_router

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET") or "dev-only"
JWT_ALGORITHM = "HS256"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production" and JWT_SECRET == "dev-only":
    raise RuntimeError("JWT_SECRET must be set in production environment")

if ENVIRONMENT == "development" and JWT_SECRET == "dev-only":
    logger.warning("Using insecure JWT_SECRET in development mode. Set JWT_SECRET environment variable for production.")

security = HTTPBearer(auto_error=False)


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> dict:
    """验证JWT令牌（可选认证）"""
    if ENVIRONMENT != "production" and JWT_SECRET == "dev-only":
        return {"user": "anonymous"}

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    try:
        from ..infrastructure.security import Sanitizer
        token = credentials.credentials
        payload = Sanitizer.verify_token(token, JWT_SECRET, JWT_ALGORITHM)
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def _get_scheduler_config_from_db(settings_service: SettingsService) -> Optional[dict]:
    """从数据库获取调度器配置，转换为调度器期望的嵌套结构"""
    try:
        # 获取数据库中的设置（使用空的运行状态）
        settings = settings_service.get_settings(False, {})
        sched = settings.scheduler

        # 转换为调度器期望的嵌套结构
        return {
            'timezone': sched.timezone,
            'daily': {
                'enabled': sched.daily_enabled,
                'time': sched.daily_time
            },
            'weekly': {
                'enabled': sched.weekly_enabled,
                'day': sched.weekly_day,
                'time': sched.weekly_time
            },
            'monthly': {
                'enabled': sched.monthly_enabled,
                'time': sched.monthly_time
            }
        }
    except Exception as e:
        logger.warning(f"Failed to get scheduler config from database: {e}, using YAML config")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database manager inside lifespan
    db_manager = DatabaseManager(db_path="data/trending.db")
    db_manager.init_db()
    app.state.db_manager = db_manager

    # Initialize repositories and services
    data_repo = DataRepository(db_manager)
    app.state.data_repo = data_repo
    app.state.trending_service = TrendingService(db_manager, data_repo)
    app.state.stats_service = StatsService(db_manager, data_repo)
    app.state.settings_service = SettingsService(db_manager)

    # Initialize task manager and background tasks set
    app.state.task_manager = BackgroundTaskManager()
    app.state.background_tasks = set()

    # Store verify_token function for routers
    app.state.verify_token = verify_token

    # Health monitor
    app.state.health_monitor = HealthMonitor()

    # Initialize config with database-first mode
    config_manager = ConfigManager()
    config_manager.set_db_manager(db_manager)
    config = config_manager.get_all()

    # Initialize business core
    trending_push = TrendingPush(db_manager=db_manager, config=config)
    app.state.trending_push = trending_push

    # Initialize scheduler with database settings if available
    # Override YAML config with database settings for scheduler
    db_scheduler_config = _get_scheduler_config_from_db(app.state.settings_service)
    if db_scheduler_config:
        config['scheduler'] = db_scheduler_config
        logger.info("Using scheduler settings from database")

    scheduler = TrendingScheduler(config, db_manager=db_manager)
    scheduler.set_daily_job(lambda: trending_push.run_task('daily'))
    scheduler.set_weekly_job(lambda: trending_push.run_task('weekly'))
    scheduler.set_monthly_job(lambda: trending_push.run_task('monthly'))
    scheduler.start()
    app.state.scheduler = scheduler

    logger.info("Application resources initialized (Scheduler + TrendingPush)")

    # Check if database is empty and trigger initialization
    try:
        stats = app.state.stats_service.get_overview()
        if stats.get('total_repositories', 0) == 0:
            logger.info("Database is empty. Triggering initial data fetch sequence (Daily -> Weekly -> Monthly)...")

            async def run_initialization_sequence():
                await asyncio.sleep(3)
                for task_type in ['daily', 'weekly', 'monthly']:
                    try:
                        task_id = app.state.task_manager.create_task(task_type)
                        logger.info(f"Starting initialization task: {task_type} (ID: {task_id})")
                        await _execute_task_background(app, task_id, task_type, is_startup=True)
                        logger.info(f"Completed initialization task: {task_type}")
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.error(f"Initialization task {task_type} failed: {e}")

            task = asyncio.create_task(run_initialization_sequence())
            app.state.background_tasks.add(task)
            task.add_done_callback(app.state.background_tasks.discard)

    except Exception as e:
        logger.error(f"Failed to trigger initialization tasks: {e}")

    yield

    # Cleanup resources
    logger.info("Cleaning up resources...")
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.stop()

    if hasattr(app.state, 'trending_push'):
        await app.state.trending_push.close()


async def _execute_task_background(app: FastAPI, task_id: str, task_type: str, is_startup: bool = False):
    """后台执行任务"""
    trending_push = app.state.trending_push
    scheduler = app.state.scheduler
    task_manager = app.state.task_manager

    task_manager.update_task(task_id, status="running", started_at=datetime.now().isoformat())
    record_id = scheduler.record_task_start(task_type, task_id)

    try:
        result = await trending_push.run_task_async(task_type, is_startup=is_startup)

        task_manager.update_task(
            task_id,
            status="success" if result.success else "failed",
            finished_at=datetime.now().isoformat(),
            repos_found=result.repos_found,
            repos_after_filter=result.repos_after_filter,
            email_sent=result.email_sent,
            error_message=result.error_message
        )

        scheduler.record_task_end(record_id, result.success, result.error_message)
        logger.info(f"Task {task_id} completed: {result.success}")

    except Exception as e:
        task_manager.update_task(
            task_id,
            status="failed",
            finished_at=datetime.now().isoformat(),
            error_message=str(e)
        )
        scheduler.record_task_end(record_id, False, str(e))
        logger.error(f"Task {task_id} failed: {e}")


app = FastAPI(
    title="GitHub Trending Push API",
    description="GitHub趋势项目追踪系统后端API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
if ENVIRONMENT == "production":
    FRONTEND_URL = os.getenv("FRONTEND_URL")
    if not FRONTEND_URL:
        raise RuntimeError("FRONTEND_URL must be set in production environment")
    ALLOWED_ORIGINS = [FRONTEND_URL]
else:
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    import secrets
    nonce = secrets.token_urlsafe(16)
    request.state.csp_nonce = nonce

    response = await call_next(request)

    if ENVIRONMENT == "production":
        csp = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}'; "
            f"style-src 'self' 'nonce-{nonce}'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    else:
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:"
        )

    response.headers["Content-Security-Policy"] = csp
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """统一处理未捕获的异常，返回一致的错误格式"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    content = {"detail": "Internal server error"}
    if ENVIRONMENT != "production":
        content["type"] = type(exc).__name__
    return JSONResponse(status_code=500, content=content)


# Register routers
app.include_router(trending_router)
app.include_router(stats_router)
app.include_router(settings_router)
app.include_router(tasks_router)
app.include_router(analysis_router)


@app.get("/", tags=["System"])
@limiter.limit("100/minute")
async def root(request: Request):
    """API根路径"""
    return {"message": "GitHub Trending Push API", "version": "1.0.0", "docs": "/api/docs"}


@app.get("/api/health", tags=["System"])
@limiter.limit("60/minute")
async def health_check(request: Request):
    """健康检查端点"""
    try:
        health_monitor = request.app.state.health_monitor
        health_result = await health_monitor.check_all()
        if health_result['status'] == 'unhealthy':
            return JSONResponse(status_code=503, content=health_result)
        return health_result
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": "Health check failed"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
