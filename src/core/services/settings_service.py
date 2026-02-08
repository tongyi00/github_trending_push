import json
from datetime import datetime
from typing import Any, Optional
from loguru import logger
from ..database import DatabaseManager
from ..models import Settings, TaskHistory
from ...web.schemas import (
    SettingsUpdateRequest, EmailSettings, SchedulerSettings,
    FilterSettings, SubscriptionSettings, TaskHistoryItem, SettingsResponse
)
from ...infrastructure.config_manager import ConfigManager


class SettingsService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._config_manager = None

    @property
    def config_manager(self) -> ConfigManager:
        """延迟初始化 ConfigManager"""
        if self._config_manager is None:
            self._config_manager = ConfigManager()
        return self._config_manager

    def _get_yaml_config(self, *keys: str, default: Any = None) -> Any:
        """从 config.yaml 获取配置值（仅 yaml，不触发数据库查询）"""
        try:
            return self.config_manager.get_yaml_only(*keys, default=default)
        except Exception:
            return default

    def _get_or_create_settings(self, session) -> Settings:
        """获取或创建设置记录"""
        settings = session.query(Settings).first()
        if not settings:
            settings = Settings()
            session.add(settings)
            session.flush()
        return settings

    def get_settings(self, scheduler_running: bool, next_run_times: dict) -> SettingsResponse:
        """获取所有设置（数据库优先，config.yaml 作为回退）"""
        with self.db_manager.get_session() as session:
            settings = self._get_or_create_settings(session)

            # Email - 数据库优先，回退到 config.yaml
            db_recipients = json.loads(settings.email_recipients) if settings.email_recipients else None
            yaml_recipients = self._get_yaml_config('email', 'recipients', default=[])
            email = EmailSettings(
                recipients=db_recipients if db_recipients is not None else yaml_recipients
            )

            # Scheduler - 数据库优先，回退到 config.yaml
            scheduler = SchedulerSettings(
                timezone=settings.scheduler_timezone if settings.scheduler_timezone else self._get_yaml_config('scheduler', 'timezone', default='Asia/Shanghai'),
                daily_enabled=settings.scheduler_daily_enabled if settings.scheduler_daily_enabled is not None else self._get_yaml_config('scheduler', 'daily', 'enabled', default=True),
                daily_time=settings.scheduler_daily_time if settings.scheduler_daily_time else self._get_yaml_config('scheduler', 'daily', 'time', default='08:00'),
                weekly_enabled=settings.scheduler_weekly_enabled if settings.scheduler_weekly_enabled is not None else self._get_yaml_config('scheduler', 'weekly', 'enabled', default=True),
                weekly_day=settings.scheduler_weekly_day if settings.scheduler_weekly_day else self._get_yaml_config('scheduler', 'weekly', 'day', default='sunday'),
                weekly_time=settings.scheduler_weekly_time if settings.scheduler_weekly_time else self._get_yaml_config('scheduler', 'weekly', 'time', default='22:00'),
                monthly_enabled=settings.scheduler_monthly_enabled if settings.scheduler_monthly_enabled is not None else self._get_yaml_config('scheduler', 'monthly', 'enabled', default=True),
                monthly_time=settings.scheduler_monthly_time if settings.scheduler_monthly_time else self._get_yaml_config('scheduler', 'monthly', 'time', default='22:00')
            )

            # Filters - 数据库优先，回退到 config.yaml
            filters = FilterSettings(
                min_stars=settings.filters_min_stars if settings.filters_min_stars is not None else self._get_yaml_config('filters', 'min_stars', default=100),
                min_stars_daily=settings.filters_min_stars_daily if settings.filters_min_stars_daily is not None else self._get_yaml_config('filters', 'min_stars_daily', default=50),
                min_stars_weekly=settings.filters_min_stars_weekly if settings.filters_min_stars_weekly is not None else self._get_yaml_config('filters', 'min_stars_weekly', default=200),
                min_stars_monthly=settings.filters_min_stars_monthly if settings.filters_min_stars_monthly is not None else self._get_yaml_config('filters', 'min_stars_monthly', default=500)
            )

            # Subscription - 数据库优先，回退到空列表（config.yaml 中无此配置）
            subscription = SubscriptionSettings(
                keywords=json.loads(settings.subscription_keywords) if settings.subscription_keywords else [],
                languages=json.loads(settings.subscription_languages) if settings.subscription_languages else []
            )

            history = session.query(TaskHistory).order_by(TaskHistory.started_at.desc()).limit(10).all()
            task_history = [
                TaskHistoryItem(
                    id=h.id,
                    task_type=h.task_type,
                    started_at=h.started_at.isoformat(),
                    finished_at=h.finished_at.isoformat() if h.finished_at else None,
                    status=h.status,
                    error_message=h.error_message
                ) for h in history
            ]

            return SettingsResponse(
                email=email,
                scheduler=scheduler,
                filters=filters,
                subscription=subscription,
                scheduler_running=scheduler_running,
                next_run_times=next_run_times,
                task_history=task_history
            )

    def update_settings(self, update: SettingsUpdateRequest):
        """更新设置"""
        with self.db_manager.get_session() as session:
            settings = self._get_or_create_settings(session)

            if update.email:
                settings.email_recipients = json.dumps(update.email.recipients)

            if update.scheduler:
                settings.scheduler_timezone = update.scheduler.timezone
                settings.scheduler_daily_enabled = update.scheduler.daily_enabled
                settings.scheduler_daily_time = update.scheduler.daily_time
                settings.scheduler_weekly_enabled = update.scheduler.weekly_enabled
                settings.scheduler_weekly_day = update.scheduler.weekly_day
                settings.scheduler_weekly_time = update.scheduler.weekly_time
                settings.scheduler_monthly_enabled = update.scheduler.monthly_enabled
                settings.scheduler_monthly_time = update.scheduler.monthly_time

            if update.filters:
                settings.filters_min_stars = update.filters.min_stars
                settings.filters_min_stars_daily = update.filters.min_stars_daily
                settings.filters_min_stars_weekly = update.filters.min_stars_weekly
                settings.filters_min_stars_monthly = update.filters.min_stars_monthly

            if update.subscription:
                settings.subscription_keywords = json.dumps(update.subscription.keywords)
                settings.subscription_languages = json.dumps(update.subscription.languages)

            settings.updated_at = datetime.now()

            # 清除 ConfigManager 缓存，确保新设置立即生效
            self.config_manager.invalidate_cache()
