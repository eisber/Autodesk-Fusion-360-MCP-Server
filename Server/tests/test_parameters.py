"""Tests for the parameters tools module."""

import pytest
from unittest.mock import patch, MagicMock

from src.tools.parameters import count, list_parameters, change_parameter


class TestCount:
    """Tests for count function."""

    @patch("src.tools.parameters.send_request")
    def test_count_returns_result(self, mock_send):
        """Test count returns result."""
        mock_send.return_value = {"count": 5}
        
        result = count()
        
        assert result == {"count": 5}


class TestListParameters:
    """Tests for list_parameters function."""

    @patch("src.tools.parameters.send_request")
    def test_list_parameters_returns_list(self, mock_send):
        """Test list_parameters returns parameter list."""
        mock_send.return_value = {
            "parameters": [
                {"name": "Width", "value": "10 mm"},
                {"name": "Height", "value": "20 mm"}
            ]
        }
        
        result = list_parameters()
        
        assert "parameters" in result
        assert len(result["parameters"]) == 2


class TestChangeParameter:
    """Tests for change_parameter function."""

    @patch("src.tools.parameters.send_request")
    def test_change_parameter_basic(self, mock_send):
        """Test basic parameter change."""
        mock_send.return_value = {"status": "ok"}
        
        result = change_parameter("Width", "15 mm")
        
        data = mock_send.call_args[0][1]
        assert data["name"] == "Width"
        assert data["value"] == "15 mm"

    @patch("src.tools.parameters.send_request")
    def test_change_parameter_expression(self, mock_send):
        """Test parameter change with expression."""
        mock_send.return_value = {"status": "ok"}
        
        result = change_parameter("Height", "Width * 2")
        
        data = mock_send.call_args[0][1]
        assert data["value"] == "Width * 2"
