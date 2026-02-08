import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from src.core.models import Base, Repository, TrendingRecord, AISummary
from src.core.database import DatabaseManager
from src.core.data_repository import DataRepository

class TestP0Performance:
    """P0 Performance Tests"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory SQLite database"""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def data_repo(self, db_session):
        """Create DataRepository with mocked DatabaseManager"""
        db_manager = MagicMock(spec=DatabaseManager)
        db_manager.get_session.return_value.__enter__.return_value = db_session
        return DataRepository(db_manager)

    def test_n_plus_1_query_elimination(self, db_session, data_repo):
        """Verify N+1 query issue is resolved in get_trending_records"""

        # 1. Setup Data: Create 20 repositories with trending records and summaries
        repos = []
        for i in range(20):
            repo = Repository(
                name=f"owner/repo-{i}",
                url=f"https://github.com/owner/repo-{i}",
                description=f"Description {i}",
                language="Python"
            )
            db_session.add(repo)
            repos.append(repo)

        db_session.flush()

        record_date = datetime.now()
        for repo in repos:
            record = TrendingRecord(
                repository_id=repo.id,
                time_range="daily",
                record_date=record_date,
                stars=100 + repo.id,
                forks=10 + repo.id,
                stars_increment=5
            )
            db_session.add(record)

            summary = AISummary(
                repository_id=repo.id,
                summary_text=f"AI Summary for {repo.name}",
                model_name="deepseek"
            )
            db_session.add(summary)

        db_session.commit()

        # 2. Setup Query Counter
        query_count = 0

        @event.listens_for(db_session.bind, 'before_cursor_execute')
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        # 3. Execute Query
        results, total = data_repo.get_trending_records(time_range="daily", limit=20)

        # 4. Verify Results
        assert len(results) == 20
        assert total == 20
        assert results[0]['has_ai_analysis'] is True

        # 5. Verify Query Count
        # Expected queries:
        # 1. Count query
        # 2. Main query for records + repositories (joined)
        # 3. Subquery for latest summary timestamps
        # 4. Query for summaries using timestamps
        # Total should be small constant (around 4-5), NOT 20+

        print(f"Total queries executed: {query_count}")
        assert query_count < 10, f"Too many queries executed: {query_count}. N+1 problem might exist."

