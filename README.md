# Financial News Agent

AI agent that searches recent financial news and provides analysis with storylines and future impact assessments.

## Features

- 🔍 Real-time financial news search via NewsAPI
- 🤖 LLM-powered analysis with OpenAI GPT-4
- 📊 Storyline generation and future impact analysis
- ✅ Self-evaluation of response quality
- 🔗 Full traceability of sources and reasoning

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
```

Get a free NewsAPI key at: https://newsapi.org (100 requests/day free tier)

### 3. Run the Agent

**Interactive CLI:**
```bash
uv run python -m financial_news_agent
```

**Test Script:**
```bash
uv run python .dev_process/test_agent.py
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

## Architecture

```
User Query → Agent Loop (LLM + Tools) → Answer → Self-Evaluation → Result
                  ↓
         [NewsAPI Search Tool]
         [Traceability Tracker]
```

## Project Structure

```
financial_news_agent/
├── __init__.py
├── __main__.py          # CLI entry point
├── agent.py             # Main agent loop
├── news_tool.py         # NewsAPI integration
├── evaluator.py         # Self-evaluation
└── traceability.py      # Source tracking
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
  }
}
```

## Requirements

- Python 3.11+
- OpenAI API key
- NewsAPI key (free tier available)
