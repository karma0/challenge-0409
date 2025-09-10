# Makefile for QA Chain Project

.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[36m
RESET := \033[0m

.PHONY: help
help: ## Display this help message
	@echo "QA Chain Project - Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Usage: make [target]"

# Environment setup
.PHONY: venv
venv: ## Create Python virtual environment (.venv)
	python -m venv .venv
	@echo "Virtual environment created. Activate with: source .venv/bin/activate"

.PHONY: install
install: ## Install runtime dependencies only
	pip install -r requirements.txt

.PHONY: install-dev
install-dev: install ## Install all dependencies (runtime + development)
	pip install -r requirements-dev.txt

.PHONY: dev
dev: venv install-dev install-hooks ## Complete dev setup (venv, deps, hooks)

# Code quality
.PHONY: lint
lint: ## Check code style without changes
	@echo "Running ruff..."
	ruff check src/ tests/ examples/
	@echo "Checking black formatting..."
	black --check src/ tests/ examples/
	@echo "Checking import sorting..."
	isort --check-only src/ tests/ examples/

.PHONY: format
format: ## Auto-format code (black, isort)
	black src/ tests/ examples/
	isort src/ tests/ examples/

.PHONY: fix
fix: ## Fix linting errors and format code
	ruff check --fix src/ tests/ examples/
	$(MAKE) format

.PHONY: type-check
type-check: ## Check type annotations (mypy)
	mypy src/

# Testing
.PHONY: test
test: ## Run all tests
	PYTHONPATH=src pytest tests/

.PHONY: test-coverage
test-coverage: ## Run tests + generate coverage report
	PYTHONPATH=src pytest tests/ --cov=src/qa_chain --cov-report=html --cov-report=term

.PHONY: test-coverage-strict
test-coverage-strict: ## Run tests + enforce 90% coverage
	PYTHONPATH=src pytest tests/ --cov=src/qa_chain --cov-report=term --cov-fail-under=90

# Docker
.PHONY: docker-build
docker-build: ## Build Docker image (qa-chain:latest)
	docker build -t qa-chain:latest .

.PHONY: docker-run
docker-run: ## Run example in Docker container
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "Error: OPENAI_API_KEY is not set"; \
		exit 1; \
	fi
	./docker-run.sh --question "What is the capital of France?" --context "Paris is the capital of France."

.PHONY: docker-compose-run
docker-compose-run: ## Run API with docker-compose
	docker compose up

.PHONY: docker-api-build
docker-api-build: ## Build API Docker image
	docker build -f Dockerfile.api -t qa-api:latest .

.PHONY: docker-api-run
docker-api-run: ## Run API server in Docker
	docker compose up

.PHONY: docker-api-dev
docker-api-dev: ## Run API with hot reload for development
	docker compose run --rm -p 8000:8000 -v $$(pwd)/examples:/app/examples qa-api

.PHONY: docker-clean
docker-clean: ## Remove Docker images and volumes
	-docker rmi qa-chain:latest qa-api:latest
	-docker compose down -v

# Examples
.PHONY: run
run: ## Run CLI with custom args (ARGS="--question ...")
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "Error: OPENAI_API_KEY is not set"; \
		exit 1; \
	fi
	python -m examples.run $(ARGS)

.PHONY: run-simple
run-simple: ## Run basic example (no args needed)
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "Error: OPENAI_API_KEY is not set"; \
		exit 1; \
	fi
	python examples/simple_qa.py

.PHONY: run-api
run-api: ## Run API server locally (port 8000)
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "Error: OPENAI_API_KEY is not set"; \
		exit 1; \
	fi
	python examples/api_server.py

# Cleanup
.PHONY: clean
clean: ## Clean temp files (caches, coverage, etc.)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

.PHONY: clean-all
clean-all: clean docker-clean ## Full reset (temp files + Docker + venv)
	rm -rf .venv/

# Git hooks
.PHONY: install-hooks
install-hooks: ## Install git hooks (pre-commit, pre-push)
	pre-commit install
	pre-commit install --hook-type pre-push

.PHONY: run-hooks
run-hooks: ## Manually run all git hooks
	pre-commit run --all-files

# Combined workflows
.PHONY: check
check: lint type-check test ## Run all validation checks

.PHONY: pre-commit
pre-commit: fix check ## Auto-fix issues before commit

.PHONY: pre-push
pre-push: test test-coverage-strict ## Validate tests + coverage before push

.PHONY: ci
ci: check test-coverage-strict ## Full CI validation suite
