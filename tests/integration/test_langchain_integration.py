"""Integration tests for LangChain integration.

These tests verify that DrasiTool integrates correctly with LangChain
components like AgentExecutor and can be used in agent workflows.
Note: These tests require DrasiTool implementation to be complete.
"""
# pyright: reportPossiblyUnboundVariable=false, reportOptionalMemberAccess=false, reportCallIssue=false, reportInvalidTypeForm=false, reportAttributeAccessIssue=false, reportMissingImports=false

import pytest

# These imports will fail until modules are implemented
try:
    from langchain.agents import AgentExecutor, create_react_agent  # type: ignore[import-not-found]
    from langchain_core.prompts import PromptTemplate

    from langchain_drasi.config import MCPConnectionConfig
    from langchain_drasi.tool import DrasiTool, create_drasi_tool
    IMPORTS_AVAILABLE = True
except ImportError:
    AgentExecutor = object  # type: ignore[misc,assignment]
    create_react_agent = lambda *args, **kwargs: None  # type: ignore[misc,assignment]
    PromptTemplate = object  # type: ignore[misc,assignment]
    MCPConnectionConfig = object  # type: ignore[misc,assignment]
    DrasiTool = object  # type: ignore[misc,assignment]
    create_drasi_tool = lambda *args, **kwargs: None  # type: ignore[misc,assignment]
    IMPORTS_AVAILABLE = False


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="DrasiTool not yet implemented")
@pytest.mark.integration
class TestLangChainIntegration:
    """Integration tests for LangChain agent integration."""

    @pytest.fixture
    def mcp_config(self) -> "MCPConnectionConfig":
        """Fixture providing MCP connection config for testing."""
        return MCPConnectionConfig(
            server_url="http://localhost:8080/mcp",
        )

    @pytest.fixture
    def drasi_tool(self, mcp_config: "MCPConnectionConfig") -> "DrasiTool":
        """Fixture providing DrasiTool instance."""
        return create_drasi_tool(mcp_config=mcp_config)

    @pytest.mark.asyncio
    async def test_drasi_tool_is_valid_langchain_tool(
        self, drasi_tool: "DrasiTool"
    ) -> None:
        """Test that DrasiTool is recognized as valid LangChain tool."""
        from langchain_core.tools import BaseTool

        assert isinstance(drasi_tool, BaseTool), "DrasiTool must be a BaseTool"
        assert drasi_tool.name, "Tool must have a name"
        assert drasi_tool.description, "Tool must have a description"
        assert drasi_tool.args_schema, "Tool must have args_schema"

    @pytest.mark.asyncio
    async def test_tool_can_be_invoked_with_langchain(
        self, drasi_tool: "DrasiTool"
    ) -> None:
        """Test that DrasiTool can be invoked using LangChain's invoke method."""
        # Use the standard LangChain tool invocation
        result = await drasi_tool.ainvoke(
            {"query_name": "test-query", "operation": "read"}
        )
        assert result is not None, "Tool should return result"

    @pytest.mark.asyncio
    async def test_tool_works_in_tool_list(self, drasi_tool: "DrasiTool") -> None:
        """Test that DrasiTool works when added to a tools list."""
        # Should be able to add to a list of tools
        tools = [drasi_tool]
        assert len(tools) == 1
        assert tools[0] == drasi_tool

    @pytest.mark.asyncio
    async def test_tool_schema_serialization(self, drasi_tool: "DrasiTool") -> None:
        """Test that DrasiTool schema can be serialized for agent use."""
        # LangChain tools should be able to provide their schema
        schema = drasi_tool.args_schema.schema()
        assert "properties" in schema, "Schema must have properties"
        assert "query_name" in schema["properties"], "Must have query_name field"
        assert "operation" in schema["properties"], "Must have operation field"

    @pytest.mark.asyncio
    async def test_tool_error_handling_in_langchain_context(
        self, drasi_tool: "DrasiTool"
    ) -> None:
        """Test that tool errors are properly handled in LangChain context."""
        from langchain_drasi.exceptions import QueryNotFoundError

        # Attempting to read non-existent query should raise error
        with pytest.raises(QueryNotFoundError):
            await drasi_tool.ainvoke(
                {"query_name": "nonexistent-query", "operation": "read"}
            )

    @pytest.mark.asyncio
    async def test_multiple_operations_via_tool(self, drasi_tool: "DrasiTool") -> None:
        """Test that tool can perform multiple operations."""
        # Discover queries
        discover_result = await drasi_tool.ainvoke(
            {"query_name": "", "operation": "discover"}
        )
        assert discover_result is not None

        # Read a query
        read_result = await drasi_tool.ainvoke(
            {"query_name": "test-query", "operation": "read"}
        )
        assert read_result is not None

        # Subscribe to a query
        subscribe_result = await drasi_tool.ainvoke(
            {"query_name": "test-query", "operation": "subscribe"}
        )
        assert subscribe_result is not None


# If imports failed, create a failing test
if not IMPORTS_AVAILABLE:
    def test_langchain_integration_not_implemented() -> None:
        """Fail to indicate LangChain integration implementation is needed."""
        pytest.fail(
            "LangChain integration not ready yet. "
            "This test will pass once DrasiTool is fully implemented."
        )
