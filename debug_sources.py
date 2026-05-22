#!/usr/bin/env python3
"""Debug tool calls and sources."""

from financial_news_agent.agent import run_agent
import json

def main():
    query = "How is Tesla performing recently?"
    print(f"Query: {query}\n")

    result = run_agent(query)

    print("=" * 60)
    print("TOOL CALLS DETAIL:")
    print("=" * 60)
    for i, call in enumerate(result.get('tool_calls', []), 1):
        print(f"\n{i}. Tool: {call.get('tool_name')}")
        print(f"   Arguments: {json.dumps(call.get('arguments', {}), indent=2)}")
        print(f"   Result count: {len(call.get('result', []))} articles")

    print("\n" + "=" * 60)
    print("SOURCES DETAIL:")
    print("=" * 60)
    for i, source in enumerate(result.get('sources', []), 1):
        print(f"\n{i}. {source.get('title')}")
        print(f"   Date: {source.get('date')}")
        print(f"   Source: {source.get('source')}")
        print(f"   Summary: {source.get('summary', '')[:200]}...")

if __name__ == "__main__":
    main()
