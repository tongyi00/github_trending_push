"""Background tasks endpoints router"""
import asyncio
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Path, HTTPException
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..schemas import TaskRunRequest, TaskRunResponse, TaskStatusResponse
from ...infrastructure.task_manager import BackgroundTaskManager
from ...core.models import TaskHistory
from ...constants import MAX_BACKGROUND_TASKS

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])
limiter = Limiter(key_func=get_remote_address)


def get_verify_token(request: Request):
    return request.app.state.verify_token


def get_task_manager(request: Request) -> BackgroundTaskManager:
    return request.app.state.task_manager


def get_db_manager(request: Request):
    return request.app.state.db_manager


async def _execute_task_background(request: Request, task_id: str, task_type: str, is_startup: bool = False):
    """后台执行任务"""
    trending_push = request.app.state.trending_push
    scheduler = request.app.state.scheduler
    task_manager = request.app.state.task_manager

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


@router.post("/run", response_model=TaskRunResponse)
@limiter.limit("5/minute")
async def run_task(
    request: Request,
    task_request: TaskRunRequest,
    current_user: dict = Depends(get_verify_token)
):
    """手动触发任务（异步提交，立即返回任务ID）"""
    if task_request.task_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid task_type")

    if not hasattr(request.app.state, 'trending_push') or request.app.state.trending_push is None:
        raise HTTPException(status_code=503, detail="TrendingPush not initialized")
    if not hasattr(request.app.state, 'scheduler') or request.app.state.scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    background_tasks = request.app.state.background_tasks
    if len(background_tasks) >= MAX_BACKGROUND_TASKS:
        raise HTTPException(status_code=429, detail=f"Too many background tasks ({MAX_BACKGROUND_TASKS} max). Please wait for existing tasks to complete.")

    task_manager = request.app.state.task_manager
    task_id = task_manager.create_task(task_request.task_type)

    task = asyncio.create_task(_execute_task_background(request, task_id, task_request.task_type))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    logger.info(f"Task {task_id} ({task_request.task_type}) submitted")
    return TaskRunResponse(
        task_id=task_id,
        task_type=task_request.task_type,
        status="pending",
        message="Task submitted successfully"
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
@limiter.limit("30/minute")
async def get_task_status(
    request: Request,
    task_id: str = Path(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', description="任务UUID"),
    current_user: dict = Depends(get_verify_token)
):
    """查询任务执行状态"""
    task_manager = request.app.state.task_manager
    task_info = task_manager.get_task(task_id)
    if task_info:
        return TaskStatusResponse(
            task_id=task_id,
            task_type=task_info["task_type"],
            status=task_info["status"],
            started_at=task_info.get("started_at"),
            finished_at=task_info.get("finished_at"),
            repos_found=task_info.get("repos_found", 0),
            repos_after_filter=task_info.get("repos_after_filter", 0),
            email_sent=task_info.get("email_sent", False),
            error_message=task_info.get("error_message")
        )

    try:
        db_manager = request.app.state.db_manager
        with db_manager.get_session() as session:
            history = session.query(TaskHistory).filter_by(task_id=task_id).first()
            if history:
                return TaskStatusResponse(
                    task_id=task_id,
                    task_type=history.task_type,
                    status=history.status,
                    started_at=history.started_at.isoformat() if history.started_at else None,
                    finished_at=history.finished_at.isoformat() if history.finished_at else None,
                    repos_found=0,
                    repos_after_filter=0,
                    email_sent=history.status == 'success',
                    error_message=history.error_message
                )
    except Exception as e:
        logger.error(f"Failed to query task history: {e}")

    raise HTTPException(status_code=404, detail="Task not found")
