#!/usr/bin/env python3
"""FastAPI server for the QA Chain application."""

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qa_chain import QAConfig, SecurityError, answer_question

# Create FastAPI app
app = FastAPI(
    title="QA Chain API",
    description="API for question-answering using context",
    version="1.0.0",
)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QARequest(BaseModel):
    """Request model for question-answering."""

    question: str = Field(
        ..., min_length=1, max_length=1000, description="The question to answer"
    )
    context: str = Field(
        ..., min_length=1, max_length=50000, description="Context to search for answer"
    )
    model: Optional[str] = Field(default="gpt-4o-mini", description="LLM model to use")
    temperature: Optional[float] = Field(
        default=0.2, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_context_chars: Optional[int] = Field(
        default=6000, ge=500, description="Maximum context characters"
    )


class QAResponse(BaseModel):
    """Response model for question-answering."""

    answer: str = Field(..., description="The generated answer")
    question: str = Field(..., description="The original question")
    model: str = Field(..., description="Model used")


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "QA Chain API",
        "docs": "/docs",
        "health": "/health",
        "answer_endpoint": "/answer",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    # Check if API key is configured
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")

    return {
        "status": "healthy" if api_key else "unhealthy",
        "api_key_configured": bool(api_key),
        "message": (
            "API key not configured" if not api_key else "Ready to process requests"
        ),
    }


@app.post(
    "/answer",
    response_model=QAResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def answer_endpoint(request: QARequest):
    """
    Answer a question based on provided context.

    This endpoint processes a question and context through an LLM to generate
    an answer based solely on the provided context.
    """
    try:
        # Create config from request
        config = QAConfig(
            model=request.model,
            temperature=request.temperature,
            max_context_chars=request.max_context_chars,
        )

        # Get answer
        answer = answer_question(
            question=request.question,
            context=request.context,
            config=config,
        )

        return QAResponse(
            answer=answer,
            question=request.question,
            model=request.model,
        )

    except SecurityError as e:
        # Security violations (rate limiting, input validation)
        raise HTTPException(
            status_code=429 if "rate limit" in str(e).lower() else 400,
            detail=str(e),
        )
    except ValueError as e:
        # Invalid configuration
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Other errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}",
        )


# Example usage endpoint
@app.get("/example")
async def example():
    """Get an example request/response."""
    return {
        "example_request": {
            "question": "What is the capital of France?",
            "context": "Paris is the capital of France. It is known for the Eiffel Tower.",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
        },
        "example_response": {
            "answer": "Paris",
            "question": "What is the capital of France?",
            "model": "gpt-4o-mini",
        },
        "curl_example": 'curl -X POST "http://localhost:8000/answer" '
        '-H "Content-Type: application/json" '
        '-d \'{"question": "What is the capital of France?", '
        '"context": "Paris is the capital of France."}\'',
    }


if __name__ == "__main__":
    import uvicorn

    # Check for API key
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")):
        print(
            "Warning: No API key configured. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY."
        )

    # Run server
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
