"""Sample application using LangGraph with DrasiTool.

This example demonstrates how to use DrasiTool with LangGraph to build
a stateful agent that can query and monitor Drasi continuous queries.

Prerequisites:
    - Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY in environment
    - Have a Drasi MCP server running and accessible
    - Set DRASI_SERVER_URL in your .env file (default: http://localhost:8083)
    - Optional: Set DRASI_API_TOKEN if your server requires authentication
    - Install langgraph: pip install langgraph

IMPORTANT: This example requires a running Drasi MCP server. Without one,
the agent will not be able to discover or read queries.

Usage:
    python examples/langgraph_example.py
"""

import asyncio
import os
import sys
import logging
from typing import TypedDict, Annotated, Any
from dotenv import load_dotenv

logging.basicConfig(
    #level=logging.DEBUG,
    #format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    #stream=sys.stdout
)

from langgraph.graph import StateGraph, END, add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool

# Import Drasi components
from langchain_drasi import (
    create_drasi_tool,
    MCPConnectionConfig,
    BaseDrasiNotificationHandler,
)
from langchain_drasi.handlers import MemoryHandler

# Import Azure OpenAI (can also use langchain_openai.ChatOpenAI)
try:
    from langchain_openai import AzureChatOpenAI
    USE_AZURE = True
except ImportError:
    from langchain_openai import ChatOpenAI
    USE_AZURE = False


# Load environment variables
load_dotenv()


# Define agent state
class AgentState(TypedDict):
    """State for the LangGraph agent."""

    messages: Annotated[list[BaseMessage], add_messages]


# Node functions
def should_continue(state: AgentState) -> str:
    """Determine if the agent should continue or end.

    Args:
        state: Current agent state

    Returns:
        "continue" to invoke tools, "end" to finish
    """
    last_message = state["messages"][-1]

    # If the last message has tool calls, continue
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"

    # Otherwise, end
    return "end"


async def call_model(state: AgentState, llm: Any) -> dict:
    """Call the LLM to decide what to do next.

    Args:
        state: Current agent state
        llm: Language model to use

    Returns:
        Updated state with LLM response
    """
    messages = state["messages"]
    response = await llm.ainvoke(messages)

    return {"messages": [response]}


async def call_tool(state: AgentState, tools: dict[str, BaseTool]) -> dict:
    """Execute tool calls from the LLM.

    Args:
        state: Current agent state
        tools: Dictionary mapping tool names to tool instances

    Returns:
        Updated state with tool results
    """
    last_message = state["messages"][-1]

    # Execute each tool call
    tool_messages = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]

        # Get the tool
        tool = tools.get(tool_name)
        if not tool:
            tool_messages.append(
                ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found",
                    tool_call_id=tool_call["id"],
                )
            )
            continue

        # Execute tool
        try:
            result = await tool.ainvoke(tool_input)
            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                )
            )
        except Exception as e:
            tool_messages.append(
                ToolMessage(
                    content=f"Error executing tool: {str(e)}",
                    tool_call_id=tool_call["id"],
                )
            )

    return {"messages": tool_messages}


# Custom notification handler
class MyHandler(BaseDrasiNotificationHandler):
    """Custom handler that prints changes to the console."""

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Handle when results are added to a query."""
        print(f"\n🆕 ADDED to '{query_name}':")
        print(f"   {added_data}")

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Handle when results are updated in a query."""
        print(f"\n🔄 UPDATED in '{query_name}':")
        print(f"   {updated_data}")

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Handle when results are deleted from a query."""
        print(f"\n🗑️  DELETED from '{query_name}':")
        print(f"   {deleted_data}")


async def main() -> None:
    """Run the LangGraph example."""
    print("=" * 60)
    print("LangGraph + Drasi Example")
    print("=" * 60)

    # Check for server URL configuration
    server_url = os.getenv("DRASI_SERVER_URL")
    if not server_url:
        print("\n⚠️  WARNING: DRASI_SERVER_URL not set in environment!")
        print("Using default URL - ensure your Drasi MCP server is running at http://localhost:8083")
        print("Or set DRASI_SERVER_URL in your .env file to point to your server.\n")

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

    # Create notification handlers
    memory_handler = MemoryHandler(max_size=100)
    my_handler = MyHandler()

    # Create Drasi tool with both handlers
    print("\nCreating Drasi tool...")
    drasi_tool = create_drasi_tool(
        mcp_config=mcp_config,
        notification_handlers=[memory_handler, my_handler],
    )

    # Create LLM
    print("Initializing LLM...")
    if USE_AZURE:
        llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            temperature=0,
        )
    else:
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=0,
        )

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools([drasi_tool])

    # Create tool mapping
    tools = {drasi_tool.name: drasi_tool}

    # Create LangGraph
    print("Building LangGraph workflow...")
    workflow = StateGraph(AgentState)

    # Create bound node functions with proper async handling
    async def agent_node(state: AgentState) -> dict:
        """Agent node that calls the LLM."""
        return await call_model(state, llm_with_tools)

    async def tools_node(state: AgentState) -> dict:
        """Tools node that executes tool calls."""
        return await call_tool(state, tools)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )

    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")

    # Compile the graph
    app = workflow.compile()

    # Example conversation
    queries = [
        "What Drasi queries are available? List them all.",
        "Read the current results from the 'freezerx' query.",
        "Now subscribe to the 'freezerx' query to get real-time updates.",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Query {i}: {query}")
        print(f"{'=' * 60}\n")

        try:
            # Invoke the graph
            result = await app.ainvoke(
                {"messages": [HumanMessage(content=query)]},
                config={"recursion_limit": 10},
            )

            # Print final response
            final_message = result["messages"][-1]
            if isinstance(final_message, AIMessage):
                print(f"\nAgent Response:\n{final_message.content}\n")

        except Exception as e:
            print(f"Error: {e}\n")

    # Show notification statistics
    print("\n" + "=" * 60)
    print("Notification Statistics")
    print("=" * 60)
    print(f"Total notifications received: {memory_handler.get_count()}")
    print(f"By query: {memory_handler.get_count_by_query()}")
    print(f"By type: {memory_handler.get_count_by_type()}")

    # Listen for more notifications
    print("\n" + "=" * 60)
    print("Listening for notifications (Ctrl+C to exit)...")
    print("=" * 60)

    try:
        # Keep the event loop running to receive notifications
        while True:
            await asyncio.sleep(5)

            # Show new notifications
            notifications = memory_handler.get_all()
            if notifications:
                latest = notifications[-1]
                print(f"\nLatest notification: {latest}")

    except KeyboardInterrupt:
        print("\nShutting down...")

        # Show final stats
        print("\nFinal Statistics:")
        print(f"Total notifications: {memory_handler.get_count()}")
        print(f"By query: {memory_handler.get_count_by_query()}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
