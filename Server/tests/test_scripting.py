"""Tests for the scripting tools module."""

import pytest
from unittest.mock import patch, MagicMock

from src.tools.scripting import execute_fusion_script, cancel_fusion_task


class TestExecuteFusionScript:
    """Tests for execute_fusion_script function."""

    @patch("src.tools.scripting.submit_task_and_wait")
    def test_execute_script_success(self, mock_submit):
        """Test successful script execution."""
        mock_submit.return_value = {
            "success": True,
            "return_value": "test_result"
        }
        
        result = execute_fusion_script("result = 'test_result'")
        
        assert result["success"] is True
        assert result["return_value"] == "test_result"
        mock_submit.assert_called_once()

    @patch("src.tools.scripting.submit_task_and_wait")
    def test_execute_script_queue_failed(self, mock_submit):
        """Test script execution when submission fails."""
        mock_submit.side_effect = Exception("Connection refused")
        
        result = execute_fusion_script("result = 1")
        
        assert result["success"] is False
        assert "Connection refused" in result["error"]

    @patch("src.tools.scripting.submit_task_and_wait")
    def test_execute_script_with_error(self, mock_submit):
        """Test script execution with error."""
        mock_submit.return_value = {
            "success": False,
            "error": "SyntaxError: invalid syntax",
            "error_line": 1
        }
        
        result = execute_fusion_script("def broken(")
        
        assert result["success"] is False
        assert "SyntaxError" in result["error"]

    @patch("src.tools.scripting.submit_task_and_wait")
    def test_execute_script_with_progress(self, mock_submit):
        """Test script execution with progress callback."""
        mock_submit.return_value = {"success": True}
        
        result = execute_fusion_script("progress(50, 'half done')")
        
        # Verify on_progress callback was passed
        call_args = mock_submit.call_args
        assert call_args[1].get("on_progress") is not None


class TestCancelFusionTask:
    """Tests for cancel_fusion_task function."""

    @patch("src.tools.scripting.sse_cancel_task")
    def test_cancel_task_success(self, mock_cancel):
        """Test successful task cancellation."""
        mock_cancel.return_value = {
            "success": True,
            "task_id": "abc12345",
            "status": "cancelled"
        }
        
        result = cancel_fusion_task("abc12345")
        
        assert result["success"] is True
        mock_cancel.assert_called_once_with("abc12345")

    @patch("src.tools.scripting.sse_cancel_task")
    def test_cancel_task_not_found(self, mock_cancel):
        """Test cancelling non-existent task."""
        mock_cancel.return_value = {
            "success": False,
            "error": "Task not found"
        }
        
        result = cancel_fusion_task("invalid_id")
        
        assert result["success"] is False

    @patch("src.tools.scripting.sse_cancel_task")
    def test_cancel_task_exception(self, mock_cancel):
        """Test cancellation with exception."""
        mock_cancel.side_effect = Exception("Connection error")
        
        result = cancel_fusion_task("abc12345")
        
        assert result["success"] is False
        assert "Connection error" in result["error"]
