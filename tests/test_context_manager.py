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
        """Test basic field reduction (Tier 1)."""
        articles = [
            {
                "title": "Tesla Stock Rises",
                "source": "Reuters",
                "url": "https://example.com/1",
                "published_at": "2026-05-23",
                "description": "Long description here...",
                "content": "Full article content...",
                "api_source": "newsapi"
            },
            {
                "title": "Ford Announces EV",
                "source": "Bloomberg",
                "url": "https://example.com/2",
                "published_at": "2026-05-22",
                "description": "Another description...",
                "content": "More content...",
                "api_source": "finnhub"
            }
        ]

        result = compress_tool_result(articles, aggressive=False)

        assert len(result) == 2
        assert result[0] == {
            "id": 1,
            "title": "Tesla Stock Rises",
            "source": "Reuters",
            "url": "https://example.com/1",
            "published_at": "2026-05-23"
        }
        assert "description" not in result[0]
        assert "content" not in result[0]
        assert "api_source" not in result[0]

    def test_compress_aggressive(self):
        """Test aggressive compression (Tier 2: limit articles)."""
        articles = [{"title": f"Article {i}", "source": "Test", "url": f"url{i}", "published_at": "2026-05-23"}
                    for i in range(20)]

        result = compress_tool_result(articles, aggressive=True)

        assert len(result) == 10  # Limited to 10 articles
        assert result[0]["title"] == "Article 0"
        assert result[9]["title"] == "Article 9"

    def test_compress_empty_list(self):
        """Test compression with empty list."""
        result = compress_tool_result([], aggressive=False)
        assert result == []

    def test_compress_missing_fields(self):
        """Test compression handles missing fields gracefully."""
        articles = [{"title": "Test"}]  # Missing other fields

        result = compress_tool_result(articles, aggressive=False)

        assert len(result) == 1
        assert result[0] == {
            "id": 1,
            "title": "Test",
            "source": "",
            "url": "",
            "published_at": ""
        }


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
