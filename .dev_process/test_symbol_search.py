"""Test dynamic symbol search functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from financial_news_agent.news_tool import _extract_ticker, _search_symbol_finnhub

load_dotenv()


def test_symbol_search():
    """Test Finnhub symbol search API."""
    print("\n=== Testing Finnhub Symbol Search API ===\n")

    test_cases = [
        # Known companies (should use hardcoded dict)
        "nvidia",
        "apple",
        "tesla",

        # Unknown companies (should use API)
        "palantir",
        "snowflake",
        "databricks",
        "stripe",

        # Already tickers
        "NVDA",
        "AAPL",

        # Parenthetical format
        "Palantir (PLTR)",
    ]

    for query in test_cases:
        ticker = _extract_ticker(query)
        print(f"'{query}' -> '{ticker}'")

    print("\n=== Direct API Search Tests ===\n")

    api_test_cases = [
        "palantir",
        "snowflake",
        "databricks",
        "unknown company xyz",
    ]

    for query in api_test_cases:
        result = _search_symbol_finnhub(query)
        status = "✓" if result else "✗"
        print(f"{status} '{query}' -> {result or 'Not found'}")


if __name__ == "__main__":
    test_symbol_search()
