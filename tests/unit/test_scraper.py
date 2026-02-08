"""
Unit tests for GitHub Trending Scraper
"""
import pytest
from unittest.mock import patch, MagicMock
from src.collectors.scraper_trending import ScraperTrending


class TestScraperTrending:
    """Tests for ScraperTrending class"""

    def test_init(self):
        """Test scraper initialization"""
        scraper = ScraperTrending()
        assert scraper.headers is not None
        assert 'User-Agent' in scraper.headers
        assert scraper.session is not None

    def test_parse_number_simple(self):
        """Test parsing simple numbers"""
        scraper = ScraperTrending()
        assert scraper._parse_number("1234") == 1234
        assert scraper._parse_number("0") == 0
        assert scraper._parse_number("") == 0
        assert scraper._parse_number(None) == 0

    def test_parse_number_with_commas(self):
        """Test parsing numbers with comma separators"""
        scraper = ScraperTrending()
        assert scraper._parse_number("1,234") == 1234
        assert scraper._parse_number("12,345,678") == 12345678

    def test_parse_number_with_k_suffix(self):
        """Test parsing numbers with 'k' suffix (thousands)"""
        scraper = ScraperTrending()
        assert scraper._parse_number("1.2k") == 1200
        assert scraper._parse_number("5K") == 5000
        assert scraper._parse_number("10.5k") == 10500

    def test_parse_number_with_m_suffix(self):
        """Test parsing numbers with 'm' suffix (millions)"""
        scraper = ScraperTrending()
        assert scraper._parse_number("1.5m") == 1500000
        assert scraper._parse_number("2M") == 2000000

    def test_parse_number_with_text(self):
        """Test extracting numbers from text"""
        scraper = ScraperTrending()
        assert scraper._parse_number("89 stars today") == 89
        assert scraper._parse_number("Built by") == 0

    @patch('src.collectors.scraper_trending.check_robots_permission')
    def test_scrape_respects_robots_txt(self, mock_robots):
        """Test that scraper respects robots.txt"""
        mock_robots.return_value = False
        scraper = ScraperTrending()

        with patch.object(scraper.session, 'get') as mock_get:
            result = scraper.scrape_trending_by_range('daily')

            assert result == []
            mock_get.assert_not_called()

    @patch('src.collectors.scraper_trending.check_robots_permission')
    @patch('src.collectors.scraper_trending.get_recommended_delay')
    def test_scrape_with_mock_response(self, mock_delay, mock_robots, mock_html_trending_page):
        """Test scraping with mocked HTML response"""
        mock_robots.return_value = True
        mock_delay.return_value = None

        scraper = ScraperTrending()

        mock_response = MagicMock()
        mock_response.content = mock_html_trending_page.encode('utf-8')
        mock_response.raise_for_status = MagicMock()

        with patch.object(scraper.session, 'get', return_value=mock_response):
            result = scraper.scrape_trending_by_range('daily')

            # The mock HTML has one article
            assert isinstance(result, list)

    @patch('src.collectors.scraper_trending.check_robots_permission')
    @patch('src.collectors.scraper_trending.get_recommended_delay')
    def test_scrape_handles_request_error(self, mock_delay, mock_robots):
        """Test error handling for failed requests"""
        import requests
        mock_robots.return_value = True
        mock_delay.return_value = None

        scraper = ScraperTrending()

        with patch.object(scraper.session, 'get', side_effect=requests.RequestException("Network error")):
            result = scraper.scrape_trending_by_range('daily')
            assert result == []

    @patch('src.collectors.scraper_trending.check_robots_permission')
    @patch('src.collectors.scraper_trending.get_recommended_delay')
    def test_scrape_empty_page(self, mock_delay, mock_robots):
        """Test handling of empty trending page"""
        mock_robots.return_value = True
        mock_delay.return_value = None

        scraper = ScraperTrending()

        mock_response = MagicMock()
        mock_response.content = b"<html><body><div class='Box'></div></body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch.object(scraper.session, 'get', return_value=mock_response):
            result = scraper.scrape_trending_by_range('daily')
            assert result == []

    def test_time_ranges_mapping(self):
        """Test time range mappings are correct"""
        scraper = ScraperTrending()
        assert 'daily' in scraper.time_ranges
        assert 'weekly' in scraper.time_ranges
        assert 'monthly' in scraper.time_ranges
