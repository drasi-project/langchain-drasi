"""End-to-end test for notification recall from memory.

This test verifies that notifications added to LangChain memory by the
LangChainMemoryHandler can be recalled by the LLM without refetching data.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain import hub
from langchain_core.prompts import PromptTemplate

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

        assert "<<DRASI NOTIFICATION>>" in chat_history
        assert "freezerx" in chat_history
        assert "35" in chat_history
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
        assert "<<DRASI NOTIFICATION>>" in chat_history
        assert "NOTIFICATION" in chat_history
        assert "freezerx" in chat_history
        assert '"freezerId": "2"' in chat_history or "'freezerId': '2'" in chat_history
        assert "35" in chat_history

        # Verify it's formatted properly (not raw Python objects)
        assert "HumanMessage" not in chat_history
        assert "AIMessage" not in chat_history

        print("\n✓ Notification is properly formatted and visible in chat history")

    @pytest.mark.asyncio
    async def test_react_agent_with_notification_memory(
        self,
        drasi_tool_with_memory,
        memory: ConversationBufferMemory,
    ):
        """Test ReAct agent with notification memory integration."""
        tool, memory_handler = drasi_tool_with_memory

        # Create a mock LLM that we can control
        mock_llm = MagicMock()

        # Set up the LLM to respond appropriately based on input
        def mock_invoke(prompt_value, *args, **kwargs):
            prompt_text = str(prompt_value)

            # Create a mock response object
            response = MagicMock()

            # If the prompt contains our notification, respond without using tools
            if "<<DRASI NOTIFICATION>>" in prompt_text and "What notifications" in prompt_text:
                response.content = """Thought: Do I need to use a tool? No
Final Answer: I can see from the conversation history that you received a notification for the freezerx query. The notification shows freezerId "2" with a temperature of 35 degrees, which triggered an alert."""
            else:
                # Default response
                response.content = """Thought: Do I need to use a tool? No
Final Answer: I processed your request."""

            return response

        mock_llm.invoke = mock_invoke

        # Create ReAct prompt
        prompt = hub.pull("hwchase17/react-chat")

        # Create agent with memory
        agent = create_react_agent(mock_llm, [tool], prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=[tool],
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )

        # Step 1: Subscribe to a query
        memory.save_context(
            {"input": "Subscribe to freezerx"},
            {"output": "Successfully subscribed to freezerx"}
        )

        # Step 2: Simulate notification arrival
        memory_handler.on_result_added(
            "freezerx",
            {"freezerId": "2", "temperature": 35, "alert": True}
        )

        # Step 3: Ask about notifications
        result = await agent_executor.ainvoke({
            "input": "What notifications have I received?"
        })

        print("\n" + "="*70)
        print("AGENT RESPONSE:")
        print("="*70)
        print(result["output"])
        print("="*70)

        # The agent should be able to recall the notification
        output = result["output"].lower()
        assert "freezerx" in output or "freezer" in output
        assert "35" in output or "temperature" in output

        print("\n✓ Agent successfully recalled notification from memory")

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
        assert chat_history.count("<<DRASI NOTIFICATION>>") == 3
        assert "ADDED" in chat_history
        assert "UPDATED" in chat_history
        assert "DELETED" in chat_history

        # Check they're distinguishable from normal conversation
        lines = chat_history.split("\n")
        notification_lines = [l for l in lines if "<<DRASI NOTIFICATION>>" in l]
        assert len(notification_lines) == 3

        print(f"\n✓ Found {len(notification_lines)} distinct notification markers")
