"""News search tool using NewsAPI and Finnhub."""

import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Company name to ticker mapping for Finnhub
COMPANY_TO_TICKER = {
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
    "amd": "AMD",
    "intel": "INTC",
    "qualcomm": "QCOM",
    "broadcom": "AVGO",
    "oracle": "ORCL",
    "salesforce": "CRM",
    "adobe": "ADBE",
    "cisco": "CSCO",
    "ibm": "IBM",
    "walmart": "WMT",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "bank of america": "BAC",
    "wells fargo": "WFC",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    "visa": "V",
    "mastercard": "MA",
    "paypal": "PYPL",
    "berkshire hathaway": "BRK.B",
    "johnson & johnson": "JNJ",
    "unitedhealth": "UNH",
    "pfizer": "PFE",
    "merck": "MRK",
    "abbvie": "ABBV",
    "eli lilly": "LLY",
    "exxon": "XOM",
    "exxonmobil": "XOM",
    "chevron": "CVX",
    "conocophillips": "COP",
    "boeing": "BA",
    "lockheed martin": "LMT",
    "ge": "GE",
    "general electric": "GE",
    "caterpillar": "CAT",
    "3m": "MMM",
    "honeywell": "HON",
    "coca cola": "KO",
    "coca-cola": "KO",
    "pepsico": "PEP",
    "procter & gamble": "PG",
    "nike": "NKE",
    "starbucks": "SBUX",
    "mcdonald's": "MCD",
    "mcdonalds": "MCD",
    "disney": "DIS",
    "comcast": "CMCSA",
    "verizon": "VZ",
    "at&t": "T",
    "t-mobile": "TMUS",
}

# In-memory cache for symbol lookups
_symbol_cache = {}


def _search_symbol_finnhub(company_name: str) -> Optional[str]:
    """
    Search for ticker symbol using Finnhub Symbol Search API.

    Args:
        company_name: Company name to search for

    Returns:
        Ticker symbol if found, None otherwise
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return None

    # Check cache first
    cache_key = company_name.lower().strip()
    if cache_key in _symbol_cache:
        return _symbol_cache[cache_key]

    url = "https://finnhub.io/api/v1/search"
    params = {
        "q": company_name,
        "token": api_key
    }

    try:
        response = requests.get(url, params=params, timeout=5)
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
                        _symbol_cache[cache_key] = symbol
                        print(f"Found ticker via API: {company_name} -> {symbol}")
                        return symbol

            # Fallback to first result if no Common Stock found
            if results:
                symbol = results[0].get("symbol")
                if symbol:
                    _symbol_cache[cache_key] = symbol
                    print(f"Found ticker via API (non-stock): {company_name} -> {symbol}")
                    return symbol

    except requests.exceptions.RequestException as e:
        print(f"Error searching Finnhub for '{company_name}': {e}")

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
                        "description": "Search query - company name, stock ticker, or industry (e.g., 'NVIDIA', 'Tesla', 'semiconductor industry')"
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

    Uses a hybrid approach:
    1. Check for explicit ticker in parentheses
    2. Check if query is already a ticker
    3. Try hardcoded dictionary (fast path)
    4. Try Finnhub Symbol Search API (dynamic lookup)
    5. Try partial matches in dictionary
    6. Fallback to query as-is

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

    # Try hardcoded dictionary (fast path - no API call)
    query_lower = query.lower().strip()
    if query_lower in COMPANY_TO_TICKER:
        return COMPANY_TO_TICKER[query_lower]

    # Try dynamic lookup via Finnhub Symbol Search API
    symbol = _search_symbol_finnhub(query)
    if symbol:
        return symbol

    # Check for partial matches in hardcoded dictionary (fallback)
    for company, ticker in COMPANY_TO_TICKER.items():
        if company in query_lower or query_lower in company:
            return ticker

    # Final fallback: return query as-is (uppercase)
    return query.strip().upper()


def _search_newsapi(query: str, days_back: int = 7) -> List[Dict]:
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
        print("Warning: NEWS_API_KEY not set, skipping NewsAPI")
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
        print(f"Error fetching from NewsAPI: {e}")
        return []


def _search_finnhub_news(query: str, days_back: int = 7) -> List[Dict]:
    """
    Search for financial news using Finnhub.

    Args:
        query: Search query (company name or ticker)
        days_back: Number of days to search back

    Returns:
        List of news articles with metadata
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("Warning: FINNHUB_API_KEY not set, skipping Finnhub")
        return []

    # Extract ticker from query
    ticker = _extract_ticker(query)

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
        print(f"Error fetching from Finnhub: {e}")
        return []


def search_financial_news(query: str, days_back: int = 7) -> List[Dict]:
    """
    Search for financial news using both NewsAPI and Finnhub.

    Queries both APIs in parallel, combines results, deduplicates by URL,
    and returns sorted by published date.

    Args:
        query: Search query (company, ticker, or industry)
        days_back: Number of days to search back

    Returns:
        List of news articles with metadata from both sources
    """
    all_articles = []

    # Query both APIs in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_search_newsapi, query, days_back): "newsapi",
            executor.submit(_search_finnhub_news, query, days_back): "finnhub"
        }

        for future in as_completed(futures):
            source = futures[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
                print(f"Fetched {len(articles)} articles from {source}")
            except Exception as e:
                print(f"Error fetching from {source}: {e}")

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
        except:
            pass
        return datetime.min

    unique_articles.sort(key=parse_date, reverse=True)

    # Return top 20 results
    return unique_articles[:20]


def execute_tool(tool_name: str, arguments: dict) -> List[Dict]:
    """Execute the news search tool."""
    if tool_name == "search_financial_news":
        query = arguments.get("query", "")
        days_back = arguments.get("days_back", 7)
        return search_financial_news(query, days_back)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
