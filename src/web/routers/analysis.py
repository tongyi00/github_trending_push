"""Analysis endpoints router"""
import json
from fastapi import APIRouter, Request, Depends, Path, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..schemas import AnalysisResponse
from ...core.services.trending_service import TrendingService
from ...analyzers.async_ai_summarizer import AsyncAISummarizer

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])
limiter = Limiter(key_func=get_remote_address)

_ai_summarizer = None


def get_ai_summarizer() -> AsyncAISummarizer:
    global _ai_summarizer
    if _ai_summarizer is None:
        _ai_summarizer = AsyncAISummarizer()
    return _ai_summarizer


def get_trending_service(request: Request) -> TrendingService:
    return request.app.state.trending_service


def get_verify_token(request: Request):
    return request.app.state.verify_token


@router.get("/{owner}/{repo}", response_model=AnalysisResponse)
@limiter.limit("10/minute")
async def get_detailed_analysis(
    request: Request,
    owner: str = Path(..., pattern=r'^[a-zA-Z0-9_.-]+$', description="仓库所有者"),
    repo: str = Path(..., pattern=r'^[a-zA-Z0-9_.-]+$', description="仓库名称"),
    service: TrendingService = Depends(get_trending_service),
    current_user: dict = Depends(get_verify_token)
):
    """获取项目详细 AI 分析报告"""
    repo_data = service.get_repository_data(owner, repo)
    if not repo_data:
        raise HTTPException(status_code=404, detail=f"Repository '{owner}/{repo}' not found")

    try:
        summarizer = get_ai_summarizer()
        result = await summarizer.generate_detailed_report(repo_data)
        if not result['success']:
            return AnalysisResponse(success=False, error=result.get('error', 'Analysis generation failed'))
        return AnalysisResponse(success=True, data=result['report'], model_used=result['model_used'], generated_at=result['generated_at'])
    except Exception as e:
        logger.error(f"Failed to generate analysis for {repo_data['name']}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis generation failed")


@router.get("/{owner}/{repo}/stream")
@limiter.limit("5/minute")
async def get_detailed_analysis_stream(
    request: Request,
    owner: str = Path(..., pattern=r'^[a-zA-Z0-9_.-]+$', description="仓库所有者"),
    repo: str = Path(..., pattern=r'^[a-zA-Z0-9_.-]+$', description="仓库名称"),
    service: TrendingService = Depends(get_trending_service),
    current_user: dict = Depends(get_verify_token)
):
    """流式获取项目详细 AI 分析报告（SSE）"""
    repo_data = service.get_repository_data(owner, repo)
    if not repo_data:
        async def error_generator():
            yield f"event: error\ndata: {json.dumps({'message': f'Repository {owner}/{repo} not found'})}\n\n"
        return StreamingResponse(error_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})

    async def event_generator():
        try:
            summarizer = get_ai_summarizer()
            async for event in summarizer.generate_detailed_report_stream(repo_data):
                event_type = event.get('event', 'message')
                event_data = json.dumps(event.get('data', {}), ensure_ascii=False)
                yield f"event: {event_type}\ndata: {event_data}\n\n"
        except HTTPException as e:
            logger.warning(f"HTTP exception in stream for {repo_data['name']}: {e.detail}")
            yield f"event: error\ndata: {json.dumps({'message': e.detail})}\n\n"
        except Exception as e:
            logger.error(f"Unexpected error in stream for {repo_data['name']}: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'message': 'Internal server error'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})
