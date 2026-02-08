#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据仓库层 - 封装数据库操作
"""

from loguru import logger
from datetime import datetime
from sqlalchemy import and_, func
from sqlalchemy.orm import Query
from .database import DatabaseManager
from ..constants import SUMMARY_PREVIEW_LENGTH
from typing import List, Optional, Dict, Tuple, Any
from .models import Repository, TrendingRecord, AISummary


class DataRepository:
    """数据仓库 - 提供高层数据访问接口"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_trending_data(self, repos: List[Dict], time_range: str, record_date: Optional[datetime] = None, batch_size: int = 10) -> int:
        """保存趋势数据（分批处理避免长事务）"""
        if record_date is None:
            record_date = datetime.now()

        saved_count = 0
        total_batches = (len(repos) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(repos))
            batch_repos = repos[start_idx:end_idx]

            with self.db.get_session() as session:
                # 1. 批量查询 Repositories
                repo_names = [r['name'] for r in batch_repos]
                existing_repos = session.query(Repository).filter(Repository.name.in_(repo_names)).all()
                repo_map = {r.name: r for r in existing_repos}

                # 2. 更新或创建 Repositories
                current_batch_repos = []  # 保存当前批次的 repo 对象，用于后续查询记录
                for repo_data in batch_repos:
                    name = repo_data['name']
                    repo = repo_map.get(name)

                    if not repo:
                        repo = Repository(
                            name=name,
                            url=repo_data['url'],
                            description=repo_data.get('description', ''),
                            language=repo_data.get('language', '')
                        )
                        session.add(repo)
                        # 注意：此时 repo.id 为 None，需要 flush
                        repo_map[name] = repo
                    else:
                        repo.description = repo_data.get('description', repo.description)
                        repo.language = repo_data.get('language', repo.language)
                        repo.last_updated_at = datetime.now()

                    current_batch_repos.append(repo)

                # 提交以获取新创建的 repo.id
                session.flush()

                # 3. 批量查询 TrendingRecords
                repo_ids = [r.id for r in current_batch_repos]
                existing_records = session.query(TrendingRecord).filter(
                    TrendingRecord.repository_id.in_(repo_ids),
                    TrendingRecord.time_range == time_range,
                    func.date(TrendingRecord.record_date) == record_date.date()
                ).all()

                record_map = {r.repository_id: r for r in existing_records}

                # 4. 创建不存在的 TrendingRecords
                for repo_data in batch_repos:
                    repo = repo_map.get(repo_data['name'])
                    if not repo:
                        continue # Should not happen

                    if repo.id not in record_map:
                        trending_record = TrendingRecord(
                            repository_id=repo.id,
                            time_range=time_range,
                            record_date=record_date,
                            stars=repo_data.get('stars', 0),
                            forks=repo_data.get('forks', 0),
                            stars_increment=repo_data.get('stars_daily', 0)
                        )
                        session.add(trending_record)
                        saved_count += 1

            logger.debug(f"Batch {batch_idx + 1}/{total_batches} saved")

        logger.info(f"Saved {saved_count} new trending records for {time_range}")
        return saved_count

    def get_seen_projects(self, time_range: str) -> set:
        """获取指定时间范围内已见过的项目名称"""
        with self.db.get_session() as session:
            records = session.query(Repository.name).join(TrendingRecord).filter(TrendingRecord.time_range == time_range).distinct().all()
            return {record[0] for record in records}

    def _get_latest_date(self, session, time_range: str, start_date: Optional[datetime], end_date: Optional[datetime]) -> Optional[datetime]:
        """获取指定时间范围内的最新记录日期"""
        latest_date_query = session.query(func.max(TrendingRecord.record_date)).filter(TrendingRecord.time_range == time_range)
        if start_date:
            latest_date_query = latest_date_query.filter(TrendingRecord.record_date >= start_date)
        if end_date:
            latest_date_query = latest_date_query.filter(TrendingRecord.record_date <= end_date)
        return latest_date_query.scalar()

    def _build_filter_query(self, session, time_range: str, target_date: datetime, language: Optional[str], min_stars: Optional[int]):
        """构建过滤查询"""
        query = session.query(TrendingRecord, Repository).join(Repository)
        query = query.filter(TrendingRecord.time_range == time_range, TrendingRecord.record_date == target_date)
        if language:
            query = query.filter(func.lower(Repository.language) == language.lower())
        if min_stars is not None:
            query = query.filter(TrendingRecord.stars >= min_stars)
        return query

    def _fetch_records_with_count(self, query, limit: int, offset: int) -> Tuple[List[Tuple], int]:
        """获取记录和总数（使用 window function 优化）"""
        from sqlalchemy import over
        count_column = func.count().over().label('total_count')
        query = query.add_columns(count_column)
        query = query.order_by(TrendingRecord.record_date.desc(), TrendingRecord.stars_increment.desc())
        if limit > 0:
            query = query.limit(limit).offset(offset)
        results_with_count = query.yield_per(50).all()
        total = results_with_count[0][2] if results_with_count else 0
        records_and_repos = [(row[0], row[1]) for row in results_with_count]
        return records_and_repos, total

    def _fetch_ai_summaries(self, session, repo_ids: List[int]) -> Dict[int, str]:
        """批量获取最新的AI摘要"""
        from sqlalchemy import func as sqla_func
        latest_summary_subq = session.query(AISummary.repository_id, sqla_func.max(AISummary.created_at).label('max_created')).filter(AISummary.repository_id.in_(repo_ids)).group_by(AISummary.repository_id).subquery()
        summaries = session.query(AISummary).join(latest_summary_subq, and_(AISummary.repository_id == latest_summary_subq.c.repository_id, AISummary.created_at == latest_summary_subq.c.max_created)).all()
        return {s.repository_id: s.summary_text for s in summaries}

    def _format_to_dicts(self, records_and_repos: List[Tuple], summary_map: Dict[int, str]) -> List[Dict]:
        """格式化记录为字典列表"""
        results = []
        for record, repo in records_and_repos:
            ai_summary = summary_map.get(repo.id)
            results.append({
                'name': repo.name,
                'url': repo.url,
                'description': repo.description,
                'language': repo.language,
                'stars': record.stars,
                'forks': record.forks,
                'stars_increment': record.stars_increment,
                'time_range': record.time_range,
                'record_date': record.record_date.strftime('%Y-%m-%d'),
                'ai_summary': ai_summary,
                'has_ai_analysis': ai_summary is not None,
            })
        return results

    def get_trending_records(self, time_range: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             language: Optional[str] = None,
                             min_stars: Optional[int] = None,
                             limit: int = 20,
                             offset: int = 0) -> Tuple[List[Dict], int]:
        """查询趋势记录（包含AI摘要，支持分页和过滤）"""
        with self.db.get_session() as session:
            target_date = self._get_latest_date(session, time_range, start_date, end_date)
            if not target_date:
                return [], 0

            query = self._build_filter_query(session, time_range, target_date, language, min_stars)
            records_and_repos, total = self._fetch_records_with_count(query, limit, offset)

            if not records_and_repos:
                return [], total

            repo_ids = [repo.id for _, repo in records_and_repos]
            summary_map = self._fetch_ai_summaries(session, repo_ids)
            results = self._format_to_dicts(records_and_repos, summary_map)

            return results, total

    def save_ai_summary(self, repo_name: str, summary_text: str, model_name: Optional[str] = None) -> bool:
        """保存AI摘要"""
        with self.db.get_session() as session:
            repo = session.query(Repository).filter_by(name=repo_name).first()

            if not repo:
                logger.warning(f"Repository {repo_name} not found, cannot save summary")
                return False

            summary = AISummary(
                repository_id=repo.id,
                summary_text=summary_text,
                model_name=model_name
            )
            session.add(summary)

        logger.info(f"AI summary saved for {repo_name}")
        return True

    def get_latest_summary(self, repo_name: str) -> Optional[str]:
        """获取最新的AI摘要"""
        with self.db.get_session() as session:
            result = session.query(AISummary.summary_text).join(Repository).filter(Repository.name == repo_name).order_by(AISummary.created_at.desc()).first()
            return result[0] if result else None

    def get_summary_with_metadata(self, repo_name: str) -> Optional[Dict]:
        """获取最新的AI摘要及元数据"""
        with self.db.get_session() as session:
            result = session.query(AISummary, Repository).join(Repository).filter(Repository.name == repo_name).order_by(AISummary.created_at.desc()).first()

            if not result:
                return None

            summary, repo = result
            return {
                'summary_text': summary.summary_text,
                'model_name': summary.model_name,
                'created_at': summary.created_at,
                'description': repo.description,
                'last_updated_at': repo.last_updated_at
            }

    def get_latest_stars(self, repo_name: str) -> Optional[int]:
        """获取项目最新的Stars数"""
        with self.db.get_session() as session:
            result = session.query(TrendingRecord.stars).join(Repository).filter(Repository.name == repo_name).order_by(TrendingRecord.record_date.desc()).first()
            return result[0] if result else None

    def get_repository_stats(self) -> Dict:
        """获取仓库统计信息"""
        with self.db.get_session() as session:
            total_repos = session.query(func.count(Repository.id)).scalar()
            total_records = session.query(func.count(TrendingRecord.id)).scalar()
            total_summaries = session.query(func.count(AISummary.id)).scalar()

            return {
                'total_repositories': total_repos,
                'total_trending_records': total_records,
                'total_ai_summaries': total_summaries
            }
