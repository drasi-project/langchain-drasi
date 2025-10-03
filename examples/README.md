# LangChain-Drasi Examples

This directory contains example applications demonstrating how to use `langchain-drasi` with different LangChain frameworks.

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install langchain-drasi python-dotenv langchain-openai

   # For LangGraph example
   pip install langgraph
   ```

2. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   # Drasi Server Configuration
   DRASI_SERVER_URL=https://your-drasi-server.com/api
   DRASI_API_TOKEN=your-api-token  # Optional, if your server requires authentication

   # For OpenAI
   OPENAI_API_KEY=your-api-key
   OPENAI_MODEL=gpt-4

   # OR for Azure OpenAI
   AZURE_OPENAI_API_KEY=your-api-key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

3. **Have a Drasi MCP server running:**
   The examples connect to a Drasi MCP server over HTTP/HTTPS using the SSE (Server-Sent Events) protocol. **You must have a running Drasi MCP server** accessible at the configured URL.

   - Default URL: `http://localhost:8083`
   - Update `DRASI_SERVER_URL` in your `.env` file to point to your MCP SSE endpoint
   - The URL should be the SSE endpoint of your Drasi MCP server
   - Without a properly running MCP SSE server, the examples will fail with connection errors

   **Common connection errors:**
   - `400 Bad Request` or `Invalid or missing session ID` - The server at this URL is not an MCP SSE server
   - `Connection refused` - No server is running at this address
   - Ensure you're pointing to the correct MCP SSE endpoint URL

## Examples

### 0. Mock Example (No Server Required)

**File:** `langgraph_mock_example.py`

Demonstrates the LangGraph workflow using a mock Drasi tool, **without requiring a running Drasi MCP server**. Perfect for testing the agent structure and LLM integration.

**Run:**
```bash
python examples/langgraph_mock_example.py
```

**What it does:**
1. Creates a LangGraph workflow with a mock Drasi tool
2. Demonstrates tool calling and state management
3. Shows how the agent interacts with query operations

### 1. Vanilla LangChain Example

**File:** `vanilla_langchain.py`

Demonstrates using `DrasiTool` with a basic LangChain ReAct agent.

**Features:**
- Discovers available Drasi queries
- Reads query results
- Subscribes to real-time updates
- Uses `ConsoleHandler` to display notifications

**Run:**
```bash
python examples/vanilla_langchain.py
```

**What it does:**
1. Creates a ReAct agent with access to DrasiTool
2. Asks the agent to discover available queries
3. Reads results from a specific query
4. Subscribes to query updates
5. Listens for notifications for 60 seconds

### 2. LangGraph Example

**File:** `langgraph_example.py`

Demonstrates using `DrasiTool` with LangGraph for stateful agent workflows.

**Features:**
- Stateful conversation flow with LangGraph
- Tool execution with LangGraph's built-in tool executor
- Uses `MemoryHandler` to track and analyze notifications
- Shows notification statistics

**Run:**
```bash
python examples/langgraph_example.py
```

**What it does:**
1. Creates a LangGraph workflow with DrasiTool
2. Executes a multi-turn conversation about Drasi queries
3. Tracks all notifications in memory
4. Displays notification statistics
5. Continuously listens for new notifications

## Customization

### Using Different Notification Handlers

Both examples can be customized with different notification handlers:

**LoggingHandler** - Logs notifications using Python's logging:
```python
from langchain_drasi.handlers import LoggingHandler

handler = LoggingHandler(logger_name="my.logger", log_level=logging.INFO)
tool = create_drasi_tool(mcp_config=config, notification_handlers=[handler])
```

**ConsoleHandler** - Prints to console:
```python
from langchain_drasi.handlers import ConsoleHandler

handler = ConsoleHandler(include_timestamp=True, pretty_print=True)
tool = create_drasi_tool(mcp_config=config, notification_handlers=[handler])
```

**MemoryHandler** - Stores in memory for analysis:
```python
from langchain_drasi.handlers import MemoryHandler

handler = MemoryHandler(max_size=1000)
tool = create_drasi_tool(mcp_config=config, notification_handlers=[handler])

# Later, retrieve notifications
all_notifs = handler.get_all()
freezer_notifs = handler.get_by_query("freezerx")
```

**Custom Handler** - Implement your own:
```python
from langchain_drasi import BaseDrasiNotificationHandler

class MyHandler(BaseDrasiNotificationHandler):
    def on_result_added(self, query_name: str, added_data: dict) -> None:
        # Custom logic here
        print(f"New result in {query_name}: {added_data}")
```

### Configuring MCP Connection

Update the `MCPConnectionConfig` to match your Drasi server:

```python
from langchain_drasi import MCPConnectionConfig

config = MCPConnectionConfig(
    server_url="https://your-drasi-server.com/api",  # Your Drasi server URL
    headers={"Authorization": "Bearer token"},        # Optional authentication headers
    timeout=30.0,                                     # Request timeout in seconds
)
```

## Troubleshooting

**Connection errors:**
- Verify your Drasi MCP server is running and accessible
- Check `DRASI_SERVER_URL` is correct in your `.env` file
- Verify authentication headers if your server requires them
- Check network connectivity and firewall rules

**LLM errors:**
- Verify API keys are set correctly in `.env`
- Check your API quota/limits
- Ensure the model name is correct

**Import errors:**
- Make sure all dependencies are installed
- For LangGraph example, install `langgraph`
- Install the library: `pip install -e .` from project root

## Next Steps

- Explore the [API documentation](../README.md)
- Create custom notification handlers
- Build your own agent workflows
- Integrate with other LangChain components
