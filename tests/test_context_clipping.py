"""Test context clipping functionality."""

from qa_chain.chain import _clip_context


def test_clip_context_short():
    """Test clipping doesn't affect short contexts."""
    context = "This is a short context."
    result = _clip_context(context, 1000)
    assert result == context


def test_clip_context_long_with_sentence():
    """Test clipping finds sentence boundary."""
    context = "A" * 100 + ". This is a sentence. " + "B" * 100
    result = _clip_context(context, 150)
    # Should clip at the sentence boundary
    assert result == "A" * 100 + ". This is a sentence."


def test_clip_context_long_no_sentence():
    """Test clipping when no sentence boundary found."""
    context = "A" * 300
    result = _clip_context(context, 200)
    assert len(result) == 200
    assert result == "A" * 200


def test_clip_context_with_multiple_terminators():
    """Test clipping with different sentence terminators."""
    context = "First sentence! Second sentence? Third sentence. " + "X" * 200
    result = _clip_context(context, 100)
    # Should keep up to "Third sentence."
    assert result.endswith(".")
    assert "Third sentence." in result
