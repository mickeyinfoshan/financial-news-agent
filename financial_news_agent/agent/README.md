# Agent Module

Core agent orchestration logic, refactored from the original monolithic `agent.py` (738 lines) into focused, single-responsibility modules.

## Architecture

This module implements the main agent loop with LLM orchestration, tool calling, and automatic retry mechanisms. The code is organized following the Single Responsibility Principle (SRP):

```
agent/
├── __init__.py          # Public API exports
├── prompts.py           # System prompt configuration
├── query_rewriter.py    # Multi-turn context resolution
├── shared.py            # Shared business logic
├── sync.py              # Synchronous execution
└── streaming.py         # Async streaming execution
```

## Module Responsibilities

### `__init__.py` - Public API
Exports the public interface used by the rest of the application:
- `create_conversation()` - Initialize empty conversation
- `run_agent()` - Synchronous agent execution
- `run_agent_with_retry()` - Synchronous with automatic retry
- `run_agent_stream()` - Async streaming execution
- `run_agent_with_retry_stream()` - Async streaming with retry

### `prompts.py` - Configuration
Contains system prompts and templates:
- `SYSTEM_PROMPT` - Main agent instructions and behavior
- `RETRY_PROMPT_TEMPLATE` - Template for retry attempts

### `query_rewriter.py` - Context Resolution
Handles multi-turn conversation context:
- `rewrite_query_with_context()` - Resolves pronouns and implicit references using conversation history

### `shared.py` - Business Logic
Shared functions used by both sync and streaming modes:
- `should_force_final_answer()` - Determines when to force final answer
- `process_tool_results()` - Adds articles to traceability tracker
- `compress_and_build_tool_message()` - Compresses tool results and builds messages
- `build_final_result()` - Constructs final AgentResult with evaluation
- `should_retry()` - Decides if retry is needed based on evaluation
- `decide_retry_strategy()` - Chooses FIX vs REDO strategy

### `sync.py` - Synchronous Execution
Synchronous agent implementation:
- `create_conversation()` - Creates empty message list
- `run_agent()` - Main agent loop with tool calling
- `run_agent_with_retry()` - Wrapper with automatic retry/fix

**Key Features:**
- Iterative reasoning with tool calls
- Token usage tracking
- Context window management
- Final answer evaluation

### `streaming.py` - Async Streaming
Asynchronous streaming implementation with real-time events:
- `run_agent_stream()` - Streaming agent loop
- `run_agent_with_retry_stream()` - Streaming with retry
- `_merge_tool_call_delta()` - Merges streaming tool call deltas

**Event Types:**
- `reasoning` - LLM reasoning steps
- `tool_call` - Tool invocation details
- `tool_result` - Tool execution results
- `answer` - Final answer tokens
- `evaluation` - Quality evaluation scores
- `retry` - Retry attempt notifications
- `complete` - Final result with full traceability

## Usage

### Basic Usage

```python
from financial_news_agent.agent import run_agent, create_conversation

# Initialize conversation
messages = create_conversation()

# Run agent
result, updated_messages = run_agent(
    user_query="What's happening with NVIDIA?",
    messages=messages
)

print(result["answer"])
print(f"Sources: {len(result['sources'])}")
```

### With Automatic Retry

```python
from financial_news_agent.agent import run_agent_with_retry, create_conversation

messages = create_conversation()

# Automatically retries if quality score is below threshold
result, updated_messages = run_agent_with_retry(
    user_query="What's happening with NVIDIA?",
    messages=messages
)

# Check if retry was triggered
if result.get("retry_history"):
    print(f"Retried {len(result['retry_history'])} times")
```

### Streaming Mode

```python
from financial_news_agent.agent import run_agent_stream, create_conversation

messages = create_conversation()

async for event in run_agent_stream(
    user_query="What's happening with NVIDIA?",
    messages=messages
):
    event_type = event["type"]
    
    if event_type == "reasoning":
        print(f"Thinking: {event['content']}")
    elif event_type == "tool_call":
        print(f"Calling tool: {event['tool_name']}")
    elif event_type == "answer":
        print(event["content"], end="", flush=True)
    elif event_type == "complete":
        result = event["result"]
        messages = event["messages"]
```

### Multi-turn Conversation

```python
from financial_news_agent.agent import run_agent_with_retry, create_conversation

# Initialize conversation
messages = create_conversation()

# First query
result, messages = run_agent_with_retry("What's happening with NVIDIA?", messages)
print(result["answer"])

# Follow-up query (context is preserved)
result, messages = run_agent_with_retry("What about AMD?", messages)
print(result["answer"])

# Pronouns and references are automatically resolved
result, messages = run_agent_with_retry("Compare them", messages)
print(result["answer"])
```

## Design Decisions

### Why Split by Execution Mode?

The original `agent.py` contained both synchronous and asynchronous implementations with significant code duplication. We considered several approaches:

1. ❌ **Split by feature** (e.g., separate `retry.py`) - Led to duplication of retry logic in both sync and async
2. ✅ **Split by execution mode** - Natural grouping where sync and async each handle their own retry logic

This approach:
- Eliminates duplication by extracting shared business logic to `shared.py`
- Keeps sync and async implementations separate (they have fundamentally different control flow)
- Makes it easy to find all sync-related code in one place, all async code in another

### What Goes in `shared.py`?

Functions that:
- Contain business logic (not just I/O)
- Are used by both sync and async implementations
- Don't depend on sync/async execution details

Examples:
- ✅ `should_retry()` - Pure business logic based on evaluation scores
- ✅ `compress_and_build_tool_message()` - Data transformation
- ❌ OpenAI API calls - Fundamentally different in sync vs async
- ❌ Event emission - Only exists in streaming mode

## Type Safety

All modules use strict type annotations and pass `mypy` type checking with zero errors. Key types:

- `MessageDict` - OpenAI message format
- `AgentResult` - Final result with answer, sources, evaluation
- `ArticleData` - News article structure
- `TraceabilityTracker` - Source tracking

## Testing

The module is covered by 89 unit tests in `tests/`:
- `test_agent.py` - Core agent functionality
- `test_retry.py` - Retry mechanism
- `test_streaming.py` - Streaming events
- `test_context_manager.py` - Context window management

Run tests:
```bash
uv run pytest tests/
```

## Migration Notes

This refactoring maintains **100% backward compatibility**. All public APIs remain unchanged:

**Before:**
```python
from financial_news_agent.agent import run_agent, create_conversation
```

**After (same imports work):**
```python
from financial_news_agent.agent import run_agent, create_conversation
```

The only change is the internal organization - the public interface is identical.

## Performance

- **Code size**: 738 lines → 938 lines (200 line increase due to module documentation and imports)
- **Runtime**: No performance impact - same logic, different organization
- **Type safety**: 0 mypy errors (strict type checking)
- **Test coverage**: 89/89 tests passing

## Future Improvements

Potential enhancements:
- Extract evaluation logic to separate module
- Add more granular streaming events
- Support custom retry strategies
- Add agent state persistence
