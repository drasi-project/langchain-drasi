"""End-to-end test for notification recall from memory.

This test verifies that notifications added to LangChain memory by the
LangChainMemoryHandler can be recalled by the LLM without refetching data.
"""

import pytest

from langchain.memory import ConversationBufferMemory

from langchain_drasi import create_drasi_tool, MCPConnectionConfig
from langchain_drasi.handlers import LangChainMemoryHandler
from langchain_drasi.models import ChangeNotification, ChangeType


@pytest.mark.integration
class TestNotificationMemoryRecall:
    """Test that notifications in memory can be recalled by the LLM."""

    @pytest.fixture
    def memory(self) -> ConversationBufferMemory:
        """Create conversation memory for testing."""
        return ConversationBufferMemory(
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            return_messages=False,  # ReAct prompt expects string format
        )

    @pytest.fixture
    def mcp_config(self) -> MCPConnectionConfig:
        """MCP configuration for testing."""
        return MCPConnectionConfig(
            server_url="http://localhost:8080/mcp",
        )

    @pytest.fixture
    async def drasi_tool_with_memory(
        self,
        mcp_config: MCPConnectionConfig,
        memory: ConversationBufferMemory,
        mock_mcp_transport
    ):
        """Create DrasiTool with LangChainMemoryHandler attached."""
        memory_handler = LangChainMemoryHandler(memory)
        tool = create_drasi_tool(
            mcp_config=mcp_config,
            notification_handlers=[memory_handler],
        )
        return tool, memory_handler

    @pytest.mark.asyncio
    async def test_notification_is_added_to_memory(
        self,
        drasi_tool_with_memory,
        memory: ConversationBufferMemory,
    ):
        """Test that notifications are properly added to memory."""
        tool, memory_handler = drasi_tool_with_memory

        # Simulate receiving a notification
        notification = ChangeNotification()
        notification.change_type = ChangeType.ADDED
        notification.query_name = "freezerx"
        notification.data = {"freezerId": "2", "temperature": 35}

        # Handler should add to memory
        memory_handler.on_result_added("freezerx", notification.data)

        # Check memory contains the notification
        chat_history = memory.load_memory_variables({})["chat_history"]

        assert "[Notification at" in chat_history
        assert "freezerx" in chat_history
        assert "35" in chat_history
        assert "I've recorded this notification" in chat_history
        print("\n✓ Notification added to memory successfully")
        print(f"Memory content:\n{chat_history}")

    @pytest.mark.asyncio
    async def test_mock_llm_can_recall_notification_from_memory(
        self,
        drasi_tool_with_memory,
        memory: ConversationBufferMemory,
    ):
        """Test that an LLM can see and recall notifications from memory."""
        tool, memory_handler = drasi_tool_with_memory

        # Add a normal conversation turn
        memory.save_context(
            {"input": "Subscribe to freezerx"},
            {"output": "Successfully subscribed to freezerx query"}
        )

        # Simulate a notification
        memory_handler.on_result_added(
            "freezerx",
            {"freezerId": "2", "temperature": 35, "alert": True}
        )

        # Add another conversation turn
        memory.save_context(
            {"input": "What notifications have I received?"},
            {"output": "Checking memory..."}
        )

        # Get the chat history as the LLM would see it
        chat_history = memory.load_memory_variables({})["chat_history"]

        print("\n" + "="*70)
        print("CHAT HISTORY AS LLM SEES IT:")
        print("="*70)
        print(chat_history)
        print("="*70)

        # Verify the notification is visible
        assert "[Notification at" in chat_history
        assert "freezerx" in chat_history
        assert '"freezerId": "2"' in chat_history or "'freezerId': '2'" in chat_history
        assert "35" in chat_history
        assert "I've recorded this notification" in chat_history

        # Verify it's formatted properly (not raw Python objects)
        assert "HumanMessage" not in chat_history
        assert "AIMessage" not in chat_history

        print("\n✓ Notification is properly formatted and visible in chat history")


    @pytest.mark.asyncio
    async def test_notification_format_in_chat_history(
        self,
        memory: ConversationBufferMemory,
    ):
        """Test that notification format is clear and distinguishable."""
        handler = LangChainMemoryHandler(memory)

        # Add different types of notifications
        handler.on_result_added("query1", {"id": 1, "value": "test"})
        handler.on_result_updated("query2", {"id": 2, "value": "updated"})
        handler.on_result_deleted("query3", {"id": 3})

        chat_history = memory.load_memory_variables({})["chat_history"]

        print("\n" + "="*70)
        print("FORMATTED NOTIFICATIONS IN MEMORY:")
        print("="*70)
        print(chat_history)
        print("="*70)

        # Check all notification types are present
        assert chat_history.count("[Notification at") == 3
        assert "detected new data" in chat_history
        assert "detected updated data" in chat_history
        assert "detected deleted data" in chat_history

        # Check they're distinguishable from normal conversation
        lines = chat_history.split("\n")
        notification_lines = [l for l in lines if "[Notification at" in l]
        assert len(notification_lines) == 3

        print(f"\n✓ Found {len(notification_lines)} distinct notification markers")
