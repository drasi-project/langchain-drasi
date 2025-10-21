"""Standard LangChain unit tests for DrasiTool.

This module implements the standard LangChain test suite for the DrasiTool,
ensuring compliance with the BaseTool interface and LangChain best practices.

See: https://python.langchain.com/docs/contributing/how_to/integrations/standard_tests/
"""

import pytest
from langchain_tests.unit_tests.tools import ToolsUnitTests

from langchain_drasi import DrasiTool, MCPConnectionConfig


class TestDrasiToolStandardTests(ToolsUnitTests):
    """Standard LangChain unit tests for DrasiTool.

    This test class validates that DrasiTool properly implements the BaseTool
    interface according to LangChain standards. It tests:

    - Tool initialization
    - Tool name presence
    - Input schema definition
    - Schema validation against example parameters
    """

    @property
    def tool_constructor(self) -> type[DrasiTool]:
        """Returns the DrasiTool class to be tested."""
        return DrasiTool

    @property
    def tool_constructor_params(self) -> dict:
        """Returns parameters required to initialize DrasiTool.

        DrasiTool requires:
        - mcp_config: Configuration for MCP connection
        - notification_handlers: Optional list of notification handlers
        """
        # Create a minimal MCP configuration for testing
        mcp_config = MCPConnectionConfig(
            server_url="http://localhost:8083",
            timeout=30.0,
        )

        return {
            "mcp_config": mcp_config,
        }

    @property
    def tool_invoke_params_example(self) -> dict:
        """Returns example parameters for tool invocation.

        The DrasiTool accepts an 'input' parameter which is a string
        in the format 'operation:query_name' or just 'operation'.

        Examples:
        - 'discover' - List all queries
        - 'read:my-query' - Read results from a query
        - 'subscribe:my-query' - Subscribe to query updates
        - 'unsubscribe:my-query' - Unsubscribe from query
        """
        return {
            "input": "discover",
        }

    @property
    def init_from_env_params(self) -> tuple[dict, dict, dict]:
        """Init from env params.

        DrasiTool doesn't currently support initialization from environment
        variables, so we return empty dictionaries.

        Returns:
            Tuple of (env_vars, init_args, expected_attrs)
        """
        return {}, {}, {}


# Additional custom tests specific to DrasiTool
class TestDrasiToolCustom:
    """Custom tests for DrasiTool functionality beyond standard tests."""

    def test_tool_has_correct_name(self) -> None:
        """Test that DrasiTool has the expected name."""
        mcp_config = MCPConnectionConfig(server_url="http://localhost:8083")

        tool = DrasiTool(mcp_config=mcp_config)

        assert tool.name == "drasi_query"

    def test_tool_has_description(self) -> None:
        """Test that DrasiTool has a meaningful description."""
        mcp_config = MCPConnectionConfig(server_url="http://localhost:8083")

        tool = DrasiTool(mcp_config=mcp_config)

        assert tool.description
        assert len(tool.description) > 10
        assert "Drasi" in tool.description

    def test_tool_accepts_various_input_formats(self) -> None:
        """Test that the input schema validates different operation formats."""
        mcp_config = MCPConnectionConfig(server_url="http://localhost:8083")

        tool = DrasiTool(mcp_config=mcp_config)

        input_schema = tool.get_input_schema()

        # Test various valid input formats
        valid_inputs = [
            {"input": "discover"},
            {"input": "read:my-query"},
            {"input": "subscribe:freezerx"},
            {"input": "unsubscribe:active-orders"},
        ]

        for input_data in valid_inputs:
            validated = input_schema(**input_data)
            assert validated is not None
            assert validated.input == input_data["input"]

    def test_tool_requires_mcp_config(self) -> None:
        """Test that DrasiTool requires mcp_config parameter."""
        with pytest.raises(TypeError):
            # Should fail without mcp_config
            DrasiTool()  # type: ignore

    def test_tool_accepts_optional_notification_handlers(self) -> None:
        """Test that DrasiTool can be initialized with optional notification handlers."""
        from langchain_drasi.handlers import ConsoleHandler

        mcp_config = MCPConnectionConfig(server_url="http://localhost:8083")
        handler = ConsoleHandler()

        # Should work with handlers
        tool = DrasiTool(mcp_config=mcp_config, notification_handlers=[handler])
        assert tool is not None
        assert len(tool.notification_handlers) == 1

        # Should also work without handlers
        tool_no_handlers = DrasiTool(mcp_config=mcp_config)
        assert tool_no_handlers is not None
        assert len(tool_no_handlers.notification_handlers) == 0
