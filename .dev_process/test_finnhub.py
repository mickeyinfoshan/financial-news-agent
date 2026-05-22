"""Test script for Finnhub integration."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from financial_news_agent.news_tool import (
    _extract_ticker,
    _search_finnhub_news,
    _search_newsapi,
    search_financial_news
)

load_dotenv()


def test_ticker_extraction():
    """Test ticker extraction logic."""
    print("\n=== Testing Ticker Extraction ===")

    test_cases = [
        ("NVDA", "NVDA"),
        ("nvidia", "NVDA"),
        ("Tesla (TSLA)", "TSLA"),
        ("Apple Inc", "AAPL"),
        ("microsoft", "MSFT"),
        ("palantir", "PLTR"),  # NEW: Should use API
        ("snowflake", "SNOW"),  # NEW: Should use API
        ("UNKNOWN", "UNKNOWN"),
    ]

    for query, expected in test_cases:
        result = _extract_ticker(query)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{query}' -> '{result}' (expected: '{expected}')")


def test_finnhub_api():
    """Test Finnhub API connection."""
    print("\n=== Testing Finnhub API ===")

    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("✗ FINNHUB_API_KEY not set")
        return

    print(f"✓ API key found: {api_key[:10]}...")

    # Test with NVIDIA
    print("\nFetching news for NVIDIA...")
    articles = _search_finnhub_news("NVDA", days_back=7)

    if articles:
        print(f"✓ Fetched {len(articles)} articles from Finnhub")
        print("\nSample article:")
        article = articles[0]
        print(f"  Title: {article.get('title', 'N/A')[:80]}...")
        print(f"  Source: {article.get('source', 'N/A')}")
        print(f"  Published: {article.get('published_at', 'N/A')}")
        print(f"  URL: {article.get('url', 'N/A')[:60]}...")
        print(f"  API Source: {article.get('api_source', 'N/A')}")
    else:
        print("✗ No articles returned from Finnhub")


def test_newsapi():
    """Test NewsAPI connection."""
    print("\n=== Testing NewsAPI ===")

    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        print("✗ NEWS_API_KEY not set")
        return

    print(f"✓ API key found: {api_key[:10]}...")

    # Test with NVIDIA
    print("\nFetching news for NVIDIA...")
    articles = _search_newsapi("NVIDIA", days_back=7)

    if articles:
        print(f"✓ Fetched {len(articles)} articles from NewsAPI")
        print("\nSample article:")
        article = articles[0]
        print(f"  Title: {article.get('title', 'N/A')[:80]}...")
        print(f"  Source: {article.get('source', 'N/A')}")
        print(f"  Published: {article.get('published_at', 'N/A')}")
        print(f"  URL: {article.get('url', 'N/A')[:60]}...")
        print(f"  API Source: {article.get('api_source', 'N/A')}")
    else:
        print("✗ No articles returned from NewsAPI")


def test_combined_search():
    """Test combined search from both sources."""
    print("\n=== Testing Combined Search ===")

    print("\nSearching for 'Tesla' across both sources...")
    articles = search_financial_news("Tesla", days_back=7)

    if articles:
        print(f"✓ Fetched {len(articles)} total articles")

        # Count by source
        newsapi_count = sum(1 for a in articles if a.get("api_source") == "newsapi")
        finnhub_count = sum(1 for a in articles if a.get("api_source") == "finnhub")

        print(f"  - NewsAPI: {newsapi_count} articles")
        print(f"  - Finnhub: {finnhub_count} articles")

        print("\nTop 3 articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. [{article.get('api_source', 'unknown').upper()}] {article.get('title', 'N/A')[:70]}...")
            print(f"   Source: {article.get('source', 'N/A')}")
            print(f"   Published: {article.get('published_at', 'N/A')[:19]}")
    else:
        print("✗ No articles returned from combined search")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Finnhub Integration Test Suite")
    print("=" * 60)

    test_ticker_extraction()
    test_finnhub_api()
    test_newsapi()
    test_combined_search()

    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
