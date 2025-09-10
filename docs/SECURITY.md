# Security Guide

This document outlines the security features and best practices implemented in the QA Chain application.

## Security Features

### 1. Input Validation

All user inputs are validated before processing:

- **Question Length**: Must be between 1 and 1,000 characters
- **Context Length**: Maximum 50,000 characters
- **Content Filtering**: Blocks potential injection attempts including:
  - HTML/JavaScript injection patterns (`<script>`, `javascript:`, event handlers)
  - Prompt injection attempts (e.g., "ignore previous instructions")
  - System/Assistant role hijacking attempts
  - Smart quote normalization to prevent encoding-based bypasses

### 2. Output Sanitization

Model outputs are sanitized to prevent:
- HTML/Script tag injection (all HTML tags are stripped)
- JavaScript execution (`javascript:` URLs removed)
- Accidental exposure of API keys or secrets
  - OpenAI API key patterns (`sk-...`)
  - Generic hex secrets
  - Password/token patterns in output

### 3. Rate Limiting

Built-in rate limiting prevents abuse:
- Default: 20 requests per minute per identifier
- Thread-safe sliding window algorithm
- Configurable per deployment via `configure_rate_limiter()`
- Can use different identifiers (API key, user ID, IP address)
- Automatic cleanup of old request records
- Can be disabled via `QAConfig(enable_rate_limiting=False)` for testing

### 4. Model Restrictions

Only approved OpenAI models are allowed:
- gpt-3.5-turbo, gpt-3.5-turbo-16k
- gpt-4, gpt-4-32k, gpt-4-turbo-preview
- gpt-4o, gpt-4o-mini

### 5. Configuration Validation

All configuration parameters are validated:
- Temperature: Must be between 0 and 2 (Pydantic validation)
- Context length: Must be >= 500 characters (Pydantic validation)
- Model names: Must be in allowed list (runtime validation)
- Additional runtime checks ensure max_context_chars doesn't exceed 50,000

## Environment Variables

### Required
- `OPENAI_API_KEY` or `AZURE_OPENAI_API_KEY`: Your API key

### Optional for Azure
- `AZURE_OPENAI_ENDPOINT`: Your Azure endpoint
- `AZURE_OPENAI_API_VERSION`: API version

## Implementation Details

### Security Module Structure

The security features are implemented across several modules:

- **`security.py`**: Core validation functions and SecurityError exception
- **`rate_limiter.py`**: Thread-safe rate limiting implementation
- **`chain.py`**: Integration point for all security checks
- **`config.py`**: Pydantic models with built-in validation

### Security Check Order

When `answer_question()` is called, security checks occur in this order:
1. Input validation (length, content filtering)
2. Configuration validation (model, temperature, limits)
3. Rate limiting check (if enabled)
4. LLM API call
5. Output sanitization

## Best Practices

### 1. API Key Management

- Never commit API keys to version control
- Use `.env` files locally (already in `.gitignore`)
- Use secure secret management in production (e.g., AWS Secrets Manager, Azure Key Vault)
- Rotate API keys regularly
- API keys are validated for basic format before use

### 2. Rate Limiting Configuration

For production deployments, configure rate limiting based on your use case:

```python
from qa_chain.rate_limiter import configure_rate_limiter

# Configure for your needs
configure_rate_limiter(
    max_requests=100,  # requests per window
    window_seconds=60  # 1 minute window
)
```

### 3. Error Handling

The application provides specific security errors:

```python
from qa_chain import answer_question, SecurityError

try:
    answer = answer_question(question, context)
except SecurityError as e:
    # Handle security violations
    log_security_event(e)
    return "Request blocked for security reasons"
```

### 4. Logging and Monitoring

Implement logging for security events:
- Failed validation attempts
- Rate limit violations
- Suspicious input patterns

### 5. Network Security

When deploying:
- Use HTTPS only
- Implement proper CORS policies
- Use API authentication (OAuth2, API keys)
- Consider IP allowlisting for sensitive deployments

### 6. Docker Security

The provided Dockerfile follows security best practices:
- Uses minimal base image (`python:3.11-slim`)
- Runs as non-root user (container runtime should enforce)
- No unnecessary packages installed
- Clear separation of build and runtime

### 7. Input Size Limits

Be aware of limits:
- Questions: 1,000 characters max
- Context: 50,000 characters max (configurable)
- These limits prevent DoS attacks and control costs

## Testing

Security features are thoroughly tested in `tests/test_security.py`:
- Input validation edge cases
- Output sanitization scenarios
- Rate limiting behavior
- Configuration validation
- Integration tests with the full pipeline

Run security tests specifically:
```bash
pytest tests/test_security.py -v
```

## Security Checklist for Deployment

- [ ] API keys stored securely (not in code or configs)
- [ ] Rate limiting configured appropriately
- [ ] HTTPS enabled
- [ ] Authentication implemented
- [ ] Logging configured for security events
- [ ] Input validation enabled (automatic)
- [ ] Output sanitization enabled (automatic)
- [ ] Regular security updates applied
- [ ] Monitoring alerts configured
- [ ] Pre-commit hooks installed for code security
- [ ] Docker container runs as non-root user

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:
1. Do not open a public issue
2. Email security details to your security team
3. Include steps to reproduce
4. Allow time for patching before disclosure

## Updates

This security guide should be reviewed and updated regularly as new threats emerge and the application evolves.
