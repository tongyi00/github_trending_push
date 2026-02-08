#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub Trending Push 核心业务类
"""

import json
import asyncio
import datetime
from pathlib import Path
from loguru import logger
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from ..outputs.mailer import EmailSender
from ..core.database import DatabaseManager
from ..core.data_repository import DataRepository
from ..infrastructure.filters import ProjectFilter
from ..analyzers.keyword_matcher import KeywordMatcher
from ..collectors.async_scraper import AsyncScraperTrending
from ..infrastructure.config_manager import ConfigManager
from ..analyzers.async_ai_summarizer import AsyncAISummarizer


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    task_type: str
    repos_found: int = 0
    repos_after_filter: int = 0
    email_sent: bool = False
    error_message: Optional[str] = None


class TrendingPush:
    """GitHub Trending Push 核心业务类"""

    def __init__(self, config_path: str = "config/config.yaml", db_manager: DatabaseManager = None, config: dict = None):
        self.config_path = config_path
        self.config = config or ConfigManager.get_instance(config_path).get_all()

        logger.info("Initializing GitHub Trending Push...")

        self.scraper = AsyncScraperTrending()
        self.summarizer = AsyncAISummarizer(config_path)
        self.mailer = EmailSender(self.config)
        self.filter = ProjectFilter(config_path)
        self.keyword_matcher = KeywordMatcher(config_path)

        self.db_manager = db_manager or DatabaseManager(db_path="data/trending.db")
        self.db_manager.init_db()
        self.data_repo = DataRepository(self.db_manager)

        logger.info("TrendingPush initialization complete")

    def _save_data(self, repos: List[Dict[str, Any]], time_range: str) -> None:
        """保存数据到数据库"""
        try:
            self.data_repo.save_trending_data(repos, time_range)
            logger.info(f"Data saved to database for {time_range}")
        except Exception as e:
            logger.error(f"Failed to save data to database: {e}")
            self._save_data_to_json_backup(repos, time_range)

    def _save_data_to_json_backup(self, repos: list, time_range: str):
        """备份数据到 JSON 文件（向后兼容）"""
        file_path = Path("data/trending.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        all_data = {}
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read existing data file: {e}, creating new one")

        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        repos_dict = {repo['name']: repo for repo in repos}

        if time_range not in all_data:
            all_data[time_range] = {}
        all_data[time_range][current_date] = repos_dict

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Backup data saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save backup data: {e}")

    def _filter_duplicates(self, repos: list, time_range: str) -> list:
        """根据历史记录过滤重复项目"""
        try:
            seen_projects = self.data_repo.get_seen_projects(time_range)
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

    async def close(self):
        """释放资源"""
        if hasattr(self.summarizer, 'close'):
            await self.summarizer.close()

        if hasattr(self.scraper, 'close'):
            await self.scraper.close()

        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.close()

        logger.info("TrendingPush resources released")

    def run_task(self, time_range: str, is_startup: bool = False) -> TaskResult:
        """执行单次推送任务（同步版本，用于调度器）"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.run_task_async(time_range, is_startup))
                return future.result()
        else:
            return asyncio.run(self.run_task_async(time_range, is_startup))

    async def run_task_async(self, time_range: str, is_startup: bool = False) -> TaskResult:
        """执行单次推送任务（异步版本），返回结构化结果"""
        logger.info(f"Starting {time_range} trending push task... (Startup: {is_startup})")
        result = TaskResult(success=False, task_type=time_range)

        try:
            logger.info(f"Scraping {time_range} trending repositories...")
            # Async scraper call
            repos = await self.scraper.scrape_trending_by_range(since=time_range)

            if not repos:
                logger.warning(f"No {time_range} trending repositories found")
                result.success = True
                return result

            result.repos_found = len(repos)

            repos = self._filter_duplicates(repos, time_range)

            if not repos:
                logger.warning(f"No new {time_range} trending repositories found after filtering")
                result.success = True
                return result

            logger.info(f"Found {len(repos)} new repositories")

            logger.info("Applying filters...")
            # 如果是启动初始化 (is_startup=True)，则忽略阈值过滤 (ignore_thresholds=True)
            repos = self.filter.filter_all(repos, time_range, ignore_thresholds=is_startup)

            if not repos:
                logger.warning(f"No repositories left after filtering")
                result.success = True
                return result

            result.repos_after_filter = len(repos)
            logger.info(f"After filtering: {len(repos)} repositories")

            if self.keyword_matcher.keywords:
                logger.info("Applying keyword matching...")
                matched_repos = self.keyword_matcher.filter_repos(repos)
                if matched_repos:
                    logger.info(f"Found {len(matched_repos)} repositories matching keywords")
                    repos = matched_repos

            logger.info("Saving repository data to database...")
            self._save_data(repos, time_range)

            logger.info("Generating AI summaries (async)...")
            try:
                repos_with_summary = await self.summarizer.batch_summarize(repos)

                # Save summaries to database
                for repo in repos_with_summary:
                    if repo.get('ai_summary'):
                        # Determine model name (simple logic, or could be passed back from summarizer)
                        model_name = self.config.get('ai_models', {}).get('enabled', ['unknown'])[0]
                        self.data_repo.save_ai_summary(repo['name'], repo['ai_summary'], model_name)

            except Exception as e:
                logger.error(f"AI Summary generation failed: {e}")
                # Don't fail the whole task, just continue without summaries
                repos_with_summary = repos

            logger.info("Sending email...")
            success = self.mailer.send_trending_email(repos_with_summary, time_range)
            result.email_sent = success

            if success:
                logger.info(f"{time_range.capitalize()} trending push completed successfully")
                result.success = True
            else:
                logger.error(f"{time_range.capitalize()} trending push failed")
                result.error_message = "Email sending failed"

            return result

        except Exception as e:
            logger.error(f"Task failed: {e}")
            result.error_message = str(e)
            return result
