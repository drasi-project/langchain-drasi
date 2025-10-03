"""Notification routing and processing for Drasi query updates.

This module handles parsing standard MCP resource update notifications with
Drasi-specific params. Drasi uses the standard MCP notifications/resources/updated
method with additional 'operation' and 'data' fields in params.
"""

import logging
from typing import Any, Protocol, runtime_checkable

from .exceptions import NotificationProcessingError
from .models import ChangeNotification, ChangeType

logger = logging.getLogger(__name__)


@runtime_checkable
class NotificationHandler(Protocol):
    """Protocol for notification handlers.

    This protocol defines the interface that notification handlers must implement.
    Handlers receive parsed notifications and can process them as needed.
    """

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Handle result added notification."""
        ...

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Handle result updated notification."""
        ...

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Handle result deleted notification."""
        ...

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Handle notification processing error."""
        ...


class NotificationRouter:
    """Routes Drasi notifications to registered handlers.

    This class parses incoming MCP notifications using Drasi's custom format
    and dispatches them to appropriate handler methods based on change type.

    The Drasi notification format is:
    - Method: "notifications/{query-name}/{change-type}"
    - Params: dict with notification payload

    Attributes:
        handlers: List of registered notification handlers
    """

    def __init__(self, handlers: list[NotificationHandler] | None = None) -> None:
        """Initialize notification router.

        Args:
            handlers: Optional list of notification handlers to register
        """
        self.handlers: list[NotificationHandler] = handlers or []

    def add_handler(self, handler: NotificationHandler) -> None:
        """Add a notification handler.

        Args:
            handler: Handler implementing NotificationHandler protocol
        """
        if handler not in self.handlers:
            self.handlers.append(handler)
            logger.debug(f"Added notification handler: {type(handler).__name__}")

    def remove_handler(self, handler: NotificationHandler) -> None:
        """Remove a notification handler.

        Args:
            handler: Handler to remove
        """
        if handler in self.handlers:
            self.handlers.remove(handler)
            logger.debug(f"Removed notification handler: {type(handler).__name__}")

    def route_notification(self, notification: ChangeNotification) -> None:
        """Route a parsed notification to appropriate handler methods."""
        logger.debug(f"Routing notification: {notification}")

        # Route to appropriate handler method based on change type
        for handler in self.handlers:
            try:
                if notification.change_type == ChangeType.ADDED:
                    handler.on_result_added(notification.query_name, notification.data)
                elif notification.change_type == ChangeType.UPDATED:
                    handler.on_result_updated(notification.query_name, notification.data)
                elif notification.change_type == ChangeType.DELETED:
                    handler.on_result_deleted(notification.query_name, notification.data)
                else:
                    logger.warning(f"Unknown change type: {notification.change_type}")

            except Exception as e:
                logger.error(
                    f"Handler {type(handler).__name__} failed processing notification: {e}"
                )
                # Notify handler of error
                try:
                    handler.on_notification_error(notification.query_name, e)
                except Exception as handler_error:
                    logger.error(
                        f"Handler error callback failed: {handler_error}"
                    )

    