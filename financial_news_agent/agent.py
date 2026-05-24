"""Main agent loop with LLM and tool calling."""

import os
import json
import logging
from typing import Any, AsyncGenerator
from openai import OpenAI, AsyncOpenAI
from .traceability import TraceabilityTracker
from .news_tool import get_tool_schema, execute_tool
from .evaluator import evaluate_response
from .context_manager import manage_context, compress_tool_result, load_config
from .retry_manager import RetryConfig, decide_retry_strategy, build_fix_prompt, build_redo_prompt
from .types import AgentResult, MessageDict, EvaluationResult, ContextConfig, ArticleData

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """You are a financial news analyst AI agent. Your job is to:
1. Search for recent financial news about the company or industry the user asks about
2. Analyze the news to create a coherent storyline of what has been happening
3. Provide future impact analysis based on the trends you observe
4. **Cite your sources using numbered references [1], [2], [3] etc.**

When using the search_financial_news tool:
- Use the 'query' parameter for your full search query with keywords
- Use the 'company_name' parameter to specify the company name (e.g., 'Tesla', 'Goldman Sachs') for accurate ticker lookup
- IMPORTANT: Only provide company_name when searching for a SINGLE specific company
- For multiple companies or industry queries, leave company_name empty and use descriptive query text
- For competitor analysis, make SEPARATE tool calls for each company with their respective company_name

Examples:
- Single company: query="Tesla earnings Q1 2026", company_name="Tesla"
- Multiple companies: query="BYD sales China", company_name="BYD" (separate call)
- Industry: query="EV industry trends", company_name=None

**CRITICAL - Source Citations Rules:**
When you receive news articles from the tool, they will be numbered with unique IDs (id: 1, 2, 3, etc.).
These IDs are CUMULATIVE across all tool calls - if you make multiple searches, the numbering continues.
For example: first search returns articles 1-10, second search returns articles 11-18.

YOU MUST:
- ONLY cite sources that were returned by the search_financial_news tool
- Use the exact IDs provided in the tool response: [1], [2], [3], etc.
- Base ALL claims strictly on the retrieved articles

YOU MUST NEVER:
- Cite sources from your training data or general knowledge
- Invent or hallucinate article titles, sources, or citations
- Reference articles that were not returned by the tool
- Create your own source list or numbering

Example citation style:
"Apple's stock rose 5% following strong earnings [1]. Analysts predict continued growth in the AI sector [2][3]."

Always use the search_financial_news tool to gather information before answering.
Be thorough - you can call the tool multiple times with different queries if needed.
Base your analysis strictly on the sources you find and cite them appropriately."""


def create_conversation() -> list[MessageDict]:
    """Create a new conversation with initialized system message.

    Returns:
        list: Messages list with system message
    """
    return [{"role": "system", "content": _SYSTEM_PROMPT}]


def rewrite_query_with_context(user_query: str, messages: list[MessageDict], client: OpenAI) -> str:
    """
    Rewrite user query to be self-contained using conversation context.

    Handles multi-turn conversations where queries contain pronouns or implicit
    references that need context from previous messages.

    Args:
        user_query: The latest user query (may contain pronouns)
        messages: Full conversation history
        client: OpenAI client for rewriting

    Returns:
        str: Rewritten query that is self-contained and clear
    """
    # Edge case 1: First turn (only system message exists)
    # No context needed, return original query
    if len(messages) <= 1:
        return user_query

    # Edge case 2: Query already seems self-contained
    # Check for pronouns and implicit references
    pronouns: list[str] = ['their', 'its', 'it', 'they', 'them', 'this', 'that', 'these', 'those']
    query_lower: str = user_query.lower()
    has_pronouns: bool = any(f' {pronoun} ' in f' {query_lower} ' or
                      query_lower.startswith(f'{pronoun} ') or
                      query_lower.endswith(f' {pronoun}')
                      for pronoun in pronouns)

    # If no pronouns and query is reasonably long, likely self-contained
    if not has_pronouns and len(user_query.split()) > 3:
        return user_query

    # Build context from recent conversation (last 3-5 exchanges)
    # Exclude system message, focus on user-assistant exchanges
    context_messages: list[str] = []
    for msg in messages[1:]:  # Skip system message
        role: str = msg.get("role", "")
        content: str | None = msg.get("content", "")

        if role == "user" and content:
            context_messages.append(f"User: {content}")
        elif role == "assistant" and content:
            # Truncate long assistant responses
            content_preview: str = content[:300] if len(content) > 300 else content
            context_messages.append(f"Assistant: {content_preview}")

    # Limit to last 6 messages (3 exchanges) to avoid token bloat
    recent_context: list[str] = context_messages[-6:] if len(context_messages) > 6 else context_messages
    context_text: str = "\n".join(recent_context)

    rewrite_prompt: str = f"""Given the conversation context below, rewrite the user's latest query to be self-contained and clear.

CONVERSATION CONTEXT:
{context_text}

LATEST USER QUERY:
{user_query}

Rewrite the query so it can be understood without the conversation context. Replace pronouns with specific entities. Keep it concise (1-2 sentences max).

Examples:
- "What about their competitors?" → "What are Apple's main competitors?"
- "How is it performing?" → "How is Tesla's stock performing?"
- "Tell me about that acquisition" → "Tell me about Microsoft's acquisition of Activision"

REWRITTEN QUERY:"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at rewriting queries to be self-contained. Output only the rewritten query, nothing else."
                },
                {"role": "user", "content": rewrite_prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )

        rewritten: str = response.choices[0].message.content.strip() if response.choices[0].message.content else user_query

        # Remove quotes if LLM wrapped the response
        if rewritten.startswith('"') and rewritten.endswith('"'):
            rewritten = rewritten[1:-1]
        if rewritten.startswith("'") and rewritten.endswith("'"):
            rewritten = rewritten[1:-1]

        logger.debug(f"Query rewriting: '{user_query}' → '{rewritten}'")
        return rewritten

    except Exception as e:
        logger.debug(f"Query rewriting failed: {e}, using original query")
        # Fallback: return original query if rewriting fails
        return user_query


def run_agent(user_query: str, messages: list[MessageDict]) -> tuple[AgentResult, list[MessageDict]]:
    """
    Run the financial news agent.

    Args:
        user_query: User's question about a company or industry
        messages: Existing conversation history (includes system message)

    Returns:
        Tuple of (result dict, updated messages list)
    """
    client: OpenAI = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    tracker: TraceabilityTracker = TraceabilityTracker()
    config: ContextConfig = load_config()

    # Append new user query to existing conversation
    messages.append({"role": "user", "content": user_query})

    # Tool definitions
    tools: list[dict[str, Any]] = [get_tool_schema()]

    # Agent loop (max 10 iterations)
    final_answer: str | None = None
    total_tokens: int = 0  # Track cumulative token usage

    for iteration in range(10):
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

                with tracker.time_operation("LLM Reasoning Call", "llm_call", llm_metadata) as timing_node:
                    response = client.chat.completions.create(
                        model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
                        messages=messages,  # type: ignore[arg-type]
                        tools=tools,  # type: ignore[arg-type]
                        tool_choice="auto",
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
                    "tool_calls": assistant_message.tool_calls  # type: ignore[typeddict-item]
                })

                # Track reasoning if there's text content AND tool calls
                # (Don't add final answer to reasoning steps)
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
                            result: list[ArticleData] = execute_tool(tool_name, tool_args, tracker)

                        # Track the tool call
                        tracker.add_tool_call(tool_name, tool_args, result)

                        # Calculate starting ID BEFORE adding sources (for continuous numbering)
                        start_id: int = len(tracker.sources) + 1

                        # Add sources (use full result for traceability)
                        for article in result:
                            tracker.add_source({
                                "title": article.get("title", ""),
                                "date": article.get("published_at", ""),
                                "source": article.get("source", ""),
                                "url": article.get("url", ""),
                                "summary": article.get("description", ""),
                                "api_source": article.get("api_source", "unknown")
                            })

                        # Compress result for LLM context with correct offset
                        aggressive: bool = total_tokens > config["warning_threshold"]
                        compressed_articles: list[dict[str, Any]] = compress_tool_result(result, aggressive=aggressive, start_id=start_id)

                        # Add compressed tool result to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({"articles": compressed_articles}, ensure_ascii=False)
                        })
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

    # Rewrite query for evaluation (handles multi-turn context)
    rewritten_query: str
    with tracker.time_operation("Query Rewriting", "llm_call", {"purpose": "context_resolution"}):
        rewritten_query = rewrite_query_with_context(user_query, messages, client)

    # Self-evaluate the response with rewritten query
    evaluation: EvaluationResult
    with tracker.time_operation("Response Evaluation", "llm_call", {"purpose": "quality_assessment"}):
        evaluation = evaluate_response(final_answer, tracker, user_query=rewritten_query)

    # Return structured result and updated messages
    result: AgentResult = {
        "answer": final_answer,
        "sources": tracker.sources,
        "tool_calls": tracker.tool_calls,
        "reasoning_steps": tracker.reasoning_steps,
        "evaluation": evaluation,
        "trace": tracker.get_trace()
    }
    return result, messages


def run_agent_with_retry(user_query: str, messages: list[MessageDict]) -> tuple[AgentResult, list[MessageDict]]:
    """
    Run agent with retry/fix mechanism for low-quality responses.

    This is the main entry point that wraps run_agent() with retry logic.

    Args:
        user_query: User's question
        messages: Conversation history

    Returns:
        Tuple of (result dict, updated messages list)
    """
    # Create tracker at the top level to capture all timing
    tracker: TraceabilityTracker = TraceabilityTracker()
    config: RetryConfig = RetryConfig()

    # Track retry attempts
    attempt: int = 0
    retry_history: list[dict[str, Any]] = []  # Store attempts if show_attempts=true
    previous_result: AgentResult | None = None
    previous_messages: list[MessageDict] | None = None

    with tracker.time_operation("Agent Request", "request", {"query": user_query}):
        while attempt <= config.max_attempts:
            attempt_metadata: dict[str, Any] = {"attempt": attempt + 1, "max_attempts": config.max_attempts + 1}

            with tracker.time_operation(f"Attempt {attempt + 1}", "attempt", attempt_metadata):
                try:
                    # Run the agent
                    result: AgentResult
                    result, messages = run_agent(user_query, messages)

                    evaluation: EvaluationResult = result["evaluation"]

                    # Store attempt if configured
                    if config.show_attempts and attempt > 0:
                        retry_history.append({
                            "attempt": attempt,
                            "evaluation": evaluation,
                            "answer": result["answer"]
                        })

                    # Check if retry needed
                    if not config.should_retry(evaluation, attempt):
                        # Success or max attempts reached
                        if config.show_attempts and retry_history:
                            result["retry_history"] = retry_history  # type: ignore[typeddict-unknown-key]

                        # Merge timing from top-level tracker
                        if "trace" in result and "timing" not in result["trace"]:
                            result["trace"]["timing"] = tracker.get_timing_summary()  # type: ignore[typeddict-item]

                        return result, messages

                    # Save current result in case retry fails
                    previous_result = result
                    previous_messages = messages.copy()

                    # Decide strategy
                    strategy: str = decide_retry_strategy(evaluation, result["sources"], config)

                    if strategy == "none":
                        if config.show_attempts and retry_history:
                            result["retry_history"] = retry_history  # type: ignore[typeddict-unknown-key]

                        # Merge timing from top-level tracker
                        if "trace" in result and "timing" not in result["trace"]:
                            result["trace"]["timing"] = tracker.get_timing_summary()  # type: ignore[typeddict-item]

                        return result, messages

                    logger.info(f"[Retry {attempt + 1}/{config.max_attempts}] Strategy: {strategy.upper()}")
                    logger.info(f"Reason: Overall={evaluation['overall']:.1f}, Accuracy={evaluation.get('accuracy', 0)}/10")

                    # Execute retry strategy
                    if strategy == "fix":
                        # FIX: Continue conversation with improvement prompt
                        fix_prompt: str = build_fix_prompt(evaluation, user_query)
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
                            previous_result["retry_history"] = retry_history  # type: ignore[typeddict-unknown-key]

                        # Merge timing from top-level tracker
                        if previous_result and "trace" in previous_result and "timing" not in previous_result["trace"]:
                            previous_result["trace"]["timing"] = tracker.get_timing_summary()  # type: ignore[typeddict-item]

                        return previous_result, previous_messages  # type: ignore[return-value]

        # Max attempts exhausted
        logger.warning(f"Maximum retry attempts reached ({config.max_attempts})")
        if config.show_attempts and retry_history:
            result["retry_history"] = retry_history  # type: ignore[typeddict-unknown-key]

        # Merge timing from top-level tracker
        if "trace" in result and "timing" not in result["trace"]:
            result["trace"]["timing"] = tracker.get_timing_summary()  # type: ignore[typeddict-item]

        return result, messages


def _merge_tool_call_delta(accumulated: list[dict[str, Any]], deltas: list[Any]) -> None:
    """Merge incremental tool call deltas from streaming response."""
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
    messages: list[MessageDict]
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Async generator that yields events during agent execution.

    Yields:
        Event dicts with {"event": type, "data": {...}}

    Final event is always "done" with complete result.
    """
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    tracker = TraceabilityTracker()
    config = load_config()

    yield {"event": "agent_start", "data": {"query": user_query}}

    messages.append({"role": "user", "content": user_query})
    tools = [get_tool_schema()]
    final_answer = None
    total_tokens = 0

    for iteration in range(10):
        yield {"event": "iteration_start", "data": {"iteration": iteration + 1}}

        # Manage context (note: manage_context expects sync client, but we'll handle it)
        # For now, skip context management in streaming or make it work with async
        # messages = manage_context(messages, total_tokens, client, config)

        try:
            # Always use stream=True
            stream = await client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )

            # Accumulate response
            accumulated = {
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
            # (Don't add final answer to reasoning steps)
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
                    result = execute_tool(tool_name, tool_args, tracker)
                    tracker.add_tool_call(tool_name, tool_args, result)

                    # Calculate starting ID BEFORE adding sources (for continuous numbering)
                    start_id = len(tracker.sources) + 1

                    # Track sources
                    for article in result:
                        tracker.add_source({
                            "title": article.get("title", ""),
                            "date": article.get("published_at", ""),
                            "source": article.get("source", ""),
                            "url": article.get("url", ""),
                            "summary": article.get("description", ""),
                            "api_source": article.get("api_source", "unknown")
                        })

                    yield {
                        "event": "tool_call_complete",
                        "data": {
                            "tool_name": tool_name,
                            "result_summary": f"Retrieved {len(result)} articles",
                            "article_count": len(result),
                            "iteration": iteration + 1
                        }
                    }

                    # Compress and add to messages with correct offset
                    aggressive = total_tokens > config["warning_threshold"]
                    compressed_articles = compress_tool_result(result, aggressive=aggressive, start_id=start_id)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps({"articles": compressed_articles}, ensure_ascii=False)
                    })
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

    # Rewrite query for evaluation (using sync client for now)
    sync_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    rewritten_query = rewrite_query_with_context(user_query, messages, sync_client)

    # Self-evaluate
    evaluation = evaluate_response(final_answer, tracker, user_query=rewritten_query)
    yield {"event": "evaluation", "data": evaluation}

    # Emit timing summary
    timing_summary = tracker.get_timing_summary()
    if timing_summary["total_duration_ms"] > 0:
        yield {"event": "timing", "data": timing_summary}

    # Build final result
    result = {
        "answer": final_answer,
        "sources": tracker.sources,
        "tool_calls": tracker.tool_calls,
        "reasoning_steps": tracker.reasoning_steps,
        "evaluation": evaluation,
        "trace": tracker.get_trace()
    }

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
    messages: list
) -> AsyncGenerator[dict, None]:
    """Streaming version with retry support."""
    config = RetryConfig()
    attempt = 0
    retry_history = []

    while attempt < config.max_attempts:
        attempt += 1

        # Run agent and collect result
        result = None
        updated_messages = None

        async for event in run_agent_stream(user_query, messages):
            # Capture final result
            if event["event"] == "done":
                result = event["data"]["result"]
                updated_messages = event["data"]["messages"]

            # Forward all events
            yield event

        # Check if retry needed
        evaluation = result["evaluation"]
        should_retry = (
            evaluation["overall"] < config.threshold_overall or
            evaluation["accuracy"] < config.threshold_accuracy
        )

        if not should_retry or attempt >= config.max_attempts:
            # Add retry history to final result if any retries occurred
            if retry_history:
                result["retry_history"] = retry_history
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
        strategy = decide_retry_strategy(evaluation, result)
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
        if strategy == "redo":
            messages = create_conversation()  # Reset
            messages.append({"role": "user", "content": user_query})
        # else: continue with existing messages (fix strategy)
