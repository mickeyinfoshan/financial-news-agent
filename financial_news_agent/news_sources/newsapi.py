"""NewsAPI provider for financial news."""

import os
import logging
from datetime import datetime, timedelta
from typing import Any
import requests

from ..types import ArticleData
from ..traceability import TraceabilityTracker

logger = logging.getLogger(__name__)


def _search_newsapi(query: str, days_back: int = 7) -> list[ArticleData]:
    """
    Search for financial news using NewsAPI.

    Args:
        query: Search query (company, ticker, or industry)
        days_back: Number of days to search back

    Returns:
        List of news articles with metadata
    """
    api_key: str | None = os.getenv("NEWS_API_KEY")
    if not api_key:
        logger.warning("NEWS_API_KEY not set, skipping NewsAPI")
        return []

    # Calculate date range
    to_date: datetime = datetime.now()
    from_date: datetime = to_date - timedelta(days=min(days_back, 30))

    # NewsAPI endpoint
    url: str = "https://newsapi.org/v2/everything"
    params: dict[str, Any] = {
        "q": query,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": api_key,
        "pageSize": 10
    }

    try:
        response: requests.Response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        if data.get("status") != "ok":
            return []

        # Parse and structure articles
        articles: list[ArticleData] = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
                "content": article.get("content", ""),
                "api_source": "newsapi"
            })

        return articles

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from NewsAPI: {e}")
        return []


class NewsAPIProvider:
    """NewsAPI provider implementation."""

    @property
    def name(self) -> str:
        return "newsapi"

    @property
    def is_available(self) -> bool:
        return os.getenv("NEWS_API_KEY") is not None

    def search(
        self,
        query: str,
        days_back: int = 7,
        company_name: str | None = None,
        tracker: TraceabilityTracker | None = None
    ) -> list[ArticleData]:
        """Search NewsAPI."""
        if not self.is_available:
            logger.warning("NEWS_API_KEY not set, skipping NewsAPI")
            return []

        if tracker:
            with tracker.time_operation(
                f"{self.name.upper()} Request",
                "api_call",
                {"query": query, "days_back": days_back}
            ):
                return _search_newsapi(query, days_back)
        else:
            return _search_newsapi(query, days_back)
