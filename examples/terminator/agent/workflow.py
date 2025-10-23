"""LangGraph workflow for Terminator hunting behavior."""

import asyncio
import json
import random

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from game_map import get_adjacent_positions
from .llm_helpers import parse_llm_json, build_targets_prompt
from .pathfinding import find_path_bfs


class HuntingState(MessagesState):
    """State for the hunting workflow."""
    current_position: tuple[int, int]
    path: list[tuple[int, int]]
    current_target: str | None
    reevaluate_plan: bool
    sensor_log: list[str]
    known_targets: list[dict]  # List of {"player_id": str, "x": int, "y": int}


class WorkflowNodes:
    """Container for workflow node implementations."""

    def __init__(self, agent):
        """Initialize with reference to parent TerminatorAgent."""
        self.agent = agent

    async def setup_queries_prompt_node(self, state: HuntingState) -> HuntingState:
        """Node: Add initial prompt for query setup (only once)."""
        if self.agent.initialized:
            return state

        print(f"[{self.agent.agent_id}] Setting up query subscriptions...")

        setup_prompt = """You have access to the drasi_query tool. Use it to:
1. Discover what queries are available (operation="discover")
2. Subscribe to all queries that track player positions (operation="subscribe" with query_name)

Do this now."""

        return {**state, "messages": [HumanMessage(content=setup_prompt)]}

    async def call_model_node(self, state: HuntingState) -> HuntingState:
        """Node: Call LLM with tools bound."""
        response = await self.agent.llm.bind_tools([self.agent.drasi_tool]).ainvoke(state["messages"])

        # Check if setup is complete (no more tool calls)
        if not self.agent.initialized and (not hasattr(response, 'tool_calls') or not response.tool_calls):
            print(f"[{self.agent.agent_id}] ✓ Query setup complete")
            self.agent.initialized = True

        # Return response - MessagesState automatically appends to messages
        return {"messages": [response]}

    async def check_sensors(self, state: HuntingState) -> HuntingState:
        """Node: Wait briefly and check for new notifications."""
        if len(state.get("path", [])) > 0:
            await asyncio.sleep(0.2)
        else:
            await asyncio.sleep(0.8)
        if self.agent.sensor_handler.has_new_notifications():
            new_logs = [json.dumps(m) for m in self.agent.sensor_handler.get_new_notifications()]
            return {"reevaluate_plan": True, "sensor_log": [*state["sensor_log"], *new_logs]}

        return state

    async def evaluate_targets_node(self, state: HuntingState) -> HuntingState:
        """Node: Use LLM to extract list of all known targets from sensor data."""
        return await self._evaluate_targets_with_llm(state["sensor_log"])

    async def select_and_plan_node(self, state: HuntingState) -> HuntingState:
        """Node: Select closest target and plan BFS path (code-based, no LLM)."""
        current_x, current_y = state['current_position']
        known_targets = state.get("known_targets", [])
        return self._select_closest_and_plan(current_x, current_y, known_targets)

    async def execute_move_node(self, state: HuntingState) -> HuntingState:
        """Node: Execute the next move in the path."""
        path = state.get("path", [])
        known_targets = state.get("known_targets", [])

        if not path:
            # No path, patrol randomly
            valid_moves = get_adjacent_positions(self.agent.x, self.agent.y)
            if valid_moves:
                new_x, new_y = random.choice(valid_moves)
                await self.agent._move_to(new_x, new_y)
                print(f"[{self.agent.agent_id}] Patrolling")
            return {"current_position": (self.agent.x, self.agent.y), "path": []}

        # Take next step from path
        next_x, next_y = path[0]

        # Validate the move
        valid_moves = get_adjacent_positions(self.agent.x, self.agent.y)
        if (next_x, next_y) in valid_moves:
            await self.agent._move_to(next_x, next_y)

            # Update path - remove completed step
            self.agent.current_path = path[1:]

            # Check if we've reached the end of the path (target reached)
            if len(self.agent.current_path) == 0 and self.agent.current_target:
                print(f"[{self.agent.agent_id}] ✓ Reached target location for {self.agent.current_target}")

                # Remove this target from known_targets list
                updated_targets = [t for t in known_targets if t["player_id"] != self.agent.current_target]
                print(f"[{self.agent.agent_id}] Removed {self.agent.current_target} from targets, {len(updated_targets)} remaining")

                # Log to sensor for LLM context
                self.agent.sensor_handler.custom_log(f"Reached target position for {self.agent.current_target} at ({next_x},{next_y})")

                # Clear current target and trigger fresh evaluation
                self.agent.current_target = None
                return {
                    "current_position": (self.agent.x, self.agent.y),
                    "path": [],
                    "known_targets": updated_targets,
                    "reevaluate_plan": True  # Get fresh target list from LLM
                }
            elif self.agent.current_target:
                print(f"[{self.agent.agent_id}] {len(self.agent.current_path)} steps remaining to {self.agent.current_target}")

            return {"current_position": (self.agent.x, self.agent.y), "path": self.agent.current_path}
        else:
            # Hit an invalid move (wall or obstacle) - shouldn't happen with BFS but just in case
            print(f"[{self.agent.agent_id}] ⚠ Hit invalid move to ({next_x},{next_y}), forcing replan")
            self.agent.current_path = []
            return {"current_position": (self.agent.x, self.agent.y), "path": [], "reevaluate_plan": True}

    # Helper methods
    async def _evaluate_targets_with_llm(self, sensor_log: list[str]) -> dict:
        """Use LLM to extract all known targets from sensor data."""
        targets_prompt = build_targets_prompt(sensor_log)
        response = await self.agent.llm.ainvoke([HumanMessage(content=targets_prompt)])
        response_text = response.content.strip()

        # Parse JSON response
        result = parse_llm_json(response_text)
        if not result:
            print(f"[{self.agent.agent_id}] ⚠ Could not parse JSON from LLM response.")
            print(f"[{self.agent.agent_id}] Response: {response_text[:200]}")
            return {"known_targets": []}

        # Extract targets list
        targets = result.get("targets", [])
        print(f"[{self.agent.agent_id}] LLM identified {len(targets)} targets: {[t['player_id'] for t in targets]}")

        return {"known_targets": targets, "reevaluate_plan": False}

    def _select_closest_and_plan(self, current_x: int, current_y: int, known_targets: list[dict]) -> dict:
        """Select the closest target and plan a BFS path to it (code-based, no LLM)."""
        if not known_targets:
            print(f"[{self.agent.agent_id}] No known targets to hunt")
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

        print(f"[{self.agent.agent_id}] Selected closest target: {target_player} at ({target_x},{target_y}), distance={closest_dist}")

        # Use BFS to find optimal path
        path = find_path_bfs(self.agent.agent_id, (current_x, current_y), (target_x, target_y))

        if not path:
            print(f"[{self.agent.agent_id}] ⚠ No valid path to {target_player} at ({target_x},{target_y})")
            # Remove unreachable target from list
            updated_targets = [t for t in known_targets if t["player_id"] != target_player]
            return {"known_targets": updated_targets, "path": [], "current_target": None}

        print(f"[{self.agent.agent_id}] ✓ BFS found path with {len(path)} steps")

        # Update path and target
        return self._update_path_and_target(target_player, path)

    def _update_path_and_target(self, target_player: str | None, path: list[tuple[int, int]]) -> dict:
        """Update the current path and target."""
        # New target with valid path
        if target_player != self.agent.current_target and path:
            print(f"[{self.agent.agent_id}] New target: {target_player}, {len(path)} steps")
            print(f"[{self.agent.agent_id}] Path: {' -> '.join(f'({x},{y})' for x, y in path)}")
            self.agent.current_target = target_player
            self.agent.current_path = path
        # Same target, keep current path
        elif self.agent.current_path and target_player == self.agent.current_target:
            print(f"[{self.agent.agent_id}] Continuing to {self.agent.current_target}, {len(self.agent.current_path)} steps left")
            path = self.agent.current_path
        # No valid target
        else:
            print(f"[{self.agent.agent_id}] No valid target")
            self.agent.current_target = None
            self.agent.current_path = []

        return {"path": path, "current_target": target_player, "reevaluate_plan": False}

    def _random_patrol_move(self, x: int, y: int) -> dict:
        """Generate a random patrol move."""
        valid_moves = get_adjacent_positions(x, y)
        return {"path": [random.choice(valid_moves)], "current_target": None}


def build_hunting_workflow(agent, drasi_tool) -> StateGraph:
    """Build the LangGraph workflow for hunting behavior."""
    workflow = StateGraph(HuntingState)
    nodes = WorkflowNodes(agent)

    # Add nodes
    workflow.add_node("setup_queries_prompt", nodes.setup_queries_prompt_node)
    workflow.add_node("setup_queries_call_model", nodes.call_model_node)
    workflow.add_node("setup_queries_tools", ToolNode([drasi_tool]))
    workflow.add_node("check_sensors", nodes.check_sensors)
    workflow.add_node("evaluate_targets", nodes.evaluate_targets_node)
    workflow.add_node("select_and_plan", nodes.select_and_plan_node)
    workflow.add_node("execute_move", nodes.execute_move_node)

    # Add edges
    def route_start(state: HuntingState) -> str:
        """Skip setup if already initialized."""
        if agent.initialized:
            return "check_sensors"
        return "setup_queries_prompt"

    workflow.add_conditional_edges(START, route_start, ["setup_queries_prompt", "check_sensors"])
    workflow.add_edge("setup_queries_prompt", "setup_queries_call_model")

    def should_continue_setup(state: HuntingState) -> str:
        """Check if LLM wants to call more tools."""
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "setup_queries_tools"
        return "check_sensors"

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

    workflow.add_conditional_edges("setup_queries_call_model", should_continue_setup, ["setup_queries_tools", "check_sensors"])
    workflow.add_edge("setup_queries_tools", "setup_queries_call_model")  # Loop back for more tool calls

    # Main hunting loop
    workflow.add_conditional_edges("check_sensors", route_after_wait, ["evaluate_targets", "select_and_plan", "execute_move"])
    workflow.add_edge("evaluate_targets", "select_and_plan")
    workflow.add_edge("select_and_plan", "execute_move")
    workflow.add_edge("execute_move", "check_sensors")  # Loop back

    return workflow.compile()
