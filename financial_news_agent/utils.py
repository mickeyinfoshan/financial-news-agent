"""Utility functions for the financial news agent."""

import re


def extract_citations(text: str) -> list[int]:
    """
    Extract citation numbers from text.

    Args:
        text: Text containing citations in format [1], [2], [3], etc.

    Returns:
        Sorted list of unique citation numbers

    Example:
        >>> extract_citations("Apple stock rose [1]. Analysts predict growth [2][3].")
        [1, 2, 3]
    """
    citations: list[str] = re.findall(r'\[(\d+)\]', text)
    return sorted(set(int(c) for c in citations if c.isdigit()))


def strip_markdown(text: str) -> str:
    """
    Strip common markdown formatting from text.

    Removes: **bold**, _italic_, `code`, [links](url), ## headers, etc.

    Args:
        text: Text with markdown formatting

    Returns:
        Plain text with markdown removed

    Example:
        >>> strip_markdown("**Apple's revenue** grew `15%`")
        "Apple's revenue grew 15%"
    """
    # Triple asterisk (must come before double)
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)

    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # Italic: _text_ or *text* (single asterisk/underscore)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)

    # Inline code: `text`
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Links: [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Headers: ## Header (at line start)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    return text


def preprocess_answer(text: str) -> str:
    """
    Preprocess answer text for claim validation.

    Removes citation markers [1], [2], etc. and markdown formatting
    to enable plain-text claim matching.

    Args:
        text: Answer text with citations and markdown

    Returns:
        Plain text with citations and markdown removed

    Example:
        >>> preprocess_answer("**Apple's revenue** grew `15%` [1]")
        "Apple's revenue grew 15% "
    """
    # Remove citation markers [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)

    # Remove markdown formatting
    text = strip_markdown(text)

    return text
