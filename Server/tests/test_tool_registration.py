"""Tests for tool registration."""

import pytest

from src.tools import (
    draw_box, draw_cylinder, draw_sphere,
    circular_pattern, rectangular_pattern,
    export_step, export_stl,
    test_connection, get_model_state,
    count, list_parameters
)


class TestToolImports:
    """Tests for tool imports."""

    def test_geometry_tools_importable(self):
        """Test geometry tools can be imported."""
        assert draw_box is not None
        assert draw_cylinder is not None
        assert draw_sphere is not None

    def test_pattern_tools_importable(self):
        """Test pattern tools can be imported."""
        assert circular_pattern is not None
        assert rectangular_pattern is not None

    def test_export_tools_importable(self):
        """Test export tools can be imported."""
        assert export_step is not None
        assert export_stl is not None

    def test_validation_tools_importable(self):
        """Test validation tools can be imported."""
        assert test_connection is not None
        assert get_model_state is not None

    def test_parameter_tools_importable(self):
        """Test parameter tools can be imported."""
        assert count is not None
        assert list_parameters is not None


class TestToolCallable:
    """Tests for tool callability."""

    def test_draw_box_callable(self):
        """Test draw_box is callable."""
        assert callable(draw_box)

    def test_circular_pattern_callable(self):
        """Test circular_pattern is callable."""
        assert callable(circular_pattern)

    def test_export_step_callable(self):
        """Test export_step is callable."""
        assert callable(export_step)
