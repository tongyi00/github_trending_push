#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub Trending Push - 统一入口
启动 Web API 服务器，同时运行后台定时任务
"""

import signal
import sys
import uvicorn
from loguru import logger
from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.logging_config import setup_logging
from src.web.api import app

# Graceful shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    if shutdown_requested:
        logger.warning("Force shutdown requested, exiting immediately...")
        sys.exit(1)

    shutdown_requested = True
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name}, initiating graceful shutdown...")


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Windows-specific: SIGBREAK for Ctrl+Break
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)

    # Initialize config and logging
    config = ConfigManager.get_instance().get_all()
    setup_logging(config)

    api_config = config.get('api', {})
    host = api_config.get('host', '127.0.0.1')
    port = api_config.get('port', 8000)

    logger.info("Starting GitHub Trending Push (API + Scheduler)...")
    logger.info(f"API documentation: http://{host}:{port}/api/docs")

    uvicorn.run(
        "src.web.api:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
