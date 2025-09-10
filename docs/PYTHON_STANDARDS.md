# Python Standards Compliance

This document details how the QA Chain application adheres to Python standards, best practices, and community conventions.

## PEP Compliance

### PEP 8 - Style Guide for Python Code

The project strictly follows PEP 8 guidelines through automated tooling:

- **Line Length**: 88 characters (Black's default, slightly longer than PEP 8's 79)
- **Indentation**: 4 spaces (no tabs)
- **Naming Conventions**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private: Leading underscore `_private_function`

**Enforcement Tools**:
- Black (formatter)
- Ruff (linter)
- Pre-commit hooks

### PEP 257 - Docstring Conventions

All public functions include properly formatted docstrings:

```python
def answer_question(question: str, context: str, config: QAConfig | None = None) -> str:
    """Answer a user's question using ONLY the provided context.

    This function implements the challenge spec requirements:
    1. Accepts two inputs: a question and context paragraph
    2. Integrates OpenAI LLM to generate answers
    3. Preprocesses inputs (normalizes whitespace, handles special chars)
    4. Returns formatted answer as a string

    Args:
        question: The user's question (string).
        context: A paragraph (or more) with the relevant context.
        config: Optional QAConfig to control model, temperature, and max_context_chars.
                If not provided, uses sensible defaults.

    Returns:
        The model's answer as a plain string. If the answer cannot be found
        in the context, returns "I don't know based on the provided context."

    Raises:
        SecurityError: If inputs or config violate security constraints.

    Example:
        >>> answer = answer_question(
        ...     "What is the capital?",
        ...     "Paris is the capital of France."
        ... )
        >>> print(answer)
        'Paris' or 'The capital is Paris.'
    """
```

### PEP 484/526 - Type Hints

Complete type annotations throughout the codebase:

```python
# Function annotations
def validate_input(question: str, context: str) -> None:
    ...

# Variable annotations
requests: Dict[str, List[float]] = {}

# Complex types
from typing import Any, Dict, List, Optional

def build_chain(config: QAConfig) -> Any:
    ...

# Union types (PEP 604 syntax)
def answer_question(question: str, context: str, config: QAConfig | None = None) -> str:
    ...
```

### PEP 517/518 - Build System Specifications

Modern packaging with `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "qa-chain"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "langchain>=0.2.6",
    "langchain-openai>=0.1.8",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "fastapi>=0.104.1",
    "uvicorn>=0.24.0",
]
```

## Code Quality Tools

### Black - Code Formatter

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
```

Features:
- Uncompromising code formatting
- No configuration debates
- Consistent style across the project

### Ruff - Fast Linter

Configuration in `pyproject.toml`:
```toml
[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C90", # mccabe complexity
    "UP",  # pyupgrade
]
```

Checks for:
- Syntax errors
- Undefined names
- Unused imports
- Code complexity
- Modern Python idioms

### isort - Import Sorting

Configuration in `pyproject.toml`:
```toml
[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
```

Import order:
1. Standard library
2. Third-party packages
3. Local imports

### mypy - Static Type Checker

Configuration in `mypy.ini`:
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

Strict type checking ensures:
- All functions have type hints
- Return types are explicit
- No untyped function definitions

## Best Practices Implementation

### 1. Project Structure

Clean, modular organization:
```
src/
├── qa_chain/           # Main package
│   ├── __init__.py     # Public API exports
│   ├── chain.py        # Core logic
│   ├── config.py       # Configuration
│   ├── security.py     # Security features
│   └── ...
tests/                  # Comprehensive test suite
docs/                   # Documentation
```

### 2. Error Handling

Custom exceptions with inheritance:
```python
class SecurityError(Exception):
    """Raised when a security constraint is violated."""
    pass

class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass
```

### 3. Configuration Management

Environment-based configuration with Pydantic:
```python
class QAConfig(BaseSettings):
    model: str = "gpt-4o-mini"
    temperature: float = 0.2

    class Config:
        env_prefix = "QA_"  # QA_MODEL, QA_TEMPERATURE
```

### 4. Testing

Pytest with fixtures and parametrization:
```python
@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API calls."""
    ...

@pytest.mark.parametrize("question,expected", [
    ("What?", "Too short"),
    ("x" * 1001, "Too long"),
])
def test_validation(question, expected):
    ...
```

### 5. Documentation

Comprehensive documentation:
- Docstrings for all public APIs
- Type hints for clarity
- Examples in docstrings
- Separate documentation files

## Python 3.11+ Features Used

### 1. Union Type Syntax (PEP 604)
```python
# Old style
from typing import Union, Optional
config: Optional[QAConfig] = None
config: Union[str, int] = "test"

# New style (Python 3.10+)
config: QAConfig | None = None
config: str | int = "test"
```

### 2. Improved Error Messages
Python 3.11's enhanced error messages help during development

### 3. Performance Improvements
Python 3.11 is up to 60% faster than 3.10

## Security Best Practices

### 1. Input Validation
```python
def validate_input(question: str, context: str) -> None:
    if len(question) > MAX_QUESTION_LENGTH:
        raise SecurityError(f"Question exceeds maximum length")
```

### 2. Secrets Management
```python
# Never hardcode secrets
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")
```

### 3. Output Sanitization
```python
def sanitize_output(output: str) -> str:
    # Remove potential secrets
    output = re.sub(r"sk-[a-zA-Z0-9]{48}", "[REDACTED]", output)
    return output
```

## Performance Considerations

### 1. Efficient String Operations
```python
# Use join for multiple concatenations
result = " ".join(parts)  # Not: result = part1 + " " + part2

# Use f-strings for formatting
message = f"Error: {error}"  # Not: "Error: {}".format(error)
```

### 2. Generator Usage
Where applicable, use generators for memory efficiency

### 3. Caching Decorators
Ready for caching implementation:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param: str) -> str:
    ...
```

## Development Workflow Compliance

### Pre-commit Hooks
Ensures code quality before commits:
```yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

### Continuous Integration Ready
- All tools can run in CI/CD pipelines
- Exit codes indicate success/failure
- Machine-readable output formats

## Conclusion

The QA Chain application demonstrates professional Python development practices:

1. **Standards Compliance**: Follows all relevant PEPs
2. **Tool Integration**: Uses modern Python tooling
3. **Type Safety**: Complete type annotations
4. **Code Quality**: Automated formatting and linting
5. **Testing**: Comprehensive test coverage
6. **Security**: Best practices for secure coding
7. **Documentation**: Clear, comprehensive documentation

This adherence to standards ensures:
- Maintainable code
- Consistent style
- Fewer bugs
- Easier onboarding
- Professional quality
