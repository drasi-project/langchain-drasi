"""End-to-end integration tests.

These tests verify complete workflows from discovery through subscription
and notification handling. They test the entire system working together.
"""
# pyright: reportPossiblyUnboundVariable=false, reportOptionalMemberAccess=false, reportCallIssue=false, reportInvalidTypeForm=false, reportGeneralTypeIssues=false

import asyncio
from typing import Any

import pytest

# These imports will fail until modules are implemented
try:
    from langchain_drasi.callbacks import BaseDrasiNotificationHandler
    from langchain_drasi.config import MCPConnectionConfig
    from langchain_drasi.models import ChangeType
    from langchain_drasi.tool import DrasiTool, create_drasi_tool
    IMPORTS_AVAILABLE = True
except ImportError:
    BaseDrasiNotificationHandler = object  # type: ignore[misc,assignment]
    MCPConnectionConfig = object  # type: ignore[misc,assignment]
    ChangeType = object  # type: ignore[misc,assignment]
    DrasiTool = object  # type: ignore[misc,assignment]
    create_drasi_tool = lambda *args, **kwargs: None  # type: ignore[misc,assignment]
    IMPORTS_AVAILABLE = False


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Implementation not complete")
@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end tests for complete workflows."""

    @pytest.fixture
    def mcp_config(self) -> "MCPConnectionConfig":
        """Fixture providing MCP connection config for testing."""
        return MCPConnectionConfig(
            server_url="http://localhost:8080/mcp",
        )

    @pytest.mark.asyncio
    async def test_complete_discovery_read_workflow(
        self, mcp_config: "MCPConnectionConfig", mock_mcp_transport
    ) -> None:
        """Test complete workflow: discover queries → read query results."""
        tool = create_drasi_tool(mcp_config=mcp_config)

        # Step 1: Discover available queries
        queries = await tool.discover_queries()
        assert isinstance(queries, list), "Should return list of queries"
        assert len(queries) > 0, "Should find at least one query"

        # Verify query structure
        first_query = queries[0]
        assert "name" in first_query
        assert "uri" in first_query
        query_name = first_query["name"]

        # Step 2: Read query results
        result = await tool.read_query(query_name)
        assert result is not None, "Should return query results"
        assert "content" in result, "Result should have content"
        assert "query_name" in result
        assert result["query_name"] == query_name

    @pytest.mark.asyncio
    async def test_complete_subscribe_notify_workflow(
        self, mcp_config: "MCPConnectionConfig", mock_mcp_transport
    ) -> None:
        """Test complete workflow: subscribe → receive notification → callback invoked."""

        # Create a test handler to track notifications
        class TestHandler(BaseDrasiNotificationHandler):
            def __init__(self) -> None:
                self.notifications: list[tuple[str, str, dict[str, Any]]] = []

            def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
                self.notifications.append(("added", query_name, added_data))

            def on_result_updated(
                self, query_name: str, updated_data: dict[str, Any]
            ) -> None:
                self.notifications.append(("updated", query_name, updated_data))

            def on_result_deleted(
                self, query_name: str, deleted_data: dict[str, Any]
            ) -> None:
                self.notifications.append(("deleted", query_name, deleted_data))

        handler = TestHandler()
        tool = create_drasi_tool(mcp_config=mcp_config, notification_handlers=[handler])

        # Step 1: Subscribe to a query
        query_name = "test-query"
        await tool.subscribe(query_name)

        # Step 2: Wait for notification (mock server should send one)
        # Give some time for notification to be received and processed
        await asyncio.sleep(0.5)

        # Step 3: Verify callback was invoked
        assert len(handler.notifications) > 0, "Handler should receive notifications"
        change_type, notified_query, data = handler.notifications[0]
        assert notified_query == query_name, "Notification should be for subscribed query"
        assert change_type in ["added", "updated", "deleted"]
        assert isinstance(data, dict), "Notification data should be a dict"

    @pytest.mark.asyncio
    async def test_multiple_subscriptions_workflow(
        self, mcp_config: "MCPConnectionConfig", mock_mcp_transport
    ) -> None:
        """Test workflow with multiple query subscriptions."""

        class MultiQueryHandler(BaseDrasiNotificationHandler):
            def __init__(self) -> None:
                self.queries_notified: set[str] = set()

            def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
                self.queries_notified.add(query_name)

            def on_result_updated(
                self, query_name: str, updated_data: dict[str, Any]
            ) -> None:
                self.queries_notified.add(query_name)

        handler = MultiQueryHandler()
        tool = create_drasi_tool(mcp_config=mcp_config, notification_handlers=[handler])

        # Subscribe to multiple queries
        queries = ["query-1", "query-2", "query-3"]
        for query in queries:
            await tool.subscribe(query)

        # Wait for notifications
        await asyncio.sleep(1.0)

        # Verify we received notifications from multiple queries
        assert len(handler.queries_notified) > 0, "Should receive notifications"

    @pytest.mark.asyncio
    async def test_unsubscribe_workflow(
        self, mcp_config: "MCPConnectionConfig", mock_mcp_transport
    ) -> None:
        """Test workflow: subscribe → unsubscribe → verify no more notifications."""

        class CountingHandler(BaseDrasiNotificationHandler):
            def __init__(self) -> None:
                self.count = 0

            def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
                self.count += 1

        handler = CountingHandler()
        tool = create_drasi_tool(mcp_config=mcp_config, notification_handlers=[handler])

        query_name = "test-query"

        # Subscribe
        await tool.subscribe(query_name)
        await asyncio.sleep(0.5)
        count_after_subscribe = handler.count

        # Unsubscribe
        await tool.unsubscribe(query_name)
        await asyncio.sleep(0.5)
        count_after_unsubscribe = handler.count

        # After unsubscribe, count should not increase significantly
        # (allowing for in-flight notifications)
        assert count_after_unsubscribe <= count_after_subscribe + 1, \
            "Should stop receiving notifications after unsubscribe"

    @pytest.mark.asyncio
    async def test_error_handling_workflow(
        self, mcp_config: "MCPConnectionConfig", mock_mcp_transport
    ) -> None:
        """Test workflow with error conditions."""

        class ErrorTrackingHandler(BaseDrasiNotificationHandler):
            def __init__(self) -> None:
                self.errors: list[tuple[str, Exception]] = []

            def on_notification_error(
                self, query_name: str, error: Exception
            ) -> None:
                self.errors.append((query_name, error))

        handler = ErrorTrackingHandler()
        tool = create_drasi_tool(mcp_config=mcp_config, notification_handlers=[handler])

        # Try to read non-existent query
        from langchain_drasi.exceptions import QueryNotFoundError

        with pytest.raises(QueryNotFoundError):
            await tool.read_query("nonexistent-query")

        # Try to subscribe to invalid query
        from langchain_drasi.exceptions import SubscriptionError

        with pytest.raises((SubscriptionError, QueryNotFoundError)):
            await tool.subscribe("invalid-query-name")

    @pytest.mark.asyncio
    async def test_full_agent_workflow(
        self, mcp_config: "MCPConnectionConfig", mock_mcp_transport
    ) -> None:
        """Test complete agent workflow using DrasiTool."""
        tool = create_drasi_tool(mcp_config=mcp_config)

        # Simulate agent decision-making process

        # 1. Agent discovers what queries are available
        result = await tool.ainvoke(
            {"query_name": "", "operation": "discover"}
        )
        assert result is not None, "Discovery should return results"

        # 2. Agent reads specific query
        result = await tool.ainvoke(
            {"query_name": "test-query", "operation": "read"}
        )
        assert result is not None, "Read should return results"

        # 3. Agent subscribes to query for updates
        result = await tool.ainvoke(
            {"query_name": "test-query", "operation": "subscribe"}
        )
        assert result is not None, "Subscribe should confirm subscription"

        # 4. Later, agent unsubscribes
        result = await tool.ainvoke(
            {"query_name": "test-query", "operation": "unsubscribe"}
        )
        assert result is not None, "Unsubscribe should confirm unsubscription"


# If imports failed, create a failing test
if not IMPORTS_AVAILABLE:
    def test_end_to_end_not_implemented() -> None:
        """Fail to indicate end-to-end implementation is needed."""
        pytest.fail(
            "End-to-end workflow not ready yet. "
            "This test will pass once all components are implemented."
        )
