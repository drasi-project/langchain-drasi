"""LangChain memory integration handler.

This handler integrates with LangChain's ConversationBufferMemory to automatically inject
notifications into the conversation history as system messages.
"""

import json
from datetime import datetime
from typing import Any

from ..callbacks import BaseDrasiNotificationHandler
from langchain_core.memory import BaseMemory



class LangChainMemoryHandler(BaseDrasiNotificationHandler):
    """Handler that automatically injects notifications into LangChain conversation memory.

    This handler holds a reference to a LangChain ConversationBufferMemory and automatically
    adds notifications as system messages to the conversation history. This makes notifications
    seamlessly available to the agent without manual intervention.

    Args:
        memory: LangChain ConversationBufferMemory instance

    Example:
        ```python
        from langchain_drasi import create_drasi_tool, MCPConnectionConfig
        from langchain_drasi.handlers import LangChainMemoryHandler
        from langchain.memory import ConversationBufferMemory
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain import hub

        # Create memory and handler
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        handler = LangChainMemoryHandler(memory)

        # Create tool with handler
        tool = create_drasi_tool(
            mcp_config=config,
            notification_handlers=[handler]
        )

        # Create agent with memory
        prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(llm, tools=[tool], prompt=prompt)
        agent_executor = AgentExecutor(agent=agent, tools=[tool], memory=memory)

        # Notifications are automatically added to conversation history!
        result = await agent_executor.ainvoke({"input": user_input})
        ```

    Note:
        Requires langchain and langchain-core to be installed.
    """

    def __init__(
        self,
        memory: BaseMemory
    ) -> None:
        """Initialize handler with memory reference.

        Args:
            memory: LangChain ConversationBufferMemory instance
        """

        super().__init__()
        self.memory = memory

    def _add_system_message(self, message: str) -> None:
        """Add a system message to the conversation history.

        Args:
            message: System message content
        """
        # Format as if the user is informing the AI about the notification
        # This creates a natural conversation pattern that LLMs are trained to recall
        # The acknowledgment explicitly states this is current data to prevent refetching
        self.memory.save_context(
            {"input": message},
            {"output": "I've recorded this notification, and will use it to inform future responses."}
        )        

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Handle when results are added."""
        try:
            data_str = json.dumps(added_data, default=str)
        except Exception:
            data_str = str(added_data)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            f"[Notification at {timestamp}] The '{query_name}' query detected new data: {data_str}"
        )
        self._add_system_message(message)

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Handle when results are updated."""
        try:
            data_str = json.dumps(updated_data, default=str)
        except Exception:
            data_str = str(updated_data)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            f"[Notification at {timestamp}] The '{query_name}' query detected updated data: {data_str}"
        )
        self._add_system_message(message)

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Handle when results are deleted."""
        try:
            data_str = json.dumps(deleted_data, default=str)
        except Exception:
            data_str = str(deleted_data)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            f"[Notification at {timestamp}] The '{query_name}' query detected deleted data: {data_str}"
        )
        self._add_system_message(message)
