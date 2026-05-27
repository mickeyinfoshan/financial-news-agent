# Adding New News Sources

This guide shows you how to add new financial news API integrations to the system.

## Overview

The system uses a Protocol-based provider architecture that makes adding new news sources straightforward. Each provider implements a simple interface and is automatically integrated into the parallel search system.

## Step-by-Step Guide

### 1. Create a New Provider File

Create a new file in `financial_news_agent/news_sources/`:

```python
# financial_news_agent/news_sources/my_provider.py
import os
import logging
from datetime import datetime, timedelta
import requests

from ..types import ArticleData
from ..traceability import TraceabilityTracker

logger = logging.getLogger(__name__)

class MyProvider:
    """My news provider implementation."""
    
    @property
    def name(self) -> str:
        return "myprovider"
    
    @property
    def is_available(self) -> bool:
        return os.getenv("MY_PROVIDER_API_KEY") is not None
    
    def search(
        self,
        query: str,
        days_back: int = 7,
        company_name: str | None = None,
        tracker: TraceabilityTracker | None = None
    ) -> list[ArticleData]:
        """Search for news articles."""
        if not self.is_available:
            logger.warning("MY_PROVIDER_API_KEY not set")
            return []
        
        # Implement your API call here
        api_key = os.getenv("MY_PROVIDER_API_KEY")
        # ... fetch and parse articles ...
        
        # Return list of ArticleData dictionaries
        return [
            {
                "title": "Article title",
                "description": "Article description",
                "source": "Source name",
                "url": "https://...",
                "published_at": "2024-01-01T00:00:00",
                "content": "Article content",
                "api_source": self.name  # Must match self.name
            }
        ]
```

### 2. Export the Provider

Add your provider to `financial_news_agent/news_sources/__init__.py`:

```python
from .base import NewsSourceProvider
from .newsapi import NewsAPIProvider
from .finnhub import FinnhubProvider
from .marketaux import MarketauxProvider
from .my_provider import MyProvider  # Add this line

__all__ = [
    "NewsSourceProvider",
    "NewsAPIProvider",
    "FinnhubProvider",
    "MarketauxProvider",
    "MyProvider",  # Add this line
]
```

### 3. Register the Provider

Add your provider to `financial_news_agent/news_tool.py`:

```python
from .news_sources import (
    NewsSourceProvider,
    NewsAPIProvider,
    FinnhubProvider,
    MarketauxProvider,
    MyProvider  # Add this import
)

def get_active_providers() -> list[NewsSourceProvider]:
    """Get list of active news providers based on available API keys."""
    providers: list[NewsSourceProvider] = []
    
    newsapi = NewsAPIProvider()
    if newsapi.is_available:
        providers.append(newsapi)
    
    finnhub = FinnhubProvider()
    if finnhub.is_available:
        providers.append(finnhub)
    
    marketaux = MarketauxProvider()
    if marketaux.is_available:
        providers.append(marketaux)
    
    # Add your provider
    myprovider = MyProvider()
    if myprovider.is_available:
        providers.append(myprovider)
    
    return providers
```

### 4. Add API Key Configuration

Add your API key to `.env`:

```bash
MY_PROVIDER_API_KEY=your_api_key_here
```

Add to `.env.example` for documentation:

```bash
MY_PROVIDER_API_KEY=your-api-key-here
```

## Protocol Requirements

Your provider class must implement:

- **`name` property**: Returns provider name (string, used in `api_source` field)
- **`is_available` property**: Returns `True` if API key is configured
- **`search()` method**: Returns `list[ArticleData]` with these required fields:
  - `title`: Article title (string)
  - `description`: Article description/summary (string)
  - `source`: News source name (string)
  - `url`: Article URL (string)
  - `published_at`: Publication date in ISO 8601 format (string)
  - `content`: Article content/snippet (string)
  - `api_source`: Must match `self.name` (string)

## Benefits of This Architecture

- **Automatic Integration**: New providers are automatically included in parallel searches
- **Type Safety**: Protocol ensures compile-time type checking with mypy
- **Dynamic Activation**: Providers activate automatically when API keys are present
- **No Core Changes**: Adding providers doesn't require modifying search orchestration logic
- **Isolated Testing**: Each provider can be tested independently

## Examples

See existing implementations for reference:
- `financial_news_agent/news_sources/newsapi.py` - General news provider
- `financial_news_agent/news_sources/finnhub.py` - Company-specific news with ticker lookup
- `financial_news_agent/news_sources/marketaux.py` - Additional financial news source

## Related Documentation

- [Architecture](../architecture.md) - System architecture overview
- [Configuration](../configuration.md) - Environment variables and settings
