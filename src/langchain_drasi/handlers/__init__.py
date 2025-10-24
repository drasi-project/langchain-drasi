"""Built-in notification handlers for common use cases.

This package provides ready-to-use notification handlers for common scenarios
like logging, printing to console, and collecting notifications in memory.
"""

from .buffer_handler import BufferHandler
from .console_handler import ConsoleHandler
from .langgraph_memory_handler import LangGraphMemoryHandler
from .logging_handler import LoggingHandler
from .memory_handler import MemoryHandler

# LangChainMemoryHandler requires langchain_core.memory which was removed in newer versions
# Import it conditionally to avoid breaking the package
try:
    from .langchain_memory_handler import LangChainMemoryHandler
    _has_langchain_memory = True
except ImportError:
    LangChainMemoryHandler = None  # type: ignore
    _has_langchain_memory = False

__all__ = [
    "BufferHandler",
    "ConsoleHandler",
    "LoggingHandler",
    "MemoryHandler",
    "LangChainMemoryHandler",
    "LangGraphMemoryHandler",
]
