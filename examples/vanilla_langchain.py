"""Sample application using vanilla LangChain with DrasiTool.

This example demonstrates how to use DrasiTool with a basic LangChain
ReAct agent to query Drasi continuous queries.

Prerequisites:
    - Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY in environment
    - Have a Drasi MCP server running and accessible
    - Set DRASI_SERVER_URL in your .env file (default: http://localhost:8083)
    - Optional: Set DRASI_API_TOKEN if your server requires authentication

IMPORTANT: This example requires a running Drasi MCP server. Without one,
the agent will not be able to discover or read queries.

Usage:
    python examples/vanilla_langchain.py
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    stream=sys.stdout
)

from langchain.agents import AgentExecutor, create_react_agent  # type: ignore[import-not-found]
from langchain_core.prompts import PromptTemplate

# Import Drasi components
from langchain_drasi import (
    create_drasi_tool,
    MCPConnectionConfig,
)
from langchain_drasi.handlers import ConsoleHandler

# Import OpenAI models
try:
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
    USE_AZURE = True
except ImportError:
    from langchain_openai import ChatOpenAI
    AzureChatOpenAI = ChatOpenAI  # type: ignore[misc,assignment]
    USE_AZURE = False


# Load environment variables
load_dotenv()


# ReAct prompt template
REACT_PROMPT = PromptTemplate.from_template(
    """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""
)


async def main() -> None:
    """Run the vanilla LangChain example."""
    print("=" * 60)
    print("Vanilla LangChain + Drasi Example")
    print("=" * 60)

    # Check for server URL configuration
    server_url = os.getenv("DRASI_SERVER_URL")
    if not server_url:
        print("\n⚠️  WARNING: DRASI_SERVER_URL not set in environment!")
        print("Using default placeholder URL - this will likely fail.")
        print("Set DRASI_SERVER_URL in your .env file to point to your Drasi MCP server.")
        print("Example: DRASI_SERVER_URL=http://localhost:8083\n")

    # Configure HTTP connection to remote Drasi MCP server
    # Update this to match your Drasi server URL and authentication
    mcp_config = MCPConnectionConfig(
        server_url=server_url or "http://localhost:8083",
        headers={
            "Authorization": f"Bearer {os.getenv('DRASI_API_TOKEN')}"
        } if os.getenv("DRASI_API_TOKEN") else None,
        timeout=30.0,
    )

    print(f"\nConnecting to Drasi server: {mcp_config.server_url}")

    # Create notification handler to see real-time updates
    console_handler = ConsoleHandler(
        include_timestamp=True,
        pretty_print=True,
    )

    # Create Drasi tool
    print("\nCreating Drasi tool...")
    drasi_tool = create_drasi_tool(
        mcp_config=mcp_config,
        notification_handlers=[console_handler],
    )

    # Create LLM
    print("Initializing LLM...")
    if USE_AZURE:
        llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),  # type: ignore[call-arg]
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),  # type: ignore[call-arg]
            temperature=0,
        )
    else:
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=0,
        )

    # Create ReAct agent
    print("Creating agent...")
    agent = create_react_agent(
        llm=llm,
        tools=[drasi_tool],
        prompt=REACT_PROMPT,
    )

    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[drasi_tool],
        verbose=True,
        handle_parsing_errors=True,
    )

    # Example queries
    queries = [
        "What Drasi queries are available?",
        "Read the results from the 'active-orders' query",
        "Subscribe to updates from the 'freezerx' query",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Query {i}: {query}")
        print(f"{'=' * 60}\n")

        try:
            result = await agent_executor.ainvoke({"input": query})
            print(f"\nAgent Response:\n{result['output']}\n")

        except Exception as e:
            print(f"Error: {e}\n")

    # Keep running to receive notifications (if subscribed)
    print("\n" + "=" * 60)
    print("Listening for notifications (Ctrl+C to exit)...")
    print("=" * 60)

    try:
        # Keep the event loop running to receive notifications
        await asyncio.sleep(60)  # Listen for 60 seconds
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
