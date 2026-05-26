"""Async streaming agent execution implementations."""

import os
import json
import logging
from typing import Any, AsyncGenerator
from openai import AsyncOpenAI, OpenAI
from ..types import AgentResult, MessageDict, EvaluationResult, ContextConfig, ArticleData
from ..traceability import TraceabilityTracker
from ..news_tool import get_tool_schema, execute_tool
from ..context_manager import load_config
from ..retry_manager import RetryConfig, build_fix_prompt, build_redo_prompt
from .prompts import SYSTEM_PROMPT
from .sync import create_conversation
from . import shared

logger = logging.getLogger(__name__)


def _merge_tool_call_delta(
    accumulated: list[dict[str, Any]],
    deltas: list[Any]
) -> None:
    """
    Merge incremental tool call chunks into accumulated state.

    Args:
        accumulated: List of accumulated tool call dicts
        deltas: List of tool call delta objects from streaming response
    """
    for delta in deltas:
        index: int = delta.index

        # Ensure list is long enough
        while len(accumulated) <= index:
            accumulated.append({
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""}
            })

        # Merge fields
        if delta.id:
            accumulated[index]["id"] = delta.id
        if delta.function:
            if delta.function.name:
                accumulated[index]["function"]["name"] += delta.function.name
            if delta.function.arguments:
                accumulated[index]["function"]["arguments"] += delta.function.arguments


async def run_agent_stream(
    user_query: str,
    messages: list[MessageDict],
    tracker: TraceabilityTracker | None = None,
    append_query: bool = True
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Async streaming agent execution with real-time events.

    Args:
        user_query: User's question about a company or industry
        messages: Existing conversation history (includes system message)
        tracker: Optional tracker to reuse (for retry accumulation). If None, creates new tracker.
        append_query: Whether to append user_query to messages (False for retry scenarios)

    Yields:
        Event dicts with types: agent_start, iteration_start, token, tool_call_start,
        tool_call_complete, evaluation, timing, done
    """
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    if tracker is None:
        tracker = TraceabilityTracker()
    config: ContextConfig = load_config()

    yield {"event": "agent_start", "data": {"query": user_query}}

    # Append new user query to existing conversation (skip for retries)
    if append_query:
        messages.append({"role": "user", "content": user_query})
    tools = [get_tool_schema()]
    final_answer: str | None = None
    total_tokens = 0  # Track cumulative token usage
    MAX_ITERATIONS = 10

    for iteration in range(MAX_ITERATIONS):
        yield {"event": "iteration_start", "data": {"iteration": iteration + 1}}

        try:
            # Force final answer on last iteration - prevents infinite tool calling loops
            is_final_iteration, tool_choice_param = shared.should_force_final_answer(iteration, MAX_ITERATIONS)

            # Stream response
            stream = await client.chat.completions.create(  # type: ignore[call-overload]
                model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
                messages=messages,
                tools=tools,
                tool_choice=tool_choice_param,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )

            # Accumulate response
            accumulated: dict[str, Any] = {
                "content": "",
                "tool_calls": [],
                "role": "assistant"
            }

            # Stream tokens
            async for chunk in stream:
                delta = chunk.choices[0].delta

                # Stream content tokens
                if delta.content:
                    accumulated["content"] += delta.content
                    yield {
                        "event": "token",
                        "data": {
                            "content": delta.content,
                            "iteration": iteration + 1
                        }
                    }

                # Accumulate tool calls (incremental deltas)
                if delta.tool_calls:
                    _merge_tool_call_delta(accumulated["tool_calls"], delta.tool_calls)

            # Track reasoning if there's text content AND tool calls
            # Final answers (no tool_calls) are tracked separately in result["answer"]
            if accumulated["content"] and accumulated["tool_calls"]:
                tracker.add_reasoning(accumulated["content"])

            # Add assistant message to conversation
            messages.append({
                "role": "assistant",
                "content": accumulated["content"],
                "tool_calls": accumulated["tool_calls"] if accumulated["tool_calls"] else None
            })

            # Execute tool calls
            if accumulated["tool_calls"]:
                for tool_call in accumulated["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])

                    yield {
                        "event": "tool_call_start",
                        "data": {
                            "tool_name": tool_name,
                            "arguments": tool_args,
                            "iteration": iteration + 1
                        }
                    }

                    # Execute tool
                    tool_result: list[ArticleData] = execute_tool(tool_name, tool_args, tracker)
                    tracker.add_tool_call(tool_name, tool_args, tool_result)

                    # Calculate start_id before adding sources - ensures continuous numbering across tool calls
                    # Example: first call adds 10 sources (1-10), second call starts at 11
                    start_id = len(tracker.sources) + 1

                    # Track sources
                    shared.process_tool_results(tool_result, tracker)

                    yield {
                        "event": "tool_call_complete",
                        "data": {
                            "tool_name": tool_name,
                            "result_summary": f"Retrieved {len(tool_result)} articles",
                            "article_count": len(tool_result),
                            "iteration": iteration + 1
                        }
                    }

                    # Send compressed version to LLM to save tokens
                    tool_message = shared.compress_and_build_tool_message(
                        tool_result, tool_call["id"], total_tokens, config, start_id
                    )
                    messages.append(tool_message)
            else:
                # No tool calls = final answer
                final_answer = accumulated["content"] or "No answer generated."
                break

        except Exception as e:
            logger.error(f"Error in agent loop: {e}")
            yield {
                "event": "error",
                "data": {
                    "message": str(e),
                    "iteration": iteration + 1
                }
            }
            final_answer = f"Error occurred: {str(e)}"
            break

    # If no answer after max iterations
    if final_answer is None:
        final_answer = "Agent reached maximum iterations without completing the analysis."

    # Create sync client for evaluation operations
    sync_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )

    # Step 1: Rewrite query
    rewritten_query = shared.do_query_rewriting(user_query, messages, sync_client, tracker)

    # Step 2: Validate citations
    citation_validation = shared.do_citation_validation(final_answer, tracker.sources, sync_client, tracker)
    if citation_validation:
        yield {"event": "citation_validation", "data": citation_validation}

    # Step 3: Evaluate response
    evaluation = shared.do_evaluation(final_answer, tracker, rewritten_query, citation_validation)
    yield {"event": "evaluation", "data": evaluation}

    # Step 4: Emit timing summary
    timing_summary = tracker.get_timing_summary()
    if timing_summary["total_duration_ms"] > 0:
        yield {"event": "timing", "data": timing_summary}

    # Step 5: Build final result
    result = shared.build_agent_result(final_answer, tracker, evaluation, citation_validation)

    # Final event with complete result
    yield {
        "event": "done",
        "data": {
            "result": result,
            "messages": messages
        }
    }


async def run_agent_with_retry_stream(
    user_query: str,
    messages: list[MessageDict]
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Async streaming agent execution with retry/fix mechanism.

    Args:
        user_query: User's question about a company or industry
        messages: Existing conversation history (includes system message)

    Yields:
        Event dicts including retry events when quality is low
    """
    config = RetryConfig()
    tracker = TraceabilityTracker()  # Create tracker once for all attempts
    attempt = 0
    retry_history: list[dict[str, Any]] = []

    while attempt <= config.max_attempts:
        attempt += 1

        # Run agent and collect result (skip appending query for retries)
        result: AgentResult | None = None
        updated_messages: list[MessageDict] | None = None

        async for event in run_agent_stream(user_query, messages, tracker, append_query=(attempt == 1)):
            # Capture final result
            if event["event"] == "done":
                result = event["data"]["result"]
                updated_messages = event["data"]["messages"]

            # Forward all events
            yield event

        # Check if retry needed
        if result is None:
            break

        evaluation: EvaluationResult = result["evaluation"]
        citation_validation = result.get("citation_validation")

        if not shared.should_retry(evaluation, attempt - 1, config, citation_validation) or attempt > config.max_attempts:
            # Add retry history to final result if any retries occurred
            if retry_history:
                result["retry_history"] = retry_history  # type: ignore[typeddict-item]
                # Re-emit done event with retry history
                yield {
                    "event": "done",
                    "data": {
                        "result": result,
                        "messages": updated_messages
                    }
                }
            return

        # Determine retry strategy
        strategy = shared.decide_retry_strategy_wrapper(evaluation, result["sources"], config, citation_validation)

        if strategy == "none":
            if retry_history:
                result["retry_history"] = retry_history  # type: ignore[typeddict-item]
                yield {
                    "event": "done",
                    "data": {
                        "result": result,
                        "messages": updated_messages
                    }
                }
            return

        retry_info = {
            "attempt": attempt,
            "previous_score": evaluation["overall"],
            "strategy": strategy,
            "reason": f"Quality below threshold (overall: {evaluation['overall']:.1f})"
        }
        retry_history.append(retry_info)

        # Emit retry event
        yield {
            "event": "retry",
            "data": retry_info
        }

        # Prepare for retry
        if strategy == "fix":
            # FIX: Mark the low-quality assistant response as internal
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].get("role") == "assistant":
                    messages[i]["internal"] = True
                    break

            # FIX: Continue conversation with improvement prompt
            fix_prompt: str = build_fix_prompt(evaluation, user_query, citation_validation)
            messages.append({"role": "user", "content": fix_prompt, "internal": True})
        elif strategy == "redo":
            # REDO: Mark failed response and tool messages as internal, then request fresh search
            # Mark the failed assistant response as internal
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].get("role") == "assistant":
                    messages[i]["internal"] = True
                    break

            # Mark all tool messages as internal (signals: don't reuse these sources)
            for msg in messages:
                if msg.get("role") == "tool":
                    msg["internal"] = True

            # Append redo prompt requesting fresh search
            redo_prompt: str = build_redo_prompt(evaluation, user_query)
            messages.append({"role": "user", "content": redo_prompt, "internal": True})
