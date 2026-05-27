# Configuration

This document provides a complete reference for all environment variables and configuration options.

## Required API Keys

These API keys must be configured in `.env`:

```bash
# OpenAI API (Required)
OPENAI_API_KEY=your_openai_api_key

# News Sources (At least one required)
NEWS_API_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_api_key
MARKETAUX_API_KEY=your_marketaux_api_key  # Optional
```

## Optional Configuration

### OpenAI Settings

```bash
# Custom OpenAI-compatible endpoint
OPENAI_BASE_URL=https://www.right.codes/codex/v1

# Model selection (optional, defaults to gpt-5.5)
OPENAI_MODEL=gpt-5.5
```

**Note:** This project uses a custom OpenAI-compatible endpoint. If using standard OpenAI API, set `OPENAI_BASE_URL=https://api.openai.com/v1`

### Context Window Management

Controls token usage and conversation history management:

```bash
# When to trigger summarization (default: 12000)
CONTEXT_TOKEN_THRESHOLD=12000

# Fallback message count limit (default: 15)
CONTEXT_MESSAGE_THRESHOLD=15

# How many recent messages to preserve (default: 4)
CONTEXT_RECENT_MESSAGES=4

# When to apply aggressive compression (default: 8000)
CONTEXT_WARNING_THRESHOLD=8000

# Max articles per tool result in aggressive mode (default: 10)
CONTEXT_MAX_ARTICLES=10

# Master switch for compression (default: true)
CONTEXT_ENABLE_COMPRESSION=true
```

**How It Works:**
- When token count exceeds `CONTEXT_TOKEN_THRESHOLD`, old messages are summarized
- Recent messages (controlled by `CONTEXT_RECENT_MESSAGES`) are always preserved
- When approaching `CONTEXT_WARNING_THRESHOLD`, aggressive compression kicks in
- Tool results are compressed to max `CONTEXT_MAX_ARTICLES` articles

**See Also:** [Architecture - Context Management](architecture.md#10-context-management-context_managerpy)

### Retry/Fix Mechanism

Controls automatic quality improvement:

```bash
# Enable automatic retry for low-quality responses (default: true)
RETRY_ENABLE=true

# Trigger retry if overall score < this value (default: 6.0)
RETRY_THRESHOLD_OVERALL=6.0

# Critical threshold for accuracy (default: 5.0)
RETRY_THRESHOLD_ACCURACY=5.0

# Maximum retry attempts (default: 1, range: 1-3)
RETRY_MAX_ATTEMPTS=1

# Strategy selection (default: auto)
# Options: auto|fix|redo|disabled
RETRY_STRATEGY=auto

# Show retry history to user (default: true)
RETRY_SHOW_ATTEMPTS=true
```

**Strategies:**

- **auto** (recommended): Automatically chooses FIX or REDO based on evaluation scores
- **fix**: Always use FIX strategy (improves existing answer with same sources)
- **redo**: Always use REDO strategy (starts fresh with new search)
- **disabled**: Disables retry mechanism

**FIX Strategy:**
- Used when sources are correct but narrative needs improvement
- Preserves existing sources
- Improves storyline and reasoning
- Lower token cost (~1.3x)

**REDO Strategy:**
- Used when fundamental issues exist (low accuracy/relevance, no sources)
- Searches for news again
- Starts fresh with better queries
- Higher token cost (~2.0x)

**Cost Control:**
- `RETRY_MAX_ATTEMPTS=1` means 2 total attempts max (1 original + 1 retry)
- Set to `0` to disable retries
- Higher values increase quality but also cost

**See Also:** [Architecture - Retry/Fix Mechanism](architecture.md#9-retryfix-mechanism-retry_managerpy)

### API Server Settings

Controls the FastAPI server behavior:

```bash
# Server host (default: 0.0.0.0)
API_HOST=0.0.0.0

# Server port (default: 8000)
API_PORT=8000

# Enable auto-reload for development (default: false)
API_RELOAD=false

# Allowed CORS origins, comma-separated (default: http://localhost:3000)
API_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Request timeout in seconds (default: 120)
API_REQUEST_TIMEOUT_SECONDS=120
```

**See Also:** [API Reference](api-reference.md)

## Configuration File Example

Complete `.env` file example:

```bash
# API Keys (Required)
OPENAI_API_KEY=sk-...
NEWS_API_KEY=...
FINNHUB_API_KEY=...
MARKETAUX_API_KEY=...

# OpenAI Settings (Optional)
OPENAI_BASE_URL=https://www.right.codes/codex/v1
OPENAI_MODEL=gpt-5.5

# Context Window Management (Optional)
CONTEXT_TOKEN_THRESHOLD=12000
CONTEXT_MESSAGE_THRESHOLD=15
CONTEXT_RECENT_MESSAGES=4
CONTEXT_WARNING_THRESHOLD=8000
CONTEXT_MAX_ARTICLES=10
CONTEXT_ENABLE_COMPRESSION=true

# Retry/Fix Mechanism (Optional)
RETRY_ENABLE=true
RETRY_THRESHOLD_OVERALL=6.0
RETRY_THRESHOLD_ACCURACY=5.0
RETRY_MAX_ATTEMPTS=1
RETRY_STRATEGY=auto
RETRY_SHOW_ATTEMPTS=true

# API Configuration (Optional)
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_CORS_ORIGINS=http://localhost:3000
API_REQUEST_TIMEOUT_SECONDS=120
```

## Related Documentation

- [Architecture](architecture.md) - System architecture overview
- [API Reference](api-reference.md) - REST API documentation
- [Adding News Sources](guides/adding-news-sources.md) - How to add new providers
