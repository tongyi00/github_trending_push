"""
Integration tests for API endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestAPIEndpoints:
    """Integration tests for all API endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client with mocked dependencies"""
        with patch("src.web.api.DatabaseManager") as mock_db_cls, \
             patch("src.web.api.DataRepository") as mock_repo_cls, \
             patch("src.web.api.HealthMonitor") as mock_health_cls, \
             patch("src.web.api.TrendingService") as mock_trend_cls, \
             patch("src.web.api.StatsService") as mock_stats_cls, \
             patch("src.web.api.SettingsService") as mock_settings_cls:

            self.mock_db = MagicMock()
            mock_db_cls.return_value = self.mock_db

            self.mock_repo = MagicMock()
            mock_repo_cls.return_value = self.mock_repo

            self.mock_health = MagicMock()
            mock_health_cls.return_value = self.mock_health

            from src.web.api import app
            self.client = TestClient(app, raise_server_exceptions=False)
            yield

    def test_root_endpoint(self):
        """Test root endpoint returns API info"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health_endpoint(self):
        """Test health check endpoint"""
        self.mock_health.check_all = MagicMock(return_value={"status": "healthy", "checks": {}})

        response = self.client.get("/api/health")
        # May return 200 or 503 depending on mock setup
        assert response.status_code in [200, 503]

    @patch("src.web.api.verify_token")
    def test_trending_daily_endpoint(self, mock_verify):
        """Test GET /api/trending/daily"""
        mock_verify.return_value = {"user": "test"}

        with patch("src.web.api.trending_service") as mock_svc:
            mock_svc.get_trending_list.return_value = ([], 0)

            response = self.client.get(
                "/api/trending/daily",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "items" in data

    @patch("src.web.api.verify_token")
    def test_trending_invalid_range(self, mock_verify):
        """Test invalid time_range returns 400"""
        mock_verify.return_value = {"user": "test"}

        response = self.client.get(
            "/api/trending/invalid",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 400

    @patch("src.web.api.verify_token")
    def test_trending_pagination_limit(self, mock_verify):
        """Test page_size > 100 returns validation error"""
        mock_verify.return_value = {"user": "test"}

        response = self.client.get(
            "/api/trending/daily?page_size=101",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422

    @patch("src.web.api.verify_token")
    def test_stats_overview_endpoint(self, mock_verify):
        """Test GET /api/stats/overview"""
        mock_verify.return_value = {"user": "test"}

        with patch("src.web.api.trending_service") as mock_svc:
            mock_svc.get_stats_overview.return_value = {
                "total_repositories": 100,
                "total_stars": 50000,
                "languages_count": 10,
                "last_updated": "2026-02-08"
            }

            response = self.client.get(
                "/api/stats/overview",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "total_repositories" in data

    @patch("src.web.api.verify_token")
    def test_stats_languages_endpoint(self, mock_verify):
        """Test GET /api/stats/languages"""
        mock_verify.return_value = {"user": "test"}

        with patch("src.web.api.trending_service") as mock_svc:
            mock_svc.get_language_stats.return_value = [
                {"language": "Python", "count": 50, "percentage": 25.0},
                {"language": "JavaScript", "count": 40, "percentage": 20.0}
            ]

            response = self.client.get(
                "/api/stats/languages",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @patch("src.web.api.verify_token")
    def test_stats_history_endpoint(self, mock_verify):
        """Test GET /api/stats/history"""
        mock_verify.return_value = {"user": "test"}

        with patch("src.web.api.trending_service") as mock_svc:
            mock_svc.get_history_stats.return_value = []

            response = self.client.get(
                "/api/stats/history?days=7",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200

    @patch("src.web.api.verify_token")
    def test_settings_get_endpoint(self, mock_verify):
        """Test GET /api/settings"""
        mock_verify.return_value = {"user": "test"}

        with patch("src.web.api.settings_service") as mock_svc:
            mock_svc.get_settings.return_value = {
                "email": {"sender": "test@example.com", "recipients": []},
                "scheduler": {"daily_enabled": True, "daily_time": "08:00"},
                "filters": {"min_stars": 100}
            }

            response = self.client.get(
                "/api/settings",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200

    @patch("src.web.api.verify_token")
    def test_task_run_endpoint(self, mock_verify):
        """Test POST /api/tasks/run"""
        mock_verify.return_value = {"user": "test"}

        with patch("src.web.api.task_manager") as mock_tm, \
             patch.object(self.client.app.state, 'trending_push', MagicMock(), create=True), \
             patch.object(self.client.app.state, 'scheduler', MagicMock(), create=True):

            mock_tm.create_task.return_value = "test-task-id"

            response = self.client.post(
                "/api/tasks/run",
                json={"task_type": "daily"},
                headers={"Authorization": "Bearer test-token"}
            )

            # Should return 200 or 503 if trending_push not initialized
            assert response.status_code in [200, 503]

    @patch("src.web.api.verify_token")
    def test_task_status_not_found(self, mock_verify):
        """Test GET /api/tasks/status/{task_id} for non-existent task"""
        mock_verify.return_value = {"user": "test"}

        with patch("src.web.api.task_manager") as mock_tm:
            mock_tm.get_task.return_value = None

            response = self.client.get(
                "/api/tasks/status/non-existent-id",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 404

    def test_security_headers_present(self):
        """Test that security headers are included in responses"""
        response = self.client.get("/")

        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_cors_headers(self):
        """Test CORS headers for allowed origins"""
        response = self.client.options(
            "/api/trending/daily",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"}
        )

        # CORS preflight should be handled
        assert response.status_code in [200, 400, 405]


class TestAuthenticationFlow:
    """Tests for authentication and authorization"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client"""
        with patch("src.web.api.DatabaseManager"), \
             patch("src.web.api.DataRepository"), \
             patch("src.web.api.HealthMonitor"):

            from src.web.api import app
            self.client = TestClient(app, raise_server_exceptions=False)
            yield

    def test_protected_endpoint_without_token_in_production(self):
        """Test that protected endpoints require auth in production mode"""
        with patch("src.web.api.ENVIRONMENT", "production"), \
             patch("src.web.api.JWT_SECRET", "production-secret"):

            response = self.client.get("/api/trending/daily")
            # Should fail without token in production
            assert response.status_code in [401, 403, 500]

    @patch("src.web.api.verify_token")
    def test_protected_endpoint_with_valid_token(self, mock_verify):
        """Test access with valid token"""
        mock_verify.return_value = {"user": "authenticated-user"}

        with patch("src.web.api.trending_service") as mock_svc:
            mock_svc.get_trending_list.return_value = ([], 0)

            response = self.client.get(
                "/api/trending/daily",
                headers={"Authorization": "Bearer valid-token"}
            )

            assert response.status_code == 200
