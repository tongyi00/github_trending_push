from typing import Optional, List, Dict, Tuple
from datetime import datetime
from loguru import logger
from ..database import DatabaseManager
from ..data_repository import DataRepository
from ..models import Repository, TrendingRecord

class TrendingService:
    def __init__(self, db_manager: DatabaseManager, data_repo: DataRepository):
        self.db_manager = db_manager
        self.data_repo = data_repo

    def get_trending_list(self,
                          time_range: str,
                          page: int = 1,
                          page_size: int = 20,
                          language: Optional[str] = None,
                          min_stars: Optional[int] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> Tuple[List[Dict], int]:
        """获取趋势项目列表"""
        start_dt = None
        end_dt = None

        try:
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            logger.warning(f"Invalid date format: {e}")
            return [], 0

        offset = (page - 1) * page_size
        return self.data_repo.get_trending_records(
            time_range=time_range,
            start_date=start_dt,
            end_date=end_dt,
            language=language,
            min_stars=min_stars,
            limit=page_size,
            offset=offset
        )

    def get_repository_data(self, owner: str, repo: str) -> Optional[Dict]:
        """获取仓库详情"""
        full_name = f"{owner}/{repo}"

        with self.db_manager.get_session() as session:
            repo_record = session.query(Repository).filter_by(name=full_name).first()
            if not repo_record:
                return None

            latest_trending = session.query(TrendingRecord).filter_by(
                repository_id=repo_record.id
            ).order_by(TrendingRecord.record_date.desc()).first()

            return {
                'name': repo_record.name,
                'url': repo_record.url,
                'description': repo_record.description,
                'language': repo_record.language,
                'stars': latest_trending.stars if latest_trending else 0,
                'forks': latest_trending.forks if latest_trending else 0
            }
