"""Settings and scheduler endpoints router"""
from fastapi import APIRouter, Request, Depends, HTTPException
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..schemas import SettingsResponse, SettingsUpdateRequest, APIResponse, SchedulerStatusUpdate
from ...core.services.settings_service import SettingsService

router = APIRouter(prefix="/api", tags=["Settings"])
limiter = Limiter(key_func=get_remote_address)


def get_settings_service(request: Request) -> SettingsService:
    return request.app.state.settings_service


def get_verify_token(request: Request):
    return request.app.state.verify_token


def get_scheduler(request: Request):
    if not hasattr(request.app.state, 'scheduler') or request.app.state.scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    return request.app.state.scheduler


@router.get("/settings", response_model=SettingsResponse)
@limiter.limit("30/minute")
async def get_settings(
    request: Request,
    service: SettingsService = Depends(get_settings_service),
    current_user: dict = Depends(get_verify_token)
):
    """获取所有设置（统一接口）"""
    try:
        scheduler_running = False
        next_run_times = {"daily": None, "weekly": None, "monthly": None}
        if hasattr(request.app.state, 'scheduler') and request.app.state.scheduler:
            scheduler_running = request.app.state.scheduler.is_running()
            next_run_times = request.app.state.scheduler.get_next_run_times()
        return service.get_settings(scheduler_running, next_run_times)
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get settings")


@router.put("/settings", response_model=APIResponse)
@limiter.limit("10/minute")
async def update_settings(
    request: Request,
    update: SettingsUpdateRequest,
    service: SettingsService = Depends(get_settings_service),
    current_user: dict = Depends(get_verify_token)
):
    """更新设置（部分更新）"""
    try:
        service.update_settings(update)

        if update.scheduler and hasattr(request.app.state, 'scheduler') and request.app.state.scheduler:
            sched = request.app.state.scheduler
            sched._reschedule_job('daily', update.scheduler.daily_enabled, update.scheduler.daily_time)
            sched._reschedule_job('weekly', update.scheduler.weekly_enabled, f"{update.scheduler.weekly_day} {update.scheduler.weekly_time}")
            sched._reschedule_job('monthly', update.scheduler.monthly_enabled, update.scheduler.monthly_time)

        logger.info("Settings updated successfully")
        return APIResponse(success=True, message="Settings updated successfully", data=None)
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")


@router.put("/scheduler", response_model=APIResponse)
@limiter.limit("5/minute")
async def update_scheduler_status(
    request: Request,
    status_update: SchedulerStatusUpdate,
    scheduler = Depends(get_scheduler),
    current_user: dict = Depends(get_verify_token)
):
    """更新调度器状态 (Start/Stop)"""
    if status_update.status == "running":
        if scheduler.is_running():
            raise HTTPException(status_code=409, detail="Scheduler is already running")
        scheduler.start()
        return APIResponse(success=True, message="Scheduler started", data=None)
    elif status_update.status == "stopped":
        if not scheduler.is_running():
            raise HTTPException(status_code=409, detail="Scheduler is not running")
        scheduler.stop()
        return APIResponse(success=True, message="Scheduler stopped", data=None)

    raise HTTPException(status_code=400, detail="Invalid status")
