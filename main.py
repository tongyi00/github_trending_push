#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub Trending Push - 主入口
定时抓取GitHub热门项目，AI生成摘要，邮件推送
"""

import sys
import argparse
import datetime
import json
import signal
import time
from pathlib import Path

from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.ai_summarizer import AISummarizer
from src.config_validator import load_config, validate_config
from src.logging_config import setup_logging
from src.mailer import EmailSender
from src.scheduler import TrendingScheduler
from src.scraper_treding import ScraperTrending


class TrendingPush:
    """GitHub Trending Push 主类"""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = load_config(config_path)
        setup_logging(self.config)

        logger.info("Initializing GitHub Trending Push...")

        self.scraper = ScraperTrending()
        self.summarizer = AISummarizer(config_path)
        self.mailer = EmailSender(self.config)
        self.scheduler = TrendingScheduler(self.config)

        # 注册调度任务
        self.scheduler.set_daily_job(lambda: self.run_task('daily'))
        self.scheduler.set_weekly_job(lambda: self.run_task('weekly'))
        self.scheduler.set_monthly_job(lambda: self.run_task('monthly'))

        logger.info("Initialization complete")

    def _save_data(self, repos: list, time_range: str):
        """保存数据到文件"""
        file_path = Path("data/trending.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取现有数据
        all_data = {}
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read existing data file: {e}, creating new one")

        # 更新数据
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        repos_dict = {repo['name']: repo for repo in repos}

        if time_range not in all_data:
            all_data[time_range] = {}
        all_data[time_range][current_date] = repos_dict

        # 保存文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Data saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")

    def _filter_duplicates(self, repos: list, time_range: str) -> list:
        """根据历史记录过滤重复项目"""
        file_path = Path("data/trending.json")
        if not file_path.exists():
            return repos

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_data = json.load(f)

            # 获取该时间范围下的所有历史项目名称
            history_data = all_data.get(time_range, {})
            seen_projects = {name for projects in history_data.values() for name in projects.keys()}

            # 过滤掉已存在的项目
            new_repos = [repo for repo in repos if repo['name'] not in seen_projects]
            filtered_count = len(repos) - len(new_repos)

            for repo in repos:
                if repo['name'] in seen_projects:
                    logger.debug(f"Skipping duplicate project: {repo['name']}")

            logger.info(f"Filtered {filtered_count} duplicates. Remaining: {len(new_repos)}")
            return new_repos

        except Exception as e:
            logger.error(f"Failed to filter duplicates: {e}")
            return repos

    def run_task(self, time_range: str) -> bool:
        """执行单次推送任务"""
        logger.info(f"Starting {time_range} trending push task...")

        try:
            # 1. 爬取trending数据
            logger.info(f"Scraping {time_range} trending repositories...")
            repos = self.scraper.scrape_trending_by_range(since=time_range)

            if not repos:
                logger.warning(f"No {time_range} trending repositories found")
                return False

            # 2. 过滤重复项目
            repos = self._filter_duplicates(repos, time_range)

            if not repos:
                logger.warning(f"No new {time_range} trending repositories found after filtering")
                return True  # 没有新项目，但任务本身算执行成功

            logger.info(f"Found {len(repos)} new repositories")

            # 3. 保存原始数据
            self._save_data(repos, time_range)

            # 4. AI生成摘要
            logger.info("Generating AI summaries...")
            repos_with_summary = self.summarizer.batch_summarize(repos)

            # 5. 发送邮件
            logger.info("Sending email...")
            success = self.mailer.send_trending_email(repos_with_summary, time_range)

            if success:
                logger.info(f"{time_range.capitalize()} trending push completed successfully")
            else:
                logger.error(f"{time_range.capitalize()} trending push failed")

            return success

        except Exception as e:
            logger.error(f"Task failed: {e}")
            return False

    def start_daemon(self):
        """启动守护进程模式"""
        logger.info("Starting daemon mode...")

        def signal_handler(signum, frame):
            logger.info("Received shutdown signal, stopping scheduler...")
            self.scheduler.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.scheduler.start()
        logger.info("Daemon started. Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.scheduler.stop()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='GitHub Trending Push - Daily/Weekly/Monthly trending email push',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python main.py --validate        Validate configuration only
  python main.py --test            Run daily task once (test mode)
  python main.py --daily           Run daily task once
  python main.py --weekly          Run weekly task once
  python main.py --monthly         Run monthly task once
  python main.py --daemon          Start scheduler daemon
'''
    )

    parser.add_argument('--config', '-c', default='config/config.yaml', help='Configuration file path (default: config/config.yaml)')
    parser.add_argument('--validate', action='store_true', help='Validate configuration and exit')
    parser.add_argument('--test', action='store_true', help='Run daily task once (test mode)')
    parser.add_argument('--daily', action='store_true', help='Run daily task once')
    parser.add_argument('--weekly', action='store_true', help='Run weekly task once')
    parser.add_argument('--monthly', action='store_true', help='Run monthly task once')
    parser.add_argument('--daemon', '-d', action='store_true', help='Start scheduler daemon')

    args = parser.parse_args()

    if args.validate:
        success = validate_config(args.config)
        sys.exit(0 if success else 1)

    if not any([args.test, args.daily, args.weekly, args.monthly, args.daemon]):
        parser.print_help()
        sys.exit(0)

    try:
        app = TrendingPush(args.config)
    except SystemExit:
        sys.exit(1)
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)

    if args.daemon:
        app.start_daemon()
    elif args.test or args.daily:
        success = app.run_task('daily')
        sys.exit(0 if success else 1)
    elif args.weekly:
        success = app.run_task('weekly')
        sys.exit(0 if success else 1)
    elif args.monthly:
        success = app.run_task('monthly')
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
