"""In-memory session management."""

import uuid
from datetime import datetime, UTC
from typing import Optional, Any


class SessionManager:
    """Manages agent conversation sessions in memory."""

    def __init__(self):
        """Initialize session storage."""
        self._sessions: dict[str, dict[str, Any]] = {}

    def _generate_title(self, messages: list[dict[str, Any]]) -> str:
        """Generate session title from first user message.

        Args:
            messages: List of conversation messages

        Returns:
            Title string (first user message truncated to 60 chars, or "New conversation")
        """
        for msg in messages:
            if msg.get("role") == "user" and msg.get("content"):
                content = msg["content"].strip()
                if content:
                    return content[:60] + "..." if len(content) > 60 else content
        return "New conversation"

    def create_session(self, messages: list[dict[str, Any]]) -> str:
        """Create a new session with initialized conversation.

        Args:
            messages: Initial messages list (typically just system prompt)

        Returns:
            session_id: UUID string for the new session
        """
        session_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        self._sessions[session_id] = {
            "session_id": session_id,
            "messages": messages,
            "created_at": now,
            "last_activity": now,
            "title": "New conversation",
            "metadata": {
                "total_queries": 0,
                "total_tokens": 0,
                "last_evaluation_score": 0.0
            }
        }

        return session_id

    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session data dict or None if not found
        """
        session = self._sessions.get(session_id)
        if session and "title" not in session:
            # Lazy migration: add title to old sessions
            session["title"] = self._generate_title(session["messages"])
        return session

    def update_session(
        self,
        session_id: str,
        messages: list[dict[str, Any]],
        result: Optional[dict[str, Any]] = None
    ) -> bool:
        """Update session with new messages and optional result metadata.

        If result is provided, embeds it into the last assistant message.

        Args:
            session_id: Session UUID
            messages: Updated messages list
            result: Optional agent result dict for metadata extraction

        Returns:
            True if updated, False if session not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Update title if this is the first user message
        if session["metadata"]["total_queries"] == 0:
            session["title"] = self._generate_title(messages)

        # If result provided, embed it into the last assistant message
        if result and messages:
            # Find the last assistant message
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].get("role") == "assistant":
                    # Embed all result data directly into the message
                    messages[i]["sources"] = result.get("sources", [])
                    messages[i]["evaluation"] = result.get("evaluation")
                    messages[i]["tool_calls"] = result.get("tool_calls", [])
                    messages[i]["reasoning_steps"] = result.get("reasoning_steps", [])
                    messages[i]["trace"] = result.get("trace")
                    messages[i]["retry_history"] = result.get("retry_history")
                    break

        session["messages"] = messages
        session["last_activity"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        session["metadata"]["total_queries"] += 1

        if result:
            # Extract evaluation score if available
            if "evaluation" in result and "overall" in result["evaluation"]:
                session["metadata"]["last_evaluation_score"] = result["evaluation"]["overall"]

        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session UUID

        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self, limit: int = 20, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
        """List all sessions with pagination.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            Tuple of (session_list, total_count)
        """
        all_sessions = list(self._sessions.values())
        total = len(all_sessions)

        # Sort by last_activity descending (most recent first)
        all_sessions.sort(key=lambda s: s["last_activity"], reverse=True)

        # Apply pagination
        paginated = all_sessions[offset:offset + limit]

        # Return simplified metadata
        session_list = [
            {
                "session_id": s["session_id"],
                "created_at": s["created_at"],
                "last_activity": s["last_activity"],
                "message_count": len(s["messages"]),
                "title": s.get("title", self._generate_title(s["messages"]))
            }
            for s in paginated
        ]

        return session_list, total


# Global session manager instance
session_manager = SessionManager()
