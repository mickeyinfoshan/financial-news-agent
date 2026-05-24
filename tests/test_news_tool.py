"""Tests for news_tool module."""

import requests

import pytest

from financial_news_agent.news_tool import (
    search_financial_news,
    get_tool_schema,
    execute_tool
)
from financial_news_agent.news_sources.finnhub import _search_symbol_finnhub
from financial_news_agent.news_sources.newsapi import _search_newsapi
from financial_news_agent.news_sources.finnhub import _search_finnhub_news


class TestSearchSymbolFinnhub:
    """Test suite for _search_symbol_finnhub function."""

    def test_api_key_missing(self, mocker, monkeypatch):
        """Test behavior when API key is not set."""
        monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
        result = _search_symbol_finnhub("nvidia")
        assert result is None

    def test_successful_lookup_common_stock(self, mocker, mock_env_vars, sample_finnhub_search_response):
        """Test successful symbol lookup returning Common Stock."""
        # Clear LRU cache to ensure fresh test
        _search_symbol_finnhub.cache_clear()

        mock_get = mocker.patch('requests.get')
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_finnhub_search_response
        mock_get.return_value = mock_response

        result = _search_symbol_finnhub("test_nvidia_lookup")
        assert result == "NVDA"

    def test_rate_limit_with_retry(self, mocker, mock_env_vars, sample_finnhub_search_response):
        """Test retry logic when hitting rate limit."""
        _search_symbol_finnhub.cache_clear()

        mock_get = mocker.patch('requests.get')
        mock_sleep = mocker.patch('time.sleep')

        # First call returns 429, second succeeds
        mock_response_429 = mocker.Mock()
        mock_response_429.status_code = 429

        mock_response_200 = mocker.Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = sample_finnhub_search_response

        mock_get.side_effect = [mock_response_429, mock_response_200]

        result = _search_symbol_finnhub("test_rate_limit")

        assert result == "NVDA"
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1

    def test_rate_limit_exhausted(self, mocker, mock_env_vars):
        """Test when rate limit persists after all retries."""
        _search_symbol_finnhub.cache_clear()

        mock_get = mocker.patch('requests.get')
        mock_sleep = mocker.patch('time.sleep')

        mock_response = mocker.Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        result = _search_symbol_finnhub("test_rate_exhausted")

        assert result is None
        assert mock_get.call_count == 3  # Initial + 2 retries

    def test_timeout_with_retry(self, mocker, mock_env_vars):
        """Test retry logic on timeout."""
        _search_symbol_finnhub.cache_clear()

        mock_get = mocker.patch('requests.get')
        mock_sleep = mocker.patch('time.sleep')

        mock_get.side_effect = requests.exceptions.Timeout("Timeout")

        result = _search_symbol_finnhub("test_timeout")

        # Should return None after retries
        assert result is None
        assert mock_get.call_count == 3  # Initial + 2 retries

    def test_empty_results(self, mocker, mock_env_vars):
        """Test when API returns no results."""
        _search_symbol_finnhub.cache_clear()

        mock_get = mocker.patch('requests.get')
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"count": 0, "result": []}
        mock_get.return_value = mock_response

        result = _search_symbol_finnhub("unknown_company_xyz")
        assert result is None


class TestSearchNewsAPI:
    """Test suite for _search_newsapi function."""

    def test_api_key_missing(self, mocker, monkeypatch):
        """Test behavior when API key is not set."""
        monkeypatch.delenv("NEWS_API_KEY", raising=False)
        result = _search_newsapi("nvidia")
        assert result == []

    def test_successful_search(self, mocker, mock_env_vars, sample_newsapi_response):
        """Test successful news search."""
        mock_get = mocker.patch('requests.get')
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_newsapi_response
        mock_get.return_value = mock_response

        result = _search_newsapi("nvidia", days_back=7)

        assert len(result) == 2
        assert result[0]["title"] == "NVIDIA Launches New Product"
        assert result[0]["api_source"] == "newsapi"
        assert result[1]["source"] == "Bloomberg"

    def test_api_error(self, mocker, mock_env_vars):
        """Test handling of API errors."""
        mock_get = mocker.patch('requests.get')
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = _search_newsapi("nvidia")
        assert result == []


class TestSearchFinnhubNews:
    """Test suite for _search_finnhub_news function."""

    def test_api_key_missing(self, mocker, monkeypatch):
        """Test behavior when API key is not set."""
        monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
        result = _search_finnhub_news("nvidia")
        assert result == []

    def test_successful_search(self, mocker, mock_env_vars, sample_finnhub_news_response):
        """Test successful news search."""
        mock_get = mocker.patch('requests.get')
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_finnhub_news_response
        mock_get.return_value = mock_response

        # Mock _extract_ticker to avoid API call
        mocker.patch('financial_news_agent.news_sources.finnhub._extract_ticker', return_value="NVDA")

        result = _search_finnhub_news("nvidia", days_back=7)

        assert len(result) == 2
        assert result[0]["title"] == "NVIDIA Announces New AI Chip"
        assert result[0]["api_source"] == "finnhub"
        assert result[0]["source"] == "Reuters"

    def test_api_error(self, mocker, mock_env_vars):
        """Test handling of API errors."""
        mock_get = mocker.patch('requests.get')
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        mocker.patch('financial_news_agent.news_sources.finnhub._extract_ticker', return_value="NVDA")

        result = _search_finnhub_news("nvidia")
        assert result == []


class TestSearchFinancialNews:
    """Test suite for search_financial_news function."""

    def test_parallel_search_both_sources(self, mocker, mock_env_vars, sample_newsapi_response, sample_finnhub_news_response):
        """Test parallel querying of both APIs."""
        # Mock both API calls
        mocker.patch('financial_news_agent.news_sources.finnhub._extract_ticker', return_value="NVDA")

        mock_newsapi = mocker.patch('financial_news_agent.news_sources.newsapi._search_newsapi')
        mock_newsapi.return_value = [
            {
                "title": "News 1",
                "url": "https://example.com/1",
                "published_at": "2026-05-22T10:00:00Z",
                "api_source": "newsapi"
            }
        ]

        mock_finnhub = mocker.patch('financial_news_agent.news_sources.finnhub._search_finnhub_news')
        mock_finnhub.return_value = [
            {
                "title": "News 2",
                "url": "https://example.com/2",
                "published_at": "2026-05-21T10:00:00Z",
                "api_source": "finnhub"
            }
        ]

        result = search_financial_news("nvidia", days_back=7)

        assert len(result) == 2
        mock_newsapi.assert_called_once()
        mock_finnhub.assert_called_once()

    def test_deduplication_by_url(self, mocker, mock_env_vars):
        """Test that duplicate URLs are removed."""
        mocker.patch('financial_news_agent.news_sources.finnhub._extract_ticker', return_value="NVDA")

        mock_newsapi = mocker.patch('financial_news_agent.news_sources.newsapi._search_newsapi')
        mock_newsapi.return_value = [
            {"title": "News 1", "url": "https://example.com/1", "published_at": "2026-05-22T10:00:00Z"}
        ]

        mock_finnhub = mocker.patch('financial_news_agent.news_sources.finnhub._search_finnhub_news')
        mock_finnhub.return_value = [
            {"title": "News 1 Duplicate", "url": "https://example.com/1", "published_at": "2026-05-22T10:00:00Z"}
        ]

        result = search_financial_news("nvidia")

        # Should only have 1 article after deduplication
        assert len(result) == 1

    def test_sorting_by_date(self, mocker, mock_env_vars):
        """Test that results are sorted by published date (most recent first)."""
        mocker.patch('financial_news_agent.news_sources.finnhub._extract_ticker', return_value="NVDA")

        mock_newsapi = mocker.patch('financial_news_agent.news_sources.newsapi._search_newsapi')
        mock_newsapi.return_value = [
            {"title": "Older", "url": "https://example.com/1", "published_at": "2026-05-20T10:00:00Z"}
        ]

        mock_finnhub = mocker.patch('financial_news_agent.news_sources.finnhub._search_finnhub_news')
        mock_finnhub.return_value = [
            {"title": "Newer", "url": "https://example.com/2", "published_at": "2026-05-22T10:00:00Z"}
        ]

        result = search_financial_news("nvidia")

        assert result[0]["title"] == "Newer"
        assert result[1]["title"] == "Older"


class TestToolSchema:
    """Test suite for tool schema and execution."""

    def test_get_tool_schema(self):
        """Test that tool schema is properly formatted."""
        schema = get_tool_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "search_financial_news"
        assert "query" in schema["function"]["parameters"]["properties"]
        assert "days_back" in schema["function"]["parameters"]["properties"]

    def test_execute_tool(self, mocker, mock_env_vars):
        """Test tool execution."""
        mock_search = mocker.patch('financial_news_agent.news_tool.search_financial_news')
        mock_search.return_value = [{"title": "Test"}]

        result = execute_tool("search_financial_news", {"query": "nvidia", "days_back": 7})

        mock_search.assert_called_once_with("nvidia", 7, None, None)
        assert result == [{"title": "Test"}]

    def test_execute_tool_unknown(self):
        """Test that unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            execute_tool("unknown_tool", {})
