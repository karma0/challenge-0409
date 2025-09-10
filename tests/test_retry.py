"""Tests for retry functionality."""

from unittest.mock import MagicMock

import pytest

from qa_chain.retry import (
    RetryError,
    RetryPolicy,
    exponential_backoff,
    is_retriable_error,
    retry_with_exponential_backoff,
)


class TestExponentialBackoff:
    """Test exponential backoff calculation."""

    def test_basic_backoff(self):
        """Test basic exponential backoff."""
        assert exponential_backoff(0, base_delay=1.0, jitter=False) == 1.0
        assert exponential_backoff(1, base_delay=1.0, jitter=False) == 2.0
        assert exponential_backoff(2, base_delay=1.0, jitter=False) == 4.0
        assert exponential_backoff(3, base_delay=1.0, jitter=False) == 8.0

    def test_max_delay(self):
        """Test that backoff is capped at max_delay."""
        assert (
            exponential_backoff(10, base_delay=1.0, max_delay=5.0, jitter=False) == 5.0
        )

    def test_jitter(self):
        """Test that jitter adds randomness."""
        # Without jitter, delays should be consistent
        delay1 = exponential_backoff(2, base_delay=1.0, jitter=False)
        delay2 = exponential_backoff(2, base_delay=1.0, jitter=False)
        assert delay1 == delay2 == 4.0

        # With jitter, delays should vary
        delays_with_jitter = [
            exponential_backoff(2, base_delay=1.0, jitter=True) for _ in range(10)
        ]
        # All should be between 4.0 and 5.0 (4.0 + up to 25% jitter)
        assert all(4.0 <= d <= 5.0 for d in delays_with_jitter)
        # Should have some variation
        assert len(set(delays_with_jitter)) > 1


class TestRetriableError:
    """Test retriable error detection."""

    def test_known_retriable_exceptions(self):
        """Test that known exceptions are retriable."""
        assert is_retriable_error(ConnectionError("Connection failed"))
        assert is_retriable_error(TimeoutError("Timeout"))
        assert is_retriable_error(IOError("IO Error"))

    def test_retriable_error_messages(self):
        """Test that certain error messages trigger retry."""
        assert is_retriable_error(Exception("rate limit exceeded"))
        assert is_retriable_error(Exception("Connection timeout"))
        assert is_retriable_error(Exception("Service temporarily unavailable"))
        assert is_retriable_error(Exception("502 Bad Gateway"))

    def test_non_retriable_errors(self):
        """Test that some errors are not retriable."""
        assert not is_retriable_error(ValueError("Invalid value"))
        assert not is_retriable_error(KeyError("Missing key"))
        assert not is_retriable_error(Exception("Authentication failed"))

    def test_api_error_with_status_code(self):
        """Test API errors with status codes."""
        # Mock an API error with response
        error = Exception("API Error")
        error.response = MagicMock()

        # Retriable status codes
        for code in [429, 500, 502, 503, 504]:
            error.response.status_code = code
            assert is_retriable_error(error)

        # Non-retriable status codes
        for code in [400, 401, 403, 404]:
            error.response.status_code = code
            assert not is_retriable_error(error)


class TestRetryDecorator:
    """Test retry decorator functionality."""

    def test_successful_first_attempt(self):
        """Test function that succeeds on first try."""
        mock_func = MagicMock(return_value="success")

        @retry_with_exponential_backoff(max_attempts=3)
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_failure(self):
        """Test function that fails then succeeds."""
        mock_func = MagicMock(
            side_effect=[
                ConnectionError("Failed"),
                ConnectionError("Failed"),
                "success",
            ]
        )

        @retry_with_exponential_backoff(max_attempts=3, base_delay=0.01)
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 3

    def test_exhaust_retries(self):
        """Test function that exhausts all retries."""
        mock_func = MagicMock(side_effect=ConnectionError("Always fails"))

        @retry_with_exponential_backoff(max_attempts=3, base_delay=0.01)
        def test_func():
            return mock_func()

        with pytest.raises(RetryError) as exc_info:
            test_func()

        assert "Failed after 3 attempts" in str(exc_info.value)
        assert mock_func.call_count == 3

    def test_non_retriable_error(self):
        """Test that non-retriable errors are raised immediately."""
        mock_func = MagicMock(side_effect=ValueError("Bad value"))

        @retry_with_exponential_backoff(max_attempts=3)
        def test_func():
            return mock_func()

        with pytest.raises(ValueError):
            test_func()

        # Should only try once
        assert mock_func.call_count == 1

    def test_custom_retriable_exceptions(self):
        """Test custom retriable exceptions."""

        class CustomError(Exception):
            pass

        mock_func = MagicMock(side_effect=[CustomError("Failed"), "success"])

        @retry_with_exponential_backoff(
            max_attempts=3, base_delay=0.01, retriable_exceptions=(CustomError,)
        )
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2

    def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        callback_mock = MagicMock()
        mock_func = MagicMock(side_effect=[ConnectionError("Failed"), "success"])

        @retry_with_exponential_backoff(
            max_attempts=3, base_delay=0.01, on_retry=callback_mock
        )
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert callback_mock.call_count == 1

        # Check callback was called with error and attempt number
        call_args = callback_mock.call_args[0]
        assert isinstance(call_args[0], ConnectionError)
        assert call_args[1] == 1  # First retry


class TestRetryPolicy:
    """Test RetryPolicy class."""

    def test_default_policy(self):
        """Test default retry policy."""
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.jitter is True

    def test_custom_policy(self):
        """Test custom retry policy."""
        policy = RetryPolicy(
            max_attempts=5, base_delay=2.0, max_delay=120.0, jitter=False
        )
        assert policy.max_attempts == 5
        assert policy.base_delay == 2.0
        assert policy.max_delay == 120.0
        assert policy.jitter is False

    def test_should_retry(self):
        """Test should_retry logic."""
        policy = RetryPolicy(max_attempts=3)

        # Should retry on retriable errors
        error = ConnectionError("Failed")
        assert policy.should_retry(error, attempt=1)
        assert policy.should_retry(error, attempt=2)
        assert not policy.should_retry(error, attempt=3)  # Max attempts reached

        # Should not retry on non-retriable errors
        error = ValueError("Bad value")
        assert not policy.should_retry(error, attempt=1)

    def test_get_delay(self):
        """Test delay calculation."""
        policy = RetryPolicy(base_delay=2.0, jitter=False)

        assert policy.get_delay(0) == 2.0
        assert policy.get_delay(1) == 4.0
        assert policy.get_delay(2) == 8.0

    def test_as_decorator(self):
        """Test converting policy to decorator."""
        policy = RetryPolicy(max_attempts=2, base_delay=0.01)
        mock_func = MagicMock(side_effect=[ConnectionError("Failed"), "success"])

        @policy.as_decorator()
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2


class TestRetryWithChain:
    """Test retry with actual chain-like behavior."""

    def test_chain_retry_integration(self):
        """Test retry with a mock chain."""
        # Mock a chain that fails twice then succeeds
        mock_chain = MagicMock()
        mock_chain.invoke = MagicMock(
            side_effect=[
                ConnectionError("API unavailable"),
                TimeoutError("Request timed out"),
                "The answer is 42",
            ]
        )

        policy = RetryPolicy(max_attempts=3, base_delay=0.01)

        @policy.as_decorator()
        def invoke_chain(inputs):
            return mock_chain.invoke(inputs)

        result = invoke_chain({"question": "What is the answer?", "context": "42"})
        assert result == "The answer is 42"
        assert mock_chain.invoke.call_count == 3

    def test_chain_non_retriable_error(self):
        """Test chain with non-retriable error."""
        mock_chain = MagicMock()
        mock_chain.invoke = MagicMock(
            side_effect=ValueError("Invalid model configuration")
        )

        policy = RetryPolicy(max_attempts=3)

        @policy.as_decorator()
        def invoke_chain(inputs):
            return mock_chain.invoke(inputs)

        with pytest.raises(ValueError):
            invoke_chain({"question": "Test", "context": "Test"})

        # Should not retry on ValueError
        assert mock_chain.invoke.call_count == 1
