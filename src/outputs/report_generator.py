"""
报告生成器 - 生成HTML/PDF趋势分析报告
"""

import html
from pathlib import Path
from loguru import logger
from typing import Dict, Optional


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        self.template_path = Path(__file__).parent.parent.parent / "templates/report_template.html"

    def generate_html_report(self, report_data: Dict, charts: Dict, output_path: Optional[str] = None) -> str:
        """生成HTML报告"""
        if not self.template_path.exists():
            logger.error(f"Template not found: {self.template_path}")
            return ""

        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        html_content = self._fill_template(template, report_data, charts)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML report saved to {output_path}")

        return html_content

    def _fill_template(self, template: str, report_data: Dict, charts: Dict) -> str:
        """填充HTML模板"""
        time_range_names = {'daily': 'Daily Trending', 'weekly': 'Weekly Trending', 'monthly': 'Monthly Trending'}
        title = f"{time_range_names.get(report_data['time_range'], 'Trending')} - Last {report_data['period_days']} Days"

        result = template.replace("{{TITLE}}", title)
        result = result.replace("{{GENERATED_AT}}", report_data['generated_at'])

        stats_cards_html = self._generate_stats_cards(report_data)
        result = result.replace("{{STATS_CARDS}}", stats_cards_html)

        result = result.replace("{{GROWTH_CHART}}", charts.get('growth_chart', ''))
        result = result.replace("{{LANGUAGE_CHART}}", charts.get('language_chart', ''))
        result = result.replace("{{KEYWORD_CHART}}", charts.get('keyword_chart', ''))

        top_projects_html = self._generate_top_projects_html(report_data['top_growing'])
        result = result.replace("{{TOP_PROJECTS}}", top_projects_html)

        keyword_tags_html = self._generate_keyword_tags(report_data['emerging_keywords'][:20])
        result = result.replace("{{KEYWORD_TAGS}}", keyword_tags_html)

        category_section = ""
        if report_data.get('category_distribution'):
            category_chart = charts.get('category_chart', '')
            category_section = f'''
            <div class="section">
                <h2 class="section-title">🏷️ Project Category Distribution</h2>
                <div class="chart-container">
                    <img src="{category_chart}" alt="Category Chart">
                </div>
            </div>
            '''
        result = result.replace("{{CATEGORY_SECTION}}", category_section)

        comparison_html = self._generate_comparison_cards(report_data['period_comparison'])
        result = result.replace("{{COMPARISON_CARDS}}", comparison_html)

        return result

    def _generate_stats_cards(self, report_data: Dict) -> str:
        """生成统计卡片HTML"""
        comparison = report_data['period_comparison']
        current = comparison['current_period']['stats']
        growth = comparison['growth_rate']

        cards = []

        stats = [
            ('Total Projects', current['total_projects'], growth.get('total_projects', 0)),
            ('Total Stars', f"{current['total_stars']:,}", growth.get('total_stars', 0)),
            ('Stars Growth', f"{current['total_growth']:,}", growth.get('total_growth', 0)),
            ('Avg Stars/Project', f"{current['avg_stars']:,}", growth.get('avg_stars', 0))
        ]

        for label, value, growth_val in stats:
            growth_class = 'positive' if growth_val > 0 else 'negative' if growth_val < 0 else ''
            growth_symbol = '↑' if growth_val > 0 else '↓' if growth_val < 0 else '→'
            growth_html = f'<div class="stat-growth {growth_class}">{growth_symbol} {abs(growth_val):.1f}% vs previous period</div>' if growth_val != 0 else ''

            card = f'''
            <div class="stat-card">
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
                {growth_html}
            </div>
            '''
            cards.append(card)

        return ''.join(cards)

    def _generate_top_projects_html(self, projects: list) -> str:
        """生成Top项目列表HTML"""
        items = []
        for idx, proj in enumerate(projects[:10], 1):
            # 转义所有用户输入防止XSS
            safe_url = html.escape(proj['url'])
            safe_name = html.escape(proj['name'])
            safe_description = html.escape(proj['description'][:150])
            safe_language = html.escape(proj['language'])

            item = f'''
            <li class="project-item">
                <div class="project-header">
                    <div class="project-rank">{idx}</div>
                    <a href="{safe_url}" class="project-name" target="_blank">{safe_name}</a>
                </div>
                <p style="color: #586069; margin: 5px 0 10px 47px;">{safe_description}...</p>
                <div class="project-stats">
                    <span>⭐ {proj['total_stars']:,} stars</span>
                    <span>📈 +{proj['total_growth']:,} growth</span>
                    <span>💻 {safe_language}</span>
                    <span>📊 {proj['appearances']} appearances</span>
                </div>
            </li>
            '''
            items.append(item)

        return ''.join(items)

    def _generate_keyword_tags(self, keywords: list) -> str:
        """生成关键词标签HTML"""
        tags = []
        for kw in keywords:
            safe_keyword = html.escape(kw["keyword"])
            tag = f'<span class="keyword-tag">{safe_keyword} ({kw["count"]})</span>'
            tags.append(tag)
        return ''.join(tags)

    def _generate_comparison_cards(self, comparison: Dict) -> str:
        """生成对比卡片HTML"""
        current = comparison['current_period']
        previous = comparison['previous_period']

        current_card = f'''
        <div class="comparison-card">
            <h3>Current Period ({current['start_date']} ~ {current['end_date']})</h3>
            <div class="comparison-item">
                <span>Total Projects</span>
                <strong>{current['stats']['total_projects']}</strong>
            </div>
            <div class="comparison-item">
                <span>Total Stars</span>
                <strong>{current['stats']['total_stars']:,}</strong>
            </div>
            <div class="comparison-item">
                <span>Stars Growth</span>
                <strong>{current['stats']['total_growth']:,}</strong>
            </div>
            <div class="comparison-item">
                <span>Avg Stars/Project</span>
                <strong>{current['stats']['avg_stars']:,}</strong>
            </div>
        </div>
        '''

        previous_card = f'''
        <div class="comparison-card">
            <h3>Previous Period ({previous['start_date']} ~ {previous['end_date']})</h3>
            <div class="comparison-item">
                <span>Total Projects</span>
                <strong>{previous['stats']['total_projects']}</strong>
            </div>
            <div class="comparison-item">
                <span>Total Stars</span>
                <strong>{previous['stats']['total_stars']:,}</strong>
            </div>
            <div class="comparison-item">
                <span>Stars Growth</span>
                <strong>{previous['stats']['total_growth']:,}</strong>
            </div>
            <div class="comparison-item">
                <span>Avg Stars/Project</span>
                <strong>{previous['stats']['avg_stars']:,}</strong>
            </div>
        </div>
        '''

        return current_card + previous_card


def create_report_generator() -> ReportGenerator:
    """创建报告生成器实例"""
    return ReportGenerator()
