FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ ./src/
COPY examples/ ./examples/

# Set Python path to include src directory
ENV PYTHONPATH=/app/src

# Default command (can be overridden)
ENTRYPOINT ["python", "-m", "examples.run"]
