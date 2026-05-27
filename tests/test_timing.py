"""Unit tests for timing instrumentation."""

import time
import pytest
from threading import Thread
from financial_news_agent.traceability import TraceabilityTracker, TimingNode


class TestTimingNode:
    """Test TimingNode class."""

    def test_timing_node_creation(self):
        """Test creating a timing node."""
        node = TimingNode("Test Operation", "test_category")
        assert node.name == "Test Operation"
        assert node.category == "test_category"
        assert node.parent is None
        assert node.children == []
        assert node.start_time is None
        assert node.end_time is None
        assert node.duration is None
        assert node.metadata == {}
        assert node.error is None

    def test_timing_node_with_parent(self):
        """Test creating a child timing node."""
        parent = TimingNode("Parent", "parent_category")
        child = TimingNode("Child", "child_category", parent)
        assert child.parent == parent
        assert child.name == "Child"

    def test_timing_node_start_end(self):
        """Test starting and ending a timing node."""
        node = TimingNode("Test", "test")
        node.start()
        assert node.start_time is not None

        time.sleep(0.01)  # Sleep 10ms
        node.end()
        assert node.end_time is not None
        assert node.duration is not None
        assert node.duration >= 0.01  # At least 10ms

    def test_timing_node_with_error(self):
        """Test timing node with error."""
        node = TimingNode("Test", "test")
        node.start()
        node.end(error="Test error")
        assert node.error == "Test error"
        assert node.duration is not None

    def test_timing_node_add_child(self):
        """Test adding children to timing node."""
        parent = TimingNode("Parent", "parent")
        child1 = TimingNode("Child1", "child")
        child2 = TimingNode("Child2", "child")

        parent.add_child(child1)
        parent.add_child(child2)

        assert len(parent.children) == 2
        assert parent.children[0] == child1
        assert parent.children[1] == child2

    def test_timing_node_to_dict(self):
        """Test converting timing node to dictionary."""
        parent = TimingNode("Parent", "parent")
        parent.metadata["key"] = "value"
        parent.start()
        time.sleep(0.01)
        parent.end()

        child = TimingNode("Child", "child")
        child.start()
        time.sleep(0.005)
        child.end()
        parent.add_child(child)

        result = parent.to_dict()
        assert result["name"] == "Parent"
        assert result["category"] == "parent"
        assert result["duration_ms"] >= 10
        assert result["metadata"] == {"key": "value"}
        assert len(result["children"]) == 1
        assert result["children"][0]["name"] == "Child"


class TestTraceabilityTracker:
    """Test TraceabilityTracker timing functionality."""

    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = TraceabilityTracker()
        assert tracker.sources == []
        assert tracker.tool_calls == []
        assert tracker.reasoning_steps == []
        assert tracker._timing_root is None
        assert tracker._timing_stack == []

    def test_time_operation_context_manager(self):
        """Test time_operation context manager."""
        tracker = TraceabilityTracker()

        with tracker.time_operation("Test Op", "test", {"key": "value"}) as node:
            time.sleep(0.01)
            assert node.name == "Test Op"
            assert node.category == "test"
            assert node.metadata["key"] == "value"

        # After context exit, timing should be recorded
        assert tracker._timing_root is not None
        assert tracker._timing_root.duration >= 0.01

    def test_nested_timing_operations(self):
        """Test nested timing operations."""
        tracker = TraceabilityTracker()

        with tracker.time_operation("Parent", "parent"):
            time.sleep(0.01)
            with tracker.time_operation("Child1", "child"):
                time.sleep(0.005)
            with tracker.time_operation("Child2", "child"):
                time.sleep(0.005)

        # Check hierarchy
        assert tracker._timing_root.name == "Parent"
        assert len(tracker._timing_root.children) == 2
        assert tracker._timing_root.children[0].name == "Child1"
        assert tracker._timing_root.children[1].name == "Child2"

        # Parent duration should be >= sum of children
        parent_duration = tracker._timing_root.duration
        child1_duration = tracker._timing_root.children[0].duration
        child2_duration = tracker._timing_root.children[1].duration
        assert parent_duration >= child1_duration + child2_duration

    def test_timing_with_exception(self):
        """Test timing continues even when exception is raised."""
        tracker = TraceabilityTracker()

        with pytest.raises(ValueError):
            with tracker.time_operation("Test", "test") as node:
                time.sleep(0.01)
                raise ValueError("Test error")

        # Timing should still be recorded
        assert tracker._timing_root is not None
        assert tracker._timing_root.duration >= 0.01
        assert tracker._timing_root.error == "Test error"

    def test_get_timing_summary_empty(self):
        """Test getting timing summary with no operations."""
        tracker = TraceabilityTracker()
        summary = tracker.get_timing_summary()

        assert summary["total_duration_ms"] == 0
        assert summary["breakdown"] == {}
        assert summary["hierarchy"] is None

    def test_get_timing_summary_with_operations(self):
        """Test getting timing summary with operations."""
        tracker = TraceabilityTracker()

        # Nest operations under a parent to test breakdown
        with tracker.time_operation("Parent", "parent"):
            with tracker.time_operation("LLM Call 1", "llm_call", {"iteration": 1}):
                time.sleep(0.02)

            with tracker.time_operation("LLM Call 2", "llm_call", {"iteration": 2}):
                time.sleep(0.01)

            with tracker.time_operation("API Call", "api_call"):
                time.sleep(0.015)

        summary = tracker.get_timing_summary()

        # Check total duration (parent duration)
        assert summary["total_duration_ms"] >= 45  # At least 45ms total

        # Check breakdown by category
        assert "llm_call" in summary["breakdown"]
        assert "api_call" in summary["breakdown"]
        assert "parent" in summary["breakdown"]

        llm_breakdown = summary["breakdown"]["llm_call"]
        assert llm_breakdown["count"] == 2
        assert llm_breakdown["total_ms"] >= 30  # At least 30ms for LLM calls

        api_breakdown = summary["breakdown"]["api_call"]
        assert api_breakdown["count"] == 1
        assert api_breakdown["total_ms"] >= 15  # At least 15ms for API call

        # Check operations list
        assert len(llm_breakdown["operations"]) == 2
        assert llm_breakdown["operations"][0]["name"] == "LLM Call 1"
        assert llm_breakdown["operations"][0]["metadata"]["iteration"] == 1

    def test_get_trace_includes_timing(self):
        """Test that get_trace includes timing data."""
        tracker = TraceabilityTracker()

        # Add some traceability data
        tracker.add_source({"title": "Test Article", "url": "http://example.com"})
        tracker.add_tool_call("test_tool", {"arg": "value"}, [])
        tracker.add_reasoning("Test reasoning")

        # Add timing data
        with tracker.time_operation("Test", "test"):
            time.sleep(0.01)

        trace = tracker.get_trace()

        # Check traceability data
        assert len(trace["sources"]) == 1
        assert len(trace["tool_calls"]) == 1
        assert len(trace["reasoning_steps"]) == 1

        # Check timing data is included
        assert "timing" in trace
        assert trace["timing"]["total_duration_ms"] >= 10

    def test_parallel_timing_thread_safety(self):
        """Test thread safety of timing with parallel operations.

        Note: When threads create timing operations, they check the timing stack
        which is shared across threads. The lock ensures thread-safe access.
        However, the timing stack is thread-local in behavior - when a thread
        starts a timing operation, it sees the current stack state.
        """
        tracker = TraceabilityTracker()
        results = []
        errors = []

        def worker(name, sleep_time):
            try:
                # Each worker creates its own timing node
                with tracker.time_operation(name, "worker"):
                    time.sleep(sleep_time)
                    results.append(name)
            except Exception as e:
                errors.append((name, str(e)))

        with tracker.time_operation("Parent", "parent"):
            threads = [
                Thread(target=worker, args=("Worker1", 0.01)),
                Thread(target=worker, args=("Worker2", 0.01)),
                Thread(target=worker, args=("Worker3", 0.01))
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

        # Check that all workers completed without errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3

        # Check that parent was recorded
        assert tracker._timing_root.name == "Parent"

        # Workers should be children of parent (they see parent on stack when they start)
        # The lock ensures thread-safe addition of children
        assert len(tracker._timing_root.children) >= 1  # At least one worker recorded

        # Check that timing data exists for recorded children
        for child in tracker._timing_root.children:
            assert child.duration is not None
            assert child.duration >= 0.01

    def test_timing_metadata_updates(self):
        """Test updating metadata during timing operation."""
        tracker = TraceabilityTracker()

        with tracker.time_operation("Test", "test", {"initial": "value"}) as node:
            time.sleep(0.01)
            # Update metadata during operation
            node.metadata["tokens"] = 1234
            node.metadata["model"] = "gpt-5.5"

        # Check metadata was preserved
        assert tracker._timing_root.metadata["initial"] == "value"
        assert tracker._timing_root.metadata["tokens"] == 1234
        assert tracker._timing_root.metadata["model"] == "gpt-5.5"

    def test_multiple_root_operations(self):
        """Test multiple separate timing operations (not nested)."""
        tracker = TraceabilityTracker()

        # First operation
        with tracker.time_operation("Op1", "test"):
            time.sleep(0.01)

        # Second operation (should replace root)
        with tracker.time_operation("Op2", "test"):
            time.sleep(0.01)

        # Only the last root operation should be tracked
        assert tracker._timing_root.name == "Op2"

    def test_timing_summary_hierarchy(self):
        """Test timing summary includes full hierarchy."""
        tracker = TraceabilityTracker()

        with tracker.time_operation("Request", "request"):
            with tracker.time_operation("Iteration 1", "iteration"):
                with tracker.time_operation("LLM Call", "llm_call"):
                    time.sleep(0.01)
                with tracker.time_operation("Tool Call", "tool_call"):
                    time.sleep(0.01)

        summary = tracker.get_timing_summary()

        # Check hierarchy structure
        hierarchy = summary["hierarchy"]
        assert hierarchy["name"] == "Request"
        assert hierarchy["category"] == "request"
        assert len(hierarchy["children"]) == 1

        iteration = hierarchy["children"][0]
        assert iteration["name"] == "Iteration 1"
        assert len(iteration["children"]) == 2

        llm_call = iteration["children"][0]
        tool_call = iteration["children"][1]
        assert llm_call["name"] == "LLM Call"
        assert tool_call["name"] == "Tool Call"
