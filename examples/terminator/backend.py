"""FastAPI backend server for the Terminator game.

This server provides:
- Player CRUD operations
- WebSocket connections for real-time updates
- PostgreSQL database integration
"""

import os
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncpg
from dotenv import load_dotenv

from game_map import (
    get_random_spawn_position,
    is_valid_position,
    MAP_WIDTH,
    MAP_HEIGHT,
    WALLS,
)

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "test")
DB_NAME = os.getenv("DB_NAME", "game")

# Global state
db_pool: Optional[asyncpg.Pool] = None
websocket_connections: List[WebSocket] = []


class Player(BaseModel):
    """Player model."""
    id: str
    x: int
    y: int
    type: str  # 'human' or 'ai'


class PlayerCreate(BaseModel):
    """Player creation request."""
    id: str


class MoveRequest(BaseModel):
    """Player move request."""
    direction: str  # "up", "down", "left", "right"


class PlayerPosition(BaseModel):
    """Player position update from external service."""
    x: int
    y: int
    type: str  # 'human' or 'ai'


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global db_pool

    # Startup: Create database connection pool
    db_pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        min_size=5,
        max_size=20,
    )
    print(f"Database pool created: {DB_HOST}:{DB_PORT}/{DB_NAME}")

    # Clear player table on startup
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM player")
    print("Cleared player table")

    yield

    # Shutdown: Close database pool
    if db_pool:
        await db_pool.close()
        print("Database pool closed")


app = FastAPI(title="Terminator Game API", lifespan=lifespan)


async def broadcast_update(message: dict) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    disconnected = []
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)

    # Remove disconnected clients
    for ws in disconnected:
        websocket_connections.remove(ws)


@app.get("/api/players", response_model=List[Player])
async def get_players():
    """Get all players."""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, x, y, type FROM player ORDER BY id")
        return [Player(id=row["id"], x=row["x"], y=row["y"], type=row["type"]) for row in rows]


@app.get("/api/players/{player_id}", response_model=Player)
async def get_player(player_id: str):
    """Get a specific player."""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, x, y, type FROM player WHERE id = $1", player_id)
        if not row:
            raise HTTPException(status_code=404, detail="Player not found")
        return Player(id=row["id"], x=row["x"], y=row["y"], type=row["type"])


@app.post("/api/players", response_model=Player)
async def create_player(player: PlayerCreate):
    """Create a new player with a random spawn position."""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Validate player ID
    if len(player.id) > 20 or len(player.id) < 1:
        raise HTTPException(status_code=400, detail="Player ID must be 1-20 characters")

    # Get random spawn position
    x, y = get_random_spawn_position()

    async with db_pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO player (id, x, y, type) VALUES ($1, $2, $3, $4)",
                player.id, x, y, 'human'
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Player ID already exists")

    new_player = Player(id=player.id, x=x, y=y, type='human')

    # Broadcast player joined
    await broadcast_update({
        "type": "player_joined",
        "player": new_player.model_dump()
    })

    return new_player


@app.delete("/api/players/{player_id}")
async def delete_player(player_id: str):
    """Delete a player."""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM player WHERE id = $1", player_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Player not found")

    # Broadcast player left
    await broadcast_update({
        "type": "player_left",
        "player_id": player_id
    })

    return {"message": "Player deleted"}


@app.post("/api/players/{player_id}/move", response_model=Player)
async def move_player(player_id: str, move: MoveRequest):
    """Move a player in the specified direction."""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Get current position and type
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT x, y, type FROM player WHERE id = $1", player_id)
        if not row:
            raise HTTPException(status_code=404, detail="Player not found")

        current_x, current_y, player_type = row["x"], row["y"], row["type"]

    # Calculate new position
    new_x, new_y = current_x, current_y
    if move.direction == "up":
        new_y -= 1
    elif move.direction == "down":
        new_y += 1
    elif move.direction == "left":
        new_x -= 1
    elif move.direction == "right":
        new_x += 1
    else:
        raise HTTPException(status_code=400, detail="Invalid direction")

    # Validate new position
    if not is_valid_position(new_x, new_y):
        raise HTTPException(status_code=400, detail="Cannot move there (wall or out of bounds)")

    # Update position
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE player SET x = $1, y = $2 WHERE id = $3",
            new_x, new_y, player_id
        )

    updated_player = Player(id=player_id, x=new_x, y=new_y, type=player_type)

    # Broadcast player moved
    await broadcast_update({
        "type": "player_moved",
        "player": updated_player.model_dump()
    })

    return updated_player


@app.get("/api/map")
async def get_map_info():
    """Get map information."""
    return {
        "width": MAP_WIDTH,
        "height": MAP_HEIGHT,
        "walls": WALLS,
    }


# @app.put("/api/webhook/{player_id}")
# async def player_position_changed(player_id: str, position: PlayerPosition):
#     """
#     Receive player position update from external service (e.g., Drasi).
#     This endpoint does not modify the database - it only broadcasts to WebSocket clients.
#     """
#     # Broadcast player moved
#     await broadcast_update({
#         "type": "player_moved",
#         "player": {
#             "id": player_id,
#             "x": position.x,
#             "y": position.y,
#             "type": position.type
#         }
#     })
#     return {"message": "Position update broadcasted"}


# @app.delete("/api/webhook/{player_id}")
# async def player_removed(player_id: str):
#     """
#     Receive player removal notification from external service (e.g., Drasi).
#     This endpoint does not modify the database - it only broadcasts to WebSocket clients.
#     """
#     # Broadcast player left
#     await broadcast_update({
#         "type": "player_left",
#         "player_id": player_id
#     })
#     return {"message": "Player removal broadcasted"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time game updates."""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        # Send initial state
        if db_pool:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT id, x, y, type FROM player")
                players = [Player(id=row["id"], x=row["x"], y=row["y"], type=row["type"]).model_dump() for row in rows]
                await websocket.send_json({
                    "type": "initial_state",
                    "players": players
                })

        # Keep connection alive and listen for messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)


# Serve static files (HTML, CSS, JS)
@app.get("/")
async def serve_index():
    """Serve the main HTML page."""
    import pathlib
    static_path = pathlib.Path(__file__).parent / "static" / "index.html"
    return FileResponse(str(static_path))


def main() -> None:
    """Main entry point for the backend server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
