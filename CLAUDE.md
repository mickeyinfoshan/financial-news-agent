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
- **News Sources**: NewsAPI and Finnhub for financial news

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
financial_news_agent/     # Main source code (flat structure)
├── __init__.py
├── __main__.py           # Entry point
├── agent.py              # Main agent loop with LLM and tool calling
├── news_tool.py          # News search (NewsAPI + Finnhub)
├── traceability.py       # Traceability tracking
├── evaluator.py          # Self-evaluation logic
└── retry_manager.py      # Retry/fix mechanism for low-quality responses

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

1. **Agent Loop** (`agent.py`): Orchestrates LLM calls with OpenAI function calling
   - Iterative loop (max 10 iterations)
   - Calls news search tool as needed
   - Tracks all tool calls and reasoning steps
   - Wrapped by `run_agent_with_retry()` for automatic quality improvement

2. **News Search** (`news_tool.py`): Multi-source news retrieval
   - NewsAPI for general financial news
   - Finnhub for company-specific news with ticker lookup
   - Parallel API calls with deduplication
   - Dynamic ticker resolution via Finnhub Symbol Search API

3. **Traceability** (`traceability.py`): Audit trail tracking
   - Records all sources, tool calls, and reasoning steps
   - Maintains query → sources → reasoning → response chain

4. **Self-Evaluation** (`evaluator.py`): Quality validation
   - Evaluates accuracy, relevance, coherence, and impact analysis
   - Produces scores (1-10 scale) for each dimension
   - Triggers retry mechanism when scores are below threshold

5. **Retry/Fix Mechanism** (`retry_manager.py`): Automatic quality improvement
   - Monitors evaluation scores and triggers retries when quality is low
   - **FIX strategy**: Improves existing answer using same sources (for coherence/reasoning issues)
   - **REDO strategy**: Starts fresh with new search (for accuracy/relevance issues)
   - Configurable thresholds and retry limits to control cost

## Implementation Priorities

1. **Transparency First**: Every claim must link back to specific sources
2. **Audit Trail**: Log all decision points and data transformations
3. **Quality Gates**: Self-evaluation triggers automatic retry/fix for low-quality responses
4. **Multi-Source Coverage**: Combine NewsAPI and Finnhub for comprehensive news coverage
5. **Automatic Quality Improvement**: Retry mechanism ensures responses meet quality thresholds

## Environment Variables

Required API keys in `.env`:
```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional, for custom endpoints
OPENAI_MODEL=gpt-4.5  # Optional, defaults to gpt-4.5
NEWS_API_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_api_key

# Retry/Fix Mechanism (Optional)
RETRY_ENABLE=true                    # Enable automatic retry for low-quality responses
RETRY_THRESHOLD_OVERALL=6.0          # Trigger retry if overall score < 6.0
RETRY_THRESHOLD_ACCURACY=5.0         # Critical threshold for accuracy
RETRY_MAX_ATTEMPTS=1                 # Maximum retry attempts (1-3 recommended)
RETRY_STRATEGY=auto                  # Strategy: auto|fix|redo|disabled
RETRY_SHOW_ATTEMPTS=true             # Show retry history to user
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
