"""LangChain tool for Drasi continuous query integration.

This module provides a LangChain BaseTool implementation that allows AI agents
to discover, read, and subscribe to Drasi continuous queries via MCP.
"""

import logging
from enum import Enum
from typing import Any, Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from .callbacks import DrasiNotificationHandler
from .client import MCPClient
from .config import MCPConnectionConfig
from .exceptions import SubscriptionError
from .models import ChangeNotification, QueryInfo, QueryResult
from .notifications import NotificationRouter

logger = logging.getLogger(__name__)


class DrasiOperation(str, Enum):
    """Supported operations for DrasiTool."""

    DISCOVER = "discover"
    READ = "read"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


class DrasiQueryInput(BaseModel):
    """Input schema for DrasiTool.

    This schema defines the parameters that can be passed to the tool
    when invoked by an AI agent.
    """

    query_name: str = Field(
        default="",
        description=(
            "Name of the Drasi query to operate on. "
            "Leave empty for 'discover' operation to list all queries."
        ),
    )

    operation: DrasiOperation = Field(
        default=DrasiOperation.READ,
        description=(
            "Operation to perform: "
            "'discover' lists all available queries, "
            "'read' retrieves current query results, "
            "'subscribe' starts receiving real-time updates, "
            "'unsubscribe' stops receiving updates."
        ),
    )


class DrasiTool(BaseTool):
    """LangChain tool for interacting with Drasi continuous queries.

    This tool enables AI agents to:
    - Discover available Drasi queries
    - Read current query results
    - Subscribe to real-time query updates
    - Unsubscribe from queries

    The tool communicates with a Drasi MCP server and routes notifications
    to registered handlers.

    Example:
        ```python
        from langchain_drasi import create_drasi_tool, MCPConnectionConfig

        config = MCPConnectionConfig(
            server_url="https://your-drasi-server.com/api",
            headers={"Authorization": "Bearer your-token"},
            timeout=30.0
        )

        tool = create_drasi_tool(mcp_config=config)

        # Agent can now use the tool
        result = await tool.ainvoke({
            "query_name": "active-orders",
            "operation": "read"
        })
        ```

    Attributes:
        name: Tool name for LangChain
        description: Tool description for LLM
        args_schema: Pydantic schema for tool inputs
        mcp_config: MCP connection configuration
        notification_handlers: List of notification handlers
    """

    name: str = "drasi_query"
    description: str = (
        "Access Drasi continuous queries to get real-time data insights. "
        "Use 'discover' to list available queries, 'read' to get current results, "
        "'subscribe' to receive real-time updates, or 'unsubscribe' to stop updates."
    )
    args_schema: type[BaseModel] = DrasiQueryInput  # type: ignore[assignment]

    # Custom attributes (using Any to avoid Pydantic validation issues with Protocol types)
    mcp_config: MCPConnectionConfig
    notification_handlers: list[Any] = Field(default_factory=list)

    # Internal state
    _client: MCPClient
    _router: NotificationRouter

    def __init__(
        self,
        mcp_config: MCPConnectionConfig,
        notification_handlers: list[DrasiNotificationHandler] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize DrasiTool.

        Args:
            mcp_config: MCP connection configuration
            notification_handlers: Optional list of notification handlers
            **kwargs: Additional arguments passed to BaseTool
        """
        super().__init__(
            mcp_config=mcp_config,
            notification_handlers=notification_handlers or [],
            **kwargs,
        )

        # Initialize notification router with handlers
        self._router = NotificationRouter(handlers=self.notification_handlers)

        # Initialize MCP client with notification callback
        self._client = MCPClient(
            self.mcp_config,
            notification_callback=self._handle_notification
        )

    def _handle_notification(self, notification: ChangeNotification) -> None:
        try:
            logger.debug(f"Received notification: {notification}")
            self._router.route_notification(notification)
        except Exception as e:
            logger.error(f"Error processing notification: {e}")

    async def discover_queries(self) -> list[QueryInfo]:
        """Discover available Drasi queries.

        Returns:
            List of QueryInfo objects describing available queries

        Raises:
            MCPConnectionError: If discovery fails
        """
        if not self._client:
            raise RuntimeError("MCP client not initialized")

        # Ensure connected
        if not self._client._connected:
            await self._client.connect()

        return await self._client.list_resources()

    async def read_query(self, query_name: str) -> QueryResult:
        """Read current results from a Drasi query.

        Args:
            query_name: Name of the query to read

        Returns:
            QueryResult with current query data

        Raises:
            QueryNotFoundError: If query doesn't exist
            MCPConnectionError: If read fails
        """
        if not self._client:
            raise RuntimeError("MCP client not initialized")

        # Ensure connected
        if not self._client._connected:
            await self._client.connect()

        # Construct URI from query name
        uri = f"drasi://query/{query_name}"

        return await self._client.read_resource(uri)

    async def subscribe(self, query_name: str) -> str:
        """Subscribe to real-time updates from a query.

        Args:
            query_name: Name of the query to subscribe to

        Returns:
            Confirmation message

        Raises:
            SubscriptionError: If subscription fails
        """
        if not self._client:
            raise RuntimeError("MCP client not initialized")

        # Ensure connected
        if not self._client._connected:
            await self._client.connect()

        # Construct URI from query name
        uri = f"drasi://query/{query_name}"

        try:
            await self._client.subscribe(uri)
            return f"Successfully subscribed to query: {query_name}"

        except Exception as e:
            raise SubscriptionError(
                f"Failed to subscribe to query '{query_name}': {e}",
                details={"query_name": query_name, "error": str(e)},
            ) from e

    async def unsubscribe(self, query_name: str) -> str:
        """Unsubscribe from a query.

        Args:
            query_name: Name of the query to unsubscribe from

        Returns:
            Confirmation message

        Raises:
            SubscriptionError: If unsubscription fails
        """
        if not self._client:
            raise RuntimeError("MCP client not initialized")

        # Ensure connected
        if not self._client._connected:
            await self._client.connect()

        # Construct URI from query name
        uri = f"drasi://query/{query_name}"

        try:
            await self._client.unsubscribe(uri)
            return f"Successfully unsubscribed from query: {query_name}"

        except Exception as e:
            raise SubscriptionError(
                f"Failed to unsubscribe from query '{query_name}': {e}",
                details={"query_name": query_name, "error": str(e)},
            ) from e

    def _run(self, query_name: str = "", operation: str = "read") -> str:
        """Synchronous execution (not supported).

        DrasiTool requires async execution. Use _arun() or ainvoke() instead.

        Raises:
            NotImplementedError: Always raised
        """
        raise NotImplementedError(
            "DrasiTool only supports async execution. Use ainvoke() instead."
        )

    async def _arun(
        self, query_name: str = "", operation: str = "read"
    ) -> str | list[QueryInfo] | QueryResult:
        """Async execution of the tool.

        This is the main entry point when the tool is invoked by an agent.

        Args:
            query_name: Name of the query (empty for discover)
            operation: Operation to perform

        Returns:
            Operation-specific result

        Raises:
            ValueError: If operation is invalid
            QueryNotFoundError: If query doesn't exist
            SubscriptionError: If subscription operation fails
        """
        # Convert operation string to enum
        try:
            op = DrasiOperation(operation)
        except ValueError:
            raise ValueError(
                f"Invalid operation: {operation}. "
                f"Must be one of: {[o.value for o in DrasiOperation]}"
            )

        # Execute operation
        if op == DrasiOperation.DISCOVER:
            queries = await self.discover_queries()
            # Format as string for LLM
            if not queries:
                return "No Drasi queries found."
            query_list = "\n".join(
                f"- {q['name']}: {q['description']}" for q in queries
            )
            return f"Available Drasi queries:\n{query_list}"

        if op == DrasiOperation.READ:
            if not query_name:
                raise ValueError("query_name is required for 'read' operation")

            result = await self.read_query(query_name)
            # Format as string for LLM
            content_count = len(result["content"])

            # Format content as readable JSON
            import json
            formatted_content = json.dumps(result["content"], indent=2)

            return (
                f"Query '{query_name}' returned {content_count} result(s):\n"
                f"{formatted_content}"
            )

        if op == DrasiOperation.SUBSCRIBE:
            if not query_name:
                raise ValueError("query_name is required for 'subscribe' operation")

            return await self.subscribe(query_name)

        if op == DrasiOperation.UNSUBSCRIBE:
            if not query_name:
                raise ValueError("query_name is required for 'unsubscribe' operation")

            return await self.unsubscribe(query_name)

        raise ValueError(f"Unsupported operation: {operation}")


def create_drasi_tool(
    mcp_config: MCPConnectionConfig,
    notification_handlers: list[DrasiNotificationHandler] | None = None,
    **kwargs: Any,
) -> DrasiTool:
    """Factory function to create a DrasiTool instance.

    This is the recommended way to create a DrasiTool.

    Args:
        mcp_config: MCP connection configuration
        notification_handlers: Optional list of notification handlers
        **kwargs: Additional arguments passed to DrasiTool

    Returns:
        Configured DrasiTool instance

    Example:
        ```python
        from langchain_drasi import create_drasi_tool, MCPConnectionConfig

        config = MCPConnectionConfig(
            server_url="https://your-drasi-server.com/api",
            headers={"Authorization": "Bearer your-token"}
        )

        tool = create_drasi_tool(mcp_config=config)
        ```
    """
    return DrasiTool(
        mcp_config=mcp_config,
        notification_handlers=notification_handlers,
        **kwargs,
    )
