"""Data models for the LangChain-Drasi library.

This module defines TypedDicts and Enums for structured data used throughout
the library, providing type safety and clear data contracts.
"""

from enum import Enum
from typing import Any, TypedDict


class ChangeType(Enum):
    """Types of changes that can occur in query results.

    These values correspond to the notification methods emitted by the
    Drasi MCP server when query result sets change.
    """

    ADDED = "added"
    UPDATED = "updated"
    DELETED = "deleted"


class QueryInfo(TypedDict):
    """Information about an available Drasi query.

    This represents metadata about a query exposed by the MCP server,
    used for query discovery and selection.

    Attributes:
        name: Unique identifier for the query
        title: Human-readable display title
        uri: MCP resource URI in format "drasi://query/{name}"
        description: Purpose and nature of the query
        mime_type: Content MIME type, typically "application/json"
    """

    name: str
    title: str
    uri: str
    description: str
    mime_type: str


class QueryResult(TypedDict):
    """Result set from reading a Drasi query.

    This represents the current state of a query's result set at a
    point in time. Results are always fetched fresh from the MCP
    server (no local caching per FR-020).

    Attributes:
        query_name: Name of the query this result belongs to
        uri: Resource URI of the query
        mime_type: Content MIME type
        content: JSON array of result rows (list of dictionaries)
        timestamp: Optional timestamp of when result was fetched
    """

    query_name: str
    uri: str
    mime_type: str
    content: list[dict[str, Any]]
    timestamp: str | None


class ChangeNotification:
    """Notification of a change to a query result set.

    This represents a notification message received from the MCP server
    when a subscribed query's result set changes.
    
    Attributes:
        change_type: Type of change (added, updated, or deleted)
        query_name: Name of the query that changed
        data: The actual change data payload"""

    change_type: ChangeType
    query_name: str    
    data: dict[str, Any]