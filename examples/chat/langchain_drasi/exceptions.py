"""Exception hierarchy for the LangChain-Drasi library.

This module defines all custom exceptions used throughout the library,
providing clear error handling and debugging information.
"""

from typing import Any


class DrasiError(Exception):
    """Base exception for all Drasi-related errors.

    All exceptions raised by this library inherit from this base class,
    making it easy to catch all library-specific errors.

    Args:
        message: Human-readable error description
        details: Optional additional context about the error
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the DrasiError with message and optional details."""
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class MCPConnectionError(DrasiError):
    """Raised when MCP server connection fails or is lost.

    This exception indicates issues with establishing or maintaining
    a connection to the MCP server.

    Examples:
        - Server not reachable
        - Connection timeout
        - Authentication failure
        - Connection dropped unexpectedly
    """



class QueryNotFoundError(DrasiError):
    """Raised when attempting to access a non-existent query.

    This exception is raised when a query name doesn't match any
    available Drasi queries on the MCP server.

    Args:
        query_name: The name of the query that wasn't found
        available_queries: Optional list of available query names
    """

    def __init__(
        self,
        query_name: str,
        available_queries: list[str] | None = None,
    ) -> None:
        """Initialize QueryNotFoundError with query details."""
        message = f"Query '{query_name}' not found"
        details: dict[str, Any] = {"query_name": query_name}
        if available_queries:
            details["available_queries"] = available_queries  # type: ignore[assignment]
        super().__init__(message, details)
        self.query_name = query_name
        self.available_queries = available_queries


class SubscriptionError(DrasiError):
    """Raised when subscription operations fail.

    This exception covers failures in subscribing to or unsubscribing
    from query change notifications.

    Examples:
        - Subscription request rejected by server
        - Unsubscribe from non-subscribed query
        - Subscription limit exceeded
        - Subscription state corruption
    """



class NotificationProcessingError(DrasiError):
    """Raised when notification processing encounters errors.

    This exception indicates failures in parsing, routing, or processing
    notifications from the MCP server. Note that callback handler errors
    are logged but not raised as NotificationProcessingError per FR-018.

    Examples:
        - Invalid notification format
        - Missing required notification fields
        - Notification routing failure
        - Critical processing errors (non-callback)
    """

