# Architecture

This document provides a detailed overview of the financial news agent system architecture.

## System Overview

The system uses a simple agentic loop with OpenAI function calling to search and analyze financial news from multiple sources. The architecture prioritizes traceability, quality validation, and extensibility.

## Core Components

### 1. Agent Module (`agent/`)

Orchestrates LLM calls with OpenAI function calling.

**Key Features:**
- **Synchronous Mode** (`sync.py`): Standard agent execution
- **Streaming Mode** (`streaming.py`): Real-time streaming responses for API
- Iterative loop (max 10 iterations)
- Calls news search tool as needed
- Tracks all tool calls and reasoning steps
- Wrapped by `run_agent_with_retry()` for automatic quality improvement
- Query rewriting (`query_rewriter.py`) for better search results
- Shared utilities (`shared.py`) for common agent operations

### 2. News Search (`news_tool.py`)

Multi-source news retrieval with extensible provider system.

**Key Features:**
- **Provider Abstraction**: Protocol-based design for easy addition of new sources
- **NewsAPI**: General financial news
- **Finnhub**: Company-specific news with ticker lookup
- **Marketaux**: Additional financial news source
- Parallel API calls with deduplication across all sources
- Dynamic ticker resolution via Finnhub Symbol Search API
- Providers automatically activated based on API key availability

**See Also:** [Adding News Sources Guide](guides/adding-news-sources.md)

### 3. REST API (`api/`)

FastAPI-based web service for frontend integration.

**Key Features:**
- Session management with conversation history
- Synchronous and streaming endpoints
- CORS support for frontend integration
- Request timeout and error handling

**See Also:** [API Reference](api-reference.md)

### 4. Type System (`types.py`)

Comprehensive type definitions for all data structures.

**Key Features:**
- TypedDict definitions for all data structures
- Zero runtime overhead with full type safety
- Covers articles, sources, evaluations, traces, sessions, and API models

### 5. Configuration (`config.py`)

Centralized configuration management.

**Key Features:**
- Environment variable loading
- Type-safe configuration access
- Default values and validation

**See Also:** [Configuration Reference](configuration.md)

### 6. Traceability (`traceability.py`)

Audit trail tracking for all agent operations.

**Key Features:**
- Records all sources, tool calls, and reasoning steps
- Maintains query → sources → reasoning → response chain
- Enables full transparency of agent decision-making

### 7. Self-Evaluation (`evaluator.py`)

Quality validation for agent responses.

**Key Features:**
- Evaluates accuracy, relevance, coherence, and impact analysis
- Produces scores (1-10 scale) for each dimension
- Triggers retry mechanism when scores are below threshold
- Uses shared citation extraction utility from `utils.py`

### 8. Citation Validation (`citation_validator.py`)

Ensures citation accuracy and prevents hallucinations.

**Key Features:**
- Extracts claims and their citations from agent responses
- Validates that citations actually support the claims
- LLM-based validation with confidence scoring
- Prevents hallucinated or mismatched citations

### 9. Retry/Fix Mechanism (`retry_manager.py`)

Automatic quality improvement for low-quality responses.

**Key Features:**
- Monitors evaluation scores and triggers retries when quality is low
- **FIX strategy**: Improves existing answer using same sources (for coherence/reasoning issues)
- **REDO strategy**: Starts fresh with new search (for accuracy/relevance issues)
- Configurable thresholds and retry limits to control cost

**Trigger Conditions:**
- Overall score < 6.0 OR Accuracy < 5.0

**Strategy Selection:**
- **FIX**: Used when sources are correct but narrative needs improvement
  - Preserves existing sources
  - Improves storyline and reasoning
  - Lower token cost (~1.3x)
- **REDO**: Used when fundamental issues exist (low accuracy/relevance, no sources)
  - Searches for news again
  - Starts fresh with better queries
  - Higher token cost (~2.0x)

**See Also:** [Retry Configuration](configuration.md#retry-fix-mechanism)

### 10. Context Management (`context_manager.py`)

Token optimization for long conversations.

**Key Features:**
- Compresses tool results to reduce token usage
- Summarizes old conversation history when approaching limits
- Tracks token usage from OpenAI API responses
- Configurable thresholds and compression strategies

**See Also:** [Context Configuration](configuration.md#context-window-management)

### 11. Utilities (`utils.py`)

Shared helper functions used across modules.

**Key Features:**
- `extract_citations()`: Extracts citation numbers from text
- Eliminates code duplication across modules

## Data Flow

```
User Query
    ↓
Agent Loop (agent/sync.py or agent/streaming.py)
    ↓
Query Rewriter (agent/query_rewriter.py)
    ↓
News Search (news_tool.py)
    ↓
Parallel Provider Calls (news_sources/)
    ├→ NewsAPI
    ├→ Finnhub (with ticker lookup)
    └→ Marketaux
    ↓
Deduplication & Aggregation
    ↓
Agent Analysis (with traceability tracking)
    ↓
Self-Evaluation (evaluator.py)
    ↓
Citation Validation (citation_validator.py)
    ↓
Quality Check (retry_manager.py)
    ├→ Pass: Return response
    └→ Fail: Retry with FIX or REDO strategy
```

## Implementation Priorities

1. **Transparency First**: Every claim must link back to specific sources
2. **Audit Trail**: Log all decision points and data transformations
3. **Quality Gates**: Self-evaluation triggers automatic retry/fix for low-quality responses
4. **Multi-Source Coverage**: Combine multiple news sources for comprehensive coverage
5. **Automatic Quality Improvement**: Retry mechanism ensures responses meet quality thresholds
6. **Extensible Architecture**: Protocol-based provider system makes adding new news sources trivial

## Related Documentation

- [Configuration Reference](configuration.md) - Environment variables and settings
- [Adding News Sources](guides/adding-news-sources.md) - How to add new providers
- [API Reference](api-reference.md) - REST API documentation
- [Implementation Details](implementation.md) - Code-level implementation details
