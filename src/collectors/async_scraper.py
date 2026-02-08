#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异步 GitHub Trending 爬虫 - 使用 aiohttp 提升性能
"""

import ssl
import asyncio
import aiohttp
from datetime import datetime
from loguru import logger
from pyquery import PyQuery as pq
from typing import List, Dict, Optional

from ..constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_CRAWL_DELAY
from .utils import parse_github_number

try:
    from ..infrastructure.rate_limiter import AdaptiveRateLimiter
except ImportError:
    logger.warning("AdaptiveRateLimiter not found, rate limiting disabled")
    AdaptiveRateLimiter = None

try:
    from ..infrastructure.robots_checker import check_robots_permission, get_recommended_delay
except ImportError:
    logger.warning("robots_checker module not found, robots.txt checking disabled")
    def check_robots_permission(url): return True
    def get_recommended_delay(url): return None


class AsyncScraperTrending:
    """异步 GitHub Trending 爬虫"""

    def __init__(self, max_concurrent: int = 5):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8'
        }
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_SECONDS)
        self.ssl_context = ssl.create_default_context()  # Explicit SSL verification
        self.rate_limiter = AdaptiveRateLimiter(initial_rate=2.0, min_interval=0.5, max_interval=5.0) if AdaptiveRateLimiter else None
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建复用的ClientSession"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, ssl=self.ssl_context)
            self._session = aiohttp.ClientSession(connector=connector)
            logger.info("Created new aiohttp ClientSession with SSL verification")
        return self._session

    async def close(self):
        """关闭ClientSession释放资源"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Closed aiohttp ClientSession")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    async def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """异步获取网页内容，支持重试和速率限制"""
        session = await self._get_session()

        for attempt in range(retries):
            try:
                # 应用速率限制
                if self.rate_limiter:
                    await self.rate_limiter.wait_async()

                async with self.semaphore:
                    async with session.get(url, headers=self.headers, timeout=self.timeout) as response:
                        if response.status == 200:
                            if self.rate_limiter:
                                await self.rate_limiter.record_success_async()
                            return await response.text()
                        elif response.status == 429:
                            logger.warning(f"Rate limit hit for {url}, attempt {attempt + 1}/{retries}")
                            if self.rate_limiter:
                                await self.rate_limiter.record_error_async(is_rate_limit=True)
                        else:
                            logger.warning(f"HTTP {response.status} for {url}, attempt {attempt + 1}/{retries}")
                            if self.rate_limiter:
                                await self.rate_limiter.record_error_async()
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url}, attempt {attempt + 1}/{retries}")
                if self.rate_limiter:
                    await self.rate_limiter.record_error_async()
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}, attempt {attempt + 1}/{retries}")
                if self.rate_limiter:
                    await self.rate_limiter.record_error_async()

            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)

        return None

    def parse_trending_page(self, html: str) -> List[Dict]:
        """解析 trending 页面（同步解析）"""
        if not html:
            return []

        repos = []
        doc = pq(html)
        items = doc('article.Box-row').items()

        for item in items:
            try:
                repo_info = {}
                h2 = item.find('h2 a')
                repo_info['name'] = h2.attr('href').strip('/') if h2.attr('href') else ''
                repo_info['url'] = f"https://github.com{h2.attr('href')}" if h2.attr('href') else ''

                desc_elem = item.find('p')
                repo_info['description'] = desc_elem.text().strip() if desc_elem else ''

                lang_elem = item.find('span[itemprop="programmingLanguage"]')
                repo_info['language'] = lang_elem.text().strip() if lang_elem else ''

                # Stars
                # Selector strategy: Find the link to stargazers, which contains the count
                stars_link = item.find(f'a[href="/{repo_info["name"]}/stargazers"]')
                if stars_link:
                    stars_text = stars_link.text().strip()
                    repo_info['stars'] = parse_github_number(stars_text)
                else:
                    # Fallback: try finding the svg and getting its parent text
                    stars_elem = item.find('svg.octicon-star').parent()
                    stars_text = stars_elem.text().strip() if stars_elem else '0'
                    repo_info['stars'] = parse_github_number(stars_text)

                forks_elem = item.find('svg.octicon-repo-forked').parent()
                forks_text = forks_elem.text().strip() if forks_elem else '0'
                repo_info['forks'] = parse_github_number(forks_text)

                stars_today_elem = item.find('span.d-inline-block.float-sm-right')
                stars_today_text = stars_today_elem.text().strip() if stars_today_elem else '0'
                repo_info['stars_daily'] = parse_github_number(stars_today_text)

                repo_info['updated_at'] = datetime.now().strftime('%Y-%m-%d')

                repos.append(repo_info)

            except Exception as e:
                logger.error(f"Error parsing repository item: {e}")
                continue

        return repos

    async def scrape_trending_by_range(self, since: str = 'daily', language: str = '') -> List[Dict]:
        """异步爬取指定时间范围的 trending 项目"""
        if language:
            url = f'https://github.com/trending/{language}?since={since}'
        else:
            url = f'https://github.com/trending?since={since}'

        # 检查 robots.txt 权限
        if not check_robots_permission(url):
            logger.error(f"Robots.txt disallows crawling: {url}")
            return []

        # 获取建议的爬取延迟
        recommended_delay = get_recommended_delay(url)
        if recommended_delay:
            logger.info(f"Applying robots.txt recommended delay: {recommended_delay}s")
            await asyncio.sleep(recommended_delay)

        logger.info(f"Scraping trending ({since}): {url}")

        html = await self.fetch_page(url)

        if html:
            repos = self.parse_trending_page(html)
            logger.info(f"Found {len(repos)} repositories for {since}")
            return repos
        else:
            logger.error(f"Failed to fetch trending page for {since}")
            return []

    async def scrape_all_ranges(self, time_ranges: List[str] = None) -> Dict[str, List[Dict]]:
        """异步并发爬取多个时间范围的 trending 项目"""
        if time_ranges is None:
            time_ranges = ['daily', 'weekly', 'monthly']

        try:
            tasks = [self.scrape_trending_by_range(since=time_range) for time_range in time_ranges]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_data = {}
            for time_range, result in zip(time_ranges, results):
                if isinstance(result, Exception):
                    logger.error(f"Error scraping {time_range}: {result}")
                    all_data[time_range] = []
                else:
                    all_data[time_range] = result

            # 输出速率限制器统计信息
            if self.rate_limiter:
                stats = self.rate_limiter.get_stats()
                logger.info(f"Rate limiter stats: {stats}")

            return all_data
        except Exception as e:
            logger.error(f"Error in scrape_all_ranges: {e}")
            raise
