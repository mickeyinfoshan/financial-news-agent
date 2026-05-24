"""Tests for FastAPI endpoints."""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from financial_news_agent.api.main import app
from financial_news_agent.api.session_manager import SessionManager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_agent():
    """Mock the agent function to avoid real API calls."""
    mock_result = {
        "answer": "Test answer with citations [1][2].",
        "sources": [
            {
                "title": "Test Article 1",
                "date": "2026-05-23",
                "source": "Test Source",
                "url": "https://example.com/1",
                "summary": "Test summary",
                "api_source": "newsapi"
            },
            {
                "title": "Test Article 2",
                "date": "2026-05-23",
                "source": "Test Source",
                "url": "https://example.com/2",
                "summary": "Test summary",
                "api_source": "finnhub"
            }
        ],
        "evaluation": {
            "accuracy": 8,
            "relevance": 9,
            "coherence": 8,
            "reasonableness": 8,
            "overall": 8.25,
            "feedback": "Good response"
        },
        "tool_calls": [
            {
                "tool": "search_financial_news",
                "args": {"query": "test", "company_name": None, "days_back": 7},
                "result_summary": {"type": "list", "count": 2}
            }
        ],
        "reasoning_steps": ["Step 1", "Step 2"],
        "trace": {"query": "test", "sources": [], "tool_calls": [], "reasoning": []},
        "retry_history": None
    }

    mock_messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Test query"},
        {"role": "assistant", "content": "Test answer"}
    ]

    with patch("financial_news_agent.api.routes.run_agent_with_retry") as mock:
        mock.return_value = (mock_result, mock_messages)
        yield mock


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_create_session_without_query(client):
    """Test creating a session without initial query."""
    response = client.post("/api/v1/session/create", json={})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "created_at" in data
    assert "message_count" in data
    assert data["message_count"] == 1  # Just system prompt


def test_create_session_with_query(client, mock_agent):
    """Test creating a session with initial query."""
    response = client.post(
        "/api/v1/session/create",
        json={"query": "What's happening with Tesla?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "answer" in data
    assert "sources" in data
    assert "evaluation" in data
    assert mock_agent.called


def test_query_session(client, mock_agent):
    """Test querying an existing session."""
    # Create session first
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    # Query the session
    response = client.post(
        f"/api/v1/session/{session_id}/query",
        json={"query": "What about AMD?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "evaluation" in data


def test_query_nonexistent_session(client):
    """Test querying a session that doesn't exist."""
    response = client.post(
        "/api/v1/session/nonexistent-id/query",
        json={"query": "test"}
    )
    assert response.status_code == 404


def test_get_session_metadata(client):
    """Test getting session metadata."""
    # Create session
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    # Get metadata
    response = client.get(f"/api/v1/session/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "created_at" in data
    assert "last_activity" in data
    assert "message_count" in data
    assert "metadata" in data


def test_get_session_messages(client):
    """Test getting session conversation history."""
    # Create session
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    # Get messages
    response = client.get(f"/api/v1/session/{session_id}/messages")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "messages" in data
    assert len(data["messages"]) >= 1  # At least system prompt


def test_list_sessions(client):
    """Test listing sessions."""
    # Create a few sessions
    client.post("/api/v1/session/create", json={})
    client.post("/api/v1/session/create", json={})

    # List sessions
    response = client.get("/api/v1/session/list")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["sessions"]) >= 2


def test_list_sessions_pagination(client):
    """Test session list pagination."""
    # Create sessions
    for _ in range(5):
        client.post("/api/v1/session/create", json={})

    # Test pagination
    response = client.get("/api/v1/session/list?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0


def test_delete_session(client):
    """Test deleting a session."""
    # Create session
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    # Delete session
    response = client.delete(f"/api/v1/session/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True
    assert data["session_id"] == session_id

    # Verify it's gone
    get_response = client.get(f"/api/v1/session/{session_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_session(client):
    """Test deleting a session that doesn't exist."""
    response = client.delete("/api/v1/session/nonexistent-id")
    assert response.status_code == 404


def test_multi_turn_conversation(client, mock_agent):
    """Test multi-turn conversation in a session."""
    # Create session with initial query
    create_response = client.post(
        "/api/v1/session/create",
        json={"query": "What's happening with NVIDIA?"}
    )
    session_id = create_response.json()["session_id"]

    # Follow-up query
    response = client.post(
        f"/api/v1/session/{session_id}/query",
        json={"query": "What about their competitors?"}
    )
    assert response.status_code == 200

    # Check messages accumulated
    messages_response = client.get(f"/api/v1/session/{session_id}/messages")
    messages = messages_response.json()["messages"]
    assert len(messages) >= 3  # System + user + assistant (at least)


def test_messages_contain_embedded_data(client, mock_agent):
    """Test that assistant messages contain embedded sources and evaluation."""
    # Create session with query
    create_response = client.post(
        "/api/v1/session/create",
        json={"query": "What's happening with Tesla?"}
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["session_id"]

    # Get messages
    response = client.get(f"/api/v1/session/{session_id}/messages")
    assert response.status_code == 200
    data = response.json()

    # Find assistant message
    assistant_msg = next(
        (msg for msg in data["messages"] if msg["role"] == "assistant"),
        None
    )

    assert assistant_msg is not None
    assert "sources" in assistant_msg
    assert len(assistant_msg["sources"]) == 2
    assert "evaluation" in assistant_msg
    assert "tool_calls" in assistant_msg
    assert "reasoning_steps" in assistant_msg
    assert "trace" in assistant_msg


def test_multiple_queries_each_have_data(client, mock_agent):
    """Test that each assistant message has its own embedded data."""
    # Create session
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    # First query
    response1 = client.post(
        f"/api/v1/session/{session_id}/query",
        json={"query": "Tesla news"}
    )
    assert response1.status_code == 200

    # Second query
    response2 = client.post(
        f"/api/v1/session/{session_id}/query",
        json={"query": "Apple news"}
    )
    assert response2.status_code == 200

    # Get messages
    response = client.get(f"/api/v1/session/{session_id}/messages")
    data = response.json()

    # Find all assistant messages
    assistant_msgs = [
        msg for msg in data["messages"] if msg["role"] == "assistant"
    ]

    # Should have at least one assistant message with embedded data
    assert len(assistant_msgs) >= 1
    # Each should have embedded data
    for msg in assistant_msgs:
        assert "sources" in msg
        assert "evaluation" in msg


def test_backward_compatibility_no_query_results(client):
    """Test that sessions without query_results still work."""
    # Create session without query
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    # Get session - should work even without embedded data
    response = client.get(f"/api/v1/session/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "messages" not in data  # Metadata endpoint doesn't return messages


def test_empty_query_validation(client):
    """Test that empty queries are rejected."""
    # Create session
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    # Try empty query
    response = client.post(
        f"/api/v1/session/{session_id}/query",
        json={"query": ""}
    )
    assert response.status_code == 422  # Validation error


@pytest.fixture
def mock_agent_stream():
    """Mock the streaming agent function."""
    async def mock_stream_generator(query, messages):
        """Generate mock streaming events."""
        # Agent start
        yield {"event": "agent_start", "data": {"query": query}}

        # Iteration 1
        yield {"event": "iteration_start", "data": {"iteration": 1}}

        # Tool call
        yield {
            "event": "tool_call_start",
            "data": {
                "tool_name": "search_financial_news",
                "arguments": {"query": "test", "company_name": "Tesla"},
                "iteration": 1
            }
        }
        yield {
            "event": "tool_call_complete",
            "data": {
                "tool_name": "search_financial_news",
                "result_summary": "Retrieved 20 articles",
                "article_count": 20,
                "iteration": 1
            }
        }

        # Iteration 2 - final answer
        yield {"event": "iteration_start", "data": {"iteration": 2}}

        # Stream tokens
        tokens = ["Test", " answer", " with", " streaming"]
        for token in tokens:
            yield {"event": "token", "data": {"content": token, "iteration": 2}}

        # Evaluation
        yield {
            "event": "evaluation",
            "data": {
                "overall": 8.5,
                "accuracy": 8,
                "relevance": 9,
                "coherence": 8,
                "reasonableness": 9
            }
        }

        # Done
        yield {
            "event": "done",
            "data": {
                "result": {
                    "answer": "Test answer with streaming",
                    "sources": [{"title": "Test", "url": "http://test.com"}],
                    "evaluation": {"overall": 8.5},
                    "tool_calls": [],
                    "reasoning_steps": [],
                    "trace": {}
                },
                "messages": [
                    {"role": "system", "content": "System"},
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": "Test answer with streaming"}
                ]
            }
        }

    with patch("financial_news_agent.api.routes.run_agent_with_retry_stream") as mock:
        mock.side_effect = mock_stream_generator
        yield mock


def test_query_session_stream(client, mock_agent_stream):
    """Test streaming query endpoint."""
    # Create session
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    # Stream query
    with client.stream(
        "POST",
        f"/api/v1/session/{session_id}/query/stream",
        json={"query": "What's happening with Tesla?"}
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        events = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                event_data = json.loads(line[6:])
                events.append(event_data)

        # Verify event sequence
        assert len(events) > 0
        assert events[0]["event"] == "agent_start"
        assert events[0]["data"]["query"] == "What's happening with Tesla?"

        # Check for key event types
        event_types = [e["event"] for e in events]
        assert "agent_start" in event_types
        assert "iteration_start" in event_types
        assert "tool_call_start" in event_types
        assert "tool_call_complete" in event_types
        assert "token" in event_types
        assert "evaluation" in event_types
        assert "done" in event_types

        # Verify token events
        token_events = [e for e in events if e["event"] == "token"]
        assert len(token_events) == 4
        token_content = "".join([e["data"]["content"] for e in token_events])
        assert token_content == "Test answer with streaming"

        # Verify done event has result
        done_event = [e for e in events if e["event"] == "done"][0]
        assert "result" in done_event["data"]
        assert "messages" in done_event["data"]
        assert done_event["data"]["result"]["answer"] == "Test answer with streaming"


def test_query_session_stream_nonexistent(client):
    """Test streaming query with nonexistent session."""
    response = client.post(
        "/api/v1/session/nonexistent-id/query/stream",
        json={"query": "test"}
    )
    assert response.status_code == 404


def test_query_session_stream_with_retry(client):
    """Test streaming query with retry event."""
    async def mock_stream_with_retry(query, messages):
        """Generate mock streaming events with retry."""
        yield {"event": "agent_start", "data": {"query": query}}
        yield {"event": "iteration_start", "data": {"iteration": 1}}

        # First attempt - low score
        yield {"event": "token", "data": {"content": "Bad answer", "iteration": 1}}
        yield {
            "event": "evaluation",
            "data": {"overall": 4.0, "accuracy": 4, "relevance": 4, "coherence": 4, "reasonableness": 4}
        }
        yield {
            "event": "done",
            "data": {
                "result": {"answer": "Bad answer", "sources": [], "evaluation": {"overall": 4.0}},
                "messages": []
            }
        }

        # Retry event
        yield {
            "event": "retry",
            "data": {
                "attempt": 2,
                "previous_score": 4.0,
                "strategy": "fix",
                "reason": "Quality below threshold (overall: 4.0)"
            }
        }

        # Second attempt - better
        yield {"event": "iteration_start", "data": {"iteration": 2}}
        yield {"event": "token", "data": {"content": "Better answer", "iteration": 2}}
        yield {
            "event": "evaluation",
            "data": {"overall": 8.0, "accuracy": 8, "relevance": 8, "coherence": 8, "reasonableness": 8}
        }
        yield {
            "event": "done",
            "data": {
                "result": {
                    "answer": "Better answer",
                    "sources": [],
                    "evaluation": {"overall": 8.0},
                    "retry_history": [{"attempt": 1, "previous_score": 4.0, "strategy": "fix"}]
                },
                "messages": []
            }
        }

    # Create session
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    with patch("financial_news_agent.api.routes.run_agent_with_retry_stream") as mock:
        mock.return_value = mock_stream_with_retry("test", [])

        with client.stream(
            "POST",
            f"/api/v1/session/{session_id}/query/stream",
            json={"query": "test"}
        ) as response:
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

            # Verify retry event exists
            event_types = [e["event"] for e in events]
            assert "retry" in event_types

            retry_event = [e for e in events if e["event"] == "retry"][0]
            assert retry_event["data"]["attempt"] == 2
            assert retry_event["data"]["strategy"] == "fix"
            assert retry_event["data"]["previous_score"] == 4.0


def test_query_session_stream_error_handling(client):
    """Test streaming query error handling."""
    async def mock_stream_with_error(query, messages):
        """Generate mock streaming events with error."""
        yield {"event": "agent_start", "data": {"query": query}}
        yield {"event": "iteration_start", "data": {"iteration": 1}}

        # Error event
        yield {
            "event": "error",
            "data": {
                "message": "Test error occurred",
                "iteration": 1
            }
        }

        yield {
            "event": "done",
            "data": {
                "result": {"answer": "Error occurred: Test error occurred", "sources": [], "evaluation": {"overall": 1.0}},
                "messages": []
            }
        }

    # Create session
    create_response = client.post("/api/v1/session/create", json={})
    session_id = create_response.json()["session_id"]

    with patch("financial_news_agent.api.routes.run_agent_with_retry_stream") as mock:
        mock.return_value = mock_stream_with_error("test", [])

        with client.stream(
            "POST",
            f"/api/v1/session/{session_id}/query/stream",
            json={"query": "test"}
        ) as response:
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

            # Verify error event exists
            event_types = [e["event"] for e in events]
            assert "error" in event_types

            error_event = [e for e in events if e["event"] == "error"][0]
            assert "Test error occurred" in error_event["data"]["message"]
