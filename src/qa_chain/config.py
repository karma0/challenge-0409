from pydantic import BaseModel, Field


class QAConfig(BaseModel):
    """Configuration for the QA chain."""

    model: str = Field(default="gpt-4o-mini", description="OpenAI chat model name")
    temperature: float = Field(
        default=0.2, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_context_chars: int = Field(
        default=6000,
        ge=500,
        description="Max characters from context to include in prompt",
    )
    enable_rate_limiting: bool = Field(
        default=True, description="Enable rate limiting for API calls"
    )
    rate_limit_identifier: str = Field(
        default="global", description="Identifier for rate limiting (e.g., user ID)"
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json for structured, simple for human-readable)",
        pattern="^(json|simple)$",
    )
    log_file: str | None = Field(
        default=None, description="Optional log file path (logs to stderr by default)"
    )
    enable_debug_mode: bool = Field(
        default=False, description="Enable debug mode with verbose logging"
    )
    log_slow_requests: bool = Field(
        default=True,
        description="Log requests that take longer than log_slow_request_threshold",
    )
    log_slow_request_threshold: float = Field(
        default=1.0, ge=0.1, description="Threshold in seconds for slow request logging"
    )
