"""Statistics endpoints router"""
from typing import List
from fastapi import APIRouter, Request, Query, Depends, HTTPException
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..schemas import StatsOverview, LanguageStats, HistoryStatsResponse, ComparisonResponse, DailyStats
from ...core.services.stats_service import StatsService

router = APIRouter(prefix="/api/stats", tags=["Statistics"])
limiter = Limiter(key_func=get_remote_address)


def get_stats_service(request: Request) -> StatsService:
    return request.app.state.stats_service


def get_verify_token(request: Request):
    return request.app.state.verify_token


@router.get("/overview", response_model=StatsOverview)
@limiter.limit("30/minute")
async def get_stats_overview(
    request: Request,
    service: StatsService = Depends(get_stats_service),
    current_user: dict = Depends(get_verify_token)
):
    """获取统计概览"""
    try:
        stats_data = service.get_overview()
        return StatsOverview(**stats_data)
    except Exception as e:
        logger.error(f"Failed to get stats overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats overview")


@router.get("/languages", response_model=List[LanguageStats])
@limiter.limit("30/minute")
async def get_language_stats(
    request: Request,
    service: StatsService = Depends(get_stats_service),
    current_user: dict = Depends(get_verify_token)
):
    """获取语言分布统计"""
    try:
        return service.get_language_stats()
    except Exception as e:
        logger.error(f"Failed to get language stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get language stats")


@router.get("/history", response_model=HistoryStatsResponse)
@limiter.limit("30/minute")
async def get_history_stats(
    request: Request,
    days: int = Query(7, ge=1, le=90),
    service: StatsService = Depends(get_stats_service),
    current_user: dict = Depends(get_verify_token)
):
    """获取历史统计数据（按日期聚合）"""
    try:
        data = service.get_history_stats(days)
        return HistoryStatsResponse(days=days, data=data)
    except Exception as e:
        logger.error(f"Failed to get history stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get history stats")


@router.get("/comparison", response_model=ComparisonResponse)
@limiter.limit("30/minute")
async def get_week_comparison(
    request: Request,
    service: StatsService = Depends(get_stats_service),
    current_user: dict = Depends(get_verify_token)
):
    """获取周对比数据（本周 vs 上周）"""
    try:
        data = service.get_week_comparison()
        return ComparisonResponse(
            current=data['current'],
            last=data['last'],
            growth=data['growth']
        )
    except Exception as e:
        logger.error(f"Failed to get week comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to get week comparison")
