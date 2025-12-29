"""Tests for the export tools module."""

import pytest
from unittest.mock import patch, MagicMock

from src.tools.export import export_step, export_stl


class TestExportStep:
    """Tests for export_step function."""

    @patch("src.tools.export.send_request")
    def test_export_step_basic(self, mock_send):
        """Test basic STEP export."""
        mock_send.return_value = {"status": "ok", "path": "/exports/model.step"}
        
        result = export_step("MyModel")
        
        data = mock_send.call_args[0][1]
        assert data["name"] == "MyModel"

    @patch("src.tools.export.send_request")
    def test_export_step_returns_path(self, mock_send):
        """Test that STEP export returns file path."""
        mock_send.return_value = {"status": "ok", "path": "/exports/test.step"}
        
        result = export_step("test")
        
        assert result["path"] == "/exports/test.step"


class TestExportStl:
    """Tests for export_stl function."""

    @patch("src.tools.export.send_request")
    def test_export_stl_basic(self, mock_send):
        """Test basic STL export."""
        mock_send.return_value = {"status": "ok", "folder": "/exports/MyModel"}
        
        result = export_stl("MyModel")
        
        data = mock_send.call_args[0][1]
        assert data["name"] == "MyModel"

    @patch("src.tools.export.send_request")
    def test_export_stl_returns_folder(self, mock_send):
        """Test that STL export returns folder path."""
        mock_send.return_value = {"status": "ok", "folder": "/exports/parts"}
        
        result = export_stl("parts")
        
        assert result["folder"] == "/exports/parts"
