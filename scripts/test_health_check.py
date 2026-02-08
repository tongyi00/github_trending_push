#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
健康检查测试脚本 - 执行一次完整的健康检查
"""
import os
import sys
import asyncio
from pathlib import Path
from loguru import logger
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))
from src.infrastructure import HealthMonitor


async def main():
    """执行健康检查并输出结果"""
    logger.info("Starting health check test...")

    monitor = HealthMonitor()

    try:
        result = await monitor.check_all()

        logger.info("\n" + "="*60)
        logger.info("HEALTH CHECK RESULTS")
        logger.info("="*60)
        logger.info(f"\n📊 Overall Status: {result['status'].upper()}")
        logger.info(f"⏰ Timestamp: {result['timestamp']}")
        logger.info(f"\n📈 Summary:")
        logger.info(f"  Total Checks: {result['summary']['total']}")
        logger.info(f"  Healthy: {result['summary']['healthy']}")
        logger.info(f"  Degraded: {result['summary']['degraded']}")
        logger.info(f"  Unhealthy: {result['summary']['unhealthy']}")

        logger.info(f"\n🔍 Individual Checks:")
        for check in result['checks']:
            status_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌'
            }
            emoji = status_emoji.get(check['status'], '❓')
            logger.info(f"\n  {emoji} {check['name'].upper()}")
            logger.info(f"     Status: {check['status']}")
            logger.info(f"     Message: {check['message']}")
            if check.get('details'):
                logger.info(f"     Details: {check['details']}")

        logger.info("\n" + "="*60)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise
    finally:
        monitor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
