"""Simple rate limiter for API calls."""

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, Optional, Tuple


class RateLimiter:
    """Thread-safe rate limiter using sliding window algorithm."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = Lock()

    def is_allowed(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """Check if request is allowed for given identifier.

        Args:
            identifier: Unique identifier (e.g., IP, user ID, API key)

        Returns:
            Tuple of (is_allowed, seconds_until_retry)
        """
        with self.lock:
            now = time.time()
            request_times = self.requests[identifier]

            # Remove old requests outside window
            while request_times and request_times[0] <= now - self.window_seconds:
                request_times.popleft()

            # Check if under limit
            if len(request_times) < self.max_requests:
                request_times.append(now)
                return True, None
            else:
                # Calculate when the oldest request will expire
                oldest_request = request_times[0]
                seconds_until_retry = (oldest_request + self.window_seconds) - now
                return False, seconds_until_retry

    def reset(self, identifier: Optional[str] = None) -> None:
        """Reset rate limit tracking.

        Args:
            identifier: Reset specific identifier, or all if None
        """
        with self.lock:
            if identifier:
                self.requests.pop(identifier, None)
            else:
                self.requests.clear()


# Global rate limiter instance (can be configured per deployment)
_global_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)


def check_rate_limit(identifier: str = "global") -> None:
    """Check rate limit and raise error if exceeded.

    Args:
        identifier: Unique identifier for rate limiting

    Raises:
        SecurityError: If rate limit is exceeded
    """
    from .security import SecurityError

    allowed, retry_after = _global_rate_limiter.is_allowed(identifier)
    if not allowed:
        raise SecurityError(
            f"Rate limit exceeded. Please retry after {retry_after:.1f} seconds."
        )


def configure_rate_limiter(max_requests: int, window_seconds: int) -> None:
    """Configure the global rate limiter.

    Args:
        max_requests: Maximum requests per window
        window_seconds: Window size in seconds
    """
    global _global_rate_limiter
    _global_rate_limiter = RateLimiter(max_requests, window_seconds)
