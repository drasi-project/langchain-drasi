# Standard LangChain Tests

This directory contains the standard LangChain test suite for the `langchain-drasi` library. These tests ensure that the DrasiTool properly implements the LangChain `BaseTool` interface and adheres to LangChain best practices.

## Overview

The standard tests are based on LangChain's official testing framework ([langchain-tests](https://pypi.org/project/langchain-tests/)) and validate:

- **Tool initialization**: Verifies the tool can be properly initialized with required parameters
- **Tool naming**: Ensures the tool has a valid name attribute
- **Input schema**: Validates that the tool defines a proper input schema
- **Schema validation**: Tests that example parameters match the declared input schema

## Test Files

### `test_drasi_tool.py`

Contains two test classes:

1. **`TestDrasiToolStandardTests`** - Extends `ToolsUnitTests` from `langchain_tests.unit_tests.tools`
   - Implements required properties for standard LangChain tool testing
   - Tests are automatically inherited from the base class
   - Standard tests include:
     - `test_init` - Tool initialization
     - `test_init_from_env` - Environment-based initialization
     - `test_has_name` - Name attribute validation
     - `test_has_input_schema` - Input schema presence
     - `test_input_schema_matches_invoke_params` - Schema validation

2. **`TestDrasiToolCustom`** - Custom tests specific to DrasiTool
   - `test_tool_has_correct_name` - Validates the tool name is "drasi_query"
   - `test_tool_has_description` - Ensures a meaningful description exists
   - `test_tool_accepts_various_input_formats` - Tests different operation formats
   - `test_tool_requires_mcp_config` - Validates required parameters
   - `test_tool_accepts_optional_notification_handlers` - Tests optional handlers

## Running the Tests

### Run all standard tests:
```bash
pytest tests/standard_tests/ -v
```

### Run only the standard LangChain tests:
```bash
pytest tests/standard_tests/test_drasi_tool.py::TestDrasiToolStandardTests -v
```

### Run only the custom tests:
```bash
pytest tests/standard_tests/test_drasi_tool.py::TestDrasiToolCustom -v
```

### Run a specific test:
```bash
pytest tests/standard_tests/test_drasi_tool.py::TestDrasiToolStandardTests::test_has_input_schema -v
```

## Test Configuration

The standard tests are configured with the following properties:

- **`tool_constructor`**: Returns the `DrasiTool` class
- **`tool_constructor_params`**: Provides minimal required parameters:
  - `mcp_config`: MCPConnectionConfig with server URL
- **`tool_invoke_params_example`**: Example input for tool invocation:
  - `{"input": "discover"}` - A simple discover operation

## Why These Tests Matter

1. **LangChain Compatibility**: Ensures DrasiTool works correctly with LangChain agents and frameworks
2. **API Contract**: Validates that the tool adheres to the BaseTool interface contract
3. **Regression Prevention**: Catches breaking changes to the tool's interface
4. **Documentation**: Serves as executable documentation of the tool's expected behavior

## Related Documentation

- [LangChain Standard Tests Guide](https://python.langchain.com/docs/contributing/how_to/integrations/standard_tests/)
- [LangChain Tools Documentation](https://python.langchain.com/docs/concepts/tools/)
- [langchain-tests PyPI](https://pypi.org/project/langchain-tests/)

## Maintenance

When updating the DrasiTool:

1. **Run standard tests** to ensure compatibility is maintained
2. **Update test parameters** if the tool's constructor signature changes
3. **Add custom tests** for new DrasiTool-specific functionality
4. **Keep example parameters current** with the tool's input schema

If any standard test fails, it likely indicates a breaking change to the LangChain interface. Review the changes carefully before proceeding.
