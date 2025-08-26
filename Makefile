# Avatar Intelligence System - Makefile
# Development and deployment automation

# Python executable - can be overridden
PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python)

.PHONY: help install install-dev test test-pytest test-verbose test-coverage lint format type-check clean build upload install-local uninstall deploy-system check-system docs

# Default target
help:
	@echo "Avatar Intelligence System - Development Commands"
	@echo "================================================="
	@echo "Detected Python: $(PYTHON)"
	@echo ""
	@echo "Installation:"
	@echo "  install        Install package in current environment"
	@echo "  install-dev    Install package with development dependencies"
	@echo "  install-local  Install package locally in editable mode"
	@echo "  uninstall      Uninstall package"
	@echo ""
	@echo "Development:"
	@echo "  test           Run all tests"
	@echo "  test-verbose   Run tests with verbose output"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  lint           Run code linting"
	@echo "  format         Format code with black and isort"
	@echo "  type-check     Run type checking with mypy"
	@echo ""
	@echo "Building:"
	@echo "  clean          Clean build artifacts"
	@echo "  build          Build package distributions"
	@echo "  upload         Upload to PyPI (requires credentials)"
	@echo ""
	@echo "System Operations:"
	@echo "  deploy-system  Deploy Avatar Intelligence System to Neo4j"
	@echo "  check-system   Check system status and health"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make test PYTHON=python3    Override Python executable"
	@echo "  sh test_python.sh           Test Python detection"
	@echo "  make info                   Show package information"
	@echo ""

# Installation targets
install:
	$(PYTHON) -m pip install .

install-dev:
	$(PYTHON) -m pip install -e ".[dev,test,docs]"

install-local:
	$(PYTHON) -m pip install -e .

uninstall:
	$(PYTHON) -m pip uninstall avatar-intelligence-system -y

# Development targets
test:
	$(PYTHON) run_tests.py

test-pytest:
	$(PYTHON) -m pytest tests/ -v

test-verbose:
	$(PYTHON) -m pytest tests/ -v -s

test-coverage:
	$(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

lint:
	flake8 src/ tests/ examples/
	black --check src/ tests/ examples/
	isort --check-only src/ tests/ examples/

format:
	black src/ tests/ examples/
	isort src/ tests/ examples/

type-check:
	mypy src/ --ignore-missing-imports

# Build targets  
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

build: clean
	$(PYTHON) -m build

upload: build
	$(PYTHON) -m twine upload dist/*

# System operation targets
deploy-system:
	@echo "Deploying Avatar Intelligence System..."
	@echo "Usage: make deploy-system NEO4J_PASSWORD=your_password"
	@if [ -z "$(NEO4J_PASSWORD)" ]; then \
		echo "Error: Please provide NEO4J_PASSWORD"; \
		echo "Example: make deploy-system NEO4J_PASSWORD=mypassword"; \
		exit 1; \
	fi
	$(PYTHON) src/avatar_system_deployment.py --password "$(NEO4J_PASSWORD)" --command deploy

check-system:
	@echo "Checking system status..."
	@echo "Usage: make check-system NEO4J_PASSWORD=your_password"
	@if [ -z "$(NEO4J_PASSWORD)" ]; then \
		echo "Error: Please provide NEO4J_PASSWORD"; \
		echo "Example: make check-system NEO4J_PASSWORD=mypassword"; \
		exit 1; \
	fi
	$(PYTHON) src/avatar_system_deployment.py --password "$(NEO4J_PASSWORD)" --command status

# Documentation targets
docs:
	@echo "Documentation generation not yet implemented"
	@echo "See README.md for current documentation"

# Development workflow targets
dev-setup: install-dev
	@echo "Development environment set up successfully!"
	@echo "Run 'make test' to verify installation"

dev-test: format lint type-check test
	@echo "All development checks passed!"

# CI/CD targets
ci-test: install-dev test-coverage lint type-check
	@echo "CI tests completed successfully!"

# Quick development cycle
quick-test:
	$(PYTHON) -m pytest tests/ -x --tb=short

# Install pre-commit hooks (if available)
install-hooks:
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
		echo "Pre-commit hooks installed"; \
	else \
		echo "pre-commit not available, skipping hooks"; \
	fi

# Full development setup
full-setup: dev-setup install-hooks
	@echo ""
	@echo "✅ Full development setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure your Neo4j connection"
	@echo "2. Run 'make deploy-system' to set up the database schema"
	@echo "3. Run 'make test' to verify everything works"
	@echo "4. Start developing!"

# Show package info
info:
	@echo "Avatar Intelligence System Package Information"
	@echo "============================================="
	@echo "Version: 1.0.0"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Location: $(shell pwd)"
	@echo "Dependencies: $(shell $(PYTHON) -m pip list | grep -E 'neo4j|pandas|numpy' || echo 'Not installed')"
	@echo ""
	@echo "Package structure:"
	@find . -name "*.py" -not -path "./build/*" -not -path "./dist/*" -not -path "./.git/*" | head -20

# Emergency cleanup
emergency-clean: clean uninstall
	$(PYTHON) -m pip cache purge
	@echo "Emergency cleanup completed"
