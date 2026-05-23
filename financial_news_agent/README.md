# financial_news_agent

Core application source code for the financial news agent system.

## Purpose

This directory contains the main application logic for searching, analyzing, and evaluating financial news with full traceability.

## Ownership

Main application code. All core business logic lives here.

## Contents

- `__main__.py` - CLI entry point for running the agent
- `agent.py` - Main agent loop with LLM orchestration and tool calling
- `news_tool.py` - Multi-source news retrieval (NewsAPI + Finnhub with ticker lookup)
- `evaluator.py` - Self-evaluation logic for quality validation
- `context_manager.py` - Context window management with summarization
- `traceability.py` - Source tracking and audit trail for all agent actions

## Key Concepts

- **Agent Loop**: Iterative LLM-based reasoning with OpenAI function calling
- **News Search**: Parallel API calls to NewsAPI and Finnhub with deduplication
- **Traceability**: Every claim links back to specific sources
- **Self-Evaluation**: Quality gates that block low-quality responses

## Usage

Run the agent:
```bash
uv run python -m financial_news_agent
```
