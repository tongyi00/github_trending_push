"""
GitHub项目分类器 - 基于关键词匹配和AI分类的混合方法
"""

from loguru import logger
from typing import Any, Dict, List, Optional

class ProjectClassifier:
    """项目分类器"""

    DEFAULT_CATEGORIES = {
        'AI/ML': {
            'keywords': ['ai', 'ml', 'machine learning', 'deep learning', 'neural', 'llm', 'gpt', 'chatbot', 'openai', 'langchain', 'transformers', 'pytorch', 'tensorflow', 'stable diffusion', 'computer vision', 'nlp', 'bert', 'llama'],
            'color': '#FF6B6B',
            'icon': '🤖'
        },
        'Web框架': {
            'keywords': ['react', 'vue', 'angular', 'next.js', 'nuxt', 'svelte', 'flask', 'django', 'fastapi', 'express', 'nest.js', 'spring boot', 'laravel', 'rails'],
            'color': '#4ECDC4',
            'icon': '🌐'
        },
        'DevOps': {
            'keywords': ['docker', 'kubernetes', 'k8s', 'jenkins', 'ci/cd', 'terraform', 'ansible', 'prometheus', 'grafana', 'nginx', 'deployment', 'container', 'microservice'],
            'color': '#95E1D3',
            'icon': '🔧'
        },
        '数据库': {
            'keywords': ['database', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite', 'orm', 'prisma', 'sequelize'],
            'color': '#F38181',
            'icon': '💾'
        },
        '命令行工具': {
            'keywords': ['cli', 'terminal', 'command line', 'shell', 'bash', 'zsh', 'console'],
            'color': '#AA96DA',
            'icon': '⌨️'
        },
        '安全': {
            'keywords': ['security', 'encryption', 'authentication', 'authorization', 'jwt', 'oauth', 'vulnerability', 'penetration', 'firewall'],
            'color': '#FCBAD3',
            'icon': '🔒'
        },
        '数据分析': {
            'keywords': ['data analysis', 'visualization', 'pandas', 'numpy', 'jupyter', 'matplotlib', 'dashboard', 'analytics', 'bi'],
            'color': '#FFFFD2',
            'icon': '📊'
        },
        '游戏开发': {
            'keywords': ['game', 'unity', 'unreal', 'godot', 'pygame', 'game engine', 'game development'],
            'color': '#A8D8EA',
            'icon': '🎮'
        },
        '移动开发': {
            'keywords': ['android', 'ios', 'flutter', 'react native', 'swift', 'kotlin', 'mobile'],
            'color': '#FFAAA7',
            'icon': '📱'
        },
        '区块链': {
            'keywords': ['blockchain', 'crypto', 'ethereum', 'bitcoin', 'web3', 'smart contract', 'solidity', 'nft'],
            'color': '#FFD3B4',
            'icon': '⛓️'
        },
        '前端组件': {
            'keywords': ['ui', 'component', 'design system', 'tailwind', 'css', 'sass', 'styled-components'],
            'color': '#FFAAA5',
            'icon': '🎨'
        },
        '后端服务': {
            'keywords': ['api', 'backend', 'server', 'microservice', 'graphql', 'rest', 'grpc'],
            'color': '#FF8B94',
            'icon': '⚙️'
        },
        '测试工具': {
            'keywords': ['test', 'testing', 'jest', 'pytest', 'selenium', 'cypress', 'unit test', 'e2e'],
            'color': '#C7CEEA',
            'icon': '🧪'
        },
        '开发工具': {
            'keywords': ['vscode', 'editor', 'ide', 'plugin', 'extension', 'devtools', 'debugger'],
            'color': '#B5EAD7',
            'icon': '🛠️'
        }
    }

    def __init__(self, custom_categories: Optional[Dict] = None):
        self.categories = custom_categories if custom_categories else self.DEFAULT_CATEGORIES
        for category, config in self.categories.items():
            if 'keywords' in config:
                config['keywords'] = [kw.lower() for kw in config['keywords']]

    def classify_by_keywords(self, repo_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """基于关键词匹配进行分类"""
        text_to_search = f"{repo_data.get('name', '')} {repo_data.get('description', '')} {repo_data.get('language', '')}".lower()

        matched_tags = []
        for category, config in self.categories.items():
            keywords = config.get('keywords', [])
            for keyword in keywords:
                if keyword in text_to_search:
                    matched_tags.append({
                        'name': category,
                        'color': config.get('color', '#999999'),
                        'icon': config.get('icon', '🏷️'),
                        'source': 'keyword'
                    })
                    break

        return matched_tags

    def classify_by_language(self, repo_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """基于编程语言添加标签"""
        language = repo_data.get('language', '').lower()
        if not language or language == 'unknown':
            return []

        language_map = {
            'python': {'color': '#3776AB', 'icon': '🐍'},
            'javascript': {'color': '#F7DF1E', 'icon': '📜'},
            'typescript': {'color': '#3178C6', 'icon': '📘'},
            'go': {'color': '#00ADD8', 'icon': '🐹'},
            'rust': {'color': '#CE422B', 'icon': '🦀'},
            'java': {'color': '#007396', 'icon': '☕'},
            'c++': {'color': '#00599C', 'icon': '➕'},
            'c#': {'color': '#239120', 'icon': '#️⃣'},
            'ruby': {'color': '#CC342D', 'icon': '💎'},
            'php': {'color': '#777BB4', 'icon': '🐘'},
            'swift': {'color': '#FA7343', 'icon': '🐦'},
            'kotlin': {'color': '#7F52FF', 'icon': '🅺'}
        }

        lang_config = language_map.get(language)
        if lang_config:
            return [{
                'name': language.capitalize(),
                'color': lang_config['color'],
                'icon': lang_config['icon'],
                'source': 'language'
            }]

        return [{
            'name': language.capitalize(),
            'color': '#888888',
            'icon': '💻',
            'source': 'language'
        }]

    def classify_by_stars(self, repo_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """基于Star数添加热度标签"""
        stars = repo_data.get('stars', 0)
        tags = []

        if stars >= 10000:
            tags.append({'name': '超人气', 'color': '#FF0000', 'icon': '🔥', 'source': 'stars'})
        elif stars >= 5000:
            tags.append({'name': '热门', 'color': '#FF6347', 'icon': '⭐', 'source': 'stars'})
        elif stars >= 1000:
            tags.append({'name': '流行', 'color': '#FFA500', 'icon': '✨', 'source': 'stars'})

        return tags

    def classify(self, repo_data: Dict[str, Any], max_tags: int = 5) -> List[Dict[str, str]]:
        """综合分类方法"""
        all_tags = []

        all_tags.extend(self.classify_by_stars(repo_data))
        all_tags.extend(self.classify_by_keywords(repo_data))
        all_tags.extend(self.classify_by_language(repo_data))

        seen = set()
        unique_tags = []
        for tag in all_tags:
            if tag['name'] not in seen:
                unique_tags.append(tag)
                seen.add(tag['name'])

        return unique_tags[:max_tags]

    def classify_with_ai(self, repo_data: Dict[str, Any], ai_summary: Optional[str] = None) -> List[Dict[str, str]]:
        """结合AI分析结果进行分类"""
        tags = self.classify(repo_data)

        if ai_summary:
            summary_lower = ai_summary.lower()
            for category, config in self.categories.items():
                if category in [t['name'] for t in tags]:
                    continue

                keywords = config.get('keywords', [])
                for keyword in keywords:
                    if keyword in summary_lower:
                        tags.append({
                            'name': category,
                            'color': config.get('color', '#999999'),
                            'icon': config.get('icon', '🏷️'),
                            'source': 'ai_summary'
                        })
                        break

        return tags[:5]

    def batch_classify(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量分类"""
        classified_repos = []
        for repo in repos:
            repo_copy = repo.copy()
            ai_summary = repo_copy.get('ai_summary', '')
            tags = self.classify_with_ai(repo_copy, ai_summary)
            repo_copy['tags'] = tags
            classified_repos.append(repo_copy)
            logger.debug(f"Classified {repo_copy.get('name')}: {[t['name'] for t in tags]}")

        logger.info(f"Batch classification completed for {len(repos)} repositories")
        return classified_repos


def create_classifier(custom_categories: Optional[Dict] = None) -> ProjectClassifier:
    """创建分类器实例"""
    return ProjectClassifier(custom_categories)
