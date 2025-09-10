"""Test the FastAPI server."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add examples to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from api_server import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_root(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "QA Chain API"
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"
    assert data["answer_endpoint"] == "/answer"


def test_health_no_api_key(client, monkeypatch):
    """Test health endpoint without API key."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["api_key_configured"] is False


def test_health_with_api_key(client, monkeypatch):
    """Test health endpoint with API key."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_key_configured"] is True


def test_example(client):
    """Test example endpoint."""
    response = client.get("/example")
    assert response.status_code == 200
    data = response.json()
    assert "example_request" in data
    assert "example_response" in data
    assert "curl_example" in data


@pytest.mark.skipif(
    "OPENAI_API_KEY" not in __import__("os").environ, reason="needs OPENAI_API_KEY"
)
def test_answer_endpoint(client):
    """Test answer endpoint with real API."""
    response = client.post(
        "/answer",
        json={
            "question": "What is the capital of France?",
            "context": "Paris is the capital and largest city of France.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "question" in data
    assert data["question"] == "What is the capital of France?"
    assert "paris" in data["answer"].lower()


def test_answer_validation_errors(client):
    """Test answer endpoint validation."""
    # Missing required fields
    response = client.post("/answer", json={})
    assert response.status_code == 422

    # Empty question
    response = client.post(
        "/answer",
        json={"question": "", "context": "Some context"},
    )
    assert response.status_code == 422

    # Question too long
    response = client.post(
        "/answer",
        json={"question": "a" * 1001, "context": "Some context"},
    )
    assert response.status_code == 422

    # Invalid temperature
    response = client.post(
        "/answer",
        json={
            "question": "Question?",
            "context": "Context",
            "temperature": 3.0,
        },
    )
    assert response.status_code == 422


def test_answer_security_error(client, monkeypatch):
    """Test answer endpoint security errors."""

    # Mock to force security error
    def mock_answer(*args, **kwargs):
        from qa_chain import SecurityError

        raise SecurityError("Input contains blocked content patterns")

    # Patch the import in api_server module
    monkeypatch.setattr("api_server.answer_question", mock_answer)

    response = client.post(
        "/answer",
        json={
            "question": "What is X?",
            "context": "X is Y.",
        },
    )
    assert response.status_code == 400


def test_answer_rate_limit_error(client, monkeypatch):
    """Test answer endpoint rate limit errors."""

    # Mock to force rate limit error
    def mock_answer(*args, **kwargs):
        from qa_chain import SecurityError

        raise SecurityError("Rate limit exceeded")

    # Patch the import in api_server module
    monkeypatch.setattr("api_server.answer_question", mock_answer)

    response = client.post(
        "/answer",
        json={
            "question": "What is X?",
            "context": "X is Y.",
        },
    )
    assert response.status_code == 429
