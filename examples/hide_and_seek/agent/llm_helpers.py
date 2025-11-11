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
    return f"""You are a seeker AI in an invisible hide and seek game, analyzing sensor data.

Recent sensor log:
{sensor_log}

Task: Extract a list of ALL invisible hider players currently in the game, with their last known positions revealed by your sensors.

Algorithm:
1. Review all sensor notifications
2. Track each hider's last known position from "added" or "updated" notifications
3. Remove any players that appear in "deleted" notifications (already found)
4. Return the complete list of still-hiding players with their coordinates

Rules:
- Include ALL active hiders, not just the closest
- Use the MOST RECENT position for each hider
- Exclude players marked as "deleted" or "found"
- Player IDs starting with "S-" are seekers (your teammates), not hiders - IGNORE them
- Only include human players (the hiders you're seeking)

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
