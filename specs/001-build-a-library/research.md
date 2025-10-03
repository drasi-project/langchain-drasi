# Technical Research: LangChain-Drasi MCP Integration Library

## 1. MCP Python SDK

### Decision
Use the official `mcp` package from PyPI (modelcontextprotocol/python-sdk) as the primary SDK for MCP client implementation.

### Rationale
- **Official support**: Maintained by the Model Context Protocol organization
- **Complete implementation**: Implements the full MCP specification including resources, tools, and prompts
- **Active development**: Latest version (1.7.1+) with ongoing updates and bug fixes
- **Well-documented**: Comprehensive documentation and examples available
- **Community adoption**: Widely used across MCP implementations with strong community support

### Alternatives Considered
- **fastmcp**: Third-party alternative by jlowin that provides a more Pythonic API
  - Pros: Simpler API, faster development
  - Cons: Not the official implementation, potential compatibility issues
- **Custom implementation**: Building from scratch using MCP protocol spec
  - Pros: Full control, minimal dependencies
  - Cons: Significant development effort, maintenance burden, potential protocol incompatibilities

### Implementation Notes

#### Installation
```bash
# Using pip
pip install "mcp[cli]"

# Using uv (recommended for new projects)
uv add "mcp[cli]"
```

#### Core Client Classes

**Primary Classes:**
- `ClientSession`: Main entry point for MCP client operations
- `StdioServerParameters`: Configuration for stdio-based server connections
- `stdio_client`: Async context manager for stdio transport

**Key Imports:**
```python
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.exceptions import MCPError, ResourceNotFoundError
```

#### Client Initialization Pattern
```python
async def initialize_mcp_client():
    """Initialize MCP client connection to a server."""
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None  # Optional environment variables
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Session is now ready for operations
            yield session
```

#### Listing Resources
```python
async def list_available_resources(session: ClientSession):
    """List all available resources from the MCP server."""
    resources = await session.list_resources()
    print(f"Available resources: {resources}")
    return resources
```

#### Reading Resources
```python
async def read_resource(session: ClientSession, resource_uri: str):
    """Read a specific resource by URI."""
    try:
        content, mime_type = await session.read_resource(resource_uri)
        return {"content": content, "mime_type": mime_type}
    except ResourceNotFoundError as e:
        print(f"Resource not found: {e}")
        raise
    except MCPError as e:
        print(f"MCP error: {e}")
        raise
```

#### Subscribing to Resource Updates
```python
async def subscribe_to_resources(session: ClientSession):
    """Subscribe to resource updates from the MCP server."""
    async for resources in session.subscribe_resources():
        print(f"Resources updated: {resources}")
        # Handle resource updates
        yield resources
```

#### Notification Handling

**Server-Side Notification Methods:**
```python
# In MCP server implementation
await ctx.session.send_resource_list_changed()  # Notify resource list changed
await ctx.session.send_resource_updated(AnyUrl(resource_uri))  # Notify specific resource updated
await ctx.session.send_tool_list_changed()  # Notify tool list changed
await ctx.session.send_prompt_list_changed()  # Notify prompt list changed
```

**Client-Side Notification Pattern:**
The MCP protocol uses standard notification types, but **Drasi MCP servers use a custom notification format**:

**Standard MCP Notifications** (most MCP servers):
1. `notifications/resources/list_changed`: Indicates the list of available resources changed
2. `notifications/resources/updated`: Indicates a specific subscribed resource was updated

**Drasi Custom Notifications** (what we'll receive):
- `notifications/{query-name}/added`: New row added to query results
- `notifications/{query-name}/updated`: Existing row updated in query results
- `notifications/{query-name}/deleted`: Row deleted from query results

**Implementation Pattern for Drasi**:
```python
async def handle_notification(notification: dict):
    """Route Drasi notifications to appropriate callback handlers."""
    method = notification.get("method")
    params = notification.get("params", {})

    # Parse method: "notifications/freezerx/added" -> ("freezerx", "added")
    if method and method.startswith("notifications/"):
        parts = method.split("/")
        if len(parts) == 3:
            query_name = parts[1]
            change_type = parts[2]  # "added", "updated", or "deleted"

            # Route to appropriate callback
            if change_type == "added":
                handler.on_result_added(query_name, params)
            elif change_type == "updated":
                handler.on_result_updated(query_name, params)
            elif change_type == "deleted":
                handler.on_result_deleted(query_name, params)
```

**Capabilities Declaration:**
Servers must declare subscription support during initialization to enable resource subscriptions.

#### Error Handling Best Practices
```python
from mcp.exceptions import MCPError, ResourceNotFoundError

try:
    content, mime_type = await session.read_resource("file://example.txt")
except ResourceNotFoundError as e:
    # Handle missing resource
    logger.warning(f"Resource not found: {e}")
except MCPError as e:
    # Handle general MCP errors
    logger.error(f"MCP protocol error: {e}")
except Exception as e:
    # Handle unexpected errors
    logger.exception(f"Unexpected error: {e}")
```

#### Connection Types Supported
- **stdio**: Subprocess-based communication (most common)
- **WebSocket**: Network-based communication
- **Socket**: Direct socket connections

#### Key Gotchas
1. **Always use async/await**: MCP SDK is fully asynchronous
2. **Context manager cleanup**: Always use async context managers to ensure proper resource cleanup
3. **Initialize before use**: Must call `session.initialize()` before any operations
4. **Capability checking**: Check server capabilities before attempting operations (not all servers support subscriptions)
5. **URI formats**: Resources use URI format (e.g., `file://path`, `http://url`)
6. **Connection lifecycle**: Ensure reconnection logic for production use
7. **Data validation**: Always validate and sanitize data received from MCP servers

---

## 2. LangChain Python Tool Integration

### Decision
Use the `@tool` decorator for simple tools and `BaseTool` subclassing for complex tools requiring state management or custom initialization.

### Rationale
- **Simplicity first**: `@tool` decorator provides the quickest path for simple function-based tools
- **Flexibility when needed**: `BaseTool` subclassing offers full control for complex scenarios
- **Official recommendation**: LangChain documentation recommends starting with `@tool` and moving to `BaseTool` only when needed
- **Type safety**: Both approaches support type hints and Pydantic validation
- **Future-proof**: Compatible with LangGraph (the recommended agent framework as of 2025)

### Alternatives Considered
- **StructuredTool.from_function()**: Middle ground between decorator and subclassing
  - Pros: More configuration than decorator, less boilerplate than subclassing
  - Cons: More verbose than decorator, less flexible than BaseTool
  - When to use: When you need to specify both sync and async implementations separately
- **LangGraph native**: Building tools directly in LangGraph
  - Pros: Tight integration with modern agent framework
  - Cons: Less portable, more complex for simple use cases

### Implementation Notes

#### Tool Base Classes and Protocols

**Primary Classes:**
- `BaseTool`: Abstract base class for all tools
- `StructuredTool`: Concrete tool class for function-based tools
- `@tool`: Decorator for simplest tool creation

**Key Imports:**
```python
from langchain_core.tools import BaseTool, StructuredTool, tool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.callbacks import CallbackManagerForToolRun
```

#### Method 1: @tool Decorator (Recommended for Simple Tools)
```python
from langchain_core.tools import tool

@tool
def query_drasi_resource(resource_uri: str) -> str:
    """Query a Drasi resource via MCP.

    Args:
        resource_uri: The URI of the resource to query (e.g., 'drasi://query/my-query')

    Returns:
        The resource content as a string
    """
    # Implementation here
    return f"Content from {resource_uri}"

# Async version
@tool
async def query_drasi_resource_async(resource_uri: str) -> str:
    """Async query a Drasi resource via MCP.

    Args:
        resource_uri: The URI of the resource to query

    Returns:
        The resource content as a string
    """
    # Async implementation
    return f"Content from {resource_uri}"
```

#### Method 2: StructuredTool (For Configuration Needs)
```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class DrasiQueryInput(BaseModel):
    """Input schema for Drasi query tool."""
    resource_uri: str = Field(description="The URI of the Drasi resource to query")
    format: str = Field(default="json", description="Output format (json, text)")

def _query_drasi(resource_uri: str, format: str = "json") -> str:
    """Internal sync implementation."""
    return f"Sync: Content from {resource_uri} as {format}"

async def _query_drasi_async(resource_uri: str, format: str = "json") -> str:
    """Internal async implementation."""
    return f"Async: Content from {resource_uri} as {format}"

drasi_query_tool = StructuredTool.from_function(
    func=_query_drasi,
    coroutine=_query_drasi_async,
    name="DrasiQuery",
    description="Query Drasi continuous queries via MCP",
    args_schema=DrasiQueryInput,
    return_direct=False
)
```

#### Method 3: BaseTool Subclassing (For Complex State Management)
```python
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from typing import Optional, Type
from pydantic import BaseModel, Field

class DrasiQueryInput(BaseModel):
    """Input for Drasi query tool."""
    resource_uri: str = Field(description="URI of the Drasi resource")

class DrasiQueryTool(BaseTool):
    """Tool for querying Drasi resources via MCP."""

    name: str = "drasi_query"
    description: str = "Query Drasi continuous queries via MCP. Use this when you need real-time data."
    args_schema: Type[BaseModel] = DrasiQueryInput
    return_direct: bool = False

    # Custom state (not serializable by default)
    mcp_client: Optional[object] = None

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        resource_uri: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Synchronous implementation."""
        # Access self.mcp_client for stateful operations
        if run_manager:
            run_manager.on_text(f"Querying {resource_uri}...\n", color="green")
        return f"Result from {resource_uri}"

    async def _arun(
        self,
        resource_uri: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Asynchronous implementation."""
        if run_manager:
            run_manager.on_text(f"Async querying {resource_uri}...\n", color="green")
        # Async implementation with self.mcp_client
        return f"Async result from {resource_uri}"
```

#### Callback Infrastructure

**Understanding LangChain Callbacks:**
LangChain provides a flexible callback system for monitoring and interacting with LLM applications at various stages.

**Callback Registration Methods:**

1. **Constructor Callbacks (Object-Scoped)**
```python
from langchain_core.callbacks import BaseCallbackHandler

class MyHandler(BaseCallbackHandler):
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"Tool started with input: {input_str}")

    def on_tool_end(self, output, **kwargs):
        print(f"Tool completed with output: {output}")

# Register at tool creation
tool = DrasiQueryTool(callbacks=[MyHandler()])
```

2. **Runtime Callbacks (Inherited by Children)**
```python
# Register at invocation
result = tool.invoke(
    {"resource_uri": "drasi://query/test"},
    {"callbacks": [MyHandler()]}
)
```

3. **Using with_config() for Reusable Callbacks**
```python
# Attach callbacks to be used across multiple executions
configured_tool = tool.with_config(callbacks=[MyHandler()])

# Now every invocation uses these callbacks
result1 = configured_tool.invoke({"resource_uri": "drasi://query/1"})
result2 = configured_tool.invoke({"resource_uri": "drasi://query/2"})
```

**Key Callback Events for Tools:**
```python
class ToolCallbackHandler(BaseCallbackHandler):
    """Custom handler for tool events."""

    def on_tool_start(self, serialized, input_str, **kwargs):
        """Called when tool starts."""
        pass

    def on_tool_end(self, output, **kwargs):
        """Called when tool completes successfully."""
        pass

    def on_tool_error(self, error, **kwargs):
        """Called when tool raises an error."""
        pass
```

**Callback Inheritance Rules:**
- **Constructor callbacks**: Scoped only to the object, NOT inherited by children
- **Runtime callbacks**: Automatically inherited by all child objects
- **with_config() callbacks**: Persist across multiple invocations of the same object

#### Tool Initialization Best Practices

1. **Keep Tools Stateless When Possible**
```python
# Good: Stateless tool
@tool
def query_resource(uri: str) -> str:
    """Query a resource."""
    client = get_mcp_client()  # Get from dependency injection
    return client.read(uri)

# Avoid: Stateful tool (unless necessary)
class StatefulTool(BaseTool):
    _client = None  # Mutable state can cause issues
```

2. **Use Dependency Injection for Resources**
```python
from typing import Callable

def create_drasi_tool(mcp_client_factory: Callable):
    """Factory function for creating tool with injected dependencies."""

    @tool
    def query_drasi(uri: str) -> str:
        """Query Drasi resource."""
        client = mcp_client_factory()
        return client.read(uri)

    return query_drasi
```

3. **Configure Temperature for Tool Usage**
```python
from langchain_openai import ChatOpenAI

# Low temperature for deterministic tool usage
llm = ChatOpenAI(model="gpt-4", temperature=0)  # 0-0.3 recommended
llm_with_tools = llm.bind_tools([drasi_tool])
```

4. **Set Iteration Limits for Safety**
```python
from langgraph.prebuilt import create_react_agent

# Prevent infinite loops
agent = create_react_agent(
    llm,
    tools=[drasi_tool],
    max_iterations=5  # Recommended starting point
)
```

#### Integration with Agents

**Modern Approach (LangGraph - Recommended for 2025):**
```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)
tools = [drasi_query_tool, drasi_subscribe_tool]

agent = create_react_agent(
    llm,
    tools,
    state_modifier="You are a helpful assistant with access to Drasi queries."
)

# Invoke with state management
result = agent.invoke({
    "messages": [("user", "What's in the orders query?")]
})
```

**Legacy Approach (Still Supported):**
```python
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with access to Drasi queries."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

#### Key Gotchas

1. **Async/Sync Mismatch**: Always implement both `_run` and `_arun` for BaseTool, or provide separate implementations for StructuredTool
2. **Docstring Required**: The `@tool` decorator requires a docstring - it becomes the tool description
3. **Type Hints Critical**: Type hints are used to generate the args schema
4. **Return Direct**: Set `return_direct=True` only if you want the tool output to bypass the LLM and return directly to the user
5. **Error Handling**: Raise `ToolException` for expected errors that the agent should handle
6. **Serialization**: Tools passed to agents must be serializable - avoid complex state in constructor
7. **Memory Management**: With BaseTool, use `Config.arbitrary_types_allowed = True` for complex types

---

## 3. Python Project Structure

### Decision
Use **src/ layout** with pyproject.toml for packaging configuration.

### Rationale
- **Import safety**: Prevents accidentally importing from source instead of installed package
- **Test isolation**: Ensures tests run against installed version, catching packaging issues early
- **Official recommendation**: PyPA (Python Packaging Authority) and pyOpenSci strongly recommend src/ layout
- **Modern standard**: Aligns with Python packaging best practices as of 2025
- **Build tool compatibility**: Works seamlessly with modern build tools (setuptools, hatchling, poetry 2.0+)

### Alternatives Considered
- **Flat layout**: Package in project root
  - Pros: Simpler structure, fewer directories
  - Cons: Import ambiguity, tests may pass locally but fail when installed
  - When to use: Simple scripts, not recommended for libraries
- **Tests inside package**: Including tests in the package directory
  - Pros: Tests shipped with package
  - Cons: Increases package size, generally not recommended for libraries

### Implementation Notes

#### Recommended Directory Structure
```
langchain-drasi/
├── .git/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── langchain_drasi/
│       ├── __init__.py
│       ├── py.typed              # PEP 561 marker for type hints
│       ├── client.py             # MCP client wrapper
│       ├── tools.py              # LangChain tools
│       ├── callbacks.py          # Callback handlers
│       ├── exceptions.py         # Custom exceptions
│       └── types.py              # Type definitions
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_client.py
│   │   └── test_tools.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_mcp_integration.py
│   └── contract/
│       ├── __init__.py
│       └── test_langchain_contract.py
├── docs/
│   ├── index.md
│   ├── quickstart.md
│   └── api/
├── examples/
│   ├── basic_query.py
│   └── agent_integration.py
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

#### pyproject.toml Configuration

**Complete Modern Configuration (2025):**
```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "langchain-drasi"
version = "0.1.0"
description = "LangChain extension for Drasi continuous queries via MCP"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
maintainers = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["langchain", "drasi", "mcp", "continuous-queries", "agents"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.7.0",
    "langchain-core>=0.3.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-mock>=3.14.0",
    "black>=24.0.0",
    "ruff>=0.7.0",
    "mypy>=1.13.0",
    "pre-commit>=4.0.0",
]
docs = [
    "mkdocs>=1.6.0",
    "mkdocs-material>=9.5.0",
    "mkdocstrings[python]>=0.27.0",
]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-mock>=3.14.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/langchain-drasi"
Documentation = "https://langchain-drasi.readthedocs.io"
Repository = "https://github.com/yourusername/langchain-drasi"
Issues = "https://github.com/yourusername/langchain-drasi/issues"
Changelog = "https://github.com/yourusername/langchain-drasi/blob/main/CHANGELOG.md"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
langchain_drasi = ["py.typed"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=langchain_drasi",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "contract: Contract tests",
    "slow: Slow tests",
]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "examples/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]

[tool.black]
line-length = 100
target-version = ["py311", "py312", "py313"]
include = '\.pyi?$'

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

#### Type Hints and Static Typing Best Practices

**Modern Type Hint Syntax (Python 3.11+):**
```python
from typing import Optional, Protocol, TypeVar, Generic
from collections.abc import Sequence, Mapping, Callable, Awaitable

# Use built-in generics (Python 3.9+)
def process_items(items: list[str]) -> dict[str, int]:
    """Process items and return counts."""
    return {item: len(item) for item in items}

# Union types with | (Python 3.10+)
def parse_value(value: str | int | None) -> str:
    """Parse various value types."""
    if value is None:
        return "null"
    return str(value)

# Generic types
T = TypeVar("T")

class Resource(Generic[T]):
    """Generic resource wrapper."""

    def __init__(self, data: T) -> None:
        self.data = data

    def get(self) -> T:
        return self.data

# Protocol for structural typing
class MCPClientProtocol(Protocol):
    """Protocol defining MCP client interface."""

    async def read_resource(self, uri: str) -> tuple[str, str]:
        """Read a resource."""
        ...

    async def list_resources(self) -> list[dict[str, str]]:
        """List available resources."""
        ...
```

**Best Practices for 2025:**

1. **Use Modern Syntax**
```python
# Preferred (Python 3.10+)
def func(x: int | None) -> str | None:
    pass

# Legacy (still works)
from typing import Optional, Union
def func(x: Optional[int]) -> Union[str, None]:
    pass
```

2. **Strategic Application**
```python
# Public API: Always type
def public_function(data: str, options: dict[str, int]) -> list[str]:
    """Public function with full typing."""
    return _internal_helper(data, options)

# Private/Internal: Can be more lenient
def _internal_helper(data, options):
    """Internal helper, less strict typing acceptable."""
    return [data] * options.get("repeat", 1)
```

3. **Use TYPE_CHECKING for Import Optimization**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp import ClientSession
    from langchain_core.callbacks import BaseCallbackHandler

def create_tool(
    session: "ClientSession",
    callbacks: list["BaseCallbackHandler"] | None = None
) -> None:
    """Function using forward references for type hints."""
    pass
```

4. **PEP 561 Compliance (py.typed marker)**
```python
# Create src/langchain_drasi/py.typed (empty file)
# This signals to type checkers that the package includes type hints
```

5. **Pydantic for Runtime Validation**
```python
from pydantic import BaseModel, Field, field_validator

class DrasiQueryConfig(BaseModel):
    """Configuration for Drasi query tool."""

    server_command: str = Field(description="Command to start MCP server")
    server_args: list[str] = Field(default_factory=list)
    timeout: int = Field(default=30, gt=0, description="Timeout in seconds")

    @field_validator("server_command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Command cannot be empty")
        return v
```

#### Docstring Conventions

**Decision: Use Google Style**

**Rationale:**
- Most readable for short to medium-length docstrings
- Wide adoption in Python community
- Excellent Sphinx integration via Napoleon
- Horizontal space efficiency
- Preferred by major projects (TensorFlow, Google projects)

**Google Style Examples:**
```python
def query_drasi_resource(
    uri: str,
    format: str = "json",
    timeout: int | None = None
) -> dict[str, str]:
    """Query a Drasi continuous query resource.

    This function connects to a Drasi MCP server and retrieves the current
    state of a continuous query. The result can be formatted as JSON or plain text.

    Args:
        uri: The URI of the Drasi resource (e.g., 'drasi://query/my-query').
        format: Output format, either 'json' or 'text'. Defaults to 'json'.
        timeout: Optional timeout in seconds. If None, uses default timeout.

    Returns:
        A dictionary containing:
            - content: The query result
            - mime_type: The MIME type of the content
            - timestamp: When the query was executed

    Raises:
        ResourceNotFoundError: If the specified resource doesn't exist.
        TimeoutError: If the query exceeds the timeout.
        MCPError: For other MCP protocol errors.

    Example:
        >>> result = query_drasi_resource("drasi://query/orders")
        >>> print(result["content"])
        [{"id": 1, "total": 100.0}, ...]

    Note:
        This function is async and must be awaited.
    """
    pass

class DrasiTool:
    """LangChain tool for Drasi continuous queries.

    This tool provides LangChain agents with access to Drasi continuous queries
    through the Model Context Protocol (MCP).

    Attributes:
        name: The unique name of this tool.
        description: Human-readable description for the LLM.
        mcp_client: The MCP client instance for server communication.
    """

    def __init__(self, server_params: dict[str, str]) -> None:
        """Initialize the Drasi tool.

        Args:
            server_params: Parameters for MCP server connection including
                'command' and 'args'.
        """
        pass
```

**NumPy Style (Alternative for Complex Projects):**
```python
def complex_analysis(
    data: list[dict[str, float]],
    algorithms: list[str],
    config: dict[str, int]
) -> tuple[list[float], dict[str, float]]:
    """
    Perform complex analysis on continuous query results.

    This function applies multiple algorithms to analyze streaming query
    results from Drasi, computing various statistical measures and trends.

    Parameters
    ----------
    data : list[dict[str, float]]
        List of data points from the continuous query, where each dict
        contains field names mapped to numeric values.
    algorithms : list[str]
        Names of algorithms to apply. Supported values are:
        - 'mean': Compute rolling mean
        - 'variance': Compute variance
        - 'trend': Detect trends
    config : dict[str, int]
        Configuration parameters including:
        - 'window_size': Size of rolling window
        - 'min_samples': Minimum samples required

    Returns
    -------
    results : list[float]
        Computed results for each data point.
    metadata : dict[str, float]
        Summary statistics including:
        - 'total_samples': Total number of samples processed
        - 'avg_value': Average across all results

    Raises
    ------
    ValueError
        If algorithms list is empty or contains unsupported values.
    InsufficientDataError
        If data has fewer points than config['min_samples'].

    See Also
    --------
    simple_analysis : For basic statistical analysis.
    stream_analysis : For real-time streaming analysis.

    Notes
    -----
    The analysis is performed incrementally and can handle large datasets
    efficiently. Memory usage is O(window_size).

    Examples
    --------
    >>> data = [{"value": 1.0}, {"value": 2.0}, {"value": 3.0}]
    >>> results, meta = complex_analysis(data, ["mean"], {"window_size": 2})
    >>> print(results)
    [1.0, 1.5, 2.5]
    """
    pass
```

**Key Gotchas:**
1. Always include type hints in addition to docstring parameter descriptions
2. Use imperative mood for function descriptions ("Query a resource", not "Queries a resource")
3. Document all parameters, even if obvious
4. Include examples for non-trivial functions
5. Use `py.typed` marker file for PEP 561 compliance
6. Run static type checkers (mypy, pyright) in CI/CD

---

## 4. Testing Framework

### Decision
Use **pytest** as the primary testing framework with pytest-asyncio, pytest-mock, and pytest-cov plugins.

### Rationale
- **Industry standard**: Over 80% of Python developers use pytest as of 2023
- **Async support**: Excellent async/await support via pytest-asyncio
- **Plugin ecosystem**: 1300+ plugins for various testing needs
- **Better DX**: Less boilerplate, more readable tests
- **Fixture system**: Powerful dependency injection for test setup
- **Better failure output**: More informative error messages

### Alternatives Considered
- **unittest**: Python's built-in framework
  - Pros: No installation needed, familiar xUnit style
  - Cons: Verbose, limited async support, more boilerplate
  - When to use: Legacy codebases, strict standard-library-only requirements
- **doctest**: Testing via docstrings
  - Pros: Documentation and tests combined
  - Cons: Limited to simple cases, not suitable for integration tests
  - When to use: Supplementary to main tests, documentation examples

### Implementation Notes

#### Test Organization Structure
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, isolated tests
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_tools.py
│   └── test_callbacks.py
├── integration/             # Tests with real dependencies
│   ├── __init__.py
│   ├── test_mcp_integration.py
│   └── test_langchain_integration.py
└── contract/                # API contract tests
    ├── __init__.py
    ├── test_mcp_contract.py
    └── test_langchain_contract.py
```

#### Pytest Configuration (in pyproject.toml)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"  # Automatically detect async tests
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=langchain_drasi",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
    "-v",
]
markers = [
    "unit: Fast unit tests",
    "integration: Integration tests requiring external services",
    "contract: Contract tests for API compatibility",
    "slow: Slow running tests",
]
```

#### Contract Testing Patterns

**What are Contract Tests?**
Contract tests verify that your library correctly implements expected interfaces and behaviors, ensuring compatibility with dependencies (MCP SDK, LangChain).

**MCP Contract Test Example:**
```python
import pytest
from mcp import ClientSession
from langchain_drasi.client import DrasiMCPClient

@pytest.mark.contract
class TestMCPContract:
    """Verify compliance with MCP client contract."""

    async def test_implements_required_methods(self):
        """Verify all required MCP methods are implemented."""
        client = DrasiMCPClient()

        # Verify method existence
        assert hasattr(client, 'initialize')
        assert hasattr(client, 'list_resources')
        assert hasattr(client, 'read_resource')
        assert hasattr(client, 'subscribe_resources')

        # Verify signatures match protocol
        import inspect
        sig = inspect.signature(client.read_resource)
        assert 'uri' in sig.parameters

    async def test_read_resource_returns_expected_format(self):
        """Verify read_resource returns (content, mime_type) tuple."""
        client = DrasiMCPClient()
        # Mock the MCP server response
        result = await client.read_resource("test://uri")

        assert isinstance(result, tuple)
        assert len(result) == 2
        content, mime_type = result
        assert isinstance(content, str)
        assert isinstance(mime_type, str)
```

**LangChain Contract Test Example:**
```python
import pytest
from langchain_core.tools import BaseTool
from langchain_drasi.tools import DrasiQueryTool

@pytest.mark.contract
class TestLangChainContract:
    """Verify compliance with LangChain tool contract."""

    def test_tool_inherits_from_basetool(self):
        """Verify tool properly extends BaseTool."""
        tool = DrasiQueryTool()
        assert isinstance(tool, BaseTool)

    def test_tool_has_required_attributes(self):
        """Verify tool has all required LangChain attributes."""
        tool = DrasiQueryTool()

        assert hasattr(tool, 'name')
        assert isinstance(tool.name, str)
        assert len(tool.name) > 0

        assert hasattr(tool, 'description')
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0

    def test_tool_implements_run_method(self):
        """Verify _run method is implemented."""
        tool = DrasiQueryTool()
        assert hasattr(tool, '_run')
        assert callable(tool._run)

    async def test_tool_implements_arun_method(self):
        """Verify _arun method is implemented for async."""
        tool = DrasiQueryTool()
        assert hasattr(tool, '_arun')
        assert callable(tool._arun)

    def test_tool_serialization(self):
        """Verify tool can be serialized for agent use."""
        tool = DrasiQueryTool()
        # LangChain requires tools to be serializable
        schema = tool.args_schema.schema() if tool.args_schema else {}
        assert isinstance(schema, dict)
```

#### Mocking Strategies for External Dependencies

**Mocking MCP Server:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_drasi.client import DrasiMCPClient

@pytest.fixture
def mock_mcp_session(mocker):
    """Mock MCP ClientSession."""
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_resources = AsyncMock(return_value=[
        {"uri": "drasi://query/test", "name": "test_query"}
    ])
    session.read_resource = AsyncMock(return_value=(
        '{"data": "test"}',
        "application/json"
    ))
    return session

@pytest.fixture
def mock_stdio_client(mocker, mock_mcp_session):
    """Mock stdio_client context manager."""
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=(
        MagicMock(),  # read stream
        MagicMock()   # write stream
    ))
    mock_context.__aexit__ = AsyncMock()

    mocker.patch(
        'langchain_drasi.client.stdio_client',
        return_value=mock_context
    )

    # Mock ClientSession creation
    mocker.patch(
        'langchain_drasi.client.ClientSession',
        return_value=mock_mcp_session
    )

    return mock_context

@pytest.mark.asyncio
async def test_client_read_resource(mock_stdio_client, mock_mcp_session):
    """Test reading a resource with mocked MCP server."""
    client = DrasiMCPClient(command="python", args=["server.py"])

    async with client:
        result = await client.read_resource("drasi://query/test")

    assert result[0] == '{"data": "test"}'
    assert result[1] == "application/json"
    mock_mcp_session.read_resource.assert_called_once_with("drasi://query/test")
```

**Mocking LangChain Components:**
```python
import pytest
from unittest.mock import MagicMock, AsyncMock
from langchain_drasi.tools import DrasiQueryTool

@pytest.fixture
def mock_callback_manager(mocker):
    """Mock CallbackManager for tool testing."""
    manager = MagicMock()
    manager.on_text = MagicMock()
    return manager

@pytest.mark.asyncio
async def test_tool_with_callbacks(mock_stdio_client, mock_callback_manager):
    """Test tool execution with callback manager."""
    tool = DrasiQueryTool()

    result = await tool._arun(
        resource_uri="drasi://query/test",
        run_manager=mock_callback_manager
    )

    assert result is not None
    # Verify callback was invoked
    mock_callback_manager.on_text.assert_called()
```

#### Async Testing Patterns

**Basic Async Test:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    result = await some_async_function()
    assert result == expected_value
```

**Async Context Manager Mocking:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class AsyncContextManagerMock:
    """Reusable async context manager mock."""

    def __init__(self, return_value=None):
        self.return_value = return_value
        self.enter_called = False
        self.exit_called = False

    async def __aenter__(self):
        self.enter_called = True
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exit_called = True
        return False

@pytest.fixture
def mock_client_session():
    """Mock MCP client session as async context manager."""
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.read_resource = AsyncMock(return_value=("data", "text/plain"))

    return AsyncContextManagerMock(return_value=mock_session)

@pytest.mark.asyncio
async def test_with_async_context_manager(mock_client_session):
    """Test using async context manager mock."""
    async with mock_client_session as session:
        result = await session.read_resource("test://uri")

    assert mock_client_session.enter_called
    assert mock_client_session.exit_called
    assert result == ("data", "text/plain")
```

**Testing Async Iterators:**
```python
import pytest

class AsyncIteratorMock:
    """Mock async iterator for testing subscriptions."""

    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item

@pytest.mark.asyncio
async def test_resource_subscription():
    """Test subscribing to resource updates."""
    mock_updates = AsyncIteratorMock([
        {"uri": "drasi://query/1", "data": "update1"},
        {"uri": "drasi://query/1", "data": "update2"},
    ])

    results = []
    async for update in mock_updates:
        results.append(update)

    assert len(results) == 2
    assert results[0]["data"] == "update1"
```

#### Integration Testing Patterns

**Pytest Fixtures for Integration Tests:**
```python
import pytest
import asyncio
from pathlib import Path
import tempfile

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session-scoped async fixtures."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def mcp_test_server():
    """Start a real MCP test server for integration tests."""
    import subprocess

    # Start test server
    server_process = subprocess.Popen(
        ["python", "-m", "tests.fixtures.test_server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to be ready
    await asyncio.sleep(1)

    yield server_process

    # Cleanup
    server_process.terminate()
    server_process.wait(timeout=5)

@pytest.fixture
async def drasi_client(mcp_test_server):
    """Create DrasiMCPClient connected to test server."""
    from langchain_drasi.client import DrasiMCPClient

    client = DrasiMCPClient(
        command="python",
        args=["-m", "tests.fixtures.test_server"]
    )

    async with client:
        yield client

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_server_connection(drasi_client):
    """Test connection to real MCP test server."""
    resources = await drasi_client.list_resources()
    assert len(resources) > 0

    # Test reading a resource
    content, mime_type = await drasi_client.read_resource(resources[0]["uri"])
    assert content is not None
    assert mime_type in ["application/json", "text/plain"]
```

**Dependency Injection with Fixtures:**
```python
import pytest
from langchain_drasi.tools import create_drasi_tool

@pytest.fixture
def mcp_client_factory(mock_mcp_session):
    """Factory for creating mock MCP clients."""
    def _factory():
        return mock_mcp_session
    return _factory

@pytest.fixture
def drasi_tool(mcp_client_factory):
    """Create DrasiTool with injected mock client."""
    return create_drasi_tool(mcp_client_factory)

def test_tool_with_dependency_injection(drasi_tool):
    """Test tool created with dependency injection."""
    result = drasi_tool.invoke({"uri": "drasi://query/test"})
    assert result is not None
```

#### Best Practices Summary

1. **Fixture Organization**
   - Put shared fixtures in `conftest.py`
   - Use fixture scopes appropriately (function, class, module, session)
   - Create factory fixtures for parameterized setups

2. **Test Markers**
   - Mark tests by type: `@pytest.mark.unit`, `@pytest.mark.integration`
   - Use `-m` flag to run specific test types: `pytest -m unit`

3. **Async Testing**
   - Always use `@pytest.mark.asyncio` for async tests
   - Set `asyncio_mode = "auto"` in pytest.ini for auto-detection
   - Use `AsyncMock` instead of `Mock` for async functions

4. **Mocking Guidelines**
   - Mock at the boundary (mock external dependencies, not internal functions)
   - Use `autospec=True` to enforce method signatures
   - Prefer dependency injection over patching when possible

5. **Coverage**
   - Aim for 80%+ coverage
   - Exclude `if TYPE_CHECKING:` blocks
   - Don't chase 100% - focus on critical paths

6. **CI/CD Integration**
   ```yaml
   # .github/workflows/test.yml
   name: Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       strategy:
         matrix:
           python-version: ["3.11", "3.12", "3.13"]
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: ${{ matrix.python-version }}
         - run: pip install -e ".[test]"
         - run: pytest -v --cov
   ```

#### Key Gotchas

1. **Async fixture scope**: Session-scoped async fixtures require custom event loop
2. **Mock persistence**: Mocks persist within test function scope, reset between tests
3. **AsyncMock vs Mock**: Always use AsyncMock for async functions/methods
4. **Fixture execution order**: Fixtures execute in dependency order, not declaration order
5. **Parametrize with async**: Use `@pytest.mark.parametrize` with async tests normally
6. **Assert await**: With AsyncMock, use `assert_awaited()` not `assert_called()`
7. **Context manager cleanup**: Always test both `__enter__/__exit__` or `__aenter__/__aexit__`

---

## Summary of Decisions

| Aspect | Decision | Key Reason |
|--------|----------|------------|
| **MCP SDK** | Official `mcp` package | Complete spec implementation, official support |
| **LangChain Tools** | `@tool` decorator + `BaseTool` subclassing | Simplicity + flexibility when needed |
| **Project Structure** | src/ layout | Import safety, test isolation |
| **Packaging** | pyproject.toml | Modern standard (PEP 621) |
| **Type Hints** | Modern syntax (PEP 604, 585) | Readability, Python 3.11+ features |
| **Docstrings** | Google style | Readability, wide adoption |
| **Testing Framework** | pytest | Industry standard, async support, plugins |
| **Mocking** | pytest-mock + AsyncMock | Clean API, async compatibility |
| **Contract Tests** | Interface verification | Ensure compatibility with dependencies |

---

## Next Steps for Implementation

1. **Setup Project Structure**
   - Create src/ layout
   - Configure pyproject.toml
   - Setup testing infrastructure

2. **Implement MCP Client Wrapper**
   - Wrap MCP ClientSession with convenience methods
   - Add connection management
   - Implement error handling

3. **Create LangChain Tools**
   - Query tool for reading resources
   - Subscription tool for updates (if needed)
   - Document with Google style docstrings

4. **Write Tests**
   - Unit tests for isolated components
   - Contract tests for MCP and LangChain compliance
   - Integration tests with mock MCP server

5. **Add Type Hints**
   - Full type coverage for public API
   - Add py.typed marker
   - Configure mypy for strict checking

6. **Documentation**
   - README with quickstart
   - API documentation
   - Usage examples

7. **CI/CD**
   - GitHub Actions for testing
   - Code coverage reporting
   - Type checking and linting
