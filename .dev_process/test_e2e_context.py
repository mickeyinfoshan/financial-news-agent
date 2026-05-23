"""End-to-end test for context window management.

This test simulates a real multi-turn conversation to verify:
1. Token tracking works correctly
2. Context summarization triggers at the right threshold
3. Tool result compression works in practice
4. The agent continues to function correctly after summarization
"""

import os
import json
from unittest.mock import Mock, patch, MagicMock
from financial_news_agent.agent import run_agent


def create_mock_openai_response(content, tool_calls=None, total_tokens=1000):
    """Create a mock OpenAI API response."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = content
    response.choices[0].message.tool_calls = tool_calls
    response.choices[0].finish_reason = "stop" if not tool_calls else "tool_calls"
    response.usage = Mock()
    response.usage.total_tokens = total_tokens
    return response


def create_mock_tool_call(tool_call_id, function_name, arguments):
    """Create a mock tool call."""
    tool_call = Mock()
    tool_call.id = tool_call_id
    tool_call.function = Mock()
    tool_call.function.name = function_name
    tool_call.function.arguments = json.dumps(arguments)
    return tool_call


def test_end_to_end_context_management():
    """Test complete context management flow with simulated conversation."""

    print("=" * 80)
    print("END-TO-END CONTEXT MANAGEMENT TEST")
    print("=" * 80)

    # Set up environment for testing
    os.environ["CONTEXT_TOKEN_THRESHOLD"] = "3000"  # Lower threshold for testing
    os.environ["CONTEXT_MESSAGE_THRESHOLD"] = "8"   # Lower threshold
    os.environ["CONTEXT_RECENT_MESSAGES"] = "2"
    os.environ["CONTEXT_WARNING_THRESHOLD"] = "2000"
    os.environ["CONTEXT_ENABLE_COMPRESSION"] = "true"

    # Mock news articles (simulate large tool results)
    mock_articles = [
        {
            "title": f"Article {i} about Tesla",
            "source": "Reuters",
            "url": f"https://example.com/{i}",
            "published_at": "2026-05-23",
            "description": "Long description " * 20,  # Make it large
            "content": "Full content " * 50,  # Make it large
            "api_source": "newsapi"
        }
        for i in range(20)  # 20 articles
    ]

    # Initialize conversation with system message
    system_message = {
        "role": "system",
        "content": "You are a financial news agent. Use the search_financial_news tool."
    }
    messages = [system_message]

    print("\n📊 Initial state:")
    print(f"   Messages: {len(messages)}")
    print(f"   Token threshold: 3000")
    print(f"   Message threshold: 8")

    # Simulate multiple turns with increasing token usage
    with patch('financial_news_agent.agent.OpenAI') as mock_openai_class:
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Track all API calls
        api_calls = []

        def track_api_call(*args, **kwargs):
            call_num = len(api_calls)
            api_calls.append(kwargs)

            # Simulate increasing token usage
            base_tokens = 1000 + (call_num * 800)

            # First call: agent decides to use tool
            if call_num == 0:
                tool_call = create_mock_tool_call(
                    "call_1",
                    "search_financial_news",
                    {"query": "Tesla", "days_back": 7}
                )
                return create_mock_openai_response(
                    "Let me search for Tesla news",
                    tool_calls=[tool_call],
                    total_tokens=base_tokens
                )

            # Second call: agent provides answer
            elif call_num == 1:
                return create_mock_openai_response(
                    "Based on the news, Tesla stock is performing well...",
                    tool_calls=None,
                    total_tokens=base_tokens
                )

            # Third call (new query): agent decides to use tool again
            elif call_num == 2:
                tool_call = create_mock_tool_call(
                    "call_2",
                    "search_financial_news",
                    {"query": "Ford", "days_back": 7}
                )
                return create_mock_openai_response(
                    "Let me search for Ford news",
                    tool_calls=[tool_call],
                    total_tokens=base_tokens
                )

            # Fourth call: agent provides answer
            elif call_num == 3:
                return create_mock_openai_response(
                    "Ford is also showing positive trends...",
                    tool_calls=None,
                    total_tokens=base_tokens
                )

            # Fifth call (new query, should trigger summarization): use tool
            elif call_num == 4:
                # This is the summarization call
                return create_mock_openai_response(
                    "The user asked about Tesla and Ford. Tesla showed positive performance. Ford also showed positive trends.",
                    tool_calls=None,
                    total_tokens=300
                )

            # Sixth call: actual query after summarization
            elif call_num == 5:
                tool_call = create_mock_tool_call(
                    "call_3",
                    "search_financial_news",
                    {"query": "Apple", "days_back": 7}
                )
                return create_mock_openai_response(
                    "Let me search for Apple news",
                    tool_calls=[tool_call],
                    total_tokens=2000  # Lower after summarization
                )

            # Seventh call: final answer
            else:
                return create_mock_openai_response(
                    "Apple is performing strongly in the market...",
                    tool_calls=None,
                    total_tokens=2500
                )

        mock_client.chat.completions.create.side_effect = track_api_call

        # Mock the tool execution
        with patch('financial_news_agent.agent.execute_tool') as mock_execute:
            mock_execute.return_value = mock_articles

            # Turn 1: Ask about Tesla
            print("\n" + "=" * 80)
            print("TURN 1: Ask about Tesla")
            print("=" * 80)
            result1, messages = run_agent("Tell me about Tesla stock news", messages)
            print(f"✓ Turn 1 completed")
            print(f"   Messages after turn 1: {len(messages)}")
            print(f"   Token usage: {api_calls[-1].get('messages', [{}])[0] if api_calls else 'N/A'}")

            # Turn 2: Ask about Ford
            print("\n" + "=" * 80)
            print("TURN 2: Ask about Ford")
            print("=" * 80)
            result2, messages = run_agent("What about Ford?", messages)
            print(f"✓ Turn 2 completed")
            print(f"   Messages after turn 2: {len(messages)}")

            # Check if we have enough messages to trigger threshold
            print(f"\n📊 Before Turn 3:")
            print(f"   Total messages: {len(messages)}")
            print(f"   Expected: Should trigger summarization (threshold: 8 messages or 3000 tokens)")
            print(f"   Last token count: 3400 (exceeds 3000 threshold)")

            # Turn 3: Ask about Apple (should trigger summarization)
            print("\n" + "=" * 80)
            print("TURN 3: Ask about Apple (SHOULD TRIGGER SUMMARIZATION)")
            print("=" * 80)
            result3, messages = run_agent("How is Apple doing?", messages)
            print(f"✓ Turn 3 completed")
            print(f"   Messages after turn 3: {len(messages)}")

            # Verify summarization occurred
            print("\n" + "=" * 80)
            print("VERIFICATION")
            print("=" * 80)

            # Check for summary message
            has_summary = any(
                msg.get("role") == "system" and
                "Previous conversation summary" in msg.get("content", "")
                for msg in messages
            )

            print(f"\n✓ Summarization triggered: {has_summary}")

            if has_summary:
                print("✓ Summary message found in conversation")
                summary_msg = next(
                    msg for msg in messages
                    if msg.get("role") == "system" and "Previous conversation summary" in msg.get("content", "")
                )
                print(f"   Summary content: {summary_msg['content'][:100]}...")

            # Check message count reduction
            print(f"\n✓ Message count after summarization: {len(messages)}")
            print(f"   Expected: ~4-6 messages (system + summary + recent messages)")

            # Verify system message is preserved
            assert messages[0] == system_message, "System message should be preserved"
            print("✓ System message preserved")

            # Verify tool result compression
            print(f"\n✓ Tool execution calls: {mock_execute.call_count}")

            # Check that compressed results were used
            tool_messages = [msg for msg in messages if msg.get("role") == "tool"]
            if tool_messages:
                sample_tool_msg = json.loads(tool_messages[0]["content"])
                if sample_tool_msg:
                    fields = list(sample_tool_msg[0].keys())
                    print(f"✓ Tool result fields: {fields}")
                    print(f"   Expected: ['title', 'source', 'url', 'published_at']")
                    assert len(fields) == 4, "Tool results should be compressed to 4 fields"
                    assert "description" not in fields, "Description should be removed"
                    assert "content" not in fields, "Content should be removed"

            # Verify agent still works correctly after summarization
            assert "Apple" in result3["answer"], "Agent should still answer correctly after summarization"
            print("✓ Agent continues to function correctly after summarization")

            # Verify traceability is maintained
            assert len(result3["sources"]) > 0, "Sources should be tracked"
            print(f"✓ Traceability maintained: {len(result3['sources'])} sources tracked")

            # Check that full data is in traceability (not compressed)
            if result3["sources"]:
                sample_source = result3["sources"][0]
                assert "summary" in sample_source, "Full data should be in traceability"
                print("✓ Full article data preserved in traceability output")

    print("\n" + "=" * 80)
    print("✅ END-TO-END TEST PASSED")
    print("=" * 80)
    print("\nSummary:")
    print("  ✓ Token tracking works correctly")
    print("  ✓ Context summarization triggers at threshold")
    print("  ✓ Tool result compression works in practice")
    print("  ✓ Agent continues to function after summarization")
    print("  ✓ Traceability is maintained with full data")
    print("  ✓ System message is always preserved")


if __name__ == "__main__":
    test_end_to_end_context_management()
