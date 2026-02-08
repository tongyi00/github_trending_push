#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Database and DataRepository 单元测试"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.models import Base, Repository, TrendingRecord
from src.core.database import DatabaseManager
from src.core.data_repository import DataRepository


@pytest.fixture
def in_memory_db():
    """创建内存数据库用于测试"""
    db = DatabaseManager(db_path=":memory:")
    db.init_db()
    yield db
    if hasattr(db, 'engine'):
        db.engine.dispose()


@pytest.fixture
def data_repo(in_memory_db):
    """创建 DataRepository 实例"""
    return DataRepository(in_memory_db)


class TestDatabaseManager:
    """DatabaseManager 测试类"""

    def test_database_initialization(self, in_memory_db):
        """测试数据库初始化"""
        assert in_memory_db.engine is not None
        assert in_memory_db.SessionLocal is not None

    def test_session_context_manager(self, in_memory_db):
        """测试会话上下文管理器"""
        with in_memory_db.get_session() as session:
            assert session is not None
            result = session.query(Repository).count()
            assert result == 0

    def test_transaction_rollback(self, in_memory_db):
        """测试事务回滚"""
        try:
            with in_memory_db.get_session() as session:
                repo = Repository(name="test/rollback", url="https://github.com/test/rollback")
                session.add(repo)
                session.flush()
                raise Exception("Force rollback")
        except Exception:
            pass
        with in_memory_db.get_session() as session:
            count = session.query(Repository).filter_by(name="test/rollback").count()
            assert count == 0


class TestDataRepository:
    """DataRepository 测试类"""

    def test_save_repository(self, data_repo):
        """测试保存仓库"""
        repo_data = {"name": "test/repo", "url": "https://github.com/test/repo", "description": "Test repository", "language": "Python", "stars": 100}
        repo_id = data_repo.save_repository(repo_data)
        assert repo_id is not None
        assert isinstance(repo_id, int)

    def test_batch_insert(self, data_repo):
        """测试批量插入"""
        repos = [{"name": f"test/repo{i}", "url": f"https://github.com/test/repo{i}", "language": "Python", "stars": i * 10} for i in range(5)]
        for repo in repos:
            data_repo.save_repository(repo)
        with data_repo.db_manager.get_session() as session:
            count = session.query(Repository).count()
            assert count == 5

    def test_query_filter_by_language(self, data_repo):
        """测试按语言过滤"""
        data_repo.save_repository({"name": "test/python", "url": "https://github.com/test/python", "language": "Python", "stars": 100})
        data_repo.save_repository({"name": "test/javascript", "url": "https://github.com/test/javascript", "language": "JavaScript", "stars": 200})
        with data_repo.db_manager.get_session() as session:
            python_repos = session.query(Repository).filter_by(language="Python").all()
            assert len(python_repos) == 1
            assert python_repos[0].name == "test/python"

    def test_pagination(self, data_repo):
        """测试分页功能"""
        for i in range(10):
            data_repo.save_repository({"name": f"test/repo{i}", "url": f"https://github.com/test/repo{i}", "stars": i})
        with data_repo.db_manager.get_session() as session:
            page1 = session.query(Repository).limit(5).offset(0).all()
            assert len(page1) == 5
            page2 = session.query(Repository).limit(5).offset(5).all()
            assert len(page2) == 5

    def test_unique_constraint_violation(self, data_repo):
        """测试唯一约束违反处理"""
        repo_data = {"name": "test/unique", "url": "https://github.com/test/unique", "stars": 100}
        data_repo.save_repository(repo_data)
        repo_data["stars"] = 200
        repo_id = data_repo.save_repository(repo_data)
        with data_repo.db_manager.get_session() as session:
            repo = session.query(Repository).filter_by(name="test/unique").first()
            assert repo.stars == 200

    def test_foreign_key_constraint(self, data_repo):
        """测试外键约束"""
        with data_repo.db_manager.get_session() as session:
            record = TrendingRecord(repository_id=9999, time_range="daily", record_date=datetime.now(timezone.utc), stars=100, forks=10)
            session.add(record)
            with pytest.raises(Exception):
                session.commit()
