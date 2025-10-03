"""Shared test fixtures and configuration for pytest.

This module provides fixtures used across contract, integration, and unit tests.
"""

import asyncio
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import ResourceUpdatedNotification
from mcp.types import ResourceUpdatedNotificationParams, TextResourceContents
from pydantic import AnyUrl

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


class MockMCPServer:
    """Mock MCP server for integration testing.

    Simulates MCP server responses without requiring a real server.
    """

    def __init__(self) -> None:
        """Initialize mock MCP server with sample data."""
        # Mock resources available on the server
        resource1 = MagicMock()
        resource1.name = "test-query"
        resource1.uri = AnyUrl("drasi://query/test-query")
        resource1.description = "Test query for testing"
        resource1.mimeType = "application/json"

        resource2 = MagicMock()
        resource2.name = "freezerx"
        resource2.uri = AnyUrl("drasi://query/freezerx")
        resource2.description = "Freezer temperature alerts"
        resource2.mimeType = "application/json"

        self.resources = [resource1, resource2]

        # Mock query results
        self.query_results = {
            "drasi://query/test-query": [
                {"id": "1", "name": "Test Item 1"},
                {"id": "2", "name": "Test Item 2"},
            ],
            "drasi://query/freezerx": [
                {"freezerId": "1", "temperature": 35},
                {"freezerId": "2", "temperature": 38},
            ],
            "drasi://query/query-1": [
                {"id": "1", "status": "active"},
            ],
            "drasi://query/query-2": [
                {"id": "2", "status": "processing"},
            ],
            "drasi://query/query-3": [
                {"id": "3", "status": "pending"},
            ],
        }

        # Track subscriptions
        self.subscriptions: set[str] = set()

        # Store notification callback
        self.notification_callback: Callable | None = None

        # Sample notifications to send
        self.sample_notifications = {
            "drasi://query/test-query": {
                "operation": "added",
                "data": {"id": "3", "name": "New Test Item", "timestamp": "2025-10-03T10:00:00Z"}
            },
            "drasi://query/freezerx": {
                "operation": "updated",
                "data": {"freezerId": "1", "temperature": 40, "alert": True}
            },
            "drasi://query/query-1": {
                "operation": "added",
                "data": {"id": "1", "status": "active"}
            },
            "drasi://query/query-2": {
                "operation": "updated",
                "data": {"id": "2", "status": "processing"}
            },
            "drasi://query/query-3": {
                "operation": "added",
                "data": {"id": "3", "status": "new"}
            },
        }

    async def list_resources(self) -> MagicMock:
        """Mock list_resources response."""
        response = MagicMock()
        response.resources = self.resources
        return response

    async def read_resource(self, uri: AnyUrl | str) -> MagicMock:
        """Mock read_resource response."""
        uri_str = str(uri)

        # Check if query exists
        if uri_str not in self.query_results:
            # Return empty contents to simulate "not found"
            response = MagicMock()
            response.contents = []
            return response

        content_data = self.query_results[uri_str]

        # Create TextResourceContents
        import json
        content_item = TextResourceContents(
            text=json.dumps(content_data),
            uri=AnyUrl(str(uri)),
            mimeType="application/json",
        )

        response = MagicMock()
        response.contents = [content_item]
        return response

    async def subscribe_resource(self, uri: AnyUrl | str) -> None:
        """Mock subscribe_resource."""
        uri_str = str(uri)

        # Validate that the query exists (similar to real server behavior)
        if uri_str not in self.query_results:
            # MCP servers would return an error, which would cause the client to raise an exception
            raise ValueError(f"Query not found: {uri_str}")

        self.subscriptions.add(uri_str)

        # Simulate sending a notification after subscription
        if self.notification_callback and uri_str in self.sample_notifications:
            asyncio.create_task(self._send_notification(uri_str))

    async def unsubscribe_resource(self, uri: AnyUrl | str) -> None:
        """Mock unsubscribe_resource."""
        self.subscriptions.discard(str(uri))

    async def _send_notification(self, uri: str) -> None:
        """Send a mock notification for the subscribed resource."""
        await asyncio.sleep(0.1)  # Small delay to simulate async notification

        if not self.notification_callback:
            return

        notification_data = self.sample_notifications.get(uri)
        if not notification_data:
            return

        # Create ResourceUpdatedNotification with Drasi-specific params
        params = MagicMock(spec=ResourceUpdatedNotificationParams)
        params.uri = AnyUrl(uri)
        params.model_extra = notification_data

        notification = ResourceUpdatedNotification(params=params)

        # Call the notification callback
        if hasattr(self.notification_callback, '_received_notification'):
            await self.notification_callback._received_notification(notification)  # type: ignore[attr-defined]

    async def initialize(self) -> MagicMock:
        """Mock initialize response."""
        response = MagicMock()
        response.serverInfo = MagicMock(
            name="Mock Drasi MCP Server",
            version="1.0.0"
        )
        return response


@pytest.fixture
async def mock_mcp_server() -> MockMCPServer:
    """Fixture providing a mock MCP server for integration tests."""
    return MockMCPServer()


@pytest.fixture
def mock_mcp_session(mock_mcp_server: MockMCPServer) -> MagicMock:
    """Fixture that patches MCP client session with mock server.

    Use this fixture to automatically mock MCP connections in tests.
    """
    # Use a real MagicMock instance with custom methods
    mock_session = MagicMock()
    mock_session.list_resources = mock_mcp_server.list_resources
    mock_session.read_resource = mock_mcp_server.read_resource
    mock_session.subscribe_resource = mock_mcp_server.subscribe_resource
    mock_session.unsubscribe_resource = mock_mcp_server.unsubscribe_resource
    mock_session.initialize = mock_mcp_server.initialize

    # Store reference to mock server so we can set the callback later
    mock_session._mock_server = mock_mcp_server

    # Store notification callback reference
    mock_session._notification_callback = None

    # Add _received_notification method that will be called by the mock server
    async def _received_notification(notification):
        # This simulates the DrasiClientSession._received_notification method
        # which calls the drasi_notification_callback
        if mock_session._notification_callback:
            from langchain_drasi.models import ChangeNotification, ChangeType

            # Extract params from notification
            params = notification.params if hasattr(notification, 'params') else None
            if params and hasattr(params, 'model_extra'):
                model_extra = params.model_extra
                uri_path = params.uri.path if hasattr(params.uri, 'path') else str(params.uri)

                change_notification = ChangeNotification()
                operation = model_extra.get("operation")
                if operation:
                    change_notification.change_type = ChangeType(operation)
                change_notification.query_name = uri_path.lstrip("/").split("/")[-1]
                change_notification.data = model_extra.get("data", {})

                # Call the notification callback
                mock_session._notification_callback(change_notification)

    mock_session._received_notification = _received_notification

    # Make it work as async context manager
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    return mock_session


@pytest.fixture
def mock_mcp_transport(mock_mcp_session: MagicMock):
    """Fixture that patches the MCP HTTP transport to use mock session."""
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(
        return_value=(
            MagicMock(),  # read_stream
            MagicMock(),  # write_stream
            lambda: "test-session-id",  # get_session_id
        )
    )
    mock_context.__aexit__ = AsyncMock(return_value=None)

    # Create a wrapper for DrasiClientSession that captures the notification callback
    def create_session_wrapper(read_stream, write_stream, drasi_notification_callback=None):
        # Store the notification callback in the mock session
        mock_mcp_session._notification_callback = drasi_notification_callback

        # Store the mock session in the mock server so it can send notifications
        if hasattr(mock_mcp_session, '_mock_server'):
            mock_mcp_session._mock_server.notification_callback = mock_mcp_session

        # Return the mock session
        return mock_mcp_session

    with patch('langchain_drasi.client.streamablehttp_client', return_value=mock_context), \
         patch('langchain_drasi.client.DrasiClientSession', side_effect=create_session_wrapper):
        yield mock_mcp_session
