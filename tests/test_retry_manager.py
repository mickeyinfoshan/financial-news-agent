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

    def test_should_retry_with_invalid_citations(self):
        """Test retry is triggered when citations are invalid."""
        config = RetryConfig()

        # Good evaluation scores but invalid citations
        evaluation = {
            "accuracy": 8,
            "relevance": 8,
            "coherence": 8,
            "reasonableness": 8,
            "overall": 8.0,
            "feedback": "Good answer"
        }

        citation_validation = {
            "claims": [],
            "extraction_attempts": 1,
            "total_invalid_citations": 2,
            "validation_passed": False
        }

        # Should retry despite good scores
        assert config.should_retry(evaluation, 0, citation_validation) is True

    def test_should_not_retry_with_valid_citations(self):
        """Test retry is not triggered when citations are valid and scores are good."""
        config = RetryConfig()

        evaluation = {
            "accuracy": 8,
            "relevance": 8,
            "coherence": 8,
            "reasonableness": 8,
            "overall": 8.0,
            "feedback": "Good answer"
        }

        citation_validation = {
            "claims": [],
            "extraction_attempts": 1,
            "total_invalid_citations": 0,
            "validation_passed": True
        }

        # Should not retry with good scores and valid citations
        assert config.should_retry(evaluation, 0, citation_validation) is False

    def test_should_not_retry_invalid_citations_max_attempts(self):
        """Test retry is not triggered when max attempts reached even with invalid citations."""
        config = RetryConfig()
        config.max_attempts = 1

        evaluation = {"overall": 8.0, "accuracy": 8.0}
        citation_validation = {"validation_passed": False, "total_invalid_citations": 2}

        # Should not retry when max attempts reached
        assert config.should_retry(evaluation, 1, citation_validation) is False

    def test_should_not_retry_invalid_citations_when_disabled(self):
        """Test retry is not triggered when disabled even with invalid citations."""
        config = RetryConfig()
        config.enabled = False

        evaluation = {"overall": 8.0, "accuracy": 8.0}
        citation_validation = {"validation_passed": False, "total_invalid_citations": 2}

        # Should not retry when disabled
        assert config.should_retry(evaluation, 0, citation_validation) is False


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

    def test_strategy_fix_with_citation_failure(self):
        """Test FIX strategy is used when citation validation fails."""
        config = RetryConfig()

        # Good scores but invalid citations
        evaluation = {
            "accuracy": 8,
            "relevance": 8,
            "coherence": 8,
            "reasonableness": 8,
            "overall": 8.0,
            "feedback": "Good answer"
        }

        citation_validation = {
            "validation_passed": False,
            "total_invalid_citations": 1,
            "claims": []
        }

        sources = [{"title": "test"}]

        strategy = decide_retry_strategy(evaluation, sources, config, citation_validation)
        assert strategy == "fix"

    def test_strategy_fix_citation_failure_overrides_redo(self):
        """Test citation failure uses FIX even when scores would suggest REDO."""
        config = RetryConfig()

        # Low accuracy would normally trigger REDO
        evaluation = {
            "accuracy": 4,
            "relevance": 7,
            "coherence": 7,
            "reasonableness": 7,
            "overall": 6.25,
            "feedback": "Low accuracy"
        }

        citation_validation = {
            "validation_passed": False,
            "total_invalid_citations": 2,
            "claims": []
        }

        sources = [{"title": "test"}]

        # Citation failure should use FIX, not REDO
        strategy = decide_retry_strategy(evaluation, sources, config, citation_validation)
        assert strategy == "fix"


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

    def test_fix_prompt_with_citation_issues(self):
        """Test fix prompt includes citation-specific guidance when validation fails."""
        evaluation = {
            "accuracy": 7.0,
            "relevance": 7.0,
            "coherence": 7.0,
            "reasonableness": 7.0,
            "feedback": "Good content but citation issues"
        }

        citation_validation = {
            "validation_passed": False,
            "total_invalid_citations": 2,
            "claims": [
                {
                    "claim": "Test claim",
                    "citations": [1],
                    "invalid_citations": [],
                    "validation_result": {"supported": False, "confidence": "high", "explanation": "Not supported"}
                }
            ]
        }

        query = "Test query"

        prompt = build_fix_prompt(evaluation, query, citation_validation)

        # Should include citation-specific guidance with claim-level details
        assert "UNSUPPORTED CLAIMS" in prompt
        assert "Test claim" in prompt  # Should include the actual claim text
        assert "Not supported" in prompt  # Should include the explanation
        assert "CRITICAL" in prompt

    def test_fix_prompt_without_citation_issues(self):
        """Test fix prompt works normally when citations are valid."""
        evaluation = {
            "accuracy": 6.0,
            "relevance": 6.0,
            "coherence": 5.0,
            "reasonableness": 5.0,
            "feedback": "Needs improvement"
        }

        citation_validation = {
            "validation_passed": True,
            "total_invalid_citations": 0,
            "claims": []
        }

        query = "Test query"

        prompt = build_fix_prompt(evaluation, query, citation_validation)

        # Should not include citation-specific guidance
        assert "CITATION ISSUES DETECTED" not in prompt
        assert "CRITICAL" not in prompt


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
