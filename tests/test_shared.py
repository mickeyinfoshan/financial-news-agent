"""Unit tests for agent/shared module."""

from financial_news_agent.agent.shared import process_tool_results
from financial_news_agent.traceability import TraceabilityTracker
from financial_news_agent.types import ArticleData


class TestProcessToolResults:
    """Tests for process_tool_results function."""

    def test_process_tool_results_assigns_ids(self):
        """Test that process_tool_results assigns sequential IDs starting from 1."""
        tracker = TraceabilityTracker()
        articles = [
            {
                "title": "Article 1",
                "description": "Description 1",
                "source": "Source A",
                "url": "https://example.com/1",
                "published_at": "2026-05-27T10:00:00",
                "content": "Content 1",
                "api_source": "newsapi"
            },
            {
                "title": "Article 2",
                "description": "Description 2",
                "source": "Source B",
                "url": "https://example.com/2",
                "published_at": "2026-05-27T09:00:00",
                "content": "Content 2",
                "api_source": "finnhub"
            }
        ]

        result = process_tool_results(articles, tracker)

        # Check returned sources have IDs
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

        # Check tracker.sources also has the same sources with IDs
        assert len(tracker.sources) == 2
        assert tracker.sources[0]["id"] == 1
        assert tracker.sources[1]["id"] == 2

    def test_process_tool_results_continues_numbering(self):
        """Test that IDs continue from existing sources in tracker."""
        tracker = TraceabilityTracker()

        # First batch of articles
        first_batch = [
            {
                "title": "Article 1",
                "description": "Description 1",
                "source": "Source A",
                "url": "https://example.com/1",
                "published_at": "2026-05-27T10:00:00",
                "content": "Content 1",
                "api_source": "newsapi"
            },
            {
                "title": "Article 2",
                "description": "Description 2",
                "source": "Source B",
                "url": "https://example.com/2",
                "published_at": "2026-05-27T09:00:00",
                "content": "Content 2",
                "api_source": "finnhub"
            }
        ]

        result1 = process_tool_results(first_batch, tracker)
        assert result1[0]["id"] == 1
        assert result1[1]["id"] == 2
        assert len(tracker.sources) == 2

        # Second batch should continue numbering
        second_batch = [
            {
                "title": "Article 3",
                "description": "Description 3",
                "source": "Source C",
                "url": "https://example.com/3",
                "published_at": "2026-05-27T08:00:00",
                "content": "Content 3",
                "api_source": "newsapi"
            }
        ]

        result2 = process_tool_results(second_batch, tracker)
        assert result2[0]["id"] == 3
        assert len(tracker.sources) == 3
        assert tracker.sources[2]["id"] == 3

    def test_process_tool_results_converts_fields(self):
        """Test that ArticleData fields are correctly converted to SourceData fields."""
        tracker = TraceabilityTracker()
        articles = [
            {
                "title": "Test Article",
                "description": "Test description",
                "source": "Test Source",
                "url": "https://example.com/test",
                "published_at": "2026-05-27T10:00:00",
                "content": "Test content",
                "api_source": "newsapi"
            }
        ]

        result = process_tool_results(articles, tracker)

        # Check field mapping
        assert result[0]["id"] == 1
        assert result[0]["title"] == "Test Article"
        assert result[0]["date"] == "2026-05-27T10:00:00"  # published_at -> date
        assert result[0]["summary"] == "Test description"  # description -> summary
        assert result[0]["source"] == "Test Source"
        assert result[0]["url"] == "https://example.com/test"
        assert result[0]["api_source"] == "newsapi"

        # content field should not be in SourceData
        assert "content" not in result[0]
        assert "description" not in result[0]
        assert "published_at" not in result[0]

    def test_process_tool_results_handles_empty_list(self):
        """Test that empty article list is handled correctly."""
        tracker = TraceabilityTracker()
        articles = []

        result = process_tool_results(articles, tracker)

        assert result == []
        assert len(tracker.sources) == 0

    def test_process_tool_results_handles_missing_description(self):
        """Test that missing description field is handled gracefully."""
        tracker = TraceabilityTracker()
        articles = [
            {
                "title": "Test Article",
                # description is missing
                "source": "Test Source",
                "url": "https://example.com/test",
                "published_at": "2026-05-27T10:00:00",
                "content": "Test content",
                "api_source": "newsapi"
            }
        ]

        result = process_tool_results(articles, tracker)

        assert result[0]["summary"] == ""  # Should default to empty string

    def test_process_tool_results_sequential_ids_with_multiple_batches(self):
        """Test that IDs remain sequential across multiple tool calls."""
        tracker = TraceabilityTracker()

        # Simulate 3 tool calls with different numbers of articles
        batch1 = [{"title": f"Article {i}", "description": f"Desc {i}", "source": "Source",
                   "url": f"url{i}", "published_at": "2026-05-27", "content": "content",
                   "api_source": "test"} for i in range(1, 6)]  # 5 articles

        batch2 = [{"title": f"Article {i}", "description": f"Desc {i}", "source": "Source",
                   "url": f"url{i}", "published_at": "2026-05-27", "content": "content",
                   "api_source": "test"} for i in range(6, 9)]  # 3 articles

        batch3 = [{"title": f"Article {i}", "description": f"Desc {i}", "source": "Source",
                   "url": f"url{i}", "published_at": "2026-05-27", "content": "content",
                   "api_source": "test"} for i in range(9, 11)]  # 2 articles

        result1 = process_tool_results(batch1, tracker)
        result2 = process_tool_results(batch2, tracker)
        result3 = process_tool_results(batch3, tracker)

        # Check IDs are sequential
        assert [s["id"] for s in result1] == [1, 2, 3, 4, 5]
        assert [s["id"] for s in result2] == [6, 7, 8]
        assert [s["id"] for s in result3] == [9, 10]

        # Check total sources in tracker
        assert len(tracker.sources) == 10
        assert tracker.sources[0]["id"] == 1
        assert tracker.sources[9]["id"] == 10
