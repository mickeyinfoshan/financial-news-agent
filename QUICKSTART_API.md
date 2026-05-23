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

### 4. Streaming Query (Real-time Response)
```bash
curl -N -X POST http://localhost:8000/api/v1/session/{SESSION_ID}/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the outlook for EV stocks?"}'
```

The `-N` flag disables buffering so you see events in real-time.

### 5. List All Sessions
```bash
curl http://localhost:8000/api/v1/session/list
```

### 6. Get Session Details
```bash
curl http://localhost:8000/api/v1/session/{SESSION_ID}
```

### 7. Get Conversation History
```bash
curl http://localhost:8000/api/v1/session/{SESSION_ID}/messages
```

### 8. Delete Session
```bash
curl -X DELETE http://localhost:8000/api/v1/session/{SESSION_ID}
```

## Streaming vs Non-Streaming

**Non-streaming** (`/query`): Returns complete response after agent finishes
- Use when you want the full result at once
- Simpler to handle
- Example: batch processing, background jobs

**Streaming** (`/query/stream`): Returns events in real-time as agent works
- Use when you want to show progress to users
- See tool calls, reasoning, and answer as they happen
- Better UX for long-running queries (30+ seconds)
- Uses Server-Sent Events (SSE) format

## Python Client Example

### Non-Streaming
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

### Streaming
```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Create session
response = requests.post(f"{BASE_URL}/session/create", json={})
session_id = response.json()["session_id"]

# Stream query
response = requests.post(
    f"{BASE_URL}/session/{session_id}/query/stream",
    json={"query": "What's happening with Tesla?"},
    stream=True
)

print("Streaming response:")
for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        event = json.loads(line[6:])
        
        if event['event'] == 'token':
            # Print answer tokens as they arrive
            print(event['data']['content'], end='', flush=True)
        
        elif event['event'] == 'tool_call_start':
            print(f"\n[Searching {event['data']['tool_name']}...]")
        
        elif event['event'] == 'evaluation':
            print(f"\n\nScore: {event['data']['overall']}/10")
        
        elif event['event'] == 'done':
            print("\n\nComplete!")
            break
```

## JavaScript Client Example

### Streaming with Fetch API
```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/session/SESSION_ID/query/stream',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: "What's happening with Apple?" })
  }
);

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value);
  const lines = text.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      
      switch (event.event) {
        case 'token':
          // Append token to UI
          document.getElementById('answer').textContent += event.data.content;
          break;
        
        case 'tool_call_start':
          document.getElementById('status').textContent = 
            `Searching ${event.data.tool_name}...`;
          break;
        
        case 'tool_call_complete':
          document.getElementById('status').textContent = 
            `Found ${event.data.article_count} articles`;
          break;
        
        case 'evaluation':
          document.getElementById('score').textContent = 
            `Score: ${event.data.overall}/10`;
          break;
        
        case 'done':
          console.log('Complete:', event.data.result);
          break;
      }
    }
  }
}
```

## Streaming Event Types

| Event | Description | Data Fields |
|-------|-------------|-------------|
| `agent_start` | Agent begins processing | `query` |
| `iteration_start` | New agent loop iteration | `iteration` (1-10) |
| `token` | Token from LLM response | `content`, `iteration` |
| `tool_call_start` | Tool execution begins | `tool_name`, `arguments`, `iteration` |
| `tool_call_complete` | Tool execution finished | `tool_name`, `result_summary`, `article_count`, `iteration` |
| `evaluation` | Self-evaluation results | `overall`, `accuracy`, `relevance`, `coherence`, `reasonableness` |
| `retry` | Retry triggered (low quality) | `attempt`, `reason`, `strategy` |
| `done` | Processing complete | `result` (full result dict), `messages` |
| `error` | Error occurred | `message` |

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

Run manual test scripts (requires server running):

```bash
# Terminal 1: Start server
uv run python -m financial_news_agent.api_server

# Terminal 2: Test non-streaming
uv run python .dev_process/test_api_manual.py

# Terminal 3: Test streaming
uv run python .dev_process/test_api_streaming.py
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

**Streaming not working:**
- Make sure you're using `-N` flag with curl (disables buffering)
- In Python, use `stream=True` with requests
- In JavaScript, use ReadableStream API

## CLI Still Works

The original CLI is still available:

```bash
uv run python -m financial_news_agent
```
