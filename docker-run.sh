#!/bin/bash

# Helper script to run the QA chain in a Docker container

# Check if either OpenAI or Azure OpenAI credentials are set
if [ -z "$OPENAI_API_KEY" ] && [ -z "$AZURE_OPENAI_API_KEY" ]; then
    echo "Error: No API key found"
    echo "Please set one of the following:"
    echo "  - For OpenAI: export OPENAI_API_KEY=sk-..."
    echo "  - For Azure: export AZURE_OPENAI_API_KEY=... (plus AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_VERSION)"
    exit 1
fi

# Build the Docker image if it doesn't exist or if --build flag is passed
if [[ "$(docker images -q qa-chain:latest 2> /dev/null)" == "" ]] || [[ "$1" == "--build" ]]; then
    echo "Building Docker image..."
    docker build -t qa-chain:latest .
    # Shift arguments if --build was used
    if [[ "$1" == "--build" ]]; then
        shift
    fi
fi

# Run the container with all arguments passed through
docker run --rm \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o-mini}" \
    -e OPENAI_API_TYPE="$OPENAI_API_TYPE" \
    -e AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
    -e AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    -e AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
    qa-chain:latest "$@"
