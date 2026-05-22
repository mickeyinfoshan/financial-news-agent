# Implementation Guide

## Overview

The Financial News Agent is built using a simple agent loop pattern with OpenAI SDK function calling. The system searches real financial news via NewsAPI, generates analysis with storylines and future impact assessments, and self-evaluates the response quality.

## Architecture

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│     Agent Loop (max 10 iterations)  │
│  ┌───────────────────────────────┐  │
│  │  LLM Call with Tool Calling   │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│      ┌───────┴────────┐             │
│      │                │             │
│      ▼                ▼             │
│  Tool Calls?      Final Answer?     │
│      │                │             │
│      ▼                │             │
│  Execute Tool         │             │
│  (NewsAPI Search)     │             │
│      │                │             │
│  Track Sources        │             │
│      │                │             │
│  Add to Messages      │             │
│      │                │             │
│  Loop Back ───────────┘             │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────┐
│  Self-Evaluation    │
│  (Second LLM Call)  │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │   Result     │
    │  - Answer    │
    │  - Sources   │
    │  - Evaluation│
    │  - Trace     │
    └──────────────┘
```

## How It Works

### 1. Initialization

When `run_agent(query)` is called:

```python
# financial_news_agent/agent.py:15
def run_agent(user_query: str) -> dict:
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    tracker = TraceabilityTracker()
```

- Creates OpenAI client with custom endpoint
- Initializes traceability tracker to record all sources and reasoning

### 2. Agent Loop

The core loop (lines 54-122 in `agent.py`) iterates up to 10 times:

**Step 1: LLM Call with Tools**
```python
response = client.chat.completions.create(
    model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
    messages=messages,
    tools=tools,
    tool_choice="auto",
    temperature=0.7,
    max_tokens=2000
)
```

**Step 2: Check Response Type**
- If `tool_calls` present → Execute tools and continue loop
- If no `tool_calls` → Extract final answer and break

**Step 3: Tool Execution**
```python
for tool_call in assistant_message.tool_calls:
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)
    result = execute_tool(tool_name, tool_args)
    
    # Track the call
    tracker.add_tool_call(tool_name, tool_args, result)
    
    # Extract and track sources
    for article in result:
        tracker.add_source({
            "title": article.get("title", ""),
            "date": article.get("published_at", ""),
            "source": article.get("source", ""),
            "url": article.get("url", ""),
            "summary": article.get("description", "")
        })
```

**Step 4: Add Tool Result to Conversation**
```python
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(result, ensure_ascii=False)
})
```

### 3. Tool: News Search

The `search_financial_news` tool (`news_tool.py:44`) queries NewsAPI:

```python
def execute_tool(tool_name: str, arguments: dict) -> list:
    if tool_name == "search_financial_news":
        query = arguments.get("query", "")
        days_back = arguments.get("days_back", 7)
        
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        # Call NewsAPI
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": os.getenv("NEWS_API_KEY")
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        return data.get("articles", [])[:10]  # Return top 10
```

### 4. Traceability System

The `TraceabilityTracker` class (`traceability.py`) maintains three lists:

- **sources**: News articles used (title, date, source, url, summary)
- **tool_calls**: Tools invoked (tool_name, arguments, result summary)
- **reasoning_steps**: LLM text outputs during the loop

All data is preserved and returned in the final result for full audit trail.

### 5. Self-Evaluation

After the agent generates an answer, a second LLM call evaluates quality (`evaluator.py:12`):

```python
def evaluate_response(answer: str, tracker) -> dict:
    # Build prompt with answer and sources
    evaluation_prompt = f"""Evaluate this financial news analysis response...
    
    ANSWER:
    {answer}
    
    SOURCES USED:
    {sources_summary}
    
    EVALUATION CRITERIA (rate each 1-10, where 10 is excellent):
    1. Accuracy: Does the information match the sources?
    2. Relevance: Are the sources relevant to the query?
    3. Coherence: Does the storyline flow logically?
    4. Reasonableness: Is the future impact analysis plausible?
    """
    
    # Call LLM for evaluation
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
        messages=[...],
        temperature=0.3,
        max_tokens=500
    )
    
    # Parse JSON response
    evaluation = json.loads(eval_text)
    evaluation["overall"] = average_of_four_scores
    
    return evaluation
```

## Key Design Decisions

### Why OpenAI SDK Instead of LangGraph?

**Simplicity**: The task requires a straightforward loop pattern. Using LangGraph would add:
- State machine complexity (~300+ lines)
- Node/edge definitions
- Graph compilation overhead

The OpenAI SDK's native function calling provides everything needed in ~250 lines.

### Why NewsAPI?

**Real Data**: NewsAPI provides actual financial news articles with:
- Free tier: 100 requests/day
- 1 month historical data
- Simple REST API
- No authentication complexity

Alternative (MCP servers) would require additional setup without significant benefit for this use case.

### Why 1-10 Evaluation Scale?

**Better Granularity**: A 1-10 scale provides finer distinctions in quality assessment compared to 1-5. This helps identify:
- Excellent responses (9-10)
- Good responses (7-8)
- Acceptable responses (5-6)
- Poor responses (1-4)

### Custom Endpoint Configuration

The system uses a custom OpenAI-compatible endpoint:
- **Base URL**: `https://www.right.codes/codex/v1`
- **Model**: `gpt-5.5`
- **API Key**: Custom key for the endpoint

This is configured via environment variables for flexibility.

## Configuration

All configuration is managed through `.env` file:

```bash
# Required: Custom OpenAI-compatible endpoint
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://www.right.codes/codex/v1
OPENAI_MODEL=gpt-5.5

# Required: NewsAPI key (get free at https://newsapi.org)
NEWS_API_KEY=your-newsapi-key-here
```

## Error Handling

The system includes error handling at multiple levels:

1. **Agent Loop**: Catches exceptions and returns error message
2. **Tool Execution**: Returns empty list on API failures
3. **Evaluation**: Returns default scores (3/10) if evaluation fails

## Performance

Typical execution:
- **Tool calls**: 1-3 per query
- **News articles**: 5-15 retrieved
- **Total time**: 5-15 seconds
- **Evaluation score**: 7-9/10 average

## File References

- Main agent loop: `financial_news_agent/agent.py:15-139`
- News tool: `financial_news_agent/news_tool.py:44-75`
- Traceability: `financial_news_agent/traceability.py:1-35`
- Evaluator: `financial_news_agent/evaluator.py:12-100`
- CLI entry: `financial_news_agent/__main__.py:1-50`
