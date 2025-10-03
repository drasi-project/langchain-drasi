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
from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI

# Import Drasi components
from langchain_drasi import (
    create_drasi_tool,
    MCPConnectionConfig,
    ConsoleHandler,
    MemoryHandler,
)

# Load environment variables
load_dotenv()


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

    # Create memory for conversation state
    memory = MemorySaver()
    thread_id = "drasi-chat"

    # Create notification handlers:
    # 1. Console handler to print notifications
    # 2. Memory handler to buffer notifications for the conversation
    console_handler = ConsoleHandler()
    memory_handler = MemoryHandler()

    # Create Drasi tool with both notification handlers
    drasi_tool = create_drasi_tool(
        mcp_config=mcp_config,
        notification_handlers=[console_handler, memory_handler],
    )

    # Initialize LLM
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=0,
    )

    # Create LangGraph ReAct agent
    print("Creating LangGraph ReAct agent...\n")
    agent = create_react_agent(
        model=llm,
        tools=[drasi_tool],
        checkpointer=memory,
    )

    # Configuration for conversation thread
    config: dict = {"configurable": {"thread_id": thread_id}}  # type: ignore[annotation-unchecked]

    # Interactive loop
    print("Agent ready! You can ask questions about Drasi queries.\n")
    print("Example questions:")
    print("  - What queries are available?")
    print("  - Read the results from query X")
    print("  - Subscribe to query Y for updates")
    print("\nNote: Notifications are added to the conversation, so you can ask")
    print("      the agent about them (e.g., 'What was the last notification?')")
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

            # Run agent
            try:
                # Get any buffered notifications and add them to the conversation
                notification_records = memory_handler.get_all()
                messages = []

                # Add any pending notifications as system messages
                for record in notification_records:
                    import json
                    message = (
                        f"[System Notification] {record.change_type.capitalize()} in query '{record.query_name}': "
                        f"{json.dumps(record.data, indent=2) if isinstance(record.data, dict) else str(record.data)}"
                    )
                    messages.append(("system", message))

                # Clear the notification buffer
                memory_handler.clear()

                # Add the user's message
                messages.append(("user", user_input))

                # Invoke the agent with all messages
                result = await agent.ainvoke(
                    {"messages": messages},
                    config=config  # type: ignore[arg-type]
                )

                # Print the final response
                if "messages" in result and result["messages"]:
                    last_message = result["messages"][-1]
                    if hasattr(last_message, "content"):
                        print(f"\n{last_message.content}")

            except Exception as e:
                print(f"\n❌ Error: {e}")

    except KeyboardInterrupt:
        print("\n\nShutting down...")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
