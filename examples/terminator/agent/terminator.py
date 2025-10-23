"""Terminator agent that hunts players using Drasi real-time queries."""

import os
import httpx
from langchain_openai import AzureChatOpenAI

from langchain_drasi import create_drasi_tool, MCPConnectionConfig

from .sensor import SensorHandler
from .workflow import build_hunting_workflow, HuntingState


class TerminatorAgent:
    """A terminator agent that hunts players using Drasi for real-time position tracking."""

    def __init__(
        self,
        agent_id: str,
        api_base_url: str,
        drasi_server_url: str,
        llm: AzureChatOpenAI,
    ):
        self.agent_id = agent_id
        self.api_base_url = api_base_url
        self.http_client = httpx.AsyncClient(base_url=api_base_url, timeout=10.0)
        self.x, self.y = 0, 0  # Will be set by initialize()
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
        """Initialize the terminator by creating via API."""
        try:
            response = await self.http_client.post(
                "/api/players",
                json={"id": self.agent_id, "type": "ai"}
            )
            response.raise_for_status()
            player_data = response.json()
            self.x = player_data["x"]
            self.y = player_data["y"]
            print(f"[{self.agent_id}] Spawned at ({self.x}, {self.y})")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                # Player already exists, get current position
                response = await self.http_client.get(f"/api/players/{self.agent_id}")
                response.raise_for_status()
                player_data = response.json()
                self.x = player_data["x"]
                self.y = player_data["y"]
                print(f"[{self.agent_id}] Already exists at ({self.x}, {self.y})")
            else:
                raise

        print(f"[{self.agent_id}] Query subscriptions will be set up by workflow")

    async def _move_to(self, new_x: int, new_y: int) -> None:
        """Move to a new position. Collisions are detected by the server."""
        # Calculate direction from current position to new position
        direction = None
        if new_y < self.y:
            direction = "up"
        elif new_y > self.y:
            direction = "down"
        elif new_x < self.x:
            direction = "left"
        elif new_x > self.x:
            direction = "right"

        if direction:
            try:
                response = await self.http_client.post(
                    f"/api/players/{self.agent_id}/move",
                    json={"direction": direction}
                )
                response.raise_for_status()
                move_data = response.json()
                self.x = move_data["x"]
                self.y = move_data["y"]
                print(f"[{self.agent_id}] Moved to ({self.x}, {self.y})")

                # Check if any players were eliminated
                eliminated = move_data.get("eliminated_players", [])
                for player_id in eliminated:
                    print(f"[{self.agent_id}] ⚡ ELIMINATED player '{player_id}' at ({self.x},{self.y})!")
                    # Log to sensor so LLM knows this area is now clear
                    self.sensor_handler.custom_log(f"Successfully eliminated player {player_id} at position ({self.x},{self.y})")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    print(f"[{self.agent_id}] ⚠ Player not found, may have been eliminated")
                else:
                    print(f"[{self.agent_id}] ⚠ Move failed: {e}")
                return

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
        await self.http_client.aclose()
        print(f"[{self.agent_id}] Shutdown")
