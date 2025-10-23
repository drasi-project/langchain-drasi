# Terminator Game - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.11+
- PostgreSQL installed and running
- Drasi MCP server configured
- Azure OpenAI API access

## Installation

### 1. Install uv (one-time)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and navigate

```bash
cd examples/terminator
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required settings:
- Database credentials
- `DRASI_SERVER_URL`
- Azure OpenAI credentials

### 4. Install dependencies

```bash
uv sync
```

### 5. Initialize database

```bash
psql -d game -f init_db.sql
```

### 6. Configure Drasi resources

```bash
drasi apply -f resources/sources.yaml
drasi apply -f resources/queries.yaml
```

## Run

**Terminal 1:**
```bash
make backend
```

**Terminal 2:**
```bash
make terminator
```

## Play

Open http://localhost:8000 in your browser!

## Controls

- **Arrow Keys** - Move your player
- **Goal** - Avoid the red terminators!

---

For detailed information, see [README.md](README.md)
