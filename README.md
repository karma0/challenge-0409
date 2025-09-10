# LangChain QA Application

A chain that takes a user's **question** and a **context paragraph** and returns an answer using a language model.

## Core Functionality

The application provides a simple function that meets the following requirements:

```python
from qa_chain import answer_question

# Basic usage - just question and context
answer = answer_question(
    question="What is the capital of France?",
    context="Paris is the capital of France."
)
print(answer)  # -> "Paris" or "The capital of France is Paris."
```

### Requirements Met
1. ✅ **Two inputs**: Accepts a question and context paragraph
2. ✅ **LLM Integration**: Uses OpenAI's chat completion API via LangChain
3. ✅ **Input preprocessing**: Normalizes whitespace and handles special characters
4. ✅ **Formatted output**: Returns a clean string answer

## Production Features

Beyond the basic requirements, this implementation includes:

- **Security**: Input validation, output sanitization, and injection protection
- **Rate limiting**: Configurable request throttling
- **Flexible configuration**: Temperature, model selection, and context limits
- **Logging & Debugging**: Structured JSON logging, request tracking, and debug utilities
- **Docker support**: Ready for containerized deployment
- **Development tools**: Linting, testing, and pre-commit hooks

---

## Setup

```bash
# Create and activate virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set up your API key (choose one option):

# Option 1: Create a .env file (recommended)
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Option 2: Export directly
export OPENAI_API_KEY=sk-...
```

## Basic Usage

### Simplest Form

```python
from qa_chain import answer_question

answer = answer_question(
    "Who wrote 1984?",
    "The novel '1984' was written by George Orwell."
)
print(answer)  # -> "George Orwell"
```

### With Configuration

```python
from qa_chain import answer_question, QAConfig

answer = answer_question(
    question="Who wrote the novel?",
    context="The novel '1984' was written by George Orwell.",
    config=QAConfig(model="gpt-4o-mini", temperature=0.2)
)
```

### Command Line

```bash
# Using the provided CLI
python -m examples.run --question "What is the capital of France?" --context "Paris is the capital of France."

# Or use the simple example
python examples/simple_qa.py
```

### REST API

```bash
# Start the API server
make run-api

# Make a request
curl -X POST "http://localhost:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital?", "context": "Paris is the capital of France."}'
```

See [API documentation](docs/API.md) for full API documentation.

---

## Project layout

```
src/qa_chain/
  ├─ __init__.py
  ├─ chain.py
  ├─ config.py
  ├─ prompts.py
  ├─ rate_limiter.py
  └─ security.py
examples/
  ├─ api_server.py
  ├─ run.py
  └─ simple_qa.py
tests/
  ├─ test_api.py
  ├─ test_chain.py
  ├─ test_context_clipping.py
  ├─ test_dotenv.py
  ├─ test_integration.py
  ├─ test_preprocessing.py
  ├─ test_rate_limiter.py
  ├─ test_security.py
  └─ test_spec_compliance.py
docs/
  ├─ API.md
  ├─ DOCKER.md
  ├─ FEATURES.md
  ├─ PYTHON_STANDARDS.md
  ├─ SECURITY.md
  ├─ SPEC_COMPLIANCE_SUMMARY.md
  └─ WALKTHROUGH.md
```

---

## Docker Support

Run the application without managing Python environments:

### CLI Mode
```bash
export OPENAI_API_KEY=sk-...
./docker-run.sh --question "What is the capital of France?" --context "Paris is the capital of France."
```

### API Mode
```bash
export OPENAI_API_KEY=sk-...
docker compose up
# API available at http://localhost:8000
```

See [Docker documentation](docs/DOCKER.md) for detailed Docker instructions.

---

## Security

The application includes comprehensive security features:

- **Input Validation**: Prevents injection attacks and enforces reasonable limits
- **Output Sanitization**: Removes potentially harmful content from responses
- **Rate Limiting**: Configurable per-deployment rate limits
- **API Key Validation**: Ensures proper API key format and presence

See [Security documentation](docs/SECURITY.md) for detailed security documentation.

---

## Documentation

- [Features Overview](docs/FEATURES.md) - Comprehensive overview of all features and capabilities
- [Code Walkthrough](docs/WALKTHROUGH.md) - Detailed guide through the codebase implementation
- [Python Standards](docs/PYTHON_STANDARDS.md) - Documentation of Python standards compliance
- [API Documentation](docs/API.md) - REST API endpoints and usage
- [Security Guide](docs/SECURITY.md) - Security features and best practices
- [Logging & Debugging](docs/LOGGING.md) - Structured logging and debug utilities
- [Docker Guide](docs/DOCKER.md) - Container deployment instructions
- [Spec Compliance](docs/SPEC_COMPLIANCE_SUMMARY.md) - Challenge specification compliance

---

## Notes

- **Models**: defaults to `gpt-4o-mini`. Override via `QAConfig(model=...)` or `OPENAI_MODEL` env var.
- **Streaming**: This minimal version returns a single string. It's easy to extend to streaming by swapping in a streaming-friendly runner.
- **Azure OpenAI**: You can point `langchain-openai` at Azure by setting the corresponding environment variables (`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, etc.).
- **Safety**: The prompt is constrained to the provided context; the chain will admit uncertainty if the answer isn't in the context.
