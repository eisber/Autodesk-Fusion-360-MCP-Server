"""Tests for validation tools using @fusion_tool decorator."""

from unittest.mock import MagicMock, patch

import pytest


class TestValidationTools:
    """Test suite for validation tools."""

    @patch("src.tools.base.requests.post")
    @patch("src.tools.base.get_telemetry")
    def test_test_connection(self, mock_telemetry, mock_post):
        """Test test_connection sends correct request."""
        from src.tools.validation import test_connection

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "connected"}
        mock_post.return_value = mock_response

        result = test_connection()

        assert result["status"] == "connected"
        mock_post.assert_called_once()

    @patch("src.tools.base.requests.get")
    @patch("src.tools.base.get_telemetry")
    def test_get_model_state(self, mock_telemetry, mock_get):
        """Test get_model_state uses GET request."""
        from src.tools.validation import get_model_state

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body_count": 2,
            "sketch_count": 1,
            "design_name": "TestDesign",
        }
        mock_get.return_value = mock_response

        result = get_model_state()

        assert result["body_count"] == 2
        assert result["design_name"] == "TestDesign"
        mock_get.assert_called_once()

    @patch("src.tools.base.requests.get")
    @patch("src.tools.base.get_telemetry")
    def test_get_faces_info(self, mock_telemetry, mock_get):
        """Test get_faces_info uses GET request."""
        from src.tools.validation import get_faces_info

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"face_count": 6, "faces": []}
        mock_get.return_value = mock_response

        result = get_faces_info(body_index=0)

        assert result["face_count"] == 6
        mock_get.assert_called_once()

    @patch("src.tools.base.requests.post")
    @patch("src.tools.base.get_telemetry")
    def test_delete_all(self, mock_telemetry, mock_post):
        """Test delete_all sends correct request."""
        from src.tools.validation import delete_all

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "bodies": 2, "sketches": 1}
        mock_post.return_value = mock_response

        result = delete_all()

        assert result["success"] is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["command"] == "delete_all"

    @patch("src.tools.base.requests.post")
    @patch("src.tools.base.get_telemetry")
    def test_delete_all_with_params(self, mock_telemetry, mock_post):
        """Test delete_all with selective deletion parameters."""
        from src.tools.validation import delete_all

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "bodies": 2, "sketches": 0}
        mock_post.return_value = mock_response

        result = delete_all(bodies=True, sketches=False, construction=False)

        assert result["success"] is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["bodies"] is True
        assert call_kwargs[1]["json"]["sketches"] is False

    @patch("src.tools.base.requests.post")
    @patch("src.tools.base.get_telemetry")
    def test_undo(self, mock_telemetry, mock_post):
        """Test undo sends correct request."""
        from src.tools.validation import undo

        mock_telemetry.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        result = undo()

        assert result["success"] is True
        mock_post.assert_called_once()
