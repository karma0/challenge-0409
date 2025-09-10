# Docker Setup for QA Chain

This document provides instructions for running the QA Chain application using Docker, both as a CLI tool and as a REST API.

## Prerequisites

- Docker installed on your system
- Docker Compose (included with Docker Desktop)
- OpenAI API key

## Quick Start

### CLI Mode

The easiest way to run the CLI is using the provided `docker-run.sh` script:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Make the script executable (first time only)
chmod +x docker-run.sh

# Run a query
./docker-run.sh --question "What is the capital of France?" --context "Paris is the capital of France."

# Force rebuild the Docker image and run
./docker-run.sh --build --question "Who wrote 1984?" --context "George Orwell wrote the novel 1984."
```

### API Mode

Run the application as a REST API server:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Start the API server
docker compose up qa-api

# Or in detached mode
docker compose up -d qa-api

# API is now available at http://localhost:8000
# View API docs at http://localhost:8000/docs
```

Test the API:

```bash
curl -X POST "http://localhost:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the capital of France?",
    "context": "Paris is the capital of France."
  }'
```

## Docker Compose

The `docker-compose.yml` defines the API service for easy deployment:

```bash
# Start the API server
docker compose up

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop the API
docker compose down
```

The API will be available at `http://localhost:8000`.

## Advanced Options

### Custom Model

You can specify a different OpenAI model:

```bash
export OPENAI_MODEL=gpt-4

# For CLI
./docker-run.sh --question "Your question" --context "Your context"

# For API
docker compose up qa-api
```

### Temperature Control

Adjust the temperature for response generation:

```bash
# CLI
./docker-run.sh \
  --question "Your question" \
  --context "Your context" \
  --temperature 0.7

# API (in request body)
curl -X POST "http://localhost:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Your question?",
    "context": "Your context.",
    "temperature": 0.7
  }'
```

### Context Length

Control the maximum context character limit:

```bash
# CLI
./docker-run.sh \
  --question "Your question" \
  --context "Your very long context..." \
  --max-context-chars 10000

# API (in request body)
curl -X POST "http://localhost:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Your question?",
    "context": "Your very long context...",
    "max_context_chars": 10000
  }'
```

### Azure OpenAI Support

The application fully supports Azure OpenAI. Set the following environment variables:

```bash
# Required Azure OpenAI settings
export OPENAI_API_TYPE=azure
export AZURE_OPENAI_API_KEY=your-azure-api-key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_VERSION=2023-05-15

# Optional: specify the deployment name (model)
export OPENAI_MODEL=your-deployment-name

# Run CLI
./docker-run.sh --question "Your question" --context "Your context"

# Run API
docker compose up qa-api
```

Note: When using Azure OpenAI, the `OPENAI_MODEL` should be your deployment name, not the model name.

## Building Images

### CLI Image

```bash
# Build the CLI image
docker build -t qa-chain:latest .

# Run directly
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  qa-chain:latest \
  --question "What is the capital?" \
  --context "Paris is the capital of France."
```

### API Image

```bash
# Build the API image
docker build -f Dockerfile.api -t qa-api:latest .

# Run directly
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -p 8000:8000 \
  qa-api:latest
```

## Development Mode

For development with hot reload:

```bash
# API with hot reload
docker compose run --rm \
  -p 8000:8000 \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/examples:/app/examples \
  qa-api

# Or use the make target
make docker-api-dev
```

## Docker Files Overview

- **Dockerfile**: CLI application image with Python 3.11
- **Dockerfile.api**: API server image with FastAPI and Uvicorn
- **docker-compose.yml**: Defines both CLI and API services
- **docker-run.sh**: Helper script for CLI usage

## Benefits of Docker Approach

1. **No Python environment management**: No need to create or maintain virtual environments
2. **Consistent environment**: Same Python version and dependencies across all systems
3. **Easy cleanup**: Simply remove the Docker images when done
4. **Isolation**: Applications run in isolated containers
5. **Multiple modes**: Run as CLI or API without conflicts

## Cleanup

Remove containers and images:

```bash
# Stop all services
docker compose down

# Remove images
docker rmi qa-chain:latest qa-api:latest

# Or use make
make docker-clean
```

## Troubleshooting

### Permission Denied on docker-run.sh

```bash
chmod +x docker-run.sh
```

### OpenAI API Key Not Set

Ensure your API key is exported:

```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Port Already in Use (API)

If port 8000 is already in use:

```bash
# Use a different port
docker compose run --rm -p 8080:8000 qa-api

# Or change in docker-compose.yml
```

### Docker Not Found

Make sure Docker is installed and the Docker daemon is running.

### Image Build Issues

Force a rebuild:

```bash
# CLI image
docker build --no-cache -t qa-chain:latest .

# API image
docker build --no-cache -f Dockerfile.api -t qa-api:latest .
```

## Production Deployment

For production API deployment:

1. Build the production image:
   ```bash
   docker build -f Dockerfile.api -t qa-api:prod .
   ```

2. Run with proper configuration:
   ```bash
   docker run -d \
     --name qa-api \
     --restart unless-stopped \
     -e OPENAI_API_KEY="$OPENAI_API_KEY" \
     -p 8000:8000 \
     --health-cmd "curl -f http://localhost:8000/health || exit 1" \
     --health-interval 30s \
     qa-api:prod
   ```

3. Place behind a reverse proxy (nginx, traefik, etc.)
4. Configure SSL/TLS
5. Set up monitoring and logging
