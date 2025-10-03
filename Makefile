.PHONY: help install dev-install update build test test-fast test-unit test-integration test-contract clean example-simple example-langchain example-langgraph lint format typecheck publish publish-test

help:
	@echo "Available targets:"
	@echo "  install          - Install package dependencies"
	@echo "  dev-install      - Install package with development dependencies"
	@echo "  update           - Update all dependencies"
	@echo "  build            - Build distribution packages"
	@echo "  test             - Run all tests (including integration)"
	@echo "  test-fast        - Run tests excluding integration tests"
	@echo "  test-unit        - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-contract    - Run contract tests only"
	@echo "  lint             - Run linting checks (ruff + mypy + pyright)"
	@echo "  typecheck        - Run type checking (pyright)"
	@echo "  format           - Format code"
	@echo "  clean            - Remove build artifacts"
	@echo "  example-simple   - Run simple example"
	@echo "  example-langchain - Run vanilla LangChain example"
	@echo "  example-langgraph - Run LangGraph example"
	@echo "  publish-test     - Publish to TestPyPI"
	@echo "  publish          - Publish to PyPI"

install:
	uv pip install -e .

dev-install:
	uv pip install -e ".[dev]"

update:
	uv pip compile pyproject.toml -o requirements.txt
	uv pip install -r requirements.txt

build: clean
	uv build

test:
	uv run pytest tests/ -v

test-fast:
	uv run pytest tests/ -v -m "not integration"

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-contract:
	uv run pytest tests/contract/ -v

lint:
	uv run ruff check src/ tests/ examples/
	uv run mypy src/
	uv run pyright

typecheck:
	uv run pyright

format:
	uv run ruff format src/ tests/ examples/
	uv run ruff check --fix src/ tests/ examples/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .pyright_cache
	rm -rf pyrightconfig.json
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

example-simple:
	uv run python examples/simple_example.py

example-langchain:
	uv run python examples/vanilla_langchain.py

example-langgraph:
	uv run python examples/langgraph_example.py

publish-test: build
	uv publish --publish-url https://test.pypi.org/legacy/ dist/*

publish: build
	uv publish dist/*
