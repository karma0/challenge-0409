# Docker Setup for QA Chain

This document provides instructions for running the QA Chain application using Docker, eliminating the need to manage Python virtual environments locally.

## Prerequisites

- Docker installed on your system
- OpenAI API key

## Quick Start

### Using the Helper Script

The easiest way to run the application is using the provided `docker-run.sh` script:

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

### Using Docker Compose

For a quick test with default parameters:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Run with default question/context
docker-compose up

# Run in detached mode
docker-compose up -d
```

To customize the question and context, edit the `command` section in `docker-compose.yml`.

### Direct Docker Commands

If you prefer to use Docker directly:

```bash
# Build the image
docker build -t qa-chain:latest .

# Run the container
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  qa-chain:latest \
  --question "What is the capital of France?" \
  --context "Paris is the capital of France."
```

## Advanced Options

### Custom Model

You can specify a different OpenAI model:

```bash
export OPENAI_MODEL=gpt-4

./docker-run.sh --question "Your question" --context "Your context"
```

### Temperature Control

Adjust the temperature for response generation:

```bash
./docker-run.sh \
  --question "Your question" \
  --context "Your context" \
  --temperature 0.7
```

### Context Length

Control the maximum context character limit:

```bash
./docker-run.sh \
  --question "Your question" \
  --context "Your very long context..." \
  --max-context-chars 10000
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

# Run with Azure OpenAI
./docker-run.sh --question "Your question" --context "Your context"
```

Note: When using Azure OpenAI, the `OPENAI_MODEL` should be your deployment name, not the model name.

## Docker Files Overview

- **Dockerfile**: Defines the container image with Python 3.11 and all dependencies
- **docker-compose.yml**: Provides an easy way to run the application with environment variables
- **docker-run.sh**: Helper script that handles image building and container execution

## Benefits of Docker Approach

1. **No Python environment management**: No need to create or maintain virtual environments
2. **Consistent environment**: Same Python version and dependencies across all systems
3. **Easy cleanup**: Simply remove the Docker image when done
4. **Isolation**: Application runs in an isolated container

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

### Docker Not Found

Make sure Docker is installed and the Docker daemon is running.

### Image Build Issues

Force a rebuild:

```bash
docker build --no-cache -t qa-chain:latest .
```
