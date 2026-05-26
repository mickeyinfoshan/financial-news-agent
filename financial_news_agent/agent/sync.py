"""Synchronous agent execution implementations."""

import os
import json
import logging
from typing import Any
from openai import OpenAI
from ..types import AgentResult, MessageDict, EvaluationResult, ContextConfig, ArticleData
from ..traceability import TraceabilityTracker
from ..news_tool import get_tool_schema, execute_tool
from ..context_manager import manage_context, load_config
from ..retry_manager import RetryConfig, build_fix_prompt, build_redo_prompt
from .prompts import SYSTEM_PROMPT
from . import shared

logger = logging.getLogger(__name__)


def create_conversation() -> list[MessageDict]:
    """
    Initialize a new conversation with system prompt.

    Returns:
        List containing system message
    """
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def run_agent(
    user_query: str,
    messages: list[MessageDict],
    tracker: TraceabilityTracker | None = None
) -> tuple[AgentResult, list[MessageDict]]:
    """
    Run the financial news agent.

    Args:
        user_query: User's question about a company or industry
        messages: Existing conversation history (includes system message)
        tracker: Optional tracker to reuse (for retry accumulation). If None, creates new tracker.

    Returns:
        Tuple of (result dict, updated messages list)
    """

    client: OpenAI = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    if tracker is None:
        tracker = TraceabilityTracker()
    config: ContextConfig = load_config()

    # Append new user query to existing conversation
    messages.append({"role": "user", "content": user_query})

    # Tool definitions
    tools: list[dict[str, Any]] = [get_tool_schema()]

    # Agent loop (max 10 iterations)
    MAX_ITERATIONS = 10
    final_answer: str | None = None
    total_tokens: int = 0  # Track cumulative token usage

    for iteration in range(MAX_ITERATIONS):
        logger.debug(f"[Iteration {iteration + 1}]")

        with tracker.time_operation(f"Iteration {iteration + 1}", "iteration", {"iteration": iteration + 1}):
            # Manage context window before LLM call
            with tracker.time_operation("Context Management", "context_mgmt"):
                messages = manage_context(messages, total_tokens, client, config, tracker)

            try:
                llm_metadata: dict[str, Any] = {
                    "model": os.getenv("OPENAI_MODEL", "gpt-4.5"),
                    "iteration": iteration + 1,
                    "has_tools": True
                }

                # Force final answer on last iteration - prevents infinite tool calling loops
                is_final_iteration, tool_choice_param = shared.should_force_final_answer(iteration, MAX_ITERATIONS)

                with tracker.time_operation("LLM Reasoning Call", "llm_call", llm_metadata) as timing_node:
                    response = client.chat.completions.create(  # type: ignore[call-overload]
                        model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
                        messages=messages,
                        tools=tools,
                        tool_choice=tool_choice_param,
                        temperature=0.7,
                        max_tokens=2000
                    )

                    # Track token usage from API response
                    if hasattr(response, 'usage') and response.usage:
                        total_tokens = response.usage.total_tokens
                        timing_node.metadata["tokens"] = {
                            "prompt": response.usage.prompt_tokens,
                            "completion": response.usage.completion_tokens,
                            "total": total_tokens
                        }
                        logger.debug(f"Token usage: {total_tokens}")

                assistant_message = response.choices[0].message
                finish_reason: str = response.choices[0].finish_reason

                logger.debug(f"Finish reason: {finish_reason}")
                logger.debug(f"Has tool calls: {bool(assistant_message.tool_calls)}")
                logger.debug(f"Content: {assistant_message.content[:100] if assistant_message.content else 'None'}...")

                # Add assistant message to conversation
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": assistant_message.tool_calls
                })

                # Track reasoning only when LLM explains its tool usage
                # Final answers (no tool_calls) are tracked separately in result["answer"]
                if assistant_message.content and assistant_message.tool_calls:
                    tracker.add_reasoning(assistant_message.content)

                # Check if we have tool calls to execute
                if assistant_message.tool_calls:
                    # Execute tool calls
                    for tool_call in assistant_message.tool_calls:
                        tool_name: str = tool_call.function.name
                        tool_args: dict[str, Any] = json.loads(tool_call.function.arguments)

                        tool_metadata: dict[str, Any] = {
                            "tool": tool_name,
                            "args": tool_args,
                            "iteration": iteration + 1
                        }

                        with tracker.time_operation(f"Tool: {tool_name}", "tool_call", tool_metadata):
                            # Execute the tool
                            tool_result: list[ArticleData] = execute_tool(tool_name, tool_args, tracker)

                        # Track the tool call
                        tracker.add_tool_call(tool_name, tool_args, tool_result)

                        # Calculate start_id before adding sources - ensures continuous numbering across tool calls
                        # Example: first call adds 10 sources (1-10), second call starts at 11
                        start_id: int = len(tracker.sources) + 1

                        # Store full articles in tracker for final result
                        shared.process_tool_results(tool_result, tracker)

                        # Send compressed version to LLM to save tokens
                        tool_message = shared.compress_and_build_tool_message(
                            tool_result, tool_call.id, total_tokens, config, start_id
                        )
                        messages.append(tool_message)
                else:
                    # No tool calls, this is the final answer
                    final_answer = assistant_message.content or "No answer generated."
                    break

            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                final_answer = f"Error occurred: {str(e)}"
                break

    # If no answer after max iterations
    if final_answer is None:
        final_answer = "Agent reached maximum iterations without completing the analysis."

    # Build final result with evaluation
    result = build_final_result(final_answer, tracker, user_query, messages, client)
    return result, messages


def build_final_result(
    final_answer: str,
    tracker: TraceabilityTracker,
    user_query: str,
    messages: list[MessageDict],
    client: OpenAI
) -> AgentResult:
    """
    Build final result with evaluation and citation validation.

    Uses shared operations for consistency with streaming version.

    Args:
        final_answer: The agent's final response
        tracker: TraceabilityTracker with sources and timing
        user_query: Original user query
        messages: Conversation history
        client: OpenAI client for query rewriting

    Returns:
        AgentResult with all metadata
    """
    # Step 1: Rewrite query
    rewritten_query = shared.do_query_rewriting(user_query, messages, client, tracker)

    # Step 2: Validate citations
    citation_validation = shared.do_citation_validation(final_answer, tracker.sources, client, tracker)

    # Step 3: Evaluate response
    evaluation = shared.do_evaluation(final_answer, tracker, rewritten_query, citation_validation)

    # Step 4: Build result
    return shared.build_agent_result(final_answer, tracker, evaluation, citation_validation)


def run_agent_with_retry(
    user_query: str,
    messages: list[MessageDict]
) -> tuple[AgentResult, list[MessageDict]]:
    """
    Run agent with retry/fix mechanism for low-quality responses.

    Args:
        user_query: User's question about a company or industry
        messages: Existing conversation history (includes system message)

    Returns:
        Tuple of (result dict, updated messages list)
    """

    # Create tracker at the top level to capture all timing
    tracker: TraceabilityTracker = TraceabilityTracker()
    config: RetryConfig = RetryConfig()

    # Track retry attempts
    attempt: int = 0
    retry_history: list[dict[str, Any]] = []
    previous_result: AgentResult | None = None
    previous_messages: list[MessageDict] | None = None

    with tracker.time_operation("Agent Request", "request", {"query": user_query}):
        while attempt <= config.max_attempts:
            attempt_metadata: dict[str, Any] = {"attempt": attempt + 1, "max_attempts": config.max_attempts + 1}

            with tracker.time_operation(f"Attempt {attempt + 1}", "attempt", attempt_metadata):
                try:
                    # Run the agent
                    result: AgentResult
                    result, messages = run_agent(user_query, messages, tracker)

                    evaluation: EvaluationResult = result["evaluation"]
                    citation_validation = result.get("citation_validation")

                    # Store attempt if configured
                    if config.show_attempts and attempt > 0:
                        retry_history.append({
                            "attempt": attempt,
                            "evaluation": evaluation,
                            "answer": result["answer"]
                        })

                    # Check if retry needed
                    if not shared.should_retry(evaluation, attempt, config, citation_validation):
                        # Success or max attempts reached
                        if config.show_attempts and retry_history:
                            result["retry_history"] = retry_history  # type: ignore[typeddict-item]

                        # Merge timing from top-level tracker
                        if "trace" in result and "timing" not in result["trace"]:
                            result["trace"]["timing"] = tracker.get_timing_summary()

                        return result, messages

                    # Save current result in case retry fails
                    previous_result = result
                    previous_messages = messages.copy()

                    # Decide strategy
                    strategy: str = shared.decide_retry_strategy_wrapper(evaluation, result["sources"], config, citation_validation)

                    if strategy == "none":
                        if config.show_attempts and retry_history:
                            result["retry_history"] = retry_history  # type: ignore[typeddict-item]

                        # Merge timing from top-level tracker
                        if "trace" in result and "timing" not in result["trace"]:
                            result["trace"]["timing"] = tracker.get_timing_summary()

                        return result, messages

                    logger.info(f"[Retry {attempt + 1}/{config.max_attempts}] Strategy: {strategy.upper()}")
                    logger.info(f"Reason: Overall={evaluation['overall']:.1f}, Accuracy={evaluation.get('accuracy', 0)}/10")

                    # Execute retry strategy
                    if strategy == "fix":
                        # FIX: Continue conversation with improvement prompt
                        fix_prompt: str = build_fix_prompt(evaluation, user_query, citation_validation)
                        messages.append({"role": "user", "content": fix_prompt})

                    elif strategy == "redo":
                        # REDO: Reset to system message + new query
                        system_msg: MessageDict = messages[0]
                        redo_prompt: str = build_redo_prompt(evaluation, user_query)
                        messages = [system_msg, {"role": "user", "content": redo_prompt}]

                    attempt += 1

                except Exception as e:
                    logger.error(f"Error during retry (attempt {attempt}): {e}")
                    if attempt == 0:
                        # First attempt failed, re-raise
                        raise
                    else:
                        # Retry failed, return previous result
                        if config.show_attempts and retry_history and previous_result:
                            previous_result["retry_history"] = retry_history  # type: ignore[typeddict-item]

                        # Merge timing from top-level tracker
                        if previous_result and "trace" in previous_result and "timing" not in previous_result["trace"]:
                            previous_result["trace"]["timing"] = tracker.get_timing_summary()

                        return previous_result, previous_messages  # type: ignore[return-value]

        # Max attempts exhausted
        logger.warning(f"Maximum retry attempts reached ({config.max_attempts})")
        if config.show_attempts and retry_history:
            result["retry_history"] = retry_history  # type: ignore[typeddict-item]

        # Merge timing from top-level tracker
        if "trace" in result and "timing" not in result["trace"]:
            result["trace"]["timing"] = tracker.get_timing_summary()

        return result, messages
