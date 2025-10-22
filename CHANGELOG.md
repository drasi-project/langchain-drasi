# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- Made `LangChainMemoryHandler` import conditional to support newer LangChain versions that removed `langchain_core.memory` module
- `LangChainMemoryHandler` now gracefully falls back to `None` if the legacy memory module is not available
- Users should prefer `LangGraphMemoryHandler` for new projects as it uses the modern LangGraph checkpoint system

### Changed
- Deprecated `LangChainMemoryHandler` in favor of `LangGraphMemoryHandler` which works with modern LangChain/LangGraph versions

## [0.1.0] - 2025-10-21

### Added
- Initial release
- DrasiTool for LangChain integration
- MCP client for Drasi continuous queries
- Notification handlers: Console, Logging, Memory, LangChain, LangGraph
- Support for query discovery, reading, subscribing, and unsubscribing
- Real-time notification handling via WebSocket
- Examples: simple_example.py, langchain_react.py, langgraph_react.py
- Terminator game example demonstrating LangGraph agents with Drasi
