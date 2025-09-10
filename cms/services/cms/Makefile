.PHONY: help install install-dev test lint format clean run migrations upgrade-db create-migration docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  clean        Clean cache and temporary files"
	@echo "  run          Run development server"
	@echo "  migrations   Generate new migration"
	@echo "  upgrade-db   Apply database migrations"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run with Docker Compose"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest

lint:
	flake8 app tests
	mypy app

format:
	black app tests
	isort app tests

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache

run:
	uvicorn app.main:app --reload

migrations:
	alembic revision --autogenerate -m "$(MSG)"

upgrade-db:
	alembic upgrade head

docker-build:
	docker-compose build

docker-run:
	docker-compose up
