"""LangGraph memory integration handler.

This handler integrates with LangGraph's checkpointers to automatically inject
notifications into the conversation state as system messages.
"""

import json
from datetime import datetime
from typing import Any, TYPE_CHECKING, Optional
from collections import deque

from ..callbacks import BaseDrasiNotificationHandler

if TYPE_CHECKING:
    from langchain_core.messages import SystemMessage
    from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata
    from langchain_core.runnables import RunnableConfig

try:
    from langchain_core.messages import SystemMessage
    from langgraph.checkpoint.base import BaseCheckpointSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    SystemMessage = object  # type: ignore[misc,assignment]
    BaseCheckpointSaver = object  # type: ignore[misc,assignment]


class NotificationInjectingCheckpointer(BaseCheckpointSaver):  # type: ignore[misc]
    """Checkpointer wrapper that injects pending notifications into retrieved checkpoints."""

    def __init__(self, wrapped: "BaseCheckpointSaver", notification_buffer: Any, thread_id: str) -> None:  # type: ignore[valid-type]
        """Initialize the wrapper.

        Args:
            wrapped: The actual checkpointer to wrap
            notification_buffer: Shared buffer of pending notifications
            thread_id: Thread ID to inject notifications for
        """
        self.wrapped = wrapped
        self.notification_buffer = notification_buffer
        self.thread_id = thread_id

    def get(self, config: "RunnableConfig") -> Optional["Checkpoint"]:  # type: ignore[override]
        """Get checkpoint and inject pending notifications."""
        checkpoint = self.wrapped.get(config)

        # Only inject for our thread
        if checkpoint and config.get("configurable", {}).get("thread_id") == self.thread_id:
            if len(self.notification_buffer) > 0:
                # Inject pending notifications into messages
                channel_values = checkpoint.get("channel_values", {})
                messages = list(channel_values.get("messages", []))

                # Add all buffered notifications and clear buffer
                while len(self.notification_buffer) > 0:
                    notification = self.notification_buffer.popleft()
                    messages.append(notification)

                channel_values["messages"] = messages
                checkpoint["channel_values"] = channel_values

        return checkpoint

    def put(
        self,
        config: "RunnableConfig",
        checkpoint: "Checkpoint",
        metadata: "CheckpointMetadata",
        new_versions: Any,
    ) -> "RunnableConfig":
        """Delegate to wrapped checkpointer."""
        return self.wrapped.put(config, checkpoint, metadata, new_versions)

    def list(self, config: Optional["RunnableConfig"] = None, **kwargs):  # type: ignore[no-untyped-def]
        """Delegate to wrapped checkpointer."""
        return self.wrapped.list(config, **kwargs)

    async def aget(self, config: "RunnableConfig") -> Optional["Checkpoint"]:  # type: ignore[override]
        """Async get checkpoint and inject pending notifications."""
        checkpoint = await self.wrapped.aget(config)

        # Only inject for our thread
        if checkpoint and config.get("configurable", {}).get("thread_id") == self.thread_id:
            if len(self.notification_buffer) > 0:
                # Inject pending notifications into messages
                channel_values = checkpoint.get("channel_values", {})
                messages = list(channel_values.get("messages", []))

                # Add all buffered notifications and clear buffer
                while len(self.notification_buffer) > 0:
                    notification = self.notification_buffer.popleft()
                    messages.append(notification)

                channel_values["messages"] = messages
                checkpoint["channel_values"] = channel_values

        return checkpoint

    async def aput(
        self,
        config: "RunnableConfig",
        checkpoint: "Checkpoint",
        metadata: "CheckpointMetadata",
        new_versions: Any,
    ) -> "RunnableConfig":
        """Delegate async put to wrapped checkpointer."""
        return await self.wrapped.aput(config, checkpoint, metadata, new_versions)

    async def aget_tuple(self, config: "RunnableConfig"):  # type: ignore[no-untyped-def]
        """Get checkpoint tuple and inject pending notifications."""
        checkpoint_tuple = await self.wrapped.aget_tuple(config)

        if checkpoint_tuple is None:
            return None

        # CheckpointTuple is (config, checkpoint, metadata, parent_config, pending_writes)
        checkpoint = checkpoint_tuple.checkpoint

        # Only inject for our thread
        if checkpoint and config.get("configurable", {}).get("thread_id") == self.thread_id:
            if len(self.notification_buffer) > 0:
                # Inject pending notifications into messages
                channel_values = checkpoint.get("channel_values", {})
                messages = list(channel_values.get("messages", []))

                # Add all buffered notifications and clear buffer
                while len(self.notification_buffer) > 0:
                    notification = self.notification_buffer.popleft()
                    messages.append(notification)

                channel_values["messages"] = messages
                checkpoint["channel_values"] = channel_values

        return checkpoint_tuple

    async def alist(self, config: Optional["RunnableConfig"] = None, **kwargs):  # type: ignore[no-untyped-def]
        """Delegate async list to wrapped checkpointer."""
        return self.wrapped.alist(config, **kwargs)

    async def aput_writes(self, config: "RunnableConfig", writes: Any, task_id: str, task_path: str = "") -> None:  # type: ignore[no-untyped-def]
        """Delegate async put_writes to wrapped checkpointer."""
        return await self.wrapped.aput_writes(config, writes, task_id, task_path)

    def put_writes(self, config: "RunnableConfig", writes: Any, task_id: str, task_path: str = "") -> None:  # type: ignore[no-untyped-def]
        """Delegate put_writes to wrapped checkpointer."""
        return self.wrapped.put_writes(config, writes, task_id, task_path)

    def __getattr__(self, name: str) -> Any:
        """Delegate all other method calls to wrapped checkpointer."""
        return getattr(self.wrapped, name)


class LangGraphMemoryHandler(BaseDrasiNotificationHandler):
    """Handler that automatically injects notifications into LangGraph memory.

    This handler wraps a LangGraph checkpointer to automatically inject notifications
    as system messages when checkpoints are retrieved. This makes notifications seamlessly
    available to the agent without manual intervention.

    Args:
        checkpointer: LangGraph checkpointer to wrap (MemorySaver, PostgresSaver, etc.)
        thread_id: Thread ID for the conversation
        max_buffer_size: Maximum number of pending notifications to buffer (default: 100)

    Example:
        ```python
        from langchain_drasi import create_drasi_tool, MCPConnectionConfig
        from langchain_drasi.handlers import LangGraphMemoryHandler
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.prebuilt import create_react_agent

        # Create memory and handler
        memory = MemorySaver()
        thread_id = "my-conversation"
        handler = LangGraphMemoryHandler(memory, thread_id)

        # Create tool with handler
        tool = create_drasi_tool(
            mcp_config=config,
            notification_handlers=[handler]
        )

        # Create agent with the WRAPPED checkpointer
        agent = create_react_agent(model, tools=[tool], checkpointer=handler.checkpointer)

        # Notifications are automatically injected!
        result = await agent.ainvoke(
            {"messages": [("user", user_input)]},
            config={"configurable": {"thread_id": thread_id}}
        )
        ```

    Note:
        Requires langgraph and langchain-core to be installed.
        Use `handler.checkpointer` when creating the agent, not the original checkpointer.
    """

    def __init__(
        self,
        checkpointer: "BaseCheckpointSaver",  # type: ignore[valid-type]
        thread_id: str,
        max_buffer_size: int = 100
    ) -> None:
        """Initialize handler with checkpointer wrapper.

        Args:
            checkpointer: LangGraph checkpointer instance to wrap
            thread_id: Thread ID for the conversation
            max_buffer_size: Maximum number of pending notifications to buffer

        Raises:
            ImportError: If langgraph is not installed
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraphMemoryHandler requires langgraph to be installed. "
                "Install with: pip install langgraph langchain-core"
            )

        super().__init__()
        self.thread_id = thread_id
        self._buffer: deque = deque(maxlen=max_buffer_size)
        self.checkpointer = NotificationInjectingCheckpointer(checkpointer, self._buffer, thread_id)

    def _add_system_message(self, message: str) -> None:
        """Buffer a system message for automatic injection.

        Args:
            message: System message content
        """
        system_msg = SystemMessage(content=message)  # type: ignore[call-arg]
        self._buffer.append(system_msg)

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Handle when results are added."""
        try:
            data_str = json.dumps(added_data, indent=2, default=str)
        except Exception:
            data_str = str(added_data)

        message = (
            f"[System Notification - {datetime.now().isoformat()}] "
            f"New result added to query '{query_name}': "
            f"{data_str}"
        )
        self._add_system_message(message)

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Handle when results are updated."""
        try:
            data_str = json.dumps(updated_data, indent=2, default=str)
        except Exception:
            data_str = str(updated_data)

        message = (
            f"[System Notification - {datetime.now().isoformat()}] "
            f"Result updated in query '{query_name}': "
            f"{data_str}"
        )
        self._add_system_message(message)

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Handle when results are deleted."""
        try:
            data_str = json.dumps(deleted_data, indent=2, default=str)
        except Exception:
            data_str = str(deleted_data)

        message = (
            f"[System Notification - {datetime.now().isoformat()}] "
            f"Result deleted from query '{query_name}': "
            f"{data_str}"
        )
        self._add_system_message(message)
