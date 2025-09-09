import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv


def test_dotenv_loading():
    """Test that .env file loading works correctly."""
    # Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TEST_API_KEY=test-key-12345\n")
        f.write("TEST_MODEL=gpt-test\n")
        temp_env_file = f.name

    try:
        # Load the temporary .env file
        load_dotenv(temp_env_file)

        # Verify environment variables are loaded
        assert os.getenv("TEST_API_KEY") == "test-key-12345"
        assert os.getenv("TEST_MODEL") == "gpt-test"
    finally:
        # Clean up
        os.unlink(temp_env_file)
        # Remove from environment
        os.environ.pop("TEST_API_KEY", None)
        os.environ.pop("TEST_MODEL", None)


def test_dotenv_example_file_exists():
    """Test that .env.example file exists for documentation."""
    project_root = Path(__file__).parent.parent
    env_example = project_root / ".env.example"
    assert env_example.exists(), ".env.example file should exist for documentation"
