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
    citations = re.findall(r'\[(\d+)\]', text)
    return sorted(set(int(c) for c in citations if c.isdigit()))
