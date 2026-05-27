"""Unit tests for citation_validator module."""

import pytest
from financial_news_agent.citation_validator import (
    validate_extraction,
    validate_citation_ranges
)
from financial_news_agent.types import ClaimData


class TestValidateExtraction:
    """Tests for validate_extraction function."""

    def test_validate_extraction_with_plain_text(self):
        """Test extraction validation with plain text (no markdown)."""
        answer = "Apple's revenue grew 15% [1]. Market is strong [2]."
        claims: list[ClaimData] = [
            {"claim": "Apple's revenue grew 15%", "citations": [1], "invalid_citations": []},
            {"claim": "Market is strong", "citations": [2], "invalid_citations": []}
        ]

        is_valid, errors = validate_extraction(answer, claims)
        assert is_valid
        assert len(errors) == 0

    def test_validate_extraction_with_markdown_bold(self):
        """Test extraction validation handles bold markdown."""
        answer = "**Apple's revenue grew 15%** [1]."
        claims: list[ClaimData] = [
            {"claim": "Apple's revenue grew 15%", "citations": [1], "invalid_citations": []}
        ]

        is_valid, errors = validate_extraction(answer, claims)
        assert is_valid
        assert len(errors) == 0

    def test_validate_extraction_with_markdown_code(self):
        """Test extraction validation handles inline code markdown."""
        answer = "The company reported `strong` iPhone sales [1]."
        claims: list[ClaimData] = [
            {"claim": "The company reported strong iPhone sales", "citations": [1], "invalid_citations": []}
        ]

        is_valid, errors = validate_extraction(answer, claims)
        assert is_valid
        assert len(errors) == 0

    def test_validate_extraction_with_markdown_links(self):
        """Test extraction validation handles markdown links."""
        answer = "Analysts are [optimistic](https://example.com) about growth [1]."
        claims: list[ClaimData] = [
            {"claim": "Analysts are optimistic about growth", "citations": [1], "invalid_citations": []}
        ]

        is_valid, errors = validate_extraction(answer, claims)
        assert is_valid
        assert len(errors) == 0

    def test_validate_extraction_with_markdown_headers(self):
        """Test extraction validation handles markdown headers."""
        answer = """## Future Outlook
        The tech sector shows resilience [1]."""
        claims: list[ClaimData] = [
            {"claim": "The tech sector shows resilience", "citations": [1], "invalid_citations": []}
        ]

        is_valid, errors = validate_extraction(answer, claims)
        assert is_valid
        assert len(errors) == 0

    def test_validate_extraction_with_mixed_markdown(self):
        """Test extraction validation handles multiple markdown formats."""
        answer = """**Apple's revenue grew 15%** [1].
        The company reported `strong` iPhone sales [2].
        Analysts are [optimistic](https://example.com) about growth [3].
        ## Future Outlook
        The _tech sector_ shows resilience [4]."""

        claims: list[ClaimData] = [
            {"claim": "Apple's revenue grew 15%", "citations": [1], "invalid_citations": []},
            {"claim": "The company reported strong iPhone sales", "citations": [2], "invalid_citations": []},
            {"claim": "Analysts are optimistic about growth", "citations": [3], "invalid_citations": []},
            {"claim": "The tech sector shows resilience", "citations": [4], "invalid_citations": []}
        ]

        is_valid, errors = validate_extraction(answer, claims)
        assert is_valid
        assert len(errors) == 0

    def test_validate_extraction_detects_hallucinated_claims(self):
        """Test detection of hallucinated claims not in answer."""
        answer = "Apple's revenue grew 15% [1]."
        claims: list[ClaimData] = [
            {"claim": "Tesla revenue doubled", "citations": [2], "invalid_citations": []}
        ]

        is_valid, errors = validate_extraction(answer, claims)
        assert not is_valid
        assert len(errors) > 0
        assert "not found in answer" in errors[0]

    def test_validate_extraction_detects_missing_citations(self):
        """Test detection of citations not present in answer."""
        answer = "Apple's revenue grew 15% [1]."
        claims: list[ClaimData] = [
            {"claim": "Apple's revenue grew 15%", "citations": [1, 5], "invalid_citations": []}
        ]

        is_valid, errors = validate_extraction(answer, claims)
        assert not is_valid
        assert len(errors) > 0
        assert "citation [5] not found" in errors[0]


class TestValidateCitationRanges:
    """Tests for validate_citation_ranges function."""

    def test_validate_citation_ranges_all_valid(self):
        """Test citation range validation with all valid citations."""
        claims: list[ClaimData] = [
            {"claim": "Test claim 1", "citations": [1, 2, 3], "invalid_citations": []},
            {"claim": "Test claim 2", "citations": [4, 5], "invalid_citations": []}
        ]

        result = validate_citation_ranges(claims, num_sources=5)

        assert result[0]["invalid_citations"] == []
        assert result[1]["invalid_citations"] == []

    def test_validate_citation_ranges_detects_out_of_range(self):
        """Test detection of citations outside valid range."""
        claims: list[ClaimData] = [
            {"claim": "Test claim 1", "citations": [1, 2, 3], "invalid_citations": []},
            {"claim": "Test claim 2", "citations": [1, 10, 15], "invalid_citations": []}
        ]

        result = validate_citation_ranges(claims, num_sources=5)

        assert result[0]["invalid_citations"] == []
        assert result[1]["invalid_citations"] == [10, 15]

    def test_validate_citation_ranges_detects_zero_and_negative(self):
        """Test detection of zero and negative citation numbers."""
        claims: list[ClaimData] = [
            {"claim": "Test claim", "citations": [0, -1, 1, 2], "invalid_citations": []}
        ]

        result = validate_citation_ranges(claims, num_sources=5)

        assert 0 in result[0]["invalid_citations"]
        assert -1 in result[0]["invalid_citations"]
        assert 1 not in result[0]["invalid_citations"]
        assert 2 not in result[0]["invalid_citations"]
