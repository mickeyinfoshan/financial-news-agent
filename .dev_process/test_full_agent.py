"""Test the full agent with Finnhub integration."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_news_agent.agent import run_agent


def test_agent():
    """Test the agent with a sample query."""
    print("=" * 60)
    print("Testing Full Agent with Dual News Sources")
    print("=" * 60)

    query = "What's happening with NVIDIA recently?"
    print(f"\nQuery: {query}\n")

    result = run_agent(query)

    print("\n" + "=" * 60)
    print("AGENT RESPONSE")
    print("=" * 60)
    print(result.get("answer", "No answer"))

    print("\n" + "=" * 60)
    print("SOURCES")
    print("=" * 60)
    sources = result.get("trace", {}).get("sources", [])
    print(f"Total sources: {len(sources)}")

    # Count by API source
    newsapi_count = sum(1 for s in sources if s.get("api_source") == "newsapi")
    finnhub_count = sum(1 for s in sources if s.get("api_source") == "finnhub")

    print(f"  - NewsAPI: {newsapi_count}")
    print(f"  - Finnhub: {finnhub_count}")

    print("\nSample sources:")
    for i, source in enumerate(sources[:5], 1):
        print(f"\n{i}. [{source.get('api_source', 'unknown').upper()}] {source.get('title', 'N/A')[:70]}...")
        print(f"   Source: {source.get('source', 'N/A')}")
        print(f"   Date: {source.get('date', 'N/A')[:19]}")

    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)
    evaluation = result.get("evaluation", {})
    print(f"Score: {evaluation.get('score', 'N/A')}/10")
    print(f"Feedback: {evaluation.get('feedback', 'N/A')[:200]}...")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_agent()
