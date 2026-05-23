# FastAPI Quick Start Guide

## Start the API Server

```bash
uv run python -m financial_news_agent.api_server
```

The server will start at `http://localhost:8000`

## Interactive API Documentation

Visit these URLs in your browser:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Quick Test

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Create Session and Ask Question (One Request)
```bash
curl -X POST http://localhost:8000/api/v1/session/create \
  -H "Content-Type: application/json" \
  -d '{"query": "What is happening with Tesla stock?"}'
```

Save the `session_id` from the response.

### 3. Follow-up Question
```bash
curl -X POST http://localhost:8000/api/v1/session/{SESSION_ID}/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What about their competitors?"}'
```

### 4. List All Sessions
```bash
curl http://localhost:8000/api/v1/session/list
```

### 5. Get Session Details
```bash
curl http://localhost:8000/api/v1/session/{SESSION_ID}
```

### 6. Get Conversation History
```bash
curl http://localhost:8000/api/v1/session/{SESSION_ID}/messages
```

### 7. Delete Session
```bash
curl -X DELETE http://localhost:8000/api/v1/session/{SESSION_ID}
```

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Create session with initial query
response = requests.post(
    f"{BASE_URL}/session/create",
    json={"query": "What's happening with NVIDIA?"}
)
result = response.json()
session_id = result["session_id"]

print(f"Session ID: {session_id}")
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])} articles")
print(f"Score: {result['evaluation']['overall']}/10")

# Follow-up question
response = requests.post(
    f"{BASE_URL}/session/{session_id}/query",
    json={"query": "What about AMD?"}
)
result = response.json()
print(f"\nFollow-up Answer: {result['answer']}")
```

## Configuration

Edit `.env` to customize:

```bash
API_HOST=0.0.0.0          # Listen on all interfaces
API_PORT=8000             # Port number
API_RELOAD=false          # Auto-reload on code changes (dev only)
API_CORS_ORIGINS=http://localhost:3000  # Allowed CORS origins
API_REQUEST_TIMEOUT_SECONDS=120  # Request timeout
```

## Development Mode

For development with auto-reload:

```bash
# Set in .env
API_RELOAD=true

# Or run directly with uvicorn
uv run uvicorn financial_news_agent.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing

Run automated tests:

```bash
uv run pytest tests/test_api.py -v
```

Run manual test script (requires server running):

```bash
# Terminal 1: Start server
uv run python -m financial_news_agent.api_server

# Terminal 2: Run test
uv run python .dev_process/test_api_manual.py
```

## Troubleshooting

**Port already in use:**
```bash
# Change port in .env
API_PORT=8001
```

**CORS errors:**
```bash
# Add your frontend URL to .env
API_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Connection refused:**
- Make sure the server is running
- Check firewall settings
- Verify the correct host/port

## CLI Still Works

The original CLI is still available:

```bash
uv run python -m financial_news_agent
```
