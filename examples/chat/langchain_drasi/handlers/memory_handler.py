"""Memory notification handler.

This handler stores notifications in memory for later retrieval and analysis.
Useful for testing and building reactive applications.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any

from ..callbacks import BaseDrasiNotificationHandler


class NotificationRecord:
    """Record of a single notification event.

    Attributes:
        query_name: Name of the query
        change_type: Type of change (added/updated/deleted/error)
        data: Notification data or error
        timestamp: When the notification was received
    """

    def __init__(
        self,
        query_name: str,
        change_type: str,
        data: dict[str, Any] | Exception,
        timestamp: datetime | None = None,
    ) -> None:
        """Initialize notification record.

        Args:
            query_name: Name of the query
            change_type: Type of change
            data: Notification data or error
            timestamp: Timestamp (defaults to now)
        """
        self.query_name = query_name
        self.change_type = change_type
        self.data = data
        self.timestamp = timestamp or datetime.now()

    def __repr__(self) -> str:
        """String representation of the record."""
        return (
            f"NotificationRecord(query={self.query_name}, "
            f"type={self.change_type}, timestamp={self.timestamp})"
        )


class MemoryHandler(BaseDrasiNotificationHandler):
    """Notification handler that stores events in memory.

    This handler maintains a list of all received notifications, allowing
    you to retrieve and analyze them later. Useful for testing, debugging,
    and building reactive applications.

    Example:
        ```python
        from langchain_drasi import create_drasi_tool, MCPConnectionConfig
        from langchain_drasi.handlers import MemoryHandler

        # Create handler
        handler = MemoryHandler(max_size=100)

        # Create tool with handler
        config = MCPConnectionConfig(
            server_command="npx",
            server_args=["-y", "@drasi/query-api"]
        )
        tool = create_drasi_tool(mcp_config=config, notification_handlers=[handler])

        # Later, retrieve notifications
        all_notifications = handler.get_all()
        freezer_notifications = handler.get_by_query("freezerx")
        added_events = handler.get_by_type("added")
        ```

    Attributes:
        notifications: List of all notification records
        max_size: Maximum number of notifications to store (None = unlimited)
    """

    def __init__(self, max_size: int | None = None) -> None:
        """Initialize memory handler.

        Args:
            max_size: Maximum number of notifications to store.
                     Older notifications are discarded when limit is reached.
                     None means unlimited. (default: None)
        """
        super().__init__()
        self.notifications: list[NotificationRecord] = []
        self.max_size = max_size

    def _add_record(self, record: NotificationRecord) -> None:
        """Add a notification record, respecting max_size.

        Args:
            record: Notification record to add
        """
        self.notifications.append(record)

        # Trim if exceeds max_size
        if self.max_size is not None and len(self.notifications) > self.max_size:
            # Remove oldest notifications
            excess = len(self.notifications) - self.max_size
            self.notifications = self.notifications[excess:]

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Store result added notification.

        Args:
            query_name: Name of the query
            added_data: Added result data
        """
        record = NotificationRecord(query_name, "added", added_data)
        self._add_record(record)

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Store result updated notification.

        Args:
            query_name: Name of the query
            updated_data: Updated result data
        """
        record = NotificationRecord(query_name, "updated", updated_data)
        self._add_record(record)

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Store result deleted notification.

        Args:
            query_name: Name of the query
            deleted_data: Deleted result data
        """
        record = NotificationRecord(query_name, "deleted", deleted_data)
        self._add_record(record)

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Store notification error.

        Args:
            query_name: Name of the query
            error: The exception that occurred
        """
        record = NotificationRecord(query_name, "error", error)
        self._add_record(record)

    def get_all(self) -> list[NotificationRecord]:
        """Get all stored notifications.

        Returns:
            List of all notification records
        """
        return self.notifications.copy()

    def get_by_query(self, query_name: str) -> list[NotificationRecord]:
        """Get notifications for a specific query.

        Args:
            query_name: Name of the query to filter by

        Returns:
            List of notification records for the specified query
        """
        return [n for n in self.notifications if n.query_name == query_name]

    def get_by_type(self, change_type: str) -> list[NotificationRecord]:
        """Get notifications of a specific type.

        Args:
            change_type: Type of change ('added', 'updated', 'deleted', 'error')

        Returns:
            List of notification records of the specified type
        """
        return [n for n in self.notifications if n.change_type == change_type]

    def get_count(self) -> int:
        """Get total number of stored notifications.

        Returns:
            Total count of notifications
        """
        return len(self.notifications)

    def get_count_by_query(self) -> dict[str, int]:
        """Get notification count grouped by query.

        Returns:
            Dictionary mapping query names to notification counts
        """
        counts: dict[str, int] = defaultdict(int)
        for notification in self.notifications:
            counts[notification.query_name] += 1
        return dict(counts)

    def get_count_by_type(self) -> dict[str, int]:
        """Get notification count grouped by type.

        Returns:
            Dictionary mapping change types to notification counts
        """
        counts: dict[str, int] = defaultdict(int)
        for notification in self.notifications:
            counts[notification.change_type] += 1
        return dict(counts)

    def clear(self) -> None:
        """Clear all stored notifications."""
        self.notifications.clear()

    def clear_query(self, query_name: str) -> int:
        """Clear notifications for a specific query.

        Args:
            query_name: Name of the query to clear

        Returns:
            Number of notifications cleared
        """
        original_count = len(self.notifications)
        self.notifications = [
            n for n in self.notifications if n.query_name != query_name
        ]
        return original_count - len(self.notifications)
