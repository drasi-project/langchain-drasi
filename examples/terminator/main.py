"""Main entry point for the Terminator game.

This script runs a single terminator AI agent with a random name.
Run multiple instances of this script to spawn multiple agents.
"""

import asyncio
import os
import random
import string
from dotenv import load_dotenv
import asyncpg

from terminator_agent import run_terminator

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "test")
DB_NAME = os.getenv("DB_NAME", "game")

# Global state
terminator_task: asyncio.Task = None
db_pool: asyncpg.Pool = None


def generate_agent_id() -> str:
    """Generate a random agent ID like T-X7K."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"T-{suffix}"


async def async_main():
    """Async main entry point."""
    global db_pool, terminator_task

    # Generate random agent ID
    agent_id = generate_agent_id()

    print("=" * 60)
    print(f"Terminator Agent - {agent_id}")
    print("=" * 60)

    try:
        # Create database connection pool
        print(f"\nConnecting to database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        db_pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            min_size=5,
            max_size=20,
        )
        print("Database connected")

        # Start the terminator agent
        print(f"\nStarting agent {agent_id}...")
        terminator_task = asyncio.create_task(run_terminator(agent_id, db_pool))
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

        # Close database pool
        if db_pool:
            await db_pool.close()
            print("Database pool closed")

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
