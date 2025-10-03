# Callback Interface Specifications

**Feature**: LangChain-Drasi Library
**Version**: 1.0
**Created**: 2025-10-01

---

## 1. Overview

This document specifies the callback interface for the LangChain-Drasi library. The callback system enables applications to respond to Drasi query changes in real-time while maintaining compatibility with LangChain's existing callback infrastructure.

**Design Principles**:
- **LangChain Compatible**: Follows LangChain callback patterns and conventions
- **Flexible**: Support both protocol-based and class-based implementations
- **Error Resilient**: Callback failures don't interrupt notification processing
- **Type Safe**: Full type hints for static analysis and IDE support

---

## 2. Notification Handler Protocol

### 2.1 Protocol Definition

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class DrasiNotificationHandler(Protocol):
    """Protocol defining the interface for Drasi query change notifications.

    This protocol allows structural typing - any class implementing these
    methods can be used as a notification handler without explicit inheritance.

    All methods are optional, allowing handlers to selectively respond to
    specific change types.
    """

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        """Handle notification when a row is added to query results.

        Called when the MCP server emits a notifications/{query-name}/added
        message.

        Args:
            query_name: Name of the query that changed
            added_data: Dictionary containing the newly added row data

        Returns:
            None

        Raises:
            Any exception raised will be logged but won't interrupt processing

        Example:
            >>> def on_result_added(self, query_name: str, added_data: dict):
            ...     print(f"New row in {query_name}: {added_data}")
        """
        ...

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        """Handle notification when a row in query results is updated.

        Called when the MCP server emits a notifications/{query-name}/updated
        message.

        Args:
            query_name: Name of the query that changed
            updated_data: Dictionary containing the updated row data

        Returns:
            None

        Raises:
            Any exception raised will be logged but won't interrupt processing

        Example:
            >>> def on_result_updated(self, query_name: str, updated_data: dict):
            ...     print(f"Updated row in {query_name}: {updated_data}")
        """
        ...

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        """Handle notification when a row is removed from query results.

        Called when the MCP server emits a notifications/{query-name}/deleted
        message.

        Args:
            query_name: Name of the query that changed
            deleted_data: Dictionary identifying the deleted row

        Returns:
            None

        Raises:
            Any exception raised will be logged but won't interrupt processing

        Example:
            >>> def on_result_deleted(self, query_name: str, deleted_data: dict):
            ...     print(f"Deleted row from {query_name}: {deleted_data}")
        """
        ...

    def on_notification_error(
        self,
        query_name: str,
        error: Exception
    ) -> None:
        """Handle errors that occur during notification processing.

        This is called when:
        - Notification parsing fails
        - Handler method raises an exception
        - MCP protocol error occurs

        Args:
            query_name: Name of the query where error occurred
            error: The exception that was raised

        Returns:
            None

        Note:
            This method is optional. If not implemented, errors are only logged.

        Example:
            >>> def on_notification_error(self, query_name: str, error: Exception):
            ...     logger.error(f"Error in {query_name}: {error}")
        """
        ...
```

### 2.2 Protocol Usage

**Duck Typing Example**:
```python
class MyHandler:
    """Handler using duck typing - no explicit protocol inheritance."""

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        print(f"Added: {added_data}")

# Type checker validates this implements the protocol
handler: DrasiNotificationHandler = MyHandler()
```

**Runtime Validation**:
```python
from langchain_drasi import DrasiNotificationHandler

def register_handler(handler: object) -> None:
    if isinstance(handler, DrasiNotificationHandler):
        print("Handler is compatible!")
    else:
        print("Handler missing required methods")
```

---

## 3. Base Handler Class

### 3.1 Base Class Definition

```python
from abc import ABC

class BaseDrasiNotificationHandler(ABC):
    """Abstract base class for notification handlers.

    Subclass this to create custom handlers. Override only the methods
    for change types you want to handle. Default implementations are no-ops.

    This provides a more explicit class-based alternative to the Protocol.
    """

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        """Handle added notifications. Override to implement custom logic."""
        pass

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        """Handle updated notifications. Override to implement custom logic."""
        pass

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        """Handle deleted notifications. Override to implement custom logic."""
        pass

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Handle notification errors. Override to implement custom logic."""
        pass
```

### 3.2 Convenience Methods

```python
class BaseDrasiNotificationHandler(ABC):
    """Extended with convenience methods."""

    def on_query_change(
        self,
        query_name: str,
        change_type: str,
        data: dict
    ) -> None:
        """Generic change handler called for all change types.

        This is called after the specific handler (on_result_added, etc).
        Useful for common logic across all change types.

        Args:
            query_name: Name of the query
            change_type: Type of change ("added", "updated", "deleted")
            data: Change data
        """
        pass

    def should_handle_query(self, query_name: str) -> bool:
        """Determine if this handler should process a query.

        Override to filter notifications by query name.

        Args:
            query_name: Name of the query

        Returns:
            True if handler should process this query, False otherwise

        Example:
            >>> def should_handle_query(self, query_name: str) -> bool:
            ...     return query_name.startswith("important_")
        """
        return True

    def get_handler_name(self) -> str:
        """Get a descriptive name for this handler.

        Used in logging and error messages.

        Returns:
            Handler name (defaults to class name)
        """
        return self.__class__.__name__
```

---

## 4. Function-Based Handlers

### 4.1 Simple Function Handler Factory

```python
from collections.abc import Callable

def create_simple_handler(
    on_added: Callable[[str, dict], None] | None = None,
    on_updated: Callable[[str, dict], None] | None = None,
    on_deleted: Callable[[str, dict], None] | None = None,
    on_error: Callable[[str, Exception], None] | None = None
) -> DrasiNotificationHandler:
    """Create a handler from simple functions.

    Args:
        on_added: Function to call for added notifications
        on_updated: Function to call for updated notifications
        on_deleted: Function to call for deleted notifications
        on_error: Function to call for errors

    Returns:
        Handler implementing DrasiNotificationHandler protocol

    Example:
        >>> def log_change(query: str, data: dict):
        ...     print(f"{query}: {data}")
        >>> handler = create_simple_handler(
        ...     on_added=log_change,
        ...     on_updated=log_change
        ... )
    """

    class FunctionBasedHandler:
        def on_result_added(self, query_name: str, added_data: dict) -> None:
            if on_added:
                on_added(query_name, added_data)

        def on_result_updated(self, query_name: str, updated_data: dict) -> None:
            if on_updated:
                on_updated(query_name, updated_data)

        def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
            if on_deleted:
                on_deleted(query_name, deleted_data)

        def on_notification_error(self, query_name: str, error: Exception) -> None:
            if on_error:
                on_error(query_name, error)

    return FunctionBasedHandler()
```

### 4.2 Decorator-Based Handler

```python
from typing import TypeVar, Callable
from functools import wraps

T = TypeVar('T', bound=Callable)

class HandlerBuilder:
    """Builder for creating handlers with decorators.

    Example:
        >>> handler = HandlerBuilder()
        >>>
        >>> @handler.on_added
        ... def handle_added(query: str, data: dict):
        ...     print(f"Added: {data}")
        >>>
        >>> @handler.on_updated
        ... def handle_updated(query: str, data: dict):
        ...     print(f"Updated: {data}")
        >>>
        >>> notification_handler = handler.build()
    """

    def __init__(self):
        self._on_added: Callable[[str, dict], None] | None = None
        self._on_updated: Callable[[str, dict], None] | None = None
        self._on_deleted: Callable[[str, dict], None] | None = None
        self._on_error: Callable[[str, Exception], None] | None = None

    def on_added(self, func: T) -> T:
        """Decorator to register added handler."""
        self._on_added = func
        return func

    def on_updated(self, func: T) -> T:
        """Decorator to register updated handler."""
        self._on_updated = func
        return func

    def on_deleted(self, func: T) -> T:
        """Decorator to register deleted handler."""
        self._on_deleted = func
        return func

    def on_error(self, func: T) -> T:
        """Decorator to register error handler."""
        self._on_error = func
        return func

    def build(self) -> DrasiNotificationHandler:
        """Build the handler from registered functions."""
        return create_simple_handler(
            on_added=self._on_added,
            on_updated=self._on_updated,
            on_deleted=self._on_deleted,
            on_error=self._on_error
        )
```

---

## 5. Async Handler Support

### 5.1 Async Protocol

```python
from typing import Protocol, runtime_checkable
from collections.abc import Awaitable

@runtime_checkable
class AsyncDrasiNotificationHandler(Protocol):
    """Async version of notification handler protocol.

    Use this when your handlers need to perform async operations
    (e.g., database writes, API calls).
    """

    async def on_result_added(self, query_name: str, added_data: dict) -> None:
        """Async handler for added notifications."""
        ...

    async def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        """Async handler for updated notifications."""
        ...

    async def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        """Async handler for deleted notifications."""
        ...

    async def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Async handler for notification errors."""
        ...
```

### 5.2 Async Base Class

```python
from abc import ABC

class AsyncBaseDrasiNotificationHandler(ABC):
    """Base class for async notification handlers."""

    async def on_result_added(self, query_name: str, added_data: dict) -> None:
        """Async handle added notifications. Override to implement."""
        pass

    async def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        """Async handle updated notifications. Override to implement."""
        pass

    async def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        """Async handle deleted notifications. Override to implement."""
        pass

    async def on_notification_error(self, query_name: str, error: Exception) -> None:
        """Async handle notification errors. Override to implement."""
        pass
```

### 5.3 Sync/Async Adapter

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def adapt_sync_handler(
    handler: DrasiNotificationHandler,
    executor: ThreadPoolExecutor | None = None
) -> AsyncDrasiNotificationHandler:
    """Adapt a sync handler to async interface.

    Args:
        handler: Synchronous handler
        executor: Thread pool for running sync code (optional)

    Returns:
        Async handler wrapping the sync handler

    Example:
        >>> sync_handler = MySyncHandler()
        >>> async_handler = adapt_sync_handler(sync_handler)
    """

    class SyncToAsyncAdapter:
        async def on_result_added(self, query_name: str, added_data: dict) -> None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                executor,
                handler.on_result_added,
                query_name,
                added_data
            )

        async def on_result_updated(self, query_name: str, updated_data: dict) -> None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                executor,
                handler.on_result_updated,
                query_name,
                updated_data
            )

        async def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                executor,
                handler.on_result_deleted,
                query_name,
                deleted_data
            )

        async def on_notification_error(self, query_name: str, error: Exception) -> None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                executor,
                handler.on_notification_error,
                query_name,
                error
            )

    return SyncToAsyncAdapter()
```

---

## 6. Built-in Handler Implementations

### 6.1 Logging Handler

```python
import logging
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]

class LoggingNotificationHandler(BaseDrasiNotificationHandler):
    """Handler that logs all notifications.

    Args:
        logger: Logger instance to use
        level: Log level for notifications
        include_data: Whether to include full data in logs
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        level: LogLevel = "INFO",
        include_data: bool = True
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.level = getattr(logging, level)
        self.include_data = include_data

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        msg = f"[ADDED] Query '{query_name}'"
        if self.include_data:
            msg += f": {added_data}"
        self.logger.log(self.level, msg)

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        msg = f"[UPDATED] Query '{query_name}'"
        if self.include_data:
            msg += f": {updated_data}"
        self.logger.log(self.level, msg)

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        msg = f"[DELETED] Query '{query_name}'"
        if self.include_data:
            msg += f": {deleted_data}"
        self.logger.log(self.level, msg)

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        self.logger.error(
            f"Error processing notification for '{query_name}': {error}",
            exc_info=error
        )
```

### 6.2 Queue Handler

```python
from queue import Queue
from typing import NamedTuple

class QueuedNotification(NamedTuple):
    """Notification stored in queue."""
    query_name: str
    change_type: str
    data: dict

class QueueNotificationHandler(BaseDrasiNotificationHandler):
    """Handler that queues notifications for async processing.

    Useful for decoupling notification receipt from processing.

    Args:
        queue: Queue to store notifications (created if not provided)
        max_size: Maximum queue size (0 = unlimited)
    """

    def __init__(self, queue: Queue | None = None, max_size: int = 0):
        self.queue = queue or Queue(maxsize=max_size)

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        self.queue.put(QueuedNotification(query_name, "added", added_data))

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        self.queue.put(QueuedNotification(query_name, "updated", updated_data))

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        self.queue.put(QueuedNotification(query_name, "deleted", deleted_data))

    def get_notification(self, timeout: float | None = None) -> QueuedNotification:
        """Get next notification from queue.

        Args:
            timeout: Timeout in seconds (None = block indefinitely)

        Returns:
            Next queued notification

        Raises:
            queue.Empty: If timeout expires with no notification
        """
        return self.queue.get(timeout=timeout)
```

### 6.3 Filtering Handler

```python
from typing import Callable

class FilteringNotificationHandler(BaseDrasiNotificationHandler):
    """Handler that filters notifications based on predicates.

    Args:
        inner_handler: Handler to delegate to when filter passes
        query_filter: Predicate for filtering by query name
        data_filter: Predicate for filtering by notification data
    """

    def __init__(
        self,
        inner_handler: DrasiNotificationHandler,
        query_filter: Callable[[str], bool] | None = None,
        data_filter: Callable[[dict], bool] | None = None
    ):
        self.inner_handler = inner_handler
        self.query_filter = query_filter or (lambda _: True)
        self.data_filter = data_filter or (lambda _: True)

    def _should_handle(self, query_name: str, data: dict) -> bool:
        """Check if notification should be handled."""
        return self.query_filter(query_name) and self.data_filter(data)

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        if self._should_handle(query_name, added_data):
            self.inner_handler.on_result_added(query_name, added_data)

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        if self._should_handle(query_name, updated_data):
            self.inner_handler.on_result_updated(query_name, updated_data)

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        if self._should_handle(query_name, deleted_data):
            self.inner_handler.on_result_deleted(query_name, deleted_data)
```

### 6.4 Composite Handler

```python
class CompositeNotificationHandler(BaseDrasiNotificationHandler):
    """Handler that delegates to multiple handlers.

    Notifications are sent to all handlers in registration order.
    If any handler raises an exception, it's logged and others continue.

    Args:
        handlers: List of handlers to delegate to
    """

    def __init__(self, handlers: list[DrasiNotificationHandler]):
        self.handlers = handlers

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        for handler in self.handlers:
            try:
                handler.on_result_added(query_name, added_data)
            except Exception as e:
                # Log and continue to next handler
                logging.error(f"Handler {handler} failed: {e}", exc_info=e)

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        for handler in self.handlers:
            try:
                handler.on_result_updated(query_name, updated_data)
            except Exception as e:
                logging.error(f"Handler {handler} failed: {e}", exc_info=e)

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        for handler in self.handlers:
            try:
                handler.on_result_deleted(query_name, deleted_data)
            except Exception as e:
                logging.error(f"Handler {handler} failed: {e}", exc_info=e)
```

---

## 7. Error Handling Specifications

### 7.1 Error Handling Contract

**Guarantees**:
1. Handler exceptions are caught and logged
2. One handler's failure doesn't affect others
3. Notification processing continues after errors
4. Errors are reported via `on_notification_error` if implemented

**Exception Propagation**:
```python
def _invoke_handler_safely(
    handler: DrasiNotificationHandler,
    method_name: str,
    query_name: str,
    data: dict
) -> None:
    """Safely invoke handler method with error handling.

    Args:
        handler: Handler instance
        method_name: Name of method to invoke
        query_name: Query name for context
        data: Notification data
    """
    try:
        method = getattr(handler, method_name)
        method(query_name, data)
    except Exception as e:
        # Log the error
        logging.error(
            f"Error in {handler}.{method_name} for {query_name}: {e}",
            exc_info=e
        )

        # Notify via error handler if available
        try:
            if hasattr(handler, 'on_notification_error'):
                handler.on_notification_error(query_name, e)
        except Exception as error_handler_error:
            # Error handler itself failed - only log
            logging.error(
                f"Error handler failed: {error_handler_error}",
                exc_info=error_handler_error
            )
```

### 7.2 Error Context

```python
from typing import TypedDict

class NotificationErrorContext(TypedDict):
    """Context information for notification errors."""
    query_name: str
    change_type: str
    handler_name: str
    error_type: str
    error_message: str
    notification_data: dict

def create_error_context(
    query_name: str,
    change_type: str,
    handler: DrasiNotificationHandler,
    error: Exception,
    data: dict
) -> NotificationErrorContext:
    """Create error context for logging and debugging."""
    return NotificationErrorContext(
        query_name=query_name,
        change_type=change_type,
        handler_name=handler.get_handler_name() if hasattr(handler, 'get_handler_name') else str(handler),
        error_type=type(error).__name__,
        error_message=str(error),
        notification_data=data
    )
```

---

## 8. Integration with LangChain Callbacks

### 8.1 LangChain Callback Adapter

```python
from langchain_core.callbacks import BaseCallbackHandler

class LangChainCallbackAdapter(BaseCallbackHandler):
    """Adapter to use Drasi handlers with LangChain callbacks.

    This allows Drasi notifications to trigger LangChain callback events.
    """

    def __init__(self, drasi_handler: DrasiNotificationHandler):
        super().__init__()
        self.drasi_handler = drasi_handler

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        """Called when tool starts - could trigger query read."""
        pass

    def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when tool ends - parse output for notifications."""
        # Parse tool output and invoke drasi_handler if it's a notification
        pass

    def on_tool_error(self, error: Exception, **kwargs) -> None:
        """Called on tool error."""
        if hasattr(self.drasi_handler, 'on_notification_error'):
            self.drasi_handler.on_notification_error("unknown", error)
```

### 8.2 Bidirectional Integration

```python
class DrasiLangChainHandler(BaseDrasiNotificationHandler):
    """Handler that also triggers LangChain callbacks.

    Args:
        langchain_callbacks: List of LangChain callback handlers
    """

    def __init__(self, langchain_callbacks: list[BaseCallbackHandler] | None = None):
        self.langchain_callbacks = langchain_callbacks or []

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        # Trigger LangChain on_text event
        for callback in self.langchain_callbacks:
            callback.on_text(
                f"Drasi notification: {query_name} added {added_data}",
                color="green"
            )

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        for callback in self.langchain_callbacks:
            callback.on_text(
                f"Drasi notification: {query_name} updated {updated_data}",
                color="yellow"
            )

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        for callback in self.langchain_callbacks:
            callback.on_text(
                f"Drasi notification: {query_name} deleted {deleted_data}",
                color="red"
            )
```

---

## 9. Usage Examples

### 9.1 Class-Based Handler

```python
class OrderNotificationHandler(BaseDrasiNotificationHandler):
    """Custom handler for order query notifications."""

    def __init__(self, order_service):
        self.order_service = order_service

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        if query_name == "active-orders":
            order_id = added_data.get("orderId")
            self.order_service.notify_new_order(order_id)

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        if query_name == "active-orders":
            order_id = updated_data.get("orderId")
            status = updated_data.get("status")
            self.order_service.update_order_status(order_id, status)

# Usage
handler = OrderNotificationHandler(order_service)
tool = create_drasi_tool(config, [handler])
```

### 9.2 Function-Based Handler

```python
def handle_freezer_alert(query_name: str, data: dict) -> None:
    if data.get("temperature", 0) > 35:
        send_alert(f"Critical: Freezer {data['freezerId']} at {data['temperature']}°F")

handler = create_simple_handler(on_added=handle_freezer_alert)
tool = create_drasi_tool(config, [handler])
```

### 9.3 Composite Handler Pattern

```python
# Create multiple specialized handlers
log_handler = LoggingNotificationHandler()
queue_handler = QueueNotificationHandler()
custom_handler = MyCustomHandler()

# Combine them
composite = CompositeNotificationHandler([
    log_handler,
    queue_handler,
    custom_handler
])

# Use composite handler
tool = create_drasi_tool(config, [composite])
```

### 9.4 Filtered Handler

```python
# Only handle specific queries
def is_critical_query(query_name: str) -> bool:
    return query_name in ["critical-alerts", "system-errors"]

# Only handle high-value data
def is_high_value(data: dict) -> bool:
    return data.get("priority") == "high"

inner_handler = MyHandler()
filtered_handler = FilteringNotificationHandler(
    inner_handler,
    query_filter=is_critical_query,
    data_filter=is_high_value
)

tool = create_drasi_tool(config, [filtered_handler])
```

---

## 10. Testing Callbacks

### 10.1 Mock Handler for Testing

```python
class MockNotificationHandler(BaseDrasiNotificationHandler):
    """Mock handler for testing.

    Tracks all calls for assertion in tests.
    """

    def __init__(self):
        self.added_calls: list[tuple[str, dict]] = []
        self.updated_calls: list[tuple[str, dict]] = []
        self.deleted_calls: list[tuple[str, dict]] = []
        self.error_calls: list[tuple[str, Exception]] = []

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        self.added_calls.append((query_name, added_data))

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        self.updated_calls.append((query_name, updated_data))

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        self.deleted_calls.append((query_name, deleted_data))

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        self.error_calls.append((query_name, error))

    def reset(self) -> None:
        """Reset all tracked calls."""
        self.added_calls.clear()
        self.updated_calls.clear()
        self.deleted_calls.clear()
        self.error_calls.clear()
```

### 10.2 Test Example

```python
import pytest
from langchain_drasi import create_drasi_tool, MCPConnectionConfig

def test_notification_handler():
    """Test that handler receives notifications."""
    mock_handler = MockNotificationHandler()

    config = MCPConnectionConfig(
        server_command="python",
        server_args=["test_server.py"]
    )

    tool = create_drasi_tool(config, [mock_handler])

    # Simulate notification
    # (In real test, this would come from MCP server)
    _simulate_notification(tool, "added", "test-query", {"id": 1})

    # Assert handler was called
    assert len(mock_handler.added_calls) == 1
    assert mock_handler.added_calls[0] == ("test-query", {"id": 1})
```

---

## 11. Performance Considerations

### 11.1 Handler Performance Guidelines

**Recommendations**:
1. Keep handlers lightweight - offload heavy processing
2. Use async handlers for I/O operations
3. Avoid blocking operations in handlers
4. Use queues for decoupling receipt from processing
5. Implement timeouts for external calls

**Example - Async with Timeout**:
```python
import asyncio

class TimeoutAsyncHandler(AsyncBaseDrasiNotificationHandler):
    """Handler with timeout protection."""

    async def on_result_added(self, query_name: str, added_data: dict) -> None:
        try:
            await asyncio.wait_for(
                self._process_added(query_name, added_data),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logging.warning(f"Handler timeout for {query_name}")

    async def _process_added(self, query_name: str, data: dict) -> None:
        # Potentially slow async operation
        await external_api.notify(data)
```

---

## 12. Contract Summary

### 12.1 Functional Requirements Mapping

| Requirement | Contract Element | Implementation |
|-------------|------------------|----------------|
| FR-010 | `DrasiNotificationHandler` | LangChain-compatible protocol |
| FR-011 | Handler invocation | Called on MCP notifications |
| FR-012 | Constructor parameters | Handlers provided at tool creation |
| FR-018 | Error handling | Exceptions logged, don't interrupt |

### 12.2 Guarantees

1. **Type Safety**: Full type hints, protocol checking
2. **Error Resilience**: Handler errors isolated and logged
3. **Flexibility**: Multiple implementation patterns supported
4. **Compatibility**: Works with LangChain callback system
5. **Testability**: Mock handlers for testing

---

**Document Status**: Complete
**Last Updated**: 2025-10-01
**Related Documents**:
- `/Users/danielgerlag/dev/learn/langchain-ext/langchain-drasi/specs/001-build-a-library/spec.md`
- `/Users/danielgerlag/dev/learn/langchain-ext/langchain-drasi/specs/001-build-a-library/contracts/python-api.md`
- `/Users/danielgerlag/dev/learn/langchain-ext/langchain-drasi/specs/001-build-a-library/contracts/mcp-protocol.md`
