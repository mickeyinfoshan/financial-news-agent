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
- **Agent Framework**: LangGraph for agentic workflows
- **LLM**: Claude 4.x via Anthropic SDK with prompt caching

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
├── agent/                # Agent workflow components
├── news/                 # News search and retrieval
├── knowledge/            # Knowledge management integration
├── analysis/             # Analysis and reasoning engine
└── traceability/         # Traceability tracking

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

The system is designed as an agentic workflow with these components:

1. **News Search & Retrieval**: Fetches recent financial news from multiple sources with metadata tracking
2. **Knowledge Management**: Integrates with KMS for historical context and API data
3. **Analysis Engine**: Generates storylines and impact assessments using LLM reasoning
4. **Traceability System**: Maintains audit trail from query → sources → reasoning → response
5. **Self-Evaluation**: Validates response quality against defined criteria before returning

**Agent Workflow Pattern**:
- Use LangGraph for state management and workflow orchestration
- Each node should emit traceability metadata (sources used, reasoning steps)
- Include self-evaluation as final workflow node before response
- Implement prompt caching for repeated LLM calls with same context

## Implementation Priorities

1. **Transparency First**: Every claim must link back to specific sources
2. **Audit Trail**: Log all decision points and data transformations
3. **Quality Gates**: Self-evaluation must block low-quality responses
4. **Prompt Caching**: Cache news context and knowledge base for cost efficiency
