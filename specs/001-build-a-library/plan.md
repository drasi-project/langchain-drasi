
# Implementation Plan: LangChain Extension for Drasi Query Integration

**Branch**: `001-build-a-library` | **Date**: 2025-10-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-build-a-library/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Build a Python library that extends LangChain with tools for reading and subscribing to Drasi queries via MCP (Model Context Protocol). The library integrates an MCP client that connects to a Drasi MCP server, exposes queries as LangChain tools, and invokes user-provided callbacks when query results change. Sample applications demonstrate integration with both vanilla LangChain agents and LangGraph workflows using Azure OpenAI.

**Technical Approach**: Use the official MCP Python SDK for server communication, implement LangChain BaseTool for query operations, integrate with LangChain's callback infrastructure for notifications, and follow TDD with contract tests for the public API.

## Technical Context
**Language/Version**: Python 3.13 (minimum 3.11 for compatibility)
**Primary Dependencies**:
- `mcp` (official MCP Python SDK) for MCP client implementation
- `langchain-core` for tool and callback abstractions
- `pydantic` for data validation and settings management
- `pytest` and `pytest-asyncio` for testing

**Storage**: N/A (library does not persist data; session-based only per FR-021)
**Testing**: pytest with pytest-asyncio, pytest-mock, and pytest-cov plugins
**Target Platform**: Cross-platform (Linux, macOS, Windows) - Python library
**Project Type**: Single library package with sample applications
**Performance Goals**:
- Notification delivery latency: <100ms from MCP server to callback invocation
- Support concurrent subscriptions to multiple queries (10+ simultaneous)
- Minimal memory overhead (<50MB for library itself)

**Constraints**:
- No local caching of query results (FR-020)
- Session-based subscriptions only (FR-021)
- Must integrate with LangChain callback infrastructure (FR-010)
- Type hints required throughout for IDE support
- Comprehensive docstrings for public API

**Scale/Scope**:
- Core library: ~2000-3000 LOC
- Sample applications: 2 samples (vanilla LangChain + LangGraph)
- Test coverage target: >90%
- Public API: ~5-7 main classes/functions

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Code Quality & Maintainability ✅
- **Single Responsibility**: Each module has clear purpose (MCP client, tool wrapper, callbacks, notifications)
- **Dependency Inversion**: Using Protocol classes for DrasiNotificationHandler (contracts/callbacks.md)
- **Configuration-Driven**: MCP server config via MCPConnectionConfig, no hardcoded values
- **Public API Documentation**: Comprehensive docstrings specified in contracts/python-api.md
- **No Code Duplication**: Shared utilities extracted into common modules

### II. Testing Standards (Test-First Discipline) ✅
- **TDD Approach**: Contract tests defined before implementation (contracts/ directory)
- **Contract Tests**: Required for all public API boundaries (python-api.md)
- **Integration Tests**: Required for MCP server interactions and LangChain integration
- **No Hardcoded Test Data**: Test fixtures use parameterized data and factories
- **Edge Cases Covered**: Tests for connection failures, missing queries, callback exceptions

### III. User Experience Consistency ✅
- **Error Messages**: Actionable error types defined (DrasiError hierarchy in contracts)
- **Usage Examples**: Comprehensive examples in quickstart.md
- **Environment Variables**: All config via .env files (FR-028), no hardcoded credentials
- **API Consistency**: Standard LangChain tool patterns, familiar to LangChain developers
- **Documentation**: Complete quickstart, API contracts, and usage examples

### IV. Library-First & Code Reuse ✅
- **Use Existing Libraries**: Official MCP SDK, LangChain core, Pydantic (documented in research.md)
- **Justification**: research.md documents library selection rationale
- **Pinned Dependencies**: pyproject.toml will specify version ranges
- **Security**: Dependencies evaluated for security and maintenance status
- **Reusable Components**: Callback handlers, connection managers designed for extension

### V. Observability & Debugging ✅
- **Structured Logging**: Logging configured in callback handlers and connection manager
- **Error Context**: All exceptions include query name, operation, and parameters
- **Configurable Levels**: Log levels via environment variables
- **No Sensitive Data**: Credentials excluded from logs, only query names and metadata logged

### VI. Configuration Management ✅
- **External Configuration**: MCPConnectionConfig for server settings, ReconnectPolicy for behavior
- **Environment Variables**: Azure OpenAI keys, MCP server paths via .env (FR-028)
- **Schema Validation**: Pydantic models validate config at startup
- **Development Defaults**: Local stdio transport for development without external dependencies
- **Placeholder Examples**: quickstart.md uses ${AZURE_OPENAI_KEY} placeholders

**Status**: ✅ PASS - All constitutional requirements satisfied

## Project Structure

### Documentation (this feature)
```
specs/001-build-a-library/
├── spec.md              # Feature specification (input)
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output - technical research ✅
├── data-model.md        # Phase 1 output - entity definitions ✅
├── quickstart.md        # Phase 1 output - user guide ✅
├── contracts/           # Phase 1 output - API contracts ✅
│   ├── README.md        # Navigation and overview
│   ├── python-api.md    # Public Python API contracts
│   ├── mcp-protocol.md  # MCP message schemas
│   └── callbacks.md     # Callback interface specs
└── tasks.md             # Phase 2 output (/tasks command - NOT YET CREATED)
```

### Source Code (repository root)
```
langchain-drasi/                    # Repository root
├── pyproject.toml                  # Project configuration and dependencies
├── README.md                       # Project overview and installation
├── .env.example                    # Example environment variables
│
├── src/
│   └── langchain_drasi/           # Main package
│       ├── __init__.py            # Public API exports
│       ├── tool.py                # DrasiTool (LangChain BaseTool implementation)
│       ├── client.py              # MCP client wrapper and connection management
│       ├── callbacks.py           # Notification handler protocols and implementations
│       ├── config.py              # Configuration models (MCPConnectionConfig, etc.)
│       ├── exceptions.py          # Exception hierarchy (DrasiError, etc.)
│       ├── models.py              # Data models (QueryInfo, QueryResult, etc.)
│       └── utils.py               # Shared utilities and helpers
│
├── tests/
│   ├── conftest.py                # Shared fixtures and test configuration
│   ├── contract/                  # Contract tests (API compliance)
│   │   ├── test_tool_contract.py
│   │   ├── test_callback_contract.py
│   │   └── test_mcp_protocol.py
│   ├── integration/               # Integration tests (real dependencies)
│   │   ├── test_mcp_integration.py
│   │   ├── test_langchain_integration.py
│   │   └── test_end_to_end.py
│   └── unit/                      # Unit tests (isolated, mocked)
│       ├── test_tool.py
│       ├── test_client.py
│       ├── test_callbacks.py
│       └── test_config.py
│
├── samples/
│   ├── langchain/         # Vanilla LangChain sample (FR-013)
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── README.md
│   └── langgraph/                 # LangGraph sample (FR-014)
│       ├── app.py
│       ├── requirements.txt
│       └── README.md
│
└── docs/                          # Additional documentation
    ├── architecture.md
    └── api-reference.md
```

**Structure Decision**: Single library package using src/ layout (recommended by PyPA). This structure:
- Prevents accidental imports of unpackaged code during development
- Clearly separates library code (src/), tests, and samples
- Follows Python packaging best practices for 2025
- Supports TDD with contract/integration/unit test organization
- Includes sample applications demonstrating library usage (FR-013, FR-014)

## Phase 0: Outline & Research ✅ COMPLETE

### Research Topics Addressed:
1. **MCP Python SDK**: Evaluated official `mcp` package vs alternatives (fastmcp, custom implementation)
   - Decision: Use official MCP SDK from PyPI
   - Rationale: Official support, complete implementation, active development

2. **LangChain Tool Integration**: Researched tool creation patterns and callback infrastructure
   - Decision: Use BaseTool for stateful tools, @tool decorator for simple utilities
   - Rationale: BaseTool provides full control for connection management and subscriptions

3. **Python Project Structure**: Evaluated src/ layout vs flat layout
   - Decision: Use src/ layout with pyproject.toml
   - Rationale: Import safety, test isolation, PyPA recommendation

4. **Testing Framework**: Compared pytest vs unittest
   - Decision: pytest with asyncio, mock, and coverage plugins
   - Rationale: 80%+ adoption, excellent async support, 1300+ plugins

**Output**: ✅ `research.md` completed with detailed decisions, rationale, alternatives, and implementation notes

## Phase 1: Design & Contracts ✅ COMPLETE
*Prerequisites: research.md complete*

### Design Artifacts Created:

1. **Data Model** → `data-model.md`: ✅
   - 8 core entities defined (Drasi Query, Query Result Set, Change Notification, MCP Resource, Tool, Callback Handler, MCP Connection, Subscription)
   - Python 3.13 type hints for all attributes
   - Entity relationship diagram (ASCII format)
   - State transition diagrams for Connection, Subscription, and Tool lifecycle
   - Validation rules mapped to functional requirements (FR-001 through FR-028)

2. **API Contracts** → `contracts/`: ✅
   - `python-api.md` (21 KB): Public Python API contracts with type stubs
     - DrasiTool class interface
     - Configuration classes (MCPConnectionConfig, ReconnectPolicy)
     - Callback protocol (DrasiNotificationHandler)
     - Data transfer objects (TypedDict definitions)
     - Exception hierarchy
     - Factory functions
   - `mcp-protocol.md` (23 KB): JSON schemas for MCP messages
     - Resource list, read, subscribe, unsubscribe requests/responses
     - Notification formats (added/updated/deleted)
     - Error response schemas
     - Connection lifecycle specifications
   - `callbacks.md` (31 KB): Callback interface specifications
     - Protocol-based, class-based, function-based, and async patterns
     - Built-in handler implementations (Logging, Queue, Filtering, Composite)
     - LangChain callback adapter
     - Error handling and resilience patterns
   - `README.md` (8.3 KB): Navigation guide and quick reference

3. **Quickstart Guide** → `quickstart.md`: ✅
   - Prerequisites and installation instructions
   - Step-by-step usage guide (connect, discover, read, subscribe)
   - Complete examples with Azure OpenAI integration (FR-015)
   - Environment variable configuration (FR-028)
   - Common patterns (reactive agents, query-driven workflows)
   - Troubleshooting section
   - Links to sample applications (FR-013, FR-014)

4. **Agent Context File** → `CLAUDE.md`: ✅
   - Created via `.specify/scripts/bash/update-agent-context.sh claude`
   - Contains project overview and recent technical decisions

### Contract Test Strategy:
Contract tests will be created during implementation (Phase 4) based on the contracts defined above. Tests will:
- Verify DrasiTool implements LangChain BaseTool interface
- Assert callback handlers match DrasiNotificationHandler protocol
- Validate MCP message formats against JSON schemas
- Test error handling for all exception types

**Output**: ✅ All Phase 1 artifacts complete (data-model.md, contracts/, quickstart.md, CLAUDE.md)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

### Task Generation Strategy:

The /tasks command will generate tasks following TDD principles:

**IMPORTANT - Drasi Notification Format**:
- Drasi uses standard MCP resource update notifications: `notifications/resources/updated`
- The notification params contain three required fields:
  - `uri`: Resource URI in format `drasi://query/{query-name}`
  - `operation`: Change type - either "added", "updated", or "deleted"
  - `data`: The actual change data payload
- When receiving this notification, the library must:
  1. Extract the query name from the `uri` field (parse `drasi://query/{query-name}`)
  2. Determine the callback method from the `operation` field
  3. Invoke the appropriate callback handler method (`on_result_added`, `on_result_updated`, or `on_result_deleted`)
  4. Pass the `data` field as the parameter to the callback

1. **Foundation Tasks** (sequential):
   - Project setup (pyproject.toml, package structure, .env.example)
   - Exception hierarchy implementation (exceptions.py)
   - Data models implementation (models.py based on data-model.md)
   - Configuration models (config.py - MCPConnectionConfig, ReconnectPolicy)

2. **Contract Test Tasks** (can be parallel [P]):
   - Contract test for DrasiTool API (test_tool_contract.py)
   - Contract test for Callback handlers (test_callback_contract.py)
   - Contract test for MCP protocol messages (test_mcp_protocol.py)

3. **Core Implementation Tasks** (sequential dependencies):
   - MCP client wrapper (client.py - connection management, notification listening)
   - Notification router (parse method field, route to callbacks)
   - Callback handler protocols and base classes (callbacks.py)
   - DrasiTool implementation (tool.py - LangChain BaseTool)
   - Unit tests for each module [P where independent]

4. **Integration Tasks** (after core):
   - Integration test for MCP server communication
   - Integration test for LangChain integration
   - End-to-end test covering full workflow

5. **Sample Application Tasks** [P]:
   - Vanilla LangChain sample (samples/vanilla_langchain/)
   - LangGraph sample (samples/langgraph/)

6. **Documentation Tasks** [P]:
   - README.md with installation and quick start
   - Architecture documentation (docs/architecture.md)
   - API reference generation

### Ordering Strategy:
- **TDD Order**: Contract tests → Implementation → Integration tests
- **Dependency Order**:
  - Exceptions → Models → Config (no dependencies)
  - Client (depends on Models, Config, Exceptions)
  - Callbacks (depends on Models, Exceptions)
  - Tool (depends on Client, Callbacks, Models)
- **Parallelization**: Mark [P] for independent tasks (contract tests, unit tests for different modules, samples)

### Estimated Output:
- **Setup & Foundation**: 4-5 tasks
- **Contract Tests**: 3 tasks
- **Core Implementation**: 12-15 tasks (modules + unit tests)
- **Integration Tests**: 3-4 tasks
- **Samples**: 2 tasks
- **Documentation**: 3 tasks
- **Total**: ~27-32 numbered, dependency-ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: No constitutional violations - all complexity is justified and documented in research.md


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅
- [x] Phase 1: Design complete (/plan command) ✅
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅
- [ ] Phase 3: Tasks generated (/tasks command - NEXT STEP)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved ✅
- [x] Complexity deviations documented (none) ✅

**Execution Summary**:
- ✅ Feature spec loaded and analyzed
- ✅ Technical context filled with Python 3.13, MCP SDK, LangChain dependencies
- ✅ Constitution check passed (all 6 principles satisfied)
- ✅ Phase 0: Research completed (4 technology decisions documented)
- ✅ Phase 1: Design artifacts created (data-model.md, contracts/, quickstart.md, CLAUDE.md)
- ✅ Phase 2: Task generation strategy documented (27-32 tasks estimated)
- ✅ Ready for /tasks command

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
