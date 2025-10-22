# Terminator Game

An interactive multiplayer game demonstrating the power of LangGraph agents with Drasi continuous queries.

## Quick Start

```bash
# 1. Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Navigate to the terminator directory
cd examples/terminator

# 3. Set up environment and install dependencies
cp .env.example .env
# Edit .env with your configuration
uv sync

# 4. Initialize database
psql -d game -f init_db.sql

# 5. Configure Drasi (see Setup section)

# 6. Run backend (terminal 1)
./run-backend.sh

# 7. Run agents (terminal 2)
./run-agents.sh

# 8. Play at http://localhost:8000
```

## Overview

Terminator is a real-time multiplayer game where:
- Players join via a web portal and navigate a 32x64 grid maze
- Three AI-powered terminators (LangGraph agents) hunt down players
- Terminators use **Drasi continuous queries** to discover and track player movements in real-time
- Players must avoid terminators or be eliminated from the game

This example showcases:
- **LangGraph agents** for autonomous AI behavior
- **langchain-drasi** integration for real-time query subscriptions
- **FastAPI** backend with WebSocket support
- **PostgreSQL** for game state persistence
- Real-time multiplayer gameplay

## Architecture

```
┌─────────────────┐
│   Web Browser   │ ← Players connect and play
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│  FastAPI Server │ ← Game backend + WebSocket hub
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │ ← Player positions (source for Drasi)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Drasi MCP     │ ← Continuous queries on player table
└────────┬────────┘
         │ Query subscriptions
         ▼
┌─────────────────┐
│  3 Terminator   │ ← LangGraph agents hunting players
│     Agents      │
└─────────────────┘
```

## Prerequisites

1. **Python 3.11+**
2. **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
3. **PostgreSQL** database
4. **Drasi MCP server** configured with:
   - PostgreSQL source pointing to the game database
   - Continuous queries for player tracking
5. **Azure OpenAI** API access (for the LLM powering agents)

### Installing uv

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Learn more at: https://docs.astral.sh/uv/

## Setup

### 1. Database Setup

Create a PostgreSQL database for the game:

```bash
createdb game
```

Initialize the database schema:

```bash
psql -d game -f init_db.sql
```

### 2. Drasi Configuration

Ensure your Drasi MCP server is running and configured with the resources in the `resources/` folder:

- `sources.yaml` - PostgreSQL source configuration
- `queries.yaml` - Continuous query for idle players

Apply the Drasi resources:

```bash
drasi apply -f resources/sources.yaml
drasi apply -f resources/queries.yaml
```

### 3. Environment Variables

Create a `.env` file in this directory:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=game

# Drasi MCP Server
DRASI_SERVER_URL=http://localhost:8083
DRASI_API_TOKEN=your_token_if_required

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### 4. Install Dependencies

```bash
cd examples/terminator

# Sync all dependencies (creates venv and installs everything)
uv sync
```

This will:
- Create a virtual environment
- Install all dependencies from `pyproject.toml`
- Install `langchain-drasi` from the parent directory (editable)
- Lock dependencies in `uv.lock`

## Running the Game

You need to run two processes: the backend server and the terminator agents.

### Option 1: Using convenience scripts (easiest)

**Terminal 1 - Backend Server:**
```bash
cd examples/terminator
./run-backend.sh
```

**Terminal 2 - Terminator Agents:**
```bash
cd examples/terminator
./run-agents.sh
```

### Option 2: Using uv directly

**Terminal 1 - Backend Server:**
```bash
cd examples/terminator
uv run python backend.py
```

**Terminal 2 - Terminator Agents:**
```bash
cd examples/terminator
uv run python main.py
```

> **Note:** `uv run` automatically uses the virtual environment created by `uv sync`

### Option 3: Using just (if installed)

If you have [just](https://just.systems) installed:

```bash
# One-time setup
just setup
just init-db

# Run backend
just backend

# Run agents (in another terminal)
just agents
```

## How to Play

1. **Open your browser** to `http://localhost:8000`
2. **Enter your player name** (max 20 characters)
3. **Use arrow keys** to move around the maze:
   - `↑` - Move up
   - `↓` - Move down
   - `←` - Move left
   - `→` - Move right
4. **Avoid the red terminators!**
   - Green marker = You
   - Blue markers = Other players
   - Red markers = Terminators
5. **Survive as long as possible!**

## How It Works

### Terminators (LangGraph Agents)

Each terminator is an autonomous LangGraph agent that:

1. **Discovers queries** - On startup, the agent asks the Drasi tool what queries are available
2. **Subscribes to updates** - The agent subscribes to queries that provide player position data
3. **Stores notifications** - When players move, Drasi sends notifications that are stored in the agent's memory
4. **Hunts players** - The terminator uses its memory to track the closest player and move toward them
5. **Eliminates on contact** - When a terminator reaches a player's position, the player is removed from the database

### Key Components

- **`game_map.py`** - Map definition with walls and collision detection
- **`backend.py`** - FastAPI server with player CRUD and WebSocket support
- **`terminator_agent.py`** - LangGraph agent implementation with Drasi integration
- **`main.py`** - Entry point that runs the 3 terminator agents
- **`static/index.html`** - Web UI for players

### Real-Time Synchronization

The backend uses a **periodic broadcast system** to keep all clients synchronized:

- Every 500ms, the backend queries the database for ALL players (including terminators)
- Broadcasts a `state_update` message to all connected WebSocket clients
- Frontend updates all player positions, including terminators (rendered as red markers)
- Detects when players are eliminated (no longer in the update)

This ensures terminators are visible to players even though they update the database directly rather than using the move API.

### Drasi Integration

The terminators use `langchain-drasi` to:
- Call `discover` to find available queries
- Call `subscribe` to start receiving real-time updates
- Receive notifications via `LangGraphMemoryHandler` (injected into conversation memory)
- Receive notifications via custom `TerminatorMemory` handler (for decision-making)

Example agent initialization:

```python
# Create Drasi tool with notification handlers
drasi_tool = create_drasi_tool(
    mcp_config=mcp_config,
    notification_handlers=[memory_handler, langgraph_handler],
)

# Create LangGraph agent with the tool
agent = create_react_agent(
    model=llm,
    tools=[drasi_tool],
    checkpointer=langgraph_handler.checkpointer,
)
```

## Game Map

The game uses a 32 (height) x 64 (width) grid with walls:

```
-----------------------------------------------------------------
|            |               |                    |             |
|                            |                                  |
|            |               |                    |             |
|------------|----  ---------|--------  ----------|-------------|
|            |               |                    |             |
|            |                                    |             |
|            |               |                                  |
|            |               |                    |             |
|--------  --|----  ---------|-----------------  -|-----  ------|
|                                                               |
|                                                               |
|                                                               |
|                                                               |
|---------------------------------------------------------------|
```

Players and terminators spawn at random valid positions and cannot walk through walls.

## Customization

### Adjust Terminator Behavior

In `terminator_agent.py`, you can modify:
- **Move speed** - Change the `await asyncio.sleep(1.0)` value in `run_terminator()`
- **AI temperature** - Adjust the LLM temperature for more/less random behavior
- **Number of terminators** - Modify the loop in `main.py` to spawn more or fewer

### Modify the Map

Edit the `WALLS` list in `game_map.py` to create your own maze layout.

### Add New Queries

Create additional continuous queries in `resources/queries.yaml` to give terminators more information (e.g., player velocity, clustering, etc.)

## Troubleshooting

### Import Error: ModuleNotFoundError: No module named 'langchain_core.memory'
This error has been fixed in the latest version. Make sure you have the latest `langchain-drasi`:
```bash
cd ../..  # Go to langchain-drasi root
uv sync   # Or pip install -e .
cd examples/terminator
uv sync
```

The terminator game uses `LangGraphMemoryHandler` which works with modern LangChain versions.

### Terminators not moving
- Check that the Drasi MCP server is running and accessible
- Verify the `DRASI_SERVER_URL` in your `.env` file
- Check terminator logs for subscription errors

### Players can't join
- Ensure PostgreSQL is running and accessible
- Verify database credentials in `.env`
- Check that the `player` table exists

### WebSocket connection fails
- Make sure the backend server is running on port 8000
- Check browser console for connection errors

### Port 8000 already in use
If you see "address already in use" error:
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9
# Or use a different port
uvicorn backend:app --host 0.0.0.0 --port 8001
```

## License

MIT License - see the main repository for details.

## Learn More

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Drasi Project](https://drasi.io/)
- [langchain-drasi Library](../../README.md)
