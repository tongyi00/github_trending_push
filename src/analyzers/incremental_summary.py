"""
增量摘要生成器 - 提供智能缓存和摘要刷新策略
"""

from typing import Any, Dict, Optional
from datetime import datetime, timedelta


class IncrementalSummaryManager:
    """增量摘要管理器"""

    def __init__(self, data_repository, config: Dict[str, Any]):
        self.data_repository = data_repository
        self.cache_expiry_days = config.get('cache_expiry_days', 7)
        self.stars_growth_threshold = config.get('stars_growth_threshold', 0.2)
        self.force_refresh = config.get('force_refresh', False)

    def should_regenerate_summary(self, repo_data: Dict[str, Any]) -> tuple[bool, str]:
        """判断是否需要重新生成摘要"""
        if self.force_refresh:
            return True, "force_refresh"

        repo_name = repo_data.get('name')
        summary_metadata = self.data_repository.get_summary_with_metadata(repo_name)

        if not summary_metadata:
            return True, "no_cache"

        created_at = summary_metadata['created_at']
        cache_age = datetime.now() - created_at

        if cache_age > timedelta(days=self.cache_expiry_days):
            return True, "cache_expired"

        cached_description = summary_metadata.get('description', '')
        current_description = repo_data.get('description', '')
        if cached_description != current_description:
            return True, "description_changed"

        current_stars = repo_data.get('stars', 0)
        cached_stars = self.data_repository.get_latest_stars(repo_name)

        if cached_stars and cached_stars > 0 and current_stars > 0:
            growth_rate = (current_stars - cached_stars) / cached_stars
            if growth_rate >= self.stars_growth_threshold:
                return True, f"stars_growth_{int(growth_rate*100)}%"

        return False, "cache_hit"

    def get_cached_summary(self, repo_name: str) -> Optional[str]:
        """获取缓存的摘要"""
        return self.data_repository.get_latest_summary(repo_name)
