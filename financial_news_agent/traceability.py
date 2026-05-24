"""Traceability tracker for agent operations."""

import logging
from time import perf_counter
from typing import Any, TYPE_CHECKING
from contextlib import contextmanager
from threading import Lock

if TYPE_CHECKING:
    from .types import SourceData, ToolCallRecord, TimingSummary, TraceData, TimingNodeDict

logger = logging.getLogger(__name__)


class TimingNode:
    """Represents a single timing measurement in the hierarchy."""

    def __init__(self, name: str, category: str, parent: 'TimingNode | None' = None) -> None:
        self.name: str = name
        self.category: str = category
        self.parent: TimingNode | None = parent
        self.children: list[TimingNode] = []

        self.start_time: float | None = None
        self.end_time: float | None = None
        self.duration: float | None = None

        self.metadata: dict[str, Any] = {}
        self.error: str | None = None

    def start(self) -> None:
        """Start timing this node."""
        self.start_time = perf_counter()

    def end(self, error: str | None = None) -> None:
        """End timing this node."""
        self.end_time = perf_counter()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        self.error = error

    def add_child(self, child: 'TimingNode') -> None:
        """Add a child timing node."""
        self.children.append(child)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "name": self.name,
            "category": self.category,
            "duration_ms": round(self.duration * 1000, 2) if self.duration else None,
            "metadata": self.metadata,
        }

        if self.error:
            result["error"] = self.error

        if self.children:
            result["children"] = [child.to_dict() for child in self.children]

        return result


class TraceabilityTracker:
    """Tracks sources, tool calls, reasoning steps, and timing for traceability."""

    def __init__(self) -> None:
        self.sources: list[SourceData] = []
        self.tool_calls: list[ToolCallRecord] = []
        self.reasoning_steps: list[str] = []

        # Timing infrastructure
        self._timing_root: TimingNode | None = None
        self._timing_stack: list[TimingNode] = []
        self._lock: Lock = Lock()

    def add_source(self, source_data: SourceData) -> None:
        """Add a source (news article) to the tracker."""
        self.sources.append(source_data)

    def add_tool_call(self, tool_name: str, args: dict[str, Any], result: Any) -> None:
        """Add a tool call record."""
        self.tool_calls.append({
            "tool": tool_name,
            "args": args,
            "result_summary": self._summarize_result(result)
        })

    def add_reasoning(self, step: str) -> None:
        """Add a reasoning step from LLM output."""
        if step and step.strip():
            self.reasoning_steps.append(step.strip())

    def _summarize_result(self, result: Any) -> dict[str, Any]:
        """Summarize tool result for logging."""
        if isinstance(result, list):
            return {"type": "list", "count": len(result)}
        elif isinstance(result, dict):
            return {"type": "dict", "keys": list(result.keys())}
        else:
            return {"type": type(result).__name__}

    @contextmanager
    def time_operation(
        self,
        name: str,
        category: str,
        metadata: dict[str, Any] | None = None
    ):
        """Context manager for timing an operation.

        Args:
            name: Human-readable name (e.g., "LLM Reasoning Call", "NewsAPI Request")
            category: Category for grouping (e.g., "llm_call", "api_call", "tool_call")
            metadata: Optional metadata to attach (e.g., {"model": "gpt-4.5", "tokens": 1500})

        Usage:
            with tracker.time_operation("LLM Reasoning", "llm_call", {"iteration": 1}):
                response = client.chat.completions.create(...)
        """
        with self._lock:
            parent: TimingNode | None = self._timing_stack[-1] if self._timing_stack else None
            node: TimingNode = TimingNode(name, category, parent)

            if metadata:
                node.metadata.update(metadata)

            if parent:
                parent.add_child(node)
            else:
                # This is the root node
                self._timing_root = node

            self._timing_stack.append(node)

        node.start()
        error: str | None = None

        try:
            yield node
        except Exception as e:
            error = str(e)
            raise
        finally:
            node.end(error=error)

            # Log slow operations
            if node.duration:
                if node.category == "llm_call" and node.duration > 5.0:
                    logger.warning(f"Slow LLM call: {node.name} took {node.duration:.2f}s")
                elif node.category == "api_call" and node.duration > 3.0:
                    logger.warning(f"Slow API call: {node.name} took {node.duration:.2f}s")
                elif node.category == "request" and node.duration > 30.0:
                    logger.warning(f"Slow request: {node.name} took {node.duration:.2f}s")

            with self._lock:
                self._timing_stack.pop()

    def get_timing_summary(self) -> TimingSummary:
        """Get timing summary with key metrics.

        Returns:
            Dictionary with total time, breakdown by category, and critical path
        """
        if not self._timing_root:
            return {
                "total_duration_ms": 0,
                "breakdown": {},
                "hierarchy": None
            }

        # Calculate breakdown by category
        breakdown: dict[str, Any] = {}

        def collect_by_category(node: TimingNode) -> None:
            if node.duration:
                category: str = node.category
                if category not in breakdown:
                    breakdown[category] = {
                        "total_ms": 0,
                        "count": 0,
                        "operations": []
                    }
                breakdown[category]["total_ms"] += node.duration * 1000
                breakdown[category]["count"] += 1
                breakdown[category]["operations"].append({
                    "name": node.name,
                    "duration_ms": round(node.duration * 1000, 2),
                    "metadata": node.metadata
                })

            for child in node.children:
                collect_by_category(child)

        collect_by_category(self._timing_root)

        # Round totals
        for category in breakdown:
            breakdown[category]["total_ms"] = round(breakdown[category]["total_ms"], 2)

        return {
            "total_duration_ms": round(self._timing_root.duration * 1000, 2) if self._timing_root.duration else 0,
            "breakdown": breakdown,
            "hierarchy": self._timing_root.to_dict() if self._timing_root else None
        }

    def get_trace(self) -> TraceData:
        """Get complete trace data including timing."""
        trace: TraceData = {
            "sources": self.sources,
            "tool_calls": self.tool_calls,
            "reasoning_steps": self.reasoning_steps
        }

        # Add timing data
        timing_summary: TimingSummary = self.get_timing_summary()
        if timing_summary["total_duration_ms"] > 0:
            trace["timing"] = timing_summary

        return trace
