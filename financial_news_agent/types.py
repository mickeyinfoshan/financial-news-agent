"""Type definitions for the financial news agent.

This module contains TypedDict definitions for all complex data structures
used throughout the agent system. Using TypedDict provides type safety with
zero runtime overhead.
"""

from typing import TypedDict, Any, NotRequired


class ArticleData(TypedDict):
    """Raw article data from news APIs (NewsAPI or Finnhub)."""
    title: str
    description: str
    source: str
    url: str
    published_at: str
    content: str
    api_source: str


class SourceData(TypedDict):
    """Processed source data for traceability and citations."""
    id: int
    title: str
    date: str
    source: str
    url: str
    summary: str
    api_source: str


class EvaluationResult(TypedDict):
    """LLM evaluation result with scores and feedback."""
    accuracy: int
    relevance: int
    coherence: int
    reasonableness: int
    overall: float
    feedback: str


class ToolCallRecord(TypedDict):
    """Record of a tool call execution."""
    tool: str
    args: dict[str, Any]
    result_summary: dict[str, Any]


class RetryAttempt(TypedDict):
    """Record of a retry attempt with evaluation and answer."""
    attempt: int
    evaluation: EvaluationResult
    answer: str


class TimingOperation(TypedDict):
    """Single timing operation record."""
    name: str
    duration_ms: float
    metadata: dict[str, Any]


class TimingBreakdown(TypedDict):
    """Timing breakdown by category."""
    total_ms: float
    count: int
    operations: list[TimingOperation]


class TimingNodeDict(TypedDict):
    """Hierarchical timing node for serialization."""
    name: str
    category: str
    duration_ms: float | None
    metadata: dict[str, Any]
    error: NotRequired[str]
    children: NotRequired[list['TimingNodeDict']]


class TimingSummary(TypedDict):
    """Complete timing summary with breakdown and hierarchy."""
    total_duration_ms: float
    breakdown: dict[str, TimingBreakdown]
    hierarchy: TimingNodeDict | None


class ClaimData(TypedDict):
    """Single claim with its citations and validation status."""
    claim: str
    citations: list[int]
    invalid_citations: list[int]
    validation_result: NotRequired['ClaimSourceValidation']


class ClaimSourceValidation(TypedDict):
    """LLM validation result for claim-source relationship."""
    supported: bool
    confidence: str
    explanation: str


class CitationValidationResult(TypedDict):
    """Complete citation validation output."""
    claims: list[ClaimData]
    extraction_attempts: int
    total_invalid_citations: int
    validation_passed: bool


class TraceData(TypedDict):
    """Complete trace data with sources, tool calls, and reasoning."""
    sources: list[SourceData]
    tool_calls: list[ToolCallRecord]
    reasoning_steps: list[str]
    timing: NotRequired[TimingSummary]


class AgentResult(TypedDict):
    """Complete agent execution result."""
    answer: str
    sources: list[SourceData]
    tool_calls: list[ToolCallRecord]
    reasoning_steps: list[str]
    evaluation: EvaluationResult
    trace: TraceData
    retry_history: NotRequired[list[RetryAttempt]]
    citation_validation: NotRequired[CitationValidationResult]


class ContextConfig(TypedDict):
    """Context management configuration."""
    token_threshold: int
    message_threshold: int
    recent_messages: int
    warning_threshold: int
    max_articles: int
    enable_compression: bool


class MessageDict(TypedDict, total=False):
    """OpenAI message format with optional fields."""
    role: str
    content: str | None
    tool_calls: Any
    tool_call_id: str
    name: str
    internal: bool
    # Extended fields for API responses
    sources: list[SourceData]
    evaluation: EvaluationResult
    reasoning_steps: list[str]
    trace: TraceData
    retry_history: list[RetryAttempt]
    citation_validation: CitationValidationResult


# API Module Types

class SessionData(TypedDict):
    """Internal session storage structure for the API."""
    session_id: str
    title: str
    messages: list[MessageDict]
    result: AgentResult | None
    created_at: str
    last_activity: str
    metadata: dict[str, Any]


class SessionMetadataDict(TypedDict):
    """Session metadata for list responses."""
    session_id: str
    title: str
    message_count: int
    created_at: str
    last_activity: str


class EventData(TypedDict):
    """SSE event structure for streaming responses."""
    type: str
    content: str
    done: bool
