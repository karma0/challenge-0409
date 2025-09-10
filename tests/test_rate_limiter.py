"""Test rate limiting functionality."""

import time
from threading import Thread

import pytest

from qa_chain import SecurityError
from qa_chain.rate_limiter import RateLimiter, check_rate_limit


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)

        # First two requests should pass
        assert limiter.is_allowed("user1")[0] is True
        assert limiter.is_allowed("user1")[0] is True

        # Third request should fail
        allowed, retry_after = limiter.is_allowed("user1")
        assert allowed is False
        assert retry_after is not None
        assert 0 < retry_after <= 1

    def test_window_expiry(self):
        """Test that old requests expire from the window."""
        limiter = RateLimiter(max_requests=1, window_seconds=0.1)

        # First request passes
        assert limiter.is_allowed("user1")[0] is True

        # Second request fails
        assert limiter.is_allowed("user1")[0] is False

        # Wait for window to expire
        time.sleep(0.15)

        # Request should pass again
        assert limiter.is_allowed("user1")[0] is True

    def test_different_identifiers(self):
        """Test that different identifiers are tracked separately."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # Each user gets their own limit
        assert limiter.is_allowed("user1")[0] is True
        assert limiter.is_allowed("user2")[0] is True

        # But second request for each fails
        assert limiter.is_allowed("user1")[0] is False
        assert limiter.is_allowed("user2")[0] is False

    def test_reset_specific_identifier(self):
        """Test resetting a specific identifier."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # Use up the limit
        assert limiter.is_allowed("user1")[0] is True
        assert limiter.is_allowed("user1")[0] is False

        # Reset this specific user
        limiter.reset("user1")

        # Should be allowed again
        assert limiter.is_allowed("user1")[0] is True

    def test_reset_all(self):
        """Test resetting all rate limits."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # Use up limits for multiple users
        assert limiter.is_allowed("user1")[0] is True
        assert limiter.is_allowed("user2")[0] is True
        assert limiter.is_allowed("user1")[0] is False
        assert limiter.is_allowed("user2")[0] is False

        # Reset all
        limiter.reset()

        # Both should be allowed again
        assert limiter.is_allowed("user1")[0] is True
        assert limiter.is_allowed("user2")[0] is True

    def test_thread_safety(self):
        """Test that rate limiter is thread-safe."""
        limiter = RateLimiter(max_requests=10, window_seconds=1)
        results = []

        def make_requests():
            for _ in range(5):
                allowed, _ = limiter.is_allowed("shared")
                results.append(allowed)

        # Run multiple threads
        threads = [Thread(target=make_requests) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have exactly 10 True and 10 False
        assert sum(results) == 10
        assert len(results) == 20


class TestCheckRateLimit:
    """Test check_rate_limit function."""

    def test_check_rate_limit_error(self):
        """Test that check_rate_limit raises SecurityError when limit exceeded."""
        # Configure global rate limiter with very low limit
        # Save current limiter state
        from qa_chain.rate_limiter import _global_rate_limiter, configure_rate_limiter

        original_limiter = _global_rate_limiter

        try:
            # Configure with low limit
            configure_rate_limiter(max_requests=1, window_seconds=60)

            # First call should work
            check_rate_limit("test_user_unique")

            # Second call should raise
            with pytest.raises(SecurityError, match="Rate limit exceeded"):
                check_rate_limit("test_user_unique")
        finally:
            # Restore original limiter
            import qa_chain.rate_limiter

            qa_chain.rate_limiter._global_rate_limiter = original_limiter
