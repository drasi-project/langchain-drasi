"""Main entry point for the Terminator game.

This script runs a single terminator AI agent with a random name.
Run multiple instances of this script to spawn multiple agents.
"""

import asyncio
import os
import random
import string
from dotenv import load_dotenv

from terminator_agent import run_terminator

# Load environment variables
load_dotenv()

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Global state
terminator_task: asyncio.Task = None


def generate_agent_id() -> str:
    """Generate a random agent ID like T-X7K."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"T-{suffix}"


async def async_main():
    """Async main entry point."""
    global terminator_task

    # Generate random agent ID
    agent_id = generate_agent_id()

    print("=" * 60)
    print(f"Terminator Agent - {agent_id}")
    print("=" * 60)

    try:
        # Start the terminator agent
        print(f"\nConnecting to API: {API_BASE_URL}")
        print(f"Starting agent {agent_id}...")
        terminator_task = asyncio.create_task(run_terminator(agent_id, API_BASE_URL))
        print(f"Agent {agent_id} started")

        print("\nPress Ctrl+C to stop\n")

        # Wait for the task to complete (or be cancelled)
        await terminator_task

    except asyncio.CancelledError:
        print("\nShutdown initiated...")
    except KeyboardInterrupt:
        print("\nShutdown initiated...")
    finally:
        # Cleanup
        print("Cleaning up...")

        # Cancel the terminator task
        if terminator_task and not terminator_task.done():
            terminator_task.cancel()
            try:
                await asyncio.wait_for(terminator_task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                print("Warning: Task did not complete within timeout")

        print("Shutdown complete")


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
        pass


if __name__ == "__main__":
    main()
