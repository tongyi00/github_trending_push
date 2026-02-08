#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目过滤器模块
"""

from loguru import logger
from typing import List, Dict

from .config_manager import ConfigManager


class ProjectFilter:
    """项目过滤器"""

    def __init__(self, config_path: str = "config/config.yaml"):
        config_manager = ConfigManager.get_instance(config_path)
        self.filter_config = config_manager.get_filters_config()

        self.min_total_stars = self.filter_config.get('min_total_stars', 0)
        self.min_stars_increment = self.filter_config.get('min_stars_increment', {})
        self.language_whitelist = self.filter_config.get('language_whitelist', [])
        self.language_blacklist = self.filter_config.get('language_blacklist', [])

    def filter_by_stars(self, repos: List[Dict], time_range: str = 'daily', ignore_thresholds: bool = False) -> List[Dict]:
        """根据 Star 数过滤项目"""
        if not repos:
            return []

        if ignore_thresholds:
            logger.info(f"Ignoring star thresholds for {time_range} (Startup Mode)")
            return repos

        filtered = []
        min_increment = self.min_stars_increment.get(time_range, 0)
        stars_key = f'stars_{time_range}'

        for repo in repos:
            total_stars = repo.get('stars', 0)
            stars_increment = repo.get(stars_key, 0)

            if total_stars < self.min_total_stars:
                logger.debug(f"Filtered out {repo['name']}: total stars {total_stars} < {self.min_total_stars}")
                continue

            # 特殊处理：如果是 weekly 或 monthly，爬虫可能无法直接获取增量
            # 此时如果 increment 为 0，且 total_stars 足够大，我们应该保留它
            # 或者如果 min_increment 配置为 0，也直接通过
            if min_increment > 0:
                # 只有当明确获取到了增量数据（>0），才进行比较
                # 否则，如果爬虫没拿到增量数据（=0），我们选择信任 min_total_stars 的过滤结果
                if stars_increment > 0 and stars_increment < min_increment:
                    logger.debug(f"Filtered out {repo['name']}: {stars_key} {stars_increment} < {min_increment}")
                    continue
                elif stars_increment == 0:
                    # 增量为 0，可能是没爬取到。记录日志但默认保留（依赖 total_stars 过滤）
                    logger.debug(f"Repo {repo['name']} has 0 {stars_key}, skipping increment filter (trusting total stars)")

            filtered.append(repo)

        logger.info(f"Star filter: {len(repos)} -> {len(filtered)} (removed {len(repos) - len(filtered)})")
        return filtered

    def filter_by_language(self, repos: List[Dict]) -> List[Dict]:
        """根据编程语言过滤项目"""
        if not repos:
            return []

        filtered = []

        for repo in repos:
            language = repo.get('language', '').strip()

            if self.language_whitelist and language not in self.language_whitelist:
                logger.debug(f"Filtered out {repo['name']}: language '{language}' not in whitelist")
                continue

            if self.language_blacklist and language in self.language_blacklist:
                logger.debug(f"Filtered out {repo['name']}: language '{language}' in blacklist")
                continue

            filtered.append(repo)

        logger.info(f"Language filter: {len(repos)} -> {len(filtered)} (removed {len(repos) - len(filtered)})")
        return filtered

    def filter_all(self, repos: List[Dict], time_range: str = 'daily', ignore_thresholds: bool = False) -> List[Dict]:
        """应用所有过滤规则"""
        if not repos:
            return []

        original_count = len(repos)
        logger.info(f"Starting filtering: {original_count} repositories")

        filtered = self.filter_by_stars(repos, time_range, ignore_thresholds)
        filtered = self.filter_by_language(filtered)

        logger.info(f"Filtering complete: {original_count} -> {len(filtered)} (filtered out {original_count - len(filtered)})")
        return filtered
