# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI agent system for financial news analysis. The agent searches recent financial news about stocks and industries, then provides analysis with storylines and future impact assessments based on historical news, API data, and knowledge sources.

## Core Requirements

**Traceability**: All source data and reasoning paths must be highly traceable. When the agent makes claims or suggestions, it must be clear which news articles, data points, or knowledge sources informed that conclusion.

**Self-Evaluation**: Agent responses must include self-evaluation to ensure quality. The evaluation criteria should assess:
- Accuracy of information retrieval
- Relevance of sources to the query
- Coherence of the storyline
- Reasonableness of future impact analysis

## Technology Stack

- **Language**: Python 3.11+
- **Package Manager**: `uv` (NEVER use `pip`)
- **Agent Framework**: Custom agent loop with OpenAI function calling
- **LLM**: OpenAI API (GPT-4.5 or compatible models)
- **News Sources**: NewsAPI, Finnhub, and Marketaux for financial news (extensible provider system)

## Development Setup

```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package>

# Add dev dependency
uv add --dev <package>

# Run the agent
uv run python -m financial_news_agent

# Run tests
uv run pytest
```

## Project Structure

```
financial_news_agent/     # Main source code
├── __init__.py
├── __main__.py           # Entry point
├── agent/                # Agent module (refactored for SRP)
│   ├── __init__.py       # Exports agent functions
│   ├── sync.py           # Synchronous agent implementation
│   ├── streaming.py      # Streaming agent implementation
│   ├── query_rewriter.py # Query rewriting logic
│   ├── prompts.py        # System prompts
│   ├── shared.py         # Shared agent utilities
│   └── README.md         # Agent module documentation
├── api/                  # REST API module
│   ├── __init__.py
│   ├── main.py           # FastAPI app factory
│   ├── routes.py         # API endpoints
│   ├── models.py         # Pydantic models
│   └── session_manager.py # Session management
├── api_server.py         # API server entry point
├── news_tool.py          # News search orchestration
├── news_sources/         # News provider implementations
│   ├── __init__.py       # Exports all providers
│   ├── base.py           # NewsSourceProvider Protocol
│   ├── newsapi.py        # NewsAPIProvider implementation
│   ├── finnhub.py        # FinnhubProvider implementation
│   └── marketaux.py      # MarketauxProvider implementation
├── types.py              # TypedDict definitions for all data structures
├── config.py             # Configuration management
├── traceability.py       # Traceability tracking
├── evaluator.py          # Self-evaluation logic
├── citation_validator.py # Citation validation logic
├── retry_manager.py      # Retry/fix mechanism for low-quality responses
├── context_manager.py    # Context window management
├── utils.py              # Shared utility functions (citation extraction)
└── README.md             # Package documentation

tests/                    # Formal unit and integration tests
.dev_process/             # Temporary validation scripts (not committed long-term)
.dev_docs/
├── plan/                 # Implementation plans and design docs
└── summary/              # Summaries and retrospectives
```

**File Organization Rules**:
- Planning docs → `.dev_docs/plan/`
- Summary docs → `.dev_docs/summary/`
- Temporary test scripts → `.dev_process/`
- Formal tests → `tests/`

## Architecture

The system uses a simple agentic loop with these components:

1. **Agent Module** (`agent/`): Orchestrates LLM calls with OpenAI function calling
   - **Synchronous Mode** (`sync.py`): Standard agent execution
   - **Streaming Mode** (`streaming.py`): Real-time streaming responses for API
   - Iterative loop (max 10 iterations)
   - Calls news search tool as needed
   - Tracks all tool calls and reasoning steps
   - Wrapped by `run_agent_with_retry()` for automatic quality improvement
   - Query rewriting (`query_rewriter.py`) for better search results
   - Shared utilities (`shared.py`) for common agent operations

2. **News Search** (`news_tool.py`): Multi-source news retrieval with extensible provider system
   - **Provider Abstraction**: Protocol-based design for easy addition of new sources
   - **NewsAPI**: General financial news
   - **Finnhub**: Company-specific news with ticker lookup
   - **Marketaux**: Additional financial news source
   - Parallel API calls with deduplication across all sources
   - Dynamic ticker resolution via Finnhub Symbol Search API
   - Providers automatically activated based on API key availability

3. **REST API** (`api/`): FastAPI-based web service
   - Session management with conversation history
   - Synchronous and streaming endpoints
   - CORS support for frontend integration
   - Request timeout and error handling

4. **Type System** (`types.py`): Comprehensive type definitions
   - TypedDict definitions for all data structures
   - Zero runtime overhead with full type safety
   - Covers articles, sources, evaluations, traces, sessions, and API models

5. **Configuration** (`config.py`): Centralized configuration management
   - Environment variable loading
   - Type-safe configuration access
   - Default values and validation

6. **Traceability** (`traceability.py`): Audit trail tracking
   - Records all sources, tool calls, and reasoning steps
   - Maintains query → sources → reasoning → response chain

7. **Self-Evaluation** (`evaluator.py`): Quality validation
   - Evaluates accuracy, relevance, coherence, and impact analysis
   - Produces scores (1-10 scale) for each dimension
   - Triggers retry mechanism when scores are below threshold
   - Uses shared citation extraction utility from `utils.py`

8. **Citation Validation** (`citation_validator.py`): Ensures citation accuracy
   - Extracts claims and their citations from agent responses
   - Validates that citations actually support the claims
   - LLM-based validation with confidence scoring
   - Prevents hallucinated or mismatched citations

9. **Retry/Fix Mechanism** (`retry_manager.py`): Automatic quality improvement
   - Monitors evaluation scores and triggers retries when quality is low
   - **FIX strategy**: Improves existing answer using same sources (for coherence/reasoning issues)
   - **REDO strategy**: Starts fresh with new search (for accuracy/relevance issues)
   - Configurable thresholds and retry limits to control cost

10. **Context Management** (`context_manager.py`): Token optimization
   - Compresses tool results to reduce token usage
   - Summarizes old conversation history when approaching limits
   - Tracks token usage from OpenAI API responses
   - Configurable thresholds and compression strategies

11. **Utilities** (`utils.py`): Shared helper functions
   - `extract_citations()`: Extracts citation numbers from text
   - Eliminates code duplication across modules

## Implementation Priorities

1. **Transparency First**: Every claim must link back to specific sources
2. **Audit Trail**: Log all decision points and data transformations
3. **Quality Gates**: Self-evaluation triggers automatic retry/fix for low-quality responses
4. **Multi-Source Coverage**: Combine multiple news sources (NewsAPI, Finnhub, Marketaux) for comprehensive coverage
5. **Automatic Quality Improvement**: Retry mechanism ensures responses meet quality thresholds
6. **Extensible Architecture**: Protocol-based provider system makes adding new news sources trivial

## Environment Variables

Required API keys in `.env`:
```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional, for custom endpoints
OPENAI_MODEL=gpt-4.5  # Optional, defaults to gpt-4.5
NEWS_API_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_api_key
MARKETAUX_API_KEY=your_marketaux_api_key  # Optional, for Marketaux news source

# Context Window Management (Optional)
CONTEXT_TOKEN_THRESHOLD=12000      # When to trigger summarization
CONTEXT_MESSAGE_THRESHOLD=15       # Fallback message count limit
CONTEXT_RECENT_MESSAGES=4          # How many recent messages to preserve
CONTEXT_WARNING_THRESHOLD=8000     # When to apply aggressive compression
CONTEXT_MAX_ARTICLES=10            # Max articles per tool result (aggressive mode)
CONTEXT_ENABLE_COMPRESSION=true    # Master switch for compression

# Retry/Fix Mechanism (Optional)
RETRY_ENABLE=true                    # Enable automatic retry for low-quality responses
RETRY_THRESHOLD_OVERALL=6.0          # Trigger retry if overall score < 6.0
RETRY_THRESHOLD_ACCURACY=5.0         # Critical threshold for accuracy
RETRY_MAX_ATTEMPTS=1                 # Maximum retry attempts (1-3 recommended)
RETRY_STRATEGY=auto                  # Strategy: auto|fix|redo|disabled
RETRY_SHOW_ATTEMPTS=true             # Show retry history to user

# API Configuration (Optional)
API_HOST=0.0.0.0                     # API server host
API_PORT=8000                        # API server port
API_RELOAD=false                     # Enable auto-reload for development
API_CORS_ORIGINS=http://localhost:3000  # Allowed CORS origins (comma-separated)
API_REQUEST_TIMEOUT_SECONDS=120      # Request timeout in seconds
```

### Retry/Fix Mechanism

The system automatically improves low-quality responses through intelligent retry:

- **Trigger Conditions**: Overall score < 6.0 OR Accuracy < 5.0
- **FIX Strategy**: Used when sources are correct but narrative needs improvement (low coherence/reasonableness)
  - Preserves existing sources
  - Improves storyline and reasoning
  - Lower token cost (~1.3x)
- **REDO Strategy**: Used when fundamental issues exist (low accuracy/relevance, no sources)
  - Searches for news again
  - Starts fresh with better queries
  - Higher token cost (~2.0x)
- **Smart Selection**: Automatically chooses FIX or REDO based on evaluation scores
- **Cost Control**: Configurable max attempts (default: 1 retry = 2 total attempts max)

## Adding New News Sources

The system uses a Protocol-based provider architecture that makes adding new news sources straightforward.

### Step-by-Step Guide

1. **Create a new provider file** in `financial_news_agent/news_sources/`:
   ```python
   # financial_news_agent/news_sources/my_provider.py
   import os
   import logging
   from datetime import datetime, timedelta
   import requests
   
   from ..types import ArticleData
   from ..traceability import TraceabilityTracker
   
   logger = logging.getLogger(__name__)
   
   class MyProvider:
       """My news provider implementation."""
       
       @property
       def name(self) -> str:
           return "myprovider"
       
       @property
       def is_available(self) -> bool:
           return os.getenv("MY_PROVIDER_API_KEY") is not None
       
       def search(
           self,
           query: str,
           days_back: int = 7,
           company_name: str | None = None,
           tracker: TraceabilityTracker | None = None
       ) -> list[ArticleData]:
           """Search for news articles."""
           if not self.is_available:
               logger.warning("MY_PROVIDER_API_KEY not set")
               return []
           
           # Implement your API call here
           api_key = os.getenv("MY_PROVIDER_API_KEY")
           # ... fetch and parse articles ...
           
           # Return list of ArticleData dictionaries
           return [
               {
                   "title": "Article title",
                   "description": "Article description",
                   "source": "Source name",
                   "url": "https://...",
                   "published_at": "2024-01-01T00:00:00",
                   "content": "Article content",
                   "api_source": self.name  # Must match self.name
               }
           ]
   ```

2. **Export the provider** in `financial_news_agent/news_sources/__init__.py`:
   ```python
   from .base import NewsSourceProvider
   from .newsapi import NewsAPIProvider
   from .finnhub import FinnhubProvider
   from .marketaux import MarketauxProvider
   from .my_provider import MyProvider  # Add this line
   
   __all__ = [
       "NewsSourceProvider",
       "NewsAPIProvider",
       "FinnhubProvider",
       "MarketauxProvider",
       "MyProvider",  # Add this line
   ]
   ```

3. **Register the provider** in `financial_news_agent/news_tool.py`:
   ```python
   from .news_sources import (
       NewsSourceProvider,
       NewsAPIProvider,
       FinnhubProvider,
       MarketauxProvider,
       MyProvider  # Add this import
   )
   
   def get_active_providers() -> list[NewsSourceProvider]:
       """Get list of active news providers based on available API keys."""
       providers: list[NewsSourceProvider] = []
       
       newsapi = NewsAPIProvider()
       if newsapi.is_available:
           providers.append(newsapi)
       
       finnhub = FinnhubProvider()
       if finnhub.is_available:
           providers.append(finnhub)
       
       marketaux = MarketauxProvider()
       if marketaux.is_available:
           providers.append(marketaux)
       
       # Add your provider
       myprovider = MyProvider()
       if myprovider.is_available:
           providers.append(myprovider)
       
       return providers
   ```

4. **Add API key** to `.env`:
   ```bash
   MY_PROVIDER_API_KEY=your_api_key_here
   ```

5. **Add to `.env.example`** for documentation:
   ```bash
   MY_PROVIDER_API_KEY=your-api-key-here
   ```

### Protocol Requirements

Your provider class must implement:
- `name` property: Returns provider name (string, used in `api_source` field)
- `is_available` property: Returns `True` if API key is configured
- `search()` method: Returns `list[ArticleData]` with these required fields:
  - `title`: Article title (string)
  - `description`: Article description/summary (string)
  - `source`: News source name (string)
  - `url`: Article URL (string)
  - `published_at`: Publication date in ISO 8601 format (string)
  - `content`: Article content/snippet (string)
  - `api_source`: Must match `self.name` (string)

### Benefits of This Architecture

- **Automatic Integration**: New providers are automatically included in parallel searches
- **Type Safety**: Protocol ensures compile-time type checking with mypy
- **Dynamic Activation**: Providers activate automatically when API keys are present
- **No Core Changes**: Adding providers doesn't require modifying search orchestration logic
- **Isolated Testing**: Each provider can be tested independently
