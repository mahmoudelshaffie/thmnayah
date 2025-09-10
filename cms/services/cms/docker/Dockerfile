# Multi-stage build for CMS Service
# Base Python 3.12 slim image for optimal size and security

FROM python:3.12-slim as base

# Set environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for PostgreSQL and other packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.8.2

# Configure Poetry: Don't create virtual environment, install in system Python
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-ansi \
    && rm -rf $POETRY_CACHE_DIR

# Production stage
FROM python:3.12-slim as production

# Copy installed packages from base stage
COPY --from=base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r cms && useradd -r -g cms -d /app -s /sbin/nologin -c "CMS User" cms

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=cms:cms . .

# Create required directories and set proper structure
RUN mkdir -p /app/logs /app/media /app/static \
    && chown -R cms:cms /app

# Switch to non-root user
USER cms

# Set environment variables - PYTHONPATH should point to app directory
ENV PYTHONPATH=/app/app \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage
FROM base as development

# Install development dependencies
RUN poetry install --no-ansi

# Create non-root user
RUN groupadd -r cms && useradd -r -g cms -d /app -s /bin/bash -c "CMS User" cms

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=cms:cms . .

# Create required directories
RUN mkdir -p /app/logs /app/media /app/static \
    && chown -R cms:cms /app

# Switch to non-root user
USER cms

# Set environment variables for development
ENV PYTHONPATH=/app/app \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=development \
    DEBUG=true

# Expose port
EXPOSE 8000

# Development command with auto-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]