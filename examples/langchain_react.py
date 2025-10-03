"""Simple interactive ReAct agent with DrasiTool.

This example demonstrates how to use DrasiTool with LangChain's ReAct agent
to build an interactive agent that can query and monitor Drasi continuous queries.

Prerequisites:
    - Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in environment
    - Set AZURE_OPENAI_DEPLOYMENT (e.g., "gpt-4o-mini")
    - Optional: Set AZURE_OPENAI_API_VERSION (default: "2024-02-15-preview")
    - Have a Drasi MCP server running and accessible
    - Set DRASI_SERVER_URL in your .env file (default: http://localhost:8083)
    - Optional: Set DRASI_API_TOKEN if your server requires authentication

IMPORTANT: This example requires a running Drasi MCP server. Without one,
the agent will not be able to discover or read queries.

Usage:
    python examples/langchain_react.py
"""

import asyncio
import os
import sys
import logging
from typing import Any
from dotenv import load_dotenv

from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import AzureChatOpenAI

# Import Drasi components
from langchain_drasi import (
    create_drasi_tool,
    MCPConnectionConfig,
    BaseDrasiNotificationHandler,
)

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    stream=sys.stdout
)



# Simple notification handler
class ConsoleHandler(BaseDrasiNotificationHandler):
    """Handler that prints notifications to console."""

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Handle when results are added."""
        print(f"\n🆕 NOTIFICATION: Added to '{query_name}': {added_data}")

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Handle when results are updated."""
        print(f"\n🔄 NOTIFICATION: Updated in '{query_name}': {updated_data}")

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Handle when results are deleted."""
        print(f"\n🗑️  NOTIFICATION: Deleted from '{query_name}': {deleted_data}")


async def main() -> None:
    """Run the interactive ReAct agent."""
    print("=" * 70)
    print("Interactive Drasi Agent (ReAct)")
    print("=" * 70)
    print("\nType your questions or commands. Type 'exit' or 'quit' to stop.\n")

    # Configure Drasi MCP connection
    server_url = os.getenv("DRASI_SERVER_URL", "http://localhost:8083")
    mcp_config = MCPConnectionConfig(
        server_url=server_url,
        headers={
            "Authorization": f"Bearer {os.getenv('DRASI_API_TOKEN')}"
        } if os.getenv("DRASI_API_TOKEN") else None,
        timeout=30.0,
    )

    print(f"Connecting to Drasi server: {server_url}")

    # Create Drasi tool with notification handler
    notification_handler = ConsoleHandler()
    drasi_tool = create_drasi_tool(
        mcp_config=mcp_config,
        notification_handlers=[notification_handler],
    )

    # Initialize LLM
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=0,
    )

    # Pull ReAct prompt from LangChain Hub
    print("Loading ReAct prompt template...")
    prompt = hub.pull("hwchase17/react")

    # Create ReAct agent
    print("Creating ReAct agent...\n")
    agent = create_react_agent(llm, [drasi_tool], prompt)

    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[drasi_tool],
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
    )

    # Interactive loop
    print("Agent ready! You can ask questions about Drasi queries.\n")
    print("Example questions:")
    print("  - What queries are available?")
    print("  - Read the results from query X")
    print("  - Subscribe to query Y for updates")
    print()

    try:
        while True:
            # Get user input
            user_input = input("\n> ").strip()

            # Check for exit commands
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            # Run agent
            try:
                result = await agent_executor.ainvoke({"input": user_input})
                print(f"\n{result['output']}")
            except Exception as e:
                print(f"\n❌ Error: {e}")

    except KeyboardInterrupt:
        print("\n\nShutting down...")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
