"""Callback handler protocols and base implementations.

This module provides Protocol definitions and base classes for handling
Drasi query result notifications. Users can implement these protocols
or extend the base classes to handle notifications from subscribed queries.
"""

import logging
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class DrasiNotificationHandler(Protocol):
    """Protocol for synchronous Drasi notification handlers.

    This protocol defines the interface for handling notifications from
    Drasi continuous queries. Implement this protocol to create custom
    notification handlers.

    All methods receive the query name and notification data. The query
    name identifies which query triggered the notification.
    """

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Called when a new result is added to a query.

        Args:
            query_name: Name of the query that triggered the notification
            added_data: Data for the newly added result
        """
        ...

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Called when a result is updated in a query.

        Args:
            query_name: Name of the query that triggered the notification
            updated_data: Updated data for the result
        """
        ...

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Called when a result is deleted from a query.

        Args:
            query_name: Name of the query that triggered the notification
            deleted_data: Data for the deleted result (typically includes ID)
        """
        ...

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Called when an error occurs processing a notification.

        Args:
            query_name: Name of the query that triggered the error
            error: The exception that occurred
        """
        ...


@runtime_checkable
class AsyncDrasiNotificationHandler(Protocol):
    """Protocol for asynchronous Drasi notification handlers.

    This protocol defines the async interface for handling notifications
    from Drasi continuous queries. Use this for handlers that need to
    perform async operations (e.g., database writes, API calls).

    All methods receive the query name and notification data. The query
    name identifies which query triggered the notification.
    """

    async def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Called when a new result is added to a query.

        Args:
            query_name: Name of the query that triggered the notification
            added_data: Data for the newly added result
        """
        ...

    async def on_result_updated(
        self, query_name: str, updated_data: dict[str, Any]
    ) -> None:
        """Called when a result is updated in a query.

        Args:
            query_name: Name of the query that triggered the notification
            updated_data: Updated data for the result
        """
        ...

    async def on_result_deleted(
        self, query_name: str, deleted_data: dict[str, Any]
    ) -> None:
        """Called when a result is deleted from a query.

        Args:
            query_name: Name of the query that triggered the notification
            deleted_data: Data for the deleted result (typically includes ID)
        """
        ...

    async def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Called when an error occurs processing a notification.

        Args:
            query_name: Name of the query that triggered the error
            error: The exception that occurred
        """
        ...


class BaseDrasiNotificationHandler:
    """Base class for synchronous Drasi notification handlers.

    This class provides a default implementation of DrasiNotificationHandler
    with no-op methods. Extend this class and override methods you want to
    handle.

    Example:
        ```python
        class MyHandler(BaseDrasiNotificationHandler):
            def on_result_added(self, query_name: str, added_data: dict) -> None:
                print(f"New result in {query_name}: {added_data}")
        ```
    """

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Handle result added notification.

        Default implementation logs the notification. Override to customize.

        Args:
            query_name: Name of the query that triggered the notification
            added_data: Data for the newly added result
        """
        logger.debug(f"Result added to {query_name}: {added_data}")

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Handle result updated notification.

        Default implementation logs the notification. Override to customize.

        Args:
            query_name: Name of the query that triggered the notification
            updated_data: Updated data for the result
        """
        logger.debug(f"Result updated in {query_name}: {updated_data}")

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Handle result deleted notification.

        Default implementation logs the notification. Override to customize.

        Args:
            query_name: Name of the query that triggered the notification
            deleted_data: Data for the deleted result
        """
        logger.debug(f"Result deleted from {query_name}: {deleted_data}")

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Handle notification processing error.

        Default implementation logs the error. Override to customize.

        Args:
            query_name: Name of the query that triggered the error
            error: The exception that occurred
        """
        logger.error(f"Error processing notification from {query_name}: {error}")


class AsyncBaseDrasiNotificationHandler:
    """Base class for asynchronous Drasi notification handlers.

    This class provides a default async implementation of
    AsyncDrasiNotificationHandler with no-op methods. Extend this class
    and override methods you want to handle.

    Example:
        ```python
        class MyAsyncHandler(AsyncBaseDrasiNotificationHandler):
            async def on_result_added(self, query_name: str, added_data: dict) -> None:
                await self.save_to_database(query_name, added_data)
        ```
    """

    async def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Handle result added notification.

        Default implementation logs the notification. Override to customize.

        Args:
            query_name: Name of the query that triggered the notification
            added_data: Data for the newly added result
        """
        logger.debug(f"Result added to {query_name}: {added_data}")

    async def on_result_updated(
        self, query_name: str, updated_data: dict[str, Any]
    ) -> None:
        """Handle result updated notification.

        Default implementation logs the notification. Override to customize.

        Args:
            query_name: Name of the query that triggered the notification
            updated_data: Updated data for the result
        """
        logger.debug(f"Result updated in {query_name}: {updated_data}")

    async def on_result_deleted(
        self, query_name: str, deleted_data: dict[str, Any]
    ) -> None:
        """Handle result deleted notification.

        Default implementation logs the notification. Override to customize.

        Args:
            query_name: Name of the query that triggered the notification
            deleted_data: Data for the deleted result
        """
        logger.debug(f"Result deleted from {query_name}: {deleted_data}")

    async def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Handle notification processing error.

        Default implementation logs the error. Override to customize.

        Args:
            query_name: Name of the query that triggered the error
            error: The exception that occurred
        """
        logger.error(f"Error processing notification from {query_name}: {error}")
