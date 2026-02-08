"""Trending endpoints router"""
import math
from typing import Optional, Literal
from fastapi import APIRouter, Request, Query, Depends, Path, HTTPException
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..schemas import TrendingListResponse, RepositorySchema
from ...core.services.trending_service import TrendingService

router = APIRouter(prefix="/api", tags=["Trending"])
limiter = Limiter(key_func=get_remote_address)


def get_trending_service(request: Request) -> TrendingService:
    return request.app.state.trending_service


def get_verify_token(request: Request):
    return request.app.state.verify_token


@router.get("/trending/{time_range}", response_model=TrendingListResponse)
@limiter.limit("30/minute")
async def get_trending(
    request: Request,
    time_range: Literal["daily", "weekly", "monthly"] = Path(..., description="时间范围 (daily/weekly/monthly)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    language: Optional[str] = Query(None),
    min_stars: Optional[int] = Query(None, ge=0),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service: TrendingService = Depends(get_trending_service),
    current_user: dict = Depends(get_verify_token)
):
    """获取趋势项目列表"""
    try:
        records, total = service.get_trending_list(
            time_range=time_range,
            page=page,
            page_size=page_size,
            language=language,
            min_stars=min_stars,
            start_date=start_date,
            end_date=end_date
        )
        items = [RepositorySchema(**record) for record in records]
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        return TrendingListResponse(total=total, page=page, page_size=page_size, total_pages=total_pages, items=items)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        logger.error(f"Failed to get trending records: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trending records")
