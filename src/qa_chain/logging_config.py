"""Logging configuration and utilities for the QA chain."""

import json
import logging
import sys
import time
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Optional
from uuid import uuid4

# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(record.created)
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO", format_type: str = "json", log_file: Optional[str] = None
) -> None:
    """Set up logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ('json' for structured, 'simple' for human-readable)
        log_file: Optional file path for logging (logs to stderr by default)
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Create handler
    handler: logging.Handler
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stderr)

    # Set formatter
    formatter: logging.Formatter
    if format_type == "json":
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Set specific logger levels
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def with_request_id(request_id: Optional[str] = None) -> Callable:
    """Decorator to set request ID for the duration of a function call.

    Args:
        request_id: Optional request ID. If not provided, generates a new UUID.

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            rid = request_id or str(uuid4())
            token = request_id_var.set(rid)
            try:
                return func(*args, **kwargs)
            finally:
                request_id_var.reset(token)

        return wrapper

    return decorator


def log_with_context(**extra_fields: Any) -> Callable:
    """Decorator to add extra context fields to all logs within a function.

    Args:
        **extra_fields: Additional fields to include in logs

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a logger adapter with extra fields
            class ContextAdapter(logging.LoggerAdapter):
                def process(self, msg: object, kwargs: Any) -> tuple[Any, Any]:
                    if "extra" not in kwargs:
                        kwargs["extra"] = {}
                    kwargs["extra"]["extra_fields"] = extra_fields
                    return msg, kwargs

            # Temporarily replace the logger
            original_logger = logging.getLogger(func.__module__)
            adapted_logger = ContextAdapter(original_logger, {})

            # Monkey patch for the duration of the call
            module = sys.modules[func.__module__]
            original_attr = getattr(module, "logger", None)
            setattr(module, "logger", adapted_logger)

            try:
                return func(*args, **kwargs)
            finally:
                if original_attr is not None:
                    setattr(module, "logger", original_attr)

        return wrapper

    return decorator


def log_execution_time(logger: Optional[logging.Logger] = None) -> Callable:
    """Decorator to log function execution time.

    Args:
        logger: Optional logger instance. If not provided, uses function's module logger.

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = logger or get_logger(func.__module__)
            start_time = time.time()

            log.debug(f"Starting {func.__name__}")
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                log.info(
                    f"Completed {func.__name__}",
                    extra={"extra_fields": {"execution_time_ms": int(elapsed * 1000)}},
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                log.error(
                    f"Failed {func.__name__}: {str(e)}",
                    extra={"extra_fields": {"execution_time_ms": int(elapsed * 1000)}},
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


class LogContext:
    """Context manager for adding fields to logs within a block."""

    def __init__(self, logger: logging.Logger, **fields: Any):
        """Initialize log context.

        Args:
            logger: Logger instance
            **fields: Fields to add to logs
        """
        self.logger = logger
        self.fields = fields
        self.original_class: type[logging.Logger] | None = None

    def __enter__(self) -> None:
        """Enter context and modify logger."""
        # Store original logger class
        self.original_class = self.logger.__class__

        # Store fields reference
        parent = self

        # Create a custom logger class with extra fields
        class ContextLogger(self.original_class):  # type: ignore
            def _log(self, level: int, msg: str, args: tuple, **kwargs: Any) -> None:
                if "extra" not in kwargs:
                    kwargs["extra"] = {}
                if "extra_fields" not in kwargs["extra"]:
                    kwargs["extra"]["extra_fields"] = {}
                kwargs["extra"]["extra_fields"].update(parent.fields)
                super()._log(level, msg, args, **kwargs)

        # Replace logger's class
        self.logger.__class__ = ContextLogger

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and restore logger."""
        if self.original_class is not None:
            self.logger.__class__ = self.original_class
