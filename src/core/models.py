#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模型定义
"""

from datetime import datetime, timezone
from typing import Callable, Optional
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, UniqueConstraint, Boolean
from sqlalchemy.types import TypeDecorator


def utc_now() -> datetime:
    """Return current UTC time with timezone info"""
    return datetime.now(timezone.utc)

# 加密函数通过依赖注入方式设置，避免 core 层依赖 infrastructure
_encrypt_func: Optional[Callable[[str], str]] = None
_decrypt_func: Optional[Callable[[str], str]] = None

def set_encryption_functions(encrypt_fn: Callable[[str], str], decrypt_fn: Callable[[str], str]):
    """设置加密/解密函数（由 infrastructure 层调用）"""
    global _encrypt_func, _decrypt_func
    _encrypt_func = encrypt_fn
    _decrypt_func = decrypt_fn

class EncryptedString(TypeDecorator):
    """Encrypted string type"""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and _encrypt_func is not None:
            return _encrypt_func(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and _decrypt_func is not None:
            return _decrypt_func(value)
        return value

Base = declarative_base()


class Repository(Base):
    """GitHub 仓库模型"""
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    url = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String(50), nullable=True, index=True)
    first_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    trending_records = relationship("TrendingRecord", back_populates="repository", cascade="all, delete-orphan")
    ai_summaries = relationship("AISummary", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository(name='{self.name}', language='{self.language}')>"


class TrendingRecord(Base):
    """趋势记录模型"""
    __tablename__ = 'trending_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False)
    time_range = Column(String(20), nullable=False, index=True)
    record_date = Column(DateTime, nullable=False, index=True)
    stars = Column(Integer, nullable=False, default=0)
    forks = Column(Integer, nullable=False, default=0)
    stars_increment = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    repository = relationship("Repository", back_populates="trending_records")

    __table_args__ = (
        UniqueConstraint('repository_id', 'time_range', 'record_date', name='uq_repo_range_date'),
        Index('idx_time_range_date', 'time_range', 'record_date'),
        Index('idx_repo_time_date', 'repository_id', 'time_range', 'record_date'),
    )

    def __repr__(self):
        return f"<TrendingRecord(repo='{self.repository.name if self.repository else None}', range='{self.time_range}', date='{self.record_date}')>"


class AISummary(Base):
    """AI 摘要模型"""
    __tablename__ = 'ai_summaries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False)
    summary_text = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    repository = relationship("Repository", back_populates="ai_summaries")

    __table_args__ = (
        Index('idx_repo_created', 'repository_id', 'created_at'),
    )

    def __repr__(self):
        return f"<AISummary(repo='{self.repository.name if self.repository else None}', model='{self.model_name}')>"


class TaskHistory(Base):
    """任务执行历史模型"""
    __tablename__ = 'task_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=True, index=True)
    task_type = Column(String(20), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # running/success/failed
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_task_type_started', 'task_type', 'started_at'),
    )

    def __repr__(self):
        return f"<TaskHistory(type='{self.task_type}', status='{self.status}')>"


class Settings(Base):
    """统一设置表（单例模式，只有一条记录）"""
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Email 配置（仅收件人列表，其他在 config.yaml）
    email_recipients = Column(Text, nullable=True)  # JSON 数组

    # Scheduler 配置
    scheduler_timezone = Column(String(50), nullable=True, default="Asia/Shanghai")
    scheduler_daily_enabled = Column(Boolean, nullable=True, default=True)
    scheduler_daily_time = Column(String(10), nullable=True, default="08:00")
    scheduler_weekly_enabled = Column(Boolean, nullable=True, default=True)
    scheduler_weekly_day = Column(String(20), nullable=True, default="sunday")
    scheduler_weekly_time = Column(String(10), nullable=True, default="22:00")
    scheduler_monthly_enabled = Column(Boolean, nullable=True, default=True)
    scheduler_monthly_time = Column(String(10), nullable=True, default="22:00")

    # Filters 配置
    filters_min_stars = Column(Integer, nullable=True, default=100)
    filters_min_stars_daily = Column(Integer, nullable=True, default=50)
    filters_min_stars_weekly = Column(Integer, nullable=True, default=200)
    filters_min_stars_monthly = Column(Integer, nullable=True, default=500)

    # Subscription 配置
    subscription_keywords = Column(Text, nullable=True)  # JSON 数组
    subscription_languages = Column(Text, nullable=True)  # JSON 数组

    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return f"<Settings(id={self.id})>"
