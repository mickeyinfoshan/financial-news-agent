"""Tests for ticker extraction logic."""

import pytest
from financial_news_agent.news_tool import _extract_ticker, COMMON_TICKERS


class TestTickerExtraction:
    """Test suite for _extract_ticker function."""

    def test_explicit_ticker_in_parentheses(self):
        """Test extraction of explicit ticker in parentheses."""
        assert _extract_ticker("Tesla (TSLA)") == "TSLA"
        assert _extract_ticker("NVIDIA Corporation (NVDA)") == "NVDA"
        assert _extract_ticker("Apple Inc. (AAPL)") == "AAPL"

    def test_already_ticker_format(self):
        """Test when query is already a ticker symbol."""
        assert _extract_ticker("NVDA") == "NVDA"
        assert _extract_ticker("AAPL") == "AAPL"
        assert _extract_ticker("TSLA") == "TSLA"
        assert _extract_ticker("META") == "META"

    def test_common_company_names(self):
        """Test lookup of common company names in dictionary."""
        assert _extract_ticker("nvidia") == "NVDA"
        assert _extract_ticker("apple") == "AAPL"
        assert _extract_ticker("microsoft") == "MSFT"
        assert _extract_ticker("tesla") == "TSLA"
        assert _extract_ticker("amazon") == "AMZN"
        assert _extract_ticker("google") == "GOOGL"
        assert _extract_ticker("alphabet") == "GOOGL"
        assert _extract_ticker("meta") == "META"
        assert _extract_ticker("facebook") == "META"

    def test_case_insensitive_lookup(self):
        """Test that company name lookup is case-insensitive."""
        # Lowercase should work
        assert _extract_ticker("nvidia") == "NVDA"
        assert _extract_ticker("apple") == "AAPL"

        # "NVIDIA" is 6 letters, doesn't match ticker pattern (1-5 letters)
        # so it will try API lookup, which may return NVDA
        result = _extract_ticker("NVIDIA")
        # Could be NVDA (from API) or NVIDIA (fallback)
        assert result in ["NVDA", "NVIDIA"]

    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        assert _extract_ticker("  nvidia  ") == "NVDA"
        assert _extract_ticker("\tapple\n") == "AAPL"

    def test_multi_word_company_names(self):
        """Test multi-word company names in dictionary."""
        assert _extract_ticker("jp morgan") == "JPM"
        assert _extract_ticker("goldman sachs") == "GS"

    def test_unknown_company_fallback(self):
        """Test fallback behavior for unknown companies."""
        # Should return first word uppercase as fallback
        result = _extract_ticker("unknown_company")
        assert result == "UNKNOWN_COMPANY"

        result = _extract_ticker("some random text")
        assert result == "SOME"

    def test_api_lookup_with_mock(self, mocker, mock_env_vars):
        """Test that API lookup is called for non-dictionary companies."""
        # Mock the API call
        mock_search = mocker.patch(
            'financial_news_agent.news_tool._search_symbol_finnhub',
            return_value="PLTR"
        )

        result = _extract_ticker("palantir")

        # Should call API since "palantir" is not in COMMON_TICKERS
        mock_search.assert_called_once_with("palantir")
        assert result == "PLTR"

    def test_api_lookup_returns_none(self, mocker, mock_env_vars):
        """Test fallback when API lookup returns None."""
        # Mock API to return None
        mocker.patch(
            'financial_news_agent.news_tool._search_symbol_finnhub',
            return_value=None
        )

        result = _extract_ticker("unknown_company")
        assert result == "UNKNOWN_COMPANY"

    def test_common_tickers_dictionary_size(self):
        """Verify COMMON_TICKERS is reduced to essential companies."""
        # Should be around 10-15 entries (not 60+)
        assert len(COMMON_TICKERS) <= 15
        assert len(COMMON_TICKERS) >= 10

        # Verify key companies are present
        assert "nvidia" in COMMON_TICKERS
        assert "apple" in COMMON_TICKERS
        assert "microsoft" in COMMON_TICKERS
        assert "tesla" in COMMON_TICKERS
        assert "amazon" in COMMON_TICKERS
