"""Test preprocessing functionality."""

import pytest

from qa_chain import QAConfig, answer_question


def test_preprocessing_smart_quotes():
    """Test smart quotes are converted to regular quotes."""
    context = 'The author said "Hello world!" and left.'
    question = "What did the author say?"
    config = QAConfig(temperature=0.0)

    # Should handle smart quotes without error
    answer = answer_question(question, context, config)
    assert isinstance(answer, str)


def test_preprocessing_whitespace():
    """Test extra whitespace is normalized."""
    context = "   Paris    is   the   capital   of   France.   "
    question = "  What   is   the   capital   of   France?  "
    config = QAConfig(temperature=0.0)

    answer = answer_question(question, context, config)
    assert "Paris" in answer


def test_config_defaults():
    """Test QAConfig defaults work correctly."""
    config = QAConfig()
    assert config.model == "gpt-4o-mini"
    assert config.temperature == 0.2
    assert config.max_context_chars == 6000


def test_config_custom_values():
    """Test QAConfig accepts custom values."""
    config = QAConfig(model="gpt-4", temperature=0.5, max_context_chars=3000)
    assert config.model == "gpt-4"
    assert config.temperature == 0.5
    assert config.max_context_chars == 3000


def test_answer_no_context():
    """Test behavior when answer not in context."""
    context = "Paris is the capital of France."
    question = "What is the capital of Germany?"
    config = QAConfig(temperature=0.0)

    answer = answer_question(question, context, config)
    # Should indicate it doesn't know based on the context
    assert "don't know" in answer.lower() or "not" in answer.lower()


def test_empty_inputs():
    """Test handling of empty inputs."""
    from qa_chain import SecurityError

    config = QAConfig(temperature=0.0)

    # Empty question should raise SecurityError
    with pytest.raises(SecurityError):
        answer_question("", "Some context", config)

    # Empty context should work (returns "don't know")
    answer = answer_question("Some question", "", config)
    assert isinstance(answer, str)
