"""Unit tests for context_manager module."""

from unittest.mock import Mock, patch

from financial_news_agent.context_manager import (
    compress_tool_result,
    summarize_history,
    manage_context,
    load_config
)


class TestCompressToolResult:
    """Tests for compress_tool_result function."""

    def test_compress_basic(self):
        """Test basic field reduction (Tier 1) - keeps id, title, summary, source, url, date."""
        sources = [
            {
                "id": 1,
                "title": "Tesla Stock Rises",
                "date": "2026-05-23",
                "source": "Reuters",
                "url": "https://example.com/1",
                "summary": "Tesla stock increased 5% following strong earnings report.",
                "api_source": "newsapi"
            },
            {
                "id": 2,
                "title": "Ford Announces EV",
                "date": "2026-05-22",
                "source": "Bloomberg",
                "url": "https://example.com/2",
                "summary": "Ford unveiled new electric vehicle lineup for 2027.",
                "api_source": "finnhub"
            }
        ]

        result = compress_tool_result(sources, aggressive=False)

        assert len(result) == 2
        assert result[0] == {
            "id": 1,
            "title": "Tesla Stock Rises",
            "summary": "Tesla stock increased 5% following strong earnings report.",
            "source": "Reuters",
            "url": "https://example.com/1",
            "published_at": "2026-05-23"
        }
        assert result[1] == {
            "id": 2,
            "title": "Ford Announces EV",
            "summary": "Ford unveiled new electric vehicle lineup for 2027.",
            "source": "Bloomberg",
            "url": "https://example.com/2",
            "published_at": "2026-05-22"
        }
        # api_source should be removed
        assert "api_source" not in result[0]
        assert "api_source" not in result[1]

    def test_compress_aggressive(self):
        """Test aggressive compression (Tier 2: limit sources to 10)."""
        sources = [
            {
                "id": i + 1,
                "title": f"Article {i}",
                "date": "2026-05-23",
                "source": "Test",
                "url": f"url{i}",
                "summary": f"Summary {i}",
                "api_source": "test"
            }
            for i in range(20)
        ]

        result = compress_tool_result(sources, aggressive=True)

        assert len(result) == 10  # Limited to 10 sources
        assert result[0]["title"] == "Article 0"
        assert result[0]["id"] == 1
        assert result[9]["title"] == "Article 9"
        assert result[9]["id"] == 10

    def test_compress_empty_list(self):
        """Test compression with empty list."""
        result = compress_tool_result([], aggressive=False)
        assert result == []

    def test_compress_missing_fields(self):
        """Test compression handles missing fields gracefully."""
        sources = [
            {
                "id": 1,
                "title": "Test"
                # Missing other fields
            }
        ]

        result = compress_tool_result(sources, aggressive=False)

        assert len(result) == 1
        assert result[0] == {
            "id": 1,
            "title": "Test",
            "summary": "",
            "source": "",
            "url": "",
            "published_at": ""
        }

    def test_compress_includes_summary(self):
        """Test that summary field is included for LLM analysis."""
        sources = [
            {
                "id": 1,
                "title": "Tesla Earnings Beat Expectations",
                "date": "2026-05-27",
                "source": "Reuters",
                "url": "https://example.com/tesla",
                "summary": "Tesla reported Q1 earnings of $2.50 per share, beating analyst expectations of $2.20.",
                "api_source": "newsapi"
            }
        ]

        result = compress_tool_result(sources, aggressive=False)

        assert len(result) == 1
        assert "summary" in result[0]
        assert result[0]["summary"] == "Tesla reported Q1 earnings of $2.50 per share, beating analyst expectations of $2.20."

    def test_compress_preserves_ids(self):
        """Test that source IDs are preserved in compression."""
        sources = [
            {
                "id": 5,
                "title": "Article 1",
                "date": "2026-05-27",
                "source": "Source A",
                "url": "https://example.com/1",
                "summary": "Summary 1",
                "api_source": "test"
            },
            {
                "id": 6,
                "title": "Article 2",
                "date": "2026-05-26",
                "source": "Source B",
                "url": "https://example.com/2",
                "summary": "Summary 2",
                "api_source": "test"
            }
        ]

        result = compress_tool_result(sources, aggressive=False)

        assert result[0]["id"] == 5
        assert result[1]["id"] == 6

    def test_compress_maps_date_to_published_at(self):
        """Test that 'date' field is mapped to 'published_at' in output."""
        sources = [
            {
                "id": 1,
                "title": "Test Article",
                "date": "2026-05-27T10:30:00",
                "source": "Test Source",
                "url": "https://example.com/test",
                "summary": "Test summary",
                "api_source": "test"
            }
        ]

        result = compress_tool_result(sources, aggressive=False)

        assert "date" not in result[0]
        assert "published_at" in result[0]
        assert result[0]["published_at"] == "2026-05-27T10:30:00"


class TestSummarizeHistory:
    """Tests for summarize_history function."""

    def test_summarize_success(self):
        """Test successful summarization."""
        messages = [
            {"role": "system", "content": "You are a financial agent"},
            {"role": "user", "content": "Tell me about Tesla"},
            {"role": "assistant", "content": "Let me search for Tesla news"},
            {"role": "tool", "content": "Tool results..."},
            {"role": "assistant", "content": "Here's what I found about Tesla"},
            {"role": "user", "content": "What about Ford?"},
            {"role": "assistant", "content": "Searching for Ford news"},
            {"role": "tool", "content": "More tool results..."}
        ]

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Summary of conversation about Tesla and Ford"))]
        mock_client.chat.completions.create.return_value = mock_response

        result = summarize_history(messages, mock_client, recent_count=2)

        assert result == "Summary of conversation about Tesla and Ford"
        assert mock_client.chat.completions.create.called

    def test_summarize_not_enough_messages(self):
        """Test when there aren't enough messages to summarize."""
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"}
        ]

        mock_client = Mock()
        result = summarize_history(messages, mock_client, recent_count=4)

        assert result == ""
        assert not mock_client.chat.completions.create.called

    def test_summarize_api_error(self):
        """Test handling of API errors during summarization."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
            {"role": "user", "content": "Q3"}
        ]

        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        result = summarize_history(messages, mock_client, recent_count=2)

        assert result == ""  # Returns empty string on error


class TestManageContext:
    """Tests for manage_context function."""

    def test_manage_context_below_threshold(self):
        """Test no action when below thresholds."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"}
        ]

        mock_client = Mock()
        config = {
            "token_threshold": 12000,
            "message_threshold": 15,
            "recent_messages": 4,
            "enable_compression": True
        }

        result = manage_context(messages, total_tokens=5000, client=mock_client, config=config)

        assert result == messages  # No changes
        assert not mock_client.chat.completions.create.called

    def test_manage_context_token_threshold_exceeded(self):
        """Test summarization when token threshold exceeded."""
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
            {"role": "user", "content": "Q3"},
            {"role": "assistant", "content": "A3"}
        ]

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Summary of Q1 and Q2"))]
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "token_threshold": 10000,
            "message_threshold": 20,
            "recent_messages": 2,
            "enable_compression": True
        }

        result = manage_context(messages, total_tokens=12000, client=mock_client, config=config)

        # Should have: system + summary + 2 recent messages
        assert len(result) == 4
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "system"
        assert "Previous conversation summary" in result[1]["content"]
        assert result[2] == messages[-2]  # Second to last
        assert result[3] == messages[-1]  # Last

    def test_manage_context_message_threshold_exceeded(self):
        """Test summarization when message threshold exceeded."""
        messages = [{"role": "system", "content": "System"}]
        messages.extend([{"role": "user", "content": f"Q{i}"} for i in range(20)])

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Summary"))]
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "token_threshold": 50000,
            "message_threshold": 15,
            "recent_messages": 4,
            "enable_compression": True
        }

        result = manage_context(messages, total_tokens=5000, client=mock_client, config=config)

        assert len(result) < len(messages)
        assert mock_client.chat.completions.create.called

    def test_manage_context_compression_disabled(self):
        """Test that compression can be disabled."""
        messages = [{"role": "system", "content": "System"}]
        messages.extend([{"role": "user", "content": f"Q{i}"} for i in range(20)])

        mock_client = Mock()
        config = {
            "token_threshold": 10000,
            "message_threshold": 15,
            "recent_messages": 4,
            "enable_compression": False  # Disabled
        }

        result = manage_context(messages, total_tokens=15000, client=mock_client, config=config)

        assert result == messages  # No changes
        assert not mock_client.chat.completions.create.called

    def test_manage_context_preserves_system_message(self):
        """Test that system message is always preserved."""
        messages = [
            {"role": "system", "content": "Important system message"},
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
            {"role": "user", "content": "Q3"}
        ]

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Summary"))]
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "token_threshold": 5000,
            "message_threshold": 5,
            "recent_messages": 2,
            "enable_compression": True
        }

        result = manage_context(messages, total_tokens=10000, client=mock_client, config=config)

        assert result[0] == messages[0]  # System message preserved
        assert result[0]["content"] == "Important system message"


class TestLoadConfig:
    """Tests for load_config function."""

    @patch.dict('os.environ', {
        'CONTEXT_TOKEN_THRESHOLD': '15000',
        'CONTEXT_MESSAGE_THRESHOLD': '20',
        'CONTEXT_RECENT_MESSAGES': '5',
        'CONTEXT_WARNING_THRESHOLD': '10000',
        'CONTEXT_MAX_ARTICLES': '8',
        'CONTEXT_ENABLE_COMPRESSION': 'false'
    })
    def test_load_config_from_env(self):
        """Test loading config from environment variables."""
        config = load_config()

        assert config["token_threshold"] == 15000
        assert config["message_threshold"] == 20
        assert config["recent_messages"] == 5
        assert config["warning_threshold"] == 10000
        assert config["max_articles"] == 8
        assert config["enable_compression"] is False

    @patch.dict('os.environ', {}, clear=True)
    def test_load_config_defaults(self):
        """Test default config values."""
        config = load_config()

        assert config["token_threshold"] == 600000
        assert config["message_threshold"] == 100
        assert config["recent_messages"] == 20
        assert config["warning_threshold"] == 400000
        assert config["max_articles"] == 10
        assert config["enable_compression"] is True
