"""API server entry point.

Run with: uv run python -m financial_news_agent.api_server
"""

import uvicorn
from financial_news_agent.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "financial_news_agent.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
