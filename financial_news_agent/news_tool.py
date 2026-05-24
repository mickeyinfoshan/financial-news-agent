"""News search tool with multi-source provider support."""

import logging
from datetime import datetime
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .types import ArticleData
from .traceability import TraceabilityTracker
from .news_sources import NewsSourceProvider, NewsAPIProvider, FinnhubProvider, MarketauxProvider

# Configure logging
logger = logging.getLogger(__name__)


def get_tool_schema() -> dict[str, Any]:
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


def get_active_providers() -> list[NewsSourceProvider]:
    """Get list of active news providers based on available API keys."""
    providers: list[NewsSourceProvider] = []

    newsapi = NewsAPIProvider()
    if newsapi.is_available:
        providers.append(newsapi)

    finnhub = FinnhubProvider()
    if finnhub.is_available:
        providers.append(finnhub)

    marketaux = MarketauxProvider()
    if marketaux.is_available:
        providers.append(marketaux)

    return providers


def search_financial_news(
    query: str,
    days_back: int = 7,
    company_name: str | None = None,
    tracker: 'TraceabilityTracker | None' = None
) -> list[ArticleData]:
    """
    Search for financial news using all available providers.

    Queries all active providers in parallel, combines results, deduplicates by URL,
    and returns sorted by published date.

    Args:
        query: Search query (company, ticker, or industry)
        days_back: Number of days to search back
        company_name: Optional company name for ticker lookup
        tracker: Optional traceability tracker for timing instrumentation

    Returns:
        List of news articles with metadata from all sources.
        Each article contains: title, description, source, url,
        published_at, content, api_source
    """
    # Get active providers
    providers = get_active_providers()

    if not providers:
        logger.warning("No news providers available (check API keys)")
        return []

    all_articles: list[ArticleData] = []

    # Query all providers in parallel
    with ThreadPoolExecutor(max_workers=len(providers)) as executor:
        futures: dict[Any, str] = {
            executor.submit(
                provider.search,
                query,
                days_back,
                company_name,
                tracker
            ): provider.name
            for provider in providers
        }

        for future in as_completed(futures):
            provider_name: str = futures[future]
            try:
                articles: list[ArticleData] = future.result()
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} articles from {provider_name}")
            except Exception as e:
                logger.error(f"Error fetching from {provider_name}: {e}")

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique_articles: list[ArticleData] = []
    for article in all_articles:
        url: str = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)

    # Sort by published date (most recent first)
    def parse_date(article: ArticleData) -> datetime:
        try:
            date_str: str = article.get("published_at", "")
            if date_str:
                # Handle both ISO format and other formats
                # Remove timezone info to avoid comparison issues
                dt: datetime = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                # Return as naive datetime for consistent comparison
                return dt.replace(tzinfo=None)
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
        return datetime.min

    unique_articles.sort(key=parse_date, reverse=True)

    # Return top 20 results
    return unique_articles[:20]


def execute_tool(tool_name: str, arguments: dict[str, Any], tracker: 'TraceabilityTracker | None' = None) -> list[ArticleData]:
    """
    Execute the news search tool.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments dictionary
        tracker: Optional traceability tracker for timing instrumentation

    Returns:
        List of news articles

    Raises:
        ValueError: If tool_name is unknown
    """
    if tool_name == "search_financial_news":
        query: str = arguments.get("query", "")
        days_back: int = arguments.get("days_back", 7)
        company_name: str | None = arguments.get("company_name")
        return search_financial_news(query, days_back, company_name, tracker)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
