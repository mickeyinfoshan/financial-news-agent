"""Retry/fix mechanism for low-quality responses."""

import os
from .types import EvaluationResult, SourceData, CitationValidationResult


class RetryConfig:
    """Configuration for retry mechanism."""

    def __init__(self) -> None:
        self.enabled: bool = os.getenv("RETRY_ENABLE", "true").lower() == "true"
        self.threshold_overall: float = float(os.getenv("RETRY_THRESHOLD_OVERALL", "6.0"))
        self.threshold_accuracy: float = float(os.getenv("RETRY_THRESHOLD_ACCURACY", "5.0"))
        self.max_attempts: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "1"))
        self.strategy: str = os.getenv("RETRY_STRATEGY", "auto")
        self.show_attempts: bool = os.getenv("RETRY_SHOW_ATTEMPTS", "true").lower() == "true"

    def should_retry(self, evaluation: EvaluationResult, attempt: int, citation_validation: CitationValidationResult | None = None) -> bool:
        """Check if retry should be attempted."""
        if not self.enabled or attempt >= self.max_attempts:
            return False

        # Force retry if citation validation failed
        if citation_validation and not citation_validation.get("validation_passed", True):
            return True

        overall: float = evaluation.get("overall", 0)
        accuracy: int = evaluation.get("accuracy", 0)

        return overall < self.threshold_overall or accuracy < self.threshold_accuracy


def decide_retry_strategy(
    evaluation: EvaluationResult,
    sources: list['SourceData'],
    config: RetryConfig,
    citation_validation: CitationValidationResult | None = None
) -> str:
    """
    Decide retry strategy based on evaluation scores.

    Strategy selection logic:
    - REDO: Fundamental issues (low accuracy/relevance, no sources) - needs fresh search
    - FIX: Minor issues (low coherence/reasonableness) - can improve with same sources
    - NONE: Quality acceptable or retry disabled

    Args:
        evaluation: Evaluation dict with scores
        sources: List of sources from tracker
        config: RetryConfig instance
        citation_validation: Optional citation validation result

    Returns:
        "fix", "redo", or "none"
    """
    # Manual override
    if config.strategy in ["fix", "redo", "disabled"]:
        return "none" if config.strategy == "disabled" else config.strategy

    # Auto strategy selection
    overall: float = evaluation.get("overall", 0)
    accuracy: int = evaluation.get("accuracy", 0)
    relevance: int = evaluation.get("relevance", 0)

    # Check if retry needed
    if not config.should_retry(evaluation, 0, citation_validation):
        return "none"

    # Citation validation failure → FIX strategy
    # Invalid citations mean the answer structure is wrong, but sources are likely correct
    # FIX will improve the answer using existing sources with better citation accuracy
    if citation_validation and not citation_validation.get("validation_passed", True):
        return "fix"

    # REDO: Major issues requiring fresh search
    # - Low accuracy: wrong information, needs better sources
    # - Low relevance: answered wrong question, needs better query
    # - No sources: search failed, needs to try again
    if accuracy < 5.0 or relevance < 4.0 or len(sources) == 0:
        return "redo"

    # FIX: Minor issues, existing sources are adequate
    # - Low coherence: narrative needs improvement
    # - Low reasonableness: analysis needs better logic
    return "fix"


def build_fix_prompt(evaluation: EvaluationResult, original_query: str, citation_validation: CitationValidationResult | None = None) -> str:
    """
    Build a prompt to fix the existing answer.

    Args:
        evaluation: Evaluation dict with scores and feedback
        original_query: The user's original query
        citation_validation: Optional citation validation result

    Returns:
        Fix prompt string
    """
    feedback: str = evaluation.get("feedback", "")
    scores: dict[str, int] = {
        "accuracy": evaluation.get("accuracy", 0),
        "relevance": evaluation.get("relevance", 0),
        "coherence": evaluation.get("coherence", 0),
        "reasonableness": evaluation.get("reasonableness", 0)
    }

    # Identify weak areas
    weak_areas: list[str] = [k for k, v in scores.items() if v < 6.0]

    # Build citation-specific guidance with claim-level details
    citation_guidance = ""
    if citation_validation and not citation_validation.get("validation_passed", True):
        claims = citation_validation.get("claims", [])

        # Collect claims with invalid citations (out of range)
        invalid_citation_claims = [
            c for c in claims
            if c.get("invalid_citations", [])
        ]

        # Collect claims that are unsupported by their sources
        unsupported_claims = [
            c for c in claims
            if c.get("validation_result", {}).get("supported") == False
        ]

        citation_issues = []

        # Detail invalid citation issues
        if invalid_citation_claims:
            citation_issues.append("INVALID CITATIONS (out of range):")
            for claim_data in invalid_citation_claims:
                claim_text = claim_data.get("claim", "")
                invalid_cites = claim_data.get("invalid_citations", [])
                all_cites = claim_data.get("citations", [])
                citation_issues.append(
                    f"  - Claim: \"{claim_text}\"\n"
                    f"    Used citations: {all_cites}\n"
                    f"    Invalid (out of range): {invalid_cites}"
                )

        # Detail unsupported claim issues
        if unsupported_claims:
            citation_issues.append("\nUNSUPPORTED CLAIMS (sources don't support the claim):")
            for claim_data in unsupported_claims:
                claim_text = claim_data.get("claim", "")
                cites = claim_data.get("citations", [])
                validation = claim_data.get("validation_result", {})
                explanation = validation.get("explanation", "No explanation")
                citation_issues.append(
                    f"  - Claim: \"{claim_text}\"\n"
                    f"    Citations used: {cites}\n"
                    f"    Why unsupported: {explanation}"
                )

        if citation_issues:
            citation_guidance = "\n" + "\n".join(citation_issues) + """

CRITICAL: You MUST fix all citation issues above:
1. Remove or replace invalid citation numbers that are out of range
2. Only cite sources that actually support your claims
3. If a claim is unsupported, either remove it or find supporting sources
"""

    prompt = f"""Your previous answer needs improvement. Here's the evaluation:

SCORES:
- Accuracy: {scores['accuracy']}/10
- Relevance: {scores['relevance']}/10
- Coherence: {scores['coherence']}/10
- Reasonableness: {scores['reasonableness']}/10

FEEDBACK: {feedback}
{citation_guidance}
WEAK AREAS: {', '.join(weak_areas) if weak_areas else 'overall quality'}

Please improve your answer by:
1. Addressing the weak areas identified above
2. Using the sources you already have (don't search again)
3. Improving the storyline coherence and logical flow
4. Strengthening the future impact analysis with better reasoning
5. Ensuring all citations [1], [2], etc. are accurate

Provide an improved version of your answer to the original query: "{original_query}"
"""
    return prompt


def build_redo_prompt(evaluation: EvaluationResult, original_query: str) -> str:
    """
    Build a prompt to redo the answer from scratch with fresh searches.

    Args:
        evaluation: Evaluation dict with scores and feedback
        original_query: The user's original query

    Returns:
        Redo prompt string
    """
    feedback: str = evaluation.get("feedback", "")

    prompt = f"""Your previous attempt had significant issues and needs to be redone.

EVALUATION FEEDBACK: {feedback}

You can see your previous attempt above (marked as internal). Learn from what didn't work, but DO NOT reuse those sources or tool results.

Please start fresh:
1. Search for news again with DIFFERENT and better search queries
2. Focus on finding highly relevant and accurate sources
3. Ensure you're answering the right question: "{original_query}"
4. Build a coherent storyline from the NEW sources
5. Provide well-reasoned future impact analysis

Answer the query: "{original_query}"
"""
    return prompt
