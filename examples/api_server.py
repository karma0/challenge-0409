#!/usr/bin/env python3
"""FastAPI server for the QA Chain application."""

import os
import sys
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qa_chain import QAConfig, SecurityError, answer_question
from qa_chain.logging_config import get_logger, request_id_var, setup_logging

# Initialize logging
setup_logging()
logger = get_logger(__name__)

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


# Middleware for request ID tracking
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracking."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    token = request_id_var.set(request_id)

    start_time = time.time()
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "request_id": request_id,
            }
        },
    )

    try:
        response = await call_next(request)
        elapsed = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": int(elapsed * 1000),
                    "request_id": request_id,
                }
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - {str(e)}",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": int(elapsed * 1000),
                    "error": str(e),
                    "request_id": request_id,
                }
            },
            exc_info=True,
        )
        raise
    finally:
        request_id_var.reset(token)


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
    logger.debug("Root endpoint accessed")
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

    status = "healthy" if api_key else "unhealthy"
    logger.info(
        f"Health check: {status}",
        extra={"extra_fields": {"api_key_configured": bool(api_key)}},
    )

    return {
        "status": status,
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
    logger.info(
        "Answer request received",
        extra={
            "extra_fields": {
                "question_length": len(request.question),
                "context_length": len(request.context),
                "model": request.model,
                "temperature": request.temperature,
            }
        },
    )

    try:
        # Create config from request
        config = QAConfig(
            model=request.model,
            temperature=request.temperature,
            max_context_chars=request.max_context_chars,
        )

        # Get answer
        logger.debug("Calling answer_question function")
        answer = answer_question(
            question=request.question,
            context=request.context,
            config=config,
        )

        logger.info(
            "Answer generated successfully",
            extra={"extra_fields": {"answer_length": len(answer)}},
        )

        return QAResponse(
            answer=answer,
            question=request.question,
            model=request.model,
        )

    except SecurityError as e:
        # Security violations (rate limiting, input validation)
        is_rate_limit = "rate limit" in str(e).lower()
        status_code = 429 if is_rate_limit else 400
        logger.warning(
            f"Security error: {str(e)}",
            extra={
                "extra_fields": {
                    "error_type": "rate_limit" if is_rate_limit else "security",
                    "status_code": status_code,
                }
            },
        )
        raise HTTPException(status_code=status_code, detail=str(e))
    except ValueError as e:
        # Invalid configuration
        logger.warning(
            f"Validation error: {str(e)}",
            extra={"extra_fields": {"error_type": "validation", "status_code": 422}},
        )
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Other errors
        logger.error(
            f"Internal error: {str(e)}",
            extra={"extra_fields": {"error_type": "internal", "status_code": 500}},
            exc_info=True,
        )
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
