"""Terminator agent that hunts players using Drasi real-time queries."""

import os
import asyncpg
from langchain_openai import AzureChatOpenAI

from langchain_drasi import create_drasi_tool, MCPConnectionConfig

from game_map import get_random_spawn_position
from .sensor import SensorHandler
from .workflow import build_hunting_workflow, HuntingState


class TerminatorAgent:
    """A terminator agent that hunts players using Drasi for real-time position tracking."""

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
        self.llm = llm

        # Create Drasi notification handler
        self.sensor_handler = SensorHandler(agent_id)

        # Configure Drasi connection
        mcp_config = MCPConnectionConfig(
            server_url=drasi_server_url,
            headers={
                "Authorization": f"Bearer {os.getenv('DRASI_API_TOKEN')}"
            } if os.getenv("DRASI_API_TOKEN") else None,
            timeout=30.0,
        )

        # Create Drasi tool with notification handler
        self.drasi_tool = create_drasi_tool(
            mcp_config=mcp_config,
            notification_handlers=[self.sensor_handler],
        )

        self.initialized = False
        self.current_path: list[tuple[int, int]] = []
        self.current_target: str | None = None

        # Build hunting workflow
        self.hunting_workflow = build_hunting_workflow(self, self.drasi_tool)

    async def initialize(self) -> None:
        """Initialize the terminator by inserting into database."""
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
        print(f"[{self.agent_id}] Query subscriptions will be set up by workflow")

    async def _move_to(self, new_x: int, new_y: int) -> None:
        """Move to a new position and check collisions."""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE player SET x = $1, y = $2 WHERE id = $3",
                new_x, new_y, self.agent_id
            )

        self.x, self.y = new_x, new_y
        print(f"[{self.agent_id}] Moved to ({self.x}, {self.y})")

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
                print(f"[{self.agent_id}] ⚡ ELIMINATED player '{player_id}' at ({self.x},{self.y})!")
                # Log to sensor so LLM knows this area is now clear
                self.sensor_handler.custom_log(f"Successfully eliminated player {player_id} at position ({self.x},{self.y})")

    async def run(self) -> None:
        """Run the terminator continuously with the hunting workflow."""
        # Create initial state
        initial_state: HuntingState = {
            "messages": [],
            "current_position": (self.x, self.y),
            "path": [],
            "current_target": self.current_target,
            "reevaluate_plan": False,
            "sensor_log": [],
            "known_targets": [],
        }

        # Run the workflow - it will loop internally with high recursion limit
        config = {"recursion_limit": 10000}
        try:
            await self.hunting_workflow.ainvoke(initial_state, config=config)
        except Exception as e:
            print(f"[{self.agent_id}] ⚠ Error in hunting workflow: {e}")

    async def shutdown(self) -> None:
        """Clean up the terminator."""
        print(f"[{self.agent_id}] Shutdown")
