"""
Terminator Agent Entry Point

This example demonstrates how Drasi enables real-time reactive AI agents:

1. **Real-time Query Subscriptions**: The agent subscribes to Drasi queries that track
   player positions in the game database.

2. **Push Notifications**: Instead of polling, Drasi pushes notifications when players
   move, are added, or are eliminated.

3. **Reactive Behavior**: The agent immediately reacts to position updates, making
   intelligent hunting decisions based on fresh data.

Key Drasi Integration Points (see agent/terminator.py):
- SensorHandler: Receives real-time notifications from Drasi queries
- create_drasi_tool(): Creates LangChain tool for query discovery and subscription
- MCPConnectionConfig: Configures connection to Drasi MCP server

The heavy lifting (pathfinding, workflow, game logic) is in the agent/ module.
This file focuses on the Drasi setup and agent lifecycle.
"""

import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from agent import TerminatorAgent

# Load environment variables
load_dotenv()


async def run_terminator(agent_id: str, api_base_url: str = "http://localhost:8000") -> None:
    # Configure LLM
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=0,
    )

    # Configure Drasi server
    drasi_server_url = os.getenv("DRASI_SERVER_URL", "http://localhost:8083")

    # Create and initialize terminator with Drasi integration
    terminator = TerminatorAgent(agent_id, api_base_url, drasi_server_url, llm)
    await terminator.initialize()

    try:
        # Run continuously - workflow will subscribe to Drasi queries and react to notifications
        await terminator.run()
    except asyncio.CancelledError:
        await terminator.shutdown()
        raise
