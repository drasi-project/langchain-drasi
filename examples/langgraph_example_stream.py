"""Simple interactive ReAct agent with DrasiTool using LangGraph.

This example demonstrates how to use DrasiTool with LangGraph's ReAct agent
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
    python examples/langgraph_example.py
"""

import asyncio
import os
from typing import Any
from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI

# Import Drasi components
from langchain_drasi import (
    create_drasi_tool,
    MCPConnectionConfig,
    BaseDrasiNotificationHandler,
)

# Load environment variables
load_dotenv()

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
#     stream=sys.stdout
# )

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
    print("Interactive Drasi Agent (LangGraph)")
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

    # Create memory for conversation state
    memory = MemorySaver()

    # Create LangGraph ReAct agent
    print("Creating LangGraph ReAct agent...\n")
    agent = create_react_agent(
        model=llm,
        tools=[drasi_tool],
        checkpointer=memory,
    )

    # Configuration for conversation thread
    config: dict = {"configurable": {"thread_id": "drasi-chat"}}  # type: ignore[annotation-unchecked]

    # Interactive loop
    print("Agent ready! You can ask questions about Drasi queries.\n")
    print("Example questions:")
    print("  - What queries are available?")
    print("  - Read the results from query X")
    print("  - Subscribe to query Y for updates")
    print()

    try:
        while True:
            # Get user input (runs in executor to avoid blocking event loop)
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input("\n> ").strip()
            )

            # Check for exit commands
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            # Run agent with streaming
            try:
                print()  # Blank line before output
                event = None
                async for event in agent.astream(
                    {"messages": [("user", user_input)]},
                    config=config,  # type: ignore[arg-type]
                    stream_mode="values"
                ):
                    # Get the last message
                    if "messages" in event and event["messages"]:
                        last_message = event["messages"][-1]
                        
                        if hasattr(last_message, "content") and last_message.content:
                            # Print the response (only once at the end)
                            pass

                # Print final response
                if event and "messages" in event and event["messages"]:
                    last_message = event["messages"][-1]
                    if hasattr(last_message, "content"):
                        print(f"{last_message.content}")

            except Exception as e:
                print(f"\n❌ Error: {e}")

    except KeyboardInterrupt:
        print("\n\nShutting down...")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
