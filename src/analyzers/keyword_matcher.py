#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键词匹配引擎
"""

import re
import yaml
from loguru import logger
from typing import List, Dict
from difflib import SequenceMatcher


class MatchMode:
    """匹配模式"""
    EXACT = "exact"
    REGEX = "regex"
    FUZZY = "fuzzy"


class KeywordMatcher:
    """关键词匹配器"""

    def __init__(self, config_path: str = "config/config.yaml"):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {config_path}, using empty config")
            self.config = {}

        self.subscription_config = self.config.get('subscription', {})
        self.keywords = self.subscription_config.get('keywords', [])
        self.match_mode = self.subscription_config.get('match_mode', MatchMode.FUZZY)
        self.match_fields = self.subscription_config.get('match_fields', ['name', 'description'])
        self.fuzzy_threshold = self.subscription_config.get('fuzzy_threshold', 0.6)
        self.case_sensitive = self.subscription_config.get('case_sensitive', False)

    def _exact_match(self, text: str, keyword: str) -> bool:
        """精确匹配"""
        if not self.case_sensitive:
            text = text.lower()
            keyword = keyword.lower()
        return keyword in text

    def _regex_match(self, text: str, pattern: str) -> bool:
        """正则匹配"""
        try:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            return bool(re.search(pattern, text, flags=flags))
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return False

    def _fuzzy_match(self, text: str, keyword: str) -> bool:
        """模糊匹配"""
        if not self.case_sensitive:
            text = text.lower()
            keyword = keyword.lower()

        text_words = text.split()
        for word in text_words:
            similarity = SequenceMatcher(None, word, keyword).ratio()
            if similarity >= self.fuzzy_threshold:
                return True

        return False

    def match_keyword(self, text: str, keyword: str) -> bool:
        """根据配置的模式匹配关键词"""
        if not text or not keyword:
            return False

        if self.match_mode == MatchMode.EXACT:
            return self._exact_match(text, keyword)
        elif self.match_mode == MatchMode.REGEX:
            return self._regex_match(text, keyword)
        elif self.match_mode == MatchMode.FUZZY:
            return self._fuzzy_match(text, keyword)
        else:
            logger.warning(f"Unknown match mode '{self.match_mode}', using exact match")
            return self._exact_match(text, keyword)

    def match_repo(self, repo: Dict) -> Dict:
        """匹配单个项目，返回匹配结果"""
        matched_keywords = []
        matched_fields = {}

        for field in self.match_fields:
            field_value = str(repo.get(field, ''))
            if not field_value:
                continue

            for keyword in self.keywords:
                if self.match_keyword(field_value, keyword):
                    if keyword not in matched_keywords:
                        matched_keywords.append(keyword)

                    if field not in matched_fields:
                        matched_fields[field] = []
                    if keyword not in matched_fields[field]:
                        matched_fields[field].append(keyword)

        return {
            'matched': len(matched_keywords) > 0,
            'keywords': matched_keywords,
            'fields': matched_fields
        }

    def filter_repos(self, repos: List[Dict]) -> List[Dict]:
        """过滤匹配关键词的项目"""
        if not repos or not self.keywords:
            return repos

        matched_repos = []

        for repo in repos:
            match_result = self.match_repo(repo)
            if match_result['matched']:
                repo_copy = repo.copy()
                repo_copy['_keyword_match'] = match_result
                matched_repos.append(repo_copy)
                logger.info(f"Matched: {repo['name']} (keywords: {match_result['keywords']})")

        logger.info(f"Keyword filter: {len(repos)} -> {len(matched_repos)} (matched {len(matched_repos)})")
        return matched_repos

    def highlight_keywords(self, text: str) -> str:
        """在文本中高亮关键词（用于邮件模板）"""
        if not text or not self.keywords:
            return text

        highlighted_text = text

        for keyword in self.keywords:
            if self.match_keyword(text, keyword):
                if self.match_mode == MatchMode.EXACT:
                    if self.case_sensitive:
                        highlighted_text = highlighted_text.replace(
                            keyword,
                            f"<mark style='background-color: #ffeb3b; padding: 2px 4px;'>{keyword}</mark>"
                        )
                    else:
                        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                        highlighted_text = pattern.sub(
                            lambda m: f"<mark style='background-color: #ffeb3b; padding: 2px 4px;'>{m.group()}</mark>",
                            highlighted_text
                        )

        return highlighted_text
