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

    # Initialize conversation with system message
    system_message = {
        "role": "system",
        "content": """You are a financial news analyst AI agent. Your job is to:
1. Search for recent financial news about the company or industry the user asks about
2. Analyze the news to create a coherent storyline of what has been happening
3. Provide future impact analysis based on the trends you observe
4. **Cite your sources using numbered references [1], [2], [3] etc.**

When you receive news articles from the tool, they will be numbered (id: 1, 2, 3, etc.).
You MUST cite these sources in your answer using the format [1], [2], [3] whenever you reference information from them.

Always use the search_financial_news tool to gather information before answering.
Be thorough - you can call the tool multiple times with different queries if needed.
Base your analysis strictly on the sources you find and cite them appropriately."""
    }

    messages = [system_message]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {query}")
        print('='*70)

        try:
            result, messages = run_agent(query, messages)

            # Display summary
            print(f"\n✓ Answer generated ({len(result['answer'])} chars)")
            print(f"✓ Sources found: {len(result['sources'])}")
            print(f"✓ Tool calls made: {len(result['tool_calls'])}")
            print(f"✓ Evaluation score: {result['evaluation']['overall']}/10.0")

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
