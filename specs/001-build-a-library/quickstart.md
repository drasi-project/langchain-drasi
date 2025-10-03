# LangChain-Drasi Quickstart Guide

Welcome to LangChain-Drasi! This guide will help you get started with integrating Drasi continuous queries into your LangChain applications.

## What is LangChain-Drasi?

LangChain-Drasi is a LangChain extension that enables AI agents to access and react to real-time data from Drasi continuous queries. It provides:

- **Real-time data access**: Read current query results on-demand
- **Change notifications**: Subscribe to query changes (added, updated, deleted)
- **Seamless integration**: Works with existing LangChain tools and agents
- **Reactive agents**: Build agents that respond to data changes automatically

---

## Prerequisites

### Required Software
- **Python**: 3.11 or higher (3.13+ recommended)
- **Drasi MCP Server**: Running and accessible
- **Azure OpenAI**: Account and API credentials (for examples)

### Python Dependencies
```bash
pip install langchain-drasi langchain-core langchain-openai
```

### Environment Setup

Create a `.env` file in your project directory:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# MCP Server Configuration
MCP_SERVER_COMMAND=python
MCP_SERVER_ARGS=path/to/drasi_mcp_server.py
```

---

## Installation

Install the LangChain-Drasi library:

```bash
pip install langchain-drasi
```

For development or running examples:

```bash
# Clone the repository
git clone https://github.com/your-org/langchain-drasi.git
cd langchain-drasi

# Install with examples
pip install -e ".[examples]"
```

---

## Basic Usage

### 1. Configure MCP Connection

First, set up the connection to your Drasi MCP server:

```python
from langchain_drasi import MCPConnectionConfig, ReconnectPolicy

# Basic configuration
config = MCPConnectionConfig(
    server_command="python",
    server_args=["drasi_mcp_server.py"]
)

# Advanced configuration with reconnection policy
config = MCPConnectionConfig(
    server_command="python",
    server_args=["drasi_mcp_server.py"],
    reconnect_policy=ReconnectPolicy(
        enabled=True,
        max_retries=5,
        retry_delay=1.0,
        backoff_multiplier=2.0,
        max_delay=60.0
    ),
    timeout=30
)
```

### 2. Discover Available Queries

Discover what queries are available from your Drasi MCP server:

```python
from langchain_drasi import create_drasi_tool
import asyncio

# Create the tool
tool = create_drasi_tool(mcp_config=config)

# Discover queries
async def discover():
    queries = await tool.discover_queries()
    for query in queries:
        print(f"Query: {query['name']}")
        print(f"  Description: {query['description']}")
        print(f"  URI: {query['uri']}")
        print()

asyncio.run(discover())
```

**Output:**
```
Query: active-orders
  Description: Continuous query tracking all active customer orders
  URI: drasi://query/active-orders

Query: freezerx
  Description: Freezer temperature alert for when it goes above 32 degrees
  URI: drasi://query/freezerx
```

### 3. Read Query Results

Read the current result set of a query:

```python
async def read_query():
    result = await tool.read_query("freezerx")
    print(f"Query: {result['query_name']}")
    print(f"Data: {result['data']}")

asyncio.run(read_query())
```

**Output:**
```
Query: freezerx
Data: [
  {'id': 1, 'temp': 37},
  {'id': 3, 'temp': 41}
]
```

### 4. Subscribe to Query Changes

Create a notification handler to respond to changes:

```python
from langchain_drasi import BaseDrasiNotificationHandler

class FreezerAlertHandler(BaseDrasiNotificationHandler):
    """Handle freezer temperature alerts."""

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        if query_name == "freezerx":
            freezer_id = added_data.get("id")
            temp = added_data.get("temp")
            print(f"ALERT: Freezer {freezer_id} exceeded threshold at {temp}°F!")

    def on_result_updated(self, query_name: str, updated_data: dict) -> None:
        if query_name == "freezerx":
            freezer_id = updated_data.get("id")
            temp = updated_data.get("temp")
            print(f"UPDATE: Freezer {freezer_id} now at {temp}°F")

    def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
        if query_name == "freezerx":
            freezer_id = deleted_data.get("id")
            print(f"RESOLVED: Freezer {freezer_id} back to normal")

# Create tool with handler
handler = FreezerAlertHandler()
tool = create_drasi_tool(
    mcp_config=config,
    notification_handlers=[handler]
)

# Subscribe to changes
async def subscribe():
    await tool.subscribe("freezerx")
    print("Subscribed to freezerx query changes")

    # Keep running to receive notifications
    await asyncio.sleep(3600)  # Run for 1 hour

asyncio.run(subscribe())
```

### 5. Handle Notifications with Callbacks

For simpler use cases, use function-based handlers:

```python
from langchain_drasi import create_simple_handler

def handle_added(query_name: str, data: dict) -> None:
    print(f"New data in {query_name}: {data}")

def handle_updated(query_name: str, data: dict) -> None:
    print(f"Updated data in {query_name}: {data}")

def handle_deleted(query_name: str, data: dict) -> None:
    print(f"Deleted data from {query_name}: {data}")

def handle_error(query_name: str, error: Exception) -> None:
    print(f"Error in {query_name}: {error}")

# Create handler from functions
handler = create_simple_handler(
    on_added=handle_added,
    on_updated=handle_updated,
    on_deleted=handle_deleted,
    on_error=handle_error
)

tool = create_drasi_tool(config, [handler])
```

### 6. Use with LangChain Agents

Integrate the Drasi tool with a LangChain agent:

```python
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure Azure OpenAI
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0
)

# Create notification handler
class OrderHandler(BaseDrasiNotificationHandler):
    def on_result_added(self, query_name: str, added_data: dict) -> None:
        if query_name == "active-orders":
            print(f"New order received: {added_data}")

# Create Drasi tool
handler = OrderHandler()
drasi_tool = create_drasi_tool(config, [handler])

# Create agent with Drasi tool
agent = create_react_agent(
    llm,
    tools=[drasi_tool],
    state_modifier="You have access to Drasi continuous queries for real-time data."
)

# Use the agent
async def run_agent():
    # Subscribe to changes
    await drasi_tool.subscribe("active-orders")

    # Query the agent
    result = await agent.ainvoke({
        "messages": [("user", "What are the current active orders?")]
    })

    print(result["messages"][-1].content)

asyncio.run(run_agent())
```

---

## Sample Applications

The library includes comprehensive sample applications demonstrating different use cases:

### Vanilla LangChain Sample

Located in `/samples/vanilla-langchain/`

A basic example showing:
- Simple agent setup with Drasi tool
- Reading query results
- Subscribing to changes
- Handling notifications

**Run the sample:**
```bash
cd samples/vanilla-langchain
python main.py
```

### LangGraph Sample

Located in `/samples/langgraph/`

An advanced example demonstrating:
- Stateful agent workflows
- Multi-query subscriptions
- Complex notification handling
- Integration with LangGraph state management

**Run the sample:**
```bash
cd samples/langgraph
python main.py
```

---

## Common Patterns

### Pattern 1: Agent That Reacts to Data Changes

Build an agent that takes action when data changes:

```python
from langchain_drasi import BaseDrasiNotificationHandler
from langchain_openai import AzureChatOpenAI
import asyncio

class ReactiveOrderAgent(BaseDrasiNotificationHandler):
    """Agent that reacts to new orders."""

    def __init__(self, llm):
        self.llm = llm

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        if query_name == "active-orders":
            # Process new order with LLM
            order_id = added_data.get("orderId")
            customer = added_data.get("customerName")

            prompt = f"""
            New order received:
            - Order ID: {order_id}
            - Customer: {customer}
            - Details: {added_data}

            Determine if this order requires special handling and suggest next steps.
            """

            response = self.llm.invoke(prompt)
            print(f"Agent recommendation: {response.content}")

# Setup
llm = AzureChatOpenAI(...)
agent_handler = ReactiveOrderAgent(llm)
tool = create_drasi_tool(config, [agent_handler])

async def run():
    await tool.subscribe("active-orders")
    await asyncio.sleep(3600)  # Keep running

asyncio.run(run())
```

### Pattern 2: Query-Driven Workflows

Use query results to drive workflow decisions:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class WorkflowState(TypedDict):
    freezer_alerts: list
    actions_taken: list

async def check_freezers(state: WorkflowState):
    """Check for freezer alerts."""
    result = await drasi_tool.read_query("freezerx")
    state["freezer_alerts"] = result["data"]
    return state

async def take_action(state: WorkflowState):
    """Take action on alerts."""
    actions = []
    for alert in state["freezer_alerts"]:
        if alert["temp"] > 40:
            action = f"URGENT: Service freezer {alert['id']}"
        else:
            action = f"Monitor freezer {alert['id']}"
        actions.append(action)
    state["actions_taken"] = actions
    return state

# Build workflow
workflow = StateGraph(WorkflowState)
workflow.add_node("check", check_freezers)
workflow.add_node("action", take_action)
workflow.add_edge("check", "action")
workflow.add_edge("action", END)
workflow.set_entry_point("check")

app = workflow.compile()

# Run workflow
result = await app.ainvoke({"freezer_alerts": [], "actions_taken": []})
print(result["actions_taken"])
```

### Pattern 3: Error Handling and Reconnection

Implement robust error handling:

```python
from langchain_drasi import (
    MCPConnectionConfig,
    ReconnectPolicy,
    DrasiError,
    MCPConnectionError,
    QueryNotFoundError
)

# Configure automatic reconnection
config = MCPConnectionConfig(
    server_command="python",
    server_args=["drasi_mcp_server.py"],
    reconnect_policy=ReconnectPolicy(
        enabled=True,
        max_retries=10,
        retry_delay=2.0,
        backoff_multiplier=2.0,
        max_delay=120.0
    )
)

class ResilientHandler(BaseDrasiNotificationHandler):
    """Handler with error recovery."""

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        try:
            # Process notification
            self.process_data(added_data)
        except Exception as e:
            print(f"Error processing notification: {e}")
            # Error is logged but doesn't interrupt other notifications

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        print(f"Notification error for {query_name}: {error}")
        # Implement custom recovery logic
        self.attempt_recovery(query_name)

    def process_data(self, data: dict):
        # Your processing logic
        pass

    def attempt_recovery(self, query_name: str):
        # Your recovery logic
        pass

# Use the resilient handler
tool = create_drasi_tool(config, [ResilientHandler()])

async def run_with_error_handling():
    try:
        await tool.subscribe("active-orders")
    except QueryNotFoundError as e:
        print(f"Query not found: {e.query_name}")
        print(f"Available queries: {e.available_queries}")
    except MCPConnectionError as e:
        print(f"Connection failed: {e}")
        print(f"Server command: {e.server_command}")
    except DrasiError as e:
        print(f"Drasi error: {e}")

asyncio.run(run_with_error_handling())
```

### Pattern 4: Multiple Query Subscriptions

Monitor multiple queries simultaneously:

```python
from langchain_drasi import CompositeNotificationHandler, LoggingNotificationHandler

class MultiQueryHandler(BaseDrasiNotificationHandler):
    """Handle notifications from multiple queries."""

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        handlers = {
            "active-orders": self.handle_new_order,
            "freezerx": self.handle_freezer_alert,
            "inventory-low": self.handle_low_inventory
        }

        handler = handlers.get(query_name)
        if handler:
            handler(added_data)

    def handle_new_order(self, data: dict):
        print(f"New order: {data['orderId']}")

    def handle_freezer_alert(self, data: dict):
        print(f"Freezer alert: {data['id']} at {data['temp']}°F")

    def handle_low_inventory(self, data: dict):
        print(f"Low inventory: {data['item']} - {data['quantity']} remaining")

# Create composite handler with logging
multi_handler = MultiQueryHandler()
log_handler = LoggingNotificationHandler(level="INFO")
composite = CompositeNotificationHandler([multi_handler, log_handler])

tool = create_drasi_tool(config, [composite])

async def subscribe_all():
    queries = ["active-orders", "freezerx", "inventory-low"]
    for query in queries:
        await tool.subscribe(query)
        print(f"Subscribed to {query}")

    # Keep running
    await asyncio.sleep(3600)

asyncio.run(subscribe_all())
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "MCPConnectionError: Failed to connect to MCP server"

**Cause**: MCP server not running or incorrect configuration

**Solution**:
```python
# Verify server command and args
config = MCPConnectionConfig(
    server_command="python",  # Ensure correct command
    server_args=["path/to/drasi_mcp_server.py"],  # Verify path exists
    timeout=60  # Increase timeout if server startup is slow
)

# Test server manually
import subprocess
result = subprocess.run(
    ["python", "path/to/drasi_mcp_server.py"],
    capture_output=True,
    text=True
)
print(result.stdout)
print(result.stderr)
```

#### Issue: "QueryNotFoundError: Query 'xyz' not found"

**Cause**: Query doesn't exist or typo in query name

**Solution**:
```python
# List available queries
async def list_queries():
    try:
        queries = await tool.discover_queries()
        print("Available queries:")
        for q in queries:
            print(f"  - {q['name']}")
    except Exception as e:
        print(f"Error listing queries: {e}")

asyncio.run(list_queries())
```

#### Issue: Notifications not received

**Cause**: Not subscribed, connection lost, or callback error

**Solution**:
```python
# 1. Verify subscription
async def verify_subscription():
    await tool.subscribe("freezerx")
    print("Subscribed successfully")

# 2. Check handler is working
class DebugHandler(BaseDrasiNotificationHandler):
    def on_result_added(self, query_name: str, added_data: dict) -> None:
        print(f"Handler called: {query_name} - {added_data}")

    def on_notification_error(self, query_name: str, error: Exception) -> None:
        print(f"Handler error: {error}")

tool = create_drasi_tool(config, [DebugHandler()])

# 3. Enable logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Issue: "Connection keeps dropping"

**Cause**: Network instability or server issues

**Solution**:
```python
# Configure aggressive reconnection
config = MCPConnectionConfig(
    server_command="python",
    server_args=["drasi_mcp_server.py"],
    reconnect_policy=ReconnectPolicy(
        enabled=True,
        max_retries=None,  # Infinite retries
        retry_delay=5.0,
        backoff_multiplier=1.5,
        max_delay=300.0
    ),
    timeout=60
)
```

#### Issue: Azure OpenAI authentication fails

**Cause**: Incorrect credentials or expired key

**Solution**:
```python
# Verify environment variables
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT_NAME"
]

for var in required_vars:
    value = os.getenv(var)
    if not value:
        print(f"Missing: {var}")
    else:
        print(f"{var}: {'*' * len(value)}")

# Test connection
from langchain_openai import AzureChatOpenAI

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

try:
    response = llm.invoke("Hello")
    print("Azure OpenAI connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
```

#### Issue: Handler exceptions breaking notification flow

**Cause**: Unhandled exceptions in handler methods

**Solution**:
```python
class SafeHandler(BaseDrasiNotificationHandler):
    """Handler with internal error handling."""

    def on_result_added(self, query_name: str, added_data: dict) -> None:
        try:
            self._process_added(query_name, added_data)
        except Exception as e:
            # Log but don't raise - allows other notifications to continue
            logging.error(f"Error in on_result_added: {e}", exc_info=True)

    def _process_added(self, query_name: str, data: dict):
        # Your actual processing logic
        pass
```

---

## Next Steps

### Learn More

- **API Reference**: See `/docs/api-reference.md` for complete API documentation
- **Architecture Guide**: Review `/docs/architecture.md` to understand how the library works
- **Contract Specifications**: Explore `/specs/001-build-a-library/contracts/` for detailed protocols

### Advanced Topics

- **Custom MCP Servers**: Build your own MCP server for Drasi
- **Performance Optimization**: Tune reconnection policies and handler performance
- **Testing**: Write tests for your notification handlers
- **Deployment**: Deploy production agents with LangChain-Drasi

### Example Projects

Explore the sample applications:

1. **Vanilla LangChain** (`/samples/vanilla-langchain/`)
   - Basic agent setup
   - Simple query operations
   - Notification handling

2. **LangGraph** (`/samples/langgraph/`)
   - Stateful workflows
   - Complex agent behaviors
   - Multi-query orchestration

### Community and Support

- **GitHub**: https://github.com/your-org/langchain-drasi
- **Issues**: Report bugs and request features
- **Discussions**: Ask questions and share use cases
- **Documentation**: https://langchain-drasi.readthedocs.io

---

## Quick Reference

### Key Classes and Functions

```python
# Configuration
from langchain_drasi import MCPConnectionConfig, ReconnectPolicy

# Tool creation
from langchain_drasi import create_drasi_tool

# Notification handlers
from langchain_drasi import (
    BaseDrasiNotificationHandler,
    create_simple_handler,
    LoggingNotificationHandler,
    QueueNotificationHandler,
    CompositeNotificationHandler
)

# Exceptions
from langchain_drasi import (
    DrasiError,
    MCPConnectionError,
    QueryNotFoundError,
    SubscriptionError
)
```

### Environment Variables Template

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT_NAME=
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# MCP Server
MCP_SERVER_COMMAND=python
MCP_SERVER_ARGS=path/to/server.py
```

### Minimal Working Example

```python
import asyncio
from langchain_drasi import create_drasi_tool, MCPConnectionConfig

config = MCPConnectionConfig(
    server_command="python",
    server_args=["drasi_mcp_server.py"]
)

tool = create_drasi_tool(config)

async def main():
    # Discover queries
    queries = await tool.discover_queries()
    print(f"Found {len(queries)} queries")

    # Read a query
    if queries:
        result = await tool.read_query(queries[0]["name"])
        print(f"Data: {result['data']}")

asyncio.run(main())
```

---

**Happy coding with LangChain-Drasi!**

For questions or issues, please visit our [GitHub repository](https://github.com/your-org/langchain-drasi) or check the [full documentation](https://langchain-drasi.readthedocs.io).
