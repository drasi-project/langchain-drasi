#!/bin/sh
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

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESOURCES_DIR="$SCRIPT_DIR/../resources"
EXAMPLE_DIR="$REPO_ROOT/examples/hide_and_seek"

echo "=== Creating k3d cluster ==="

# Wait for Docker daemon to be ready
until docker info >/dev/null 2>&1; do
  echo "Waiting for Docker daemon..."
  sleep 2
done

# Create k3d cluster if not already running
if ! kubectl cluster-info >/dev/null 2>&1; then
  k3d cluster delete 2>/dev/null || true
  k3d cluster create
fi

echo "=== Deploying PostgreSQL ==="
kubectl apply -f "$RESOURCES_DIR/game-postgres.yaml"
sleep 15
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s

# Wait for PostgreSQL to be fully ready for connections
echo "Waiting for PostgreSQL to accept connections..."
until kubectl exec deploy/postgres -- pg_isready -U postgres -d game >/dev/null 2>&1; do
  sleep 2
done

echo "=== Installing Drasi ==="
sleep 30
drasi init
drasi ingress init --use-existing --ingress-class-name traefik --ingress-ip-address 127.0.0.1

echo "=== Applying Drasi resources ==="

# Apply the Codespace-compatible source (uses k8s internal hostname)
drasi apply -f "$RESOURCES_DIR/game-source.yaml"

# Apply queries and reaction from the example
drasi apply -f "$EXAMPLE_DIR/resources/queries.yaml"
drasi apply -f "$EXAMPLE_DIR/resources/reaction.yaml"

echo "=== Installing Python dependencies ==="
cd "$EXAMPLE_DIR"
"$HOME/.local/bin/uv" sync

echo "=== Post-create setup complete ==="
