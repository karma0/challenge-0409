"""Integration tests for the QA chain."""

import os
import subprocess
import sys

import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="needs OPENAI_API_KEY")
def test_cli_integration():
    """Test the CLI works end-to-end."""
    # Run the CLI
    cmd = [
        sys.executable,
        "-m",
        "examples.run",
        "--question",
        "What is the largest planet?",
        "--context",
        "Jupiter is the largest planet in our solar system.",
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": "src"}
    )

    assert result.returncode == 0
    assert "Jupiter" in result.stdout


@pytest.mark.skipif(
    os.path.exists(".env"),
    reason="Skip when .env file exists - test requires no API keys",
)
def test_cli_no_api_key():
    """Test CLI handles missing API key gracefully."""
    # This test only runs when no .env file exists
    # Run without API key
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env.pop("AZURE_OPENAI_API_KEY", None)

    cmd = [
        sys.executable,
        "-m",
        "examples.run",
        "--question",
        "test",
        "--context",
        "test",
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env={**env, "PYTHONPATH": "src"}
    )

    assert result.returncode == 1
    assert "Error: No API key found" in result.stdout


def test_cli_help():
    """Test CLI help works."""
    cmd = [sys.executable, "-m", "examples.run", "--help"]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": "src"}
    )

    assert result.returncode == 0
    assert "--question" in result.stdout
    assert "--context" in result.stdout
    assert "--model" in result.stdout
    assert "--temperature" in result.stdout
