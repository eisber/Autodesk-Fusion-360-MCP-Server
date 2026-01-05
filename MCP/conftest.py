"""Root conftest for MCP commands tests.

This file installs mock adsk modules before any test collection happens.
Includes mocks for Fusion's threading/custom event system.
"""

import queue
import sys
import threading
from unittest.mock import MagicMock

# Global storage for mock custom event system
_mock_event_handlers = {}  # event_name -> list of handlers
_mock_event_queue = queue.Queue()


class MockCustomEventHandler:
    """Mock base class for Fusion custom event handlers."""

    def __init__(self):
        pass

    def notify(self, args):
        """Override in subclass to handle events."""
        pass


class MockCustomEvent:
    """Mock Fusion custom event that can have handlers added."""

    def __init__(self, event_name: str):
        self.event_name = event_name
        self._handlers = []

    def add(self, handler):
        """Add a handler to this event."""
        self._handlers.append(handler)
        if self.event_name not in _mock_event_handlers:
            _mock_event_handlers[self.event_name] = []
        _mock_event_handlers[self.event_name].append(handler)

    def remove(self, handler):
        """Remove a handler from this event."""
        if handler in self._handlers:
            self._handlers.remove(handler)
        if self.event_name in _mock_event_handlers:
            if handler in _mock_event_handlers[self.event_name]:
                _mock_event_handlers[self.event_name].remove(handler)


class MockCustomEventArgs:
    """Mock args passed to custom event notify()."""

    def __init__(self, additional_info: str = ""):
        self.additionalInfo = additional_info


def _mock_register_custom_event(event_name: str) -> MockCustomEvent:
    """Mock for app.registerCustomEvent()."""
    return MockCustomEvent(event_name)


def _mock_fire_custom_event(event_name: str, additional_info: str = ""):
    """Mock for app.fireCustomEvent() - immediately notifies handlers."""
    if event_name in _mock_event_handlers:
        args = MockCustomEventArgs(additional_info)
        for handler in _mock_event_handlers[event_name]:
            try:
                handler.notify(args)
            except Exception:
                pass  # Swallow errors like real Fusion


def _mock_unregister_custom_event(event_name: str):
    """Mock for app.unregisterCustomEvent()."""
    _mock_event_handlers.pop(event_name, None)


# Install mock adsk module IMMEDIATELY at import time (before pytest_configure)
# This is necessary because pytest imports modules during collection
def _install_mock_adsk():
    """Install mock adsk module immediately."""
    if "adsk" in sys.modules:
        return  # Already installed

    mock_adsk = MagicMock()
    mock_core = MagicMock()
    mock_fusion = MagicMock()

    mock_adsk.core = mock_core
    mock_adsk.fusion = mock_fusion

    # Mock Application
    mock_app = MagicMock()
    mock_ui = MagicMock()
    mock_app.userInterface = mock_ui

    # Mock custom event system
    mock_app.registerCustomEvent = _mock_register_custom_event
    mock_app.fireCustomEvent = _mock_fire_custom_event
    mock_app.unregisterCustomEvent = _mock_unregister_custom_event

    mock_core.Application.get.return_value = mock_app

    # Mock CustomEventHandler base class
    mock_core.CustomEventHandler = MockCustomEventHandler

    # Mock PaletteDockingStates
    mock_core.PaletteDockingStates = MagicMock()
    mock_core.PaletteDockingStates.PaletteDockStateRight = 1
    mock_core.PaletteDockingStates.PaletteDockStateFloating = 0

    # Mock LogLevels
    mock_core.LogLevels = MagicMock()
    mock_core.LogLevels.InfoLogLevel = 2

    # Mock FeatureOperations enum
    mock_fusion.FeatureOperations = MagicMock()
    mock_fusion.FeatureOperations.NewBodyFeatureOperation = 0
    mock_fusion.FeatureOperations.JoinFeatureOperation = 1
    mock_fusion.FeatureOperations.CutFeatureOperation = 2
    mock_fusion.FeatureOperations.IntersectFeatureOperation = 3

    # Install mocks
    sys.modules["adsk"] = mock_adsk
    sys.modules["adsk.core"] = mock_core
    sys.modules["adsk.fusion"] = mock_fusion


# Install immediately when this file is imported
_install_mock_adsk()


def pytest_configure(config):
    """Ensure mock adsk module is installed before test collection."""
    _install_mock_adsk()


def get_mock_event_handlers():
    """Get the current mock event handlers (for testing)."""
    return _mock_event_handlers


def clear_mock_events():
    """Clear all mock event handlers and queue."""
    global _mock_event_handlers
    _mock_event_handlers = {}
    while not _mock_event_queue.empty():
        try:
            _mock_event_queue.get_nowait()
        except queue.Empty:
            break
