"""
任务调度模块 - 支持每日、每周、每月定时任务
"""
import calendar
from loguru import logger
from datetime import datetime
from typing import Dict, Any, Callable, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor

from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class TrendingScheduler:
    """Trending推送调度器"""

    def __init__(self, config: Dict[str, Any], db_manager=None):
        """初始化调度器"""
        self.config = config
        self.scheduler_config = config.get('scheduler', {})
        self.timezone = self.scheduler_config.get('timezone', 'Asia/Shanghai')
        self.db_manager = db_manager

        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self._is_running = False
        self._shared_executor = None

        # 任务回调函数
        self._daily_callback: Callable = None
        self._weekly_callback: Callable = None
        self._monthly_callback: Callable = None

    def is_running(self) -> bool:
        """返回调度器是否正在运行"""
        return self._is_running and self.scheduler.running

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "running": self.is_running(),
            "timezone": self.timezone,
            "jobs": [{"id": job.id, "name": job.name, "next_run": job.next_run_time.isoformat() if job.next_run_time else None} for job in self.scheduler.get_jobs()]
        }

    def get_next_run_times(self) -> Dict[str, Optional[str]]:
        """获取各任务的下次执行时间"""
        result = {"daily": None, "weekly": None, "monthly": None}
        for job in self.scheduler.get_jobs():
            if job.id == 'daily_trending' and job.next_run_time:
                result["daily"] = job.next_run_time.isoformat()
            elif job.id == 'weekly_trending' and job.next_run_time:
                result["weekly"] = job.next_run_time.isoformat()
            elif job.id == 'monthly_trending' and job.next_run_time:
                result["monthly"] = job.next_run_time.isoformat()
        return result

    def _validate_time_format(self, time_str: str) -> tuple:
        """Validate and parse HH:MM time format"""
        import re
        if not re.match(r'^([01]?\d|2[0-3]):[0-5]\d$', time_str):
            raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM (e.g., 08:00)")
        hour, minute = map(int, time_str.split(':'))
        return hour, minute

    def _validate_day_of_week(self, day: str) -> str:
        """Validate and convert day of week to cron format"""
        day_map = {'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed', 'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'}
        day_lower = day.lower().strip()
        if day_lower not in day_map:
            raise ValueError(f"Invalid day of week: {day}. Expected one of: {', '.join(day_map.keys())}")
        return day_map[day_lower]

    def _reschedule_job(self, task_type: str, enabled: bool, cron_expression: str) -> None:
        """重新注册单个任务（由 API 调用）"""
        job_id_map = {'daily': 'daily_trending', 'weekly': 'weekly_trending', 'monthly': 'monthly_trending'}
        job_name_map = {'daily': 'Daily Trending Push', 'weekly': 'Weekly Trending Push', 'monthly': 'Monthly Trending Push'}
        callback_map = {'daily': self._daily_job, 'weekly': self._weekly_job, 'monthly': self._monthly_job}

        job_id = job_id_map.get(task_type)
        if not job_id:
            return

        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed existing job: {job_id}")

        if not enabled:
            logger.info(f"Job {task_type} is disabled, not scheduling")
            return

        job_func = callback_map[task_type]

        try:
            if task_type == 'daily':
                hour, minute = self._validate_time_format(cron_expression)
                trigger = CronTrigger(hour=hour, minute=minute, timezone=self.timezone)
            elif task_type == 'weekly':
                parts = cron_expression.split()
                day = parts[0] if len(parts) > 0 else 'sunday'
                time_str = parts[1] if len(parts) > 1 else '22:00'
                hour, minute = self._validate_time_format(time_str)
                day_of_week = self._validate_day_of_week(day)
                trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, timezone=self.timezone)
            elif task_type == 'monthly':
                hour, minute = self._validate_time_format(cron_expression)
                trigger = CronTrigger(hour=hour, minute=minute, timezone=self.timezone)
            else:
                return

            self.scheduler.add_job(job_func, trigger, id=job_id, name=job_name_map[task_type], replace_existing=True)
            logger.info(f"Rescheduled {task_type} job with cron: {cron_expression}")
        except ValueError as e:
            logger.error(f"Invalid cron expression for {task_type} job: {e}")
        except Exception as e:
            logger.error(f"Failed to reschedule {task_type} job: {e}")

    def record_task_start(self, task_type: str, task_id: str = None) -> Optional[int]:
        """记录任务开始"""
        if not self.db_manager:
            return None

        from src.core.models import TaskHistory
        with self.db_manager.get_session() as session:
            record = TaskHistory(task_type=task_type, task_id=task_id, started_at=datetime.now(), status="running")
            session.add(record)
            session.flush()
            return record.id

    def record_task_end(self, record_id: int, success: bool, error_message: str = None) -> None:
        """记录任务结束"""
        if not self.db_manager or not record_id:
            return

        from src.core.models import TaskHistory
        with self.db_manager.get_session() as session:
            record = session.query(TaskHistory).filter_by(id=record_id).first()
            if record:
                record.finished_at = datetime.now()
                record.status = "success" if success else "failed"
                record.error_message = error_message

    def set_daily_job(self, callback: Callable) -> None:
        """设置每日任务回调"""
        self._daily_callback = callback

    def set_weekly_job(self, callback: Callable) -> None:
        """设置每周任务回调"""
        self._weekly_callback = callback

    def set_monthly_job(self, callback: Callable) -> None:
        """设置每月任务回调"""
        self._monthly_callback = callback

    def _get_shared_executor(self) -> ThreadPoolExecutor:
        """Get or create shared ThreadPoolExecutor"""
        if self._shared_executor is None or self._shared_executor._shutdown:
            self._shared_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="scheduler-retry")
        return self._shared_executor

    def _safe_execute(self, callback: Callable) -> None:
        """Decorator/Wrapper for safe task execution"""
        try:
            callback()
        except Exception as e:
            logger.error(f"Unhandled exception in scheduled task: {e}")
            # Optionally send alert here if not already handled inside callback
            try:
                from .alerting import Alerting
                alerting = Alerting()
                alerting.alert_task_failure("Scheduled Task", str(e))
            except Exception:
                pass
            raise e  # Re-raise to let retry logic handle it if needed

    def _execute_with_retry(self, callback: Callable, job_name: str, max_retries: int = 3, retry_delay: int = 60) -> None:
        """执行任务并支持重试（使用共享线程池避免阻塞调度线程）"""
        import threading

        def retry_task():
            for attempt in range(1, max_retries + 1):
                try:
                    # Wrap with safe execution
                    self._safe_execute(callback)
                    logger.info(f"{job_name.capitalize()} job completed successfully")
                    return
                except Exception as e:
                    logger.error(f"{job_name.capitalize()} job failed (attempt {attempt}/{max_retries}): {e}")

                    if attempt < max_retries:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        event = threading.Event()
                        event.wait(timeout=retry_delay)
                    else:
                        logger.error(f"{job_name.capitalize()} job failed after {max_retries} attempts")
                        try:
                            from .alerting import Alerting
                            alerting = Alerting()
                            alerting.alert_task_failure(f"{job_name} trending job", str(e))
                        except Exception as alert_error:
                            logger.error(f"Failed to send alert: {alert_error}")

        executor = self._get_shared_executor()
        executor.submit(retry_task)

    def _daily_job(self) -> None:
        """执行每日任务（支持重试）"""
        logger.info("Executing daily trending job...")
        if self._daily_callback:
            self._execute_with_retry(self._daily_callback, "daily")
        else:
            logger.warning("No daily callback registered")

    def _weekly_job(self) -> None:
        """执行每周任务（支持重试）"""
        logger.info("Executing weekly trending job...")
        if self._weekly_callback:
            self._execute_with_retry(self._weekly_callback, "weekly")
        else:
            logger.warning("No weekly callback registered")

    def _monthly_job(self) -> None:
        """执行每月任务（仅在月末执行，支持重试）"""
        today = datetime.now()
        last_day = calendar.monthrange(today.year, today.month)[1]

        if today.day != last_day:
            logger.debug(f"Not the last day of month (today: {today.day}, last: {last_day}), skipping")
            return

        logger.info("Executing monthly trending job (last day of month)...")
        if self._monthly_callback:
            self._execute_with_retry(self._monthly_callback, "monthly")
        else:
            logger.warning("No monthly callback registered")

    def _register_jobs(self) -> None:
        """注册所有定时任务"""
        # 每日任务
        daily_config = self.scheduler_config.get('daily', {})
        if daily_config.get('enabled', True):
            time_str = daily_config.get('time', '08:00')
            hour, minute = map(int, time_str.split(':'))

            self.scheduler.add_job(self._daily_job, CronTrigger(hour=hour, minute=minute, timezone=self.timezone), id='daily_trending', name='Daily Trending Push', replace_existing=True)
            logger.info(f"Registered daily job at {time_str} ({self.timezone})")

        # 每周任务
        weekly_config = self.scheduler_config.get('weekly', {})
        if weekly_config.get('enabled', True):
            time_str = weekly_config.get('time', '22:00')
            day = weekly_config.get('day', 'sunday')
            hour, minute = map(int, time_str.split(':'))

            day_map = {'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed', 'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'}
            day_of_week = day_map.get(day.lower(), 'sun')

            self.scheduler.add_job(self._weekly_job, CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, timezone=self.timezone), id='weekly_trending', name='Weekly Trending Push', replace_existing=True)
            logger.info(f"Registered weekly job at {day} {time_str} ({self.timezone})")

        # 每月任务（月末执行）
        monthly_config = self.scheduler_config.get('monthly', {})
        if monthly_config.get('enabled', True):
            time_str = monthly_config.get('time', '22:00')
            hour, minute = map(int, time_str.split(':'))

            self.scheduler.add_job(self._monthly_job, CronTrigger(day='last', hour=hour, minute=minute, timezone=self.timezone), id='monthly_trending', name='Monthly Trending Push', replace_existing=True)
            logger.info(f"Registered monthly job at {time_str} on last day of month ({self.timezone})")

    def start(self) -> None:
        """启动调度器"""
        self._register_jobs()
        self.scheduler.start()
        self._is_running = True
        logger.info("Scheduler started")

        self._print_next_run_times()

    def stop(self) -> None:
        """停止调度器"""
        self.scheduler.shutdown()
        self._is_running = False
        if self._shared_executor:
            self._shared_executor.shutdown(wait=False)
            self._shared_executor = None
        logger.info("Scheduler stopped")

    def _print_next_run_times(self) -> None:
        """打印下次执行时间"""
        jobs = self.scheduler.get_jobs()
        if not jobs:
            logger.info("No jobs registered")
            return

        logger.info("Scheduled jobs:")
        for job in jobs:
            next_run = job.next_run_time
            if next_run:
                logger.info(f"  - {job.name}: next run at {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    def get_jobs(self):
        """获取所有注册的任务"""
        return self.scheduler.get_jobs()


def create_scheduler(config: Dict[str, Any]) -> TrendingScheduler:
    """创建调度器实例"""
    return TrendingScheduler(config)
