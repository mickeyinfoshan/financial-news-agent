"""Query context resolution for multi-turn conversations."""

import os
import logging
from openai import OpenAI
from ..types import MessageDict

logger = logging.getLogger(__name__)


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
    # Skip rewriting on first turn - no prior context exists
    if len(messages) <= 1:
        return user_query

    # Skip rewriting if query appears self-contained (no pronouns, sufficient length)
    # Avoids unnecessary LLM call when query is already clear
    pronouns: list[str] = ['their', 'its', 'it', 'they', 'them', 'this', 'that', 'these', 'those']
    query_lower: str = user_query.lower()
    has_pronouns: bool = any(f' {pronoun} ' in f' {query_lower} ' or
                      query_lower.startswith(f'{pronoun} ') or
                      query_lower.endswith(f' {pronoun}')
                      for pronoun in pronouns)

    if not has_pronouns and len(user_query.split()) > 3:
        return user_query

    # Build context from recent conversation (last 3-5 exchanges)
    context_messages: list[str] = []
    for msg in messages[1:]:  # Skip system message - it doesn't contain conversation history
        role: str = msg.get("role", "")
        content: str | None = msg.get("content", "")

        if role == "user" and content:
            context_messages.append(f"User: {content}")
        elif role == "assistant" and content:
            # Truncate to 300 chars - full responses would overwhelm the rewriting prompt
            content_preview: str = content[:300] if len(content) > 300 else content
            context_messages.append(f"Assistant: {content_preview}")

    # Limit to 6 messages (3 exchanges) - older context rarely helps pronoun resolution
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
            model=os.getenv("OPENAI_MODEL", "gpt-5.5"),
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

        # Strip quotes - LLMs sometimes wrap output in quotes despite instructions
        if rewritten.startswith('"') and rewritten.endswith('"'):
            rewritten = rewritten[1:-1]
        if rewritten.startswith("'") and rewritten.endswith("'"):
            rewritten = rewritten[1:-1]

        logger.debug(f"Query rewriting: '{user_query}' → '{rewritten}'")
        return rewritten

    except Exception as e:
        logger.debug(f"Query rewriting failed: {e}, using original query")
        # Graceful degradation - better to evaluate with ambiguous query than fail
        return user_query
