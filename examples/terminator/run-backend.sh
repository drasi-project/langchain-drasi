#!/bin/bash
# Quick start script for the backend server using uv

set -e

echo "Starting Terminator Game Backend Server..."
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Copy .env.example to .env and configure your settings."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Running backend with uv..."
uv run python backend.py
