"""Tests for the patterns tools module."""

import pytest
from unittest.mock import patch, MagicMock

from src.tools.patterns import (
    circular_pattern, rectangular_pattern, move_latest_body
)


class TestCircularPattern:
    """Tests for circular_pattern function."""

    @patch("src.tools.patterns.send_request")
    def test_circular_pattern_basic(self, mock_send):
        """Test basic circular pattern."""
        mock_send.return_value = {"status": "ok"}
        
        result = circular_pattern("XY", 6.0, "Z")
        
        data = mock_send.call_args[0][1]
        assert data["plane"] == "XY"
        assert data["quantity"] == 6.0
        assert data["axis"] == "Z"

    @patch("src.tools.patterns.send_request")
    def test_circular_pattern_different_axis(self, mock_send):
        """Test circular pattern with different axis."""
        mock_send.return_value = {"status": "ok"}
        
        result = circular_pattern("YZ", 4.0, "X")
        
        data = mock_send.call_args[0][1]
        assert data["axis"] == "X"


class TestRectangularPattern:
    """Tests for rectangular_pattern function."""

    @patch("src.tools.patterns.send_request")
    def test_rectangular_pattern_basic(self, mock_send):
        """Test basic rectangular pattern."""
        mock_send.return_value = {"status": "ok"}
        
        result = rectangular_pattern("XY", 3.0, 4.0, 10.0, 15.0, "X", "Y")
        
        data = mock_send.call_args[0][1]
        assert data["quantity_one"] == 3.0
        assert data["quantity_two"] == 4.0
        assert data["distance_one"] == 10.0
        assert data["distance_two"] == 15.0

    @patch("src.tools.patterns.send_request")
    def test_rectangular_pattern_axes(self, mock_send):
        """Test rectangular pattern axis configuration."""
        mock_send.return_value = {"status": "ok"}
        
        result = rectangular_pattern("XZ", 2.0, 3.0, 5.0, 10.0, "X", "Z")
        
        data = mock_send.call_args[0][1]
        assert data["axis_one"] == "X"
        assert data["axis_two"] == "Z"


class TestMoveLatestBody:
    """Tests for move_latest_body function."""

    @patch("src.tools.patterns.send_request")
    def test_move_body_basic(self, mock_send):
        """Test basic body movement."""
        mock_send.return_value = {"status": "ok"}
        
        result = move_latest_body(5.0, 10.0, 15.0)
        
        data = mock_send.call_args[0][1]
        assert data["x"] == 5.0
        assert data["y"] == 10.0
        assert data["z"] == 15.0

    @patch("src.tools.patterns.send_request")
    def test_move_body_negative(self, mock_send):
        """Test body movement with negative values."""
        mock_send.return_value = {"status": "ok"}
        
        result = move_latest_body(-3.0, 0.0, -5.0)
        
        data = mock_send.call_args[0][1]
        assert data["x"] == -3.0
        assert data["z"] == -5.0
