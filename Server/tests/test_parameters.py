"""Tests for parameter tools using @fusion_tool decorator."""

import pytest
from unittest.mock import patch, MagicMock


class TestParameterTools:
    """Test suite for parameter tools."""

    @patch('src.tools.base.requests.get')
    @patch('src.tools.base.get_telemetry')
    def test_list_parameters(self, mock_telemetry, mock_get):
        """Test list_parameters sends correct request."""
        from src.tools.parameters import list_parameters
        
        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "parameters": [{"name": "width", "value": 10}]
        }
        mock_get.return_value = mock_response
        
        result = list_parameters()
        
        assert len(result["parameters"]) == 1
        mock_get.assert_called_once()

    @patch('src.tools.base.requests.post')
    @patch('src.tools.base.get_telemetry')
    def test_set_parameter(self, mock_telemetry, mock_post):
        """Test set_parameter sends correct request."""
        from src.tools.parameters import set_parameter
        
        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        result = set_parameter(name="width", value="20")
        
        assert result["success"] is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]['json']['name'] == 'width'
        assert call_kwargs[1]['json']['value'] == '20'
