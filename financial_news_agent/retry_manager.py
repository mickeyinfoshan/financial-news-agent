"""Retry/fix mechanism for low-quality responses."""

import os


class RetryConfig:
    """Configuration for retry mechanism."""

    def __init__(self):
        self.enabled = os.getenv("RETRY_ENABLE", "true").lower() == "true"
        self.threshold_overall = float(os.getenv("RETRY_THRESHOLD_OVERALL", "6.0"))
        self.threshold_accuracy = float(os.getenv("RETRY_THRESHOLD_ACCURACY", "5.0"))
        self.max_attempts = int(os.getenv("RETRY_MAX_ATTEMPTS", "1"))
        self.strategy = os.getenv("RETRY_STRATEGY", "auto")
        self.show_attempts = os.getenv("RETRY_SHOW_ATTEMPTS", "true").lower() == "true"

    def should_retry(self, evaluation: dict, attempt: int) -> bool:
        """Check if retry should be attempted."""
        if not self.enabled or attempt >= self.max_attempts:
            return False

        overall = evaluation.get("overall", 0)
        accuracy = evaluation.get("accuracy", 0)

        return overall < self.threshold_overall or accuracy < self.threshold_accuracy


def decide_retry_strategy(
    evaluation: dict,
    sources: list,
    config: RetryConfig
) -> str:
    """
    Decide retry strategy based on evaluation scores.

    Args:
        evaluation: Evaluation dict with scores
        sources: List of sources from tracker
        config: RetryConfig instance

    Returns:
        "fix", "redo", or "none"
    """
    # Manual override
    if config.strategy in ["fix", "redo", "disabled"]:
        return "none" if config.strategy == "disabled" else config.strategy

    # Auto strategy selection
    overall = evaluation.get("overall", 0)
    accuracy = evaluation.get("accuracy", 0)
    relevance = evaluation.get("relevance", 0)

    # Check if retry needed
    if not config.should_retry(evaluation, 0):
        return "none"

    # REDO conditions (major issues)
    if accuracy < 5.0 or relevance < 4.0 or len(sources) == 0:
        return "redo"

    # FIX conditions (minor issues)
    return "fix"


def build_fix_prompt(evaluation: dict, original_query: str) -> str:
    """
    Build a prompt to fix the existing answer.

    Args:
        evaluation: Evaluation dict with scores and feedback
        original_query: The user's original query

    Returns:
        Fix prompt string
    """
    feedback = evaluation.get("feedback", "")
    scores = {
        "accuracy": evaluation.get("accuracy", 0),
        "relevance": evaluation.get("relevance", 0),
        "coherence": evaluation.get("coherence", 0),
        "reasonableness": evaluation.get("reasonableness", 0)
    }

    # Identify weak areas
    weak_areas = [k for k, v in scores.items() if v < 6.0]

    prompt = f"""Your previous answer needs improvement. Here's the evaluation:

SCORES:
- Accuracy: {scores['accuracy']}/10
- Relevance: {scores['relevance']}/10
- Coherence: {scores['coherence']}/10
- Reasonableness: {scores['reasonableness']}/10

FEEDBACK: {feedback}

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


def build_redo_prompt(evaluation: dict, original_query: str) -> str:
    """
    Build a prompt to redo the answer from scratch.

    Args:
        evaluation: Evaluation dict with scores and feedback
        original_query: The user's original query

    Returns:
        Redo prompt string
    """
    feedback = evaluation.get("feedback", "")

    prompt = f"""Your previous attempt had significant issues and needs to be redone.

EVALUATION FEEDBACK: {feedback}

Please start fresh:
1. Search for news again with better search queries
2. Focus on finding highly relevant and accurate sources
3. Ensure you're answering the right question: "{original_query}"
4. Build a coherent storyline from the sources
5. Provide well-reasoned future impact analysis

Answer the query: "{original_query}"
"""
    return prompt
