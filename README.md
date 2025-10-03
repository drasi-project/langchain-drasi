# LangChain-Drasi

A LangChain extension library for integrating Drasi continuous queries into AI agent workflows via the Model Context Protocol (MCP).

## Overview

`langchain-drasi` provides a seamless way to connect LangChain agents to Drasi continuous queries, enabling AI agents to:

- **Discover** available Drasi queries
- **Read** current query results
- **Subscribe** to real-time query updates
- **React** to changes via notification handlers

## Installation

```bash
pip install langchain-drasi
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/your-org/langchain-drasi.git
cd langchain-drasi

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
from langchain_drasi import create_drasi_tool, MCPConnectionConfig
from langchain_drasi.handlers import ConsoleHandler

# Configure HTTP connection to remote Drasi MCP server
config = MCPConnectionConfig(
    server_url="https://your-drasi-server.com/api",
    headers={"Authorization": "Bearer your-token"},  # Optional authentication
    timeout=30.0
)

# Create notification handler
handler = ConsoleHandler(include_timestamp=True, pretty_print=True)

# Create the tool
tool = create_drasi_tool(
    mcp_config=config,
    notification_handlers=[handler]
)

# Use with LangChain agents
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI()
agent = create_react_agent(llm, [tool], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[tool])

# Agent can now discover and read Drasi queries
result = await agent_executor.ainvoke({
    "input": "What active orders are there?"
})
```

## Features

### 🔍 Query Discovery

Agents can discover available Drasi queries automatically:

```python
queries = await tool.discover_queries()
# Returns: [QueryInfo, QueryInfo, ...]
```

### 📖 Query Reading

Read current results from any Drasi query:

```python
result = await tool.read_query("active-orders")
# Returns: QueryResult with current data
```

### 🔔 Real-time Subscriptions

Subscribe to query updates and handle changes:

```python
await tool.subscribe("freezerx")
# Notifications routed to registered handlers
```

### 🎯 Built-in Handlers

Three ready-to-use notification handlers:

- **LoggingHandler**: Logs notifications using Python logging
- **ConsoleHandler**: Prints notifications to stdout
- **MemoryHandler**: Stores notifications in memory for analysis

### 🛠️ Custom Handlers

Implement your own notification handlers:

```python
from langchain_drasi import BaseDrasiNotificationHandler

class MyHandler(BaseDrasiNotificationHandler):
    def on_result_added(self, query_name: str, added_data: dict) -> None:
        # Custom logic for new results
        self.save_to_database(query_name, added_data)

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        # Custom logic for updates
        self.update_cache(query_name, updated_data)

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        # Custom logic for deletions
        self.remove_from_cache(query_name, deleted_data)
```

## Architecture

### Core Components

- **DrasiTool**: LangChain `BaseTool` implementation for agent integration
- **MCPClient**: Wrapper around MCP SDK for Drasi server communication
- **NotificationRouter**: Parses Drasi's custom notification format and routes to handlers
- **Callback Protocols**: Type-safe interfaces for notification handling

### Data Models

- **QueryInfo**: Metadata about available queries
- **QueryResult**: Query execution results
- **ChangeNotification**: Parsed notification events
- **ChangeType**: Enum for added/updated/deleted events

### Configuration

- **MCPConnectionConfig**: MCP server connection settings
- **ReconnectPolicy**: Connection retry and backoff configuration

## Examples

See the [examples/](examples/) directory for complete working examples:

- **vanilla_langchain.py**: Basic ReAct agent with Drasi
- **langgraph_example.py**: Stateful LangGraph workflow with Drasi

## API Reference

### Main Functions

#### `create_drasi_tool()`

Factory function to create a DrasiTool instance.

**Parameters:**
- `mcp_config` (MCPConnectionConfig): MCP connection configuration
- `notification_handlers` (list[DrasiNotificationHandler], optional): Notification handlers

**Returns:** DrasiTool instance

### Configuration

#### `MCPConnectionConfig`

Pydantic model for HTTP-based MCP server connection configuration.

**Fields:**
- `server_url` (str): HTTP/HTTPS URL of the Drasi MCP server
- `headers` (dict[str, str], optional): HTTP headers for authentication
- `timeout` (float): Request timeout in seconds (default: 30.0)
- `reconnect_policy` (ReconnectPolicy): Reconnection settings

### Handlers

#### `LoggingHandler`

Logs notifications using Python's logging framework.

```python
handler = LoggingHandler(
    logger_name="drasi.notifications",
    log_level=logging.INFO
)
```

#### `ConsoleHandler`

Prints notifications to console.

```python
handler = ConsoleHandler(
    include_timestamp=True,
    pretty_print=True
)
```

#### `MemoryHandler`

Stores notifications in memory.

```python
handler = MemoryHandler(max_size=100)

# Retrieve notifications
all_notifs = handler.get_all()
freezer_notifs = handler.get_by_query("freezerx")
added_events = handler.get_by_type("added")
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run contract tests only
pytest tests/contract/

# Run with coverage
pytest --cov=langchain_drasi --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Requirements

- Python 3.11+
- LangChain Core 0.1.0+
- MCP SDK 1.0.0+
- Pydantic 2.0.0+

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/langchain-drasi/issues)
- **Documentation**: [Full docs](https://your-org.github.io/langchain-drasi/)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/langchain-drasi/discussions)

## Acknowledgments

- Built with [LangChain](https://www.langchain.com/)
- Powered by [Drasi](https://drasi.io/)
- Uses [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
