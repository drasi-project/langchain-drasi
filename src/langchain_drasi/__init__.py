"""LangChain extension for Drasi continuous query integration.

This library provides LangChain tools and utilities for integrating Drasi
continuous queries into AI agent workflows via the Model Context Protocol (MCP).

Quick Start:
    ```python
    from langchain_drasi import create_drasi_tool, MCPConnectionConfig

    # Configure HTTP connection to remote Drasi MCP server
    config = MCPConnectionConfig(
        server_url="https://your-drasi-server.com/api",
        headers={"Authorization": "Bearer your-token"},
        timeout=30.0
    )

    # Create the tool
    tool = create_drasi_tool(mcp_config=config)

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

Main Components:
    - DrasiTool: LangChain tool for query operations
    - MCPConnectionConfig: Connection configuration
    - DrasiNotificationHandler: Protocol for handling real-time updates
    - BaseDrasiNotificationHandler: Base class for custom handlers
"""

# Tool and factory
# Callbacks
from .callbacks import (
    AsyncBaseDrasiNotificationHandler,
    AsyncDrasiNotificationHandler,
    BaseDrasiNotificationHandler,
    DrasiNotificationHandler,
)

# MCP Client (advanced usage)
from .client import MCPClient

# Configuration
from .config import MCPConnectionConfig, ReconnectPolicy

# Exceptions
from .exceptions import (
    DrasiError,
    MCPConnectionError,
    NotificationProcessingError,
    QueryNotFoundError,
    SubscriptionError,
)

# Built-in handlers
from .handlers import ConsoleHandler, LoggingHandler, MemoryHandler

# Models
from .models import ChangeNotification, ChangeType, QueryInfo, QueryResult
from .tool import DrasiQueryInput, DrasiTool, create_drasi_tool

# Utilities
from .utils import (
    build_query_uri,
    extract_query_name_from_notification_method,
    parse_query_uri,
    validate_query_uri,
)

__version__ = "0.1.0"

__all__ = [
    # Tool
    "DrasiTool",
    "DrasiQueryInput",
    "create_drasi_tool",
    # Configuration
    "MCPConnectionConfig",
    "ReconnectPolicy",
    # Callbacks
    "DrasiNotificationHandler",
    "AsyncDrasiNotificationHandler",
    "BaseDrasiNotificationHandler",
    "AsyncBaseDrasiNotificationHandler",
    # Models
    "QueryInfo",
    "QueryResult",
    "ChangeNotification",
    "ChangeType",
    # Exceptions
    "DrasiError",
    "MCPConnectionError",
    "QueryNotFoundError",
    "SubscriptionError",
    "NotificationProcessingError",
    # Client
    "MCPClient",
    # Utilities
    "build_query_uri",
    "parse_query_uri",
    "validate_query_uri",
    "extract_query_name_from_notification_method",
    # Built-in Handlers
    "LoggingHandler",
    "ConsoleHandler",
    "MemoryHandler",
    # Version
    "__version__",
]
