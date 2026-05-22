"""Integration tests requiring real API keys.

These tests are marked with @pytest.mark.integration and are skipped
unless real API keys are available in the environment.

Run with: uv run pytest tests/test_integration.py -v -m integration
"""

import os
import pytest
from financial_news_agent.news_tool import (
    _search_symbol_finnhub,
    _search_finnhub_news,
    _search_newsapi,
    search_financial_news
)


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("FINNHUB_API_KEY"),
    reason="Requires real FINNHUB_API_KEY"
)
class TestFinnhubIntegration:
    """Integration tests for Finnhub API."""

    def test_real_symbol_search(self):
        """Test real Finnhub symbol search API."""
        result = _search_symbol_finnhub("palantir")
        assert result is not None
        assert isinstance(result, str)
        assert len(result) <= 5  # Valid ticker length

    def test_real_news_search(self):
        """Test real Finnhub news API."""
        articles = _search_finnhub_news("NVDA", days_back=7)
        assert isinstance(articles, list)

        if len(articles) > 0:
            article = articles[0]
            assert "title" in article
            assert "url" in article
            assert "api_source" in article
            assert article["api_source"] == "finnhub"


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("NEWS_API_KEY"),
    reason="Requires real NEWS_API_KEY"
)
class TestNewsAPIIntegration:
    """Integration tests for NewsAPI."""

    def test_real_news_search(self):
        """Test real NewsAPI search."""
        articles = _search_newsapi("NVIDIA", days_back=7)
        assert isinstance(articles, list)

        if len(articles) > 0:
            article = articles[0]
            assert "title" in article
            assert "url" in article
            assert "api_source" in article
            assert article["api_source"] == "newsapi"


@pytest.mark.integration
@pytest.mark.skipif(
    not (os.getenv("FINNHUB_API_KEY") and os.getenv("NEWS_API_KEY")),
    reason="Requires both FINNHUB_API_KEY and NEWS_API_KEY"
)
class TestCombinedIntegration:
    """Integration tests for combined news search."""

    def test_real_combined_search(self):
        """Test real combined search from both APIs."""
        articles = search_financial_news("NVIDIA", days_back=7)

        assert isinstance(articles, list)
        assert len(articles) <= 20  # Should return top 20

        if len(articles) > 0:
            # Check that articles have required fields
            article = articles[0]
            assert "title" in article
            assert "url" in article
            assert "api_source" in article
            assert article["api_source"] in ["newsapi", "finnhub"]

            # Check for deduplication (all URLs should be unique)
            urls = [a["url"] for a in articles]
            assert len(urls) == len(set(urls))

            # Check sorting (dates should be in descending order)
            dates = [a.get("published_at", "") for a in articles if a.get("published_at")]
            if len(dates) > 1:
                for i in range(len(dates) - 1):
                    assert dates[i] >= dates[i + 1], "Articles should be sorted by date (newest first)"

    def test_real_ticker_extraction_with_api(self):
        """Test ticker extraction using real API for unknown companies."""
        from financial_news_agent.news_tool import _extract_ticker

        # Test with a company not in COMMON_TICKERS
        result = _extract_ticker("snowflake")
        assert result is not None
        assert isinstance(result, str)
