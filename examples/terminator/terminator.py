#!/usr/bin/env python3
"""
Terminator Agent Runner

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
"""

import asyncio
import os
import random
import string
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from agent import TerminatorAgent

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DRASI_SERVER_URL = os.getenv("DRASI_SERVER_URL", "http://localhost:8083")


def generate_agent_id() -> str:
    """Generate a random agent ID like T-X7K."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"T-{suffix}"


async def async_main():
    """Async main entry point."""
    # Generate agent ID
    agent_id = generate_agent_id()

    print("=" * 60)
    print(f"Terminator Agent - {agent_id}")
    print("=" * 60)
    print(f"\nConnecting to API: {API_BASE_URL}")
    print(f"Drasi Server: {DRASI_SERVER_URL}")
    print(f"\nStarting agent {agent_id}...")
    print("\nPress Ctrl+C to stop\n")

    # Configure LLM
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=0,
    )

    # Create and initialize terminator with Drasi integration
    terminator = TerminatorAgent(agent_id, API_BASE_URL, DRASI_SERVER_URL, llm)
    await terminator.initialize()

    try:
        # Run continuously - workflow will subscribe to Drasi queries and react to notifications
        await terminator.run()
    except asyncio.CancelledError:
        print("\nShutdown initiated...")
        await terminator.shutdown()
    except KeyboardInterrupt:
        print("\nShutdown initiated...")
        await terminator.shutdown()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
