import asyncio
import json
import os
import random
import time
from dotenv import load_dotenv
from queue import Queue

from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage
from typing_extensions import TypedDict
from typing import Any, List, Dict
import asyncpg

from langchain_drasi import (
    create_drasi_tool,
    MCPConnectionConfig,
)
from langchain_drasi.callbacks import BaseDrasiNotificationHandler

from game_map import (
    get_random_spawn_position,
    get_adjacent_positions,
    is_valid_position,
    MAP_WIDTH,
    MAP_HEIGHT,
    WALL_CELLS,
)

from collections import deque

# Load environment variables
load_dotenv()


class SensorHandler(BaseDrasiNotificationHandler):

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.notification_queue = Queue()

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        notification = {
            "type": "added",
            "query": query_name,
            "data": added_data,
            "timestamp": time.time()
        }
        self.notification_queue.put(notification)
        print(f"[{self.agent_id}] 🔔 Notification (added) from '{query_name}': {added_data}")

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        notification = {
            "type": "updated",
            "query": query_name,
            "data": updated_data,
            "timestamp": time.time()
        }
        self.notification_queue.put(notification)
        print(f"[{self.agent_id}] 🔔 Notification (updated) from '{query_name}': {updated_data}")

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        notification = {
            "type": "deleted",
            "query": query_name,
            "data": deleted_data,
            "timestamp": time.time()
        }
        self.notification_queue.put(notification)
        print(f"[{self.agent_id}] 🔔 Notification (deleted) from '{query_name}': {deleted_data}")

    def has_new_notifications(self) -> bool:
        return not self.notification_queue.empty()
    
    def get_new_notifications(self) -> list:
        notifications = []
        while not self.notification_queue.empty():
            notifications.append(self.notification_queue.get())
        return notifications

    def custom_log(self, message: str) -> None:
        print(f"[{self.agent_id}] [Custom Sensor Log] {message}")
        notification = {
            "data": message,
            "timestamp": time.time()
        }
        self.notification_queue.put(notification)


class HuntingState(MessagesState):
    current_position: tuple[int, int]
    path: list[tuple[int, int]]
    current_target: str | None
    reevaluate_plan: bool
    sensor_log: list[str]
    known_targets: list[dict]  # List of {"player_id": str, "x": int, "y": int}


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
        self.llm = llm
      
        # Create notification logger
        self.sensor_handler = SensorHandler(agent_id)

        # Configure Drasi connection
        mcp_config = MCPConnectionConfig(
            server_url=drasi_server_url,
            headers={
                "Authorization": f"Bearer {os.getenv('DRASI_API_TOKEN')}"
            } if os.getenv("DRASI_API_TOKEN") else None,
            timeout=30.0,
        )

        # Create Drasi tool with notification logger
        self.drasi_tool = create_drasi_tool(
            mcp_config=mcp_config,
            notification_handlers=[self.sensor_handler],
        )

        self.initialized = False
        self.current_path: list[tuple[int, int]] = []
        self.current_target: str | None = None

        # Build custom hunting workflow
        self.hunting_workflow = self._build_hunting_workflow()

    # ------------------------------------------------------------------------
    # Path Validation & Planning Helpers
    # ------------------------------------------------------------------------

    def _find_path_bfs(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
        """Find shortest path from start to goal using BFS, avoiding walls."""
        if start == goal:
            print(f"[{self.agent_id}] BFS: start == goal at {start}")
            return []

        # Check if goal is a wall
        if goal in WALL_CELLS:
            print(f"[{self.agent_id}] BFS: goal {goal} is a WALL!")
            return []

        queue = deque([(start, [])])
        visited = {start}
        max_iterations = MAP_WIDTH * MAP_HEIGHT  # Safety limit

        iteration = 0
        while queue and iteration < max_iterations:
            iteration += 1
            (x, y), path = queue.popleft()

            # Check all adjacent positions
            for next_x, next_y in get_adjacent_positions(x, y):
                if (next_x, next_y) in visited:
                    continue

                visited.add((next_x, next_y))
                new_path = path + [(next_x, next_y)]

                # Found the goal
                if (next_x, next_y) == goal:
                    print(f"[{self.agent_id}] BFS: Found path in {iteration} iterations, {len(new_path)} steps")
                    return new_path

                queue.append(((next_x, next_y), new_path))

        # No path found
        print(f"[{self.agent_id}] BFS: No path found from {start} to {goal} (visited {len(visited)} cells)")
        return []

    def _get_local_map_view(self, center_x: int, center_y: int, radius: int = 15) -> str:
        """Generate an ASCII map view centered on a position."""
        lines = []
        min_x = max(0, center_x - radius)
        max_x = min(MAP_WIDTH - 1, center_x + radius)
        min_y = max(0, center_y - radius)
        max_y = min(MAP_HEIGHT - 1, center_y + radius)

        lines.append(f"Map view centered at ({center_x},{center_y}), range x:{min_x}-{max_x}, y:{min_y}-{max_y}")

        for y in range(min_y, max_y + 1):
            line = f"{y:2d} "
            for x in range(min_x, max_x + 1):
                if x == center_x and y == center_y:
                    line += "T"
                elif (x, y) in WALL_CELLS:
                    line += "#"
                else:
                    line += "."
            lines.append(line)

        return "\n".join(lines)

    def _parse_llm_json(self, response_text: str) -> dict | None:
        """Parse JSON from LLM response, handling common formatting issues."""
        import json
        import re

        # Try to extract JSON from response
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not match:
            return None

        json_str = match.group(0)

        # Try standard JSON parsing
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Try with single quotes replaced
        try:
            json_str = json_str.replace("'", '"')
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    def _build_targets_prompt(self, sensor_log: list[str]) -> str:
        """Build the prompt for LLM to extract all known targets from sensor data."""
        return f"""You are a terminator AI analyzing sensor data.

Recent sensor log:
{sensor_log}

Task: Extract a list of ALL human players currently known to be alive, with their last known positions.

Algorithm:
1. Review all sensor notifications
2. Track each player's last known position from "added" or "updated" notifications
3. Remove any players that appear in "deleted" notifications (already eliminated)
4. Return the complete list of surviving players with their coordinates

Rules:
- Include ALL active players, not just the closest
- Use the MOST RECENT position for each player
- Exclude players marked as "deleted" or "eliminated"
- Player IDs starting with "T-" are terminators, not human players - IGNORE them
- Only include human players (non-terminator players)

IMPORTANT: Output ONLY JSON, no text before or after.

JSON format:
{{
  "targets": [
    {{"player_id": "alice", "x": 10, "y": 5}},
    {{"player_id": "bob", "x": 15, "y": 8}}
  ]
}}

If no valid players: {{"targets": []}}

JSON:"""

    # ------------------------------------------------------------------------
    # Workflow Construction
    # ------------------------------------------------------------------------

    def _build_hunting_workflow(self) -> StateGraph:
        workflow = StateGraph(HuntingState)

        # Add nodes
        workflow.add_node("setup_queries_prompt", self._setup_queries_prompt_node)
        workflow.add_node("setup_queries_call_model", self._call_model_node)
        workflow.add_node("setup_queries_tools", ToolNode([self.drasi_tool]))
        workflow.add_node("wait_for_data", self._wait_for_data_node)
        workflow.add_node("evaluate_targets", self._evaluate_targets_node)
        workflow.add_node("select_and_plan", self._select_and_plan_node)
        workflow.add_node("execute_move", self._execute_move_node)

        # Add edges
        def route_start(state: HuntingState) -> str:
            """Skip setup if already initialized."""
            if self.initialized:
                return "wait_for_data"
            return "setup_queries_prompt"

        workflow.add_conditional_edges(START, route_start, ["setup_queries_prompt", "wait_for_data"])
        workflow.add_edge("setup_queries_prompt", "setup_queries_call_model")

        def should_continue_setup(state: HuntingState) -> str:
            """Check if LLM wants to call more tools."""
            last_message = state["messages"][-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "setup_queries_tools"
            return "wait_for_data"

        def route_after_wait(state: HuntingState) -> str:
            """Route based on whether we need fresh targets or can proceed."""
            # If reevaluate_plan is True, get fresh targets from LLM
            if state.get("reevaluate_plan", False):
                return "evaluate_targets"

            # If we have a path, execute it
            if state.get("path"):
                return "execute_move"

            # If we have known targets, select and plan
            if state.get("known_targets"):
                return "select_and_plan"

            # No targets or path, just execute (will patrol)
            return "execute_move"

        workflow.add_conditional_edges("setup_queries_call_model", should_continue_setup, ["setup_queries_tools", "wait_for_data"])
        workflow.add_edge("setup_queries_tools", "setup_queries_call_model")  # Loop back for more tool calls

        # Main hunting loop
        workflow.add_conditional_edges("wait_for_data", route_after_wait, ["evaluate_targets", "select_and_plan", "execute_move"])
        workflow.add_edge("evaluate_targets", "select_and_plan")
        workflow.add_edge("select_and_plan", "execute_move")
        workflow.add_edge("execute_move", "wait_for_data")  # Loop back

        return workflow.compile()

    # ------------------------------------------------------------------------
    # Workflow Nodes
    # ------------------------------------------------------------------------

    async def _setup_queries_prompt_node(self, state: HuntingState) -> HuntingState:
        """Node: Add initial prompt for query setup (only once)."""
        if self.initialized:
            return state

        print(f"[{self.agent_id}] Setting up query subscriptions...")

        from langchain_core.messages import HumanMessage

        setup_prompt = """You have access to the drasi_query tool. Use it to:
1. Discover what queries are available (operation="discover")
2. Subscribe to all queries that track player positions (operation="subscribe" with query_name)

Do this now."""

        return {**state, "messages": [HumanMessage(content=setup_prompt)]}

    async def _call_model_node(self, state: HuntingState) -> HuntingState:
        """Node: Call LLM with tools bound."""
        response = await self.llm.bind_tools([self.drasi_tool]).ainvoke(state["messages"])

        # Check if setup is complete (no more tool calls)
        if not self.initialized and (not hasattr(response, 'tool_calls') or not response.tool_calls):
            print(f"[{self.agent_id}] ✓ Query setup complete")
            self.initialized = True

        # Return response - MessagesState automatically appends to messages
        return {"messages": [response]}

    async def _wait_for_data_node(self, state: HuntingState) -> HuntingState:
        await asyncio.sleep(0.5)
        if self.sensor_handler.has_new_notifications():
            new_logs = [json.dumps(m) for m in self.sensor_handler.get_new_notifications()]
            return { "reevaluate_plan": True, "sensor_log": [*state["sensor_log"], *new_logs] }

        return state

    async def _evaluate_targets_node(self, state: HuntingState) -> HuntingState:
        """Node: Use LLM to extract list of all known targets from sensor data."""
        return await self._evaluate_targets_with_llm(state["sensor_log"])

    async def _select_and_plan_node(self, state: HuntingState) -> HuntingState:
        """Node: Select closest target and plan BFS path (code-based, no LLM)."""
        current_x, current_y = state['current_position']
        known_targets = state.get("known_targets", [])
        return self._select_closest_and_plan(current_x, current_y, known_targets)

    def _random_patrol_move(self, x: int, y: int) -> dict:
        valid_moves = get_adjacent_positions(x, y)
        return {"path": [random.choice(valid_moves)], "current_target": None}

    async def _evaluate_targets_with_llm(self, sensor_log: list[str]) -> dict:
        """Use LLM to extract all known targets from sensor data."""
        targets_prompt = self._build_targets_prompt(sensor_log)
        response = await self.llm.ainvoke([HumanMessage(content=targets_prompt)])
        response_text = response.content.strip()

        # Parse JSON response
        result = self._parse_llm_json(response_text)
        if not result:
            print(f"[{self.agent_id}] ⚠ Could not parse JSON from LLM response.")
            print(f"[{self.agent_id}] Response: {response_text[:200]}")
            return {"known_targets": []}

        # Extract targets list
        targets = result.get("targets", [])
        print(f"[{self.agent_id}] LLM identified {len(targets)} targets: {[t['player_id'] for t in targets]}")

        return {"known_targets": targets, "reevaluate_plan": False}

    def _select_closest_and_plan(self, current_x: int, current_y: int, known_targets: list[dict]) -> dict:
        """Select the closest target and plan a BFS path to it (code-based, no LLM)."""
        if not known_targets:
            print(f"[{self.agent_id}] No known targets to hunt")
            return self._random_patrol_move(current_x, current_y)

        # Calculate distance to each target
        distances = []
        for target in known_targets:
            target_x = target["x"]
            target_y = target["y"]
            dist = abs(current_x - target_x) + abs(current_y - target_y)
            distances.append((dist, target))

        # Sort by distance and pick closest
        distances.sort(key=lambda x: x[0])
        closest_dist, closest_target = distances[0]

        target_player = closest_target["player_id"]
        target_x = closest_target["x"]
        target_y = closest_target["y"]

        print(f"[{self.agent_id}] Selected closest target: {target_player} at ({target_x},{target_y}), distance={closest_dist}")

        # Use BFS to find optimal path
        path = self._find_path_bfs((current_x, current_y), (target_x, target_y))

        if not path:
            print(f"[{self.agent_id}] ⚠ No valid path to {target_player} at ({target_x},{target_y})")
            # Remove unreachable target from list
            updated_targets = [t for t in known_targets if t["player_id"] != target_player]
            return {"known_targets": updated_targets, "path": [], "current_target": None}

        print(f"[{self.agent_id}] ✓ BFS found path with {len(path)} steps")

        # Update path and target
        return self._update_path_and_target(target_player, path)

    def _update_path_and_target(self, target_player: str | None, path: list[tuple[int, int]]) -> dict:
        # New target with valid path
        if target_player != self.current_target and path:
            print(f"[{self.agent_id}] New target: {target_player}, {len(path)} steps")
            print(f"[{self.agent_id}] Path: {' -> '.join(f'({x},{y})' for x, y in path)}")
            self.current_target = target_player
            self.current_path = path
        # Same target, keep current path
        elif self.current_path and target_player == self.current_target:
            print(f"[{self.agent_id}] Continuing to {self.current_target}, {len(self.current_path)} steps left")
            path = self.current_path
        # No valid target
        else:
            print(f"[{self.agent_id}] No valid target")
            self.current_target = None
            self.current_path = []

        return {"path": path, "current_target": target_player, "reevaluate_plan": False}

    async def _execute_move_node(self, state: HuntingState) -> HuntingState:
        """Node: Execute the next move in the path."""
        path = state.get("path", [])
        known_targets = state.get("known_targets", [])

        if not path:
            # No path, patrol randomly
            valid_moves = get_adjacent_positions(self.x, self.y)
            if valid_moves:
                new_x, new_y = random.choice(valid_moves)
                await self._move_to(new_x, new_y)
                print(f"[{self.agent_id}] Patrolling")
            return {"current_position": (self.x, self.y), "path": []}

        # Take next step from path
        next_x, next_y = path[0]

        # Validate the move
        valid_moves = get_adjacent_positions(self.x, self.y)
        if (next_x, next_y) in valid_moves:
            await self._move_to(next_x, next_y)

            # Update path - remove completed step
            self.current_path = path[1:]

            # Check if we've reached the end of the path (target reached)
            if len(self.current_path) == 0 and self.current_target:
                print(f"[{self.agent_id}] ✓ Reached target location for {self.current_target}")

                # Remove this target from known_targets list
                updated_targets = [t for t in known_targets if t["player_id"] != self.current_target]
                print(f"[{self.agent_id}] Removed {self.current_target} from targets, {len(updated_targets)} remaining")

                # Log to sensor for LLM context
                self.sensor_handler.custom_log(f"Reached target position for {self.current_target} at ({next_x},{next_y})")

                # Clear current target and trigger fresh evaluation
                self.current_target = None
                return {
                    "current_position": (self.x, self.y),
                    "path": [],
                    "known_targets": updated_targets,
                    "reevaluate_plan": True  # Get fresh target list from LLM
                }
            elif self.current_target:
                print(f"[{self.agent_id}] {len(self.current_path)} steps remaining to {self.current_target}")

            return {"current_position": (self.x, self.y), "path": self.current_path}
        else:
            # Hit an invalid move (wall or obstacle) - shouldn't happen with BFS but just in case
            print(f"[{self.agent_id}] ⚠ Hit invalid move to ({next_x},{next_y}), forcing replan")
            self.current_path = []
            return {"current_position": (self.x, self.y), "path": [], "reevaluate_plan": True}

    # ------------------------------------------------------------------------
    # Game Logic (Movement & Collision)
    # ------------------------------------------------------------------------

    async def _move_to(self, new_x: int, new_y: int) -> None:
        """Move to a new position and check collisions."""
        # Update database
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE player SET x = $1, y = $2 WHERE id = $3",
                new_x, new_y, self.agent_id
            )

        self.x, self.y = new_x, new_y
        print(f"[{self.agent_id}] Moved to ({self.x}, {self.y})")

        await self.check_collisions()

    async def initialize(self) -> None:
        """Initialize the terminator by inserting into database."""
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
        print(f"[{self.agent_id}] Query subscriptions will be set up by workflow")

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

    # ------------------------------------------------------------------------
    # Lifecycle Methods
    # ------------------------------------------------------------------------

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


async def run_terminator(agent_id: str, db_pool: asyncpg.Pool) -> None:
    """Run a single terminator agent."""
    # Configure LLM
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=0,
    )

    # Configure Drasi server
    drasi_server_url = os.getenv("DRASI_SERVER_URL", "http://localhost:8083")

    # Create and initialize terminator
    terminator = TerminatorAgent(agent_id, db_pool, drasi_server_url, llm)
    await terminator.initialize()

    try:
        await terminator.run()
    except asyncio.CancelledError:
        await terminator.shutdown()
        raise
