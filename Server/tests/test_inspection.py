"""Tests for the inspection tools module."""

import pytest
from unittest.mock import patch, MagicMock

from src.tools.inspection import inspect_adsk_api, get_adsk_class_info


class TestInspectAdskApi:
    """Tests for inspect_adsk_api function."""

    @patch("src.tools.inspection.execute_fusion_script")
    def test_inspect_module_success(self, mock_execute):
        """Test successful module inspection."""
        mock_execute.return_value = {
            "success": True,
            "return_value": {
                "path": "adsk.fusion",
                "type": "module",
                "members": [
                    {"name": "Sketch", "type": "class"},
                    {"name": "BRepBody", "type": "class"},
                ],
                "member_count": 2,
            }
        }
        
        result = inspect_adsk_api("adsk.fusion")
        
        assert result["success"] is True
        assert result["path"] == "adsk.fusion"
        assert result["type"] == "module"
        assert len(result["members"]) == 2
        mock_execute.assert_called_once()

    @patch("src.tools.inspection.execute_fusion_script")
    def test_inspect_class_success(self, mock_execute):
        """Test successful class inspection."""
        mock_execute.return_value = {
            "success": True,
            "return_value": {
                "path": "adsk.fusion.Sketch",
                "type": "class",
                "docstring": "Represents a sketch in the design.",
                "members": [
                    {"name": "sketchCurves", "type": "property", "docstring": "Returns the curves."},
                    {"name": "add", "type": "method", "signature": "(plane)"},
                ],
                "member_count": 2,
            }
        }
        
        result = inspect_adsk_api("adsk.fusion.Sketch")
        
        assert result["success"] is True
        assert result["path"] == "adsk.fusion.Sketch"
        assert result["type"] == "class"
        assert "docstring" in result
        mock_execute.assert_called_once()

    @patch("src.tools.inspection.execute_fusion_script")
    def test_inspect_method_success(self, mock_execute):
        """Test successful method inspection."""
        mock_execute.return_value = {
            "success": True,
            "return_value": {
                "path": "adsk.core.Point3D.create",
                "type": "method",
                "signature": "create(x: float, y: float, z: float) -> Point3D",
                "docstring": "Creates a Point3D object.",
            }
        }
        
        result = inspect_adsk_api("adsk.core.Point3D.create")
        
        assert result["success"] is True
        assert result["type"] == "method"
        assert "signature" in result
        mock_execute.assert_called_once()

    @patch("src.tools.inspection.execute_fusion_script")
    def test_inspect_invalid_path(self, mock_execute):
        """Test inspection with invalid path."""
        mock_execute.return_value = {
            "success": True,
            "return_value": {
                "error": '"NonExistent" not found in adsk.fusion',
                "path": "adsk.fusion.NonExistent",
                "available": ["Sketch", "BRepBody", "Component"],
            }
        }
        
        result = inspect_adsk_api("adsk.fusion.NonExistent")
        
        assert result["success"] is True
        assert "error" in result
        assert "available" in result

    @patch("src.tools.inspection.execute_fusion_script")
    def test_inspect_script_execution_failure(self, mock_execute):
        """Test inspection when script execution fails."""
        mock_execute.return_value = {
            "success": False,
            "error": "Connection refused",
        }
        
        result = inspect_adsk_api("adsk.fusion")
        
        assert result["success"] is False
        assert "error" in result

    @patch("src.tools.inspection.execute_fusion_script")
    def test_inspect_default_path(self, mock_execute):
        """Test inspection uses default path."""
        mock_execute.return_value = {
            "success": True,
            "return_value": {"path": "adsk.fusion", "type": "module"}
        }
        
        result = inspect_adsk_api()  # Uses default "adsk.fusion"
        
        assert result["success"] is True
        # Verify the script contains the default path
        call_args = mock_execute.call_args[0][0]
        assert "'adsk.fusion'" in call_args


class TestGetAdskClassInfo:
    """Tests for get_adsk_class_info function."""

    @patch("src.tools.inspection.execute_fusion_script")
    def test_get_class_info_success(self, mock_execute):
        """Test successful class info retrieval."""
        mock_execute.return_value = {
            "success": True,
            "return_value": {
                "class_name": "Sketch",
                "path": "adsk.fusion.Sketch",
                "docstring": "class Sketch:\n    # Properties\n    # sketchCurves\n",
                "properties": [{"name": "sketchCurves", "summary": "Returns curves"}],
                "methods": [{"name": "add", "signature": "(plane)", "summary": "Add sketch"}],
                "property_count": 1,
                "method_count": 1,
            }
        }
        
        result = get_adsk_class_info("adsk.fusion.Sketch")
        
        assert result["success"] is True
        assert result["class_name"] == "Sketch"
        assert "docstring" in result
        assert result["property_count"] == 1
        assert result["method_count"] == 1

    @patch("src.tools.inspection.execute_fusion_script")
    def test_get_class_info_with_formatted_docstring(self, mock_execute):
        """Test that class info returns properly formatted docstring."""
        mock_execute.return_value = {
            "success": True,
            "return_value": {
                "class_name": "Point3D",
                "path": "adsk.core.Point3D",
                "docstring": """class Point3D:
    # Properties
    # x: The x coordinate.
    # y: The y coordinate.
    # z: The z coordinate.
    
    # Methods
    # def create(x, y, z)
    #     Creates a new Point3D.""",
                "properties": [],
                "methods": [],
                "property_count": 3,
                "method_count": 1,
            }
        }
        
        result = get_adsk_class_info("adsk.core.Point3D")
        
        assert result["success"] is True
        assert "class Point3D:" in result["docstring"]
        assert "# Properties" in result["docstring"]
        assert "# Methods" in result["docstring"]

    @patch("src.tools.inspection.execute_fusion_script")
    def test_get_class_info_invalid_path(self, mock_execute):
        """Test class info with invalid path."""
        mock_execute.return_value = {
            "success": True,
            "return_value": {
                "error": "Path not found: adsk.fusion.NotAClass"
            }
        }
        
        result = get_adsk_class_info("adsk.fusion.NotAClass")
        
        assert result["success"] is True
        assert "error" in result

    @patch("src.tools.inspection.execute_fusion_script")
    def test_get_class_info_execution_failure(self, mock_execute):
        """Test class info when script execution fails."""
        mock_execute.return_value = {
            "success": False,
            "error": "Timeout",
            "traceback": "...",
        }
        
        result = get_adsk_class_info("adsk.fusion.Sketch")
        
        assert result["success"] is False
        assert "error" in result

    @patch("src.tools.inspection.execute_fusion_script")
    def test_get_class_info_exception_handling(self, mock_execute):
        """Test class info handles exceptions gracefully."""
        mock_execute.side_effect = Exception("Network error")
        
        result = get_adsk_class_info("adsk.fusion.Sketch")
        
        assert result["success"] is False
        assert "Network error" in result["error"]
        assert "traceback" in result
