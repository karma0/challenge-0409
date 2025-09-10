"""Retry logic for handling API failures."""

import time
from functools import wraps
from typing import Any, Callable, Optional, Type

from .logging_config import get_logger

logger = get_logger(__name__)

# Common API errors that should trigger retries
RETRIABLE_ERRORS = (
    ConnectionError,
    TimeoutError,
    IOError,
)

# Error messages that indicate retriable conditions
RETRIABLE_ERROR_MESSAGES = [
    "rate limit",
    "timeout",
    "connection",
    "temporarily unavailable",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "too many requests",
]


class RetryError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.last_error = last_error


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds
    """
    delay: float = min(base_delay * (2**attempt), max_delay)

    if jitter:
        import random

        # Add up to 25% jitter
        jitter_amount: float = delay * 0.25 * random.random()
        delay = delay + jitter_amount

    return delay


def is_retriable_error(error: Exception) -> bool:
    """Check if an error is retriable.

    Args:
        error: The exception to check

    Returns:
        True if the error is retriable
    """
    # Check if it's a known retriable error type
    if isinstance(error, RETRIABLE_ERRORS):
        return True

    # Check error message for retriable conditions
    error_message = str(error).lower()
    for pattern in RETRIABLE_ERROR_MESSAGES:
        if pattern in error_message:
            return True

    # Check for specific API errors
    if hasattr(error, "response"):
        status_code = getattr(error.response, "status_code", None)
        if status_code in [429, 500, 502, 503, 504]:
            return True

    return False


def retry_with_exponential_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retriable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries
        retriable_exceptions: Tuple of exceptions to retry on
        on_retry: Optional callback called on each retry

    Returns:
        Decorated function
    """
    if retriable_exceptions is None:
        retriable_exceptions = RETRIABLE_ERRORS

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Optional[Exception] = None

            for attempt in range(max_attempts):
                try:
                    logger.debug(
                        f"Attempting {func.__name__} (attempt {attempt + 1}/{max_attempts})"
                    )
                    result = func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(
                            f"Successfully completed {func.__name__} after {attempt + 1} attempts"
                        )

                    return result

                except Exception as error:
                    last_error = error

                    # Check if we should retry
                    if not is_retriable_error(error) and not isinstance(
                        error, retriable_exceptions
                    ):
                        logger.error(
                            f"Non-retriable error in {func.__name__}: {error}",
                            exc_info=True,
                        )
                        raise

                    # Check if we've exhausted attempts
                    if attempt >= max_attempts - 1:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}",
                            extra={
                                "extra_fields": {
                                    "function": func.__name__,
                                    "attempts": max_attempts,
                                    "last_error": str(error),
                                }
                            },
                        )
                        raise RetryError(
                            f"Failed after {max_attempts} attempts", last_error=error
                        )

                    # Calculate delay
                    delay = exponential_backoff(attempt, base_delay, max_delay)

                    logger.warning(
                        f"Retriable error in {func.__name__} (attempt {attempt + 1}/{max_attempts}): "
                        f"{error}. Retrying in {delay:.1f}s...",
                        extra={
                            "extra_fields": {
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_attempts": max_attempts,
                                "delay_seconds": delay,
                                "error_type": type(error).__name__,
                            }
                        },
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(error, attempt + 1)
                        except Exception as callback_error:
                            logger.error(f"Error in retry callback: {callback_error}")

                    # Wait before retrying
                    time.sleep(delay)

            # This should never be reached due to the raise in the loop
            raise RetryError(
                f"Failed after {max_attempts} attempts", last_error=last_error
            )

        return wrapper

    return decorator


class RetryPolicy:
    """Configurable retry policy for API calls."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retriable_status_codes: Optional[list[int]] = None,
        retriable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    ):
        """Initialize retry policy.

        Args:
            max_attempts: Maximum number of attempts
            base_delay: Base delay between retries
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
            jitter: Whether to add jitter to delays
            retriable_status_codes: HTTP status codes to retry
            retriable_exceptions: Exception types to retry
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retriable_status_codes = retriable_status_codes or [
            429,
            500,
            502,
            503,
            504,
        ]
        self.retriable_exceptions = retriable_exceptions or RETRIABLE_ERRORS

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Check if we should retry after an error.

        Args:
            error: The exception that occurred
            attempt: Current attempt number (1-based)

        Returns:
            True if we should retry
        """
        if attempt >= self.max_attempts:
            return False

        return is_retriable_error(error) or isinstance(error, self.retriable_exceptions)

    def get_delay(self, attempt: int) -> float:
        """Get delay before next retry.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        return exponential_backoff(
            attempt, self.base_delay, self.max_delay, self.jitter
        )

    def as_decorator(self) -> Callable:
        """Convert policy to a decorator.

        Returns:
            Retry decorator using this policy
        """
        return retry_with_exponential_backoff(
            max_attempts=self.max_attempts,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            retriable_exceptions=self.retriable_exceptions,
        )
