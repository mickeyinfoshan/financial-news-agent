"""Context window management for the financial news agent.

This module provides functions to manage the conversation context window by:
1. Compressing tool results to reduce token usage
2. Summarizing old conversation history when approaching token limits
3. Tracking token usage from OpenAI API responses
"""

import os
import logging
from typing import Optional, TYPE_CHECKING
from openai import OpenAI

if TYPE_CHECKING:
    from .traceability import TraceabilityTracker

logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load context management configuration from environment variables.

    Returns:
        dict: Configuration dictionary with thresholds and settings
    """
    return {
        "token_threshold": int(os.getenv("CONTEXT_TOKEN_THRESHOLD", "12000")),
        "message_threshold": int(os.getenv("CONTEXT_MESSAGE_THRESHOLD", "15")),
        "recent_messages": int(os.getenv("CONTEXT_RECENT_MESSAGES", "4")),
        "warning_threshold": int(os.getenv("CONTEXT_WARNING_THRESHOLD", "8000")),
        "max_articles": int(os.getenv("CONTEXT_MAX_ARTICLES", "10")),
        "enable_compression": os.getenv("CONTEXT_ENABLE_COMPRESSION", "true").lower() == "true"
    }


def compress_tool_result(articles: list, aggressive: bool = False) -> list:
    """Compress tool result articles to save tokens.

    Tier 1 (always): Keep only essential fields (title, source, url, published_at)
    Tier 2 (aggressive): Limit to first 10 articles

    Args:
        articles: List of article dictionaries from news search
        aggressive: If True, apply aggressive compression (limit articles)

    Returns:
        list: Compressed articles with reduced fields and source numbering
    """
    if not articles:
        return []

    # Tier 2: Limit number of articles if aggressive mode
    if aggressive:
        articles = articles[:10]
        logger.info(f"Aggressive compression: limited to {len(articles)} articles")

    # Tier 1: Keep only essential fields and add source numbering
    compressed = []
    for idx, article in enumerate(articles, 1):
        compressed.append({
            "id": idx,
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "url": article.get("url", ""),
            "published_at": article.get("published_at", "")
        })

    return compressed


def summarize_history(messages: list, client: OpenAI, recent_count: int = 4) -> str:
    """Summarize middle conversation history using LLM.

    Preserves system message and recent N messages, summarizes everything in between.

    Args:
        messages: Full messages list
        client: OpenAI client for summarization API call
        recent_count: Number of recent messages to exclude from summary

    Returns:
        str: Summary text (200-400 tokens), or empty string if not enough to summarize
    """
    # Need at least: system message + some middle messages + recent messages
    if len(messages) <= recent_count + 1:
        logger.info("Not enough messages to summarize")
        return ""

    # Extract middle messages (skip system message at index 0 and recent messages)
    middle_messages = messages[1:-(recent_count)] if recent_count > 0 else messages[1:]

    if not middle_messages:
        logger.info("No middle messages to summarize")
        return ""

    # Format messages for summarization (truncate long content)
    formatted = []
    for msg in middle_messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        if content:
            # Truncate long content to avoid overwhelming the summarization prompt
            content_preview = content[:500] if len(content) > 500 else content
            formatted.append(f"{role.upper()}: {content_preview}")

    if not formatted:
        logger.info("No content to summarize")
        return ""

    history_text = "\n\n".join(formatted)

    prompt = f"""Summarize the following conversation history between a user and a financial news agent.

CONVERSATION HISTORY:
{history_text}

Create a concise summary (200-400 tokens) that preserves:
1. What queries the user asked
2. What tools were called and with what parameters
3. Key findings from news articles
4. Main conclusions or insights

Format as a narrative paragraph, not bullet points."""

    try:
        logger.info("Calling LLM for conversation summarization...")
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at summarizing conversations concisely while preserving key facts."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"Summarization complete: {len(summary)} characters")
        return summary

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return ""  # Return empty on failure, continue without summary


def manage_context(
    messages: list,
    total_tokens: int,
    client: OpenAI,
    config: Optional[dict] = None,
    tracker: Optional['TraceabilityTracker'] = None
) -> list:
    """Main context management function - checks and compresses context.

    Monitors token usage and message count. When thresholds are exceeded,
    summarizes old conversation history while preserving system message
    and recent messages.

    Args:
        messages: Current messages list
        total_tokens: Current token count from OpenAI API response.usage
        client: OpenAI client for summarization
        config: Optional config dict (uses load_config() if None)
        tracker: Optional traceability tracker for timing instrumentation

    Returns:
        list: Potentially modified messages list (with summarization if needed)
    """
    if config is None:
        config = load_config()

    # Check if compression is enabled
    if not config["enable_compression"]:
        logger.debug("Context compression disabled")
        return messages

    message_count = len(messages)

    logger.info(f"Context: {total_tokens} tokens, {message_count} messages")

    # Check if summarization needed
    token_exceeded = total_tokens > config["token_threshold"]
    message_exceeded = message_count > config["message_threshold"]

    if token_exceeded or message_exceeded:
        reason = []
        if token_exceeded:
            reason.append(f"tokens ({total_tokens} > {config['token_threshold']})")
        if message_exceeded:
            reason.append(f"messages ({message_count} > {config['message_threshold']})")

        logger.info(f"Context threshold exceeded: {', '.join(reason)}")
        logger.info("Summarizing conversation history...")

        # Generate summary with timing
        summary_metadata = {
            "reason": "token_exceeded" if token_exceeded else "message_exceeded",
            "tokens": total_tokens,
            "messages": message_count
        }

        if tracker:
            with tracker.time_operation("Conversation Summarization", "llm_call", summary_metadata):
                summary = summarize_history(messages, client, config["recent_messages"])
        else:
            summary = summarize_history(messages, client, config["recent_messages"])

        if summary:
            # Replace middle messages with summary
            recent_count = config["recent_messages"]
            system_msg = messages[0]
            recent_msgs = messages[-(recent_count):] if recent_count > 0 else []

            # Create new messages list: system + summary + recent messages
            new_messages = [
                system_msg,
                {
                    "role": "system",
                    "content": f"[Previous conversation summary]: {summary}",
                    "name": "context_summary"
                }
            ] + recent_msgs

            logger.info(
                f"Summarization applied: {message_count} messages -> "
                f"{len(new_messages)} messages"
            )

            return new_messages
        else:
            logger.warning("Summarization failed, keeping original messages")

    return messages
