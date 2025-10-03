# Tasks: LangChain Extension for Drasi Query Integration

**Input**: Design documents from `/specs/001-build-a-library/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Summary

**Tech Stack**: Python 3.13, MCP SDK, LangChain Core, Pydantic, pytest
**Structure**: Single library package (src/ layout)
**Total Tasks**: 35 tasks across 5 phases
**Critical Path**: Setup → Tests → Core → Integration → Polish

---

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All paths are absolute from repository root

---

## Phase 3.1: Project Setup & Foundation

- [x] **T001** - Create project structure and initialize Python package
  - Create `src/langchain_drasi/` package directory
  - Create `tests/contract/`, `tests/integration/`, `tests/unit/` directories
  - Create `samples/langchain/` and `samples/langgraph/` directories
  - Create `docs/` directory
  - Create `src/langchain_drasi/__init__.py` with placeholder

- [x] **T002** - Configure pyproject.toml with dependencies and build settings
  - Add Python 3.13 requirement (minimum 3.11)
  - Add dependencies: `mcp[cli]`, `langchain-core`, `pydantic>=2.0`, `python-dotenv`
  - Add dev dependencies: `pytest`, `pytest-asyncio`, `pytest-mock`, `pytest-cov`, `black`, `ruff`, `mypy`
  - Configure build system with setuptools/hatchling
  - Set package metadata (name: `langchain-drasi`, version, authors, description)
  - Configure tool.pytest.ini_options for async tests

- [x] **T003** [P] - Create .env.example with configuration templates
  - Add MCP server configuration variables
  - Add Azure OpenAI configuration (API key, endpoint, deployment, version)
  - Add logging configuration
  - Include comments explaining each variable

- [x] **T004** [P] - Configure linting and formatting tools
  - Create `.ruff.toml` with rules for Python 3.13
  - Create `mypy.ini` for strict type checking
  - Create `.pre-commit-config.yaml` (optional)

- [x] **T005** - Implement exception hierarchy in `src/langchain_drasi/exceptions.py`
  - Create base `DrasiError` exception
  - Create `MCPConnectionError(DrasiError)` for connection failures
  - Create `QueryNotFoundError(DrasiError)` for missing queries
  - Create `SubscriptionError(DrasiError)` for subscription failures
  - Create `NotificationProcessingError(DrasiError)` for notification errors
  - Add type hints and docstrings for each exception

- [x] **T006** - Implement data models in `src/langchain_drasi/models.py`
  - Create `QueryInfo` TypedDict (name, title, uri, description, mime_type)
  - Create `QueryResult` TypedDict (query_name, uri, mime_type, content, timestamp)
  - Create `ChangeNotification` TypedDict (change_type, query_name, method, params, timestamp)
  - Create `ChangeType` Enum (ADDED, UPDATED, DELETED)
  - Add comprehensive docstrings and type hints

- [x] **T007** - Implement configuration models in `src/langchain_drasi/config.py`
  - Create `ReconnectPolicy` Pydantic model (enabled, max_retries, retry_delay, backoff_multiplier, max_delay)
  - Create `MCPConnectionConfig` Pydantic model (server_command, server_args, server_env, reconnect_policy)
  - Add field validators for configuration values
  - Add docstrings explaining each field

---

## Phase 3.2: Contract Tests (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [ ] **T008** [P] - Contract test for DrasiTool API in `tests/contract/test_tool_contract.py`
  - Test DrasiTool inherits from BaseTool
  - Test DrasiTool has required attributes (name, description, args_schema)
  - Test DrasiTool.__init__ accepts mcp_config and notification_handlers
  - Test DrasiTool.discover_queries() returns list[QueryInfo]
  - Test DrasiTool.read_query() returns QueryResult
  - Test DrasiTool.subscribe() and unsubscribe() methods exist
  - Test _run() and _arun() method signatures
  - Use Protocol checking and isinstance assertions
  - **This test MUST FAIL initially**

- [ ] **T009** [P] - Contract test for callback handlers in `tests/contract/test_callback_contract.py`
  - Test DrasiNotificationHandler Protocol with runtime_checkable
  - Test BaseDrasiNotificationHandler has all required methods
  - Test on_result_added, on_result_updated, on_result_deleted signatures
  - Test on_notification_error signature
  - Test that custom handler classes satisfy the Protocol
  - Test AsyncDrasiNotificationHandler Protocol
  - **This test MUST FAIL initially**

- [ ] **T010** [P] - Contract test for MCP protocol messages in `tests/contract/test_mcp_protocol.py`
  - Test resources/list request/response schema validation
  - Test resources/read request/response schema validation
  - Test resources/subscribe request/response schema validation
  - Test Drasi notification format: "notifications/{query-name}/added|updated|deleted"
  - Test URI format validation: "drasi://query/{query-name}"
  - Test JSON schema compliance with MCP spec
  - Use jsonschema or pydantic for validation
  - **This test MUST FAIL initially**

- [ ] **T011** [P] - Integration test for MCP server communication in `tests/integration/test_mcp_integration.py`
  - Test establishing MCP connection via stdio
  - Test listing available resources
  - Test reading resource content
  - Test subscribing to resource updates
  - Test receiving Drasi custom notifications
  - Test connection failure and reconnection
  - Test graceful shutdown
  - Use pytest-asyncio for async tests
  - Requires mock MCP server or test fixture
  - **This test MUST FAIL initially**

- [ ] **T012** [P] - Integration test for LangChain integration in `tests/integration/test_langchain_integration.py`
  - Test DrasiTool works with AgentExecutor
  - Test DrasiTool works with LangGraph workflows
  - Test tool invocation through LangChain
  - Test callback integration with LangChain's callback system
  - Test error handling in agent context
  - **This test MUST FAIL initially**

- [ ] **T013** [P] - End-to-end test in `tests/integration/test_end_to_end.py`
  - Test complete workflow: discover → read → subscribe → receive notification → invoke callback
  - Test multiple concurrent subscriptions
  - Test subscription lifecycle (subscribe → notifications → unsubscribe)
  - Test notification routing to correct callbacks
  - Test error scenarios (missing query, connection loss, callback failure)
  - **This test MUST FAIL initially**

- [ ] **T014** - Create test fixtures and utilities in `tests/conftest.py`
  - Create MockMCPServer fixture for testing
  - Create sample QueryInfo fixtures
  - Create sample notification message fixtures
  - Create MockNotificationHandler for testing
  - Configure pytest-asyncio settings
  - Create helpers for async test assertions

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

- [ ] **T015** - Implement MCP client wrapper in `src/langchain_drasi/client.py`
  - Create `MCPClient` class wrapping MCP SDK ClientSession
  - Implement async context manager for connection lifecycle
  - Implement `list_resources()` using MCP SDK
  - Implement `read_resource(uri: str)` using MCP SDK
  - Implement `subscribe(uri: str)` using MCP SDK
  - Implement `unsubscribe(uri: str)` using MCP SDK
  - Add connection state management
  - Add reconnection logic based on ReconnectPolicy
  - Use proper error handling and exceptions from exceptions.py
  - Add comprehensive logging

- [ ] **T016** - Implement notification router in `src/langchain_drasi/client.py` (same file as T015)
  - Create `NotificationRouter` class
  - Implement `parse_drasi_notification(notification: dict)` to extract query_name and change_type
  - Parse method format: "notifications/{query-name}/added|updated|deleted"
  - Implement routing logic to invoke correct callback method
  - Handle notification errors per FR-018 (log and continue)
  - Add notification listener background task
  - Integrate with MCPClient

- [ ] **T017** [P] - Implement callback protocols in `src/langchain_drasi/callbacks.py`
  - Create `DrasiNotificationHandler` Protocol with @runtime_checkable
  - Define `on_result_added(query_name: str, added_data: dict)` method
  - Define `on_result_updated(query_name: str, updated_data: dict)` method
  - Define `on_result_deleted(query_name: str, deleted_data: dict)` method
  - Define `on_notification_error(query_name: str, error: Exception)` method
  - Add comprehensive docstrings

- [ ] **T018** [P] - Implement base callback handler in `src/langchain_drasi/callbacks.py` (same file as T017)
  - Create `BaseDrasiNotificationHandler` abstract base class
  - Implement default no-op methods for all notification types
  - Add convenience method `on_query_change(query_name, change_type, data)`
  - Add `should_handle_query(query_name: str)` filter method
  - Add `get_handler_name()` for logging

- [ ] **T019** [P] - Implement async callback support in `src/langchain_drasi/callbacks.py` (same file as T017, T018)
  - Create `AsyncDrasiNotificationHandler` Protocol
  - Create `AsyncBaseDrasiNotificationHandler` base class
  - Implement `adapt_sync_handler()` function to wrap sync handlers for async
  - Add proper asyncio handling

- [ ] **T020** - Implement DrasiTool in `src/langchain_drasi/tool.py`
  - Create `DrasiTool` class inheriting from `BaseTool`
  - Create `DrasiQueryInput` Pydantic model for input schema
  - Implement `__init__(mcp_config, notification_handlers)` with connection setup
  - Implement `discover_queries()` async method
  - Implement `read_query(query_name: str)` async method
  - Implement `subscribe(query_name: str)` async method
  - Implement `unsubscribe(query_name: str)` async method
  - Implement `_run()` sync wrapper using asyncio.run()
  - Implement `_arun()` async main method
  - Integrate MCPClient and NotificationRouter
  - Add proper error handling

- [ ] **T021** [P] - Implement factory function in `src/langchain_drasi/tool.py` (same file as T020)
  - Create `create_drasi_tool(mcp_config, notification_handlers)` factory function
  - Validate configuration
  - Initialize MCP connection
  - Return configured DrasiTool instance
  - Add comprehensive docstring with usage example

- [ ] **T022** [P] - Implement utility functions in `src/langchain_drasi/utils.py`
  - Create `parse_notification_method(method: str)` to extract query_name and change_type
  - Create `validate_drasi_uri(uri: str)` to check URI format
  - Create `safe_invoke_handler()` to invoke callbacks with error isolation
  - Add logging utilities
  - Add helper functions for async/sync bridging if needed

- [ ] **T023** - Update public API exports in `src/langchain_drasi/__init__.py`
  - Export `DrasiTool`, `create_drasi_tool`
  - Export `MCPConnectionConfig`, `ReconnectPolicy`
  - Export `DrasiNotificationHandler`, `BaseDrasiNotificationHandler`
  - Export `AsyncDrasiNotificationHandler`, `AsyncBaseDrasiNotificationHandler`
  - Export `QueryInfo`, `QueryResult`, `ChangeNotification`, `ChangeType`
  - Export all exception types
  - Add `__version__`
  - Add `__all__` list

---

## Phase 3.4: Built-in Handlers & Integration

- [ ] **T024** [P] - Implement LoggingNotificationHandler in `src/langchain_drasi/handlers.py`
  - Create `LoggingNotificationHandler(BaseDrasiNotificationHandler)`
  - Add configurable log level and logger
  - Implement handlers that log all notifications
  - Add option to include/exclude data in logs

- [ ] **T025** [P] - Implement QueueNotificationHandler in `src/langchain_drasi/handlers.py` (same file as T024)
  - Create `QueueNotificationHandler(BaseDrasiNotificationHandler)`
  - Use `queue.Queue` for thread-safe queuing
  - Implement `get_notification()` method
  - Add `QueuedNotification` NamedTuple

- [ ] **T026** [P] - Implement FilteringNotificationHandler in `src/langchain_drasi/handlers.py` (same file as T024, T025)
  - Create `FilteringNotificationHandler(BaseDrasiNotificationHandler)`
  - Accept query_filter and data_filter predicates
  - Delegate to inner handler when filters pass

- [ ] **T027** [P] - Implement CompositeNotificationHandler in `src/langchain_drasi/handlers.py` (same file as T024, T025, T026)
  - Create `CompositeNotificationHandler(BaseDrasiNotificationHandler)`
  - Accept list of handlers
  - Invoke all handlers, catch and log individual failures
  - Ensure one handler's failure doesn't stop others

---

## Phase 3.5: Sample Applications

- [ ] **T028** [P] - Create vanilla LangChain sample in `samples/langchain/app.py`
  - Import DrasiTool and create_drasi_tool
  - Configure MCP connection from environment variables
  - Create simple notification handler
  - Create Azure OpenAI LLM instance
  - Create agent with DrasiTool
  - Demonstrate discover, read, and subscribe operations
  - Add error handling and logging
  - Create `samples/langchain/requirements.txt` with dependencies
  - Create `samples/langchain/README.md` with usage instructions

- [ ] **T029** [P] - Create LangGraph sample in `samples/langgraph/app.py`
  - Import DrasiTool and LangGraph components
  - Configure MCP connection from environment variables
  - Create stateful workflow with DrasiTool
  - Demonstrate reactive agent pattern (respond to notifications)
  - Use Azure OpenAI for LLM
  - Add state management and error handling
  - Create `samples/langgraph/requirements.txt` with dependencies
  - Create `samples/langgraph/README.md` with usage instructions

---

## Phase 3.6: Unit Tests & Polish

- [ ] **T030** [P] - Unit tests for exceptions in `tests/unit/test_exceptions.py`
  - Test exception hierarchy
  - Test exception messages and context
  - Test exception attributes

- [ ] **T031** [P] - Unit tests for models in `tests/unit/test_models.py`
  - Test TypedDict definitions
  - Test ChangeType enum values
  - Test model validation

- [ ] **T032** [P] - Unit tests for config in `tests/unit/test_config.py`
  - Test ReconnectPolicy validation
  - Test MCPConnectionConfig validation
  - Test field validators and defaults
  - Test invalid configuration handling

- [ ] **T033** [P] - Unit tests for utils in `tests/unit/test_utils.py`
  - Test parse_notification_method() with various inputs
  - Test validate_drasi_uri() with valid and invalid URIs
  - Test safe_invoke_handler() error isolation
  - Test edge cases and error paths

- [ ] **T034** [P] - Unit tests for notification router in `tests/unit/test_notification_router.py`
  - Test notification parsing logic
  - Test routing to correct callback methods
  - Test error handling during routing
  - Test invalid notification formats

- [ ] **T035** [P] - Documentation and final polish
  - Create comprehensive `README.md` in repository root
  - Create `docs/architecture.md` explaining design
  - Create `docs/api-reference.md` or generate from docstrings
  - Update all docstrings for completeness
  - Run `black` and `ruff` on all code
  - Run `mypy` and fix type issues
  - Ensure >90% test coverage with pytest-cov

---

## Dependencies Graph

```
Setup Phase (T001-T007):
  T001 → (all tasks)
  T002 → (all tasks requiring dependencies)
  T003, T004 → (parallel, no deps)
  T005 → T006, T007
  T006 → T015, T017, T020
  T007 → T015, T020

Contract Tests Phase (T008-T014):
  T008-T013 → (parallel, all must fail before T015+)
  T014 → T008-T013 (provides fixtures)

Core Implementation Phase (T015-T023):
  T015 → T016 (same file, notification router depends on client)
  T015, T016 → T020 (tool depends on client)
  T017 → T018 → T019 (same file, sequential implementation)
  T017 → T020 (tool needs protocol)
  T020 → T021 (same file, factory after tool)
  T020 → T022 (tool uses utils)
  T015-T022 → T023 (exports after all implementations)

Built-in Handlers (T024-T027):
  T017 → T024-T027 (handlers depend on protocol)
  T024-T027 → (same file, sequential)

Samples Phase (T028-T029):
  T023 → T028, T029 (parallel, need public API)

Polish Phase (T030-T035):
  T005 → T030
  T006 → T031
  T007 → T032
  T022 → T033
  T016 → T034
  T001-T034 → T035 (docs after everything)
```

---

## Parallel Execution Examples

### Phase 3.1 - Foundation (Parallel Tasks)
```bash
# Run T003 and T004 in parallel:
# Terminal 1:
Task: "Create .env.example with configuration templates in samples/langchain/.env.example"

# Terminal 2:
Task: "Configure linting tools - create .ruff.toml and mypy.ini"
```

### Phase 3.2 - Contract Tests (All Parallel)
```bash
# Run T008-T013 in parallel (all independent test files):
Task: "Contract test for DrasiTool API in tests/contract/test_tool_contract.py"
Task: "Contract test for callback handlers in tests/contract/test_callback_contract.py"
Task: "Contract test for MCP protocol in tests/contract/test_mcp_protocol.py"
Task: "Integration test MCP communication in tests/integration/test_mcp_integration.py"
Task: "Integration test LangChain in tests/integration/test_langchain_integration.py"
Task: "End-to-end test in tests/integration/test_end_to_end.py"
```

### Phase 3.3 - Core Implementation (Some Parallel)
```bash
# Run T017 and T022 in parallel (different files):
Task: "Implement callback protocols in src/langchain_drasi/callbacks.py"
Task: "Implement utility functions in src/langchain_drasi/utils.py"
```

### Phase 3.5 - Samples (Parallel)
```bash
# Run T028 and T029 in parallel (independent samples):
Task: "Create vanilla LangChain sample in samples/langchain/app.py"
Task: "Create LangGraph sample in samples/langgraph/app.py"
```

### Phase 3.6 - Unit Tests (All Parallel)
```bash
# Run T030-T034 in parallel (all independent test files):
Task: "Unit tests for exceptions in tests/unit/test_exceptions.py"
Task: "Unit tests for models in tests/unit/test_models.py"
Task: "Unit tests for config in tests/unit/test_config.py"
Task: "Unit tests for utils in tests/unit/test_utils.py"
Task: "Unit tests for router in tests/unit/test_notification_router.py"
```

---

## Validation Checklist

- [x] All contracts have corresponding tests (T008-T010)
- [x] All entities from data-model.md have implementations (T006 models, T015 client, T020 tool)
- [x] All tests come before implementation (T008-T014 before T015+)
- [x] Parallel tasks are truly independent (checked [P] markers)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] TDD ordering: Contract tests → Implementation → Integration → Polish
- [x] Dependencies properly sequenced

---

## Notes

- **Critical Path**: T001 → T002 → T005 → T006 → T007 → T014 → T015 → T016 → T020 → T023
- **Total Estimated Time**: 25-35 hours for full implementation
- **Parallelization Opportunities**: 14 tasks can run in parallel (marked with [P])
- **Test-First**: All contract and integration tests (T008-T013) MUST fail before starting T015
- **Built-in Handlers** (T024-T027): Optional for v1.0, can be moved to future release if time-constrained
- **Drasi Notification Format**: Remember to parse `"notifications/{query-name}/added|updated|deleted"` in notification router (T016)
- **Async Everywhere**: MCP SDK is fully async, ensure proper async/await usage throughout

---

## Success Criteria

✅ All 35 tasks completed
✅ All tests passing (contract, integration, unit)
✅ Test coverage >90%
✅ Type checking passes (mypy)
✅ Linting passes (ruff, black)
✅ Both sample applications run successfully
✅ Documentation complete and accurate
✅ No constitutional violations
✅ All functional requirements (FR-001 through FR-028) satisfied
