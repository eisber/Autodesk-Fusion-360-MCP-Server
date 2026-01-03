"""Tests for parametric tools using @fusion_tool decorator."""

import pytest
from unittest.mock import patch, MagicMock


class TestParametricTools:
    """Test suite for parametric tools."""

    @patch('src.tools.base.requests.post')
    @patch('src.tools.base.get_telemetry')
    def test_create_user_parameter(self, mock_telemetry, mock_post):
        """Test create_user_parameter sends correct request."""
        from src.tools.parametric import create_user_parameter
        
        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "parameter_name": "width",
            "value": 10.0
        }
        mock_post.return_value = mock_response
        
        result = create_user_parameter(name="width", value="10", unit="mm")
        
        assert result["success"] is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]['json']['command'] == 'create_user_parameter'

    @patch('src.tools.base.requests.post')
    @patch('src.tools.base.get_telemetry')
    def test_delete_user_parameter(self, mock_telemetry, mock_post):
        """Test delete_user_parameter sends correct request."""
        from src.tools.parametric import delete_user_parameter
        
        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        result = delete_user_parameter(name="width")
        
        assert result["success"] is True

    @patch('src.tools.base.requests.get')
    @patch('src.tools.base.get_telemetry')
    def test_get_sketch_info(self, mock_telemetry, mock_get):
        """Test get_sketch_info uses GET request."""
        from src.tools.parametric import get_sketch_info
        
        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sketch_name": "Sketch1",
            "is_fully_constrained": True
        }
        mock_get.return_value = mock_response
        
        result = get_sketch_info(sketch_index=0)
        
        assert result["sketch_name"] == "Sketch1"
        mock_get.assert_called_once()

    @patch('src.tools.base.requests.get')
    @patch('src.tools.base.get_telemetry')
    def test_get_timeline_info(self, mock_telemetry, mock_get):
        """Test get_timeline_info uses GET request."""
        from src.tools.parametric import get_timeline_info
        
        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "feature_count": 5,
            "current_position": 5
        }
        mock_get.return_value = mock_response
        
        result = get_timeline_info()
        
        assert result["feature_count"] == 5

    @patch('src.tools.base.requests.post')
    @patch('src.tools.base.get_telemetry')
    def test_check_interference(self, mock_telemetry, mock_post):
        """Test check_interference sends correct request."""
        from src.tools.parametric import check_interference
        
        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "has_interference": False
        }
        mock_post.return_value = mock_response
        
        result = check_interference(body1_index=0, body2_index=1)
        
        assert result["has_interference"] is False

    @patch('src.tools.base.requests.post')
    @patch('src.tools.base.get_telemetry')
    def test_create_offset_plane(self, mock_telemetry, mock_post):
        """Test create_offset_plane sends correct request."""
        from src.tools.parametric import create_offset_plane
        
        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "plane_name": "ConstructionPlane1"
        }
        mock_post.return_value = mock_response
        
        result = create_offset_plane(offset=5.0, base_plane="XY")
        
        assert result["success"] is True

    @patch('src.tools.base.requests.get')
    @patch('src.tools.base.get_telemetry')
    def test_list_construction_geometry(self, mock_telemetry, mock_get):
        """Test list_construction_geometry uses GET request."""
        from src.tools.parametric import list_construction_geometry
        
        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "planes": [],
            "axes": [],
            "points": []
        }
        mock_get.return_value = mock_response
        
        result = list_construction_geometry()
        
        assert "planes" in result
