"""Interactive ReAct agent with conversation memory and automatic notification injection.

This example demonstrates how to use DrasiTool with LangChain's ReAct agent
and automatically integrate notifications into the conversation memory using
LangChainMemoryHandler. Notifications are added as system messages directly
to the conversation history, so the agent is aware of them without manual injection.

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
from dotenv import load_dotenv

from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI

# Import Drasi components
from langchain_drasi import (
    create_drasi_tool,
    MCPConnectionConfig,
    ConsoleHandler,
    LangChainMemoryHandler,
)

# Load environment variables
load_dotenv()


async def main() -> None:
    """Run the interactive ReAct agent with automatic notification memory."""
    print("=" * 70)
    print("Interactive Drasi Agent (ReAct + Auto Notification Memory)")
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

    # Create conversation memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        input_key="input",
        output_key="output",
    )

    # Create notification handlers:
    # 1. Console handler to print notifications
    # 2. LangChain memory handler to automatically inject notifications
    console_handler = ConsoleHandler()
    langchain_handler = LangChainMemoryHandler(memory)

    # Create Drasi tool with both notification handlers
    drasi_tool = create_drasi_tool(
        mcp_config=mcp_config,
        notification_handlers=[console_handler, langchain_handler],
    )

    # Initialize LLM
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=0,
    )

    # Pull ReAct prompt with chat history support
    print("Loading ReAct prompt template...")
    prompt = hub.pull("hwchase17/react-chat")

    # Create ReAct agent
    print("Creating ReAct agent with memory...\n")
    agent = create_react_agent(llm, [drasi_tool], prompt)

    # Create agent executor with memory
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[drasi_tool],
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=20,
    )

    # Interactive loop
    print("Agent ready! You can ask questions about Drasi queries.\n")
    print("Example questions:")
    print("  - What queries are available?")
    print("  - Track freezers above 32")
    print("  - What is the status of freezer 2?")
    print("  - What was your last notification?")
    print("\nNote: Notifications are AUTOMATICALLY added to the conversation memory!")
    print("      Ask about them anytime (e.g., 'What notifications have I received?')")
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

            # Run agent - notifications are automatically injected
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
