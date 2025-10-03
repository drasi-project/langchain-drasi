"""MCP client wrapper for Drasi query communication.

This module provides a wrapper around the MCP SDK client with Drasi-specific
functionality for connecting to remote HTTP-based MCP servers, listing queries,
reading results, and managing subscriptions.
"""

import logging
from typing import Any, Callable

from mcp import ClientSession, ResourceUpdatedNotification, ServerNotification
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import JSONRPCNotification
from mcp.shared.session import RequestResponder

from .config import MCPConnectionConfig
from .exceptions import MCPConnectionError, QueryNotFoundError
from .models import ChangeNotification, ChangeType, QueryInfo, QueryResult

logger = logging.getLogger(__name__)


class DrasiClientSession(ClientSession):
    """Custom ClientSession that handles Drasi notifications.

    This extends the standard MCP ClientSession to handle notifications/resources/updated
    messages with Drasi-specific params (uri, operation, data) that fail MCP validation.
    """

    def __init__(self, read_stream: Any, write_stream: Any, drasi_notification_callback: Callable[[ChangeNotification], None] | None = None):
        """Initialize Drasi client session.

        Args:
            read_stream: Stream for reading messages
            write_stream: Stream for writing messages
            drasi_notification_callback: Callback for Drasi-specific notifications
        """
        super().__init__(read_stream, write_stream)
        self._drasi_notification_callback = drasi_notification_callback

    async def _received_notification(self, notification: ServerNotification) -> None:
        """Override to handle Drasi notifications.

        Args:
            notification: The notification object from MCP SDK
        """
        logger.debug(f"Received notification: {notification}")

        # Extract the actual notification
        actual_notif = notification.root if hasattr(notification, 'root') else notification

        # Check if this is a ResourceUpdatedNotification
        if isinstance(actual_notif, ResourceUpdatedNotification):
            params = actual_notif.params if hasattr(actual_notif, 'params') else {}

            if params.uri.scheme == "drasi":
            
                logger.debug(f"Detected Drasi notification with params: {params}")
                if self._drasi_notification_callback:
                    
                    change_notification = ChangeNotification()
                    change_notification.change_type = ChangeType(params.model_extra.get("operation")) 
                    change_notification.query_name = params.uri.path.lstrip("/").split("/")[-1]  # Extract query name from URI
                    change_notification.data = params.model_extra.get("data")

                    logger.info(f"Routing Drasi notification: {params.uri} - {params.model_extra.get('operation')}")
                    self._drasi_notification_callback(change_notification)
                    return

        # Let parent handle standard MCP notifications
        logger.debug("Passing notification to base handler")
        await super()._received_notification(notification)



class MCPClient:
    """Wrapper around MCP SDK client for Drasi query operations via HTTP.

    This class manages the connection to a remote HTTP-based MCP server
    and provides methods for discovering queries, reading query results,
    and managing subscriptions.

    Attributes:
        config: MCP connection configuration
        session: Active MCP client session (when connected)
    """

    def __init__(self, config: MCPConnectionConfig, notification_callback: Callable[[ChangeNotification], None] | None = None) -> None:
        """Initialize MCP client with configuration.

        Args:
            config: MCP connection configuration including server URL and headers
            notification_callback: Optional callback for handling raw notifications
        """
        self.config = config
        self.session: DrasiClientSession | None = None
        self._read_stream: Any = None
        self._write_stream: Any = None
        self._get_session_id: Callable[[], str | None] | None = None
        self._http_context: Any = None
        self._notification_callback = notification_callback
        self._connected = False

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry - establish connection."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - close connection."""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection to remote HTTP-based MCP server.

        Raises:
            MCPConnectionError: If connection fails
        """
        if self._connected:
            logger.warning("Already connected to MCP server")
            return

        try:
            logger.info(f"Connecting to MCP server: {self.config.server_url}")

            # Establish HTTP connection using streamable HTTP transport
            self._http_context = streamablehttp_client(
                url=self.config.server_url,
                headers=self.config.headers or {},
                timeout=self.config.timeout,
            )

            # Enter the HTTP context to get streams and session ID getter
            read_stream, write_stream, get_session_id = await self._http_context.__aenter__()
            self._read_stream = read_stream
            self._write_stream = write_stream
            self._get_session_id = get_session_id

            # Create session with Drasi notification handling
            self.session = DrasiClientSession(
                read_stream,
                write_stream,
                drasi_notification_callback=self._notification_callback
            )

            # Initialize session
            await self.session.__aenter__()

            # Perform MCP initialization handshake
            init_result = await self.session.initialize()
            logger.info(f"MCP initialized: {init_result.serverInfo.name} v{init_result.serverInfo.version}")

            self._connected = True
            logger.info(f"Successfully connected to MCP server at {self.config.server_url}")

            # Log session ID if available
            session_id = get_session_id() if get_session_id else None
            if session_id:
                logger.debug(f"Session ID: {session_id}")

        except Exception as e:
            # Extract useful error message from ExceptionGroup if present
            error_msg = str(e)
            if hasattr(e, 'exceptions') and e.exceptions:
                # Get the first underlying exception for better error message
                underlying = e.exceptions[0]
                error_msg = f"{type(underlying).__name__}: {str(underlying)}"

            raise MCPConnectionError(
                f"Failed to connect to MCP server at {self.config.server_url}: {error_msg}",
                details={
                    "server_url": self.config.server_url,
                    "error": error_msg,
                    "type": type(e).__name__,
                },
            ) from e

    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if not self._connected:
            return

        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
                self.session = None

            # Clean up HTTP context
            if self._http_context:
                await self._http_context.__aexit__(None, None, None)
                self._http_context = None

            self._connected = False
            logger.info("Disconnected from MCP server")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def _ensure_connected(self) -> ClientSession:
        """Ensure client is connected and return session.

        Returns:
            Active ClientSession

        Raises:
            MCPConnectionError: If not connected
        """
        if not self._connected or self.session is None:
            raise MCPConnectionError(
                "Not connected to MCP server. Use 'async with MCPClient()' or call connect().",
                details={"connected": self._connected},
            )
        return self.session

    async def list_resources(self) -> list[QueryInfo]:
        """List available Drasi queries from MCP server.

        Returns:
            List of QueryInfo objects describing available queries

        Raises:
            MCPConnectionError: If request fails
        """
        session = self._ensure_connected()

        try:
            logger.debug("Requesting resources list from MCP server")

            # Call MCP resources/list
            response = await session.list_resources()

            # Convert MCP resources to QueryInfo
            queries: list[QueryInfo] = []
            for resource in response.resources:
                query_info: QueryInfo = {
                    "name": resource.name,
                    "title": getattr(resource, "title", resource.name),
                    "uri": resource.uri,
                    "description": resource.description or "",
                    "mime_type": resource.mimeType or "application/json",
                }
                queries.append(query_info)

            logger.debug(f"Found {len(queries)} queries")
            return queries

        except Exception as e:
            raise MCPConnectionError(
                f"Failed to list resources: {e}",
                details={"error": str(e)},
            ) from e

    async def read_resource(self, uri: str) -> QueryResult:
        """Read query results from MCP server.

        Args:
            uri: Resource URI (format: drasi://query/{query-name})

        Returns:
            QueryResult with query data

        Raises:
            QueryNotFoundError: If query doesn't exist
            MCPConnectionError: If request fails
        """
        session = self._ensure_connected()

        try:
            logger.debug(f"Reading resource: {uri}")

            # Call MCP resources/read
            response = await session.read_resource(uri)

            if not response.contents:
                raise QueryNotFoundError(
                    f"No content returned for query: {uri}",
                    details={"uri": uri},
                )

            # Parse content (first content item)
            content_item = response.contents[0]

            # Extract query name from URI
            query_name = uri.split("/")[-1] if "/" in uri else uri

            # Parse JSON content
            import json
            content_data = json.loads(content_item.text)

            result: QueryResult = {
                "query_name": query_name,
                "uri": uri,
                "mime_type": content_item.mimeType or "application/json",
                "content": content_data if isinstance(content_data, list) else [content_data],
                "timestamp": None,  # MCP doesn't provide timestamp
            }

            logger.debug(f"Successfully read resource: {query_name}")
            return result

        except QueryNotFoundError:
            raise
        except json.JSONDecodeError as e:
            raise MCPConnectionError(
                f"Failed to parse query results as JSON: {e}",
                details={"uri": uri, "error": str(e)},
            ) from e
        except Exception as e:
            # Check if it's a "not found" type error
            error_msg = str(e).lower()
            if "not found" in error_msg or "does not exist" in error_msg:
                raise QueryNotFoundError(
                    f"Query not found: {uri}",
                    details={"uri": uri, "error": str(e)},
                ) from e

            raise MCPConnectionError(
                f"Failed to read resource: {e}",
                details={"uri": uri, "error": str(e)},
            ) from e

    async def subscribe(self, uri: str) -> None:
        """Subscribe to query updates.

        Args:
            uri: Resource URI to subscribe to

        Raises:
            MCPConnectionError: If subscription fails
        """
        session = self._ensure_connected()

        try:
            logger.debug(f"Subscribing to resource: {uri}")

            # Call MCP resources/subscribe
            await session.subscribe_resource(uri)

            logger.info(f"Successfully subscribed to: {uri}")

        except Exception as e:
            raise MCPConnectionError(
                f"Failed to subscribe to resource: {e}",
                details={"uri": uri, "error": str(e)},
            ) from e

    async def unsubscribe(self, uri: str) -> None:
        """Unsubscribe from query updates.

        Args:
            uri: Resource URI to unsubscribe from

        Raises:
            MCPConnectionError: If unsubscription fails
        """
        session = self._ensure_connected()

        try:
            logger.debug(f"Unsubscribing from resource: {uri}")

            # Call MCP resources/unsubscribe
            await session.unsubscribe_resource(uri)

            logger.info(f"Successfully unsubscribed from: {uri}")

        except Exception as e:
            logger.error(f"Failed to unsubscribe from resource: {e}")
            # Don't raise - unsubscribe failures are not critical
