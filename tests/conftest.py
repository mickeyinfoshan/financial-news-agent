"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("FINNHUB_API_KEY", "test_finnhub_key")
    monkeypatch.setenv("NEWS_API_KEY", "test_news_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.5")


@pytest.fixture
def sample_finnhub_search_response():
    """Sample Finnhub symbol search API response."""
    return {
        "count": 2,
        "result": [
            {
                "symbol": "NVDA",
                "type": "Common Stock",
                "description": "NVIDIA CORP"
            },
            {
                "symbol": "NVDA.SW",
                "type": "ADR",
                "description": "NVIDIA ADR"
            }
        ]
    }


@pytest.fixture
def sample_finnhub_news_response():
    """Sample Finnhub company news API response."""
    return [
        {
            "category": "company news",
            "datetime": 1716345600,
            "headline": "NVIDIA Announces New AI Chip",
            "id": 123456,
            "image": "https://example.com/image.jpg",
            "related": "NVDA",
            "source": "Reuters",
            "summary": "NVIDIA unveiled its latest AI chip today.",
            "url": "https://example.com/news/1"
        },
        {
            "category": "company news",
            "datetime": 1716259200,
            "headline": "NVIDIA Stock Rises on Strong Earnings",
            "id": 123457,
            "image": "https://example.com/image2.jpg",
            "related": "NVDA",
            "source": "Bloomberg",
            "summary": "NVIDIA shares jumped after earnings beat expectations.",
            "url": "https://example.com/news/2"
        }
    ]


@pytest.fixture
def sample_newsapi_response():
    """Sample NewsAPI response."""
    return {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {
                "source": {"id": "reuters", "name": "Reuters"},
                "author": "John Doe",
                "title": "NVIDIA Launches New Product",
                "description": "NVIDIA announced a new product line today.",
                "url": "https://example.com/news/3",
                "urlToImage": "https://example.com/image3.jpg",
                "publishedAt": "2026-05-22T10:00:00Z",
                "content": "Full article content here..."
            },
            {
                "source": {"id": "bloomberg", "name": "Bloomberg"},
                "author": "Jane Smith",
                "title": "Tech Stocks Rally",
                "description": "Technology stocks including NVIDIA rallied today.",
                "url": "https://example.com/news/4",
                "urlToImage": "https://example.com/image4.jpg",
                "publishedAt": "2026-05-21T15:30:00Z",
                "content": "Full article content here..."
            }
        ]
    }
