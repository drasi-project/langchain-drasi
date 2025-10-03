"""Integration tests for LangGraphMemoryHandler.

Tests that notifications are properly added to LangGraph conversation memory.
"""
import asyncio
import pytest

from langchain_drasi import create_drasi_tool, MCPConnectionConfig, LangGraphMemoryHandler
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models.chat_models import SimpleChatModel


class ToolBindableFakeChatModel(SimpleChatModel):
    """Fake chat model that supports bind_tools for testing."""

    def _call(self, messages, stop=None, run_manager=None, **kwargs):
        """Return a simple response."""
        return "OK"

    def bind_tools(self, tools, **kwargs):
        """Mock bind_tools - just return self."""
        return self

    @property
    def _llm_type(self) -> str:
        return "fake"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_langgraph_memory_handler_adds_notifications_to_memory(mock_mcp_transport):
    """Test that notifications are added to LangGraph memory and visible to agent."""

    # Create memory and thread
    memory = MemorySaver()
    thread_id = "test-notifications"
    config = {"configurable": {"thread_id": thread_id}}

    # Create handler
    handler = LangGraphMemoryHandler(memory, thread_id)

    # Create MCP config
    mcp_config = MCPConnectionConfig(server_url="http://localhost:8080/mcp")

    # Create tool with handler
    tool = create_drasi_tool(
        mcp_config=mcp_config,
        notification_handlers=[handler]
    )

    # Create agent with mock LLM - use wrapped checkpointer
    llm = ToolBindableFakeChatModel()
    agent = create_react_agent(
        model=llm,
        tools=[tool],
        checkpointer=handler.checkpointer,
    )

    # First agent interaction - creates initial checkpoint
    result1 = await agent.ainvoke(
        {"messages": [HumanMessage(content="Hello")]},
        config=config  # type: ignore[arg-type]
    )

    print(f"\n=== After first invocation ===")
    all_messages1 = result1["messages"]
    system_messages1 = [m for m in all_messages1 if hasattr(m, 'type') and m.type == 'system']
    print(f"System messages: {len(system_messages1)}")
    assert len(system_messages1) == 0, "Should have no system messages initially"

    # Simulate a notification arriving
    print("\n=== Simulating notification ===")
    handler.on_result_added(
        "test-query",
        {"id": "123", "value": "test data"}
    )

    # Check that notification is buffered
    print("\n=== Checking buffered notifications ===")
    print(f"Buffered notifications: {len(handler._buffer)}")
    assert len(handler._buffer) > 0, "Should have buffered notifications"

    # Second agent interaction - notifications automatically injected
    print("\n=== Second invocation ===")
    print(f"Buffered notifications will be auto-injected: {len(handler._buffer)}")

    result2 = await agent.ainvoke(
        {"messages": [HumanMessage(content="What's in your memory?")]},
        config=config  # type: ignore[arg-type]
    )

    # The agent should see the notification as a system message
    all_messages2 = result2["messages"]
    system_messages2 = [m for m in all_messages2 if hasattr(m, 'type') and m.type == 'system']
    print(f"System messages in conversation: {len(system_messages2)}")
    for msg in system_messages2:
        print(f"  - {msg.content[:100]}")

    # Assert: Should have at least one system message from notification
    assert len(system_messages2) > 0, f"Should have system message from notification, got {len(system_messages2)}"
    assert any("test-query" in msg.content for msg in system_messages2), \
        "System message should mention the query name"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_langgraph_memory_handler_multiple_notifications(mock_mcp_transport):
    """Test that multiple notifications are all added to memory."""

    memory = MemorySaver()
    thread_id = "test-multi-notifications"
    config = {"configurable": {"thread_id": thread_id}}

    handler = LangGraphMemoryHandler(memory, thread_id)

    mcp_config = MCPConnectionConfig(server_url="http://localhost:8080/mcp")
    tool = create_drasi_tool(
        mcp_config=mcp_config,
        notification_handlers=[handler]
    )

    llm = ToolBindableFakeChatModel()
    agent = create_react_agent(
        model=llm,
        tools=[tool],
        checkpointer=handler.checkpointer,
    )

    # Initial run to create checkpoint
    await agent.ainvoke(
        {"messages": [HumanMessage(content="Start")]},
        config=config  # type: ignore[arg-type]
    )

    # Add multiple notifications
    handler.on_result_added("query1", {"data": "notification1"})
    handler.on_result_updated("query2", {"data": "notification2"})
    handler.on_result_deleted("query3", {"data": "notification3"})

    # Run agent again - notifications automatically injected
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="Check memory")]},
        config=config  # type: ignore[arg-type]
    )

    # Should have 3 system messages
    all_messages = result["messages"]
    system_messages = [m for m in all_messages if hasattr(m, 'type') and m.type == 'system']

    print(f"\nSystem messages: {len(system_messages)}")
    for msg in system_messages:
        print(f"  - {msg.content[:80]}")

    assert len(system_messages) >= 3, f"Should have at least 3 notifications, got {len(system_messages)}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_langgraph_memory_handler_no_checkpoint_yet(mock_mcp_transport):
    """Test that handler doesn't crash when no checkpoint exists yet."""

    memory = MemorySaver()
    thread_id = "test-no-checkpoint"

    handler = LangGraphMemoryHandler(memory, thread_id)

    # Try to add notification before any checkpoint exists
    # Should not raise an error
    handler.on_result_added("query", {"data": "test"})

    # Verify no checkpoint was created (using wrapped checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    checkpoint = handler.checkpointer.get(config)  # type: ignore[arg-type]
    assert checkpoint is None, "Should not create checkpoint when none exists"
