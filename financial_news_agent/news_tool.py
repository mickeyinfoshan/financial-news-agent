"""News search tool using NewsAPI."""

import os
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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


def search_financial_news(query: str, days_back: int = 7) -> List[Dict]:
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
        raise ValueError("NEWS_API_KEY environment variable not set")

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
        "pageSize": 10  # Limit to top 10 results
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
                "content": article.get("content", "")
            })

        return articles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []


def execute_tool(tool_name: str, arguments: dict) -> List[Dict]:
    """Execute the news search tool."""
    if tool_name == "search_financial_news":
        query = arguments.get("query", "")
        days_back = arguments.get("days_back", 7)
        return search_financial_news(query, days_back)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
