"""Buffer notification handler.

This handler stores notifications in a FIFO queue for sequential consumption.
Useful for processing notifications one at a time in order.
"""

from collections import deque
from typing import Any

from ..callbacks import BaseDrasiNotificationHandler
from .memory_handler import NotificationRecord


class BufferHandler(BaseDrasiNotificationHandler):
    """Notification handler that stores events in a FIFO queue buffer.

    This handler maintains a queue of notifications that can be consumed
    one at a time in the order they were received. Useful for sequential
    processing of notifications.

    Example:
        ```python
        from langchain_drasi import create_drasi_tool, MCPConnectionConfig
        from langchain_drasi.handlers import BufferHandler

        # Create handler
        handler = BufferHandler(max_size=50)

        # Create tool with handler
        config = MCPConnectionConfig(server_url="http://localhost:8083")
        tool = create_drasi_tool(mcp_config=config, notification_handlers=[handler])

        # Later, consume notifications
        while not handler.is_empty():
            notification = handler.consume()
            print(f"Processing: {notification}")
        ```

    Attributes:
        buffer: Queue of notification records
        max_size: Maximum number of notifications to buffer (None = unlimited)
    """

    def __init__(self, max_size: int | None = None) -> None:
        """Initialize buffer handler.

        Args:
            max_size: Maximum number of notifications to buffer.
                     Oldest notifications are discarded when limit is reached.
                     None means unlimited. (default: None)
        """
        super().__init__()
        self.buffer: deque[NotificationRecord] = deque(maxlen=max_size)
        self.max_size = max_size

    def _add_record(self, record: NotificationRecord) -> None:
        """Add a notification record to the buffer.

        If max_size is set and buffer is full, oldest notification is
        automatically discarded (deque handles this automatically).

        Args:
            record: Notification record to add
        """
        self.buffer.append(record)

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Buffer result added notification.

        Args:
            query_name: Name of the query
            added_data: Added result data
        """
        record = NotificationRecord(query_name, "added", added_data)
        self._add_record(record)

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Buffer result updated notification.

        Args:
            query_name: Name of the query
            updated_data: Updated result data
        """
        record = NotificationRecord(query_name, "updated", updated_data)
        self._add_record(record)

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Buffer result deleted notification.

        Args:
            query_name: Name of the query
            deleted_data: Deleted result data
        """
        record = NotificationRecord(query_name, "deleted", deleted_data)
        self._add_record(record)

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Buffer notification error.

        Args:
            query_name: Name of the query
            error: The exception that occurred
        """
        record = NotificationRecord(query_name, "error", error)
        self._add_record(record)

    def consume(self) -> NotificationRecord | None:
        """Consume and remove the next notification from the buffer.

        Returns the oldest notification in FIFO order and removes it
        from the buffer.

        Returns:
            The next notification record, or None if buffer is empty
        """
        if self.buffer:
            return self.buffer.popleft()
        return None

    def peek(self) -> NotificationRecord | None:
        """View the next notification without consuming it.

        Returns:
            The next notification record, or None if buffer is empty
        """
        if self.buffer:
            return self.buffer[0]
        return None

    def is_empty(self) -> bool:
        """Check if the buffer is empty.

        Returns:
            True if buffer has no notifications, False otherwise
        """
        return len(self.buffer) == 0

    def size(self) -> int:
        """Get the current number of notifications in the buffer.

        Returns:
            Number of notifications currently in the buffer
        """
        return len(self.buffer)

    def clear(self) -> None:
        """Clear all notifications from the buffer."""
        self.buffer.clear()

    def get_all(self) -> list[NotificationRecord]:
        """Get all buffered notifications without consuming them.

        Returns a copy of all notifications currently in the buffer,
        in the order they would be consumed.

        Returns:
            List of all notification records in FIFO order
        """
        return list(self.buffer)
