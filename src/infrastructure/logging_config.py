"""
日志配置模块
统一管理Loguru日志配置
"""

import os
import sys
from pathlib import Path
from loguru import logger
from typing import Dict, Any

from .security import Sanitizer


def setup_logging(config: Dict[str, Any]):
    """
    配置Loguru日志
    :param config: 包含logging部分的配置字典
    """
    logging_config = config.get('logging', {})
    level = logging_config.get('level', 'INFO')
    log_file = logging_config.get('file', 'logs/trending.log')
    rotation = logging_config.get('rotation', '10 MB')
    retention = logging_config.get('retention')
    if not retention:
        backup_count = logging_config.get('backup_count')
        if backup_count:
            retention = int(backup_count)
    if not retention:
        retention = "7 days"
    log_format = _get_log_format(logging_config.get('format', ''))
    logger.remove()
    # # 1. 添加控制台输出 (stderr)
    logger.add(sys.stderr, level=level, format=log_format, colorize=True)

    # 2. 添加文件输出
    log_path = Path(log_file)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)

        is_production = os.getenv("ENVIRONMENT", "").lower() == "production"

        def sanitize_filter(record):
            record["message"] = Sanitizer.sanitize(record["message"])
            return True

        logger.add(log_file, level=level, rotation=rotation, retention=retention, encoding='utf-8', format=log_format,
                   enqueue=True, backtrace=not is_production, diagnose=not is_production, filter=sanitize_filter)
    except Exception as e:
        # 如果文件日志设置失败，至少还有控制台日志
        logger.error(f"Failed to setup file logging: {e}")

    logger.debug(f"Logging initialized. Level: {level}, File: {log_file}")


def _get_log_format(fmt: str) -> str:
    """
    获取日志格式，支持将Python logging格式转换为Loguru格式
    """
    if not fmt:
        return "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # 如果包含 %，尝试进行简单的 logging format -> loguru format 映射
    if '%' in fmt:
        replacements = {
            '%(asctime)s': '{time:YYYY-MM-DD HH:mm:ss}',
            '%(levelname)s': '{level}',
            '%(level)s': '{level}',
            '%(message)s': '{message}',
            '%(name)s': '{name}',
            '%(module)s': '{module}',
            '%(funcName)s': '{function}',
            '%(lineno)d': '{line}',
            '%(lineno)s': '{line}',
            '%(threadName)s': '{thread}',
            '%(process)d': '{process}'
        }

        for py_fmt, loguru_fmt in replacements.items():
            fmt = fmt.replace(py_fmt, loguru_fmt)

    return fmt
