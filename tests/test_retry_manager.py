"""Tests for retry_manager module."""

from financial_news_agent.retry_manager import (
    RetryConfig,
    decide_retry_strategy,
    build_fix_prompt,
    build_redo_prompt
)


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.enabled is True
        assert config.threshold_overall == 6.0
        assert config.threshold_accuracy == 5.0
        assert config.max_attempts == 1
        assert config.strategy == "auto"
        assert config.show_attempts is True

    def test_should_retry_below_threshold(self):
        """Test retry is triggered when score is below threshold."""
        config = RetryConfig()
        evaluation = {"overall": 5.0, "accuracy": 7.0}

        assert config.should_retry(evaluation, 0) is True

    def test_should_retry_low_accuracy(self):
        """Test retry is triggered when accuracy is low."""
        config = RetryConfig()
        evaluation = {"overall": 7.0, "accuracy": 4.0}

        assert config.should_retry(evaluation, 0) is True

    def test_should_not_retry_above_threshold(self):
        """Test retry is not triggered when scores are good."""
        config = RetryConfig()
        evaluation = {"overall": 8.0, "accuracy": 8.0}

        assert config.should_retry(evaluation, 0) is False

    def test_should_not_retry_max_attempts(self):
        """Test retry is not triggered when max attempts reached."""
        config = RetryConfig()
        config.max_attempts = 1
        evaluation = {"overall": 4.0, "accuracy": 4.0}

        # First attempt should allow retry
        assert config.should_retry(evaluation, 0) is True
        # Second attempt should not allow retry (max reached)
        assert config.should_retry(evaluation, 1) is False

    def test_should_not_retry_when_disabled(self):
        """Test retry is not triggered when disabled."""
        config = RetryConfig()
        config.enabled = False
        evaluation = {"overall": 3.0, "accuracy": 3.0}

        assert config.should_retry(evaluation, 0) is False


class TestDecideRetryStrategy:
    """Tests for decide_retry_strategy function."""

    def test_strategy_none_good_scores(self):
        """Test no retry when scores are good."""
        config = RetryConfig()
        evaluation = {"overall": 8.0, "accuracy": 8.0, "relevance": 8.0}
        sources = [{"title": "test"}]

        strategy = decide_retry_strategy(evaluation, sources, config)
        assert strategy == "none"

    def test_strategy_redo_low_accuracy(self):
        """Test REDO strategy for low accuracy."""
        config = RetryConfig()
        evaluation = {"overall": 5.0, "accuracy": 4.0, "relevance": 7.0}
        sources = [{"title": "test"}]

        strategy = decide_retry_strategy(evaluation, sources, config)
        assert strategy == "redo"

    def test_strategy_redo_low_relevance(self):
        """Test REDO strategy for low relevance."""
        config = RetryConfig()
        evaluation = {"overall": 5.0, "accuracy": 7.0, "relevance": 3.0}
        sources = [{"title": "test"}]

        strategy = decide_retry_strategy(evaluation, sources, config)
        assert strategy == "redo"

    def test_strategy_redo_no_sources(self):
        """Test REDO strategy when no sources found."""
        config = RetryConfig()
        evaluation = {"overall": 5.0, "accuracy": 7.0, "relevance": 7.0}
        sources = []

        strategy = decide_retry_strategy(evaluation, sources, config)
        assert strategy == "redo"

    def test_strategy_fix_low_coherence(self):
        """Test FIX strategy for low coherence but good accuracy."""
        config = RetryConfig()
        evaluation = {"overall": 5.5, "accuracy": 7.0, "relevance": 7.0, "coherence": 4.0}
        sources = [{"title": "test"}]

        strategy = decide_retry_strategy(evaluation, sources, config)
        assert strategy == "fix"

    def test_strategy_fix_moderate_issues(self):
        """Test FIX strategy for moderate issues."""
        config = RetryConfig()
        evaluation = {"overall": 5.8, "accuracy": 6.0, "relevance": 6.0}
        sources = [{"title": "test"}]

        strategy = decide_retry_strategy(evaluation, sources, config)
        assert strategy == "fix"

    def test_strategy_manual_override_fix(self):
        """Test manual override to always fix."""
        config = RetryConfig()
        config.strategy = "fix"
        evaluation = {"overall": 3.0, "accuracy": 3.0, "relevance": 3.0}
        sources = []

        strategy = decide_retry_strategy(evaluation, sources, config)
        assert strategy == "fix"

    def test_strategy_manual_override_redo(self):
        """Test manual override to always redo."""
        config = RetryConfig()
        config.strategy = "redo"
        evaluation = {"overall": 8.0, "accuracy": 8.0, "relevance": 8.0}
        sources = [{"title": "test"}]

        strategy = decide_retry_strategy(evaluation, sources, config)
        assert strategy == "redo"

    def test_strategy_manual_override_disabled(self):
        """Test manual override to disable retry."""
        config = RetryConfig()
        config.strategy = "disabled"
        evaluation = {"overall": 3.0, "accuracy": 3.0, "relevance": 3.0}
        sources = []

        strategy = decide_retry_strategy(evaluation, sources, config)
        assert strategy == "none"


class TestBuildFixPrompt:
    """Tests for build_fix_prompt function."""

    def test_fix_prompt_contains_scores(self):
        """Test fix prompt includes evaluation scores."""
        evaluation = {
            "accuracy": 6.0,
            "relevance": 7.0,
            "coherence": 4.0,
            "reasonableness": 5.0,
            "feedback": "Storyline lacks coherence"
        }
        query = "What is the latest news about Tesla?"

        prompt = build_fix_prompt(evaluation, query)

        assert "6.0" in prompt or "6/10" in prompt
        assert "4.0" in prompt or "4/10" in prompt
        assert "coherence" in prompt.lower()
        assert query in prompt

    def test_fix_prompt_identifies_weak_areas(self):
        """Test fix prompt identifies weak areas."""
        evaluation = {
            "accuracy": 7.0,
            "relevance": 7.0,
            "coherence": 4.0,
            "reasonableness": 5.0,
            "feedback": "Issues with coherence and reasonableness"
        }
        query = "Test query"

        prompt = build_fix_prompt(evaluation, query)

        assert "coherence" in prompt.lower()
        assert "reasonableness" in prompt.lower()

    def test_fix_prompt_includes_feedback(self):
        """Test fix prompt includes evaluation feedback."""
        evaluation = {
            "accuracy": 6.0,
            "relevance": 6.0,
            "coherence": 5.0,
            "reasonableness": 5.0,
            "feedback": "Specific feedback about the issues"
        }
        query = "Test query"

        prompt = build_fix_prompt(evaluation, query)

        assert "Specific feedback about the issues" in prompt


class TestBuildRedoPrompt:
    """Tests for build_redo_prompt function."""

    def test_redo_prompt_contains_feedback(self):
        """Test redo prompt includes evaluation feedback."""
        evaluation = {
            "feedback": "Sources are not relevant to the query"
        }
        query = "What is the latest news about Apple?"

        prompt = build_redo_prompt(evaluation, query)

        assert "Sources are not relevant to the query" in prompt
        assert query in prompt

    def test_redo_prompt_instructs_new_search(self):
        """Test redo prompt instructs to search again."""
        evaluation = {
            "feedback": "Low accuracy"
        }
        query = "Test query"

        prompt = build_redo_prompt(evaluation, query)

        assert "search" in prompt.lower() or "fresh" in prompt.lower()
        assert query in prompt
