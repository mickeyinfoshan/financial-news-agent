#!/usr/bin/env python3
"""Quick test of the financial news agent."""

from financial_news_agent.agent import run_agent
import json

def main():
    print("Testing Financial News Agent\n")
    print("=" * 60)

    query = "How is Tesla performing recently?"
    print(f"Query: {query}\n")

    result = run_agent(query)

    print("\n" + "=" * 60)
    print("ANSWER:")
    print("=" * 60)
    print(result["answer"])

    print("\n" + "=" * 60)
    print("EVALUATION (out of 10):")
    print("=" * 60)
    eval_result = result["evaluation"]
    print(f"Accuracy:       {eval_result.get('accuracy', 0)}/10")
    print(f"Relevance:      {eval_result.get('relevance', 0)}/10")
    print(f"Coherence:      {eval_result.get('coherence', 0)}/10")
    print(f"Reasonableness: {eval_result.get('reasonableness', 0)}/10")
    print(f"Overall:        {eval_result.get('overall', 0):.1f}/10")
    print(f"\nFeedback: {eval_result.get('feedback', 'N/A')}")

    print("\n" + "=" * 60)
    print("TRACEABILITY:")
    print("=" * 60)
    print(f"Tool Calls: {len(result.get('tool_calls', []))}")
    print(f"Sources: {len(result.get('sources', []))}")
    print(f"Reasoning Steps: {len(result.get('reasoning_steps', []))}")

    if result.get('sources'):
        print("\nSources Used:")
        for i, source in enumerate(result['sources'][:3], 1):
            print(f"  {i}. {source.get('title', 'N/A')}")

    if result.get('tool_calls'):
        print("\nTool Calls Made:")
        for i, call in enumerate(result['tool_calls'], 1):
            print(f"  {i}. {call.get('tool_name', 'N/A')} - {call.get('arguments', {})}")

if __name__ == "__main__":
    main()
