.PHONY: install test format lint type-check clean run-example help

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run all tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make format        - Format code with black"
	@echo "  make lint          - Lint code with ruff"
	@echo "  make type-check    - Run type checking with mypy"
	@echo "  make clean         - Clean up generated files"
	@echo "  make run-example   - Run basic usage example"
	@echo "  make run-batch     - Run batch processing example"

install:
	poetry install

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=aml_triage --cov-report=html --cov-report=term

format:
	poetry run black src/ tests/ examples/

lint:
	poetry run ruff check src/ tests/ examples/

type-check:
	poetry run mypy src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete

run-example:
	poetry run python examples/basic_usage.py

run-batch:
	poetry run python examples/batch_processing.py

check: format lint type-check test
	@echo "All checks passed!"
