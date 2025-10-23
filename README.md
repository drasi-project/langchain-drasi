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

This project uses [uv](https://docs.astral.sh/uv/) for fast dependency management.

```bash
# Clone the repository
git clone https://github.com/drasi-project/langchain-drasi.git
cd langchain-drasi

# Install with development dependencies
uv sync

# Or install without dev dependencies
make install
```

## Quick Start

```python
from langchain_drasi import create_drasi_tool, MCPConnectionConfig, ConsoleHandler

# Configure HTTP connection to remote Drasi MCP server
config = MCPConnectionConfig(
    server_url="http://localhost:8083",  # Default Drasi MCP server URL
    headers={"Authorization": "Bearer your-token"},  # Optional authentication
    timeout=30.0
)

# Create notification handler
handler = ConsoleHandler()

# Create the tool
tool = create_drasi_tool(
    mcp_config=config,
    notification_handlers=[handler]
)

# Use with LangChain agents (requires langchain <1.0)
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import AzureChatOpenAI

llm = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    temperature=0
)

prompt = hub.pull("hwchase17/react-chat")
agent = create_react_agent(llm, [tool], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[tool])

# Agent can now discover and read Drasi queries
result = await agent_executor.ainvoke({
    "input": "What queries are available?"
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
await tool.subscribe("hot-freezers")
# Notifications routed to registered handlers
```

### 🎯 Built-in Handlers

Five ready-to-use notification handlers:

- **ConsoleHandler**: Prints notifications to stdout with formatting
- **LoggingHandler**: Logs notifications using Python logging
- **MemoryHandler**: Stores notifications in memory for analysis
- **LangChainMemoryHandler**: Automatically injects notifications into LangChain conversation memory
- **LangGraphMemoryHandler**: Automatically injects notifications into LangGraph checkpoints

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

### Chat Examples ([examples/chat/](examples/chat/))

Interactive ReAct agents demonstrating automatic notification memory:
- **langchain_react.py**: LangChain ReAct agent with `LangChainMemoryHandler`
- **langgraph_react.py**: LangGraph ReAct agent with `LangGraphMemoryHandler`
- **Use case**: Freezer temperature monitoring with real-time alerts

### Terminator Game ([examples/terminator/](examples/terminator/))

Complex LangGraph agent demonstrating custom workflows and notification handling:
- **Custom LangGraph state machine** that integrates Drasi tool
- **Custom `SensorHandler`** for processing real-time player positions
- **Use case**: AI agent hunts players using Drasi continuous queries

### Simple Example ([examples/simple_example.py](examples/simple_example.py))

Basic usage demonstrating core functionality

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

Prints notifications to console with formatted output.

```python
from langchain_drasi import ConsoleHandler

handler = ConsoleHandler()

# Use with create_drasi_tool
tool = create_drasi_tool(
    mcp_config=config,
    notification_handlers=[handler]
)
```

#### `MemoryHandler`

Stores notifications in memory.

```python
from langchain_drasi import MemoryHandler

handler = MemoryHandler(max_size=100)

# Retrieve notifications
all_notifs = handler.get_all()
freezer_notifs = handler.get_by_query("freezerx")
added_events = handler.get_by_type("added")
```

#### `LangChainMemoryHandler`

Automatically injects notifications into LangChain conversation memory as system messages.

```python
from langchain.memory import ConversationBufferMemory
from langchain_drasi import LangChainMemoryHandler

memory = ConversationBufferMemory(
    memory_key="chat_history",
    input_key="input",
    output_key="output",
)

handler = LangChainMemoryHandler(memory)

# Notifications are automatically added to conversation memory
tool = create_drasi_tool(
    mcp_config=config,
    notification_handlers=[handler]
)
```

See [examples/chat/langchain_react.py](examples/chat/langchain_react.py) for a complete example.

#### `LangGraphMemoryHandler`

Automatically injects notifications into LangGraph checkpoints as system messages.

```python
from langgraph.checkpoint.memory import MemorySaver
from langchain_drasi import LangGraphMemoryHandler

memory = MemorySaver()
thread_id = "my-conversation"

handler = LangGraphMemoryHandler(memory, thread_id)

# Create agent with wrapped checkpointer
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=[drasi_tool],
    checkpointer=handler.checkpointer,  # Use wrapped checkpointer
)
```

See [examples/chat/langgraph_react.py](examples/chat/langgraph_react.py) for a complete example.

## Development

### Running Tests

```bash
# Run all tests (including integration)
make test

# Run tests excluding integration tests
make test-fast

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run contract tests only
make test-contract
```

### Code Quality

```bash
# Format code
make format

# Run linting checks (ruff + mypy + pyright)
make lint

# Run type checking only
make typecheck
```

### Available Make Targets

Run `make help` to see all available commands.

## Requirements

- Python 3.11+
- LangChain Core >=0.1.0
- LangGraph >=0.1.0
- MCP SDK >=1.0.0
- Pydantic >=2.0.0

**Note**: Examples using LangChain's legacy APIs (agents, memory, hub) require LangChain <1.0. For LangChain 1.0+, use LangGraph-based workflows.

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/drasi-project/langchain-drasi/issues)
- **Drasi Documentation**: [drasi.io](https://drasi.io/)
- **LangChain Documentation**: [python.langchain.com](https://python.langchain.com/)
- **LangGraph Documentation**: [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/)

## Acknowledgments

- Built with [LangChain](https://www.langchain.com/)
- Powered by [Drasi](https://drasi.io/)
- Uses [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
