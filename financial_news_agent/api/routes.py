"""API route handlers."""

from __future__ import annotations

import asyncio
import json
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from .models import (
    CreateSessionRequest,
    CreateSessionResponse,
    CreateSessionWithResultResponse,
    QueryRequest,
    QueryResponse,
    SessionMetadata,
    SessionMessagesResponse,
    SessionListResponse,
    SessionListItem,
    DeleteSessionResponse,
    HealthResponse,
)
from .session_manager import session_manager
from ..agent import run_agent_with_retry, run_agent_with_retry_stream, create_conversation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.post("/session/create", response_model=CreateSessionResponse | CreateSessionWithResultResponse)
async def create_session(request: CreateSessionRequest) -> CreateSessionResponse | CreateSessionWithResultResponse:
    """Create a new session with optional initial query.

    If query is provided, runs the agent immediately and returns full result.
    If query is not provided, returns just session metadata.
    """
    try:
        # Initialize conversation with system prompt
        messages = create_conversation()
        session_id = session_manager.create_session(messages)
        session = session_manager.get_session(session_id)

        if not session:
            raise HTTPException(status_code=500, detail="Failed to create session")

        # If no query provided, return session metadata only
        if not request.query:
            return CreateSessionResponse(
                session_id=session_id,
                created_at=session["created_at"],
                message_count=len(messages)
            )

        # Run agent with initial query
        result, updated_messages = await asyncio.to_thread(
            run_agent_with_retry,
            request.query,
            messages
        )

        # Update session with result
        session_manager.update_session(session_id, updated_messages, result)

        # Return full result with session_id (cast TypedDict to dict for Pydantic)
        return CreateSessionWithResultResponse(
            session_id=session_id,
            created_at=session["created_at"],
            message_count=len(updated_messages),
            answer=result["answer"],
            sources=result["sources"],  # type: ignore[arg-type]
            evaluation=result["evaluation"],  # type: ignore[arg-type]
            tool_calls=result["tool_calls"],  # type: ignore[arg-type]
            reasoning_steps=result["reasoning_steps"],
            trace=result["trace"],  # type: ignore[arg-type]
            retry_history=result.get("retry_history")  # type: ignore[arg-type]
        )

    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/session/{session_id}/query", response_model=QueryResponse)
async def query_session(session_id: str, request: QueryRequest) -> QueryResponse:
    """Ask a question in an existing session."""
    try:
        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Run agent with query
        result, updated_messages = await asyncio.to_thread(
            run_agent_with_retry,
            request.query,
            session["messages"]
        )

        # Update session
        session_manager.update_session(session_id, updated_messages, result)

        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],  # type: ignore[arg-type]
            evaluation=result["evaluation"],  # type: ignore[arg-type]
            tool_calls=result["tool_calls"],  # type: ignore[arg-type]
            reasoning_steps=result["reasoning_steps"],
            trace=result["trace"],  # type: ignore[arg-type]
            retry_history=result.get("retry_history")  # type: ignore[arg-type]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@router.post("/session/{session_id}/query/stream")
async def query_session_stream(session_id: str, request: QueryRequest) -> StreamingResponse:
    """
    Stream agent response in real-time using Server-Sent Events.

    Returns events as they occur: tool calls, reasoning, tokens, evaluation.
    """
    try:
        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        async def event_generator() -> AsyncGenerator[str, None]:
            """Generate SSE events."""
            try:
                result = None
                updated_messages = None

                # Stream events from agent
                async for event in run_agent_with_retry_stream(
                    request.query,
                    session["messages"]
                ):
                    # Format as SSE
                    event_data = json.dumps(event, ensure_ascii=False)
                    yield f"data: {event_data}\n\n"

                    # Capture final result
                    if event["event"] == "done":
                        result = event["data"]["result"]
                        updated_messages = event["data"]["messages"]

                # Update session
                if result and updated_messages:
                    session_manager.update_session(session_id, updated_messages, result)

            except Exception as e:
                logger.error(f"Error in stream: {e}", exc_info=True)
                error_event = {
                    "event": "error",
                    "data": {"message": str(e)}
                }
                yield f"data: {json.dumps(error_event)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/list", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip")
) -> SessionListResponse:
    """List all active sessions with pagination."""
    sessions, total = session_manager.list_sessions(limit=limit, offset=offset)

    return SessionListResponse(
        sessions=[SessionListItem(**s) for s in sessions],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/session/{session_id}", response_model=SessionMetadata)
async def get_session(session_id: str) -> SessionMetadata:
    """Get session metadata."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return SessionMetadata(
        session_id=session["session_id"],
        created_at=session["created_at"],
        last_activity=session["last_activity"],
        message_count=len(session["messages"]),
        metadata=session["metadata"]
    )


@router.get("/session/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages(session_id: str) -> SessionMessagesResponse:
    """Get full conversation history for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return SessionMessagesResponse(
        session_id=session["session_id"],
        messages=session["messages"]  # type: ignore[arg-type]
    )


@router.delete("/session/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str) -> DeleteSessionResponse:
    """Delete a session and its conversation history."""
    deleted = session_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return DeleteSessionResponse(deleted=True, session_id=session_id)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")
