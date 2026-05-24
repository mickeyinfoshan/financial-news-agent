# Financial News Agent

[![Tests](https://github.com/mickeyinfoshan/financial-news-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/mickeyinfoshan/financial-news-agent/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

AI agent that searches recent financial news and provides analysis with storylines and future impact assessments.

## Features

- 🔍 Multi-source financial news search (NewsAPI, Finnhub, Marketaux)
- 🤖 LLM-powered analysis with OpenAI GPT-4
- 📊 Storyline generation and future impact analysis
- ✅ Self-evaluation of response quality
- 🔗 Full traceability of sources and reasoning
- 🔄 Automatic retry/fix mechanism for low-quality responses
- 📈 Smart strategy selection (FIX vs REDO) based on evaluation scores
- 🌐 FastAPI web service with streaming support (Server-Sent Events)
- 🔌 Extensible provider system for adding new news sources

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment Variables

Copy the example file and edit with your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://www.right.codes/codex/v1
OPENAI_MODEL=gpt-5.5
NEWS_API_KEY=your-newsapi-key-here
FINNHUB_API_KEY=your-finnhub-api-key-here
MARKETAUX_API_KEY=your-marketaux-api-key-here  # Optional

# Optional: Retry/Fix Mechanism
RETRY_ENABLE=true                    # Enable automatic quality improvement
RETRY_THRESHOLD_OVERALL=6.0          # Trigger retry if score < 6.0
RETRY_THRESHOLD_ACCURACY=5.0         # Critical accuracy threshold
RETRY_MAX_ATTEMPTS=1                 # Max retry attempts (1-3)
RETRY_STRATEGY=auto                  # auto|fix|redo|disabled
RETRY_SHOW_ATTEMPTS=true             # Show retry history
```

Get API keys:
- NewsAPI: https://newsapi.org (100 requests/day free tier)
- Finnhub: https://finnhub.io (60 requests/minute free tier)
- Marketaux: https://www.marketaux.com (optional, additional news source)

### 3. Run the Agent

**Web API Server:**
```bash
uv run python -m financial_news_agent.api_server
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

**Interactive CLI:**
```bash
uv run python -m financial_news_agent
```

**Test Script:**
```bash
uv run python .dev_process/test_agent.py
```

## API Usage

### Quick Start

**Python Client:**
```python
import requests

# Create session with initial query (one request)
response = requests.post(
    "http://localhost:8000/api/v1/session/create",
    json={"query": "What's happening with NVIDIA?"}
)
result = response.json()
session_id = result["session_id"]
print(result["answer"])

# Follow-up question in same session
response = requests.post(
    f"http://localhost:8000/api/v1/session/{session_id}/query",
    json={"query": "What about AMD?"}
)
print(response.json()["answer"])
```

**curl:**
```bash
# Create session with query
curl -X POST http://localhost:8000/api/v1/session/create \
  -H "Content-Type: application/json" \
  -d '{"query": "What is happening with Tesla stock?"}'

# Follow-up query (use session_id from above)
curl -X POST http://localhost:8000/api/v1/session/{session_id}/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What about their competitors?"}'

# Streaming query (real-time events)
curl -N -X POST http://localhost:8000/api/v1/session/{session_id}/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the outlook for EV stocks?"}'

# List all sessions
curl http://localhost:8000/api/v1/session/list

# Get session details
curl http://localhost:8000/api/v1/session/{session_id}

# Delete session
curl -X DELETE http://localhost:8000/api/v1/session/{session_id}
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/session/create` | Create new session (optional initial query) |
| `POST` | `/api/v1/session/{id}/query` | Ask question in existing session |
| `POST` | `/api/v1/session/{id}/query/stream` | **Stream response in real-time (SSE)** |
| `GET` | `/api/v1/session/{id}` | Get session metadata |
| `GET` | `/api/v1/session/{id}/messages` | Get conversation history |
| `GET` | `/api/v1/session/list` | List all sessions (paginated) |
| `DELETE` | `/api/v1/session/{id}` | Delete session |
| `GET` | `/api/v1/health` | Health check |

**Streaming Support:** The `/query/stream` endpoint returns Server-Sent Events (SSE) in real-time:
- See tool calls as they happen
- Watch reasoning steps unfold
- Get answer tokens as they're generated
- Monitor evaluation and retry events

See [QUICKSTART_API.md](QUICKSTART_API.md) for streaming examples.

### API Configuration

Add to `.env`:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# API Settings
API_CORS_ORIGINS=http://localhost:3000
API_REQUEST_TIMEOUT_SECONDS=120
```

## Example Usage

```
Ask about a company or industry: What's happening with NVIDIA stock?

Analyzing... (this may take a moment)

============================================================
ANSWER
============================================================
Based on recent news, NVIDIA has been experiencing significant 
developments in the AI chip market...

============================================================
SOURCES (5 articles)
============================================================
1. NVIDIA's AI Chip Demand Surges
   Source: Reuters | Date: 2026-05-20
   URL: https://...

============================================================
EVALUATION
============================================================
Overall Score: 8.5/10
  - Accuracy: 8/10
  - Relevance: 8/10
  - Coherence: 9/10
  - Reasonableness: 9/10

Feedback: Strong analysis backed by relevant sources...
```

### Automatic Quality Improvement

If the initial response scores below threshold (< 6.0), the system automatically retries:

```
[Retry 1/1] Strategy: FIX
Reason: Overall=5.5, Accuracy=7/10

Analyzing... (this may take a moment)

============================================================
ANSWER
============================================================
[Improved answer with better coherence and reasoning]

============================================================
RETRY HISTORY
============================================================

Attempt 1:
  Overall: 5.5/10
  Accuracy: 7/10
  Relevance: 6/10
  Coherence: 4/10
  Reasonableness: 5/10
  Answer Preview: [Previous attempt preview]...
```

## Architecture

```
User Query → Agent Loop (LLM + Tools) → Answer → Self-Evaluation
                  ↓                                      ↓
         [NewsAPI + Finnhub + Marketaux]         Score < Threshold?
         [Traceability Tracker]                         ↓
                                                   Retry/Fix
                                                   ↓        ↓
                                              FIX (improve)  REDO (restart)
                                                   ↓        ↓
                                                   → Result
```

### Retry/Fix Mechanism

- **FIX Strategy**: Improves existing answer using same sources (for coherence/reasoning issues)
- **REDO Strategy**: Starts fresh with new search (for accuracy/relevance issues)
- **Smart Selection**: Automatically chooses best strategy based on evaluation scores
- **Cost Control**: Configurable retry limits (default: 1 retry max)

## Project Structure

```
financial_news_agent/
├── __init__.py
├── __main__.py          # CLI entry point
├── api_server.py        # API server entry point
├── agent/               # Main agent loop (modular implementation)
│   ├── __init__.py      # Public API exports
│   ├── prompts.py       # System prompt configuration
│   ├── query_rewriter.py # Multi-turn context resolution
│   ├── shared.py        # Shared business logic
│   ├── sync.py          # Synchronous execution with retry
│   └── streaming.py     # Async streaming execution with retry
├── news_tool.py         # Multi-source news orchestration
├── news_sources/        # News provider implementations
│   ├── __init__.py      # Exports all providers
│   ├── base.py          # NewsSourceProvider Protocol
│   ├── newsapi.py       # NewsAPIProvider implementation
│   ├── finnhub.py       # FinnhubProvider implementation
│   └── marketaux.py     # MarketauxProvider implementation
├── evaluator.py         # Self-evaluation
├── traceability.py      # Source tracking
├── retry_manager.py     # Retry/fix mechanism
├── context_manager.py   # Context window management
├── config.py            # Configuration management
├── types.py             # Type definitions
├── utils.py             # Shared utilities (citation extraction)
└── api/                 # FastAPI web service
    ├── __init__.py
    ├── main.py          # FastAPI app
    ├── routes.py        # API endpoints
    ├── models.py        # Request/response models
    └── session_manager.py  # Session storage
```

## Response Format

The agent returns structured data with full traceability:

```json
{
  "answer": "Full analysis with storyline and future impact",
  "sources": [
    {
      "title": "...",
      "date": "...",
      "source": "...",
      "url": "...",
      "summary": "..."
    }
  ],
  "tool_calls": [
    {
      "tool": "search_financial_news",
      "args": {"query": "NVIDIA"},
      "result_summary": {"type": "list", "count": 5}
    }
  ],
  "reasoning_steps": ["Step 1...", "Step 2..."],
  "evaluation": {
    "accuracy": 8,
    "relevance": 8,
    "coherence": 9,
    "reasonableness": 9,
    "overall": 8.5,
    "feedback": "..."
  },
  "retry_history": [
    {
      "attempt": 1,
      "evaluation": {"overall": 5.5, "accuracy": 7, ...},
      "answer": "Previous attempt..."
    }
  ]
}
```

## Configuration

### Retry/Fix Mechanism

Control automatic quality improvement via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `RETRY_ENABLE` | `true` | Enable/disable retry mechanism |
| `RETRY_THRESHOLD_OVERALL` | `6.0` | Trigger retry if overall score < threshold |
| `RETRY_THRESHOLD_ACCURACY` | `5.0` | Critical accuracy threshold |
| `RETRY_MAX_ATTEMPTS` | `1` | Maximum retry attempts (1-3 recommended) |
| `RETRY_STRATEGY` | `auto` | Strategy: `auto`, `fix`, `redo`, or `disabled` |
| `RETRY_SHOW_ATTEMPTS` | `true` | Show retry history to user |

**Cost Impact**:
- No retry: 1.0x tokens
- FIX once: ~1.3x tokens
- REDO once: ~2.0x tokens

See `.dev_docs/summary/retry-mechanism.md` for detailed documentation.

## Requirements

- Python 3.11+
- OpenAI API key
- NewsAPI key (free tier available)
