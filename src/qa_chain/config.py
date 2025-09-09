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
    # You can add more knobs (top_p, seed, etc.) as needed.
