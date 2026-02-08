"""
图表生成器 - 使用matplotlib生成趋势分析图表
"""

import base64
from io import BytesIO
from pathlib import Path
from loguru import logger
from typing import List, Dict, Optional

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    logger.warning("matplotlib not installed, chart generation disabled")
    HAS_MATPLOTLIB = False


class ChartGenerator:
    """图表生成器"""

    def __init__(self):
        if HAS_MATPLOTLIB:
            plt.rcParams['figure.figsize'] = (10, 6)
            plt.rcParams['font.size'] = 10
            try:
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
                plt.rcParams['axes.unicode_minus'] = False
            except (KeyError, RuntimeError) as e:
                logger.warning(f"Chinese font not available, using default: {e}")

    def generate_growth_chart(self, projects: List[Dict], output_path: Optional[str] = None) -> Optional[str]:
        """生成Stars增长趋势图（柱状图）"""
        if not HAS_MATPLOTLIB:
            return None

        if not projects:
            logger.warning("No projects data provided for growth chart")
            return None

        names = [p['name'].split('/')[-1][:20] for p in projects[:10]]
        growth = [p['total_growth'] for p in projects[:10]]

        fig, ax = plt.subplots(figsize=(12, 6))
        try:
            bars = ax.barh(names, growth, color='#0366d6')
            ax.set_xlabel('Stars Growth')
            ax.set_title('Top 10 Fastest Growing Projects')
            ax.invert_yaxis()

            for i, (bar, val) in enumerate(zip(bars, growth)):
                ax.text(val, i, f' {val:,}', va='center', fontsize=9)

            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=100, bbox_inches='tight')
                return output_path
            else:
                return self._fig_to_base64()
        finally:
            plt.close(fig)

    def generate_language_pie_chart(self, languages: List[Dict], output_path: Optional[str] = None) -> Optional[str]:
        """生成语言分布饼图"""
        if not HAS_MATPLOTLIB:
            return None

        if not languages:
            logger.warning("No languages data provided for pie chart")
            return None

        top_languages = languages[:8]
        labels = [lang['language'] for lang in top_languages]
        sizes = [lang['total_growth'] for lang in top_languages]

        colors = ['#0366d6', '#28a745', '#ffd33d', '#f66a0a', '#6f42c1', '#d73a49', '#24292e', '#586069']

        fig, ax = plt.subplots(figsize=(10, 8))
        try:
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors[:len(labels)]
            )

            for text in texts:
                text.set_fontsize(11)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
                autotext.set_weight('bold')

            ax.set_title('Language Distribution by Stars Growth', fontsize=14, pad=20)
            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=100, bbox_inches='tight')
                return output_path
            else:
                return self._fig_to_base64()
        finally:
            plt.close(fig)

    def generate_keyword_bar_chart(self, keywords: List[Dict], output_path: Optional[str] = None) -> Optional[str]:
        """生成关键词柱状图"""
        if not HAS_MATPLOTLIB:
            return None

        if not keywords:
            logger.warning("No keywords data provided for bar chart")
            return None

        top_keywords = keywords[:15]
        words = [kw['keyword'] for kw in top_keywords]
        counts = [kw['count'] for kw in top_keywords]

        fig, ax = plt.subplots(figsize=(12, 7))
        try:
            bars = ax.barh(words, counts, color='#28a745')
            ax.set_xlabel('Frequency')
            ax.set_title('Emerging Technology Keywords')
            ax.invert_yaxis()

            for i, (bar, val) in enumerate(zip(bars, counts)):
                ax.text(val, i, f' {val}', va='center', fontsize=9)

            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=100, bbox_inches='tight')
                return output_path
            else:
                return self._fig_to_base64()
        finally:
            plt.close(fig)

    def generate_category_chart(self, categories: List[Dict], output_path: Optional[str] = None) -> Optional[str]:
        """生成分类占比图"""
        if not HAS_MATPLOTLIB:
            return None

        if not categories:
            logger.warning("No categories data provided for category chart")
            return None

        top_categories = categories[:10]
        labels = [cat['category'] for cat in top_categories]
        sizes = [cat['count'] for cat in top_categories]

        colors = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#F38181', '#AA96DA', '#FCBAD3', '#FFFFD2', '#A8D8EA', '#FFAAA7', '#FFD3B4']

        fig, ax = plt.subplots(figsize=(10, 8))
        try:
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors[:len(labels)]
            )

            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(9)
                autotext.set_weight('bold')

            ax.set_title('Project Category Distribution', fontsize=14, pad=20)
            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=100, bbox_inches='tight')
                return output_path
            else:
                return self._fig_to_base64()
        finally:
            plt.close(fig)

    def generate_all_charts(self, report_data: Dict, output_dir: Optional[str] = None) -> Dict[str, str]:
        """生成所有图表"""
        charts = {}

        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            charts['growth_chart'] = self.generate_growth_chart(report_data['top_growing'], str(output_path / 'growth.png'))
            charts['language_chart'] = self.generate_language_pie_chart(report_data['language_ranking'], str(output_path / 'language.png'))
            charts['keyword_chart'] = self.generate_keyword_bar_chart(report_data['emerging_keywords'], str(output_path / 'keywords.png'))
            if report_data.get('category_distribution'):
                charts['category_chart'] = self.generate_category_chart(report_data['category_distribution'], str(output_path / 'category.png'))
        else:
            charts['growth_chart'] = self.generate_growth_chart(report_data['top_growing'])
            charts['language_chart'] = self.generate_language_pie_chart(report_data['language_ranking'])
            charts['keyword_chart'] = self.generate_keyword_bar_chart(report_data['emerging_keywords'])
            if report_data.get('category_distribution'):
                charts['category_chart'] = self.generate_category_chart(report_data['category_distribution'])

        logger.info(f"Generated {len(charts)} charts")
        return charts

    def _fig_to_base64(self) -> str:
        """将matplotlib图表转换为base64字符串"""
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        return f"data:image/png;base64,{image_base64}"


def create_chart_generator() -> ChartGenerator:
    """创建图表生成器实例"""
    return ChartGenerator()
