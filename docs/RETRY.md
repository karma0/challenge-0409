# Retry Logic and Error Handling

This guide covers the retry mechanisms and error handling strategies implemented in the QA Chain application to ensure robust API interactions.

## Overview

The retry system provides automatic recovery from transient failures when calling the OpenAI API or other services. It implements:

- **Exponential backoff** with configurable delays
- **Jitter** to prevent thundering herd problems
- **Smart error detection** to retry only recoverable errors
- **Configurable retry policies** per request
- **Comprehensive logging** of retry attempts

## Configuration

### Environment Variables

Configure retry behavior through environment variables:

```bash
# Enable/disable retry logic
export QA_ENABLE_RETRY=true

# Maximum number of retry attempts (1-5)
export QA_MAX_RETRY_ATTEMPTS=3

# Base delay between retries in seconds
export QA_RETRY_BASE_DELAY=1.0

# Maximum delay between retries
export QA_RETRY_MAX_DELAY=60.0

# Exponential backoff base (1.5-3.0)
export QA_RETRY_EXPONENTIAL_BASE=2.0

# Add random jitter to delays
export QA_RETRY_JITTER=true
```

### Programmatic Configuration

```python
from qa_chain import QAConfig

config = QAConfig(
    enable_retry=True,
    max_retry_attempts=3,
    retry_base_delay=1.0,
    retry_max_delay=60.0,
    retry_exponential_base=2.0,
    retry_jitter=True
)
```

## Retry Strategy

### Exponential Backoff

The retry delay increases exponentially with each attempt:
- 1st retry: 1 second (base delay)
- 2nd retry: 2 seconds
- 3rd retry: 4 seconds
- 4th retry: 8 seconds
- 5th retry: 16 seconds (capped by max_delay)

### Jitter

To prevent multiple clients from retrying at the same time, up to 25% random jitter is added to each delay.

### Retriable Errors

The system automatically retries on:

**Exception Types:**
- `ConnectionError`
- `TimeoutError`
- `IOError`

**Error Messages containing:**
- "rate limit"
- "timeout"
- "connection"
- "temporarily unavailable"
- "service unavailable"
- "bad gateway"
- "gateway timeout"
- "too many requests"

**HTTP Status Codes:**
- 429 (Too Many Requests)
- 500 (Internal Server Error)
- 502 (Bad Gateway)
- 503 (Service Unavailable)
- 504 (Gateway Timeout)

## Usage Examples

### Basic Usage

The retry logic is automatically applied when enabled:

```python
from qa_chain import answer_question, QAConfig

# Retry is enabled by default
answer = answer_question(
    question="What is AI?",
    context="Artificial Intelligence (AI) is..."
)
```

### Custom Retry Policy

Create a custom retry policy for specific use cases:

```python
from qa_chain.retry import RetryPolicy

# Conservative policy with longer delays
policy = RetryPolicy(
    max_attempts=5,
    base_delay=2.0,
    max_delay=120.0,
    jitter=True
)

# Use with decorator
@policy.as_decorator()
def call_external_api():
    return external_api.call()
```

### Disable Retry for Specific Calls

```python
# Disable retry for time-sensitive operations
config = QAConfig(enable_retry=False)
answer = answer_question(question, context, config)
```

## Error Handling

### Retry Exhaustion

When all retry attempts fail:

```python
from qa_chain import answer_question
from qa_chain.retry import RetryError

try:
    answer = answer_question(question, context)
except RetryError as e:
    print(f"All {e.max_attempts} retry attempts failed")
    print(f"Last error: {e.last_error}")
    # Handle persistent failure
```

### Non-Retriable Errors

Some errors bypass retry logic:

```python
try:
    answer = answer_question(question, context)
except ValueError as e:
    # Configuration errors are not retried
    print(f"Configuration error: {e}")
except PermissionError as e:
    # Authentication errors are not retried
    print(f"Permission denied: {e}")
```

## Monitoring and Logging

### Retry Attempt Logs

Each retry attempt is logged with details:

```json
{
  "level": "WARNING",
  "message": "Retriable error in _invoke_chain_with_retry (attempt 1/3): Connection timeout. Retrying in 1.2s...",
  "function": "_invoke_chain_with_retry",
  "attempt": 1,
  "max_attempts": 3,
  "delay_seconds": 1.2,
  "error_type": "TimeoutError"
}
```

### Success After Retry

Successful retries are logged:

```json
{
  "level": "INFO",
  "message": "Successfully completed _invoke_chain_with_retry after 2 attempts"
}
```

### Retry Exhaustion

When all attempts fail:

```json
{
  "level": "ERROR",
  "message": "All 3 attempts failed for _invoke_chain_with_retry",
  "function": "_invoke_chain_with_retry",
  "attempts": 3,
  "last_error": "Connection timeout"
}
```

## Best Practices

### 1. Choose Appropriate Settings

- **Fast failures**: Use fewer attempts with shorter delays
- **Critical operations**: Use more attempts with longer delays
- **Rate-limited APIs**: Use exponential backoff with jitter

### 2. Monitor Retry Patterns

Track retry metrics to identify:
- Frequent failures requiring investigation
- Services with poor reliability
- Need for circuit breaker patterns

### 3. Handle Failures Gracefully

```python
def safe_answer_question(question: str, context: str) -> str:
    """Answer question with fallback on persistent failures."""
    try:
        return answer_question(question, context)
    except RetryError:
        # Log to monitoring system
        logger.error("Persistent API failure", extra={
            "question_preview": question[:50],
            "alert": "api_failure"
        })
        # Return graceful fallback
        return "I'm unable to process your request at the moment. Please try again later."
```

### 4. Test Retry Logic

```python
import pytest
from unittest.mock import patch

def test_retry_on_timeout():
    with patch('qa_chain.chain.ChatOpenAI.invoke') as mock:
        # Simulate timeout then success
        mock.side_effect = [TimeoutError(), "Success"]

        result = answer_question("Test", "Test")
        assert result == "Success"
        assert mock.call_count == 2
```

## Advanced Usage

### Custom Retry Decorator

Apply retry logic to any function:

```python
from qa_chain.retry import retry_with_exponential_backoff

@retry_with_exponential_backoff(
    max_attempts=3,
    base_delay=2.0,
    retriable_exceptions=(CustomAPIError,)
)
def call_custom_api(data):
    return api_client.process(data)
```

### Retry with Callback

Monitor retry attempts with callbacks:

```python
def on_retry(error, attempt):
    # Send metrics to monitoring
    metrics.increment('api.retry', tags=[
        f'attempt:{attempt}',
        f'error:{type(error).__name__}'
    ])

@retry_with_exponential_backoff(on_retry=on_retry)
def monitored_api_call():
    return api.call()
```

### Circuit Breaker Pattern

Combine with circuit breaker for better resilience:

```python
from qa_chain.retry import RetryPolicy

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.is_open = False

    def call(self, func, *args, **kwargs):
        if self.is_open:
            if time.time() - self.last_failure_time > self.timeout:
                self.reset()
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True

    def reset(self):
        self.failure_count = 0
        self.is_open = False
```

## Troubleshooting

### Common Issues

1. **Retries happening too quickly**
   - Increase `retry_base_delay`
   - Ensure `retry_jitter` is enabled

2. **Too many retry attempts**
   - Reduce `max_retry_attempts`
   - Check if errors are truly transient

3. **Not retrying on expected errors**
   - Check error type and message
   - Consider custom retriable exceptions

4. **Hitting rate limits despite retry**
   - Increase `retry_max_delay`
   - Use higher `retry_exponential_base`

### Debug Mode

Enable debug logging to see retry details:

```python
config = QAConfig(
    enable_debug_mode=True,
    log_level="DEBUG"
)
```

This will log:
- Each retry attempt with timing
- Error details and types
- Delay calculations
- Final success or failure

## Performance Considerations

### Impact on Response Time

With default settings, worst-case retry time:
- 1st attempt: 0s
- 1st retry: +1s delay
- 2nd retry: +2s delay
- 3rd retry: +4s delay
- Total: Up to 7s additional latency

### Optimization Strategies

1. **Fail fast for user-facing requests**:
   ```python
   config = QAConfig(
       max_retry_attempts=2,
       retry_base_delay=0.5,
       retry_max_delay=2.0
   )
   ```

2. **Aggressive retry for background jobs**:
   ```python
   config = QAConfig(
       max_retry_attempts=5,
       retry_base_delay=2.0,
       retry_max_delay=120.0
   )
   ```

3. **Disable retry for real-time operations**:
   ```python
   config = QAConfig(enable_retry=False)
   ```

This retry system ensures your application remains resilient to transient failures while maintaining good performance and user experience.
