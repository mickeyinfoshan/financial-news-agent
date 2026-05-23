"""Manual test script for context window management.

Run this script to manually test the context management features with real API calls.
You can observe:
1. Token usage tracking
2. Tool result compression
3. Context summarization when thresholds are exceeded
"""

import os
from dotenv import load_dotenv
from financial_news_agent.agent import run_agent

load_dotenv()

# Configure for easier testing (lower thresholds)
os.environ["CONTEXT_TOKEN_THRESHOLD"] = "8000"  # Lower than default 12000
os.environ["CONTEXT_MESSAGE_THRESHOLD"] = "12"
os.environ["CONTEXT_RECENT_MESSAGES"] = "4"
os.environ["CONTEXT_WARNING_THRESHOLD"] = "5000"
os.environ["CONTEXT_ENABLE_COMPRESSION"] = "true"

print("=" * 80)
print("CONTEXT WINDOW MANAGEMENT - MANUAL TEST")
print("=" * 80)
print("\nConfiguration:")
print(f"  Token threshold: {os.environ['CONTEXT_TOKEN_THRESHOLD']}")
print(f"  Message threshold: {os.environ['CONTEXT_MESSAGE_THRESHOLD']}")
print(f"  Recent messages preserved: {os.environ['CONTEXT_RECENT_MESSAGES']}")
print(f"  Warning threshold (aggressive compression): {os.environ['CONTEXT_WARNING_THRESHOLD']}")
print("\n" + "=" * 80)

# Initialize conversation
system_message = {
    "role": "system",
    "content": """You are a financial news analysis agent. Your job is to:
1. Search for recent financial news using the search_financial_news tool
2. Analyze the news and provide insights
3. Answer user questions about stocks and companies

When the user asks about a company:
- Use the search_financial_news tool with the company name
- If the user provides a specific company name (like "Tesla" or "Apple"), pass it directly as the query parameter
- Analyze the results and provide a comprehensive answer

Always provide clear, factual analysis based on the news articles you find."""
}

messages = [system_message]

# Test queries
test_queries = [
    "Tell me about recent Tesla news",
    "What's happening with Apple stock?",
    "How is Microsoft performing?",
    "Compare Tesla and Ford",
    "What about Amazon?",
]

print("\nRunning test queries...")
print("Watch for:")
print("  - 'Token usage: X' messages showing token tracking")
print("  - 'Context: X tokens, Y messages' showing context monitoring")
print("  - 'Context threshold exceeded' when summarization triggers")
print("  - 'Summarization complete' when history is compressed")
print("\n" + "=" * 80)

for i, query in enumerate(test_queries, 1):
    print(f"\n{'=' * 80}")
    print(f"QUERY {i}: {query}")
    print(f"{'=' * 80}")
    print(f"Messages before query: {len(messages)}")

    try:
        result, messages = run_agent(query, messages)

        print(f"\n✓ Query completed")
        print(f"  Messages after query: {len(messages)}")
        print(f"  Sources found: {len(result['sources'])}")
        print(f"  Tool calls made: {len(result['tool_calls'])}")

        # Show answer preview
        answer_preview = result['answer'][:200] + "..." if len(result['answer']) > 200 else result['answer']
        print(f"\n  Answer preview: {answer_preview}")

        # Check if summarization occurred
        has_summary = any(
            msg.get("role") == "system" and
            "Previous conversation summary" in msg.get("content", "")
            for msg in messages
        )

        if has_summary:
            print("\n  🔄 SUMMARIZATION OCCURRED!")
            summary_msg = next(
                msg for msg in messages
                if msg.get("role") == "system" and "Previous conversation summary" in msg.get("content", "")
            )
            summary_preview = summary_msg['content'][:150] + "..."
            print(f"     Summary: {summary_preview}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        break

    print(f"\n{'=' * 80}")

print("\n" + "=" * 80)
print("TEST COMPLETED")
print("=" * 80)
print(f"\nFinal conversation state:")
print(f"  Total messages: {len(messages)}")

# Show message breakdown
message_types = {}
for msg in messages:
    role = msg.get("role", "unknown")
    message_types[role] = message_types.get(role, 0) + 1

print(f"  Message breakdown:")
for role, count in message_types.items():
    print(f"    - {role}: {count}")

# Check for summary
has_summary = any(
    msg.get("role") == "system" and
    "Previous conversation summary" in msg.get("content", "")
    for msg in messages
)

print(f"\n  Summarization used: {'Yes ✓' if has_summary else 'No'}")

print("\n" + "=" * 80)
print("To test with your own queries, run:")
print("  uv run python -m financial_news_agent")
print("=" * 80)
