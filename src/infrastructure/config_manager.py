#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理器 - 单例模式统一管理配置
优先级：数据库设置 > config.yaml
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class ConfigManager:
    """配置管理器单例（支持数据库优先）"""

    _instance: Optional['ConfigManager'] = None
    _config: Optional[Dict[str, Any]] = None
    _config_path: Optional[str] = None
    _db_manager = None
    _db_settings_cache: Optional[Dict[str, Any]] = None
    _initialized: bool = False

    def __new__(cls, config_path: str = "config/config.yaml"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config/config.yaml"):
        if not self._initialized or self._config_path != config_path:
            self._config_path = config_path
            self._load_config()
            ConfigManager._initialized = True

    def set_db_manager(self, db_manager) -> None:
        """设置数据库管理器（启用数据库优先模式）"""
        self._db_manager = db_manager
        self._db_settings_cache = None  # 清除缓存
        logger.info("ConfigManager: Database-first mode enabled")

    def invalidate_cache(self) -> None:
        """清除数据库设置缓存（设置更新后调用）"""
        self._db_settings_cache = None

    def _load_config(self):
        """加载配置文件"""
        try:
            config_file = Path(self._config_path)

            if not config_file.exists():
                logger.warning(f"Config file not found: {self._config_path}, using defaults")
                self._config = {}
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}

            logger.info(f"Configuration loaded from {self._config_path}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {}

    def _get_db_settings(self) -> Optional[Dict[str, Any]]:
        """从数据库获取设置（带缓存，返回扁平化的字典）"""
        if not self._db_manager:
            return None

        if self._db_settings_cache is not None:
            return self._db_settings_cache

        try:
            from ..core.models import Settings
            with self._db_manager.get_session() as session:
                settings = session.query(Settings).first()
                if not settings:
                    return None

                self._db_settings_cache = {
                    'email.recipients': json.loads(settings.email_recipients) if settings.email_recipients else None,
                    'scheduler.timezone': settings.scheduler_timezone,
                    'scheduler.daily.enabled': settings.scheduler_daily_enabled,
                    'scheduler.daily.time': settings.scheduler_daily_time,
                    'scheduler.weekly.enabled': settings.scheduler_weekly_enabled,
                    'scheduler.weekly.day': settings.scheduler_weekly_day,
                    'scheduler.weekly.time': settings.scheduler_weekly_time,
                    'scheduler.monthly.enabled': settings.scheduler_monthly_enabled,
                    'scheduler.monthly.time': settings.scheduler_monthly_time,
                    'filters.min_stars': settings.filters_min_stars,
                    'filters.min_stars_increment.daily': settings.filters_min_stars_daily,
                    'filters.min_stars_increment.weekly': settings.filters_min_stars_weekly,
                    'filters.min_stars_increment.monthly': settings.filters_min_stars_monthly,
                    'subscription.keywords': json.loads(settings.subscription_keywords) if settings.subscription_keywords else None,
                    'subscription.languages': json.loads(settings.subscription_languages) if settings.subscription_languages else None,
                }
                return self._db_settings_cache
        except Exception as e:
            logger.debug(f"Failed to load settings from database: {e}")
            return None

    def reload(self):
        """重新加载配置"""
        logger.info("Reloading configuration...")
        self._load_config()

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（数据库优先，config.yaml 回退）"""
        db_settings = self._get_db_settings()
        if db_settings:
            db_value = db_settings.get(key)
            if db_value is not None:
                return db_value

        return self._get_from_yaml(key, default)

    def _get_from_yaml(self, key: str, default: Any = None) -> Any:
        """仅从 config.yaml 获取配置项（不查询数据库）"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_yaml_only(self, *keys: str, default: Any = None) -> Any:
        """仅从 config.yaml 获取嵌套配置值（不查询数据库）"""
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

    def get_all(self) -> Dict[str, Any]:
        """获取全部配置（合并数据库和 yaml，数据库优先）"""
        import copy
        merged = copy.deepcopy(self._config)

        db_settings = self._get_db_settings()
        if db_settings:
            self._merge_db_settings(merged, db_settings)

        return merged

    def _merge_db_settings(self, config: Dict, db_settings: Dict[str, Any]) -> None:
        """将数据库设置合并到配置中"""
        for flat_key, value in db_settings.items():
            if value is None:
                continue

            keys = flat_key.split('.')
            target = config
            for k in keys[:-1]:
                if k not in target or not isinstance(target[k], dict):
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value

    def get_email_config(self) -> Dict[str, Any]:
        """获取邮件配置（数据库优先）"""
        import copy
        yaml_config = copy.deepcopy(self._config.get('email', {})) if self._config else {}

        db_settings = self._get_db_settings()
        if db_settings and db_settings.get('email.recipients') is not None:
            yaml_config['recipients'] = db_settings['email.recipients']

        return yaml_config

    def get_ai_models_config(self) -> Dict[str, Any]:
        """获取AI模型配置"""
        return self.get('ai_models', {})

    def get_scheduler_config(self) -> Dict[str, Any]:
        """获取调度器配置（数据库优先）"""
        import copy
        yaml_config = copy.deepcopy(self._config.get('scheduler', {})) if self._config else {}

        db_settings = self._get_db_settings()
        if not db_settings:
            return yaml_config

        if db_settings.get('scheduler.timezone') is not None:
            yaml_config['timezone'] = db_settings['scheduler.timezone']

        for period in ['daily', 'weekly', 'monthly']:
            if period not in yaml_config:
                yaml_config[period] = {}

            enabled_key = f'scheduler.{period}.enabled'
            time_key = f'scheduler.{period}.time'

            if db_settings.get(enabled_key) is not None:
                yaml_config[period]['enabled'] = db_settings[enabled_key]
            if db_settings.get(time_key) is not None:
                yaml_config[period]['time'] = db_settings[time_key]

        if db_settings.get('scheduler.weekly.day') is not None:
            yaml_config.setdefault('weekly', {})['day'] = db_settings['scheduler.weekly.day']

        return yaml_config

    def get_filters_config(self) -> Dict[str, Any]:
        """获取过滤器配置（数据库优先）"""
        import copy
        yaml_config = copy.deepcopy(self._config.get('filters', {})) if self._config else {}

        db_settings = self._get_db_settings()
        if not db_settings:
            return yaml_config

        if db_settings.get('filters.min_stars') is not None:
            yaml_config['min_total_stars'] = db_settings['filters.min_stars']

        if 'min_stars_increment' not in yaml_config:
            yaml_config['min_stars_increment'] = {}

        for period in ['daily', 'weekly', 'monthly']:
            key = f'filters.min_stars_increment.{period}'
            if db_settings.get(key) is not None:
                yaml_config['min_stars_increment'][period] = db_settings[key]

        return yaml_config

    def get_github_config(self) -> Dict[str, Any]:
        """获取GitHub配置"""
        return self.get('github', {})

    def get_alerting_config(self) -> Dict[str, Any]:
        """获取告警配置"""
        return self.get('alerting', {})

    @classmethod
    def get_instance(cls, config_path: str = "config/config.yaml") -> 'ConfigManager':
        """获取单例实例"""
        return cls(config_path)
