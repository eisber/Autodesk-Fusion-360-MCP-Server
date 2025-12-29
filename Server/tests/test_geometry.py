"""Tests for the geometry tools module."""

import pytest
from unittest.mock import patch, MagicMock

from src.tools.geometry import (
    draw_box, draw_cylinder, draw_sphere,
    draw2Dcircle, draw_lines, draw_one_line, draw_arc,
    extrude, cut_extrude, loft, sweep
)


class TestDrawBox:
    """Tests for draw_box function."""

    @patch("src.tools.geometry.send_request")
    def test_draw_box_basic(self, mock_send):
        """Test basic box creation."""
        mock_send.return_value = {"status": "ok"}
        
        result = draw_box("5", "3", "2", 0, 0, 0, "XY")
        
        assert mock_send.called
        call_args = mock_send.call_args
        data = call_args[0][1]
        assert data["height"] == "5"
        assert data["width"] == "3"
        assert data["depth"] == "2"

    @patch("src.tools.geometry.send_request")
    def test_draw_box_with_position(self, mock_send):
        """Test box creation with position offset."""
        mock_send.return_value = {"status": "ok"}
        
        result = draw_box("10", "10", "5", 5, 5, 10, "XY")
        
        data = mock_send.call_args[0][1]
        assert data["x"] == 5
        assert data["y"] == 5
        assert data["z"] == 10

    @patch("src.tools.geometry.send_request")
    def test_draw_box_different_plane(self, mock_send):
        """Test box creation on different plane."""
        mock_send.return_value = {"status": "ok"}
        
        result = draw_box("5", "3", "2", 0, 0, 0, "YZ")
        
        data = mock_send.call_args[0][1]
        assert data["Plane"] == "YZ"


class TestDrawCylinder:
    """Tests for draw_cylinder function."""

    @patch("src.tools.geometry.send_request")
    def test_draw_cylinder_basic(self, mock_send):
        """Test basic cylinder creation."""
        mock_send.return_value = {"status": "ok"}
        
        result = draw_cylinder(2.5, 10.0, 0, 0, 0, "XY")
        
        data = mock_send.call_args[0][1]
        assert data["radius"] == 2.5
        assert data["height"] == 10.0

    @patch("src.tools.geometry.send_request")
    def test_draw_cylinder_with_position(self, mock_send):
        """Test cylinder creation with position."""
        mock_send.return_value = {"status": "ok"}
        
        result = draw_cylinder(1.0, 5.0, 3, 4, 5, "XY")
        
        data = mock_send.call_args[0][1]
        assert data["x"] == 3
        assert data["y"] == 4
        assert data["z"] == 5


class TestDrawSphere:
    """Tests for draw_sphere function."""

    @patch("src.tools.geometry.send_request")
    def test_draw_sphere_basic(self, mock_send):
        """Test basic sphere creation."""
        mock_send.return_value = {"status": "ok"}
        
        result = draw_sphere(0, 0, 0, 5)
        
        data = mock_send.call_args[0][1]
        assert data["radius"] == 5
        assert data["x"] == 0
        assert data["y"] == 0
        assert data["z"] == 0


class TestDraw2DCircle:
    """Tests for draw2Dcircle function."""

    @patch("src.tools.geometry.send_request")
    def test_draw_circle_basic(self, mock_send):
        """Test basic circle creation."""
        mock_send.return_value = {"status": "ok"}
        
        result = draw2Dcircle(3.0, 0, 0, 0, "XY")
        
        data = mock_send.call_args[0][1]
        assert data["radius"] == 3.0
        assert data["plane"] == "XY"


class TestDrawLines:
    """Tests for draw_lines function."""

    @patch("src.tools.geometry.send_request")
    def test_draw_lines_triangle(self, mock_send):
        """Test drawing a triangle."""
        mock_send.return_value = {"status": "ok"}
        points = [[0, 0, 0], [5, 0, 0], [2.5, 4, 0], [0, 0, 0]]
        
        result = draw_lines(points, "XY")
        
        data = mock_send.call_args[0][1]
        assert len(data["points"]) == 4


class TestExtrude:
    """Tests for extrude function."""

    @patch("src.tools.geometry.requests.post")
    def test_extrude_basic(self, mock_post):
        """Test basic extrusion."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response
        
        result = extrude(5.0, 0)
        
        assert result == {"status": "ok"}

    @patch("src.tools.geometry.requests.post")
    def test_extrude_with_taper(self, mock_post):
        """Test extrusion with taper angle."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response
        
        result = extrude(10.0, 15.0)
        
        assert mock_post.called


class TestCutExtrude:
    """Tests for cut_extrude function."""

    @patch("src.tools.geometry.send_request")
    def test_cut_extrude_negative_depth(self, mock_send):
        """Test cut extrusion with negative depth."""
        mock_send.return_value = {"status": "ok"}
        
        result = cut_extrude(-5.0)
        
        data = mock_send.call_args[0][1]
        assert data["depth"] == -5.0


class TestLoft:
    """Tests for loft function."""

    @patch("src.tools.geometry.send_request")
    def test_loft_two_sketches(self, mock_send):
        """Test loft between two sketches."""
        mock_send.return_value = {"status": "ok"}
        
        result = loft(2)
        
        data = mock_send.call_args[0][1]
        assert data["sketchcount"] == 2


class TestSweep:
    """Tests for sweep function."""

    @patch("src.tools.geometry.send_request")
    def test_sweep_basic(self, mock_send):
        """Test basic sweep operation."""
        mock_send.return_value = {"status": "ok"}
        
        result = sweep()
        
        assert mock_send.called
