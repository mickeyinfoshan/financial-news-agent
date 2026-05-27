# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI agent system for financial news analysis. The agent searches recent financial news about stocks and industries, then provides analysis with storylines and future impact assessments.

**Core Principles:**
- **Traceability**: All claims link back to specific sources
- **Self-Evaluation**: Automatic quality validation with retry mechanism
- **Multi-Source**: Combines NewsAPI, Finnhub, and Marketaux for comprehensive coverage

## Quick Start

```bash
# Install dependencies
uv sync

# Run the agent
uv run python -m financial_news_agent

# Run tests
uv run pytest

# Start API server
uv run python -m financial_news_agent.api_server
```

**Important:** Always use `uv`, never `pip`. See [dependency management rules](.claude/rules/dependency-management.md).

## Technology Stack

- **Language**: Python 3.11+
- **Package Manager**: `uv` (NEVER use `pip`)
- **Agent Framework**: Custom agent loop with OpenAI function calling
- **LLM**: OpenAI API (GPT-5.5 or compatible models)
- **News Sources**: NewsAPI, Finnhub, Marketaux (extensible provider system)
- **API**: FastAPI with streaming support

## Architecture at a Glance

The system uses an agentic loop with these key components:

1. **Agent Module** (`agent/`) - Orchestrates LLM calls with function calling
2. **News Search** (`news_tool.py`) - Multi-source news retrieval with parallel API calls
3. **REST API** (`api/`) - FastAPI server with session management
4. **Quality System** - Self-evaluation, citation validation, automatic retry/fix
5. **Context Management** - Token optimization for long conversations

**See:** [Architecture Documentation](docs/architecture.md) for detailed component descriptions.

## Key Files

```
financial_news_agent/
├── agent/                # Agent orchestration (sync + streaming)
├── news_tool.py          # News search orchestration
├── news_sources/         # Provider implementations (NewsAPI, Finnhub, Marketaux)
├── api/                  # FastAPI server
├── evaluator.py          # Self-evaluation logic
├── retry_manager.py      # Automatic quality improvement
├── context_manager.py    # Token optimization
└── types.py              # TypedDict definitions
```

**See:** [Implementation Details](docs/implementation.md) for complete project structure.

## Common Tasks

### Adding Dependencies
```bash
uv add <package>           # Production dependency
uv add --dev <package>     # Development dependency
```
**See:** [Dependency Management](.claude/rules/dependency-management.md)

### Adding News Sources
The system uses a Protocol-based provider architecture. Adding a new source requires:
1. Create provider class in `news_sources/`
2. Export from `news_sources/__init__.py`
3. Register in `news_tool.py`
4. Add API key to `.env`

**See:** [Adding News Sources Guide](docs/guides/adding-news-sources.md) for step-by-step instructions.

### Configuration
All settings are controlled via environment variables in `.env`:
- API keys (OpenAI, NewsAPI, Finnhub, Marketaux)
- Context window management
- Retry/fix mechanism settings
- API server configuration

**See:** [Configuration Reference](docs/configuration.md) for all options.

## Development Rules

**File Organization:**
- Plans/design docs → `.dev_docs/plan/`
- Summaries/retrospectives → `.dev_docs/summary/`
- Temporary test scripts → `.dev_process/`
- Formal tests → `tests/`

**See:** [Documentation Organization](.claude/rules/documentation-organization.md) and [Development Scripts](.claude/rules/development-scripts.md)

**Package Management:**
- ✅ Use `uv add` / `uv sync`
- ❌ Never use `pip install`

**See:** [Dependency Management](.claude/rules/dependency-management.md)

## Implementation Priorities

1. **Transparency First**: Every claim must link back to specific sources
2. **Audit Trail**: Log all decision points and data transformations
3. **Quality Gates**: Self-evaluation triggers automatic retry/fix
4. **Multi-Source Coverage**: Combine multiple news sources
5. **Extensible Architecture**: Protocol-based provider system

## Documentation

- [Architecture](docs/architecture.md) - Detailed component descriptions
- [Configuration](docs/configuration.md) - Environment variables reference
- [API Reference](docs/api-reference.md) - REST API documentation
- [Implementation](docs/implementation.md) - Code-level details
- [Guides](docs/guides/) - Step-by-step guides for common tasks

## Related Files

- `.claude/rules/` - Development conventions (dependency management, file organization)
- `.dev_docs/` - Internal development documentation (plans, summaries)
- `docs/` - User-facing documentation
