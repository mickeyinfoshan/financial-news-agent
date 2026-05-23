"""Tests for FastAPI endpoints."""

import pytest
from unittest.mock import patch, MagicMock
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
