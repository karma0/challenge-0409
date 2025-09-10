# Logging and Debugging Guide

This guide covers the comprehensive logging and debugging features available in the QA Chain application.

## Table of Contents
- [Overview](#overview)
- [Configuration](#configuration)
- [Structured Logging](#structured-logging)
- [Debug Utilities](#debug-utilities)
- [API Request Tracking](#api-request-tracking)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting](#troubleshooting)

## Overview

The QA Chain application includes a sophisticated logging system designed for production environments:

- **Structured JSON logging** for easy parsing and analysis
- **Request ID tracking** across all components
- **Debug utilities** for development and troubleshooting
- **Performance monitoring** with execution time tracking
- **Configurable log levels** and output formats

## Configuration

### Environment Variables

Configure logging through environment variables or the `QAConfig` object:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export QA_LOG_LEVEL=INFO

# Log format (json or simple)
export QA_LOG_FORMAT=json

# Log file path (optional, defaults to stderr)
export QA_LOG_FILE=/var/log/qa-chain.log

# Enable debug mode
export QA_ENABLE_DEBUG_MODE=true

# Log slow requests
export QA_LOG_SLOW_REQUESTS=true
export QA_LOG_SLOW_REQUEST_THRESHOLD=2.0
```

### Programmatic Configuration

```python
from qa_chain import QAConfig
from qa_chain.logging_config import setup_logging

# Configure via QAConfig
config = QAConfig(
    log_level="DEBUG",
    log_format="json",
    log_file="/tmp/qa-chain.log",
    enable_debug_mode=True,
    log_slow_requests=True,
    log_slow_request_threshold=1.0
)

# Or setup logging directly
setup_logging(level="INFO", format_type="json", log_file="app.log")
```

## Structured Logging

### JSON Log Format

When using JSON format, each log entry contains:

```json
{
  "timestamp": "2024-01-15 10:30:45",
  "level": "INFO",
  "logger": "qa_chain.chain",
  "message": "Processing question: What is AI?...",
  "module": "chain",
  "function": "answer_question",
  "line": 127,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_length": 12,
  "context_length": 500,
  "model": "gpt-4o-mini",
  "temperature": 0.2
}
```

### Log Levels

The application uses standard Python log levels:

- **DEBUG**: Detailed information for debugging
- **INFO**: General operational information
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause the application to fail

### Component-Specific Logging

Different components log at appropriate levels:

```python
# Chain processing
logger.info(f"Processing question: {question[:50]}...")
logger.debug(f"Normalizing text of length {len(text)}")

# Security validation
logger.warning(f"Input validation failed: blocked pattern detected")
logger.error(f"API key validation failed")

# API endpoints
logger.info(f"Request started: {method} {path}")
logger.error(f"Internal error: {error}", exc_info=True)
```

## Debug Utilities

### Debug Context Manager

Use the `DebugContext` for detailed execution tracking:

```python
from qa_chain.debug_utils import DebugContext

with DebugContext() as ctx:
    ctx.checkpoint("preprocessing", {"input_length": len(text)})
    # ... preprocessing code ...

    ctx.checkpoint("llm_call", {"model": "gpt-4"})
    # ... LLM call ...

    ctx.checkpoint("postprocessing", {"output_length": len(result)})
    # ... postprocessing ...
```

### Debug Mode

Enable debug mode for verbose logging:

```python
from qa_chain.debug_utils import debug_mode

# Temporarily enable debug logging
with debug_mode(True):
    answer = answer_question(question, context)
```

### Tracing Decorators

Trace function execution with decorators:

```python
from qa_chain.logging_config import log_execution_time
from qa_chain.debug_utils import trace_llm_call

@log_execution_time()
def process_data(data):
    # Function execution time will be logged
    return transform(data)

@trace_llm_call
def call_openai(prompt):
    # LLM calls will be traced with timing
    return openai.chat.completions.create(...)
```

### Memory Monitoring

Track memory usage during execution:

```python
from qa_chain.debug_utils import log_memory_usage

# Log current memory usage
memory_stats = log_memory_usage()
# Returns: {"rss_mb": 125.5, "vms_mb": 256.0, "percent": 2.5}
```

### Debug Information Dump

Save detailed debug information for analysis:

```python
from qa_chain.debug_utils import dump_debug_info

dump_debug_info(
    question=question,
    context=context,
    answer=answer,
    config=config,
    execution_time=elapsed,
    filename="debug_session.json"
)
```

## API Request Tracking

### Request ID Tracking

Every API request gets a unique ID for tracing:

```bash
# Client can provide request ID
curl -X POST http://localhost:8000/answer \
  -H "X-Request-ID: my-request-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "context": "..."}'

# Or one will be generated automatically
```

### Request Logging

All API requests are logged with:
- Request ID
- Method and path
- Status code
- Execution time
- Error details (if any)

Example log entry:
```json
{
  "timestamp": "2024-01-15 10:30:45",
  "level": "INFO",
  "message": "Request completed: POST /answer - 200",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/answer",
  "status_code": 200,
  "duration_ms": 523,
  "question_length": 50,
  "context_length": 1000,
  "answer_length": 150
}
```

## Performance Monitoring

### Slow Request Detection

Requests exceeding the threshold are logged as warnings:

```json
{
  "level": "WARNING",
  "message": "Slow request detected: 3.45s > 2.0s threshold",
  "request_id": "...",
  "execution_time_s": 3.45,
  "slow_request": true
}
```

### Execution Time Tracking

Key operations log their execution time:

```python
# Automatic timing for main function
logger.info(
    f"Question answered successfully in {elapsed:.2f}s",
    extra={"extra_fields": {"execution_time_s": elapsed}}
)
```

### Performance Statistics

Collect and analyze performance metrics:

```python
from qa_chain.debug_utils import DebugStats

stats = DebugStats()
stats.record("latency_ms", response_time * 1000)
stats.record("tokens_used", token_count)
stats.log_summary()
```

## Troubleshooting

### Common Issues

1. **No logs appearing**
   ```bash
   # Check log level isn't too high
   export QA_LOG_LEVEL=DEBUG

   # Ensure stderr isn't redirected
   python -m qa_chain 2>&1
   ```

2. **JSON parsing errors**
   ```bash
   # Use simple format for debugging
   export QA_LOG_FORMAT=simple
   ```

3. **Performance issues**
   ```python
   # Enable debug mode to see detailed timing
   config = QAConfig(enable_debug_mode=True)
   ```

### Log Analysis

Analyze JSON logs with standard tools:

```bash
# Filter by log level
jq 'select(.level == "ERROR")' app.log

# Find slow requests
jq 'select(.slow_request == true)' app.log

# Track specific request
jq 'select(.request_id == "abc-123")' app.log

# Calculate average response time
jq -s 'map(select(.execution_time_s != null) | .execution_time_s) | add/length' app.log
```

### Debug Workflow

1. **Enable debug mode**
   ```python
   config = QAConfig(
       enable_debug_mode=True,
       log_level="DEBUG"
   )
   ```

2. **Add checkpoints**
   ```python
   with DebugContext() as ctx:
       ctx.checkpoint("step1")
       # ... code ...
       ctx.checkpoint("step2", {"data": value})
   ```

3. **Analyze output**
   ```bash
   # Look for specific operations
   grep "checkpoint" debug.log | jq '.'
   ```

## Best Practices

1. **Use appropriate log levels**
   - DEBUG: Development and troubleshooting only
   - INFO: Key business operations
   - WARNING: Recoverable issues
   - ERROR: Failures requiring attention

2. **Include context in logs**
   ```python
   logger.info(
       "Operation completed",
       extra={"extra_fields": {
           "user_id": user_id,
           "operation": "process_question",
           "duration_ms": elapsed_ms
       }}
   )
   ```

3. **Use request IDs**
   - Always include request ID in API calls
   - Pass request ID to background tasks
   - Include in error reports

4. **Monitor performance**
   - Set appropriate slow request thresholds
   - Review slow request logs regularly
   - Use debug stats for optimization

5. **Secure logging**
   - Never log sensitive data (API keys, passwords)
   - Sanitize user input in logs
   - Use log rotation for file-based logging

## Integration Examples

### With Observability Platforms

Export structured logs to observability platforms:

```bash
# Datadog
python -m qa_chain 2>&1 | datadog-agent

# Elasticsearch/Logstash
python -m qa_chain 2>&1 | logstash -f logstash.conf

# CloudWatch
python -m qa_chain 2>&1 | aws logs put-log-events
```

### With Monitoring Systems

Parse logs for metrics:

```python
# Prometheus exporter example
import prometheus_client
from qa_chain.logging_config import get_logger

response_time = prometheus_client.Histogram(
    'qa_response_time_seconds',
    'Response time for QA requests'
)

@response_time.time()
def monitored_answer_question(question, context):
    return answer_question(question, context)
```

This logging system provides comprehensive visibility into the QA Chain application's behavior, making it easier to debug issues, monitor performance, and maintain the system in production.
