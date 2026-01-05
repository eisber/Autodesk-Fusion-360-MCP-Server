"""Tests for the client module."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.client import send_get_request, send_request


class TestSendRequest:
    """Tests for the send_request function."""

    @patch("src.client.requests.post")
    def test_send_request_success(self, mock_post):
        """Test successful POST request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = send_request(
            "http://localhost:5000/test", {"key": "value"}, {"Content-Type": "application/json"}
        )

        assert result == {"status": "ok"}
        mock_post.assert_called_once()

    @patch("src.client.requests.post")
    def test_send_request_with_empty_data(self, mock_post):
        """Test POST request with empty data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = send_request("http://localhost:5000/test", {}, {})

        assert result == {"status": "ok"}

    @patch("src.client.requests.post")
    def test_send_request_returns_json(self, mock_post):
        """Test that send_request returns JSON response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body_count": 5, "sketch_count": 3}
        mock_post.return_value = mock_response

        result = send_request("http://localhost:5000/model", {}, {})

        assert result["body_count"] == 5
        assert result["sketch_count"] == 3


class TestSendGetRequest:
    """Tests for the send_get_request function."""

    @patch("src.client.requests.get")
    def test_send_get_request_success(self, mock_get):
        """Test successful GET request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "connected"}
        mock_get.return_value = mock_response

        result = send_get_request("http://localhost:5000/status")

        assert result == {"status": "connected"}

    @patch("src.client.requests.get")
    def test_send_get_request_with_model_state(self, mock_get):
        """Test GET request for model state."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body_count": 2,
            "sketch_count": 1,
            "design_name": "TestDesign",
        }
        mock_get.return_value = mock_response

        result = send_get_request("http://localhost:5000/model_state")

        assert result["body_count"] == 2
        assert result["design_name"] == "TestDesign"
