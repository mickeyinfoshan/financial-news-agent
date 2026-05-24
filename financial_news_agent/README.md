# financial_news_agent

Core application source code for the financial news agent system.

## Purpose

This directory contains the main application logic for searching, analyzing, and evaluating financial news with full traceability.

## Ownership

Main application code. All core business logic lives here.

## Contents

- `__main__.py` - CLI entry point for running the agent
- `api_server.py` - FastAPI web service entry point
- `agent/` - Main agent loop with LLM orchestration and tool calling (modular implementation)
- `news_tool.py` - Multi-source news retrieval orchestration
- `news_sources/` - News provider implementations (NewsAPI, Finnhub, Marketaux)
- `evaluator.py` - Self-evaluation logic for quality validation
- `retry_manager.py` - Automatic retry/fix mechanism for low-quality responses
- `context_manager.py` - Context window management with summarization
- `traceability.py` - Source tracking and audit trail for all agent actions
- `config.py` - Configuration management
- `types.py` - Type definitions and data models
- `utils.py` - Shared utility functions (citation extraction)
- `api/` - FastAPI web service implementation

## Key Concepts

- **Agent Loop**: Iterative LLM-based reasoning with OpenAI function calling
- **News Search**: Parallel API calls to multiple providers (NewsAPI, Finnhub, Marketaux) with deduplication
- **Provider System**: Protocol-based extensible architecture for adding new news sources
- **Traceability**: Every claim links back to specific sources
- **Self-Evaluation**: Quality gates with automatic retry/fix mechanism
- **Web API**: FastAPI service with streaming support (Server-Sent Events)

## Usage

**Web API Server:**
```bash
uv run python -m financial_news_agent.api_server
```

**Interactive CLI:**
```bash
uv run python -m financial_news_agent
```

**Test Script:**
```bash
uv run python .dev_process/test_agent.py
```
