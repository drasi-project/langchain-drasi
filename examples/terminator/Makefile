# Makefile for Terminator Game

.PHONY: help install backend terminator init-db setup-env setup clean

# Default target - show available commands
help:
	@echo "Available targets:"
	@echo "  make install     - Install dependencies using uv"
	@echo "  make backend     - Run the backend server"
	@echo "  make terminator  - Run a terminator agent"
	@echo "  make init-db     - Initialize the database"
	@echo "  make setup-env   - Create .env from example"
	@echo "  make setup       - Full setup (env + install)"
	@echo "  make clean       - Clean up generated files"

# Install dependencies using uv
install:
	uv sync

# Run the backend server
backend:
	uv run python backend.py

# Run a terminator agent
terminator:
	uv run python terminator.py

# Initialize the database
init-db:
	@echo "Initializing database..."
	@psql -d $${DB_NAME:-game} -f init_db.sql

# Create .env from example
setup-env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file from .env.example"; \
		echo "  Please edit .env and configure your settings"; \
	else \
		echo "✗ .env file already exists"; \
	fi

# Full setup (env + install)
setup: setup-env install
	@echo ""
	@echo "✓ Setup complete!"
	@echo "  Next steps:"
	@echo "  1. Edit .env with your configuration"
	@echo "  2. Run 'make init-db' to initialize the database"
	@echo "  3. Configure Drasi with resources in resources/"
	@echo "  4. Run 'make backend' in one terminal"
	@echo "  5. Run 'make terminator' in another terminal (run multiple times for multiple agents)"

# Clean up generated files
clean:
	rm -rf .venv uv.lock
	@echo "✓ Cleaned up virtual environment and lock file"
