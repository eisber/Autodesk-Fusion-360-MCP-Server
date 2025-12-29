"""Tests for the scripting tools module."""

import pytest
from unittest.mock import patch, MagicMock

from src.tools.scripting import execute_fusion_script


class TestExecuteFusionScript:
    """Tests for execute_fusion_script function."""

    @patch("src.tools.scripting.requests.get")
    @patch("src.tools.scripting.requests.post")
    def test_execute_script_success(self, mock_post, mock_get):
        """Test successful script execution."""
        # Mock the POST to queue script
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response
        
        # Mock the GET to retrieve result
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "success": True,
            "return_value": "test_result"
        }
        mock_get.return_value = mock_get_response
        
        result = execute_fusion_script("result = 'test_result'")
        
        assert result["success"] is True
        assert result["return_value"] == "test_result"

    @patch("src.tools.scripting.requests.post")
    def test_execute_script_queue_failed(self, mock_post):
        """Test script execution when queue fails."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response
        
        result = execute_fusion_script("result = 1")
        
        assert result["success"] is False
        assert "Failed to queue script" in result["error"]

    @patch("src.tools.scripting.requests.get")
    @patch("src.tools.scripting.requests.post")
    def test_execute_script_with_error(self, mock_post, mock_get):
        """Test script execution with error."""
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response
        
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "success": False,
            "error": "SyntaxError: invalid syntax",
            "error_line": 1
        }
        mock_get.return_value = mock_get_response
        
        result = execute_fusion_script("def broken(")
        
        assert result["success"] is False
        assert "SyntaxError" in result["error"]
