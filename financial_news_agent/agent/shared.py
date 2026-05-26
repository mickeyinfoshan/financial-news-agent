"""Shared business logic used by both sync and async implementations."""

import json
import logging
from typing import Any
from openai import OpenAI
from ..types import AgentResult, MessageDict, EvaluationResult, ArticleData, ContextConfig, CitationValidationResult
from ..traceability import TraceabilityTracker
from ..evaluator import evaluate_response
from ..context_manager import compress_tool_result
from ..retry_manager import RetryConfig, decide_retry_strategy
from ..citation_validator import validate_citations
from .query_rewriter import rewrite_query_with_context

logger = logging.getLogger(__name__)


def do_query_rewriting(
    user_query: str,
    messages: list[MessageDict],
    client: OpenAI,
    tracker: TraceabilityTracker
) -> str:
    """
    Rewrite query with conversation context for better evaluation.

    Wraps timing tracking around query rewriting operation.
    """
    with tracker.time_operation("Query Rewriting", "llm_call", {"purpose": "context_resolution"}):
        return rewrite_query_with_context(user_query, messages, client)


def do_citation_validation(
    final_answer: str,
    sources: list[Any],
    client: OpenAI,
    tracker: TraceabilityTracker
) -> CitationValidationResult | None:
    """
    Validate citations in the final answer against sources.

    Returns None if validation fails (logs error but doesn't crash).
    Wraps timing tracking around validation operation.
    """
    with tracker.time_operation("Citation Validation", "validation", {"purpose": "citation_quality"}):
        try:
            result = validate_citations(final_answer, sources, client)
            logger.info(
                f"Citation validation: {len(result['claims'])} claims, "
                f"{result['total_invalid_citations']} invalid citations, "
                f"passed={result['validation_passed']}"
            )
            return result
        except Exception as e:
            logger.error(f"Citation validation failed: {e}")
            return None


def do_evaluation(
    final_answer: str,
    tracker: TraceabilityTracker,
    rewritten_query: str
) -> EvaluationResult:
    """
    Evaluate response quality using rewritten query.

    Wraps timing tracking around evaluation operation.
    """
    with tracker.time_operation("Response Evaluation", "llm_call", {"purpose": "quality_assessment"}):
        return evaluate_response(final_answer, tracker, user_query=rewritten_query)


def build_agent_result(
    final_answer: str,
    tracker: TraceabilityTracker,
    evaluation: EvaluationResult,
    citation_validation: CitationValidationResult | None
) -> AgentResult:
    """
    Build final AgentResult from components.

    Pure data assembly - no side effects or LLM calls.
    """
    result: AgentResult = {
        "answer": final_answer,
        "sources": tracker.sources,
        "tool_calls": tracker.tool_calls,
        "reasoning_steps": tracker.reasoning_steps,
        "evaluation": evaluation,
        "trace": tracker.get_trace()
    }

    if citation_validation:
        result["citation_validation"] = citation_validation

    return result


def process_tool_results(
    tool_result: list[ArticleData],
    tracker: TraceabilityTracker
) -> None:
    """
    Add articles from tool result to tracker.sources.

    Args:
        tool_result: Tool execution result containing articles
        tracker: TraceabilityTracker to add sources to
    """
    for article in tool_result:
        tracker.add_source({
            "title": article.get("title", ""),
            "date": article.get("published_at", ""),
            "source": article.get("source", ""),
            "url": article.get("url", ""),
            "summary": article.get("description", ""),
            "api_source": article.get("api_source", "unknown")
        })


def compress_and_build_tool_message(
    tool_result: list[ArticleData],
    tool_call_id: str,
    total_tokens: int,
    config: ContextConfig,
    start_id: int
) -> MessageDict:
    """
    Compress tool results based on token usage and build tool response message.

    Args:
        tool_result: Raw tool execution result
        tool_call_id: ID of the tool call
        total_tokens: Current total token count
        config: Context configuration with thresholds
        start_id: Starting ID for source numbering

    Returns:
        Tool response message dict
    """
    aggressive: bool = total_tokens > config["warning_threshold"]
    compressed_articles: list[dict[str, Any]] = compress_tool_result(
        tool_result,
        aggressive=aggressive,
        start_id=start_id
    )

    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": json.dumps({"articles": compressed_articles}, ensure_ascii=False)
    }


def should_force_final_answer(iteration: int, max_iterations: int) -> tuple[bool, str]:
    """
    Determine if we should force a final answer on this iteration.

    Args:
        iteration: Current iteration number (0-indexed)
        max_iterations: Maximum allowed iterations

    Returns:
        Tuple of (is_final, tool_choice_param)
    """
    is_final_iteration = (iteration == max_iterations - 1)
    tool_choice_param = "none" if is_final_iteration else "auto"
    return is_final_iteration, tool_choice_param


def should_retry(
    evaluation: EvaluationResult,
    attempt: int,
    config: RetryConfig
) -> bool:
    """
    Determine if retry is needed based on evaluation scores.

    Args:
        evaluation: Evaluation result with scores
        attempt: Current attempt number (0-indexed)
        config: Retry configuration with thresholds

    Returns:
        True if retry should be attempted
    """
    return config.should_retry(evaluation, attempt)


def decide_retry_strategy_wrapper(
    evaluation: EvaluationResult,
    sources: list[Any],
    config: RetryConfig
) -> str:
    """
    Decide retry strategy (fix, redo, or none).

    Args:
        evaluation: Evaluation result with scores
        sources: List of sources used
        config: Retry configuration

    Returns:
        "fix", "redo", or "none"
    """
    return decide_retry_strategy(evaluation, sources, config)
