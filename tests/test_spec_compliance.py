"""Test compliance with challenge spec requirements."""

import os

import pytest

from qa_chain import answer_question


class TestSpecCompliance:
    """Test that the application meets the challenge spec requirements."""

    def test_function_signature(self):
        """Test 1: Function accepts two inputs - question and context."""
        # Should be callable with just two string parameters
        assert callable(answer_question)

        # Verify function can be imported and has correct signature
        import inspect

        sig = inspect.signature(answer_question)
        params = list(sig.parameters.keys())

        # First two parameters should be question and context
        assert params[0] == "question"
        assert params[1] == "context"

        # Config should be optional (has default of None)
        assert sig.parameters["config"].default is None

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ, reason="needs OPENAI_API_KEY"
    )
    def test_basic_usage(self):
        """Test 2: Function integrates LLM and returns answer."""
        # Most basic usage - just question and context
        question = "What color is the sky?"
        context = "The sky appears blue during the day due to light scattering."

        # Should return a string answer
        answer = answer_question(question, context)
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_preprocessing_happens(self):
        """Test 3: Input preprocessing improves understanding."""
        # Preprocessing is comprehensively tested in test_preprocessing.py
        # This test verifies that preprocessing is part of the design

        # Check that preprocessing functions exist
        from qa_chain.chain import _normalize_text, _preprocess

        # Verify these are callable (they handle preprocessing)
        assert callable(_normalize_text)
        assert callable(_preprocess)

        # The actual preprocessing tests are in test_preprocessing.py

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ, reason="needs OPENAI_API_KEY"
    )
    def test_formatted_output(self):
        """Test 4: Output is formatted as answer."""
        question = "What is mentioned in the context?"
        context = "The Eiffel Tower is in Paris."

        answer = answer_question(question, context)

        # Should be a formatted string answer
        assert isinstance(answer, str)
        # Should not be empty
        assert len(answer.strip()) > 0
        # Should be clean text (no extra formatting)
        assert answer == answer.strip()

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ, reason="needs OPENAI_API_KEY"
    )
    def test_context_only_answer(self):
        """Test that model uses only provided context as per spec."""
        question = "What is the capital of Germany?"
        context = "France is a country in Europe. Its capital is Paris."

        answer = answer_question(question, context)

        # Should indicate it doesn't know (not in context)
        assert "don't know" in answer.lower() or "not" in answer.lower()


def test_minimal_imports():
    """Verify the function can be used with minimal imports."""
    # Should be able to import just the function
    from qa_chain import answer_question as qa_func

    assert callable(qa_func)

    # Should work without explicitly importing config
    import inspect

    sig = inspect.signature(qa_func)
    assert "config" in sig.parameters
    assert sig.parameters["config"].default is None
