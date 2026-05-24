"""Marketaux provider for financial news."""

import os
import logging
from datetime import datetime, timedelta
import requests

from ..types import ArticleData
from ..traceability import TraceabilityTracker
from .finnhub import COMMON_TICKERS, _search_symbol_finnhub

logger = logging.getLogger(__name__)


class MarketauxProvider:
    """Marketaux provider implementation.

    API: https://api.marketaux.com/v1/news/all
    """

    @property
    def name(self) -> str:
        return "marketaux"

    @property
    def is_available(self) -> bool:
        return os.getenv("MARKETAUX_API_KEY") is not None

    def search(
        self,
        query: str,
        days_back: int = 7,
        company_name: str | None = None,
        tracker: TraceabilityTracker | None = None
    ) -> list[ArticleData]:
        """Search Marketaux API."""
        if not self.is_available:
            logger.warning("MARKETAUX_API_KEY not set, skipping Marketaux")
            return []

        if tracker:
            with tracker.time_operation(
                f"{self.name.upper()} Request",
                "api_call",
                {"query": query, "days_back": days_back}
            ):
                return self._search_impl(query, days_back, company_name)
        else:
            return self._search_impl(query, days_back, company_name)

    def _search_impl(
        self,
        query: str,
        days_back: int,
        company_name: str | None
    ) -> list[ArticleData]:
        """Search Marketaux API implementation."""
        api_key = os.getenv("MARKETAUX_API_KEY")
        if not api_key:
            return []

        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=min(days_back, 30))

        url = "https://api.marketaux.com/v1/news/all"
        params: dict[str, str | int] = {
            "api_token": api_key,
            "search": query,
            "published_after": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "language": "en",
            "limit": 10
        }

        # Add symbols if we can extract a ticker
        if company_name:
            ticker = self._try_extract_ticker(company_name)
            if ticker:
                params["symbols"] = ticker

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse articles
            articles: list[ArticleData] = []
            for article in data.get("data", []):
                articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "source": article.get("source", "Unknown"),
                    "url": article.get("url", ""),
                    "published_at": article.get("published_at", ""),
                    "content": article.get("snippet", ""),
                    "api_source": "marketaux"
                })

            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Marketaux: {e}")
            return []

    def _try_extract_ticker(self, company_name: str) -> str | None:
        """Try to extract ticker from company name."""
        # Reuse existing COMMON_TICKERS dictionary
        if company_name.lower() in COMMON_TICKERS:
            return COMMON_TICKERS[company_name.lower()]

        # Try Finnhub lookup if available
        try:
            return _search_symbol_finnhub(company_name)
        except Exception:
            return None
