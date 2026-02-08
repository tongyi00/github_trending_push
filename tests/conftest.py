"""
Shared pytest fixtures for all test modules
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.models import Base, Repository, TrendingRecord, AISummary
from src.core.database import DatabaseManager


@pytest.fixture
def sample_repository_data():
    """Sample repository data for testing"""
    return {
        "name": "test/repo",
        "url": "https://github.com/test/repo",
        "description": "Test description for a sample repository",
        "language": "Python",
        "stars": 1500,
        "forks": 100,
        "stars_daily": 50,
        "updated_at": "2026-02-08"
    }


@pytest.fixture
def sample_repository_list():
    """List of sample repositories for batch testing"""
    return [
        {"name": "user1/project-a", "url": "https://github.com/user1/project-a", "description": "Project A", "language": "Python", "stars": 5000, "forks": 200, "stars_daily": 100},
        {"name": "user2/project-b", "url": "https://github.com/user2/project-b", "description": "Project B", "language": "JavaScript", "stars": 3000, "forks": 150, "stars_daily": 80},
        {"name": "user3/project-c", "url": "https://github.com/user3/project-c", "description": "Project C", "language": "Rust", "stars": 2000, "forks": 50, "stars_daily": 60},
    ]


@pytest.fixture
def mock_db_session():
    """In-memory SQLite session for isolated database tests"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def db_manager_memory():
    """DatabaseManager with in-memory SQLite for integration tests"""
    manager = DatabaseManager(db_path=":memory:")
    manager.init_db()
    yield manager
    manager.close()


@pytest.fixture
def populated_db(db_manager_memory):
    """Database pre-populated with sample data"""
    with db_manager_memory.get_session() as session:
        for i in range(5):
            repo = Repository(
                name=f"test/repo-{i}",
                url=f"https://github.com/test/repo-{i}",
                description=f"Test repository {i}",
                language="Python" if i % 2 == 0 else "JavaScript"
            )
            session.add(repo)
            session.flush()

            record = TrendingRecord(
                repository_id=repo.id,
                time_range="daily",
                record_date=datetime.now(),
                stars=1000 + i * 100,
                forks=50 + i * 10,
                stars_increment=20 + i * 5
            )
            session.add(record)

            if i < 3:
                summary = AISummary(
                    repository_id=repo.id,
                    summary_text=f"AI summary for repo {i}",
                    model_name="deepseek"
                )
                session.add(summary)

    return db_manager_memory


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "github": {"token": "test-token"},
        "email": {
            "sender": "test@example.com",
            "password": "test-password",
            "recipients": ["recipient@example.com"],
            "smtp_server": "smtp.example.com",
            "smtp_port": 465
        },
        "ai_models": {
            "enabled": ["deepseek"],
            "deepseek": {
                "api_key": "test-key",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 500
            }
        },
        "prompt_template": "Summarize project: {name} - {description} (Language: {language}, Stars: {stars}, Updated: {updated_at})",
        "scheduler": {
            "daily": {"enabled": True, "time": "08:00"},
            "weekly": {"enabled": True, "day": "sunday", "time": "22:00"},
            "monthly": {"enabled": True, "time": "22:00"}
        },
        "filters": {"min_stars": 100}
    }


@pytest.fixture
def mock_html_trending_page():
    """Mock HTML response from GitHub Trending page"""
    return """
    <div class="Box">
        <article class="Box-row">
            <h2 class="h3 lh-condensed">
                <a href="/test-org/test-repo">test-org / test-repo</a>
            </h2>
            <p class="col-9 color-fg-muted my-1 pr-4">A test repository for testing</p>
            <span itemprop="programmingLanguage">Python</span>
            <a class="Link--muted d-inline-block mr-3">
                <svg class="octicon octicon-star"></svg>
                1,234
            </a>
            <a class="Link--muted d-inline-block mr-3">
                <svg class="octicon octicon-repo-forked"></svg>
                567
            </a>
            <span class="d-inline-block float-sm-right">89 stars today</span>
        </article>
    </div>
    """
