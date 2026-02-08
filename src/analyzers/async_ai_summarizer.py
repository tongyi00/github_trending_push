#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异步 AI 摘要生成器 - 使用 AsyncOpenAI 提升性能
"""

import os
import re
import json
import yaml
import asyncio
from datetime import datetime
from loguru import logger
from openai import AsyncOpenAI
from typing import List, Dict, Optional, Any


class AsyncAISummarizer:
    """异步 AI 摘要生成器"""

    def __init__(self, config_path: str = None, max_concurrent: int = 3):
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "config/config.yaml")
        from pathlib import Path
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.ai_config = self.config['ai_models']
        self.prompt_template = self.config['prompt_template']
        self.enabled_models = self.ai_config.get('enabled', [])
        self.semaphore = asyncio.Semaphore(max_concurrent)

        self.clients = {}
        self._init_clients()

    def _init_clients(self):
        """初始化异步 AI 客户端"""
        for model_name in self.enabled_models:
            model_config = self.ai_config.get(model_name, {})

            if model_name in ['deepseek', 'nvidia']:
                api_key = model_config.get('api_key', '')
                base_url = model_config.get('base_url', '')

                if api_key and base_url:
                    # Explicitly set timeout and limits
                    self.clients[model_name] = AsyncOpenAI(
                        api_key=api_key,
                        base_url=base_url,
                        timeout=60.0,
                        max_retries=2
                    )
                else:
                    logger.warning(f"Missing API key or base URL for {model_name}")

    async def generate_summary(self, repo: Dict, model_name: str, retries: int = 5) -> Optional[str]:
        """异步生成单个项目的摘要，支持重试"""
        if model_name not in self.clients:
            logger.error(f"Model {model_name} not available")
            return None

        prompt = self.prompt_template.format(
            name=repo.get('name', ''),
            description=repo.get('description', ''),
            stars=repo.get('stars', 0),
            language=repo.get('language', ''),
            updated_at=repo.get('updated_at', '')
        )

        client = self.clients[model_name]
        model_config = self.ai_config.get(model_name, {})

        for attempt in range(retries):
            try:
                async with self.semaphore:
                    response = await client.chat.completions.create(
                        model=model_config.get('model', ''),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=model_config.get('temperature', 0.7),
                        max_tokens=model_config.get('max_tokens', 500),
                        timeout=30
                    )
                    summary = response.choices[0].message.content.strip()
                    logger.debug(f"Generated summary for {repo['name']} using {model_name}")
                    return summary

            except Exception as e:
                logger.warning(f"Error generating summary for {repo['name']} with {model_name}, attempt {attempt + 1}/{retries}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return None

    async def batch_summarize(self, repos: List[Dict], model_name: Optional[str] = None) -> List[Dict]:
        """异步批量生成摘要"""
        if not repos:
            return []

        if model_name is None:
            model_name = self.enabled_models[0] if self.enabled_models else None

        if not model_name or model_name not in self.clients:
            logger.error(f"No valid model available for summarization")
            return repos

        logger.info(f"Generating summaries for {len(repos)} repositories using {model_name}...")

        tasks = [self.generate_summary(repo, model_name) for repo in repos]
        summaries = await asyncio.gather(*tasks, return_exceptions=True)

        repos_with_summary = []
        failed_count = 0
        for repo, summary in zip(repos, summaries):
            repo_copy = repo.copy()
            if isinstance(summary, Exception):
                failed_count += 1
                logger.error(f"Failed to generate summary for {repo['name']} (url: {repo.get('url', 'N/A')}, stars: {repo.get('stars', 'N/A')}): {type(summary).__name__}: {summary}")
                repo_copy['ai_summary'] = f"摘要生成失败: {repo.get('description', '')}"
            elif summary:
                repo_copy['ai_summary'] = summary
            else:
                failed_count += 1
                logger.warning(f"Empty summary returned for {repo['name']} (url: {repo.get('url', 'N/A')})")
                repo_copy['ai_summary'] = f"项目简介: {repo.get('description', '')}"

            repos_with_summary.append(repo_copy)

        if failed_count > 0:
            logger.warning(f"Batch summarization completed with {failed_count}/{len(repos)} failures")

        logger.info(f"Completed {len(repos_with_summary)} summaries")
        return repos_with_summary

    async def generate_detailed_report(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细分析报告（异步版本）"""
        if not self.clients:
            return {'success': False, 'error': 'No AI models available', 'report': None}

        prompt = self._build_detailed_prompt(repo_data)
        raw_response = await self._call_ai_for_detailed_report(prompt)

        if not raw_response['success']:
            return {'success': False, 'error': raw_response.get('error', 'AI call failed'), 'report': None}

        report = self._parse_report_json(raw_response['content'])

        return {'success': True, 'report': report, 'model_used': raw_response['model_used'], 'generated_at': datetime.now().isoformat()}

    def _build_detailed_prompt(self, repo_data: Dict) -> str:
        """构建详细报告提示词"""
        template = self.config.get('detailed_prompt_template', '')
        if not template:
            # 使用默认模板
            template = """请对以下 GitHub 项目进行详细分析，以 JSON 格式返回：

项目名称：{name}
项目描述：{description}
Stars：{stars}
Forks：{forks}
主要语言：{language}

请返回以下结构的 JSON（严格遵守格式）：
{{
  "executive_summary": "项目的执行摘要（100-200字）",
  "scores": {{
    "architecture": {{"score": 8.5, "reason": "评分理由"}},
    "code_quality": {{"score": 7.0, "reason": "评分理由"}},
    "documentation": {{"score": 6.5, "reason": "评分理由"}},
    "community": {{"score": 9.0, "reason": "评分理由"}},
    "innovation": {{"score": 8.0, "reason": "评分理由"}}
  }},
  "key_features": ["核心功能1", "核心功能2", "核心功能3"],
  "tech_stack": ["技术栈1", "技术栈2", "技术栈3"],
  "use_cases": ["适用场景1", "适用场景2"],
  "limitations": ["局限性1", "局限性2"],
  "learning_resources": ["学习资源链接或建议"]
}}"""

        return template.format(
            name=repo_data.get('name', 'Unknown'),
            description=repo_data.get('description', 'No description'),
            stars=repo_data.get('stars', 0),
            forks=repo_data.get('forks', 0),
            language=repo_data.get('language', 'Unknown'),
            readme_content=repo_data.get('readme_content', 'Not available'),
            dependencies=repo_data.get('dependencies', 'Not available')
        )

    async def _call_ai_for_detailed_report(self, prompt: str) -> Dict[str, Any]:
        """异步调用 AI 生成详细报告"""
        model_name = self.enabled_models[0] if self.enabled_models else None

        if not model_name or model_name not in self.clients:
            return {'success': False, 'error': 'No valid model available'}

        client = self.clients[model_name]
        model_config = self.ai_config.get(model_name, {})

        try:
            logger.info(f"Generating detailed report using {model_name}...")
            async with self.semaphore:
                response = await client.chat.completions.create(
                    model=model_config.get('model', ''),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=model_config.get('temperature', 0.7),
                    max_tokens=model_config.get('max_tokens', 2000),
                    timeout=60
                )
                content = response.choices[0].message.content.strip()
                logger.info(f"Detailed report generated successfully using {model_name}")
                return {'success': True, 'content': content, 'model_used': model_name}
        except Exception as e:
            logger.error(f"{model_name} failed for detailed report: {e}")
            return {'success': False, 'error': str(e)}

    async def generate_detailed_report_stream(self, repo_data: Dict[str, Any]):
        """流式生成详细分析报告（SSE 格式）"""
        if not self.clients:
            yield {'event': 'error', 'data': {'message': 'No AI models available'}}
            return

        model_name = self.enabled_models[0] if self.enabled_models else None
        if not model_name or model_name not in self.clients:
            yield {'event': 'error', 'data': {'message': 'No valid model available'}}
            return

        yield {'event': 'thinking', 'data': {'status': 'analyzing', 'message': '正在分析项目信息...'}}

        prompt = self._build_detailed_prompt(repo_data)
        client = self.clients[model_name]
        model_config = self.ai_config.get(model_name, {})

        try:
            yield {'event': 'thinking', 'data': {'status': 'generating', 'message': '正在生成分析报告...'}}

            async with self.semaphore:
                stream = await client.chat.completions.create(
                    model=model_config.get('model', ''),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=model_config.get('temperature', 0.7),
                    max_tokens=model_config.get('max_tokens', 2000),
                    stream=True,
                    timeout=60
                )

                collected_content = ""
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        collected_content += delta
                        yield {'event': 'partial', 'data': {'content': delta}}

            yield {'event': 'thinking', 'data': {'status': 'parsing', 'message': '正在解析报告结构...'}}

            report = self._parse_report_json(collected_content)
            yield {'event': 'complete', 'data': {'success': True, 'report': report, 'model_used': model_name, 'generated_at': datetime.now().isoformat()}}

        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            yield {'event': 'error', 'data': {'message': str(e)}}

    def _parse_report_json(self, raw_content: str) -> Dict[str, Any]:
        """解析 AI 返回的 JSON，带容错处理"""
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_content)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = raw_content

        try:
            report = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e}, using fallback structure")
            report = self._create_fallback_report(raw_content)

        return self._validate_report_structure(report)

    def _create_fallback_report(self, raw_content: str) -> Dict[str, Any]:
        """创建降级报告结构"""
        return {
            'executive_summary': raw_content[:500] if raw_content else 'Analysis unavailable',
            'scores': {},
            'key_features': [],
            'tech_stack': [],
            'use_cases': [],
            'limitations': [],
            'learning_resources': []
        }

    def _validate_report_structure(self, report: Dict) -> Dict[str, Any]:
        """验证报告结构，填充缺失字段"""
        default_score = {'score': 5.0, 'reason': 'Unable to assess'}

        validated = {
            'executive_summary': report.get('executive_summary', 'No summary available'),
            'scores': {
                'architecture': report.get('scores', {}).get('architecture', default_score),
                'code_quality': report.get('scores', {}).get('code_quality', default_score),
                'documentation': report.get('scores', {}).get('documentation', default_score),
                'community': report.get('scores', {}).get('community', default_score),
                'innovation': report.get('scores', {}).get('innovation', default_score),
            },
            'key_features': report.get('key_features', [])[:6],
            'tech_stack': report.get('tech_stack', [])[:8],
            'use_cases': report.get('use_cases', [])[:5],
            'limitations': report.get('limitations', [])[:4],
            'learning_resources': report.get('learning_resources', [])[:4],
            'integration_examples': report.get('integration_examples', [])[:3],
            'faq': report.get('faq', [])[:5]
        }

        return validated

    async def close(self):
        """关闭所有异步客户端"""
        for model_name, client in self.clients.items():
            try:
                if hasattr(client, 'close'):
                    await client.close()
                elif hasattr(client, '_client') and client._client:
                    await client._client.aclose()
                logger.info(f"Closed async client for {model_name}")
            except Exception as e:
                logger.warning(f"Error closing client {model_name}: {e}")
