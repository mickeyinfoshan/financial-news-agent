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
└── evaluator.py          # Self-evaluation logic

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
   - Blocks low-quality responses before returning

## Implementation Priorities

1. **Transparency First**: Every claim must link back to specific sources
2. **Audit Trail**: Log all decision points and data transformations
3. **Quality Gates**: Self-evaluation must block low-quality responses
4. **Multi-Source Coverage**: Combine NewsAPI and Finnhub for comprehensive news coverage

## Environment Variables

Required API keys in `.env`:
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional, for custom endpoints
OPENAI_MODEL=gpt-4.5  # Optional, defaults to gpt-4.5
NEWS_API_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_api_key
```
