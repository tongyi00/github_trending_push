#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能测试脚本 - 对比同步与异步版本的性能差异
"""
import os
import sys
import time
import asyncio
from pathlib import Path
from loguru import logger
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))
from src.collectors import AsyncScraperTrending, ScraperTrending
from src.analyzers import AsyncAISummarizer


async def test_async_scraper():
    """测试异步爬虫性能"""
    logger.info("=== Testing Async Scraper ===")
    scraper = AsyncScraperTrending(max_concurrent=5)

    start_time = time.time()
    results = await scraper.scrape_all_ranges(['daily'])
    elapsed = time.time() - start_time

    total_repos = sum(len(repos) for repos in results.values())
    logger.info(f"Async Scraper: {total_repos} repos in {elapsed:.2f}s")

    return elapsed, total_repos


def test_sync_scraper():
    """测试同步爬虫性能"""
    logger.info("=== Testing Sync Scraper ===")
    scraper = ScraperTrending()

    start_time = time.time()
    repos = scraper.scrape_trending_by_range(since='daily')
    elapsed = time.time() - start_time

    logger.info(f"Sync Scraper: {len(repos)} repos in {elapsed:.2f}s")

    return elapsed, len(repos)


async def test_async_ai_summarizer(repos):
    """测试异步 AI 摘要生成性能"""
    logger.info("=== Testing Async AI Summarizer ===")

    summarizer = AsyncAISummarizer(max_concurrent=5)

    start_time = time.time()
    results = await summarizer.batch_summarize(repos[:5])
    elapsed = time.time() - start_time

    await summarizer.close()

    logger.info(f"Async AI Summarizer: {len(results)} summaries in {elapsed:.2f}s")

    return elapsed, len(results)


async def main():
    """主测试函数"""
    logger.info("Starting performance comparison tests...")

    # 1. 测试爬虫性能
    sync_scraper_time, sync_repo_count = test_sync_scraper()
    async_scraper_time, async_repo_count = await test_async_scraper()

    scraper_speedup = sync_scraper_time / async_scraper_time if async_scraper_time > 0 else 0

    # 获取项目列表用于 AI 测试
    scraper = ScraperTrending()
    repos = scraper.scrape_trending_by_range(since='daily')

    # 2. 测试 AI 摘要性能（仅异步版本）
    if len(repos) >= 5:
        logger.info("=== Testing Async AI Summarizer ===")
        start_time = time.time()

        summarizer = AsyncAISummarizer(max_concurrent=5)
        results = await summarizer.batch_summarize(repos[:5])
        await summarizer.close()

        async_ai_time = time.time() - start_time
        async_summary_count = len(results)

        logger.info(f"Async AI Summarizer: {async_summary_count} summaries in {async_ai_time:.2f}s")
    else:
        logger.warning("Not enough repos for AI testing")
        async_ai_time = async_summary_count = 0

    # 生成性能测试报告
    logger.info("\n" + "="*60)
    logger.info("PERFORMANCE TEST RESULTS")
    logger.info("="*60)
    logger.info(f"\n📊 Scraper Performance:")
    logger.info(f"  Sync:  {sync_scraper_time:.2f}s ({sync_repo_count} repos)")
    logger.info(f"  Async: {async_scraper_time:.2f}s ({async_repo_count} repos)")
    logger.info(f"  Speedup: {scraper_speedup:.2f}x")

    if async_ai_time > 0:
        logger.info(f"\n🤖 AI Summarizer Performance:")
        logger.info(f"  Async: {async_ai_time:.2f}s ({async_summary_count} summaries)")

    logger.info("\n" + "="*60)

    # 保存报告
    report = f"""# 性能测试报告

生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 测试结果

### 1. 爬虫性能对比

| 版本 | 耗时 | 项目数 | 性能提升 |
|------|------|--------|----------|
| 同步版本 | {sync_scraper_time:.2f}s | {sync_repo_count} | - |
| 异步版本 | {async_scraper_time:.2f}s | {async_repo_count} | {scraper_speedup:.2f}x |

### 2. AI 摘要生成性能

| 版本 | 耗时 | 摘要数 |
|------|------|--------|
| 异步版本 | {async_ai_time:.2f}s | {async_summary_count} |

## 总结

- ✅ 异步爬虫性能提升: **{scraper_speedup:.2f}x**
- ✅ 已全面迁移至异步 AI 摘要生成器

## 优化特性

1. **并发控制**: 使用 Semaphore 限制并发数，避免 API 限流
2. **错误重试**: 自动重试失败的请求，提高成功率
3. **超时控制**: 避免长时间阻塞
4. **资源管理**: 自动管理连接池和会话
"""

    report_path = Path("performance_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.success(f"Performance report saved to {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
