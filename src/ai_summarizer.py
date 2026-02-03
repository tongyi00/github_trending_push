"""
AI模型调用模块 - 支持多模型配置和自动降级
"""

from typing import Any, Dict, List

import yaml
from loguru import logger
from openai import OpenAI

# 可选依赖：zhipuai（仅在使用GLM官方API时需要）
try:
    from zhipuai import ZhipuAI
    HAS_ZHIPUAI = True
except Exception as e:
    logger.warning(f"Failed to import zhipuai (GLM support disabled): {e}")
    HAS_ZHIPUAI = False


class AIModelConfig:
    """AI模型配置管理"""

    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.ai_config = self.config['ai_models']
        self.prompt_template = self.config['prompt_template']

    def get_enabled_models(self) -> list:
        """获取启用的模型列表"""
        return self.ai_config.get('enabled', [])

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """获取指定模型的配置"""
        return self.ai_config.get(model_name, {})


class NvidiaClient:
    """NVIDIA API客户端 (OpenAI兼容模式)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = OpenAI(api_key=config['api_key'], base_url=config['base_url'])

    def summarize(self, prompt: str) -> str:
        """调用NVIDIA API生成总结"""
        try:
            response = self.client.chat.completions.create(model=self.config['model'], messages=[{"role": "user", "content": prompt}], temperature=self.config.get('temperature', 0.7), max_tokens=self.config.get('max_tokens', 500), timeout=30)
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            if 'API key' in error_msg or 'api_key' in error_msg:
                logger.error(f"NVIDIA API key error: {e}")
            elif 'rate limit' in error_msg.lower():
                logger.error(f"NVIDIA API rate limit: {e}")
            elif 'timeout' in error_msg.lower():
                logger.error(f"NVIDIA API request timeout: {e}")
            else:
                logger.error(f"NVIDIA API call failed: {e}")
            raise


class DeepSeekClient:
    """DeepSeek模型客户端"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = OpenAI(api_key=config['api_key'], base_url=config['base_url'])

    def summarize(self, prompt: str) -> str:
        """调用DeepSeek生成总结"""
        try:
            response = self.client.chat.completions.create(model=self.config['model'], messages=[{"role": "user", "content": prompt}], temperature=self.config.get('temperature', 0.7), max_tokens=self.config.get('max_tokens', 500), timeout=30)
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            if 'API key' in error_msg:
                logger.error(f"DeepSeek API key error: {e}")
            elif 'rate limit' in error_msg.lower():
                logger.error(f"DeepSeek API rate limit: {e}")
            elif 'timeout' in error_msg.lower():
                logger.error(f"DeepSeek API request timeout: {e}")
            else:
                logger.error(f"DeepSeek API call failed: {e}")
            raise


class GLMClient:
    """智谱GLM模型客户端"""

    def __init__(self, config: Dict[str, Any]):
        if not HAS_ZHIPUAI:
            raise ImportError("zhipuai package not installed. Install it with: pip install zhipuai>=2.0.0\nOr use NVIDIA API to call GLM model (recommended): model='z-ai/glm4_7'")
        self.config = config
        self.client = ZhipuAI(api_key=config['api_key'])

    def summarize(self, prompt: str) -> str:
        """调用GLM生成总结"""
        try:
            response = self.client.chat.completions.create(model=self.config['model'], messages=[{"role": "user", "content": prompt}], temperature=self.config.get('temperature', 0.7), max_tokens=self.config.get('max_tokens', 500))
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            if 'API key' in error_msg or 'api_key' in error_msg:
                logger.error(f"GLM API key error: {e}")
            elif 'balance' in error_msg.lower() or '余额' in error_msg:
                logger.error(f"GLM account balance insufficient: {e}")
            else:
                logger.error(f"GLM API call failed: {e}")
            raise


class KimiClient:
    """Moonshot Kimi模型客户端"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = OpenAI(api_key=config['api_key'], base_url=config['base_url'])

    def summarize(self, prompt: str) -> str:
        """调用Kimi生成总结"""
        try:
            response = self.client.chat.completions.create(model=self.config['model'], messages=[{"role": "user", "content": prompt}], temperature=self.config.get('temperature', 0.3), max_tokens=self.config.get('max_tokens', 500), timeout=30)
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            if 'API key' in error_msg:
                logger.error(f"Kimi API key error: {e}")
            elif 'rate limit' in error_msg.lower():
                logger.error(f"Kimi API rate limit: {e}")
            else:
                logger.error(f"Kimi API call failed: {e}")
            raise


class AISummarizer:
    """AI总结器 - 支持多模型配置和自动降级"""

    CLIENT_MAP = {
        'nvidia': NvidiaClient,
        'deepseek': DeepSeekClient,
        'glm': GLMClient,
        'kimi': KimiClient
    }

    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化AI总结器"""
        self.config_manager = AIModelConfig(config_path)
        self.clients = {}
        self._init_clients()

    def _init_clients(self):
        """初始化所有启用的模型客户端"""
        enabled_models = self.config_manager.get_enabled_models()

        for model_name in enabled_models:
            try:
                model_config = self.config_manager.get_model_config(model_name)

                # 验证API密钥
                if not model_config.get('api_key') or model_config['api_key'].startswith('YOUR_') or model_config['api_key'].startswith('sk-xxx') or model_config['api_key'].startswith('nvapi-xxx'):
                    logger.warning(f"Model {model_name} API key not configured, skipping initialization")
                    continue

                client_class = self.CLIENT_MAP.get(model_name)
                if client_class:
                    self.clients[model_name] = client_class(model_config)
                    logger.info(f"Model {model_name} initialized successfully")
                else:
                    logger.warning(f"Unknown model type: {model_name}")

            except Exception as e:
                logger.error(f"Model {model_name} initialization failed: {e}")

    def _build_prompt(self, repo_data: Dict[str, Any]) -> str:
        """构建AI总结提示词"""
        return self.config_manager.prompt_template.format(name=repo_data.get('name', 'Unknown'), description=repo_data.get('description', 'No description'), stars=repo_data.get('stars', 0), language=repo_data.get('language', 'Unknown'), updated_at=repo_data.get('updated_at', 'Unknown'))

    def summarize(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """智能总结项目 (多模型自动降级)"""
        if not self.clients:
            logger.warning("No AI models available, returning original description")
            return {'summary': repo_data.get('description', 'No description'), 'model_used': 'fallback', 'success': False}

        prompt = self._build_prompt(repo_data)
        enabled_models = self.config_manager.get_enabled_models()

        for model_name in enabled_models:
            if model_name not in self.clients:
                continue

            try:
                logger.info(f"Attempting to use {model_name} to generate summary...")
                summary = self.clients[model_name].summarize(prompt)

                logger.info(f"{model_name} call successful")
                return {'summary': summary, 'model_used': model_name, 'success': True}

            except Exception as e:
                logger.warning(f"{model_name} call failed: {e}, trying next model")
                continue

        logger.error("All AI model calls failed, using original description as fallback")
        return {'summary': repo_data.get('description', 'No description'), 'model_used': 'fallback', 'success': False}

    def batch_summarize(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量总结多个项目"""
        results = []

        for idx, repo in enumerate(repos, 1):
            logger.info(f"Summarizing project {idx}/{len(repos)}: {repo.get('name')}")

            summary_result = self.summarize(repo)

            repo['ai_summary'] = summary_result['summary']
            repo['model_used'] = summary_result['model_used']
            repo['summary_success'] = summary_result['success']

            results.append(repo)

        return results

    def get_available_models(self) -> list:
        """获取当前可用的模型列表"""
        return list(self.clients.keys())

    def test_all_models(self):
        """测试所有配置的模型是否可用"""
        test_repo = {'name': 'test-repo', 'description': 'A test repository', 'stars': 100, 'language': 'Python', 'updated_at': '2024-01-01'}

        print("\n" + "="*60)
        print("AI Model Connectivity Test")
        print("="*60 + "\n")

        for model_name in self.config_manager.get_enabled_models():
            if model_name not in self.clients:
                print(f"[SKIP] {model_name.upper():12} - Not initialized (check API key configuration)")
                continue

            try:
                prompt = self._build_prompt(test_repo)
                result = self.clients[model_name].summarize(prompt)
                print(f"[PASS] {model_name.upper():12} - Connection successful")
                print(f"  Response preview: {result[:50]}...\n")
            except Exception as e:
                print(f"[FAIL] {model_name.upper():12} - Connection failed")
                print(f"  Error message: {str(e)}\n")

        print("="*60)


def create_summarizer(config_path: str = "config/config.yaml") -> AISummarizer:
    """创建AI总结器实例"""
    return AISummarizer(config_path)


if __name__ == "__main__":
    summarizer = create_summarizer()
    summarizer.test_all_models()
