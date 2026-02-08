#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 数据模型定义（Pydantic）
"""

from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field, field_validator, SecretStr
import re


class RepositorySchema(BaseModel):
    """仓库信息模型"""
    name: str = Field(..., description="仓库全名（owner/repo）")
    url: str = Field(..., pattern=r'^https?://', description="仓库URL")
    description: Optional[str] = Field(None, description="项目描述")
    language: Optional[str] = Field(None, description="主要编程语言")
    stars: int = Field(0, description="Star数量")
    forks: int = Field(0, description="Fork数量")
    stars_increment: int = Field(0, description="Star增量")
    time_range: Literal["daily", "weekly", "monthly"] = Field(..., description="时间范围")
    record_date: str = Field(..., description="记录日期")
    ai_summary: Optional[str] = Field(None, description="AI摘要（简短版本）")
    has_ai_analysis: bool = Field(False, description="是否有完整的AI分析报告")


class TrendingListResponse(BaseModel):
    """趋势列表响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    items: List[RepositorySchema] = Field(..., description="仓库列表")


class LanguageStats(BaseModel):
    """语言统计模型"""
    language: str = Field(..., description="编程语言")
    count: int = Field(..., description="项目数量")
    percentage: float = Field(..., description="占比百分比")


class StatsOverview(BaseModel):
    """统计概览模型"""
    total_repositories: int = Field(..., description="总仓库数")
    total_trending_records: int = Field(..., description="总趋势记录数")
    total_ai_summaries: int = Field(..., description="总AI摘要数")
    languages: List[LanguageStats] = Field(default_factory=list, description="语言分布")


class APIResponse(BaseModel):
    """通用API响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


class ScoreDetail(BaseModel):
    """评分详情"""
    score: float = Field(..., ge=0, le=10, description="评分 0-10")
    reason: str = Field(..., description="评分依据")


class IntegrationExample(BaseModel):
    """集成示例"""
    scenario: str = Field(..., description="使用场景")
    code: str = Field(..., description="代码示例")


class FAQItem(BaseModel):
    """常见问题"""
    question: str = Field(..., description="问题")
    answer: str = Field(..., description="解答")


class DetailedAnalysisReport(BaseModel):
    """详细分析报告"""
    executive_summary: str = Field(..., description="执行摘要")
    scores: Dict[str, ScoreDetail] = Field(..., description="各维度评分")
    key_features: List[str] = Field(default_factory=list, description="核心功能")
    tech_stack: List[str] = Field(default_factory=list, description="技术栈")
    use_cases: List[str] = Field(default_factory=list, description="适用场景")
    limitations: List[str] = Field(default_factory=list, description="局限性")
    learning_resources: List[str] = Field(default_factory=list, description="学习资源")
    integration_examples: List[IntegrationExample] = Field(default_factory=list, description="集成示例")
    faq: List[FAQItem] = Field(default_factory=list, description="常见问题")


class AnalysisResponse(BaseModel):
    """分析报告响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[DetailedAnalysisReport] = Field(None, description="报告数据")
    model_used: Optional[str] = Field(None, description="使用的模型")
    generated_at: Optional[str] = Field(None, description="生成时间")
    error: Optional[str] = Field(None, description="错误信息")


class SchedulerJobInfo(BaseModel):
    """调度任务信息"""
    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    next_run: Optional[str] = Field(None, description="下次执行时间")


class SchedulerStatusUpdate(BaseModel):
    """调度器状态更新请求"""
    status: Literal["running", "stopped"] = Field(..., description="目标状态")


class TaskRunRequest(BaseModel):
    """手动触发任务请求"""
    task_type: Literal["daily", "weekly", "monthly"] = Field(..., description="任务类型 (daily/weekly/monthly)")


class TaskRunResponse(BaseModel):
    """任务提交响应（异步模式）"""
    task_id: str = Field(..., description="任务ID")
    task_type: Literal["daily", "weekly", "monthly"] = Field(..., description="任务类型")
    status: Literal["pending", "running", "success", "failed"] = Field(..., description="任务状态")
    message: str = Field(..., description="提示信息")


class TaskStatusResponse(BaseModel):
    """任务状态查询响应"""
    task_id: str = Field(..., description="任务ID")
    task_type: Literal["daily", "weekly", "monthly"] = Field(..., description="任务类型")
    status: Literal["pending", "running", "success", "failed"] = Field(..., description="任务状态")
    started_at: Optional[str] = Field(None, description="开始时间")
    finished_at: Optional[str] = Field(None, description="结束时间")
    repos_found: int = Field(0, description="发现的仓库数")
    repos_after_filter: int = Field(0, description="过滤后的仓库数")
    email_sent: bool = Field(False, description="邮件是否发送")
    error_message: Optional[str] = Field(None, description="错误信息")


class TaskHistoryItem(BaseModel):
    """任务执行历史项"""
    id: int = Field(..., description="记录ID")
    task_type: Literal["daily", "weekly", "monthly"] = Field(..., description="任务类型")
    started_at: str = Field(..., description="开始时间")
    finished_at: Optional[str] = Field(None, description="结束时间")
    status: Literal["pending", "running", "success", "failed"] = Field(..., description="任务状态")
    error_message: Optional[str] = Field(None, description="错误信息")


# ============ 统一设置模型 ============

class EmailSettings(BaseModel):
    """邮件设置（仅收件人列表，其他配置在 config.yaml）"""
    recipients: List[str] = Field(default_factory=list, description="收件人列表")


class SchedulerSettings(BaseModel):
    """调度器设置"""
    timezone: str = Field("Asia/Shanghai", description="时区")
    daily_enabled: bool = Field(True, description="每日任务是否启用")
    daily_time: str = Field("08:00", description="每日任务执行时间 (HH:MM)")
    weekly_enabled: bool = Field(True, description="每周任务是否启用")
    weekly_day: Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] = Field("sunday", description="每周任务执行日期")
    weekly_time: str = Field("22:00", description="每周任务执行时间 (HH:MM)")
    monthly_enabled: bool = Field(True, description="每月任务是否启用")
    monthly_time: str = Field("22:00", description="每月任务执行时间 (HH:MM)")

    @field_validator("daily_time", "weekly_time", "monthly_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Time must be in HH:MM format")
        hours, minutes = map(int, v.split(":"))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("Invalid time value")
        return v


class FilterSettings(BaseModel):
    """过滤器设置"""
    min_stars: int = Field(100, description="最小Star数")
    min_stars_daily: int = Field(50, description="每日最小新增Star数")
    min_stars_weekly: int = Field(200, description="每周最小新增Star数")
    min_stars_monthly: int = Field(500, description="每月最小新增Star数")


class SubscriptionSettings(BaseModel):
    """订阅设置"""
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    languages: List[str] = Field(default_factory=list, description="关注的编程语言")


class SettingsResponse(BaseModel):
    """统一设置响应模型"""
    email: EmailSettings = Field(default_factory=EmailSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    filters: FilterSettings = Field(default_factory=FilterSettings)
    subscription: SubscriptionSettings = Field(default_factory=SubscriptionSettings)
    scheduler_running: bool = Field(False, description="调度器是否运行中")
    next_run_times: Dict[str, Optional[str]] = Field(default_factory=dict, description="各任务下次执行时间")
    task_history: List[TaskHistoryItem] = Field(default_factory=list, description="最近执行历史")


class SettingsUpdateRequest(BaseModel):
    """设置更新请求模型（部分更新）"""
    email: Optional[EmailSettings] = None
    scheduler: Optional[SchedulerSettings] = None
    filters: Optional[FilterSettings] = None
    subscription: Optional[SubscriptionSettings] = None


# ============ Analytics 统计模型 ============

class DailyStats(BaseModel):
    """每日统计数据"""
    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    project_count: int = Field(0, description="新增项目数")
    total_stars: int = Field(0, description="总 Stars 数")


class HistoryStatsResponse(BaseModel):
    """历史统计响应"""
    days: int = Field(..., description="查询天数")
    data: List[DailyStats] = Field(default_factory=list, description="每日统计列表")


class WeekStats(BaseModel):
    """周统计数据"""
    projects: int = Field(0, description="项目数")
    stars: int = Field(0, description="总 Stars")
    avg_stars: int = Field(0, description="平均 Stars")


class ComparisonResponse(BaseModel):
    """周对比响应"""
    current: WeekStats = Field(..., description="本周数据")
    last: WeekStats = Field(..., description="上周数据")
    growth: Dict[str, float] = Field(default_factory=dict, description="增长率百分比")
