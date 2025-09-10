"""Debug utilities for the QA chain application."""

import json
import logging
import os
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Iterator, List, Optional

from .config import QAConfig
from .logging_config import get_logger

logger = get_logger(__name__)


class DebugContext:
    """Context manager for debug mode operations."""

    def __init__(self) -> None:
        """Initialize debug context."""
        self.start_time: float | None = None
        self.debug_info: Dict[str, Any] = {}
        self.checkpoints: List[Dict[str, Any]] = []

    def checkpoint(self, name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Add a debug checkpoint.

        Args:
            name: Checkpoint name
            data: Optional data to record
        """
        checkpoint = {
            "name": name,
            "time": time.time(),
            "elapsed": time.time() - self.start_time if self.start_time else 0,
        }
        if data:
            checkpoint["data"] = data
        self.checkpoints.append(checkpoint)
        logger.debug(f"Debug checkpoint: {name}", extra={"extra_fields": checkpoint})

    def __enter__(self) -> "DebugContext":
        """Enter debug context."""
        self.start_time = time.time()
        logger.debug("Entering debug context")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit debug context and log summary."""
        if self.start_time is None:
            return
        total_time = time.time() - self.start_time
        self.debug_info["total_time"] = total_time
        self.debug_info["checkpoints"] = self.checkpoints

        logger.debug(
            f"Debug context completed in {total_time:.3f}s",
            extra={"extra_fields": self.debug_info},
        )


def debug_chain_state(chain_state: Dict[str, Any]) -> None:
    """Log the current state of the LangChain pipeline.

    Args:
        chain_state: Current state dictionary from chain
    """
    logger.debug("Chain state", extra={"extra_fields": {"chain_state": chain_state}})


def debug_prompt(prompt_template: str, variables: Dict[str, Any]) -> None:
    """Log prompt template and variables for debugging.

    Args:
        prompt_template: The prompt template string
        variables: Variables to be substituted
    """
    logger.debug(
        "Prompt debug info",
        extra={
            "extra_fields": {
                "prompt_template": prompt_template,
                "variables": variables,
                "formatted_length": len(prompt_template.format(**variables)),
            }
        },
    )


def trace_llm_call(func: Callable) -> Callable:
    """Decorator to trace LLM API calls.

    Args:
        func: Function making LLM call

    Returns:
        Wrapped function with tracing
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        call_info = {
            "function": func.__name__,
            "args_count": len(args),
            "kwargs": list(kwargs.keys()),
        }

        logger.debug(
            f"LLM call started: {func.__name__}", extra={"extra_fields": call_info}
        )

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(
                f"LLM call completed: {func.__name__}",
                extra={
                    "extra_fields": {
                        **call_info,
                        "elapsed_ms": int(elapsed * 1000),
                        "success": True,
                    }
                },
            )
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"LLM call failed: {func.__name__}",
                extra={
                    "extra_fields": {
                        **call_info,
                        "elapsed_ms": int(elapsed * 1000),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                },
                exc_info=True,
            )
            raise

    return wrapper


def log_memory_usage() -> Dict[str, float]:
    """Log current memory usage.

    Returns:
        Dictionary with memory stats in MB
    """
    try:
        import psutil

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        memory_stats = {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
        }

        logger.debug("Memory usage", extra={"extra_fields": memory_stats})
        return memory_stats
    except ImportError:
        logger.debug("psutil not available for memory tracking")
        return {}


def debug_config(config: QAConfig) -> None:
    """Log configuration details for debugging.

    Args:
        config: QAConfig instance
    """
    config_dict = config.model_dump()
    logger.debug("Configuration", extra={"extra_fields": {"config": config_dict}})


@contextmanager
def debug_mode(enable: bool = True) -> Iterator[None]:
    """Context manager to temporarily enable debug mode.

    Args:
        enable: Whether to enable debug mode
    """
    if not enable:
        yield
        return

    original_level = logger.level
    logger.setLevel(logging.DEBUG)

    logger.debug("Debug mode enabled")
    try:
        yield
    finally:
        logger.setLevel(original_level)
        logger.debug("Debug mode disabled")


def dump_debug_info(
    question: str,
    context: str,
    answer: str,
    config: QAConfig,
    execution_time: float,
    filename: Optional[str] = None,
) -> None:
    """Dump debug information to a file.

    Args:
        question: The input question
        context: The input context
        answer: The generated answer
        config: Configuration used
        execution_time: Total execution time
        filename: Optional filename (defaults to timestamp)
    """
    if not config.enable_debug_mode:
        return

    debug_data = {
        "timestamp": time.time(),
        "execution_time": execution_time,
        "config": config.model_dump(),
        "input": {
            "question": question,
            "question_length": len(question),
            "context": context[:500] + "..." if len(context) > 500 else context,
            "context_length": len(context),
        },
        "output": {
            "answer": answer,
            "answer_length": len(answer),
        },
    }

    if not filename:
        filename = f"debug_{int(time.time())}.json"

    try:
        with open(filename, "w") as f:
            json.dump(debug_data, f, indent=2)
        logger.debug(f"Debug info dumped to {filename}")
    except Exception as e:
        logger.error(f"Failed to dump debug info: {str(e)}")


class DebugStats:
    """Collect and log debug statistics."""

    def __init__(self) -> None:
        """Initialize stats collector."""
        self.stats: Dict[str, List[float]] = {}

    def record(self, metric: str, value: float) -> None:
        """Record a metric value.

        Args:
            metric: Metric name
            value: Metric value
        """
        if metric not in self.stats:
            self.stats[metric] = []
        self.stats[metric].append(value)

    def log_summary(self) -> None:
        """Log summary statistics."""
        summary = {}
        for metric, values in self.stats.items():
            if values:
                summary[metric] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }

        logger.debug("Debug statistics summary", extra={"extra_fields": summary})
