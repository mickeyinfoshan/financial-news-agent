"""Main agent loop with LLM and tool calling."""

import os
import json
import logging
from openai import OpenAI
from .traceability import TraceabilityTracker
from .news_tool import get_tool_schema, execute_tool
from .evaluator import evaluate_response
from .context_manager import manage_context, compress_tool_result, load_config
from .retry_manager import RetryConfig, decide_retry_strategy, build_fix_prompt, build_redo_prompt

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

**IMPORTANT - Source Citations:**
When you receive news articles from the tool, they will be numbered (id: 1, 2, 3, etc.).
You MUST cite these sources in your answer using the format [1], [2], [3] whenever you reference information from them.

Example citation style:
"Apple's stock rose 5% following strong earnings [1]. Analysts predict continued growth in the AI sector [2][3]."

Always use the search_financial_news tool to gather information before answering.
Be thorough - you can call the tool multiple times with different queries if needed.
Base your analysis strictly on the sources you find and cite them appropriately."""


def create_conversation() -> list:
    """Create a new conversation with initialized system message.

    Returns:
        list: Messages list with system message
    """
    return [{"role": "system", "content": _SYSTEM_PROMPT}]


def rewrite_query_with_context(user_query: str, messages: list, client: OpenAI) -> str:
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
    pronouns = ['their', 'its', 'it', 'they', 'them', 'this', 'that', 'these', 'those']
    query_lower = user_query.lower()
    has_pronouns = any(f' {pronoun} ' in f' {query_lower} ' or
                      query_lower.startswith(f'{pronoun} ') or
                      query_lower.endswith(f' {pronoun}')
                      for pronoun in pronouns)

    # If no pronouns and query is reasonably long, likely self-contained
    if not has_pronouns and len(user_query.split()) > 3:
        return user_query

    # Build context from recent conversation (last 3-5 exchanges)
    # Exclude system message, focus on user-assistant exchanges
    context_messages = []
    for msg in messages[1:]:  # Skip system message
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "user" and content:
            context_messages.append(f"User: {content}")
        elif role == "assistant" and content:
            # Truncate long assistant responses
            content_preview = content[:300] if len(content) > 300 else content
            context_messages.append(f"Assistant: {content_preview}")

    # Limit to last 6 messages (3 exchanges) to avoid token bloat
    recent_context = context_messages[-6:] if len(context_messages) > 6 else context_messages
    context_text = "\n".join(recent_context)

    rewrite_prompt = f"""Given the conversation context below, rewrite the user's latest query to be self-contained and clear.

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

        rewritten = response.choices[0].message.content.strip()

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


def run_agent(user_query: str, messages: list) -> tuple[dict, list]:
    """
    Run the financial news agent.

    Args:
        user_query: User's question about a company or industry
        messages: Existing conversation history (includes system message)

    Returns:
        Tuple of (result dict, updated messages list)
    """
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    tracker = TraceabilityTracker()
    config = load_config()

    # Append new user query to existing conversation
    messages.append({"role": "user", "content": user_query})

    # Tool definitions
    tools = [get_tool_schema()]

    # Agent loop (max 10 iterations)
    final_answer = None
    total_tokens = 0  # Track cumulative token usage

    for iteration in range(10):
        logger.debug(f"[Iteration {iteration + 1}]")

        # Manage context window before LLM call
        messages = manage_context(messages, total_tokens, client, config)

        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000
            )

            # Track token usage from API response
            if hasattr(response, 'usage') and response.usage:
                total_tokens = response.usage.total_tokens
                logger.debug(f"Token usage: {total_tokens}")

            assistant_message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            logger.debug(f"Finish reason: {finish_reason}")
            logger.debug(f"Has tool calls: {bool(assistant_message.tool_calls)}")
            logger.debug(f"Content: {assistant_message.content[:100] if assistant_message.content else 'None'}...")

            # Add assistant message to conversation
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls
            })

            # Track reasoning if there's text content
            if assistant_message.content:
                tracker.add_reasoning(assistant_message.content)

            # Check if we have tool calls to execute
            if assistant_message.tool_calls:
                # Execute tool calls
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    # Execute the tool
                    result = execute_tool(tool_name, tool_args)

                    # Track the tool call
                    tracker.add_tool_call(tool_name, tool_args, result)

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

                    # Compress result for LLM context
                    aggressive = total_tokens > config["warning_threshold"]
                    compressed_articles = compress_tool_result(result, aggressive=aggressive)

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
    rewritten_query = rewrite_query_with_context(user_query, messages, client)

    # Self-evaluate the response with rewritten query
    evaluation = evaluate_response(final_answer, tracker, user_query=rewritten_query)

    # Return structured result and updated messages
    return {
        "answer": final_answer,
        "sources": tracker.sources,
        "tool_calls": tracker.tool_calls,
        "reasoning_steps": tracker.reasoning_steps,
        "evaluation": evaluation,
        "trace": tracker.get_trace()
    }, messages


def run_agent_with_retry(user_query: str, messages: list) -> tuple[dict, list]:
    """
    Run agent with retry/fix mechanism for low-quality responses.

    This is the main entry point that wraps run_agent() with retry logic.

    Args:
        user_query: User's question
        messages: Conversation history

    Returns:
        Tuple of (result dict, updated messages list)
    """
    config = RetryConfig()

    # Track retry attempts
    attempt = 0
    retry_history = []  # Store attempts if show_attempts=true
    previous_result = None
    previous_messages = None

    while attempt <= config.max_attempts:
        try:
            # Run the agent
            result, messages = run_agent(user_query, messages)

            evaluation = result["evaluation"]

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
                    result["retry_history"] = retry_history
                return result, messages

            # Save current result in case retry fails
            previous_result = result
            previous_messages = messages.copy()

            # Decide strategy
            strategy = decide_retry_strategy(evaluation, result["sources"], config)

            if strategy == "none":
                if config.show_attempts and retry_history:
                    result["retry_history"] = retry_history
                return result, messages

            logger.info(f"[Retry {attempt + 1}/{config.max_attempts}] Strategy: {strategy.upper()}")
            logger.info(f"Reason: Overall={evaluation['overall']:.1f}, Accuracy={evaluation.get('accuracy', 0)}/10")

            # Execute retry strategy
            if strategy == "fix":
                # FIX: Continue conversation with improvement prompt
                fix_prompt = build_fix_prompt(evaluation, user_query)
                messages.append({"role": "user", "content": fix_prompt})

            elif strategy == "redo":
                # REDO: Reset to system message + new query
                system_msg = messages[0]
                redo_prompt = build_redo_prompt(evaluation, user_query)
                messages = [system_msg, {"role": "user", "content": redo_prompt}]

            attempt += 1

        except Exception as e:
            logger.error(f"Error during retry (attempt {attempt}): {e}")
            if attempt == 0:
                # First attempt failed, re-raise
                raise
            else:
                # Retry failed, return previous result
                if config.show_attempts and retry_history:
                    previous_result["retry_history"] = retry_history
                return previous_result, previous_messages

    # Max attempts exhausted
    logger.warning(f"Maximum retry attempts reached ({config.max_attempts})")
    if config.show_attempts and retry_history:
        result["retry_history"] = retry_history
    return result, messages
