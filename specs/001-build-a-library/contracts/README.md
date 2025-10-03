# LangChain-Drasi API Contracts

**Feature**: LangChain Extension for Drasi Query Integration
**Version**: 1.0
**Created**: 2025-10-01

---

## Overview

This directory contains comprehensive API contract definitions for the LangChain-Drasi library. These contracts define the public interfaces, protocols, and message formats for integrating Drasi continuous queries with LangChain agents.

---

## Contract Documents

### 1. Python API Contracts
**File**: [`python-api.md`](./python-api.md)

Defines the public Python API including:
- **DrasiTool Class**: Main LangChain tool for accessing Drasi queries
- **Configuration Classes**: MCP connection config, reconnection policies
- **Callback Protocols**: Protocol-based notification handler interfaces
- **Data Transfer Objects**: TypedDict definitions for query info, results, notifications
- **Exception Types**: Custom exception hierarchy
- **Factory Functions**: Convenience functions for creating tools and handlers
- **Type Aliases**: Common type definitions and constants

**Key Features**:
- Python 3.13+ type hints with modern syntax (PEP 604, 585)
- Protocol classes for structural typing
- Pydantic models for runtime validation
- LangChain BaseTool integration

### 2. MCP Protocol Contracts
**File**: [`mcp-protocol.md`](./mcp-protocol.md)

Defines JSON schemas and message formats for MCP interactions:
- **Resource Discovery**: List resources request/response schemas
- **Resource Reading**: Read resource request/response schemas
- **Subscriptions**: Subscribe/unsubscribe request/response schemas
- **Notifications**: Added/updated/deleted notification formats
- **Error Responses**: JSON-RPC error response schemas
- **Connection Lifecycle**: Initialization, subscription, and reconnection flows
- **Validation Rules**: URI format, query name, notification method patterns

**Key Features**:
- JSON Schema definitions (draft-07)
- JSON-RPC 2.0 compliance
- MCP specification 2025-06-18 conformance
- Complete example message flows

### 3. Callback Interface Specifications
**File**: [`callbacks.md`](./callbacks.md)

Defines callback interfaces for handling query change notifications:
- **Notification Handler Protocol**: Protocol for implementing callbacks
- **Base Handler Classes**: Abstract base classes for inheritance
- **Function-Based Handlers**: Simple function-to-handler factories
- **Async Support**: Async handler protocols and adapters
- **Built-in Implementations**: Logging, queue, filtering, composite handlers
- **Error Handling**: Exception handling contracts and guarantees
- **LangChain Integration**: Adapters for LangChain callback system
- **Testing Support**: Mock handlers for testing

**Key Features**:
- Protocol-based (duck typing) and class-based approaches
- Sync and async handler support
- Flexible composition patterns
- Error resilience guarantees

---

## Contract Organization

```
contracts/
├── README.md              # This file - overview and navigation
├── python-api.md          # Public Python API contracts
├── mcp-protocol.md        # MCP protocol message schemas
└── callbacks.md           # Callback interface specifications
```

---

## Quick Reference

### Public API Entry Points

```python
# Main tool creation
from langchain_drasi import create_drasi_tool, MCPConnectionConfig

config = MCPConnectionConfig(
    server_command="python",
    server_args=["drasi_server.py"]
)

tool = create_drasi_tool(config, notification_handlers=[...])
```

### Notification Handler

```python
# Protocol-based (duck typing)
from langchain_drasi import DrasiNotificationHandler

class MyHandler:
    def on_result_added(self, query_name: str, added_data: dict) -> None:
        ...

# Class-based (inheritance)
from langchain_drasi import BaseDrasiNotificationHandler

class MyHandler(BaseDrasiNotificationHandler):
    def on_result_added(self, query_name: str, added_data: dict) -> None:
        ...
```

### MCP Messages

```json
// List queries
{"jsonrpc":"2.0","id":1,"method":"resources/list","params":{}}

// Read query
{"jsonrpc":"2.0","id":2,"method":"resources/read","params":{"uri":"drasi://query/orders"}}

// Subscribe to query
{"jsonrpc":"2.0","id":3,"method":"resources/subscribe","params":{"uri":"drasi://query/orders"}}

// Notification from server
{"jsonrpc":"2.0","method":"notifications/orders/added","params":{...}}
```

---

## Functional Requirements Coverage

| Requirement | Contract | Location |
|-------------|----------|----------|
| FR-001: Query discovery | `discover_queries()` | python-api.md §2.1 |
| FR-002: Read query results | `read_query()` | python-api.md §2.1 |
| FR-003: Subscribe to changes | `subscribe()` | python-api.md §2.1 |
| FR-004: MCP communication | Resource schemas | mcp-protocol.md §2-4 |
| FR-005: URI format | Validation rules | mcp-protocol.md §8.1 |
| FR-007: Change types | Notification schemas | mcp-protocol.md §5 |
| FR-010-012: Callbacks | Handler protocols | callbacks.md §2-3 |
| FR-017: Reconnection | `ReconnectPolicy` | python-api.md §3.1 |
| FR-018: Error handling | Error handling spec | callbacks.md §7 |

---

## Data Flow Summary

### 1. Query Discovery Flow
```
Agent → DrasiTool.discover_queries()
     → MCP: resources/list
     → Response: List[QueryInfo]
```

### 2. Query Read Flow
```
Agent → DrasiTool.read_query("orders")
     → MCP: resources/read(uri="drasi://query/orders")
     → Response: QueryResult
```

### 3. Subscription Flow
```
Agent → DrasiTool.subscribe("orders")
     → MCP: resources/subscribe(uri="drasi://query/orders")
     → MCP Server emits: notifications/orders/added
     → NotificationHandler.on_result_added(...)
```

---

## Type Safety

All contracts use Python 3.13+ type hints:

- **Union types**: `str | int | None` (PEP 604)
- **Generic collections**: `list[dict]`, `dict[str, int]` (PEP 585)
- **Protocols**: Structural typing with `@runtime_checkable`
- **TypedDict**: Structured dictionaries with type hints
- **Pydantic**: Runtime validation for configuration

---

## Error Handling Contracts

### Exception Hierarchy
```
DrasiError (base)
├── MCPConnectionError
├── QueryNotFoundError
├── SubscriptionError
└── NotificationProcessingError
```

### Error Guarantees
1. Callback exceptions are logged, not propagated
2. One handler's failure doesn't affect others
3. Notification processing continues after errors
4. Errors reported via `on_notification_error` when implemented

---

## Versioning and Stability

- **API Stability**: Public API follows semantic versioning
- **Breaking Changes**: Only in major versions
- **Deprecation**: Minimum 2 minor versions notice
- **Python Support**: 3.11+ (3.13+ recommended)

### Dependency Compatibility
- **LangChain Core**: >= 0.3.0
- **MCP SDK**: >= 1.7.0
- **Pydantic**: >= 2.0.0

---

## Implementation Guidelines

### For Library Developers
1. Implement all contracts in `python-api.md`
2. Follow MCP message schemas in `mcp-protocol.md`
3. Support all callback patterns in `callbacks.md`
4. Ensure error handling follows specifications
5. Validate all inputs per validation rules

### For Library Users
1. Use `create_drasi_tool()` factory function
2. Implement `DrasiNotificationHandler` protocol OR extend `BaseDrasiNotificationHandler`
3. Configure `MCPConnectionConfig` with server details
4. Handle errors in callbacks (library won't interrupt)
5. Follow URI format: `drasi://query/{query-name}`

---

## Testing Contracts

All contracts are designed to be testable:

- **Contract Tests**: Verify protocol compliance (see `mcp-protocol.md` §13)
- **Mock Handlers**: Use `MockNotificationHandler` for testing (see `callbacks.md` §10)
- **Type Checking**: Run `mypy` for static type validation
- **Schema Validation**: Validate MCP messages against JSON schemas

---

## Related Documentation

- **Feature Specification**: [`../spec.md`](../spec.md)
- **Data Model**: [`../data-model.md`](../data-model.md)
- **Technical Research**: [`../research.md`](../research.md)
- **Implementation Plan**: [`../plan.md`](../plan.md)

---

## Questions and Clarifications

For questions about these contracts:

1. **API Usage**: See examples in each contract document
2. **Protocol Details**: Refer to MCP specification 2025-06-18
3. **LangChain Integration**: See LangChain Core documentation
4. **Implementation**: Follow the implementation plan in `../plan.md`

---

**Last Updated**: 2025-10-01
**Contract Version**: 1.0
**Status**: Complete
