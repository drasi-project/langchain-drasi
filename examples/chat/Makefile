# Makefile for Chat Examples

.PHONY: help install langchain langgraph setup clean

# Default target - show available commands
help:
	@echo "Available targets:"
	@echo "  make install    - Install dependencies using uv"
	@echo "  make langchain  - Run the LangChain ReAct sample"
	@echo "  make langgraph  - Run the LangGraph ReAct sample"
	@echo "  make setup      - Full setup (install dependencies)"

# Install dependencies using uv
install:
	uv sync

# Run the LangChain ReAct sample
langchain:
	uv run python langchain_react.py

# Run the LangGraph ReAct sample
langgraph:
	uv run python langgraph_react.py

# Full setup
setup: install
	@echo ""
	@echo "✓ Setup complete!"
	@echo "  Next steps:"
	@echo "  1. Configure Drasi with appropriate resources"
	@echo "  2. Run 'make langchain' to run the LangChain sample"
	@echo "  3. Run 'make langgraph' to run the LangGraph sample"

