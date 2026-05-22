"""Test script for the financial news agent."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from financial_news_agent.agent import run_agent


def test_agent():
    """Test the agent with sample queries."""

    # Test queries
    queries = [
        "What's happening with NVIDIA stock?",
        "Tell me about the semiconductor industry",
        "How is Tesla performing recently?"
    ]

    print("=" * 70)
    print("FINANCIAL NEWS AGENT - TEST SCRIPT")
    print("=" * 70)
    print()

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {query}")
        print('='*70)

        try:
            result = run_agent(query)

            # Display summary
            print(f"\n✓ Answer generated ({len(result['answer'])} chars)")
            print(f"✓ Sources found: {len(result['sources'])}")
            print(f"✓ Tool calls made: {len(result['tool_calls'])}")
            print(f"✓ Evaluation score: {result['evaluation']['overall']}/5.0")

            # Show first 200 chars of answer
            print(f"\nAnswer preview:")
            print(result['answer'][:200] + "..." if len(result['answer']) > 200 else result['answer'])

            # Show sources
            if result['sources']:
                print(f"\nTop sources:")
                for j, source in enumerate(result['sources'][:3], 1):
                    print(f"  {j}. {source['title'][:60]}...")

            print(f"\nEvaluation: {result['evaluation']['feedback']}")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print('='*70)


if __name__ == "__main__":
    test_agent()
