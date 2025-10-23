"""LLM utilities for parsing responses and building prompts."""

import json
import re


def parse_llm_json(response_text: str) -> dict | None:
    """Parse JSON from LLM response, handling common formatting issues."""
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


def build_targets_prompt(sensor_log: list[str]) -> str:
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
