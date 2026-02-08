"""
GitHub Trending 爬虫 - 支持每日、每周、每月的trending项目抓取
"""
import os
import re
import time
import json
import datetime
import requests
from loguru import logger
from pyquery import PyQuery as pq
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from ..constants import DEFAULT_CRAWL_DELAY
from .utils import parse_github_number

try:
    from ..infrastructure.robots_checker import check_robots_permission, get_recommended_delay
except ImportError:
    logger.warning("robots_checker module not found, robots.txt checking disabled")
    def check_robots_permission(url): return True
    def get_recommended_delay(url): return None


# 支持的时间范围
TIME_RANGES = ['daily', 'weekly', 'monthly']


class ScraperTrending:
    def __init__(self):
        """初始化爬虫类"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8'
        }

        # 时间范围映射
        self.time_ranges = {
            'daily': 'daily',
            'weekly': 'weekly',
            'monthly': 'monthly'
        }

        # 配置重试策略
        self.session = requests.Session()
        self.session.verify = True  # Explicit SSL verification
        retries = Retry(total=10, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def scrape_all_ranges(self, output_file='data/trending.json'):
        """爬取所有时间范围的trending数据（每日、每周、每月）"""
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        all_data = {}

        for range_name, since_param in self.time_ranges.items():
            logger.info(f"Scraping {range_name} trending repositories...")
            repos = self.scrape_trending_by_range(since_param)

            # 按新增stars数降序排序
            repos_sorted = sorted(repos, key=lambda x: x.get(f'stars_{since_param}', 0), reverse=True)

            # 转换为 {项目名: 项目数据} 的字典格式
            repos_dict = {repo['name']: repo for repo in repos_sorted}

            # 按新的结构组织数据: {时间范围: {日期: {项目}}}
            all_data[range_name] = {
                current_date: repos_dict
            }

            logger.info(f"Completed {range_name} trending, found {len(repos)} repositories")
            time.sleep(DEFAULT_CRAWL_DELAY)

        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        logger.info(f"All data saved to {output_file}")
        return all_data

    def scrape_trending_by_range(self, since='daily', language=''):
        """
        根据时间范围爬取trending项目
        :param since: 时间范围 - 'daily'(每日), 'weekly'(每周), 'monthly'(每月)
        :param language: 编程语言筛选，留空表示所有语言
        :return: 返回项目列表
        """
        # 构造URL，根据是否指定语言添加路径
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
            time.sleep(recommended_delay)

        logger.info(f"Fetching: {url}")

        try:
            # 使用带重试的session发送请求，并增加超时时间到30秒
            r = self.session.get(url, headers=self.headers, timeout=30)
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return []

        d = pq(r.content)
        items = d('div.Box article.Box-row')

        if not items:
            logger.warning(f"No items found for {since}")
            return []

        repositories = []

        # 遍历每个trending项目
        for item in items:
            i = pq(item)

            # 提取项目名称和URL
            title = i("h2.h3 a").text().strip().replace('\n', '').replace(' ', '')
            url_path = i("h2.h3 a").attr("href")

            if not url_path:
                continue

            url = "https://github.com" + url_path

            # 提取描述
            description = i("p.col-9").text().strip()

            # 提取编程语言
            language_span = i("span[itemprop='programmingLanguage']").text().strip()

            # 提取stars总数
            stars_element = i("svg.octicon-star").parent()
            stars_text = stars_element.text().strip()
            stars = parse_github_number(stars_text)

            # 提取forks数
            forks_element = i("svg.octicon-repo-forked").parent()
            forks_text = forks_element.text().strip()
            forks = parse_github_number(forks_text)

            # 提取今日/本周/本月新增stars
            stars_today_element = i("span.d-inline-block.float-sm-right")
            stars_today_text = stars_today_element.text().strip()
            stars_period = parse_github_number(stars_today_text)

            repo_data = {
                'name': title,
                'url': url,
                'description': description,
                'language': language_span if language_span else 'Unknown',
                'stars': stars,
                'forks': forks,
                f'stars_{since}': stars_period,  # stars_daily, stars_weekly, stars_monthly
                'updated_at': datetime.datetime.now().strftime("%Y-%m-%d"),  # Trending页面通常不显示更新时间，使用当天日期作为默认值
            }

            repositories.append(repo_data)

        logger.info(f"Successfully scraped {len(repositories)} repositories")
        return repositories

    def scrape_by_languages(self, languages=None, since='daily', output_file='data/trending.json'):
        """
        按语言爬取trending项目
        :param languages: 语言列表，None表示使用默认列表
        :param since: 时间范围 - 'daily', 'weekly', 'monthly'
        :param output_file: 输出JSON文件路径
        """
        if languages is None:
            languages = ['python', 'javascript', 'go', 'java', 'c++', 'rust', 'typescript']

        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        time_range_cn = {'daily': '每日', 'weekly': '每周', 'monthly': '每月'}
        logger.info(f"Scraping {time_range_cn.get(since, since)} trending for {len(languages)} languages...")

        all_data = {
            'generated_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'time_range': since,
            'languages': {}
        }

        for language in languages:
            logger.info(f"Scraping {language}...")
            repos = self.scrape_trending_by_range(since=since, language=language)
            all_data['languages'][language] = repos
            time.sleep(DEFAULT_CRAWL_DELAY)

        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Data saved to {output_file}")
        return all_data


# 使用示例
if __name__ == '__main__':
    scraper = ScraperTrending()

    # 示例1: 爬取所有时间范围（每日、每周、每月）的trending，保存到data/trending.json
    scraper.scrape_all_ranges(output_file='data/trending.json')
