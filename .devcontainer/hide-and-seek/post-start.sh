#!/bin/bash
# Copyright 2025 The Drasi Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EXAMPLE_DIR="$REPO_ROOT/examples/hide_and_seek"
LOG_DIR="/tmp"

# Function to check if a port is already in use
check_port() {
  local port=$1
  if lsof -i :"$port" > /dev/null 2>&1; then
    echo "Port $port is already in use. Skipping port-forward."
    return 1
  fi
  return 0
}

# Verify cluster connectivity
echo "Checking cluster connectivity..."
if ! kubectl cluster-info > /dev/null 2>&1; then
  echo "Error: Cannot connect to the cluster. Check k3d setup."
  exit 1
fi

# Clean up any existing port-forward and tunnel processes
pkill -f "kubectl port-forward svc/postgres" 2>/dev/null || true
pkill -f "kubectl port-forward -n kube-system svc/traefik" 2>/dev/null || true
pkill -f "drasi tunnel reaction seeker-mcp" 2>/dev/null || true

# Forward PostgreSQL port
if check_port 5432; then
  echo "Starting port-forward for PostgreSQL..."
  nohup kubectl port-forward svc/postgres 5432:5432 > "$LOG_DIR/postgres-port-forward.log" 2>&1 &
  sleep 2
  if ps aux | grep -q "[k]ubectl port-forward svc/postgres"; then
    echo "PostgreSQL port-forward started (logs at $LOG_DIR/postgres-port-forward.log)."
  else
    echo "Error: PostgreSQL port-forward failed to start."
  fi
fi

# Forward Traefik port (for Drasi ingress access)
if check_port 8080; then
  echo "Starting port-forward for Traefik..."
  nohup kubectl port-forward -n kube-system svc/traefik 8080:80 > "$LOG_DIR/traefik-port-forward.log" 2>&1 &
  sleep 2
  if ps aux | grep -q "[k]ubectl port-forward -n kube-system svc/traefik"; then
    echo "Traefik port-forward started (logs at $LOG_DIR/traefik-port-forward.log)."
  else
    echo "Error: Traefik port-forward failed to start."
  fi
fi

# Start Drasi tunnel for MCP reaction
if check_port 8083; then
  echo "Starting Drasi tunnel for MCP reaction on port 8083..."
  nohup drasi tunnel reaction seeker-mcp 8083 > "$LOG_DIR/drasi-tunnel.log" 2>&1 &
  sleep 2
  echo "Drasi tunnel started (logs at $LOG_DIR/drasi-tunnel.log)."
fi

# Generate .env file from environment variables / Codespace secrets
echo "Generating .env file..."
ENV_FILE="$EXAMPLE_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" << EOF
# Database Configuration (auto-configured for Codespace)
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-test}
DB_NAME=${DB_NAME:-game}

# Drasi MCP Server (auto-configured for Codespace)
DRASI_SERVER_URL=${DRASI_SERVER_URL:-http://localhost:8083}
DRASI_API_TOKEN=${DRASI_API_TOKEN:-}

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY:-your_api_key_here}
AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT:-https://your-endpoint.openai.azure.com/}
AZURE_OPENAI_DEPLOYMENT=${AZURE_OPENAI_DEPLOYMENT:-gpt-4o-mini}
AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION:-2024-02-15-preview}
EOF

  if [ "${AZURE_OPENAI_API_KEY:-}" = "your_api_key_here" ] || [ -z "${AZURE_OPENAI_API_KEY:-}" ]; then
    echo ""
    echo "⚠️  Azure OpenAI credentials not found in Codespace secrets."
    echo "   Please edit $ENV_FILE with your Azure OpenAI credentials."
    echo "   Or set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and"
    echo "   AZURE_OPENAI_DEPLOYMENT as Codespace secrets for auto-configuration."
  else
    echo "✓ .env file generated with Azure OpenAI credentials from Codespace secrets."
  fi
else
  echo "✓ .env file already exists, skipping generation."
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To start the game:"
echo "  Terminal 1: make backend"
echo "  Terminal 2: make seeker"
echo ""
