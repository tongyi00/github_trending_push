"""
自适应速率限制器 - 智能控制API请求频率
"""
import time
import asyncio
import threading
from typing import Dict, Optional, Any
from loguru import logger
from collections import deque


class AdaptiveRateLimiter:
    """自适应速率限制器，根据API响应动态调整请求速率"""

    def __init__(self, initial_rate: float = 1.0, min_interval: float = 0.1, max_interval: float = 10.0):
        """
        初始化速率限制器
        :param initial_rate: 初始请求速率（请求/秒）
        :param min_interval: 最小请求间隔（秒）
        :param max_interval: 最大请求间隔（秒）
        """
        self._sync_lock = threading.Lock()
        self._async_lock = None  # 延迟初始化，避免事件循环问题
        self._async_lock_init_lock = threading.Lock()  # 保护异步锁初始化
        self.current_interval = 1.0 / initial_rate
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.last_request_time = 0.0
        self.success_count = 0
        self.error_count = 0
        self.request_history = deque(maxlen=100)

    def _get_async_lock(self):
        """延迟初始化异步锁，避免事件循环问题（线程安全）"""
        if self._async_lock is None:
            with self._async_lock_init_lock:
                if self._async_lock is None:
                    self._async_lock = asyncio.Lock()
        return self._async_lock

    def wait(self):
        """同步等待直到可以发送下一个请求（线程安全）"""
        with self._sync_lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.current_interval:
                sleep_time = self.current_interval - elapsed
                logger.debug(f"Rate limiting: waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
            self.last_request_time = time.time()

    async def wait_async(self):
        """异步等待直到可以发送下一个请求（异步安全）"""
        async with self._get_async_lock():
            elapsed = time.time() - self.last_request_time
            if elapsed < self.current_interval:
                sleep_time = self.current_interval - elapsed
                logger.debug(f"Rate limiting: waiting {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
            self.last_request_time = time.time()

    def record_success(self):
        """记录成功请求，逐步提高速率（同步版本）"""
        with self._sync_lock:
            self.success_count += 1
            self.request_history.append(('success', time.time()))

            if self.success_count >= 10:
                self.current_interval = max(self.min_interval, self.current_interval * 0.9)
                logger.debug(f"Rate limit decreased to {self.current_interval:.2f}s (faster)")
                self.success_count = 0

    async def record_success_async(self):
        """记录成功请求，逐步提高速率（异步版本）"""
        async with self._get_async_lock():
            self.success_count += 1
            self.request_history.append(('success', time.time()))

            if self.success_count >= 10:
                self.current_interval = max(self.min_interval, self.current_interval * 0.9)
                logger.debug(f"Rate limit decreased to {self.current_interval:.2f}s (faster)")
                self.success_count = 0

    def record_error(self, is_rate_limit: bool = False):
        """记录错误请求，降低速率（同步版本）"""
        with self._sync_lock:
            self.error_count += 1
            self.request_history.append(('error', time.time()))

            if is_rate_limit:
                self.current_interval = min(self.max_interval, self.current_interval * 2.0)
                logger.warning(f"Rate limit hit! Interval increased to {self.current_interval:.2f}s")
                self.error_count = 0
            elif self.error_count >= 3:
                self.current_interval = min(self.max_interval, self.current_interval * 1.5)
                logger.warning(f"Multiple errors detected. Interval increased to {self.current_interval:.2f}s")
                self.error_count = 0

    async def record_error_async(self, is_rate_limit: bool = False):
        """记录错误请求，降低速率（异步版本）"""
        async with self._get_async_lock():
            self.error_count += 1
            self.request_history.append(('error', time.time()))

            if is_rate_limit:
                self.current_interval = min(self.max_interval, self.current_interval * 2.0)
                logger.warning(f"Rate limit hit! Interval increased to {self.current_interval:.2f}s")
                self.error_count = 0
            elif self.error_count >= 3:
                self.current_interval = min(self.max_interval, self.current_interval * 1.5)
                logger.warning(f"Multiple errors detected. Interval increased to {self.current_interval:.2f}s")
                self.error_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取速率限制器统计信息"""
        recent_success = sum(1 for status, _ in self.request_history if status == 'success')
        recent_errors = sum(1 for status, _ in self.request_history if status == 'error')
        total = len(self.request_history)

        return {
            'current_interval': f"{self.current_interval:.2f}s",
            'current_rate': f"{1.0 / self.current_interval:.2f} req/s",
            'recent_success': recent_success,
            'recent_errors': recent_errors,
            'success_rate': f"{(recent_success / total * 100):.1f}%" if total > 0 else "N/A"
        }


class RateLimiterManager:
    """管理多个API端点的速率限制器"""

    def __init__(self):
        self.limiters: Dict[str, AdaptiveRateLimiter] = {}

    def get_limiter(self, endpoint: str, **kwargs) -> AdaptiveRateLimiter:
        """获取或创建指定端点的速率限制器"""
        if endpoint not in self.limiters:
            self.limiters[endpoint] = AdaptiveRateLimiter(**kwargs)
            logger.info(f"Created rate limiter for endpoint: {endpoint}")
        return self.limiters[endpoint]

    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有端点的统计信息"""
        return {endpoint: limiter.get_stats() for endpoint, limiter in self.limiters.items()}
