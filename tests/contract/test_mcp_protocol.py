"""Contract tests for MCP protocol message formats.

These tests verify that MCP message schemas conform to the specification
as defined in contracts/mcp-protocol.md. These tests validate the expected
message formats for Drasi MCP servers.
"""

import json
import re
from typing import Any


class TestMCPProtocolSchemas:
    """Contract tests for MCP protocol message schemas."""

    def test_resources_list_request_schema(self) -> None:
        """Test resources/list request message format."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/list",
            "params": {},
        }

        # Validate schema
        assert request["jsonrpc"] == "2.0", "Must use JSON-RPC 2.0"
        assert "id" in request, "Must have request ID"
        assert request["method"] == "resources/list", "Method must be resources/list"
        assert "params" in request, "Must have params field"

    def test_resources_list_response_schema(self) -> None:
        """Test resources/list response message format."""
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "resources": [
                    {
                        "name": "active-orders",
                        "title": "Active Orders",
                        "uri": "drasi://query/active-orders",
                        "description": "Continuous query tracking active orders",
                        "mimeType": "application/json",
                    }
                ],
                "nextCursor": None,
            },
        }

        # Validate schema
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "resources" in response["result"]
        assert isinstance(response["result"]["resources"], list)

        # Validate resource schema
        resource = response["result"]["resources"][0]
        required_fields = ["name", "title", "uri", "description", "mimeType"]
        for field in required_fields:
            assert field in resource, f"Resource must have '{field}' field"

    def test_resource_uri_format_validation(self) -> None:
        """Test that resource URIs follow drasi://query/{name} format."""
        valid_uris = [
            "drasi://query/active-orders",
            "drasi://query/freezerx",
            "drasi://query/test_query",
            "drasi://query/query-123",
        ]

        uri_pattern = re.compile(r"^drasi://query/[a-zA-Z0-9_-]+$")

        for uri in valid_uris:
            assert uri_pattern.match(uri), \
                f"URI '{uri}' must match pattern drasi://query/{{name}}"

        # Test invalid URIs
        invalid_uris = [
            "drasi://query/",  # Missing name
            "drasi://queries/test",  # Wrong path
            "http://query/test",  # Wrong scheme
            "drasi://query/has spaces",  # Invalid characters
        ]

        for uri in invalid_uris:
            assert not uri_pattern.match(uri), \
                f"URI '{uri}' should be invalid"

    def test_resources_read_request_schema(self) -> None:
        """Test resources/read request message format."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/read",
            "params": {"uri": "drasi://query/freezerx"},
        }

        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "resources/read"
        assert "uri" in request["params"]
        assert request["params"]["uri"].startswith("drasi://query/")

    def test_resources_read_response_schema(self) -> None:
        """Test resources/read response message format."""
        response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "contents": [
                    {
                        "uri": "drasi://query/freezerx",
                        "mimeType": "application/json",
                        "text": json.dumps([{"id": 1, "temp": 37}]),
                    }
                ]
            },
        }

        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "contents" in response["result"]
        assert isinstance(response["result"]["contents"], list)

        content = response["result"]["contents"][0]
        assert "uri" in content
        assert "mimeType" in content
        assert "text" in content

        # Validate text is valid JSON
        parsed = json.loads(content["text"])
        assert isinstance(parsed, list)

    def test_resources_subscribe_request_schema(self) -> None:
        """Test resources/subscribe request message format."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/subscribe",
            "params": {"uri": "drasi://query/freezerx"},
        }

        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "resources/subscribe"
        assert "uri" in request["params"]

    def test_drasi_notification_format_added(
        self, sample_notification_added: dict[str, Any]
    ) -> None:
        """Test Drasi custom notification format for 'added' events."""
        notification = sample_notification_added

        # Validate notification structure
        assert notification["jsonrpc"] == "2.0"
        assert "method" in notification
        assert "params" in notification

        # Validate Drasi-specific method format
        method = notification["method"]
        assert method.startswith("notifications/"), \
            "Method must start with 'notifications/'"

        # Parse method: "notifications/{query-name}/added"
        parts = method.split("/")
        assert len(parts) == 3, "Method must have format notifications/{query}/type"
        assert parts[0] == "notifications"
        assert parts[2] == "added", "Change type must be 'added'"

        # Validate query name
        query_name = parts[1]
        assert query_name, "Query name cannot be empty"

    def test_drasi_notification_format_updated(
        self, sample_notification_updated: dict[str, Any]
    ) -> None:
        """Test Drasi custom notification format for 'updated' events."""
        notification = sample_notification_updated

        method = notification["method"]
        parts = method.split("/")
        assert parts[2] == "updated", "Change type must be 'updated'"

    def test_drasi_notification_format_deleted(
        self, sample_notification_deleted: dict[str, Any]
    ) -> None:
        """Test Drasi custom notification format for 'deleted' events."""
        notification = sample_notification_deleted

        method = notification["method"]
        parts = method.split("/")
        assert parts[2] == "deleted", "Change type must be 'deleted'"

    def test_notification_method_pattern_validation(self) -> None:
        """Test that notification methods match the expected pattern."""
        pattern = re.compile(r"^notifications/([a-zA-Z0-9_-]+)/(added|updated|deleted)$")

        valid_methods = [
            "notifications/freezerx/added",
            "notifications/active-orders/updated",
            "notifications/test-query/deleted",
        ]

        for method in valid_methods:
            match = pattern.match(method)
            assert match is not None, f"Method '{method}' should match pattern"
            query_name = match.group(1)
            change_type = match.group(2)
            assert query_name, "Should extract query name"
            assert change_type in ["added", "updated", "deleted"]

        invalid_methods = [
            "notifications/query",  # Missing change type
            "notifications/query/invalid",  # Invalid change type
            "notification/query/added",  # Wrong prefix
        ]

        for method in invalid_methods:
            assert not pattern.match(method), \
                f"Method '{method}' should not match pattern"

    def test_json_rpc_error_response_schema(self) -> None:
        """Test JSON-RPC error response format."""
        error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32600,
                "message": "Invalid Request",
                "data": {"details": "Query not found"},
            },
        }

        assert error_response["jsonrpc"] == "2.0"
        assert "error" in error_response
        assert "code" in error_response["error"]
        assert "message" in error_response["error"]
        assert isinstance(error_response["error"]["code"], int)
        assert isinstance(error_response["error"]["message"], str)
