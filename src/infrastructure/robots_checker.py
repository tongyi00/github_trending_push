"""
Robots.txt 检查器 - 确保爬虫遵守网站爬取规则
"""
import threading
import requests
from functools import lru_cache
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from loguru import logger
from typing import Dict, Optional


class RobotsChecker:
    """Robots.txt 检查器，缓存并验证爬取权限"""

    def __init__(self, user_agent: str = "Mozilla/5.0"):
        self.user_agent = user_agent

    def _get_robots_url(self, url: str) -> str:
        """从URL提取robots.txt地址"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    @lru_cache(maxsize=128)
    def _get_parser(self, base_url: str) -> Optional[RobotFileParser]:
        """获取或创建robots.txt解析器"""
        robots_url = self._get_robots_url(base_url)
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            parser.read()
            logger.info(f"Loaded robots.txt from {robots_url}")
            return parser
        except Exception as e:
            logger.warning(f"Failed to load robots.txt from {robots_url}: {e}")
            logger.info(f"Assuming crawling is allowed for {base_url}")
            return None

    def can_fetch(self, url: str) -> bool:
        """检查是否允许爬取指定URL"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        parser = self._get_parser(base_url)

        if parser is None:
            return True

        allowed = parser.can_fetch(self.user_agent, url)

        if not allowed:
            logger.warning(f"Robots.txt disallows fetching: {url}")
        else:
            logger.debug(f"Robots.txt allows fetching: {url}")

        return allowed

    def get_crawl_delay(self, url: str) -> Optional[float]:
        """获取建议的爬取延迟（秒）"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        parser = self._get_parser(base_url)

        if parser is None:
            return None

        delay = parser.crawl_delay(self.user_agent)
        if delay:
            logger.info(f"Robots.txt suggests crawl delay: {delay}s for {base_url}")

        return delay


# 全局实例和锁
_robots_checker: Optional[RobotsChecker] = None
_robots_checker_lock = threading.Lock()


def get_robots_checker(user_agent: str = "Mozilla/5.0") -> RobotsChecker:
    """Factory function to get or create a RobotsChecker instance (thread-safe)"""
    global _robots_checker
    if _robots_checker is None or _robots_checker.user_agent != user_agent:
        with _robots_checker_lock:
            if _robots_checker is None or _robots_checker.user_agent != user_agent:
                _robots_checker = RobotsChecker(user_agent)
    return _robots_checker


def check_robots_permission(url: str) -> bool:
    """全局函数：检查robots.txt权限"""
    return get_robots_checker().can_fetch(url)


def get_recommended_delay(url: str) -> Optional[float]:
    """全局函数：获取建议延迟"""
    return get_robots_checker().get_crawl_delay(url)
