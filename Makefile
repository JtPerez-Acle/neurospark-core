.PHONY: help dev down build test lint format clean

# Default target
help:
	@echo "NeuroSpark Core Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make dev        - Start all services in development mode"
	@echo "  make down       - Stop all services"
	@echo "  make build      - Build all Docker images"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"
	@echo "  make clean      - Remove all build artifacts"
	@echo ""

# Start all services in development mode
dev:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Build all Docker images
build:
	docker-compose build

# Run tests
test:
	pytest -v

# Run linters
lint:
	flake8 src tests
	mypy src tests

# Format code
format:
	black src tests
	isort src tests

# Clean build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Run a specific service
run-%:
	docker-compose up -d $*

# View logs for a specific service
logs-%:
	docker-compose logs -f $*

# Create a new migration
migration:
	alembic revision --autogenerate -m "$(message)"

# Run migrations
migrate:
	alembic upgrade head

# Run a specific test
test-%:
	pytest -v tests/test_$*.py
