"""
任务调度模块 - 支持每日、每周、每月定时任务
"""
import calendar
from datetime import datetime
from typing import Dict, Any, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger


class TrendingScheduler:
    """Trending推送调度器"""

    def __init__(self, config: Dict[str, Any]):
        """初始化调度器"""
        self.config = config
        self.scheduler_config = config.get('scheduler', {})
        self.timezone = self.scheduler_config.get('timezone', 'Asia/Shanghai')

        self.scheduler = BackgroundScheduler(timezone=self.timezone)

        # 任务回调函数
        self._daily_callback: Callable = None
        self._weekly_callback: Callable = None
        self._monthly_callback: Callable = None

    def set_daily_job(self, callback: Callable):
        """设置每日任务回调"""
        self._daily_callback = callback

    def set_weekly_job(self, callback: Callable):
        """设置每周任务回调"""
        self._weekly_callback = callback

    def set_monthly_job(self, callback: Callable):
        """设置每月任务回调"""
        self._monthly_callback = callback

    def _daily_job(self):
        """执行每日任务"""
        logger.info("Executing daily trending job...")
        if self._daily_callback:
            try:
                self._daily_callback()
                logger.info("Daily job completed successfully")
            except Exception as e:
                logger.error(f"Daily job failed: {e}")
        else:
            logger.warning("No daily callback registered")

    def _weekly_job(self):
        """执行每周任务"""
        logger.info("Executing weekly trending job...")
        if self._weekly_callback:
            try:
                self._weekly_callback()
                logger.info("Weekly job completed successfully")
            except Exception as e:
                logger.error(f"Weekly job failed: {e}")
        else:
            logger.warning("No weekly callback registered")

    def _monthly_job(self):
        """执行每月任务（仅在月末执行）"""
        today = datetime.now()
        last_day = calendar.monthrange(today.year, today.month)[1]

        if today.day != last_day:
            logger.debug(f"Not the last day of month (today: {today.day}, last: {last_day}), skipping")
            return

        logger.info("Executing monthly trending job (last day of month)...")
        if self._monthly_callback:
            try:
                self._monthly_callback()
                logger.info("Monthly job completed successfully")
            except Exception as e:
                logger.error(f"Monthly job failed: {e}")
        else:
            logger.warning("No monthly callback registered")

    def _register_jobs(self):
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

            # 转换星期名称
            day_map = {'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed', 'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'}
            day_of_week = day_map.get(day.lower(), 'sun')

            self.scheduler.add_job(self._weekly_job, CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, timezone=self.timezone), id='weekly_trending', name='Weekly Trending Push', replace_existing=True)
            logger.info(f"Registered weekly job at {day} {time_str} ({self.timezone})")

        # 每月任务（每天检查是否为月末）
        monthly_config = self.scheduler_config.get('monthly', {})
        if monthly_config.get('enabled', True):
            time_str = monthly_config.get('time', '22:00')
            hour, minute = map(int, time_str.split(':'))

            self.scheduler.add_job(self._monthly_job, CronTrigger(hour=hour, minute=minute, timezone=self.timezone), id='monthly_trending', name='Monthly Trending Push', replace_existing=True)
            logger.info(f"Registered monthly job at {time_str} on last day of month ({self.timezone})")

    def start(self):
        """启动调度器"""
        self._register_jobs()
        self.scheduler.start()
        logger.info("Scheduler started")

        # 打印下次执行时间
        self._print_next_run_times()

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def _print_next_run_times(self):
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
