"""Tests for the config module."""

import pytest

from src.config import ENDPOINTS, HEADERS, BASE_URL, REQUEST_TIMEOUT


class TestEndpoints:
    """Tests for endpoint configuration."""

    def test_base_url_correct(self):
        """Test that BASE_URL is configured correctly."""
        assert BASE_URL == "http://localhost:5000"

    def test_model_state_endpoint_exists(self):
        """Test model_state endpoint is defined."""
        assert "model_state" in ENDPOINTS
        assert ENDPOINTS["model_state"] == f"{BASE_URL}/model_state"

    def test_draw_box_endpoint_exists(self):
        """Test draw_box endpoint is defined."""
        assert "draw_box" in ENDPOINTS

    def test_draw_cylinder_endpoint_exists(self):
        """Test draw_cylinder endpoint is defined."""
        assert "draw_cylinder" in ENDPOINTS

    def test_extrude_endpoint_exists(self):
        """Test extrude endpoint is defined."""
        assert "extrude" in ENDPOINTS

    def test_all_required_endpoints_exist(self):
        """Test all major endpoint categories exist."""
        required_endpoints = [
            # Model state
            "model_state", "test_connection",
            # 3D Primitives
            "draw_box", "draw_cylinder", "draw_sphere",
            # 2D Sketches
            "draw2Dcircle", "draw_lines", "spline",
            # Extrusions
            "extrude", "extrude_thin", "cut_extrude",
            # Operations
            "loft", "sweep", "revolve", "boolean_operation",
            # Patterns
            "circular_pattern", "rectangular_pattern",
            # Export
            "export_step", "export_stl",
            # Utility
            "undo", "delete_everything"
        ]
        for endpoint in required_endpoints:
            assert endpoint in ENDPOINTS, f"Missing endpoint: {endpoint}"


class TestHeaders:
    """Tests for headers configuration."""

    def test_content_type_header(self):
        """Test Content-Type header is set."""
        assert "Content-Type" in HEADERS
        assert HEADERS["Content-Type"] == "application/json"


class TestTimeouts:
    """Tests for timeout configuration."""

    def test_request_timeout_is_positive(self):
        """Test REQUEST_TIMEOUT is a positive number."""
        assert REQUEST_TIMEOUT > 0
        assert isinstance(REQUEST_TIMEOUT, (int, float))
