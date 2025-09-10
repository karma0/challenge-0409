"""Security utilities and guardrails for the QA chain."""

import os
import re
from typing import Optional

from .config import QAConfig

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
    openai_key = os.getenv("OPENAI_API_KEY")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not openai_key and not azure_key:
        raise SecurityError("No API key found in environment variables")

    # Validate OpenAI key format
    if openai_key:
        if len(openai_key) < 10:
            raise SecurityError("OPENAI_API_KEY appears to be invalid (too short)")
        if not API_KEY_PATTERN.match(openai_key):
            raise SecurityError("OPENAI_API_KEY contains invalid characters")

    # Validate Azure configuration
    if azure_key:
        if len(azure_key) < 10:
            raise SecurityError(
                "AZURE_OPENAI_API_KEY appears to be invalid (too short)"
            )
        if not os.getenv("AZURE_OPENAI_ENDPOINT"):
            raise SecurityError(
                "AZURE_OPENAI_ENDPOINT must be set when using Azure OpenAI"
            )


def validate_input(question: str, context: str) -> None:
    """Validate user inputs for security concerns.

    Args:
        question: The user's question
        context: The context paragraph

    Raises:
        SecurityError: If inputs violate security constraints
    """
    # Check lengths
    if not question or len(question.strip()) < MIN_QUESTION_LENGTH:
        raise SecurityError("Question is too short")

    if len(question) > MAX_QUESTION_LENGTH:
        raise SecurityError(
            f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters"
        )

    if len(context) > MAX_CONTEXT_LENGTH:
        raise SecurityError(
            f"Context exceeds maximum length of {MAX_CONTEXT_LENGTH} characters"
        )

    # Check for blocked patterns
    combined_input = f"{question} {context}".lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, combined_input, re.IGNORECASE | re.DOTALL):
            raise SecurityError("Input contains blocked content patterns")


def validate_config(config: QAConfig) -> None:
    """Validate configuration for security concerns.

    Args:
        config: The QAConfig object

    Raises:
        SecurityError: If configuration violates security constraints
    """
    # Temperature validation
    if not 0 <= config.temperature <= 1:
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
        raise SecurityError(f"Model '{config.model}' is not in allowed list")

    # Max context chars validation
    if config.max_context_chars < 100:
        raise SecurityError("max_context_chars must be at least 100")
    if config.max_context_chars > MAX_CONTEXT_LENGTH:
        raise SecurityError(f"max_context_chars cannot exceed {MAX_CONTEXT_LENGTH}")


def sanitize_output(output: str) -> str:
    """Sanitize model output to remove potential security issues.

    Args:
        output: Raw model output

    Returns:
        Sanitized output string
    """
    # Remove any HTML/script tags that might have been generated
    output = re.sub(r"<[^>]+>", "", output)

    # Remove potential JavaScript
    output = re.sub(r"javascript:", "", output, flags=re.IGNORECASE)

    # Ensure output doesn't contain API keys or secrets
    # Simple check for common secret patterns
    secret_patterns = [
        r"sk-[a-zA-Z0-9]{48}",  # OpenAI API key pattern
        r"[a-f0-9]{32}",  # Generic hex secrets
        r"(password|token|secret|key)\s*[:=]\s*['\"]?[^'\"]+['\"]?",
    ]

    for pattern in secret_patterns:
        output = re.sub(pattern, "[REDACTED]", output, flags=re.IGNORECASE)

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
