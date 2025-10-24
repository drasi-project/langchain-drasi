"""LangGraph workflow for Terminator hunting behavior."""

import asyncio
import json
import random

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, MessagesState

from langgraph.prebuilt import ToolNode

from game_map import get_adjacent_positions
from .llm_helpers import parse_llm_json, build_targets_prompt
from .pathfinding import find_path_bfs


class TerminatorState(MessagesState):
    """State for the terminator workflow."""
    current_position: tuple[int, int]
    path: list[tuple[int, int]]
    current_target: str | None
    reevaluate_plan: bool
    sensor_log: list[str]
    known_targets: list[dict]  # List of {"player_id": str, "x": int, "y": int}


# Node factory functions - each returns a node function with access to agent/drasi_tool

def setup_queries_prompt_node(agent):
    """Factory for setup queries prompt node."""
    async def node(state: TerminatorState) -> TerminatorState:
        """Node: Add initial prompt for query setup (only once)."""
        if agent.initialized:
            return state

        print(f"[{agent.agent_id}] Setting up query subscriptions...")

        setup_prompt = """You have access to the drasi_query tool. Use it to:
1. Discover what queries are available
2. Subscribe to all queries that track player positions

Do this now."""

        return {**state, "messages": [HumanMessage(content=setup_prompt)]}
    return node


def call_model_node(agent):
    """Factory for call model node."""
    async def node(state: TerminatorState) -> TerminatorState:
        """Node: Call LLM with tools bound."""
        response = await agent.llm.bind_tools([agent.drasi_tool]).ainvoke(state["messages"])

        # Check if setup is complete (no more tool calls)
        if not agent.initialized and (not hasattr(response, 'tool_calls') or not response.tool_calls):
            print(f"[{agent.agent_id}] ✓ Query setup complete")
            agent.initialized = True

        # Return response - MessagesState automatically appends to messages
        return {"messages": [response]}
    return node


def check_sensors_node(agent):
    """Factory for check sensors node."""
    async def node(state: TerminatorState) -> TerminatorState:
        """Node: Wait briefly and check for new notifications."""
        if len(state.get("path", [])) > 0:
            await asyncio.sleep(0.2)
        else:
            await asyncio.sleep(0.8)
        if not agent.buffer_handler.is_empty():
            # Consume all notifications and convert to JSON strings
            new_logs = []
            while not agent.buffer_handler.is_empty():
                record = agent.buffer_handler.consume()
                if record:
                    notification_dict = {
                        "type": record.change_type,
                        "query": record.query_name,
                        "data": record.data,
                        "timestamp": record.timestamp.timestamp()
                    }
                    new_logs.append(json.dumps(notification_dict))
            return {"reevaluate_plan": True, "sensor_log": [*state["sensor_log"], *new_logs]}

        return state
    return node


def evaluate_targets_node(agent):
    """Factory for evaluate targets node."""
    async def node(state: TerminatorState) -> TerminatorState:
        """Node: Use LLM to extract list of all known targets from sensor data."""
        targets_prompt = build_targets_prompt(state["sensor_log"])
        response = await agent.llm.ainvoke([HumanMessage(content=targets_prompt)])
        response_text = response.content.strip()

        # Parse JSON response
        result = parse_llm_json(response_text)
        if not result:
            print(f"[{agent.agent_id}] ⚠ Could not parse JSON from LLM response.")
            print(f"[{agent.agent_id}] Response: {response_text[:200]}")
            return {"known_targets": []}

        # Extract targets list
        targets = result.get("targets", [])
        print(f"[{agent.agent_id}] LLM identified {len(targets)} targets: {[t['player_id'] for t in targets]}")

        return {"known_targets": targets, "reevaluate_plan": False}
    return node


def select_and_plan_node(agent):
    """Factory for select and plan node."""
    async def node(state: TerminatorState) -> TerminatorState:
        """Node: Select closest target and plan BFS path (code-based, no LLM)."""
        current_x, current_y = state['current_position']
        known_targets = state.get("known_targets", [])

        if not known_targets:
            print(f"[{agent.agent_id}] No known targets to hunt")
            # Random patrol
            valid_moves = get_adjacent_positions(current_x, current_y)
            return {"path": [random.choice(valid_moves)], "current_target": None}

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

        print(f"[{agent.agent_id}] Selected closest target: {target_player} at ({target_x},{target_y}), distance={closest_dist}")

        # Use BFS to find optimal path
        path = find_path_bfs(agent.agent_id, (current_x, current_y), (target_x, target_y))

        if not path:
            print(f"[{agent.agent_id}] ⚠ No valid path to {target_player} at ({target_x},{target_y})")
            # Remove unreachable target from list
            updated_targets = [t for t in known_targets if t["player_id"] != target_player]
            return {"known_targets": updated_targets, "path": [], "current_target": None}

        print(f"[{agent.agent_id}] ✓ BFS found path with {len(path)} steps")

        # Update path and target
        current_target_from_state = state.get("current_target")
        current_path_from_state = state.get("path", [])

        if target_player != current_target_from_state and path:
            print(f"[{agent.agent_id}] New target: {target_player}, {len(path)} steps")
            print(f"[{agent.agent_id}] Path: {' -> '.join(f'({x},{y})' for x, y in path)}")
        elif current_path_from_state and target_player == current_target_from_state:
            print(f"[{agent.agent_id}] Continuing to {current_target_from_state}, {len(current_path_from_state)} steps left")
            path = current_path_from_state
        else:
            print(f"[{agent.agent_id}] No valid target")

        return {"path": path, "current_target": target_player, "reevaluate_plan": False}
    return node


def execute_move_node(agent):
    """Factory for execute move node."""
    async def node(state: TerminatorState) -> TerminatorState:
        """Node: Execute the next move in the path."""
        path = state.get("path", [])
        known_targets = state.get("known_targets", [])
        current_target = state.get("current_target")

        if not path:
            # No path, patrol randomly
            valid_moves = get_adjacent_positions(agent.x, agent.y)
            if valid_moves:
                new_x, new_y = random.choice(valid_moves)
                await agent._move_to(new_x, new_y)
                print(f"[{agent.agent_id}] Patrolling")
            return {"current_position": (agent.x, agent.y), "path": []}

        # Take next step from path
        next_x, next_y = path[0]

        # Validate the move
        valid_moves = get_adjacent_positions(agent.x, agent.y)
        if (next_x, next_y) in valid_moves:
            await agent._move_to(next_x, next_y)

            # Update path - remove completed step
            updated_path = path[1:]

            # Check if we've reached the end of the path (target reached)
            if len(updated_path) == 0 and current_target:
                print(f"[{agent.agent_id}] ✓ Reached target location for {current_target}")

                # Remove this target from known_targets list
                updated_targets = [t for t in known_targets if t["player_id"] != current_target]
                print(f"[{agent.agent_id}] Removed {current_target} from targets, {len(updated_targets)} remaining")

                # Log to buffer for LLM context
                agent.custom_log(f"Reached target position for {current_target} at ({next_x},{next_y})")

                # Clear current target and trigger fresh evaluation
                return {
                    "current_position": (agent.x, agent.y),
                    "path": [],
                    "current_target": None,
                    "known_targets": updated_targets,
                    "reevaluate_plan": True  # Get fresh target list from LLM
                }
            elif current_target:
                print(f"[{agent.agent_id}] {len(updated_path)} steps remaining to {current_target}")

            return {"current_position": (agent.x, agent.y), "path": updated_path}
        else:
            # Hit an invalid move (wall or obstacle) - shouldn't happen with BFS but just in case
            print(f"[{agent.agent_id}] ⚠ Hit invalid move to ({next_x},{next_y}), forcing replan")
            return {"current_position": (agent.x, agent.y), "path": [], "reevaluate_plan": True}
    return node


def build_hunting_workflow(agent, drasi_tool) -> StateGraph:
    """Build the LangGraph workflow for hunting behavior."""
    workflow = StateGraph(TerminatorState)

    # Create nodes using factories
    setup_prompt = setup_queries_prompt_node(agent)
    call_model = call_model_node(agent)
    check_sensors = check_sensors_node(agent)
    evaluate_targets = evaluate_targets_node(agent)
    select_and_plan = select_and_plan_node(agent)
    execute_move = execute_move_node(agent)

    # Add nodes
    workflow.add_node("setup_queries_prompt", setup_prompt)
    workflow.add_node("setup_queries_call_model", call_model)
    workflow.add_node("setup_queries_tools", ToolNode([drasi_tool]))
    workflow.add_node("check_sensors", check_sensors)
    workflow.add_node("evaluate_targets", evaluate_targets)
    workflow.add_node("select_and_plan", select_and_plan)
    workflow.add_node("execute_move", execute_move)

    # Add edges
    def route_start(state: TerminatorState) -> str:
        """Skip setup if already initialized."""
        if agent.initialized:
            return "check_sensors"
        return "setup_queries_prompt"

    workflow.add_conditional_edges(START, route_start, ["setup_queries_prompt", "check_sensors"])
    workflow.add_edge("setup_queries_prompt", "setup_queries_call_model")

    def should_continue_setup(state: TerminatorState) -> str:
        """Check if LLM wants to call more tools."""
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "setup_queries_tools"
        return "check_sensors"

    def route_after_wait(state: TerminatorState) -> str:
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
