# Python API Contracts

**Feature**: LangChain-Drasi Library
**Version**: 1.0
**Python Version**: 3.13+
**Created**: 2025-10-01

---

## 1. Overview

This document defines the public Python API contracts for the LangChain-Drasi library. All public interfaces use Python 3.13+ type hints, Protocol classes for structural typing, and TypedDict for structured dictionaries.

---

## 2. Core Tool Interface

### 2.1 DrasiTool Class

The main LangChain tool for accessing Drasi queries.

```python
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from typing import Optional, Type
from pydantic import BaseModel, Field

class DrasiQueryInput(BaseModel):
    """Input schema for Drasi query operations."""

    query_name: str = Field(
        description="Name of the Drasi query to access (e.g., 'active-orders')"
    )
    operation: str = Field(
        default="read",
        description="Operation to perform: 'read', 'subscribe', or 'unsubscribe'"
    )

class DrasiTool(BaseTool):
    """LangChain tool for accessing Drasi continuous queries via MCP.

    This tool enables LangChain agents to:
    - Discover available Drasi queries
    - Read current query results
    - Subscribe to query change notifications
    - Unsubscribe from queries

    Attributes:
        name: Tool identifier, default "drasi_query"
        description: Tool description for LLM consumption
        args_schema: Pydantic model defining input schema
        mcp_config: Configuration for MCP server connection
        callbacks: Registered callback handlers for notifications
    """

    name: str = "drasi_query"
    description: str = (
        "Access Drasi continuous queries. Use 'read' to get current results, "
        "'subscribe' to receive change notifications, 'unsubscribe' to stop notifications."
    )
    args_schema: Type[BaseModel] = DrasiQueryInput

    # Configuration
    mcp_config: "MCPConnectionConfig"
    notification_handlers: list["DrasiNotificationHandler"]

    def __init__(
        self,
        mcp_config: "MCPConnectionConfig",
        notification_handlers: list["DrasiNotificationHandler"] | None = None,
        **kwargs
    ) -> None:
        """Initialize the Drasi tool.

        Args:
            mcp_config: MCP server connection configuration
            notification_handlers: Callback handlers for change notifications
            **kwargs: Additional BaseTool arguments

        Raises:
            ValueError: If mcp_config is invalid
        """
        ...

    def _run(
        self,
        query_name: str,
        operation: str = "read",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Synchronous implementation (delegates to async).

        Args:
            query_name: Name of the query to access
            operation: Operation to perform
            run_manager: Callback manager for tool execution

        Returns:
            JSON string containing query results or operation status

        Raises:
            QueryNotFoundError: If query doesn't exist
            MCPConnectionError: If MCP connection fails
        """
        ...

    async def _arun(
        self,
        query_name: str,
        operation: str = "read",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Asynchronous implementation.

        Args:
            query_name: Name of the query to access
            operation: Operation to perform
            run_manager: Callback manager for tool execution

        Returns:
            JSON string containing query results or operation status

        Raises:
            QueryNotFoundError: If query doesn't exist
            MCPConnectionError: If MCP connection fails
        """
        ...

    async def discover_queries(self) -> list["QueryInfo"]:
        """Discover all available Drasi queries.

        Returns:
            List of QueryInfo objects describing available queries

        Raises:
            MCPConnectionError: If connection to MCP server fails
        """
        ...

    async def read_query(self, query_name: str) -> "QueryResult":
        """Read the current result set of a query.

        Args:
            query_name: Name of the query to read

        Returns:
            QueryResult containing the current data

        Raises:
            QueryNotFoundError: If query doesn't exist
            MCPConnectionError: If connection fails
        """
        ...

    async def subscribe(self, query_name: str) -> None:
        """Subscribe to change notifications for a query.

        Args:
            query_name: Name of the query to subscribe to

        Raises:
            QueryNotFoundError: If query doesn't exist
            SubscriptionError: If subscription fails
        """
        ...

    async def unsubscribe(self, query_name: str) -> None:
        """Unsubscribe from change notifications for a query.

        Args:
            query_name: Name of the query to unsubscribe from

        Raises:
            SubscriptionError: If unsubscribe operation fails
        """
        ...
```

---

## 3. Configuration Classes

### 3.1 MCP Connection Configuration

```python
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class ReconnectPolicy(BaseModel):
    """Policy for handling connection failures and reconnection.

    Attributes:
        enabled: Whether to attempt reconnection on failure
        max_retries: Maximum retry attempts (None = infinite)
        retry_delay: Initial delay between retries in seconds
        backoff_multiplier: Exponential backoff multiplier
        max_delay: Maximum delay between retries in seconds
    """

    enabled: bool = Field(default=True)
    max_retries: int | None = Field(default=5)
    retry_delay: float = Field(default=1.0, gt=0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    max_delay: float = Field(default=60.0, gt=0)

    @field_validator("retry_delay", "max_delay")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        """Ensure delay values are positive."""
        if v <= 0:
            raise ValueError("Delay must be positive")
        return v

class MCPConnectionConfig(BaseModel):
    """Configuration for MCP server connection.

    Attributes:
        server_command: Command to start the MCP server
        server_args: Arguments to pass to server command
        server_env: Environment variables for server process
        reconnect_policy: Policy for handling connection failures
        timeout: Connection timeout in seconds
    """

    server_command: str = Field(
        description="Command to start MCP server (e.g., 'python', 'node')"
    )
    server_args: list[str] = Field(
        default_factory=list,
        description="Arguments for server command"
    )
    server_env: dict[str, str] | None = Field(
        default=None,
        description="Environment variables for server process"
    )
    reconnect_policy: ReconnectPolicy = Field(
        default_factory=ReconnectPolicy
    )
    timeout: int = Field(default=30, gt=0)

    @field_validator("server_command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Ensure command is not empty."""
        if not v.strip():
            raise ValueError("Server command cannot be empty")
        return v.strip()
```

---

## 4. Callback Protocol

### 4.1 Notification Handler Protocol

```python
from typing import Protocol, runtime_checkable
from enum import Enum

class ChangeType(str, Enum):
    """Types of query result changes."""
    ADDED = "added"
    UPDATED = "updated"
    DELETED = "deleted"

@runtime_checkable
class DrasiNotificationHandler(Protocol):
    """Protocol for handling Drasi query change notifications.

    Implementations must provide at least one of the notification handlers.
    All handlers are optional to allow selective handling of change types.
    """

    def on_result_added(
        self,
        query_name: str,
        added_data: dict
    ) -> None:
        """Called when a row is added to query results.

        Args:
            query_name: Name of the query that changed
            added_data: Data for the newly added row

        Note:
            Exceptions raised in this handler will be logged but won't
            interrupt notification processing.
        """
        ...

    def on_result_updated(
        self,
        query_name: str,
        updated_data: dict
    ) -> None:
        """Called when a row in query results is updated.

        Args:
            query_name: Name of the query that changed
            updated_data: Data for the updated row

        Note:
            Exceptions raised in this handler will be logged but won't
            interrupt notification processing.
        """
        ...

    def on_result_deleted(
        self,
        query_name: str,
        deleted_data: dict
    ) -> None:
        """Called when a row is removed from query results.

        Args:
            query_name: Name of the query that changed
            deleted_data: Data identifying the deleted row

        Note:
            Exceptions raised in this handler will be logged but won't
            interrupt notification processing.
        """
        ...

    def on_notification_error(
        self,
        query_name: str,
        error: Exception
    ) -> None:
        """Called when notification processing fails.

        Args:
            query_name: Name of the query where error occurred
            error: The exception that occurred

        Note:
            This is optional. If not implemented, errors are only logged.
        """
        ...

### 4.2 Callback Handler Base Class

```python
from abc import ABC

class BaseDrasiNotificationHandler(ABC):
    """Base class for Drasi notification handlers.

    Subclass this to implement custom notification handling.
    Override only the methods for change types you want to handle.
    """

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        """Handle added notification. Override to implement."""
        pass

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        """Handle updated notification. Override to implement."""
        pass

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        """Handle deleted notification. Override to implement."""
        pass

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Handle notification errors. Override to implement."""
        pass
```

---

## 5. Data Transfer Objects

### 5.1 Query Information

```python
from typing import TypedDict

class QueryInfo(TypedDict):
    """Information about an available Drasi query.

    Attributes:
        name: Unique query identifier
        title: Display title for the query
        uri: MCP resource URI (drasi://query/{name})
        description: Purpose and nature of the query
        mime_type: Content MIME type (application/json)
    """

    name: str
    title: str
    uri: str
    description: str
    mime_type: str

class QueryResult(TypedDict):
    """Result from reading a Drasi query.

    Attributes:
        query_name: Name of the query
        uri: Resource URI
        data: Query result data as list of dictionaries
        mime_type: Content MIME type
        timestamp: Optional timestamp of result
    """

    query_name: str
    uri: str
    data: list[dict]
    mime_type: str
    timestamp: str | None

class ChangeNotification(TypedDict):
    """Change notification from MCP server.

    Attributes:
        change_type: Type of change (added, updated, deleted)
        query_name: Name of the query that changed
        method: MCP notification method name
        params: Change data parameters
        timestamp: Optional timestamp of change
    """

    change_type: ChangeType
    query_name: str
    method: str
    params: dict
    timestamp: str | None
```

---

## 6. Exception Types

### 6.1 Custom Exceptions

```python
class DrasiError(Exception):
    """Base exception for all Drasi-related errors."""
    pass

class MCPConnectionError(DrasiError):
    """Raised when MCP server connection fails.

    Attributes:
        message: Error description
        server_command: Command used to start server
        original_error: The underlying exception (if any)
    """

    def __init__(
        self,
        message: str,
        server_command: str | None = None,
        original_error: Exception | None = None
    ) -> None:
        super().__init__(message)
        self.server_command = server_command
        self.original_error = original_error

class QueryNotFoundError(DrasiError):
    """Raised when attempting to access a non-existent query.

    Attributes:
        query_name: Name of the query that wasn't found
        available_queries: List of available query names (optional)
    """

    def __init__(
        self,
        query_name: str,
        available_queries: list[str] | None = None
    ) -> None:
        message = f"Query '{query_name}' not found"
        if available_queries:
            message += f". Available queries: {', '.join(available_queries)}"
        super().__init__(message)
        self.query_name = query_name
        self.available_queries = available_queries

class SubscriptionError(DrasiError):
    """Raised when subscription operations fail.

    Attributes:
        query_name: Name of the query
        operation: The operation that failed ('subscribe' or 'unsubscribe')
        reason: Reason for failure
    """

    def __init__(
        self,
        query_name: str,
        operation: str,
        reason: str | None = None
    ) -> None:
        message = f"Subscription {operation} failed for query '{query_name}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.query_name = query_name
        self.operation = operation
        self.reason = reason

class NotificationProcessingError(DrasiError):
    """Raised when notification processing fails.

    Note: This is typically logged rather than raised, as callback
    errors should not interrupt the notification stream.

    Attributes:
        query_name: Name of the query
        notification_type: Type of notification that failed
        original_error: The callback exception
    """

    def __init__(
        self,
        query_name: str,
        notification_type: str,
        original_error: Exception
    ) -> None:
        message = (
            f"Error processing {notification_type} notification "
            f"for query '{query_name}': {str(original_error)}"
        )
        super().__init__(message)
        self.query_name = query_name
        self.notification_type = notification_type
        self.original_error = original_error
```

---

## 7. Factory Functions

### 7.1 Tool Creation

```python
def create_drasi_tool(
    mcp_config: MCPConnectionConfig,
    notification_handlers: list[DrasiNotificationHandler] | None = None,
    tool_name: str = "drasi_query",
    tool_description: str | None = None
) -> DrasiTool:
    """Factory function to create a configured DrasiTool.

    Args:
        mcp_config: MCP server connection configuration
        notification_handlers: Handlers for query change notifications
        tool_name: Custom name for the tool (optional)
        tool_description: Custom description for the tool (optional)

    Returns:
        Configured DrasiTool instance ready for use

    Raises:
        ValueError: If configuration is invalid

    Example:
        >>> config = MCPConnectionConfig(
        ...     server_command="python",
        ...     server_args=["mcp_server.py"]
        ... )
        >>> handler = MyNotificationHandler()
        >>> tool = create_drasi_tool(config, [handler])
    """
    ...

def create_simple_handler(
    on_added: Callable[[str, dict], None] | None = None,
    on_updated: Callable[[str, dict], None] | None = None,
    on_deleted: Callable[[str, dict], None] | None = None,
    on_error: Callable[[str, Exception], None] | None = None
) -> DrasiNotificationHandler:
    """Create a simple notification handler from functions.

    Args:
        on_added: Function to call for added notifications
        on_updated: Function to call for updated notifications
        on_deleted: Function to call for deleted notifications
        on_error: Function to call for errors

    Returns:
        DrasiNotificationHandler implementation

    Example:
        >>> def handle_added(query: str, data: dict):
        ...     print(f"Added to {query}: {data}")
        >>> handler = create_simple_handler(on_added=handle_added)
    """
    ...
```

---

## 8. Type Aliases and Constants

### 8.1 Type Aliases

```python
from collections.abc import Callable, Awaitable

# Callback function types
NotificationCallback = Callable[[str, dict], None]
AsyncNotificationCallback = Callable[[str, dict], Awaitable[None]]
ErrorCallback = Callable[[str, Exception], None]

# Query-related types
QueryName = str
QueryURI = str
QueryData = list[dict]

# MCP-related types
MCPMethod = str
MCPParams = dict
ResourceContent = str
```

### 8.2 Constants

```python
# URI scheme for Drasi queries
DRASI_URI_SCHEME = "drasi"
DRASI_URI_PREFIX = "drasi://query/"

# MCP notification method patterns
NOTIFICATION_METHOD_PATTERN = "notifications/{query_name}/{change_type}"

# Supported MIME types
SUPPORTED_MIME_TYPES = ["application/json"]

# Default values
DEFAULT_TOOL_NAME = "drasi_query"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRIES = 5
```

---

## 9. Usage Examples

### 9.1 Basic Tool Setup

```python
from langchain_drasi import (
    create_drasi_tool,
    MCPConnectionConfig,
    BaseDrasiNotificationHandler
)

# Configure MCP connection
config = MCPConnectionConfig(
    server_command="python",
    server_args=["drasi_mcp_server.py"]
)

# Create notification handler
class MyHandler(BaseDrasiNotificationHandler):
    def on_result_added(self, query_name: str, added_data: dict) -> None:
        print(f"New data in {query_name}: {added_data}")

# Create tool
tool = create_drasi_tool(
    mcp_config=config,
    notification_handlers=[MyHandler()]
)
```

### 9.2 Using with LangChain Agent

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(model="gpt-4", temperature=0)

agent = create_react_agent(
    llm,
    tools=[tool],
    state_modifier="You have access to Drasi continuous queries."
)

result = agent.invoke({
    "messages": [("user", "What's in the active-orders query?")]
})
```

### 9.3 Function-Based Handler

```python
from langchain_drasi import create_simple_handler

def log_changes(query_name: str, data: dict) -> None:
    print(f"Change in {query_name}: {data}")

handler = create_simple_handler(
    on_added=log_changes,
    on_updated=log_changes,
    on_deleted=log_changes
)

tool = create_drasi_tool(config, [handler])
```

---

## 10. Contract Guarantees

### 10.1 Functional Requirements Mapping

| Requirement | Contract Element | Guarantee |
|-------------|------------------|-----------|
| FR-001 | `discover_queries()` | Returns all available queries |
| FR-002 | `read_query()` | Fetches current result set |
| FR-003 | `subscribe()` | Registers for notifications |
| FR-010, FR-011 | `DrasiNotificationHandler` | LangChain-compatible callbacks |
| FR-012 | `__init__` parameters | Callbacks provided at construction |
| FR-017 | `ReconnectPolicy` | User-configurable reconnection |
| FR-018 | Exception handling | Callbacks logged, don't interrupt |
| FR-020 | `read_query()` | No caching, always fetches fresh |
| FR-021 | Subscription lifecycle | Session-based, not persisted |

### 10.2 Behavioral Contracts

1. **Connection Management**:
   - Connection established on first operation if not connected
   - Reconnection follows configured policy
   - Subscriptions re-established after reconnection

2. **Error Handling**:
   - `QueryNotFoundError` for non-existent queries
   - `MCPConnectionError` for connection failures
   - `SubscriptionError` for subscription issues
   - Callback exceptions logged, don't interrupt processing

3. **Threading and Async**:
   - All I/O operations are async
   - Sync `_run` delegates to async `_arun`
   - Thread-safe for concurrent tool invocations

4. **Data Format**:
   - All query results are JSON (list of dicts)
   - Notifications contain change type and params
   - URIs follow `drasi://query/{name}` format

---

## 11. Versioning and Compatibility

### 11.1 API Stability

- **Public API**: All documented classes, functions, and protocols
- **Stable**: Will follow semantic versioning
- **Breaking changes**: Only in major versions
- **Deprecation**: Minimum 2 minor versions notice

### 11.2 Python Version Support

- **Minimum**: Python 3.11
- **Recommended**: Python 3.13+
- **Type hints**: Using modern syntax (PEP 604, 585)

### 11.3 Dependency Compatibility

- **LangChain Core**: >= 0.3.0
- **MCP SDK**: >= 1.7.0
- **Pydantic**: >= 2.0.0

---

**Document Status**: Complete
**Last Updated**: 2025-10-01
**Related Documents**:
- `/Users/danielgerlag/dev/learn/langchain-ext/langchain-drasi/specs/001-build-a-library/spec.md`
- `/Users/danielgerlag/dev/learn/langchain-ext/langchain-drasi/specs/001-build-a-library/data-model.md`
