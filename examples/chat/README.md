# Interactive Chat - langchain-drasi Example

Interactive ReAct agents that use **langchain-drasi** to respond to real-time Drasi query changes with automatic notification memory.

This example demonstrates how to build conversational AI agents that integrate Drasi notifications directly into their conversation memory, enabling them to naturally discuss and respond to real-time database changes.

## Use Case: Freezer Monitoring

This example monitors a PostgreSQL database table of freezers and their temperatures. A Drasi continuous query detects when freezer temperatures exceed 32°F for more than 10 seconds, and the agent receives real-time notifications about overheating freezers.

## Overview

This example showcases:
- **Automatic notification memory** - Drasi notifications are injected directly into agent conversation history
- **Two implementations** - Both LangChain and LangGraph ReAct agent patterns
- **Built-in notification handlers** - Use `LangChainMemoryHandler` and `LangGraphMemoryHandler`
- **Interactive chat interface** - Ask questions about Drasi queries and receive updates in real-time
- **Query discovery and subscription** - Agent uses LLM to discover and subscribe to relevant queries

## Prerequisites

1. **Python 3.11+**
1. **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
1. **PostgreSQL** database
   - `wal_level` must be set to `logical` in `postgresql.conf` for Drasi change tracking
1. **Drasi** running in Docker Desktop
1. **Azure OpenAI** API access

## Quick Start

```bash
# 1. Install dependencies
cd examples/chat
make install

# 2. Initialize database
psql -h localhost -p 5432 -U postgres -d demo -f resources/init_db.sql

# 3. Configure Drasi resources
drasi apply -f resources/sources.yaml
drasi apply -f resources/queries.yaml
drasi apply -f resources/reaction.yaml

# 4. Create tunnel to Drasi MCP server
drasi tunnel reaction chat-mcp 8083

# 5. Configure environment
cp .env.example .env
# Edit .env with your database, Drasi server URL, and Azure OpenAI credentials

# 6. Run the LangChain ReAct sample
make langchain

# OR run the LangGraph ReAct sample
make langgraph

# 7. Update freezers in the database
psql -h localhost -p 5432 -U postgres -d demo -f resources/update-2.sql
psql -h localhost -p 5432 -U postgres -d demo -f resources/update-3.sql
```

See [Database and Drasi Setup](#database-and-drasi-setup) below for detailed setup instructions.

## How It Works

### langchain-drasi Integration

Both chat examples demonstrate the automatic notification memory pattern:

#### 1. Create Notification Handlers

The examples use built-in handlers to automatically inject notifications into conversation memory:

**LangChain Example:**
```python
from langchain.memory import ConversationBufferMemory
from langchain_drasi import LangChainMemoryHandler, ConsoleHandler

# Create conversation memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    input_key="input",
    output_key="output",
)

# Create handlers
console_handler = ConsoleHandler()
langchain_handler = LangChainMemoryHandler(memory)
```

**LangGraph Example:**
```python
from langgraph.checkpoint.memory import MemorySaver
from langchain_drasi import LangGraphMemoryHandler

# Create memory and thread
memory = MemorySaver()
thread_id = "drasi-chat"

# Create handler that automatically injects notifications
langgraph_handler = LangGraphMemoryHandler(memory, thread_id)
```

#### 2. Configure Drasi Connection

```python
from langchain_drasi import create_drasi_tool, MCPConnectionConfig

# Configure connection to Drasi MCP server
mcp_config = MCPConnectionConfig(
    server_url="http://localhost:8083",
    headers={"Authorization": f"Bearer {token}"} if token else None,
    timeout=30.0,
)

# Create the Drasi tool with notification handlers
drasi_tool = create_drasi_tool(
    mcp_config=mcp_config,
    notification_handlers=[console_handler, langchain_handler],
)
```

#### 3. Create ReAct Agent with Drasi Tool

**LangChain Example:**
```python
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent

# Pull ReAct prompt with chat history support
prompt = hub.pull("hwchase17/react-chat")

# Create ReAct agent
agent = create_react_agent(llm, [drasi_tool], prompt)

# Create agent executor with memory
agent_executor = AgentExecutor(
    agent=agent,
    tools=[drasi_tool],
    memory=memory,
    verbose=True,
)

# Notifications are automatically added to memory as system messages
result = await agent_executor.ainvoke({"input": user_input})
```

**LangGraph Example:**
```python
from langgraph.prebuilt import create_react_agent

# Create LangGraph ReAct agent with wrapped checkpointer
agent = create_react_agent(
    model=llm,
    tools=[drasi_tool],
    checkpointer=langgraph_handler.checkpointer,  # Use wrapped checkpointer
)

# Notifications are automatically added to checkpoint as system messages
config = {"configurable": {"thread_id": thread_id}}
result = await agent.ainvoke(
    {"messages": [("user", user_input)]},
    config=config
)
```

### Key Difference: Memory Handlers

The two implementations differ in how they integrate notifications into memory:

**LangChainMemoryHandler:**
- Works with LangChain's `ConversationBufferMemory`
- Adds notifications directly to the memory's chat history
- Notifications appear as system messages in the conversation

**LangGraphMemoryHandler:**
- Wraps LangGraph's checkpointer (e.g., `MemorySaver`)
- Injects notifications directly into the checkpoint state
- Must use `langgraph_handler.checkpointer` when creating the agent

Both handlers ensure notifications are automatically visible to the LLM in subsequent conversations.

### Custom Notification Handlers

You can also create custom handlers for additional notification processing:

```python
from langchain_drasi.callbacks import BaseDrasiNotificationHandler

class MyHandler(BaseDrasiNotificationHandler):
    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        print(f"🆕 NOTIFICATION: Added to '{query_name}': {added_data}")

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        print(f"🔄 NOTIFICATION: Updated in '{query_name}': {updated_data}")

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        print(f"🗑️ NOTIFICATION: Deleted from '{query_name}': {deleted_data}")

# Use multiple handlers together
drasi_tool = create_drasi_tool(
    mcp_config=mcp_config,
    notification_handlers=[my_handler, langchain_handler],
)
```

### Interactive Loop

Both examples provide an interactive chat interface:

```python
while True:
    user_input = await asyncio.get_event_loop().run_in_executor(
        None, lambda: input("\n> ").strip()
    )

    if user_input.lower() in ["exit", "quit", "q"]:
        break

    # Run agent - notifications are automatically injected
    result = await agent_executor.ainvoke({"input": user_input})
    print(result['output'])
```

Example interaction:
```
> Track freezers above 32?
[Agent discovers and and subscribes to the 'freezers-overheat' query]

🆕 NOTIFICATION: Added to 'freezers-overheat': {'freezerId': '2', 'temperature': '35', ...}

> What happened?
Freezer 2 has exceeded the temperature threshold at 35°F for more than 10 seconds.

> What notifications have I received?
You received a notification that freezer 2 is overheating with a temperature of 35°F.
```

## Database and Drasi Setup

### Database Setup

The example includes a PostgreSQL schema with a `Freezer` table that tracks freezer temperatures.

#### 1. Initialize the Database

```bash
# Create database if needed
createdb demo

# Run the initialization script
psql -d demo -f resources/init_db.sql
```

The `init_db.sql` script creates:
- A `Freezer` table with `id` and `temp` columns
- Three sample freezers with initial temperatures (22°F, 35°F, and 18°F)

#### 2. Configure PostgreSQL for Drasi

Drasi requires PostgreSQL's Write-Ahead Log (WAL) to be set to `logical` for change data capture:

```bash
# Edit postgresql.conf
wal_level = logical
```

After changing this setting, restart PostgreSQL.

### Drasi Configuration

The example includes three Drasi resource files in the `resources/` directory:

#### 1. Source Configuration (`sources.yaml`)

Defines the PostgreSQL database connection:

```yaml
apiVersion: v1
kind: Source
name: demo
spec:
  kind: PostgreSQL
  properties:
    host: host.docker.internal  # For Docker Desktop on Mac/Windows
    port: 5432
    user: postgres
    password: test  # Update with your password
    database: demo
    ssl: true
    tables:
      - public.Freezer
```

**Note:** Update the connection details to match your PostgreSQL configuration.

#### 2. Query Configuration (`queries.yaml`)

Defines a continuous query that detects overheating freezers:

```yaml
apiVersion: v1
kind: ContinuousQuery
name: freezers-overheat
spec:
  mode: query
  sources:
    subscriptions:
      - id: demo
  query: >
    MATCH
      (f:Freezer)
    WHERE drasi.trueFor(f.temp > 32, duration( { seconds: 10 } ))
    RETURN
      f.id AS id,
      f.temp AS temp
```

This query:
- Monitors all freezers in the `Freezer` table
- Detects when temperature exceeds 32°F
- Only triggers after temperature stays above threshold for 10+ seconds
- Returns the freezer ID and temperature

#### 3. Reaction Configuration (`reaction.yaml`)

Defines an MCP server that publishes query results as notifications:

```yaml
kind: Reaction
apiVersion: v1
name: chat-mcp
spec:
  kind: MCP
  queries:
    freezers-overheat: |
      description: "Freezer temperature alert for when it goes above 32 degrees for more than 10 seconds"
      added:
        template: |
          {
            "freezerId": "{{after.id}}",
            "temperature": "{{after.temp}}",
            "description": "Temperature of freezer {{after.id}} exceeded threshold for more than 10 seconds"
          }
      # ... update and delete templates
```

### Applying Drasi Resources

Apply the configurations in order:

```bash
# 1. Apply source (connects to PostgreSQL)
drasi apply -f resources/sources.yaml

# 2. Apply query (defines the continuous query)
drasi apply -f resources/queries.yaml

# 3. Apply reaction (sets up MCP server)
drasi apply -f resources/reaction.yaml
```

### Creating the Drasi Tunnel

The Drasi MCP server runs inside the Drasi environment. Create a tunnel to expose it locally:

```bash
# Create tunnel on port 8083
drasi tunnel reaction chat-mcp 8083
```

This makes the MCP server accessible at `http://localhost:8083`, which is the default `DRASI_SERVER_URL` in `.env.example`.

**Keep this terminal open** - the tunnel must remain active for the agents to connect.

### Testing the Setup

You can test your database and trigger notifications manually:

```bash
# Update a freezer temperature to trigger an alert
psql -d demo -c "UPDATE \"Freezer\" SET temp = 40 WHERE id = 1;"

# Wait 10 seconds (the query has a duration threshold)
# Then the agent should receive a notification

# Reset the temperature
psql -d demo -c "UPDATE \"Freezer\" SET temp = 22 WHERE id = 1;"
```

### File Structure

```
examples/chat/
├── langchain_react.py   # LangChain ReAct agent with LangChainMemoryHandler
├── langgraph_react.py   # LangGraph ReAct agent with LangGraphMemoryHandler
├── .env.example         # Environment variables template
├── Makefile             # Build and run commands
├── README.md            # This file
└── resources/
    ├── init_db.sql      # PostgreSQL schema and initial data
    ├── sources.yaml     # Drasi PostgreSQL source configuration
    ├── queries.yaml     # Drasi continuous query definition
    └── reaction.yaml    # Drasi MCP reaction configuration
```

## Key Concepts

### Automatic Notification Memory Pattern

This example demonstrates an **automatic notification memory pattern** where:

1. **Agent subscribes to queries** - Uses LLM + drasi_tool to discover and subscribe
2. **Drasi pushes notifications** - When database changes match query conditions
3. **Notifications automatically added to memory** - Memory handlers inject them as system messages
4. **Agent naturally discusses notifications** - LLM sees notifications in conversation context
5. **No manual notification handling required** - Everything is automatic

This enables agents to naturally maintain awareness of real-time data changes without custom code.

### LangChain vs LangGraph

Both implementations achieve the same goal but use different frameworks:

**LangChain ReAct (`langchain_react.py`):**
- Uses `create_react_agent` and `AgentExecutor` from LangChain
- Integrates with `ConversationBufferMemory`
- Uses `LangChainMemoryHandler` for automatic notification injection
- Best for simpler agent workflows

**LangGraph ReAct (`langgraph_react.py`):**
- Uses `create_react_agent` from LangGraph
- Integrates with LangGraph's checkpointer system
- Uses `LangGraphMemoryHandler` with wrapped checkpointer
- Best for more complex stateful workflows

Choose based on your agent framework preference.

## Environment Variables

Configure these in your `.env` file:

```env
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Drasi MCP Server
DRASI_SERVER_URL=http://localhost:8083
DRASI_API_TOKEN=your_token_if_required  # Optional
```

**Note:** Database credentials are configured in `resources/sources.yaml` for Drasi to connect to PostgreSQL.

## Troubleshooting

### Agent not receiving notifications
- Verify Drasi MCP server is running and accessible at `DRASI_SERVER_URL`
- Check that you've subscribed to a query using the agent
- Ensure Drasi queries are correctly configured and active
- Verify the `drasi tunnel` command is still running (don't close that terminal)
- Test manually by updating a freezer temperature to exceed threshold

### Notifications not appearing in conversation
- For LangChain: Verify `LangChainMemoryHandler` is passed to `create_drasi_tool`
- For LangGraph: Ensure you're using `langgraph_handler.checkpointer` when creating the agent
- Check that notifications are being received (use `ConsoleHandler` to debug)

### Agent can't discover queries
- Verify Drasi MCP server is running and accessible
- Check `DRASI_SERVER_URL` in your `.env` file
- Ensure you have queries configured in your Drasi instance
- Verify all Drasi resources were applied successfully: `drasi list`

### Database connection issues
- Ensure PostgreSQL is running and accessible
- Verify `wal_level = logical` is set in `postgresql.conf`
- Check database credentials in `resources/sources.yaml`
- For Docker Desktop, use `host.docker.internal` as the host
- Check Drasi source status: `drasi describe source demo`

### Freezer notifications not triggering
- Initial temperatures: Freezer 1 (22°F), Freezer 2 (35°F), Freezer 3 (18°F)
- Freezer 2 should trigger immediately (already > 32°F)
- The query requires temperature to stay above 32°F for 10+ seconds
- Update a freezer: `psql -d demo -c "UPDATE \"Freezer\" SET temp = 40 WHERE id = 1;"`
- Wait at least 10 seconds before notification appears

## Learn More

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Drasi Project](https://drasi.io/)
- [langchain-drasi Library](../../README.md)
- [Terminator Example](../terminator/README.md) - For a more complex LangGraph workflow
