"""Shared test fixtures and configuration for pytest.

This module provides fixtures used across contract, integration, and unit tests.
"""

from typing import Any

import pytest

from langchain_drasi.models import QueryInfo


@pytest.fixture
def sample_query_info() -> QueryInfo:
    """Fixture providing sample QueryInfo for testing."""
    return QueryInfo(
        name="test-query",
        title="Test Query",
        uri="drasi://query/test-query",
        description="A test query for unit testing",
        mime_type="application/json",
    )


@pytest.fixture
def sample_query_info_list() -> list[QueryInfo]:
    """Fixture providing multiple QueryInfo objects for testing."""
    return [
        QueryInfo(
            name="active-orders",
            title="Active Orders",
            uri="drasi://query/active-orders",
            description="Continuous query tracking active customer orders",
            mime_type="application/json",
        ),
        QueryInfo(
            name="freezerx",
            title="Freezer Temperature Alert",
            uri="drasi://query/freezerx",
            description="Freezer temperature alert for when it goes above 32 degrees",
            mime_type="application/json",
        ),
    ]


@pytest.fixture
def sample_notification_added() -> dict[str, Any]:
    """Fixture providing sample 'added' notification message."""
    return {
        "jsonrpc": "2.0",
        "method": "notifications/freezerx/added",
        "params": {
            "freezerId": "2",
            "temperature": "35",
            "description": "Temperature of freezer 2 exceeded threshold",
        },
    }


@pytest.fixture
def sample_notification_updated() -> dict[str, Any]:
    """Fixture providing sample 'updated' notification message."""
    return {
        "jsonrpc": "2.0",
        "method": "notifications/active-orders/updated",
        "params": {
            "orderId": "12345",
            "status": "shipped",
            "updatedAt": "2025-10-01T12:00:00Z",
        },
    }


@pytest.fixture
def sample_notification_deleted() -> dict[str, Any]:
    """Fixture providing sample 'deleted' notification message."""
    return {
        "jsonrpc": "2.0",
        "method": "notifications/test-query/deleted",
        "params": {
            "id": "999",
            "reason": "expired",
        },
    }


class MockNotificationHandler:
    """Mock notification handler for testing.

    Tracks all calls for assertion in tests.
    """

    def __init__(self) -> None:
        """Initialize the mock handler."""
        self.added_calls: list[tuple[str, dict[str, Any]]] = []
        self.updated_calls: list[tuple[str, dict[str, Any]]] = []
        self.deleted_calls: list[tuple[str, dict[str, Any]]] = []
        self.error_calls: list[tuple[str, Exception]] = []

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        """Track added notifications."""
        self.added_calls.append((query_name, added_data))

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        """Track updated notifications."""
        self.updated_calls.append((query_name, updated_data))

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        """Track deleted notifications."""
        self.deleted_calls.append((query_name, deleted_data))

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Track notification errors."""
        self.error_calls.append((query_name, error))

    def reset(self) -> None:
        """Reset all tracked calls."""
        self.added_calls.clear()
        self.updated_calls.clear()
        self.deleted_calls.clear()
        self.error_calls.clear()


@pytest.fixture
def mock_handler() -> MockNotificationHandler:
    """Fixture providing a mock notification handler."""
    return MockNotificationHandler()


@pytest.fixture
def sample_query_result() -> dict[str, Any]:
    """Fixture providing sample query result data."""
    return {
        "query_name": "freezerx",
        "uri": "drasi://query/freezerx",
        "mime_type": "application/json",
        "content": [
            {"id": 1, "temp": 37},
            {"id": 3, "temp": 41},
        ],
        "timestamp": "2025-10-01T12:00:00Z",
    }
