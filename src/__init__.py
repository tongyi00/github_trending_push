#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub Trending Push - 源代码包
"""

# 显式导入替代 import * 模式
from .analyzers.async_ai_summarizer import AsyncAISummarizer
from .analyzers.deep_analyzer import DeepAnalyzer
from .analyzers.trend_analyzer import TrendAnalyzer
from .analyzers.classifier import ProjectClassifier
from .analyzers.keyword_matcher import KeywordMatcher
from .analyzers.incremental_summary import IncrementalSummaryManager

from .collectors.scraper_trending import ScraperTrending
from .collectors.async_scraper import AsyncScraperTrending

from .core.models import Repository, TrendingRecord, AISummary, Base
from .core.database import DatabaseManager
from .core.data_repository import DataRepository

from .infrastructure.config_validator import load_config, validate_config
from .infrastructure.logging_config import setup_logging
from .infrastructure.scheduler import TrendingScheduler
from .infrastructure.health_monitor import HealthMonitor
from .infrastructure.alerting import Alerting
from .infrastructure.filters import ProjectFilter

from .outputs.report_generator import ReportGenerator
from .outputs.chart_generator import ChartGenerator
from .outputs.mailer import EmailSender

__all__ = [
    # analyzers
    'AsyncAISummarizer',
    'DeepAnalyzer',
    'TrendAnalyzer',
    'ProjectClassifier',
    'KeywordMatcher',
    'IncrementalSummaryManager',
    # collectors
    'ScraperTrending',
    'AsyncScraperTrending',
    # core
    'Repository',
    'TrendingRecord',
    'AISummary',
    'Base',
    'DatabaseManager',
    'DataRepository',
    # infrastructure
    'load_config',
    'validate_config',
    'setup_logging',
    'TrendingScheduler',
    'HealthMonitor',
    'Alerting',
    'ProjectFilter',
    # outputs
    'ReportGenerator',
    'ChartGenerator',
    'EmailSender',
]
