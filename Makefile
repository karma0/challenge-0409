# Makefile for QA Chain Project

.PHONY: help
help: ## Display this help message
	@echo "QA Chain Project - Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Usage: make [target]"

# Python environment setup
.PHONY: venv
venv: ## Create virtual environment
	python -m venv .venv
	@echo "Virtual environment created. Activate with: source .venv/bin/activate"

.PHONY: install
install: ## Install dependencies
	pip install -r requirements.txt

.PHONY: install-dev
install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

# Code quality checks
.PHONY: lint
lint: ## Run linters (ruff, black --check, isort --check)
	@echo "Running ruff..."
	ruff check src/ tests/ examples/
	@echo "Checking black formatting..."
	black --check src/ tests/ examples/
	@echo "Checking import sorting..."
	isort --check-only src/ tests/ examples/

.PHONY: format
format: ## Format code with black and isort
	@echo "Formatting with black..."
	black src/ tests/ examples/
	@echo "Sorting imports with isort..."
	isort src/ tests/ examples/

.PHONY: fix
fix: ## Fix linting issues (ruff --fix) and format code
	@echo "Fixing with ruff..."
	ruff check --fix src/ tests/ examples/
	@echo "Formatting with black..."
	black src/ tests/ examples/
	@echo "Sorting imports with isort..."
	isort src/ tests/ examples/

.PHONY: type-check
type-check: ## Run type checking with mypy
	mypy src/

# Testing
.PHONY: test
test: ## Run tests
	PYTHONPATH=src pytest tests/

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	PYTHONPATH=src pytest tests/ --cov=src/qa_chain --cov-report=html --cov-report=term

# Docker operations
.PHONY: docker-build
docker-build: ## Build Docker image
	docker build -t qa-chain:latest .

.PHONY: docker-run
docker-run: ## Run Docker container (requires OPENAI_API_KEY)
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "Error: OPENAI_API_KEY is not set"; \
		exit 1; \
	fi
	./docker-run.sh --question "What is the capital of France?" --context "Paris is the capital of France."

.PHONY: docker-compose-run
docker-compose-run: ## Run using docker-compose (pass ARGS for custom arguments)
	docker compose run --rm qa-chain $(ARGS)

.PHONY: docker-compose-up
docker-compose-up: ## Start docker-compose services in background
	docker compose up -d

.PHONY: docker-compose-down
docker-compose-down: ## Stop docker-compose services
	docker compose down

.PHONY: docker-clean
docker-clean: ## Remove Docker image and compose volumes
	docker rmi qa-chain:latest || true
	docker compose down -v || true

# Development helpers
.PHONY: run-example
run-example: ## Run example (requires OPENAI_API_KEY)
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "Error: OPENAI_API_KEY is not set"; \
		exit 1; \
	fi
	python -m examples.run --question "What is the capital of France?" --context "Paris is the capital of France."

.PHONY: clean
clean: ## Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

.PHONY: clean-all
clean-all: clean docker-clean ## Clean everything including Docker
	rm -rf .venv/

# Git hooks
.PHONY: install-hooks
install-hooks: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type pre-push

.PHONY: run-hooks
run-hooks: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# Combined commands
.PHONY: dev
dev: install-dev ## Setup development environment

.PHONY: check
check: lint type-check test ## Run all checks (lint, type-check, test)

.PHONY: all
all: clean fix check docker-build ## Clean, fix, check, and build

# CI/CD helpers
.PHONY: ci
ci: ## Run CI checks (lint, type-check, test)
	@echo "Running CI checks..."
	@make lint
	@make type-check
	@make test

.PHONY: pre-commit
pre-commit: fix check ## Run before committing (fix and check)
