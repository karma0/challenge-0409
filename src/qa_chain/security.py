"""Security utilities and guardrails for the QA chain."""

import os
import re
from typing import Optional

from .config import QAConfig
from .logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Security constants
MAX_QUESTION_LENGTH = 1000  # Maximum characters in a question
MAX_CONTEXT_LENGTH = 50000  # Maximum characters in context
MIN_QUESTION_LENGTH = 1  # Minimum characters in a question
BLOCKED_PATTERNS = [
    # Potential injection attempts
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",  # Event handlers
    # Prompt injection patterns
    r"ignore\s+(previous|above|all)\s+(instructions|prompts?)",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"###\s*(instruction|system)",
]

# API key validation pattern
API_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]+$")


class SecurityError(Exception):
    """Raised when a security constraint is violated."""

    pass


def validate_api_keys() -> None:
    """Validate that API keys are properly set and formatted."""
    logger.debug("Validating API keys")
    openai_key = os.getenv("OPENAI_API_KEY")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not openai_key and not azure_key:
        logger.error("No API key found in environment variables")
        raise SecurityError("No API key found in environment variables")

    # Validate OpenAI key format
    if openai_key:
        logger.debug("Validating OpenAI API key format")
        if len(openai_key) < 10:
            logger.error("OPENAI_API_KEY appears to be invalid (too short)")
            raise SecurityError("OPENAI_API_KEY appears to be invalid (too short)")
        if not API_KEY_PATTERN.match(openai_key):
            logger.error("OPENAI_API_KEY contains invalid characters")
            raise SecurityError("OPENAI_API_KEY contains invalid characters")
        logger.debug("OpenAI API key validation passed")

    # Validate Azure configuration
    if azure_key:
        logger.debug("Validating Azure OpenAI configuration")
        if len(azure_key) < 10:
            logger.error("AZURE_OPENAI_API_KEY appears to be invalid (too short)")
            raise SecurityError(
                "AZURE_OPENAI_API_KEY appears to be invalid (too short)"
            )
        if not os.getenv("AZURE_OPENAI_ENDPOINT"):
            logger.error("AZURE_OPENAI_ENDPOINT must be set when using Azure OpenAI")
            raise SecurityError(
                "AZURE_OPENAI_ENDPOINT must be set when using Azure OpenAI"
            )
        logger.debug("Azure OpenAI configuration validation passed")


def validate_input(question: str, context: str) -> None:
    """Validate user inputs for security concerns.

    Args:
        question: The user's question
        context: The context paragraph

    Raises:
        SecurityError: If inputs violate security constraints
    """
    logger.debug(
        f"Validating input - question length: {len(question)}, context length: {len(context)}"
    )

    # Check lengths
    if not question or len(question.strip()) < MIN_QUESTION_LENGTH:
        logger.warning("Question validation failed: too short")
        raise SecurityError("Question is too short")

    if len(question) > MAX_QUESTION_LENGTH:
        logger.warning(
            f"Question validation failed: exceeds {MAX_QUESTION_LENGTH} characters"
        )
        raise SecurityError(
            f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters"
        )

    if len(context) > MAX_CONTEXT_LENGTH:
        logger.warning(
            f"Context validation failed: exceeds {MAX_CONTEXT_LENGTH} characters"
        )
        raise SecurityError(
            f"Context exceeds maximum length of {MAX_CONTEXT_LENGTH} characters"
        )

    # Check for blocked patterns
    logger.debug("Checking for blocked patterns")
    combined_input = f"{question} {context}".lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, combined_input, re.IGNORECASE | re.DOTALL):
            logger.warning(
                f"Input validation failed: blocked pattern detected - {pattern}"
            )
            raise SecurityError("Input contains blocked content patterns")

    logger.debug("Input validation passed")


def validate_config(config: QAConfig) -> None:
    """Validate configuration for security concerns.

    Args:
        config: The QAConfig object

    Raises:
        SecurityError: If configuration violates security constraints
    """
    logger.debug(
        f"Validating config - model: {config.model}, temperature: {config.temperature}"
    )

    # Temperature validation
    if not 0 <= config.temperature <= 1:
        logger.error(f"Invalid temperature: {config.temperature}")
        raise SecurityError("Temperature must be between 0 and 1")

    # Model validation - ensure only allowed models
    allowed_models = {
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-4",
        "gpt-4-32k",
        "gpt-4-turbo-preview",
        "gpt-4o",
        "gpt-4o-mini",
    }

    if config.model not in allowed_models:
        logger.error(f"Model '{config.model}' is not in allowed list")
        raise SecurityError(f"Model '{config.model}' is not in allowed list")

    # Max context chars validation
    if config.max_context_chars < 100:
        logger.error(f"max_context_chars too small: {config.max_context_chars}")
        raise SecurityError("max_context_chars must be at least 100")
    if config.max_context_chars > MAX_CONTEXT_LENGTH:
        logger.error(f"max_context_chars too large: {config.max_context_chars}")
        raise SecurityError(f"max_context_chars cannot exceed {MAX_CONTEXT_LENGTH}")

    logger.debug("Config validation passed")


def sanitize_output(output: str) -> str:
    """Sanitize model output to remove potential security issues.

    Args:
        output: Raw model output

    Returns:
        Sanitized output string
    """
    logger.debug(f"Sanitizing output of length {len(output)}")
    original_output = output

    # Remove any HTML/script tags that might have been generated
    output = re.sub(r"<[^>]+>", "", output)
    if output != original_output:
        logger.warning("Removed HTML tags from output")

    # Remove potential JavaScript
    temp_output = re.sub(r"javascript:", "", output, flags=re.IGNORECASE)
    if temp_output != output:
        logger.warning("Removed JavaScript URLs from output")
        output = temp_output

    # Ensure output doesn't contain API keys or secrets
    # Simple check for common secret patterns
    secret_patterns = [
        r"sk-[a-zA-Z0-9]{48}",  # OpenAI API key pattern
        r"[a-f0-9]{32}",  # Generic hex secrets
        r"(password|token|secret|key)\s*[:=]\s*['\"]?[^'\"]+['\"]?",
    ]

    secrets_found = False
    for pattern in secret_patterns:
        temp_output = re.sub(pattern, "[REDACTED]", output, flags=re.IGNORECASE)
        if temp_output != output:
            secrets_found = True
            output = temp_output

    if secrets_found:
        logger.warning("Redacted potential secrets from output")

    logger.debug(f"Output sanitized - final length: {len(output.strip())}")
    return output.strip()


def get_secure_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Securely get environment variable with validation.

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        The environment variable value or default
    """
    value = os.getenv(key, default)
    if value and key.endswith("_KEY"):
        # Basic validation for API keys
        if len(value) < 10 or not API_KEY_PATTERN.match(value):
            return None
    return value
