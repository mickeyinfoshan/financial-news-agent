"""News search tool using NewsAPI and Finnhub."""

import os
import re
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import requests
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Common company to ticker mapping (fast path for frequent queries)
# Reduced to most common companies; API lookup handles the rest
COMMON_TICKERS = {
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
def _search_symbol_finnhub(company_name: str, max_retries: int = 2) -> Optional[str]:
    """
    Search for ticker symbol using Finnhub Symbol Search API with retry logic.

    Uses LRU cache to store up to 500 recent lookups in memory.

    Args:
        company_name: Company name to search for
        max_retries: Maximum number of retry attempts (default: 2)

    Returns:
        Ticker symbol if found, None otherwise
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return None

    url = "https://finnhub.io/api/v1/search"
    params = {
        "q": company_name,
        "token": api_key
    }

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=5)

            # Handle API rate limiting
            if response.status_code == 429:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"API rate limit hit for '{company_name}', retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API rate limit exceeded for '{company_name}'")
                    return None

            response.raise_for_status()
            data = response.json()

            # Extract first result (highest relevance)
            if data.get("count", 0) > 0:
                results = data.get("result", [])

                # Prefer Common Stock over ADRs and other types
                for result in results:
                    if result.get("type") == "Common Stock":
                        symbol = result.get("symbol")
                        if symbol:
                            logger.info(f"Found ticker via API: {company_name} -> {symbol}")
                            return symbol

                # Fallback to first result if no Common Stock found
                if results:
                    symbol = results[0].get("symbol")
                    if symbol:
                        logger.info(f"Found ticker via API (non-stock): {company_name} -> {symbol}")
                        return symbol

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


def get_tool_schema() -> dict:
    """Get OpenAI function calling schema for news search."""
    return {
        "type": "function",
        "function": {
            "name": "search_financial_news",
            "description": "Search recent financial news about stocks, companies, or industries. Returns relevant news articles with titles, descriptions, sources, and URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Full search query with keywords (e.g., 'Tesla earnings deliveries', 'NVIDIA AI chips', 'semiconductor industry trends')"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company name for ticker lookup (e.g., 'Tesla', 'Goldman Sachs'). Only provide if searching for a specific company. Leave empty for industry/general queries."
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to search back from today (default: 7, max: 30)",
                        "default": 7
                    }
                },
                "required": ["query"]
            }
        }
    }


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
    words = query.strip().split()
    if len(query) > 50 or len(words) > 3:
        # Take first word as company name
        company_name = words[0] if words else query.strip()
        # If second word is also capitalized, include it (e.g., "Goldman Sachs")
        if len(words) > 1 and words[1][0].isupper():
            company_name = f"{words[0]} {words[1]}"
    else:
        company_name = query.strip()

    # Try dynamic lookup via Finnhub Symbol Search API (primary method)
    symbol = _search_symbol_finnhub(company_name)
    if symbol:
        return symbol

    # Final fallback: return first word as ticker (uppercase)
    return words[0].strip().upper() if words else query.strip().upper()


def _search_newsapi(query: str, days_back: int = 7) -> List[Dict[str, str]]:
    """
    Search for financial news using NewsAPI.

    Args:
        query: Search query (company, ticker, or industry)
        days_back: Number of days to search back

    Returns:
        List of news articles with metadata
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logger.warning("NEWS_API_KEY not set, skipping NewsAPI")
        return []

    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=min(days_back, 30))

    # NewsAPI endpoint
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": api_key,
        "pageSize": 10
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            return []

        # Parse and structure articles
        articles = []
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


def _search_finnhub_news(query: str, days_back: int = 7, company_name: str = None) -> List[Dict[str, str]]:
    """
    Search for financial news using Finnhub.

    Args:
        query: Search query (company name or ticker)
        days_back: Number of days to search back
        company_name: Optional company name for ticker lookup (if not provided, uses query)

    Returns:
        List of news articles with metadata
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        logger.warning("FINNHUB_API_KEY not set, skipping Finnhub")
        return []

    # Extract ticker from company_name if provided, otherwise from query
    ticker = _extract_ticker(company_name if company_name else query)

    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=min(days_back, 30))

    # Finnhub company news endpoint
    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": ticker,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "token": api_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Parse and normalize articles
        articles = []
        for article in data:
            # Convert Unix timestamp to ISO 8601
            timestamp = article.get("datetime", 0)
            published_at = datetime.fromtimestamp(timestamp).isoformat() if timestamp else ""

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


def search_financial_news(query: str, days_back: int = 7, company_name: str = None) -> List[Dict[str, str]]:
    """
    Search for financial news using both NewsAPI and Finnhub.

    Queries both APIs in parallel, combines results, deduplicates by URL,
    and returns sorted by published date.

    Args:
        query: Search query (company, ticker, or industry)
        days_back: Number of days to search back
        company_name: Optional company name for Finnhub ticker lookup

    Returns:
        List of news articles with metadata from both sources.
        Each article contains: title, description, source, url,
        published_at, content, api_source
    """
    all_articles = []

    # Query both APIs in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_search_newsapi, query, days_back): "newsapi",
            executor.submit(_search_finnhub_news, query, days_back, company_name): "finnhub"
        }

        for future in as_completed(futures):
            source = futures[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} articles from {source}")
            except Exception as e:
                logger.error(f"Error fetching from {source}: {e}")

    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)

    # Sort by published date (most recent first)
    def parse_date(article):
        try:
            date_str = article.get("published_at", "")
            if date_str:
                # Handle both ISO format and other formats
                # Remove timezone info to avoid comparison issues
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                # Return as naive datetime for consistent comparison
                return dt.replace(tzinfo=None)
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
        return datetime.min

    unique_articles.sort(key=parse_date, reverse=True)

    # Return top 20 results
    return unique_articles[:20]


def execute_tool(tool_name: str, arguments: dict) -> List[Dict[str, str]]:
    """
    Execute the news search tool.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments dictionary

    Returns:
        List of news articles

    Raises:
        ValueError: If tool_name is unknown
    """
    if tool_name == "search_financial_news":
        query = arguments.get("query", "")
        days_back = arguments.get("days_back", 7)
        company_name = arguments.get("company_name")
        return search_financial_news(query, days_back, company_name)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
