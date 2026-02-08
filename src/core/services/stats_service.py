from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy import func
from loguru import logger
from ..database import DatabaseManager
from ..data_repository import DataRepository
from ..models import Repository, TrendingRecord
from ...web.schemas import LanguageStats, DailyStats, WeekStats

class StatsService:
    def __init__(self, db_manager: DatabaseManager, data_repo: DataRepository):
        self.db_manager = db_manager
        self.data_repo = data_repo

    def get_overview(self) -> dict:
        """获取统计概览"""
        return self.data_repo.get_repository_stats()

    def get_language_stats(self) -> List[LanguageStats]:
        """获取语言分布统计"""
        with self.db_manager.get_session() as session:
            language_stats = session.query(
                Repository.language,
                func.count(Repository.id).label('count')
            ).filter(
                Repository.language.isnot(None)
            ).group_by(
                Repository.language
            ).order_by(
                func.count(Repository.id).desc()
            ).all()

            total_repos = sum(count for _, count in language_stats)
            return [
                LanguageStats(
                    language=lang,
                    count=count,
                    percentage=round((count / total_repos * 100), 2) if total_repos > 0 else 0
                ) for lang, count in language_stats
            ]

    def get_history_stats(self, days: int) -> List[DailyStats]:
        """获取历史统计数据"""
        with self.db_manager.get_session() as session:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            daily_stats = session.query(
                func.date(TrendingRecord.record_date).label('date'),
                func.count(TrendingRecord.id).label('project_count'),
                func.sum(TrendingRecord.stars).label('total_stars')
            ).filter(
                TrendingRecord.record_date >= start_date,
                TrendingRecord.time_range == 'daily'
            ).group_by(
                func.date(TrendingRecord.record_date)
            ).order_by(
                func.date(TrendingRecord.record_date)
            ).all()

            data = [
                DailyStats(
                    date=str(row.date),
                    project_count=row.project_count or 0,
                    total_stars=row.total_stars or 0
                ) for row in daily_stats
            ]

            # Fill missing dates with zeros
            result = []
            for i in range(days):
                date = (start_date + timedelta(days=i + 1)).strftime('%Y-%m-%d')
                existing = next((d for d in data if d.date == date), None)
                if existing:
                    result.append(existing)
                else:
                    result.append(DailyStats(date=date, project_count=0, total_stars=0))

            return result

    def get_week_comparison(self) -> dict:
        """获取周对比数据"""
        with self.db_manager.get_session() as session:
            today = datetime.now().date()
            this_week_start = today - timedelta(days=today.weekday())
            last_week_start = this_week_start - timedelta(days=7)
            last_week_end = this_week_start - timedelta(days=1)

            def get_week_stats(start, end) -> WeekStats:
                result = session.query(
                    func.count(TrendingRecord.id).label('projects'),
                    func.sum(TrendingRecord.stars).label('stars')
                ).filter(
                    func.date(TrendingRecord.record_date) >= start,
                    func.date(TrendingRecord.record_date) <= end,
                    TrendingRecord.time_range == 'daily'
                ).first()

                projects = result.projects or 0
                stars = result.stars or 0
                avg_stars = int(stars / projects) if projects > 0 else 0
                return WeekStats(projects=projects, stars=stars, avg_stars=avg_stars)

            current = get_week_stats(this_week_start, today)
            last = get_week_stats(last_week_start, last_week_end)

            def calc_growth(curr: int, prev: int) -> float:
                if prev == 0:
                    return 100.0 if curr > 0 else 0.0
                return round((curr - prev) / prev * 100, 1)

            growth = {
                'projects': calc_growth(current.projects, last.projects),
                'stars': calc_growth(current.stars, last.stars),
                'avgStars': calc_growth(current.avg_stars, last.avg_stars)
            }

            return {
                'current': current,
                'last': last,
                'growth': growth
            }
