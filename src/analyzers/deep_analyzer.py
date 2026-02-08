"""
GitHub项目深度分析模块 - 提供详细的技术分析报告
"""

import re
import base64
import asyncio
import httpx
from loguru import logger
from typing import Any, Dict, Optional


class DeepAnalyzer:
    """GitHub项目深度分析器（异步版本）"""

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/vnd.github.v3+json'
        }
        if github_token:
            self._headers['Authorization'] = f'token {github_token}'

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出，确保资源清理"""
        await self.close()
        return False

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 httpx 异步客户端"""
        async with self._lock:
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(headers=self._headers, timeout=10.0)
            return self._client

    async def close(self):
        """关闭客户端释放资源"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch_readme(self, repo_url: str, max_lines: int = 500) -> Optional[str]:
        """抓取项目README内容（前N行）"""
        try:
            owner, repo = self._parse_repo_url(repo_url)
            if not owner or not repo:
                logger.warning(f"Invalid repository URL: {repo_url}")
                return None

            client = await self._get_client()
            api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            response = await client.get(api_url)

            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining and int(remaining) < 10:
                reset_time = response.headers.get('X-RateLimit-Reset')
                logger.warning(f"GitHub API rate limit low: {remaining} requests remaining, resets at {reset_time}")

            if response.status_code == 403:
                logger.error(f"GitHub API rate limit exceeded or access forbidden for {owner}/{repo}")
                return None

            if response.status_code == 404:
                logger.warning(f"README not found for {owner}/{repo}")
                return None

            response.raise_for_status()
            readme_data = response.json()

            readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
            lines = readme_content.split('\n')[:max_lines]
            readme_text = '\n'.join(lines)

            logger.info(f"Successfully fetched README for {owner}/{repo} ({len(lines)} lines)")
            return readme_text

        except httpx.RequestError as e:
            logger.error(f"Failed to fetch README for {repo_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing README: {e}")
            return None

    def extract_dependencies(self, readme_content: Optional[str]) -> list:
        """从README中识别知名库和技术栈"""
        if not readme_content:
            return []

        known_libraries = {
            'Python': ['django', 'flask', 'fastapi', 'pytorch', 'tensorflow', 'numpy', 'pandas', 'scikit-learn', 'keras', 'sqlalchemy', 'celery', 'redis', 'asyncio'],
            'JavaScript': ['react', 'vue', 'angular', 'next.js', 'express', 'nest.js', 'webpack', 'vite', 'typescript', 'node.js', 'electron'],
            'Go': ['gin', 'echo', 'fiber', 'gorm', 'cobra', 'kubernetes', 'docker', 'prometheus'],
            'Java': ['spring', 'spring boot', 'hibernate', 'mybatis', 'maven', 'gradle', 'kafka', 'elasticsearch'],
            'Rust': ['tokio', 'actix', 'rocket', 'serde', 'diesel', 'wasm'],
            'Database': ['postgresql', 'mysql', 'mongodb', 'sqlite', 'redis', 'cassandra'],
            'DevOps': ['docker', 'kubernetes', 'jenkins', 'github actions', 'terraform', 'ansible'],
            'AI/ML': ['openai', 'langchain', 'llama', 'hugging face', 'stable diffusion', 'transformers']
        }

        found_deps = []
        readme_lower = readme_content.lower()

        for category, libs in known_libraries.items():
            for lib in libs:
                if lib.lower() in readme_lower:
                    found_deps.append({'name': lib, 'category': category})

        unique_deps = []
        seen = set()
        for dep in found_deps:
            if dep['name'] not in seen:
                unique_deps.append(dep)
                seen.add(dep['name'])

        return unique_deps[:10]

    def build_deep_analysis_prompt(self, repo_data: Dict[str, Any], readme_content: Optional[str], dependencies: list) -> str:
        """构建深度分析提示词"""
        deps_text = ', '.join([f"{d['name']} ({d['category']})" for d in dependencies]) if dependencies else "未识别到主流技术栈"
        readme_excerpt = readme_content[:2000] if readme_content else "无README内容"

        prompt = f"""你是资深技术架构师和GitHub开源项目分析专家。请对以下项目进行深度技术分析：

**项目基本信息：**
- 名称: {repo_data.get('name', 'Unknown')}
- 描述: {repo_data.get('description', 'No description')}
- Stars: {repo_data.get('stars', 0)}
- 语言: {repo_data.get('language', 'Unknown')}
- URL: {repo_data.get('url', '')}

**识别到的技术栈：**
{deps_text}

**README摘要：**
```
{readme_excerpt}
```

**请按以下格式输出深度分析报告（使用中文）：**

### 🏗️ 技术架构
[分析项目的技术架构设计，包括核心组件、设计模式、技术选型的合理性]

### ✨ 技术创新点
[指出项目的技术创新之处，与同类项目的差异化优势]

### 🎯 应用场景
[列举2-3个具体的实际应用场景，说明解决了什么问题]

### ⚠️ 潜在局限
[客观分析项目可能存在的局限性或需要注意的问题]

### 🔄 竞品对比
[如果有知名竞品，简要对比优劣势；如果是新兴领域，说明市场定位]

**要求：**
1. 专业且通俗易懂，避免过度技术术语堆砌
2. 客观中立，基于事实分析
3. 总长度控制在400字以内
4. 突出技术价值和实用性
"""
        return prompt

    def _parse_repo_url(self, url: str) -> tuple:
        """解析GitHub仓库URL，提取owner和repo名称"""
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
        return None, None

    async def analyze(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整的深度分析流程"""
        repo_url = repo_data.get('url', '')

        readme_content = await self.fetch_readme(repo_url)
        dependencies = self.extract_dependencies(readme_content)
        prompt = self.build_deep_analysis_prompt(repo_data, readme_content, dependencies)

        return {
            'prompt': prompt,
            'readme_available': readme_content is not None,
            'dependencies': dependencies,
            'readme_length': len(readme_content) if readme_content else 0
        }


def create_analyzer(github_token: Optional[str] = None) -> DeepAnalyzer:
    """创建深度分析器实例"""
    return DeepAnalyzer(github_token)
