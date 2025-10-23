"""Utility functions for langchain-drasi.

This module provides helper functions for URI construction, validation,
and other common operations.
"""

import re

# Drasi URI pattern: drasi://query/{query-name}
DRASI_URI_PATTERN = re.compile(r"^drasi://query/([a-zA-Z0-9_-]+)$")


def build_query_uri(query_name: str) -> str:
    """Build a Drasi query URI from a query name.

    Args:
        query_name: Name of the query

    Returns:
        Full Drasi URI in format: drasi://query/{query-name}

    Example:
        >>> build_query_uri("active-orders")
        'drasi://query/active-orders'
    """
    # Validate query name format
    if not re.match(r"^[a-zA-Z0-9_-]+$", query_name):
        raise ValueError(
            f"Invalid query name: {query_name}. "
            "Query names must contain only alphanumeric characters, hyphens, and underscores."
        )

    return f"drasi://query/{query_name}"


def parse_query_uri(uri: str) -> str | None:
    """Parse a Drasi query URI to extract the query name.

    Args:
        uri: Drasi URI in format: drasi://query/{query-name}

    Returns:
        Query name if URI is valid, None otherwise

    Example:
        >>> parse_query_uri("drasi://query/active-orders")
        'active-orders'
        >>> parse_query_uri("invalid://uri")
        None
    """
    match = DRASI_URI_PATTERN.match(uri)
    if match:
        return match.group(1)
    return None


def validate_query_uri(uri: str) -> bool:
    """Validate that a URI follows the Drasi query URI format.

    Args:
        uri: URI to validate

    Returns:
        True if URI is valid Drasi query URI, False otherwise

    Example:
        >>> validate_query_uri("drasi://query/test-query")
        True
        >>> validate_query_uri("http://example.com")
        False
    """
    return DRASI_URI_PATTERN.match(uri) is not None


def extract_query_name_from_notification_method(method: str) -> str | None:
    """Extract query name from a Drasi notification method string.

    Drasi notification methods follow the format:
    'notifications/{query-name}/{change-type}'

    Args:
        method: Notification method string

    Returns:
        Query name if method is valid, None otherwise

    Example:
        >>> extract_query_name_from_notification_method("notifications/freezerx/added")
        'freezerx'
        >>> extract_query_name_from_notification_method("invalid-format")
        None
    """
    # Pattern: notifications/{query-name}/{added|updated|deleted}
    pattern = re.compile(r"^notifications/([a-zA-Z0-9_-]+)/(added|updated|deleted)$")
    match = pattern.match(method)
    if match:
        return match.group(1)
    return None


def format_query_result_summary(query_name: str, result_count: int) -> str:
    """Format a human-readable summary of query results.

    Args:
        query_name: Name of the query
        result_count: Number of results returned

    Returns:
        Formatted summary string

    Example:
        >>> format_query_result_summary("active-orders", 5)
        "Query 'active-orders' returned 5 result(s)"
    """
    return f"Query '{query_name}' returned {result_count} result(s)"
