"""Finnhub provider for financial news with ticker resolution."""

import os
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Any
from functools import lru_cache
import requests

from ..types import ArticleData
from ..traceability import TraceabilityTracker

logger = logging.getLogger(__name__)

# Common company to ticker mapping (fast path for frequent queries)
COMMON_TICKERS: dict[str, str] = {
    "nvidia": "NVDA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "amazon": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "goldman sachs": "GS",
}


@lru_cache(maxsize=500)
def _search_symbol_finnhub(company_name: str, max_retries: int = 2) -> str | None:
    """
    Search for ticker symbol using Finnhub Symbol Search API with retry logic.

    Uses LRU cache to store up to 500 recent lookups in memory.

    Args:
        company_name: Company name to search for
        max_retries: Maximum number of retry attempts (default: 2)

    Returns:
        Ticker symbol if found, None otherwise
    """
    api_key: str | None = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return None

    url: str = "https://finnhub.io/api/v1/search"
    params: dict[str, str] = {
        "q": company_name,
        "token": api_key
    }

    for attempt in range(max_retries + 1):
        try:
            response: requests.Response = requests.get(url, params=params, timeout=5)

            # Handle API rate limiting
            if response.status_code == 429:
                if attempt < max_retries:
                    wait_time: int = 2 ** attempt
                    logger.warning(f"API rate limit hit for '{company_name}', retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API rate limit exceeded for '{company_name}'")
                    return None

            response.raise_for_status()
            data: dict[str, Any] = response.json()

            # Extract first result (highest relevance)
            if data.get("count", 0) > 0:
                results: list[dict[str, Any]] = data.get("result", [])

                # Prefer Common Stock over ADRs and other types
                for result in results:
                    if result.get("type") == "Common Stock":
                        symbol: str | None = result.get("symbol")
                        if symbol:
                            logger.info(f"Found ticker via API: {company_name} -> {symbol}")
                            return symbol

                # Fallback to first result if no Common Stock found
                if results:
                    symbol = results[0].get("symbol")
                    if symbol:
                        logger.info(f"Found ticker via API (non-stock): {company_name} -> {symbol}")
                        return str(symbol)

            return None

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                logger.warning(f"Timeout searching for '{company_name}' (attempt {attempt + 1}/{max_retries + 1}), retrying...")
                time.sleep(1)
                continue
            else:
                logger.error(f"Timeout searching for '{company_name}' after {max_retries + 1} attempts")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Finnhub for '{company_name}': {e}")
            return None

    return None


def _extract_ticker(query: str) -> str:
    """
    Extract or map ticker symbol from query.

    Uses a hybrid approach (API-first strategy):
    1. Check for explicit ticker in parentheses
    2. Check if query is already a ticker
    3. Try common tickers dictionary (fast path for frequent queries)
    4. Extract first 1-2 words if query is too long (prevents 422 errors)
    5. Try Finnhub Symbol Search API (primary lookup method)
    6. Fallback to first word

    Args:
        query: Search query (company name, ticker, or mixed)

    Returns:
        Ticker symbol (uppercase)
    """
    # Check for ticker in parentheses: "Tesla (TSLA)" -> "TSLA"
    paren_match = re.search(r'\(([A-Z]{1,5})\)', query)
    if paren_match:
        return paren_match.group(1)

    # Check if query is already a ticker (all caps, 1-5 letters)
    if re.match(r'^[A-Z]{1,5}$', query.strip()):
        return query.strip()

    # Try common tickers dictionary (fast path - no API call)
    query_lower = query.lower().strip()
    if query_lower in COMMON_TICKERS:
        return COMMON_TICKERS[query_lower]

    # If query is too long (>50 chars or >3 words), extract company name
    # This prevents 422 errors from Finnhub Symbol Search API
    words: list[str] = query.strip().split()
    company_name: str
    if len(query) > 50 or len(words) > 3:
        # Take first word as company name
        company_name = words[0] if words else query.strip()
        # If second word is also capitalized, include it (e.g., "Goldman Sachs")
        if len(words) > 1 and words[1][0].isupper():
            company_name = f"{words[0]} {words[1]}"
    else:
        company_name = query.strip()

    # Try dynamic lookup via Finnhub Symbol Search API (primary method)
    symbol: str | None = _search_symbol_finnhub(company_name)
    if symbol:
        return symbol

    # Final fallback: return first word as ticker (uppercase)
    return words[0].strip().upper() if words else query.strip().upper()


def _search_finnhub_news(query: str, days_back: int = 7, company_name: str | None = None) -> list[ArticleData]:
    """
    Search for financial news using Finnhub.

    Args:
        query: Search query (company name or ticker)
        days_back: Number of days to search back
        company_name: Optional company name for ticker lookup (if not provided, uses query)

    Returns:
        List of news articles with metadata
    """
    api_key: str | None = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        logger.warning("FINNHUB_API_KEY not set, skipping Finnhub")
        return []

    # Extract ticker from company_name if provided, otherwise from query
    ticker: str = _extract_ticker(company_name if company_name else query)

    # Calculate date range
    to_date: datetime = datetime.now()
    from_date: datetime = to_date - timedelta(days=min(days_back, 30))

    # Finnhub company news endpoint
    url: str = "https://finnhub.io/api/v1/company-news"
    params: dict[str, Any] = {
        "symbol": ticker,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "token": api_key
    }

    try:
        response: requests.Response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json()

        # Parse and normalize articles
        articles: list[ArticleData] = []
        for article in data:
            # Convert Unix timestamp to ISO 8601
            timestamp: int | float = article.get("datetime", 0)
            published_at: str = datetime.fromtimestamp(timestamp).isoformat() if timestamp else ""

            articles.append({
                "title": article.get("headline", ""),
                "description": article.get("summary", ""),
                "source": article.get("source", "Unknown"),
                "url": article.get("url", ""),
                "published_at": published_at,
                "content": article.get("summary", ""),
                "api_source": "finnhub"
            })

        return articles

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from Finnhub: {e}")
        return []


class FinnhubProvider:
    """Finnhub provider with ticker resolution."""

    @property
    def name(self) -> str:
        return "finnhub"

    @property
    def is_available(self) -> bool:
        return os.getenv("FINNHUB_API_KEY") is not None

    def search(
        self,
        query: str,
        days_back: int = 7,
        company_name: str | None = None,
        tracker: TraceabilityTracker | None = None
    ) -> list[ArticleData]:
        """Search Finnhub with ticker resolution."""
        if not self.is_available:
            logger.warning("FINNHUB_API_KEY not set, skipping Finnhub")
            return []

        if tracker:
            metadata: dict[str, Any] = {
                "query": query,
                "days_back": days_back,
                "company_name": company_name
            }
            with tracker.time_operation(
                f"{self.name.upper()} Request",
                "api_call",
                metadata
            ):
                return _search_finnhub_news(query, days_back, company_name)
        else:
            return _search_finnhub_news(query, days_back, company_name)
