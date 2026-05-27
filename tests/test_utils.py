"""Unit tests for utils module."""

import pytest
from financial_news_agent.utils import extract_citations, strip_markdown, preprocess_answer


class TestExtractCitations:
    """Tests for extract_citations function."""

    def test_extract_citations_single(self):
        """Test extraction of single citation."""
        text = "Apple grew 15% [1]."
        citations = extract_citations(text)
        assert citations == [1]

    def test_extract_citations_multiple(self):
        """Test extraction of multiple citations."""
        text = "Apple grew 15% [1]. Market is strong [2][3]. Future looks good [5]."
        citations = extract_citations(text)
        assert citations == [1, 2, 3, 5]

    def test_extract_citations_duplicates(self):
        """Test that duplicate citations are deduplicated."""
        text = "Apple grew [1]. Revenue up [1]. Profit high [2]."
        citations = extract_citations(text)
        assert citations == [1, 2]

    def test_extract_citations_unordered(self):
        """Test that citations are returned sorted."""
        text = "Text [5] and [2] and [8] and [1]."
        citations = extract_citations(text)
        assert citations == [1, 2, 5, 8]

    def test_extract_citations_none(self):
        """Test extraction when no citations present."""
        text = "No citations here."
        citations = extract_citations(text)
        assert citations == []


class TestStripMarkdown:
    """Tests for strip_markdown function."""

    def test_strip_markdown_bold_double_asterisk(self):
        """Test stripping bold with double asterisk."""
        assert strip_markdown("**bold text**") == "bold text"

    def test_strip_markdown_bold_double_underscore(self):
        """Test stripping bold with double underscore."""
        assert strip_markdown("__bold text__") == "bold text"

    def test_strip_markdown_italic_single_asterisk(self):
        """Test stripping italic with single asterisk."""
        assert strip_markdown("*italic text*") == "italic text"

    def test_strip_markdown_italic_single_underscore(self):
        """Test stripping italic with single underscore."""
        assert strip_markdown("_italic text_") == "italic text"

    def test_strip_markdown_triple_asterisk(self):
        """Test stripping triple asterisk (bold+italic)."""
        assert strip_markdown("***bold italic***") == "bold italic"

    def test_strip_markdown_inline_code(self):
        """Test stripping inline code."""
        assert strip_markdown("`code snippet`") == "code snippet"

    def test_strip_markdown_links(self):
        """Test stripping markdown links."""
        assert strip_markdown("[link text](https://example.com)") == "link text"

    def test_strip_markdown_headers(self):
        """Test stripping markdown headers."""
        assert strip_markdown("## Header") == "Header"
        assert strip_markdown("### Subheader") == "Subheader"

    def test_strip_markdown_mixed_formats(self):
        """Test stripping multiple markdown formats."""
        text = "**bold** and _italic_ and `code`"
        assert strip_markdown(text) == "bold and italic and code"

    def test_strip_markdown_preserves_plain_text(self):
        """Test that plain text is unchanged."""
        text = "Plain text without markdown"
        assert strip_markdown(text) == text


class TestPreprocessAnswer:
    """Tests for preprocess_answer function."""

    def test_preprocess_answer_removes_citations(self):
        """Test that citation markers are removed."""
        text = "Text with [1] and [2] citations"
        result = preprocess_answer(text)
        assert "[1]" not in result
        assert "[2]" not in result

    def test_preprocess_answer_removes_markdown(self):
        """Test that markdown formatting is removed."""
        text = "**Bold** and _italic_ text"
        result = preprocess_answer(text)
        assert "**" not in result
        assert "_" not in result
        assert "Bold and italic text" in result

    def test_preprocess_answer_removes_both(self):
        """Test that both citations and markdown are removed."""
        text = "**Apple's revenue** grew `15%` [1]"
        result = preprocess_answer(text)
        assert "[1]" not in result
        assert "**" not in result
        assert "`" not in result
        assert "Apple's revenue grew 15%" in result

    def test_preprocess_answer_complex_example(self):
        """Test preprocessing with complex markdown and citations."""
        text = "**Bold** [1] and _italic_ [2] and `code` [3]"
        result = preprocess_answer(text)
        # Should have plain text only
        assert "Bold  and italic  and code " == result

    def test_preprocess_answer_preserves_content(self):
        """Test that actual content is preserved."""
        text = "Apple's revenue grew 15% [1]"
        result = preprocess_answer(text)
        assert "Apple's revenue grew 15%" in result
