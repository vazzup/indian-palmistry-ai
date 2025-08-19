# Multi-stage Dockerfile for FastAPI backend
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install -e .[dev]

# Copy application code
COPY app/ ./app/

# Copy alembic configuration if it exists
COPY alembic.ini ./ 
RUN mkdir -p ./alembic

# Create data directory
RUN mkdir -p /app/data/images && chown -R app:app /app

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Worker stage for Celery workers
FROM base as worker

# Override default command for workers
CMD ["celery", "-A", "app.core.celery_app", "worker", "--loglevel=info", "--concurrency=2"]


# Development stage with additional tools
FROM base as development

# Install development dependencies (already included in base)
# Switch back to root for development tools
USER root

# Install additional development tools
RUN apt-get update && apt-get install -y \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Switch back to app user
USER app

# Override command for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]