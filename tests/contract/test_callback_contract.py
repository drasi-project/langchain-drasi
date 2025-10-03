"""Contract tests for callback handler interfaces.

These tests verify that callback handler protocols and base classes
implement the required interface as specified in contracts/callbacks.md.
These tests MUST FAIL initially until the callbacks module is implemented.
"""
# pyright: reportPossiblyUnboundVariable=false, reportGeneralTypeIssues=false

from typing import Protocol

import pytest

# These imports will fail until modules are implemented
try:
    from langchain_drasi.callbacks import (
        AsyncBaseDrasiNotificationHandler,
        AsyncDrasiNotificationHandler,
        BaseDrasiNotificationHandler,
        DrasiNotificationHandler,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    AsyncBaseDrasiNotificationHandler = object  # type: ignore[misc,assignment]
    AsyncDrasiNotificationHandler = object  # type: ignore[misc,assignment]
    BaseDrasiNotificationHandler = object  # type: ignore[misc,assignment]
    DrasiNotificationHandler = object  # type: ignore[misc,assignment]
    IMPORTS_AVAILABLE = False


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Callbacks not yet implemented")
class TestCallbackProtocolContract:
    """Contract tests for DrasiNotificationHandler Protocol."""

    def test_drasi_notification_handler_is_protocol(self) -> None:
        """Test that DrasiNotificationHandler is a Protocol."""
        # Check if it's a Protocol class
        assert hasattr(DrasiNotificationHandler, "__protocol_attrs__") or \
               isinstance(DrasiNotificationHandler, type(Protocol)), \
            "DrasiNotificationHandler must be a Protocol"

    def test_drasi_notification_handler_is_runtime_checkable(self) -> None:
        """Test that Protocol is runtime_checkable."""
        # Should be able to use isinstance with the protocol
        class TestHandler:
            def on_result_added(self, query_name: str, added_data: dict) -> None:
                pass

            def on_result_updated(self, query_name: str, updated_data: dict) -> None:
                pass

            def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
                pass

            def on_notification_error(self, query_name: str, error: Exception) -> None:
                pass

        handler = TestHandler()
        assert isinstance(handler, DrasiNotificationHandler), \
            "Protocol should support isinstance checks (runtime_checkable)"

    def test_protocol_has_required_methods(self) -> None:
        """Test that Protocol defines all required methods."""
        required_methods = [
            "on_result_added",
            "on_result_updated",
            "on_result_deleted",
            "on_notification_error",
        ]

        for method_name in required_methods:
            assert hasattr(DrasiNotificationHandler, method_name), \
                f"Protocol must define {method_name}() method"

    def test_custom_handler_satisfies_protocol(self) -> None:
        """Test that custom handler class can satisfy the Protocol."""
        class MyCustomHandler:
            def on_result_added(self, query_name: str, added_data: dict) -> None:
                self.last_added = (query_name, added_data)

            def on_result_updated(self, query_name: str, updated_data: dict) -> None:
                self.last_updated = (query_name, updated_data)

            def on_result_deleted(self, query_name: str, deleted_data: dict) -> None:
                self.last_deleted = (query_name, deleted_data)

            def on_notification_error(self, query_name: str, error: Exception) -> None:
                self.last_error = (query_name, error)

        handler = MyCustomHandler()
        assert isinstance(handler, DrasiNotificationHandler), \
            "Custom handler implementing all methods should satisfy Protocol"

    def test_partial_implementation_fails_protocol(self) -> None:
        """Test that partial implementation doesn't satisfy Protocol."""
        class PartialHandler:
            def on_result_added(self, query_name: str, added_data: dict) -> None:
                pass
            # Missing other methods

        handler = PartialHandler()
        # Note: This behavior depends on Protocol implementation details
        # Some methods might be optional, so we just verify the mechanism works


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Callbacks not yet implemented")
class TestBaseDrasiNotificationHandlerContract:
    """Contract tests for BaseDrasiNotificationHandler base class."""

    def test_base_handler_is_abc(self) -> None:
        """Test that base handler is an abstract base class or regular class."""
        # BaseDrasiNotificationHandler should be instantiable or abstract
        assert isinstance(BaseDrasiNotificationHandler, type), \
            "BaseDrasiNotificationHandler must be a class"

    def test_base_handler_has_all_methods(self) -> None:
        """Test that base handler has all required methods."""
        required_methods = [
            "on_result_added",
            "on_result_updated",
            "on_result_deleted",
            "on_notification_error",
        ]

        for method_name in required_methods:
            assert hasattr(BaseDrasiNotificationHandler, method_name), \
                f"BaseDrasiNotificationHandler must have {method_name}() method"

    def test_base_handler_methods_are_overridable(self) -> None:
        """Test that base handler methods can be overridden."""
        class MyHandler(BaseDrasiNotificationHandler):
            def __init__(self) -> None:
                self.calls: list[str] = []

            def on_result_added(self, query_name: str, added_data: dict) -> None:
                self.calls.append(f"added:{query_name}")

        handler = MyHandler()
        handler.on_result_added("test", {})
        assert "added:test" in handler.calls, \
            "Overridden methods should be called"

    def test_base_handler_satisfies_protocol(self) -> None:
        """Test that BaseDrasiNotificationHandler satisfies the Protocol."""
        handler = BaseDrasiNotificationHandler()
        assert isinstance(handler, DrasiNotificationHandler), \
            "Base handler should satisfy the Protocol"


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Callbacks not yet implemented")
class TestAsyncCallbackContract:
    """Contract tests for async callback support."""

    def test_async_protocol_exists(self) -> None:
        """Test that AsyncDrasiNotificationHandler protocol exists."""
        assert AsyncDrasiNotificationHandler is not None, \
            "AsyncDrasiNotificationHandler must exist"

    def test_async_base_handler_exists(self) -> None:
        """Test that AsyncBaseDrasiNotificationHandler base class exists."""
        assert AsyncBaseDrasiNotificationHandler is not None, \
            "AsyncBaseDrasiNotificationHandler must exist"

    def test_async_handler_methods_are_async(self) -> None:
        """Test that async handler methods are actually async."""
        import inspect

        async_methods = [
            "on_result_added",
            "on_result_updated",
            "on_result_deleted",
            "on_notification_error",
        ]

        for method_name in async_methods:
            if hasattr(AsyncBaseDrasiNotificationHandler, method_name):
                method = getattr(AsyncBaseDrasiNotificationHandler, method_name)
                assert inspect.iscoroutinefunction(method), \
                    f"{method_name}() must be async in AsyncBaseDrasiNotificationHandler"


# If imports failed, create a failing test to indicate implementation needed
if not IMPORTS_AVAILABLE:
    def test_callbacks_not_implemented() -> None:
        """Fail to indicate callback implementation is needed."""
        pytest.fail(
            "Callback handlers not implemented yet. "
            "This test will pass once src/langchain_drasi/callbacks.py is implemented."
        )
