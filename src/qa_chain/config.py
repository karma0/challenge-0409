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
