"""
GitHub Trending 爬虫 - 支持每日、每周、每月的trending项目抓取
"""
import os
import time
import json
import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pyquery import PyQuery as pq
from loguru import logger


# 支持的时间范围
TIME_RANGES = ['daily', 'weekly', 'monthly']


class ScraperTrending:
    def __init__(self):
        """初始化爬虫类"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8'
        }

        # 配置重试策略
        self.session = requests.Session()
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
            time.sleep(2)  # 添加延迟避免请求过快

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
            stars = self._parse_number(stars_text)

            # 提取forks数
            forks_element = i("svg.octicon-repo-forked").parent()
            forks_text = forks_element.text().strip()
            forks = self._parse_number(forks_text)

            # 提取今日/本周/本月新增stars
            stars_today_element = i("span.d-inline-block.float-sm-right")
            stars_today_text = stars_today_element.text().strip()
            stars_period = self._parse_number(stars_today_text)

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

    def _parse_number(self, text):
        """
        解析GitHub上的数字格式（如 1.2k -> 1200, 3,456 -> 3456）
        :param text: 包含数字的文本
        :return: 整数
        """
        if not text:
            return 0

        # 移除逗号
        text = text.replace(',', '')

        try:
            # 处理k (千)
            if 'k' in text.lower():
                return int(float(text.lower().replace('k', '')) * 1000)
            # 处理m (百万)
            elif 'm' in text.lower():
                return int(float(text.lower().replace('m', '')) * 1000000)
            else:
                # 尝试提取数字
                import re
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
                return 0
        except:
            return 0

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
            time.sleep(2)  # 添加延迟避免请求过快

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
