# Makefile for Indian Palmistry AI development

.PHONY: help install dev test lint format type-check clean build up down logs shell

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Installation and setup
install: ## Install dependencies and setup pre-commit hooks
	pip install -e .[dev]
	pre-commit install

# Development
dev: ## Start development environment with docker-compose
	docker-compose up -d
	@echo "Development environment started:"
	@echo "  - API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - Flower (Celery monitoring): docker-compose --profile monitoring up -d flower"

monitoring: ## Start with monitoring services
	docker-compose --profile monitoring up -d

# Testing
test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	pytest-watch tests/ app/

# Code quality
lint: ## Run linting
	ruff check app/
	black --check app/
	mypy app/

format: ## Format code
	black app/
	ruff check app/ --fix

type-check: ## Run type checking
	mypy app/

# Pre-commit
pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# Docker operations
build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API logs
	docker-compose logs -f api

logs-worker: ## Show worker logs
	docker-compose logs -f worker

logs-redis: ## Show Redis logs
	docker-compose logs -f redis

# Development utilities
shell: ## Open shell in API container
	docker-compose exec api bash

shell-worker: ## Open shell in worker container
	docker-compose exec worker bash

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

# Database operations
db-upgrade: ## Run database migrations
	docker-compose exec api alembic upgrade head

db-downgrade: ## Rollback database migrations
	docker-compose exec api alembic downgrade -1

db-reset: ## Reset database (development only)
	docker-compose exec api rm -f /app/data/dev.db
	docker-compose exec api alembic upgrade head

# Celery operations
celery-worker: ## Start Celery worker manually
	docker-compose exec api celery -A app.core.celery_app worker --loglevel=info

celery-monitor: ## Show Celery worker status
	docker-compose exec api celery -A app.core.celery_app inspect active

celery-purge: ## Purge all Celery queues
	docker-compose exec api celery -A app.core.celery_app purge

# Cleanup
clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

clean-all: ## Clean up everything including images
	docker-compose down -v --rmi all
	docker system prune -af

# Health checks
health: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost:8000/healthz | jq . || echo "API health check failed"
	@docker-compose exec redis redis-cli ping || echo "Redis health check failed"

# Development workflow
fresh-start: clean build up ## Clean start with fresh build
	@echo "Fresh development environment started!"
	@make health

# Production simulation
prod-build: ## Build production images
	docker build --target base -t palmistry-ai:latest .

# Generate requirements.txt (for compatibility)
requirements: ## Generate requirements.txt from pyproject.toml
	pip-compile pyproject.toml --output-file requirements.txt