"""Pydantic models for API request/response validation."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Request model for creating a new session."""
    query: Optional[str] = Field(None, description="Optional initial query to ask immediately")


class CreateSessionResponse(BaseModel):
    """Response model for session creation without initial query."""
    session_id: str
    created_at: str
    message_count: int


class CreateSessionWithResultResponse(BaseModel):
    """Response model for session creation with initial query result."""
    session_id: str
    created_at: str
    message_count: int
    answer: str
    sources: list[dict[str, Any]]
    evaluation: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    reasoning_steps: list[str]
    trace: dict[str, Any]
    retry_history: Optional[list[dict[str, Any]]] = None


class QueryRequest(BaseModel):
    """Request model for querying a session."""
    query: str = Field(..., min_length=1, description="Question to ask the agent")


class QueryResponse(BaseModel):
    """Response model for query results."""
    answer: str
    sources: list[dict[str, Any]]
    evaluation: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    reasoning_steps: list[str]
    trace: dict[str, Any]
    retry_history: Optional[list[dict[str, Any]]] = None


class SessionMetadata(BaseModel):
    """Session metadata response."""
    session_id: str
    created_at: str
    last_activity: str
    message_count: int
    metadata: dict[str, Any]


class SessionMessagesResponse(BaseModel):
    """Response model for session messages."""
    session_id: str
    messages: list[dict[str, Any]]


class SessionListItem(BaseModel):
    """Single session item in list response."""
    session_id: str
    created_at: str
    last_activity: str
    message_count: int


class SessionListResponse(BaseModel):
    """Response model for listing sessions."""
    sessions: list[SessionListItem]
    total: int
    limit: int
    offset: int


class DeleteSessionResponse(BaseModel):
    """Response model for session deletion."""
    deleted: bool
    session_id: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str
    detail: Optional[str] = None
