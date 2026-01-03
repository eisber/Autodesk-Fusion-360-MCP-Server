"""Tests for configuration module."""

import pytest

from src.config import BASE_URL, HEADERS, REQUEST_TIMEOUT, endpoint


class TestConfig:
    """Test suite for configuration."""

    def test_base_url_correct(self):
        """Test that BASE_URL is set correctly."""
        assert BASE_URL == "http://localhost:5000"

    def test_headers_has_content_type(self):
        """Test headers include content type."""
        assert "Content-Type" in HEADERS
        assert HEADERS["Content-Type"] == "application/json"

    def test_request_timeout_is_positive(self):
        """Test request timeout is a positive number."""
        assert REQUEST_TIMEOUT > 0

    def test_endpoint_function(self):
        """Test the endpoint() helper function."""
        assert endpoint("test") == "http://localhost:5000/test"
        assert endpoint("model_state") == "http://localhost:5000/model_state"
