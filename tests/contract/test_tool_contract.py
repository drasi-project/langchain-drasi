"""Contract tests for DrasiTool API.

These tests verify that DrasiTool implements the required interface
as specified in contracts/python-api.md. These tests MUST FAIL initially
until the DrasiTool implementation is complete.
"""


import pytest
from pydantic import BaseModel

# These imports will fail until modules are implemented
try:
    from langchain_core.tools import BaseTool

    from langchain_drasi.config import MCPConnectionConfig
    from langchain_drasi.models import QueryInfo, QueryResult
    from langchain_drasi.tool import DrasiQueryInput, DrasiTool, create_drasi_tool
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="DrasiTool not yet implemented")
class TestDrasiToolContract:
    """Contract tests for DrasiTool class."""

    def test_drasi_tool_inherits_from_base_tool(self) -> None:
        """Test that DrasiTool inherits from LangChain BaseTool."""
        assert issubclass(DrasiTool, BaseTool), \
            "DrasiTool must inherit from langchain_core.tools.BaseTool"

    def test_drasi_tool_has_required_attributes(self) -> None:
        """Test that DrasiTool has required class attributes."""
        # With Pydantic 2, check model_fields instead of hasattr
        assert "name" in DrasiTool.model_fields, "DrasiTool must have 'name' field"
        assert "description" in DrasiTool.model_fields, "DrasiTool must have 'description' field"
        assert "args_schema" in DrasiTool.model_fields, "DrasiTool must have 'args_schema' field"

        # Verify args_schema default is a Pydantic model
        # Access via model_fields to get the field info
        args_schema_field = DrasiTool.model_fields["args_schema"]
        assert args_schema_field.default is not None, "args_schema must have a default"
        assert issubclass(args_schema_field.default, BaseModel), \
            "args_schema must be a Pydantic BaseModel"

    def test_drasi_query_input_schema(self) -> None:
        """Test that DrasiQueryInput has required fields."""
        # Verify DrasiQueryInput exists and is a Pydantic model
        assert issubclass(DrasiQueryInput, BaseModel), \
            "DrasiQueryInput must be a Pydantic BaseModel"

        # Create instance to verify fields
        test_input = DrasiQueryInput(query_name="test")
        assert hasattr(test_input, "query_name"), "Must have query_name field"
        assert hasattr(test_input, "operation"), "Must have operation field"
        assert test_input.operation == "read", "Default operation should be 'read'"

    def test_drasi_tool_init_accepts_config(self) -> None:
        """Test that DrasiTool.__init__ accepts mcp_config."""
        config = MCPConnectionConfig(
            server_url="https://test-server.com/api",
        )

        # Should be able to create tool with config
        tool = DrasiTool(mcp_config=config)
        assert tool is not None, "Tool should be created successfully"
        assert hasattr(tool, "mcp_config"), "Tool should store mcp_config"

    def test_drasi_tool_init_accepts_handlers(self) -> None:
        """Test that DrasiTool.__init__ accepts notification_handlers."""
        config = MCPConnectionConfig(
            server_url="https://test-server.com/api",
        )

        class DummyHandler:
            def on_result_added(self, query_name: str, added_data: dict) -> None:
                pass

        handler = DummyHandler()
        tool = DrasiTool(mcp_config=config, notification_handlers=[handler])
        assert tool is not None, "Tool should accept handlers"
        assert hasattr(tool, "notification_handlers"), "Tool should store handlers"

    def test_drasi_tool_has_discover_queries_method(self) -> None:
        """Test that DrasiTool has discover_queries() method."""
        assert hasattr(DrasiTool, "discover_queries"), \
            "DrasiTool must have discover_queries() method"

        # Verify method signature (async)
        import inspect
        method = DrasiTool.discover_queries
        assert inspect.iscoroutinefunction(method), \
            "discover_queries() must be async"

    def test_drasi_tool_has_read_query_method(self) -> None:
        """Test that DrasiTool has read_query() method."""
        assert hasattr(DrasiTool, "read_query"), \
            "DrasiTool must have read_query() method"

        # Verify method signature (async)
        import inspect
        method = DrasiTool.read_query
        assert inspect.iscoroutinefunction(method), \
            "read_query() must be async"

    def test_drasi_tool_has_subscribe_method(self) -> None:
        """Test that DrasiTool has subscribe() method."""
        assert hasattr(DrasiTool, "subscribe"), \
            "DrasiTool must have subscribe() method"

        import inspect
        method = DrasiTool.subscribe
        assert inspect.iscoroutinefunction(method), \
            "subscribe() must be async"

    def test_drasi_tool_has_unsubscribe_method(self) -> None:
        """Test that DrasiTool has unsubscribe() method."""
        assert hasattr(DrasiTool, "unsubscribe"), \
            "DrasiTool must have unsubscribe() method"

        import inspect
        method = DrasiTool.unsubscribe
        assert inspect.iscoroutinefunction(method), \
            "unsubscribe() must be async"

    def test_drasi_tool_has_run_methods(self) -> None:
        """Test that DrasiTool has _run() and _arun() methods."""
        assert hasattr(DrasiTool, "_run"), "DrasiTool must have _run() method"
        assert hasattr(DrasiTool, "_arun"), "DrasiTool must have _arun() method"

        # Verify _arun is async
        import inspect
        assert inspect.iscoroutinefunction(DrasiTool._arun), \
            "_arun() must be async"

    def test_create_drasi_tool_factory_exists(self) -> None:
        """Test that create_drasi_tool() factory function exists."""
        assert callable(create_drasi_tool), \
            "create_drasi_tool must be a callable factory function"

    def test_create_drasi_tool_returns_tool_instance(self) -> None:
        """Test that factory function returns DrasiTool instance."""
        config = MCPConnectionConfig(
            server_url="https://test-server.com/api",
        )

        tool = create_drasi_tool(mcp_config=config)
        assert isinstance(tool, DrasiTool), \
            "create_drasi_tool() should return DrasiTool instance"


# If imports failed, create a failing test to indicate implementation needed
if not IMPORTS_AVAILABLE:
    def test_drasi_tool_not_implemented() -> None:
        """Fail to indicate DrasiTool implementation is needed."""
        pytest.fail(
            "DrasiTool not implemented yet. "
            "This test will pass once src/langchain_drasi/tool.py is implemented."
        )
