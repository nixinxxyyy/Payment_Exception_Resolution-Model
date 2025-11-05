.PHONY: help install install-dev setup run test clean lint format

help:
	@echo "Customer Support Ticket Management System - Available Commands:"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make install-dev  - Install with development dependencies"
	@echo "  make setup        - Initial setup (create .env, install deps)"
	@echo "  make run          - Run the FastAPI server"
	@echo "  make run-example  - Run example ticket processing"
	@echo "  make test-api     - Test API endpoints"
	@echo "  make clean        - Remove generated files and cache"
	@echo "  make lint         - Run code linting"
	@echo "  make format       - Format code with black"
	@echo ""

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest black flake8 mypy

setup:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "✅ Created .env file. Please edit it and add your OPENAI_API_KEY"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Setup complete!"

run:
	python -m src.api.main

run-example:
	python scripts/run_example.py

test-api:
	python scripts/test_api.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .mypy_cache/

lint:
	flake8 src/ --max-line-length=100

format:
	black src/ scripts/ --line-length=100
