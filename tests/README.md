# tests

Formal test suite for the financial news agent project.

## Purpose

Unit and integration tests to ensure code quality and correctness.

## Ownership

Quality assurance and validation. All formal tests belong here.

## Contents

- `conftest.py` - Pytest configuration and shared fixtures
- `test_context_manager.py` - Context window management tests
- `test_news_tool.py` - News search and API integration tests
- `test_ticker_extraction.py` - Ticker symbol extraction tests
- `test_retry_manager.py` - Retry/fix mechanism tests
- `test_integration.py` - End-to-end integration tests

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=financial_news_agent

# Run specific test file
uv run pytest tests/test_news_tool.py
```

## Note

For temporary validation scripts, use `.dev_process/` instead. This directory is for formal, committed tests only.
