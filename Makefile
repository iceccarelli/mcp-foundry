# MCP Foundry for Trading — Makefile
# Common development tasks.

.PHONY: help install dev test lint format serve docker-build docker-run clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

dev: ## Install development dependencies
	pip install -e ".[dev]"

test: ## Run the test suite
	pytest -v

test-cov: ## Run tests with coverage report
	pytest --cov=core --cov=connectors --cov-report=term-missing --cov-report=html

lint: ## Run linter (ruff)
	ruff check .

format: ## Auto-format code (ruff)
	ruff format .

typecheck: ## Run type checker (mypy)
	mypy core/ connectors/ utils/

serve: ## Start the MCP server
	python scripts/run_server.py

serve-dev: ## Start the MCP server with auto-reload
	python scripts/run_server.py --reload

docker-build: ## Build the Docker image
	docker build -t mcp-foundry .

docker-run: ## Run the Docker container
	docker run -p 8000:8000 --env-file .env mcp-foundry

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
