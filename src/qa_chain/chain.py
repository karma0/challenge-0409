from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

from .config import QAConfig
from .logging_config import LogContext, get_logger, setup_logging
from .prompts import build_prompt
from .rate_limiter import check_rate_limit
from .retry import RetryError, RetryPolicy
from .security import sanitize_output, validate_config, validate_input

# Initialize logger
logger = get_logger(__name__)


def _normalize_text(s: str) -> str:
    # Normalize unicode and collapse whitespace
    logger.debug(f"Normalizing text of length {len(s or '')}")
    s = unicodedata.normalize("NFKC", s or "")
    # Replace smart quotes with ascii equivalents
    s = (
        s.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    logger.debug(f"Normalized text to length {len(s)}")
    return s


def _clip_context(context: str, max_chars: int) -> str:
    original_length = len(context)
    if original_length <= max_chars:
        logger.debug(f"Context length {original_length} within limit {max_chars}")
        return context

    logger.info(f"Clipping context from {original_length} to {max_chars} chars")
    # Try to cut on a sentence boundary near the limit
    clipped = context[:max_chars]
    # Backtrack to the last sentence terminator within the last 200 chars
    tail = clipped[-200:]
    idx = max(tail.rfind(". "), tail.rfind("! "), tail.rfind("? "))
    if idx != -1:
        clipped = clipped[: len(clipped) - (len(tail) - idx - 1)]

    logger.debug(f"Context clipped to {len(clipped)} chars at sentence boundary")
    return clipped


def _preprocess(inputs: Dict[str, str], config: QAConfig) -> Dict[str, str]:
    q = _normalize_text(inputs.get("question", ""))
    c = _normalize_text(inputs.get("context", ""))
    c = _clip_context(c, config.max_context_chars)
    return {"question": q, "context": c}


def build_chain(config: QAConfig) -> Any:
    preprocess = RunnableLambda(lambda d: _preprocess(d, config))
    prompt = build_prompt()
    llm = ChatOpenAI(model=config.model, temperature=config.temperature)
    return preprocess | prompt | llm | StrOutputParser()


def _invoke_chain_with_retry(
    chain: Any, question: str, context: str, config: QAConfig
) -> str:
    """Invoke the chain with retry logic if enabled.

    Args:
        chain: The LangChain pipeline
        question: The question to answer
        context: The context to use
        config: Configuration including retry settings

    Returns:
        The model's response

    Raises:
        RetryError: If all retry attempts fail
        Exception: If retry is disabled or error is non-retriable
    """
    if not config.enable_retry:
        # No retry - just invoke directly
        result: str = chain.invoke({"question": question, "context": context})
        return result

    # Create retry policy from config
    retry_policy = RetryPolicy(
        max_attempts=config.max_retry_attempts,
        base_delay=config.retry_base_delay,
        max_delay=config.retry_max_delay,
        exponential_base=config.retry_exponential_base,
        jitter=config.retry_jitter,
    )

    # Define the function to retry
    @retry_policy.as_decorator()
    def invoke_with_retry() -> str:
        result: str = chain.invoke({"question": question, "context": context})
        return result

    try:
        retry_result: str = invoke_with_retry()
        return retry_result
    except RetryError as e:
        logger.error(
            "All retry attempts exhausted",
            extra={
                "extra_fields": {
                    "max_attempts": config.max_retry_attempts,
                    "last_error": str(e.last_error) if e.last_error else None,
                }
            },
        )
        # Re-raise the last error for better error messages
        if e.last_error:
            raise e.last_error
        raise


def answer_question(question: str, context: str, config: QAConfig | None = None) -> str:
    """Answer a user's question using ONLY the provided context.

    This function implements the challenge spec requirements:
    1. Accepts two inputs: a question and context paragraph
    2. Integrates OpenAI LLM to generate answers
    3. Preprocesses inputs (normalizes whitespace, handles special chars)
    4. Returns formatted answer as a string

    Args:
        question: The user's question (string).
        context: A paragraph (or more) with the relevant context.
        config: Optional QAConfig to control model, temperature, and max_context_chars.
                If not provided, uses sensible defaults.

    Returns:
        The model's answer as a plain string. If the answer cannot be found
        in the context, returns "I don't know based on the provided context."

    Raises:
        SecurityError: If inputs or config violate security constraints.

    Example:
        >>> answer = answer_question(
        ...     "What is the capital?",
        ...     "Paris is the capital of France."
        ... )
        >>> print(answer)
        'Paris' or 'The capital is Paris.'
    """
    cfg = config or QAConfig()

    # Set up logging based on config
    if cfg.enable_debug_mode:
        setup_logging("DEBUG", cfg.log_format, cfg.log_file)
    else:
        setup_logging(cfg.log_level, cfg.log_format, cfg.log_file)

    start_time = time.time()

    # Create log context with question info
    with LogContext(
        logger,
        question_length=len(question),
        context_length=len(context),
        model=cfg.model,
        temperature=cfg.temperature,
    ):
        logger.info(f"Processing question: {question[:50]}...")

        try:
            # Validate inputs and configuration
            logger.debug("Validating inputs")
            validate_input(question, context)
            validate_config(cfg)

            # Check rate limit if enabled
            if cfg.enable_rate_limiting:
                logger.debug(f"Checking rate limit for {cfg.rate_limit_identifier}")
                check_rate_limit(cfg.rate_limit_identifier)

            # Build and run the chain
            logger.debug("Building LangChain pipeline")
            chain = build_chain(cfg)

            logger.info("Invoking LLM chain")
            result: str = _invoke_chain_with_retry(chain, question, context, cfg)

            # Sanitize output before returning
            logger.debug("Sanitizing output")
            sanitized_result = sanitize_output(result)

            # Log execution time
            elapsed = time.time() - start_time
            logger.info(
                f"Question answered successfully in {elapsed:.2f}s",
                extra={
                    "extra_fields": {
                        "execution_time_s": elapsed,
                        "answer_length": len(sanitized_result),
                    }
                },
            )

            # Log slow requests
            if cfg.log_slow_requests and elapsed > cfg.log_slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {elapsed:.2f}s > {cfg.log_slow_request_threshold}s threshold",
                    extra={"extra_fields": {"slow_request": True}},
                )

            return sanitized_result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Error processing question: {str(e)}",
                extra={
                    "extra_fields": {
                        "execution_time_s": elapsed,
                        "error_type": type(e).__name__,
                    }
                },
                exc_info=True,
            )
            raise
