"""Console notification handler.

This handler prints notifications to the console (stdout).
Useful for demos and development.
"""

from datetime import datetime
from typing import Any

from ..callbacks import BaseDrasiNotificationHandler


class ConsoleHandler(BaseDrasiNotificationHandler):
    """Notification handler that prints events to console.

    This handler prints formatted notifications to stdout, making it
    easy to see query updates in real-time during development or demos.

    Example:
        ```python
        from langchain_drasi import create_drasi_tool, MCPConnectionConfig
        from langchain_drasi.handlers import ConsoleHandler

        # Create handler with custom formatting
        handler = ConsoleHandler(
            include_timestamp=True,
            pretty_print=True
        )

        # Create tool with handler
        config = MCPConnectionConfig(
            server_command="npx",
            server_args=["-y", "@drasi/query-api"]
        )
        tool = create_drasi_tool(mcp_config=config, notification_handlers=[handler])
        ```

    Attributes:
        include_timestamp: Whether to include timestamp in output
        pretty_print: Whether to pretty-print data (multiline)
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        pretty_print: bool = False,
    ) -> None:
        """Initialize console handler.

        Args:
            include_timestamp: Include timestamp in output (default: True)
            pretty_print: Pretty-print data structures (default: False)
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.pretty_print = pretty_print

    def _format_message(
        self,
        query_name: str,
        change_type: str,
        data: dict[str, Any],
    ) -> str:
        """Format notification message for console output.

        Args:
            query_name: Name of the query
            change_type: Type of change (ADDED/UPDATED/DELETED)
            data: Notification data

        Returns:
            Formatted message string
        """
        timestamp = ""
        if self.include_timestamp:
            timestamp = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "

        if self.pretty_print:
            import json
            data_str = json.dumps(data, indent=2)
            return f"{timestamp}[{query_name}] {change_type}:\n{data_str}"
        return f"{timestamp}[{query_name}] {change_type}: {data}"

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Print result added notification.

        Args:
            query_name: Name of the query
            added_data: Added result data
        """
        message = self._format_message(query_name, "ADDED", added_data)
        print(message)

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Print result updated notification.

        Args:
            query_name: Name of the query
            updated_data: Updated result data
        """
        message = self._format_message(query_name, "UPDATED", updated_data)
        print(message)

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Print result deleted notification.

        Args:
            query_name: Name of the query
            deleted_data: Deleted result data
        """
        message = self._format_message(query_name, "DELETED", deleted_data)
        print(message)

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Print notification error.

        Args:
            query_name: Name of the query
            error: The exception that occurred
        """
        timestamp = ""
        if self.include_timestamp:
            timestamp = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "

        print(f"{timestamp}[{query_name}] ERROR: {error}")
