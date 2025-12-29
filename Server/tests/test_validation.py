"""Tests for the validation tools module."""

import pytest
from unittest.mock import patch, MagicMock

from src.tools.validation import (
    test_connection, get_model_state, get_faces_info, delete_all, undo
)


class TestTestConnection:
    """Tests for test_connection function."""

    @patch("src.tools.validation.send_request")
    def test_connection_success(self, mock_send):
        """Test successful connection."""
        mock_send.return_value = {"status": "connected"}
        
        result = test_connection()
        
        assert result["status"] == "connected"


class TestGetModelState:
    """Tests for get_model_state function."""

    @patch("src.tools.validation.send_get_request")
    def test_get_model_state_basic(self, mock_get):
        """Test getting model state."""
        mock_get.return_value = {
            "body_count": 3,
            "sketch_count": 2,
            "design_name": "TestDesign"
        }
        
        result = get_model_state()
        
        assert result["body_count"] == 3
        assert result["sketch_count"] == 2

    @patch("src.tools.validation.send_get_request")
    def test_get_model_state_empty(self, mock_get):
        """Test model state for empty design."""
        mock_get.return_value = {
            "body_count": 0,
            "sketch_count": 0,
            "design_name": "Untitled"
        }
        
        result = get_model_state()
        
        assert result["body_count"] == 0


class TestGetFacesInfo:
    """Tests for get_faces_info function."""

    @patch("src.tools.validation.send_get_request")
    def test_get_faces_info_basic(self, mock_get):
        """Test getting faces info."""
        mock_get.return_value = {
            "face_count": 6,
            "faces": [
                {"index": 0, "type": "plane", "area": 100.0}
            ]
        }
        
        result = get_faces_info(0)
        
        assert result["face_count"] == 6


class TestDeleteAll:
    """Tests for delete_all function."""

    @patch("src.tools.validation.send_request")
    def test_delete_all_success(self, mock_send):
        """Test deleting all objects."""
        mock_send.return_value = {"status": "deleted"}
        
        result = delete_all()
        
        assert result["status"] == "deleted"


class TestUndo:
    """Tests for undo function."""

    @patch("src.tools.validation.send_request")
    def test_undo_success(self, mock_send):
        """Test undo operation."""
        mock_send.return_value = {"status": "ok"}
        
        result = undo()
        
        assert result["status"] == "ok"
