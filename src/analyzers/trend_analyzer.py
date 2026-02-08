"""
趋势分析器 - 生成GitHub项目趋势分析报告
"""

import re
from loguru import logger
from typing import List, Dict
from collections import Counter
from datetime import datetime, timedelta


class TrendAnalyzer:
    """趋势分析器"""

    DEFAULT_QUERY_LIMIT = 1000

    def __init__(self, data_repository, classifier=None, query_limit: int = None):
        self.data_repository = data_repository
        self.classifier = classifier
        self.query_limit = query_limit or self.DEFAULT_QUERY_LIMIT

    def get_top_growing_projects(self, time_range: str = 'daily', limit: int = 10, days: int = 7) -> List[Dict]:
        """获取增长最快的项目（Top N）"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        records = self.data_repository.get_trending_records(
            time_range=time_range,
            start_date=start_date,
            end_date=end_date,
            limit=self.query_limit
        )

        projects_growth = {}
        for record in records:
            name = record['name']
            if name not in projects_growth:
                projects_growth[name] = {
                    'name': name,
                    'url': record['url'],
                    'description': record['description'],
                    'language': record['language'],
                    'total_stars': record['stars'],
                    'total_growth': 0,
                    'appearances': 0
                }
            projects_growth[name]['total_growth'] += record['stars_increment']
            projects_growth[name]['appearances'] += 1

        sorted_projects = sorted(
            projects_growth.values(),
            key=lambda x: x['total_growth'],
            reverse=True
        )

        return sorted_projects[:limit]

    def get_language_ranking(self, time_range: str = 'daily', days: int = 7) -> List[Dict]:
        """获取热门语言排行榜"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        records = self.data_repository.get_trending_records(
            time_range=time_range,
            start_date=start_date,
            end_date=end_date,
            limit=self.query_limit
        )

        language_stats = {}
        for record in records:
            lang = record['language'] or 'Unknown'
            if lang not in language_stats:
                language_stats[lang] = {
                    'language': lang,
                    'project_count': 0,
                    'total_stars': 0,
                    'total_growth': 0
                }
            language_stats[lang]['project_count'] += 1
            language_stats[lang]['total_stars'] += record['stars']
            language_stats[lang]['total_growth'] += record['stars_increment']

        sorted_languages = sorted(
            language_stats.values(),
            key=lambda x: x['total_growth'],
            reverse=True
        )

        return sorted_languages

    def extract_emerging_keywords(self, time_range: str = 'daily', days: int = 7, top_n: int = 20) -> List[Dict]:
        """使用TF-IDF提取新兴技术关键词"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        records = self.data_repository.get_trending_records(
            time_range=time_range,
            start_date=start_date,
            end_date=end_date,
            limit=self.query_limit
        )

        all_text = []
        for record in records:
            text = f"{record['name']} {record['description']}"
            all_text.append(text.lower())

        word_freq = Counter()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}

        for text in all_text:
            words = re.findall(r'\b[a-z]{3,}\b', text)
            for word in words:
                if word not in stop_words:
                    word_freq[word] += 1

        tech_keywords = {
            'ai', 'ml', 'llm', 'gpt', 'chatbot', 'neural', 'deep', 'learning',
            'react', 'vue', 'angular', 'next', 'nuxt', 'svelte',
            'docker', 'kubernetes', 'k8s', 'terraform', 'ansible',
            'python', 'javascript', 'typescript', 'rust', 'go', 'golang',
            'api', 'rest', 'graphql', 'grpc', 'websocket',
            'database', 'sql', 'nosql', 'postgresql', 'mysql', 'mongodb', 'redis',
            'blockchain', 'web3', 'crypto', 'nft', 'ethereum',
            'security', 'encryption', 'authentication', 'oauth',
            'cloud', 'aws', 'azure', 'gcp', 'serverless',
            'devops', 'ci', 'cd', 'pipeline', 'monitoring'
        }

        tech_word_freq = {word: count for word, count in word_freq.items() if word in tech_keywords}

        keywords = [
            {'keyword': word, 'count': count, 'weight': count / len(all_text) if all_text else 0}
            for word, count in sorted(tech_word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
        ]

        return keywords

    def get_category_distribution(self, time_range: str = 'daily', days: int = 7) -> List[Dict]:
        """获取分类占比分析（使用classifier）"""
        if not self.classifier:
            logger.warning("Classifier not available, skipping category distribution")
            return []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        records = self.data_repository.get_trending_records(
            time_range=time_range,
            start_date=start_date,
            end_date=end_date,
            limit=self.query_limit
        )

        category_stats = Counter()
        for record in records:
            tags = self.classifier.classify(record, max_tags=3)
            for tag in tags:
                if tag['source'] in ['keyword', 'ai_summary']:
                    category_stats[tag['name']] += 1

        total = sum(category_stats.values())
        distribution = [
            {
                'category': category,
                'count': count,
                'percentage': round(count / total * 100, 1) if total > 0 else 0
            }
            for category, count in category_stats.most_common(15)
        ]

        return distribution

    def compare_periods(self, time_range: str = 'daily', current_days: int = 7, previous_days: int = 7) -> Dict:
        """历史数据对比（周环比/月环比）"""
        current_end = datetime.now()
        current_start = current_end - timedelta(days=current_days)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=previous_days)

        current_records = self.data_repository.get_trending_records(
            time_range=time_range,
            start_date=current_start,
            end_date=current_end,
            limit=1000
        )

        previous_records = self.data_repository.get_trending_records(
            time_range=time_range,
            start_date=previous_start,
            end_date=previous_end,
            limit=1000
        )

        current_stats = self._calculate_stats(current_records)
        previous_stats = self._calculate_stats(previous_records)

        comparison = {
            'current_period': {
                'start_date': current_start.strftime('%Y-%m-%d'),
                'end_date': current_end.strftime('%Y-%m-%d'),
                'stats': current_stats
            },
            'previous_period': {
                'start_date': previous_start.strftime('%Y-%m-%d'),
                'end_date': previous_end.strftime('%Y-%m-%d'),
                'stats': previous_stats
            },
            'growth_rate': {}
        }

        for key in current_stats:
            if previous_stats.get(key, 0) > 0:
                growth = ((current_stats[key] - previous_stats[key]) / previous_stats[key]) * 100
                comparison['growth_rate'][key] = round(growth, 1)
            else:
                comparison['growth_rate'][key] = 0

        return comparison

    def _calculate_stats(self, records: List[Dict]) -> Dict:
        """计算统计数据"""
        total_projects = len(set(r['name'] for r in records))
        total_stars = sum(r['stars'] for r in records)
        total_growth = sum(r['stars_increment'] for r in records)
        avg_stars = round(total_stars / total_projects) if total_projects > 0 else 0

        return {
            'total_projects': total_projects,
            'total_stars': total_stars,
            'total_growth': total_growth,
            'avg_stars': avg_stars
        }

    def generate_report_data(self, time_range: str = 'daily', days: int = 7) -> Dict:
        """生成完整的报告数据"""
        logger.info(f"Generating trend report for {time_range} range, last {days} days")

        report_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'time_range': time_range,
            'period_days': days,
            'top_growing': self.get_top_growing_projects(time_range, limit=10, days=days),
            'language_ranking': self.get_language_ranking(time_range, days=days),
            'emerging_keywords': self.extract_emerging_keywords(time_range, days=days, top_n=20),
            'category_distribution': self.get_category_distribution(time_range, days=days),
            'period_comparison': self.compare_periods(time_range, current_days=days, previous_days=days)
        }

        logger.info(f"Report data generated: {len(report_data['top_growing'])} top projects, {len(report_data['language_ranking'])} languages")
        return report_data


def create_analyzer(data_repository, classifier=None) -> TrendAnalyzer:
    """创建趋势分析器实例"""
    return TrendAnalyzer(data_repository, classifier)
