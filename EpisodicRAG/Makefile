.PHONY: help test lint type-check format check all clean install

help:
	@echo "Available commands:"
	@echo "  make install     - Install dev dependencies"
	@echo "  make test        - Run tests with coverage"
	@echo "  make lint        - Run linter (ruff)"
	@echo "  make type-check  - Run type checker (mypy)"
	@echo "  make format      - Auto-format code (ruff)"
	@echo "  make check       - Run all checks (lint + type + test)"
	@echo "  make clean       - Remove cache files"

install:
	pip install -e ".[dev]"
	pre-commit install

test:
	python -m pytest scripts/test -v --cov=scripts --cov-report=term-missing

lint:
	python -m ruff check scripts/

type-check:
	python -m mypy scripts/ --ignore-missing-imports

format:
	python -m ruff check scripts/ --fix
	python -m ruff format scripts/

check: lint type-check test

all: check

clean:
ifeq ($(OS),Windows_NT)
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
	@for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d"
	@for /d /r . %%d in (.mypy_cache) do @if exist "%%d" rd /s /q "%%d"
	@del /s /q *.pyc 2>nul || echo.
else
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
endif
