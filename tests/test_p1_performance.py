import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.web.api import app
from src.core.data_repository import DataRepository

client = TestClient(app)

class TestP1Performance:
    """P1 阶段性能测试"""

    def test_pagination_limit(self):
        """验证分页限制 (page_size > 100 应失败)"""
        # 假设 headers 中包含 token
        headers = {"Authorization": "Bearer mock_token"}
        with patch("src.web.api.verify_token", return_value={"user": "test"}):
            response = client.get("/api/trending/daily?page_size=101", headers=headers)
            assert response.status_code == 422  # Validation Error

            response = client.get("/api/trending/daily?page_size=100", headers=headers)
            assert response.status_code != 422

    def test_map_lookup_performance(self):
        """验证 Map 查找性能 (N+1 问题) - 实际测试批量查询"""
        from sqlalchemy import create_engine, event
        from sqlalchemy.orm import sessionmaker
        from src.core.models import Base, Repository, TrendingRecord
        from src.core.database import DatabaseManager
        from datetime import datetime

        # 使用内存数据库进行真实测试
        db_manager = DatabaseManager(db_path=":memory:")
        db_manager.init_db()

        # 插入测试数据
        with db_manager.get_session() as session:
            for i in range(20):
                repo = Repository(name=f"test/repo-{i}", url=f"https://github.com/test/repo-{i}", description="Test", language="Python")
                session.add(repo)
                session.flush()
                record = TrendingRecord(repository_id=repo.id, time_range="daily", record_date=datetime.now(), stars=100+i, forks=10, stars_increment=5+i)
                session.add(record)

        # 使用查询计数器验证无 N+1
        query_count = [0]

        @event.listens_for(db_manager.engine, "before_cursor_execute")
        def count_queries(conn, cursor, statement, parameters, context, executemany):
            query_count[0] += 1

        repo = DataRepository(db_manager)
        records, total = repo.get_trending_records(time_range="daily", limit=20, offset=0)

        # 批量查询应该只有少量 SQL（<= 5: max_date, main query, summary subquery, summaries, count）
        assert query_count[0] <= 5, f"Too many queries: {query_count[0]}, possible N+1 problem"
        assert len(records) == 20
        db_manager.close()
