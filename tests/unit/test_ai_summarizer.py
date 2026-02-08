"""
Unit tests for AsyncAISummarizer
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.analyzers.async_ai_summarizer import AsyncAISummarizer


class TestAsyncAISummarizer:
    """Tests for AsyncAISummarizer class"""

    @pytest.fixture
    def mock_config_file(self, tmp_path, mock_config):
        """Create a temporary config file"""
        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(mock_config, f)
        return str(config_file)

    @pytest.fixture
    def mock_ai_config(self):
        """Mock AI configuration"""
        return {
            'ai_models': {
                'enabled': ['deepseek'],
                'deepseek': {
                    'api_key': 'test-api-key',
                    'base_url': 'https://api.deepseek.com',
                    'model': 'deepseek-chat',
                    'temperature': 0.7,
                    'max_tokens': 500
                }
            },
            'prompt_template': 'Summarize: {name} - {description} ({language}, {stars} stars)'
        }

    def test_init_raises_error_for_missing_config(self):
        """Test initialization fails with missing config file"""
        with pytest.raises(FileNotFoundError):
            AsyncAISummarizer(config_path="nonexistent.yaml")

    def test_init_creates_clients_for_enabled_models(self, mock_config_file):
        """Test initialization creates clients for enabled models"""
        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI') as mock_openai:
            summarizer = AsyncAISummarizer(config_path=mock_config_file)

            assert 'deepseek' in summarizer.enabled_models
            assert summarizer.semaphore._value == 3  # default max_concurrent
            mock_openai.assert_called()

    def test_init_skips_models_without_api_key(self, tmp_path):
        """Test initialization skips models without API key"""
        config = {
            'ai_models': {
                'enabled': ['deepseek'],
                'deepseek': {
                    'api_key': '',
                    'base_url': 'https://api.deepseek.com'
                }
            },
            'prompt_template': 'Test {name}'
        }

        config_file = tmp_path / "config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI'):
            summarizer = AsyncAISummarizer(config_path=str(config_file))
            assert 'deepseek' not in summarizer.clients

    @pytest.mark.asyncio
    async def test_generate_summary_success(self, mock_config_file):
        """Test successful summary generation"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test summary"))]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            repo = {
                'name': 'test/repo',
                'description': 'Test description',
                'stars': 1000,
                'language': 'Python',
                'updated_at': '2026-02-08'
            }

            result = await summarizer.generate_summary(repo, 'deepseek')

            assert result == "Test summary"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_summary_returns_none_for_invalid_model(self, mock_config_file):
        """Test generate_summary returns None for unavailable model"""
        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI'):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)

            repo = {'name': 'test/repo', 'description': 'Test'}
            result = await summarizer.generate_summary(repo, 'nonexistent')

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_summary_retries_on_error(self, mock_config_file):
        """Test retry mechanism on API errors"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[
            Exception("API Error 1"),
            Exception("API Error 2"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="Success after retries"))])
        ])

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client), \
             patch('asyncio.sleep', new_callable=AsyncMock):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            repo = {'name': 'test/repo', 'description': 'Test', 'stars': 100, 'language': 'Python', 'updated_at': '2026-02-08'}
            result = await summarizer.generate_summary(repo, 'deepseek', retries=3)

            assert result == "Success after retries"
            assert mock_client.chat.completions.create.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_summary_returns_none_after_max_retries(self, mock_config_file):
        """Test returns None after exhausting all retries"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Persistent error"))

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client), \
             patch('asyncio.sleep', new_callable=AsyncMock):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            repo = {'name': 'test/repo', 'description': 'Test', 'stars': 100, 'language': 'Python', 'updated_at': '2026-02-08'}
            result = await summarizer.generate_summary(repo, 'deepseek', retries=2)

            assert result is None
            assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_summarize_empty_list(self, mock_config_file):
        """Test batch_summarize with empty repository list"""
        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI'):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)

            result = await summarizer.batch_summarize([])
            assert result == []

    @pytest.mark.asyncio
    async def test_batch_summarize_success(self, mock_config_file):
        """Test batch_summarize generates summaries for all repos"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[
                MagicMock(choices=[MagicMock(message=MagicMock(content="Summary 1"))]),
                MagicMock(choices=[MagicMock(message=MagicMock(content="Summary 2"))])
            ]
        )

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            repos = [
                {'name': 'test/repo1', 'description': 'Test 1', 'stars': 100, 'language': 'Python', 'updated_at': '2026-02-08'},
                {'name': 'test/repo2', 'description': 'Test 2', 'stars': 200, 'language': 'JavaScript', 'updated_at': '2026-02-08'}
            ]

            result = await summarizer.batch_summarize(repos, 'deepseek')

            assert len(result) == 2
            assert result[0]['ai_summary'] == "Summary 1"
            assert result[1]['ai_summary'] == "Summary 2"

    @pytest.mark.asyncio
    async def test_batch_summarize_handles_exceptions(self, mock_config_file):
        """Test batch_summarize handles exceptions gracefully"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client), \
             patch('asyncio.sleep', new_callable=AsyncMock):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            repos = [{'name': 'test/repo', 'description': 'Test description', 'stars': 100, 'language': 'Python', 'updated_at': '2026-02-08'}]
            result = await summarizer.batch_summarize(repos, 'deepseek')

            assert len(result) == 1
            assert 'Test description' in result[0]['ai_summary']

    @pytest.mark.asyncio
    async def test_batch_summarize_uses_default_model(self, mock_config_file):
        """Test batch_summarize uses first enabled model by default"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="Default summary"))])
        )

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            repos = [{'name': 'test/repo', 'description': 'Test', 'stars': 100, 'language': 'Python', 'updated_at': '2026-02-08'}]
            result = await summarizer.batch_summarize(repos)  # No model_name specified

            assert len(result) == 1
            assert result[0]['ai_summary'] == "Default summary"

    @pytest.mark.asyncio
    async def test_generate_detailed_report_success(self, mock_config_file):
        """Test generate_detailed_report returns structured report"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"executive_summary": "Test summary", "scores": {}}'))]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            repo_data = {'name': 'test/repo', 'description': 'Test', 'stars': 1000, 'forks': 100, 'language': 'Python'}
            result = await summarizer.generate_detailed_report(repo_data)

            assert result['success'] is True
            assert 'report' in result
            assert 'executive_summary' in result['report']

    @pytest.mark.asyncio
    async def test_generate_detailed_report_no_clients(self, mock_config_file):
        """Test generate_detailed_report fails when no clients available"""
        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI'):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients = {}  # Clear clients

            repo_data = {'name': 'test/repo'}
            result = await summarizer.generate_detailed_report(repo_data)

            assert result['success'] is False
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_parse_report_json_with_code_block(self, mock_config_file):
        """Test parsing JSON from markdown code block"""
        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI'):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)

            raw_content = '```json\n{"executive_summary": "Test"}\n```'
            result = summarizer._parse_report_json(raw_content)

            assert result['executive_summary'] == "Test"

    @pytest.mark.asyncio
    async def test_parse_report_json_fallback_on_invalid(self, mock_config_file):
        """Test fallback when JSON parsing fails"""
        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI'):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)

            raw_content = 'This is not valid JSON'
            result = summarizer._parse_report_json(raw_content)

            assert 'executive_summary' in result
            assert 'This is not valid JSON' in result['executive_summary']

    @pytest.mark.asyncio
    async def test_validate_report_structure_fills_missing_fields(self, mock_config_file):
        """Test report validation fills missing fields with defaults"""
        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI'):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)

            incomplete_report = {'executive_summary': 'Test'}
            result = summarizer._validate_report_structure(incomplete_report)

            assert 'scores' in result
            assert 'architecture' in result['scores']
            assert result['scores']['architecture']['score'] == 5.0

    @pytest.mark.asyncio
    async def test_close_closes_all_clients(self, mock_config_file):
        """Test close method closes all AI clients"""
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            await summarizer.close()

            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrent_requests(self, mock_config_file):
        """Test semaphore limits concurrent API calls"""
        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI'):
            summarizer = AsyncAISummarizer(config_path=mock_config_file, max_concurrent=2)

            assert summarizer.semaphore._value == 2

    @pytest.mark.asyncio
    async def test_generate_summary_handles_empty_input(self, mock_config_file):
        """Test generate_summary handles repositories with missing fields"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="Summary"))])
        )

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            repo = {'name': 'test/minimal'}  # Minimal repository data with only name
            result = await summarizer.generate_summary(repo, 'deepseek')

            assert result == "Summary"

    @pytest.mark.asyncio
    async def test_generate_summary_timeout_handling(self, mock_config_file):
        """Test timeout is properly configured in API calls"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="Summary"))])
        )

        with patch('src.analyzers.async_ai_summarizer.AsyncOpenAI', return_value=mock_client):
            summarizer = AsyncAISummarizer(config_path=mock_config_file)
            summarizer.clients['deepseek'] = mock_client

            repo = {'name': 'test/repo', 'description': 'Test', 'stars': 100, 'language': 'Python', 'updated_at': '2026-02-08'}
            await summarizer.generate_summary(repo, 'deepseek')

            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs['timeout'] == 30
