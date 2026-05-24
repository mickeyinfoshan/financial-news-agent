"""Base protocol for news source providers."""

from typing import Protocol, runtime_checkable

from ..types import ArticleData
from ..traceability import TraceabilityTracker


@runtime_checkable
class NewsSourceProvider(Protocol):
    """Protocol for news source providers.

    Each provider implements search() to return standardized ArticleData.
    Providers handle their own API authentication, ticker resolution, and
    data normalization.
    """

    @property
    def name(self) -> str:
        """Provider name for logging and api_source field."""
        ...

    @property
    def is_available(self) -> bool:
        """Check if provider is available (API key configured)."""
        ...

    def search(
        self,
        query: str,
        days_back: int = 7,
        company_name: str | None = None,
        tracker: TraceabilityTracker | None = None
    ) -> list[ArticleData]:
        """Search for news articles.

        Returns list of articles with standardized ArticleData format.
        Each article must include api_source field set to self.name.
        """
        ...
