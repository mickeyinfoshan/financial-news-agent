"""Traceability tracker for agent operations."""

from typing import Any


class TraceabilityTracker:
    """Tracks sources, tool calls, and reasoning steps for traceability."""

    def __init__(self):
        self.sources = []
        self.tool_calls = []
        self.reasoning_steps = []

    def add_source(self, source_data: dict):
        """Add a source (news article) to the tracker."""
        self.sources.append(source_data)

    def add_tool_call(self, tool_name: str, args: dict, result: Any):
        """Add a tool call record."""
        self.tool_calls.append({
            "tool": tool_name,
            "args": args,
            "result_summary": self._summarize_result(result)
        })

    def add_reasoning(self, step: str):
        """Add a reasoning step from LLM output."""
        if step and step.strip():
            self.reasoning_steps.append(step.strip())

    def _summarize_result(self, result: Any) -> dict:
        """Summarize tool result for logging."""
        if isinstance(result, list):
            return {"type": "list", "count": len(result)}
        elif isinstance(result, dict):
            return {"type": "dict", "keys": list(result.keys())}
        else:
            return {"type": type(result).__name__}

    def get_trace(self) -> dict:
        """Get complete trace data."""
        return {
            "sources": self.sources,
            "tool_calls": self.tool_calls,
            "reasoning_steps": self.reasoning_steps
        }
