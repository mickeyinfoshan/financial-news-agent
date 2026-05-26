"""Context window management for the financial news agent.

This module provides functions to manage the conversation context window by:
1. Compressing tool results to reduce token usage
2. Summarizing old conversation history when approaching token limits
3. Tracking token usage from OpenAI API responses
"""

import os
import logging
from typing import Any
from openai import OpenAI

from .traceability import TraceabilityTracker
from .types import ContextConfig, MessageDict, ArticleData

logger = logging.getLogger(__name__)


def load_config() -> ContextConfig:
    """Load context management configuration from environment variables.

    Returns:
        dict: Configuration dictionary with thresholds and settings
    """
    return {
        "token_threshold": int(os.getenv("CONTEXT_TOKEN_THRESHOLD", "600000")),
        "message_threshold": int(os.getenv("CONTEXT_MESSAGE_THRESHOLD", "100")),
        "recent_messages": int(os.getenv("CONTEXT_RECENT_MESSAGES", "20")),
        "warning_threshold": int(os.getenv("CONTEXT_WARNING_THRESHOLD", "400000")),
        "max_articles": int(os.getenv("CONTEXT_MAX_ARTICLES", "10")),
        "enable_compression": os.getenv("CONTEXT_ENABLE_COMPRESSION", "true").lower() == "true"
    }


def compress_tool_result(articles: list[ArticleData], aggressive: bool = False, start_id: int = 1) -> list[dict[str, Any]]:
    """Compress tool result articles to save tokens.

    Two-tier compression strategy:
    - Tier 1 (always): Remove description/content fields - LLM only needs metadata
    - Tier 2 (aggressive): Limit to 10 articles when approaching token limits

    Args:
        articles: List of article dictionaries from news search
        aggressive: If True, apply aggressive compression (limit articles)
        start_id: Starting ID for numbering (default: 1). Use len(tracker.sources) + 1
                  for continuous numbering across multiple tool calls.

    Returns:
        list: Compressed articles with reduced fields and source numbering
    """
    if not articles:
        return []

    # Tier 2: Limit number of articles if aggressive mode
    compressed_articles: list[ArticleData] = articles
    if aggressive:
        compressed_articles = articles[:10]
        logger.info(f"Aggressive compression: limited to {len(compressed_articles)} articles")

    # Tier 1: Keep only essential fields and add source numbering
    compressed: list[dict[str, Any]] = []
    for idx, article in enumerate(compressed_articles, start_id):
        compressed.append({
            "id": idx,
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "url": article.get("url", ""),
            "published_at": article.get("published_at", "")
        })

    return compressed


def summarize_history(messages: list[MessageDict], client: OpenAI, recent_count: int = 4) -> str:
    """Summarize middle conversation history using LLM.

    Preserves system message and recent N messages, summarizes everything in between.
    This prevents context window overflow in long conversations while maintaining
    recent context for coherent multi-turn dialogue.

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
    middle_messages: list[MessageDict] = messages[1:-(recent_count)] if recent_count > 0 else messages[1:]

    if not middle_messages:
        logger.info("No middle messages to summarize")
        return ""

    # Format messages for summarization
    formatted: list[str] = []
    for msg in middle_messages:
        role: str = msg.get("role", "")
        content: str | None = msg.get("content", "")

        if content:
            # Truncate to 500 chars - prevents summarization prompt from becoming too large
            content_preview: str = content[:500] if len(content) > 500 else content
            formatted.append(f"{role.upper()}: {content_preview}")

    if not formatted:
        logger.info("No content to summarize")
        return ""

    history_text: str = "\n\n".join(formatted)

    prompt: str = f"""Summarize the following conversation history between a user and a financial news agent.

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

        summary: str = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
        logger.info(f"Summarization complete: {len(summary)} characters")
        return summary

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return ""  # Return empty on failure, continue without summary


def manage_context(
    messages: list['MessageDict'],
    total_tokens: int,
    client: OpenAI,
    config: 'ContextConfig | None' = None,
    tracker: 'TraceabilityTracker | None' = None
) -> list[MessageDict]:
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

    message_count: int = len(messages)

    logger.info(f"Context: {total_tokens} tokens, {message_count} messages")

    # Check if summarization needed
    token_exceeded: bool = total_tokens > config["token_threshold"]
    message_exceeded: bool = message_count > config["message_threshold"]

    if token_exceeded or message_exceeded:
        reason: list[str] = []
        if token_exceeded:
            reason.append(f"tokens ({total_tokens} > {config['token_threshold']})")
        if message_exceeded:
            reason.append(f"messages ({message_count} > {config['message_threshold']})")

        logger.info(f"Context threshold exceeded: {', '.join(reason)}")
        logger.info("Summarizing conversation history...")

        # Generate summary with timing
        summary_metadata: dict[str, Any] = {
            "reason": "token_exceeded" if token_exceeded else "message_exceeded",
            "tokens": total_tokens,
            "messages": message_count
        }

        summary: str
        if tracker:
            with tracker.time_operation("Conversation Summarization", "llm_call", summary_metadata):
                summary = summarize_history(messages, client, config["recent_messages"])
        else:
            summary = summarize_history(messages, client, config["recent_messages"])

        if summary:
            # Replace middle messages with summary
            recent_count: int = config["recent_messages"]
            system_msg: MessageDict = messages[0]
            recent_msgs: list[MessageDict] = messages[-(recent_count):] if recent_count > 0 else []

            # Create new messages list: system + summary + recent messages
            summary_msg: MessageDict = {
                "role": "system",
                "content": f"[Previous conversation summary]: {summary}",
                "name": "context_summary",
                "internal": True
            }
            new_messages: list[MessageDict] = [system_msg, summary_msg] + recent_msgs

            logger.info(
                f"Summarization applied: {message_count} messages -> "
                f"{len(new_messages)} messages"
            )

            return new_messages
        else:
            logger.warning("Summarization failed, keeping original messages")

    return messages
