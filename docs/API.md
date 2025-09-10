# API Documentation

The QA Chain application can be run as a REST API using FastAPI, providing a web service for question-answering.

## Quick Start

### Local Development

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Run the API server
make run-api

# Or directly
python examples/api_server.py
```

The API will be available at `http://localhost:8000`.

### Docker

```bash
# Build and run the API container
make docker-api-build
make docker-api-run

# Or using docker-compose
docker compose up qa-api
```

## API Endpoints

### GET `/`
Root endpoint with API information.

```bash
curl http://localhost:8000/
```

Response:
```json
{
  "message": "QA Chain API",
  "docs": "/docs",
  "health": "/health",
  "answer_endpoint": "/answer"
}
```

### GET `/health`
Health check endpoint.

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "api_key_configured": true,
  "message": "Ready to process requests"
}
```

### POST `/answer`
Main endpoint for question-answering.

```bash
curl -X POST "http://localhost:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the capital of France?",
    "context": "Paris is the capital of France. It is known for the Eiffel Tower."
  }'
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question | string | Yes | The question to answer (1-1000 chars) |
| context | string | Yes | Context to search for answer (1-50000 chars) |
| model | string | No | LLM model to use (default: "gpt-4o-mini") |
| temperature | float | No | Sampling temperature 0.0-2.0 (default: 0.2) |
| max_context_chars | int | No | Max context characters (default: 6000) |

#### Response

```json
{
  "answer": "Paris",
  "question": "What is the capital of France?",
  "model": "gpt-4o-mini"
}
```

#### Error Responses

- **400 Bad Request**: Invalid input or security violation
- **422 Validation Error**: Invalid configuration values
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected error

### GET `/docs`
Interactive API documentation (Swagger UI).

Visit `http://localhost:8000/docs` in your browser.

### GET `/example`
Get example request/response.

```bash
curl http://localhost:8000/example
```

## Configuration

The API uses the same environment variables as the CLI:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
OPENAI_MODEL=gpt-4o-mini
PORT=8000  # API server port

# For Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
```

## Security Features

The API includes all security features from the core library:

- **Input validation**: Enforces character limits and content filtering
- **Rate limiting**: Prevents abuse (configurable)
- **Output sanitization**: Removes potentially harmful content
- **CORS support**: Configurable for browser access

## Development with Docker

### Build the API image

```bash
docker build -f Dockerfile.api -t qa-api:latest .
```

### Run with docker-compose

```bash
# Start the API service
docker compose up qa-api

# Run in background
docker compose up -d qa-api

# View logs
docker compose logs -f qa-api

# Stop the service
docker compose down
```

### Development mode with hot reload

```bash
make docker-api-dev
```

This mounts the local files and enables auto-reload on changes.

## Testing the API

### Using curl

```bash
# Basic request
curl -X POST "http://localhost:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who wrote 1984?", "context": "George Orwell wrote the novel 1984."}'

# With custom parameters
curl -X POST "http://localhost:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?",
    "context": "Machine learning is a subset of artificial intelligence...",
    "temperature": 0.0,
    "model": "gpt-4o-mini"
  }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/answer",
    json={
        "question": "What is the capital?",
        "context": "Paris is the capital of France."
    }
)

print(response.json())
# {'answer': 'Paris', 'question': 'What is the capital?', 'model': 'gpt-4o-mini'}
```

### Using JavaScript

```javascript
const response = await fetch('http://localhost:8000/answer', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'What is the capital?',
    context: 'Paris is the capital of France.'
  })
});

const data = await response.json();
console.log(data.answer); // "Paris"
```

## Production Deployment

For production deployment:

1. Set appropriate CORS origins in `api_server.py`
2. Use a production ASGI server (uvicorn is included)
3. Place behind a reverse proxy (nginx, etc.)
4. Configure rate limiting appropriately
5. Set up monitoring and logging
6. Use HTTPS only
7. Implement authentication if needed

Example production Docker run:

```bash
docker run -d \
  --name qa-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -e OPENAI_API_KEY=${OPENAI_API_KEY} \
  qa-api:latest
```

## API Client Libraries

The FastAPI server automatically generates OpenAPI schema. You can:

1. View the schema at `/openapi.json`
2. Use tools like `openapi-generator` to create client libraries
3. Import the schema into Postman or similar tools

## Monitoring

The API includes:

- Health check endpoint for monitoring
- Structured error responses
- Request ID tracking (can be added)
- Prometheus metrics (can be added)

## Next Steps

To extend the API:

1. Add authentication (OAuth2, API keys)
2. Add request logging and monitoring
3. Implement caching for repeated questions
4. Add batch processing endpoint
5. Add WebSocket support for streaming
