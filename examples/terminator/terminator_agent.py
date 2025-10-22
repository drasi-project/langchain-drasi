"""LangGraph-powered Terminator AI agent.

This agent uses Drasi queries to track player movements and hunt them down.
"""

import asyncio
import os
import random
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import asyncpg

from langchain_drasi import (
    create_drasi_tool,
    MCPConnectionConfig,
    LangGraphMemoryHandler,
)
from langchain_drasi.callbacks import BaseDrasiNotificationHandler

from game_map import get_random_spawn_position, get_adjacent_positions, distance, is_wall, MAP_HEIGHT, MAP_WIDTH

# Load environment variables
load_dotenv()


class TerminatorMemory(BaseDrasiNotificationHandler):
    """Handler that stores player positions in memory for the terminator."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.player_positions: Dict[str, tuple[int, int]] = {}

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Handle new player data - just log it, LLM will interpret."""
        print(f"[{self.agent_id}] 🔔 Notification (added) from '{query_name}': {added_data}")

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Handle player position updates - just log it, LLM will interpret."""
        print(f"[{self.agent_id}] 🔔 Notification (updated) from '{query_name}': {updated_data}")

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Handle player removal - just log it, LLM will interpret."""
        print(f"[{self.agent_id}] 🔔 Notification (deleted) from '{query_name}': {deleted_data}")

    def get_closest_player(self, terminator_x: int, terminator_y: int) -> Optional[tuple[str, int, int]]:
        """Find the closest player to the terminator."""
        if not self.player_positions:
            return None

        closest_player = None
        min_distance = float('inf')

        for player_id, (px, py) in self.player_positions.items():
            dist = distance(terminator_x, terminator_y, px, py)
            if dist < min_distance:
                min_distance = dist
                closest_player = (player_id, px, py)

        return closest_player


class TerminatorAgent:
    """A terminator agent that hunts players."""

    def __init__(
        self,
        agent_id: str,
        db_pool: asyncpg.Pool,
        drasi_server_url: str,
        llm: AzureChatOpenAI,
    ):
        self.agent_id = agent_id
        self.db_pool = db_pool
        self.x, self.y = get_random_spawn_position()
        self.memory = TerminatorMemory(agent_id)

        # Create LangGraph memory and thread ID
        self.langgraph_memory = MemorySaver()
        self.thread_id = f"terminator-{agent_id}"

        # Configure Drasi connection
        mcp_config = MCPConnectionConfig(
            server_url=drasi_server_url,
            headers={
                "Authorization": f"Bearer {os.getenv('DRASI_API_TOKEN')}"
            } if os.getenv("DRASI_API_TOKEN") else None,
            timeout=30.0,
        )

        # Create handlers
        langgraph_handler = LangGraphMemoryHandler(self.langgraph_memory, self.thread_id)

        # Create Drasi tool with both handlers
        self.drasi_tool = create_drasi_tool(
            mcp_config=mcp_config,
            notification_handlers=[self.memory, langgraph_handler],
        )

        # Create LangGraph agent
        self.agent = create_react_agent(
            model=llm,
            tools=[self.drasi_tool],
            checkpointer=langgraph_handler.checkpointer,
        )

        self.config = {"configurable": {"thread_id": self.thread_id}}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the terminator by discovering and subscribing to queries."""
        if self.initialized:
            return

        # Insert terminator into database
        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO player (id, x, y, type) VALUES ($1, $2, $3, $4)",
                    self.agent_id, self.x, self.y, 'ai'
                )
            except asyncpg.UniqueViolationError:
                # Already exists, update position
                await conn.execute(
                    "UPDATE player SET x = $1, y = $2, type = $3 WHERE id = $4",
                    self.x, self.y, 'ai', self.agent_id
                )

        print(f"[{self.agent_id}] Spawned at ({self.x}, {self.y})")

        # Use the agent to discover and subscribe to queries
        initialization_prompt = """You are an AI agent in a game that needs to track player positions.

        Please perform these steps in order:
        1. Use the drasi_query tool with operation="discover" to see what queries are available
        2. For each query you discover, use operation="read" to see what data it provides
        3. Subscribe to ALL queries that return player position data (p.id, p.x, p.y) using operation="subscribe"

        This will give you real-time notifications about player positions for the game.

        Execute these steps now and report what you did."""

        try:
            print(f"[{self.agent_id}] Starting initialization - discovering and subscribing to queries...")
            result = await self.agent.ainvoke(
                {"messages": [("user", initialization_prompt)]},
                config=self.config
            )

            # Print the agent's response for debugging
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    print(f"[{self.agent_id}] Agent response: {last_message.content}")

            print(f"[{self.agent_id}] ✓ Initialization complete - subscribed to queries")
            print(f"[{self.agent_id}] Known players: {list(self.memory.player_positions.keys())}")
        except Exception as e:
            print(f"[{self.agent_id}] ✗ Error during initialization: {e}")
            import traceback
            traceback.print_exc()

        self.initialized = True

    def _get_map_view(self, target_x: int, target_y: int, view_radius: int = 10) -> str:
        """Generate a text map view showing walls, current position, and target."""
        # Calculate bounding box
        min_x = max(0, min(self.x, target_x) - view_radius)
        max_x = min(MAP_WIDTH, max(self.x, target_x) + view_radius)
        min_y = max(0, min(self.y, target_y) - view_radius)
        max_y = min(MAP_HEIGHT, max(self.y, target_y) + view_radius)

        lines = []
        for y in range(min_y, max_y):
            line = ""
            for x in range(min_x, max_x):
                if x == self.x and y == self.y:
                    line += "T"  # Terminator
                elif x == target_x and y == target_y:
                    line += "P"  # Player
                elif is_wall(x, y):
                    line += "#"  # Wall
                else:
                    line += "."  # Empty space
            lines.append(line)

        return "\n".join(lines)

    async def move_towards_target(self, target_x: int, target_y: int) -> None:
        """Use LLM to plan next move towards target, avoiding walls."""
        # Get valid adjacent positions
        valid_moves = get_adjacent_positions(self.x, self.y)

        if not valid_moves:
            return

        # Generate map view
        map_view = self._get_map_view(target_x, target_y)

        # Format valid moves for the LLM
        move_options = []
        for i, (mx, my) in enumerate(valid_moves):
            direction = ""
            if mx < self.x:
                direction = "left"
            elif mx > self.x:
                direction = "right"
            elif my < self.y:
                direction = "up"
            elif my > self.y:
                direction = "down"
            move_options.append(f"{i}: {direction} to ({mx},{my})")

        # Ask LLM to plan the next move
        planning_prompt = f"""You need to move from your current position to the target.

Current position: ({self.x}, {self.y})
Target position: ({target_x}, {target_y})

Map view (T=you, P=target, #=wall, .=empty):
{map_view}

Available moves:
{chr(10).join(move_options)}

Choose the best move that gets you closer to the target while avoiding walls.
Respond with ONLY the move number (e.g., "0" or "1" or "2" or "3")."""

        try:
            result = await self.agent.ainvoke(
                {"messages": [("user", planning_prompt)]},
                config=self.config
            )

            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    response = last_message.content.strip()
                    print(f"[{self.agent_id}] LLM chose move: {response}")

                    try:
                        move_index = int(response)
                        if 0 <= move_index < len(valid_moves):
                            new_x, new_y = valid_moves[move_index]

                            # Update database
                            async with self.db_pool.acquire() as conn:
                                await conn.execute(
                                    "UPDATE player SET x = $1, y = $2 WHERE id = $3",
                                    new_x, new_y, self.agent_id
                                )

                            self.x, self.y = new_x, new_y
                            print(f"[{self.agent_id}] Moved to ({self.x}, {self.y}) targeting ({target_x}, {target_y})")

                            # Check if we caught a player
                            await self.check_collisions()
                            return
                    except ValueError:
                        print(f"[{self.agent_id}] ⚠ Could not parse move index: {response}")
        except Exception as e:
            print(f"[{self.agent_id}] ⚠ Error asking LLM for move: {e}")

        # Fallback: use greedy approach
        best_move = None
        best_distance = float('inf')
        for new_x, new_y in valid_moves:
            dist = distance(new_x, new_y, target_x, target_y)
            if dist < best_distance:
                best_distance = dist
                best_move = (new_x, new_y)

        if best_move:
            new_x, new_y = best_move
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE player SET x = $1, y = $2 WHERE id = $3",
                    new_x, new_y, self.agent_id
                )
            self.x, self.y = new_x, new_y
            print(f"[{self.agent_id}] Moved to ({self.x}, {self.y}) using fallback")
            await self.check_collisions()

    async def check_collisions(self) -> None:
        """Check if the terminator has caught any players."""
        async with self.db_pool.acquire() as conn:
            # Find human players at the same position
            caught_players = await conn.fetch(
                "SELECT id FROM player WHERE x = $1 AND y = $2 AND id != $3 AND type = 'human'",
                self.x, self.y, self.agent_id
            )

            for row in caught_players:
                player_id = row["id"]
                await conn.execute("DELETE FROM player WHERE id = $1", player_id)
                print(f"[{self.agent_id}] ELIMINATED player '{player_id}'!")

    async def run_step(self) -> None:
        """Execute one step of the terminator's behavior."""
        # Ask the LLM where to move based on notifications
        move_prompt = f"""Based on the notifications you've received about player positions,
        I am currently at position ({self.x}, {self.y}).

        What is the nearest player position to me? Respond with just the coordinates in format: x,y
        If no players are known, respond with: none"""

        try:
            result = await self.agent.ainvoke(
                {"messages": [("user", move_prompt)]},
                config=self.config
            )

            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    response = last_message.content.strip().lower()
                    print(f"[{self.agent_id}] LLM response about target: {response}")

                    if response != "none" and "," in response:
                        # Parse coordinates
                        try:
                            parts = response.replace(" ", "").split(",")
                            target_x = int(parts[0])
                            target_y = int(parts[1])
                            print(f"[{self.agent_id}] Hunting target at ({target_x}, {target_y})")
                            await self.move_towards_target(target_x, target_y)
                            return
                        except (ValueError, IndexError):
                            print(f"[{self.agent_id}] ⚠ Could not parse coordinates: {response}")

        except Exception as e:
            print(f"[{self.agent_id}] ⚠ Error asking LLM for move: {e}")

        # Fallback: patrol randomly
        print(f"[{self.agent_id}] No target - patrolling randomly")
        valid_moves = get_adjacent_positions(self.x, self.y)
        if valid_moves:
            new_x, new_y = random.choice(valid_moves)
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE player SET x = $1, y = $2 WHERE id = $3",
                    new_x, new_y, self.agent_id
                )
            self.x, self.y = new_x, new_y
            print(f"[{self.agent_id}] Patrolling... moved to ({self.x}, {self.y})")

    async def shutdown(self) -> None:
        """Clean up the terminator."""
        print(f"[{self.agent_id}] Shutdown")


async def run_terminator(agent_id: str, db_pool: asyncpg.Pool) -> None:
    """Run a single terminator agent."""
    # Configure LLM
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=0.1,
    )

    # Configure Drasi server
    drasi_server_url = os.getenv("DRASI_SERVER_URL", "http://localhost:8083")

    # Create and initialize terminator
    terminator = TerminatorAgent(agent_id, db_pool, drasi_server_url, llm)
    await terminator.initialize()

    # Run the terminator loop (move every second)
    try:
        while True:
            await asyncio.sleep(0.5)
            await terminator.run_step()
    except asyncio.CancelledError:
        await terminator.shutdown()
        raise
