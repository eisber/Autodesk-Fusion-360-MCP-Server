"""Tests for tool registration."""

import pytest
from unittest.mock import patch, MagicMock

from src import tools
from src.tools import (
    test_connection as connection_test_tool, get_model_state,
    list_parameters,
    measure_distance, execute_fusion_script,
)


class TestAllExportsExist:
    """Tests that all __all__ exports exist and are callable."""
    
    def test_all_exports_exist(self):
        """Verify every name in __all__ actually exists in the module."""
        missing = []
        for name in tools.__all__:
            if not hasattr(tools, name):
                missing.append(name)
        assert not missing, f"Missing exports from __all__: {missing}"
    
    def test_all_exports_callable(self):
        """Verify every exported tool is callable."""
        not_callable = []
        for name in tools.__all__:
            func = getattr(tools, name, None)
            if func is not None and not callable(func):
                not_callable.append(name)
        assert not not_callable, f"Non-callable exports: {not_callable}"
    
    def test_no_duplicate_exports(self):
        """Verify no duplicate names in __all__."""
        seen = set()
        duplicates = []
        for name in tools.__all__:
            if name in seen:
                duplicates.append(name)
            seen.add(name)
        assert not duplicates, f"Duplicate exports: {duplicates}"


class TestToolImports:
    """Tests for tool imports."""

    def test_validation_tools_importable(self):
        """Test validation tools can be imported."""
        assert connection_test_tool is not None
        assert get_model_state is not None

    def test_parameter_tools_importable(self):
        """Test parameter tools can be imported."""
        assert list_parameters is not None

    def test_measurement_tools_importable(self):
        """Test measurement tools can be imported."""
        assert measure_distance is not None

    def test_scripting_tools_importable(self):
        """Test scripting tools can be imported."""
        assert execute_fusion_script is not None


class TestToolCallable:
    """Tests for tool callability."""

    def test_connection_tool_callable(self):
        """Test connection_test_tool is callable."""
        assert callable(connection_test_tool)

    def test_execute_fusion_script_callable(self):
        """Test execute_fusion_script is callable."""
        assert callable(execute_fusion_script)


@patch('src.tools.base.requests.post')
@patch('src.tools.base.get_telemetry')
def test_connection_tool_integration(mock_telemetry, mock_post):
    """Integration test: connection test tool works with mocked server."""
    mock_telemetry.return_value = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "connected"}
    mock_post.return_value = mock_response
    
    result = connection_test_tool()
    assert result["status"] == "connected"
