"""Logging notification handler.

This handler logs all notifications using Python's logging framework.
Useful for debugging and monitoring query updates.
"""

import logging
from typing import Any

from ..callbacks import BaseDrasiNotificationHandler


class LoggingHandler(BaseDrasiNotificationHandler):
    """Notification handler that logs all events using Python logging.

    This handler logs notifications at different levels:
    - Added/Updated/Deleted events: INFO level
    - Errors: ERROR level

    Example:
        ```python
        from langchain_drasi import create_drasi_tool, MCPConnectionConfig
        from langchain_drasi.handlers import LoggingHandler

        # Create handler with custom logger
        handler = LoggingHandler(logger_name="drasi.queries")

        # Create tool with handler
        config = MCPConnectionConfig(
            server_command="npx",
            server_args=["-y", "@drasi/query-api"]
        )
        tool = create_drasi_tool(mcp_config=config, notification_handlers=[handler])
        ```

    Attributes:
        logger: Logger instance for this handler
        log_level: Log level for notification events
    """

    def __init__(
        self,
        logger_name: str = "langchain_drasi.notifications",
        log_level: int = logging.INFO,
    ) -> None:
        """Initialize logging handler.

        Args:
            logger_name: Name of the logger to use
            log_level: Log level for notification events (default: INFO)
        """
        super().__init__()
        self.logger = logging.getLogger(logger_name)
        self.log_level = log_level

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Log result added notification.

        Args:
            query_name: Name of the query
            added_data: Added result data
        """
        self.logger.log(
            self.log_level,
            f"[{query_name}] Result ADDED: {added_data}",
        )

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Log result updated notification.

        Args:
            query_name: Name of the query
            updated_data: Updated result data
        """
        self.logger.log(
            self.log_level,
            f"[{query_name}] Result UPDATED: {updated_data}",
        )

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Log result deleted notification.

        Args:
            query_name: Name of the query
            deleted_data: Deleted result data
        """
        self.logger.log(
            self.log_level,
            f"[{query_name}] Result DELETED: {deleted_data}",
        )

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Log notification error.

        Args:
            query_name: Name of the query
            error: The exception that occurred
        """
        self.logger.error(
            f"[{query_name}] Notification ERROR: {error}",
            exc_info=error,
        )
