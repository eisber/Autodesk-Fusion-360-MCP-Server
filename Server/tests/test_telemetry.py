"""Tests for telemetry module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.telemetry import (
    TelemetryClient,
    TelemetryConfig,
    TelemetryLevel,
    get_telemetry,
    get_telemetry_status,
    set_telemetry_level,
    track_event,
    tracked_tool,
)


class TestTelemetryLevel:
    """Test TelemetryLevel enum."""

    def test_level_values(self):
        """Test that levels have expected values."""
        assert TelemetryLevel.OFF.value == "off"
        assert TelemetryLevel.BASIC.value == "basic"
        assert TelemetryLevel.DETAILED.value == "detailed"

    def test_level_from_string(self):
        """Test creating level from string."""
        assert TelemetryLevel("off") == TelemetryLevel.OFF
        assert TelemetryLevel("basic") == TelemetryLevel.BASIC
        assert TelemetryLevel("detailed") == TelemetryLevel.DETAILED


class TestTelemetryConfig:
    """Test TelemetryConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TelemetryConfig()
        assert config.level == TelemetryLevel.DETAILED  # Default is DETAILED
        assert config.user_id  # Should have a UUID
        assert config.first_seen  # Should have a timestamp

    def test_save_and_load_config(self):
        """Test config persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "telemetry.json"
            config_dir = Path(tmpdir)

            # Create and save config - patch with Path objects
            with patch("src.telemetry.CONFIG_FILE", config_file):
                with patch("src.telemetry.CONFIG_DIR", config_dir):
                    config = TelemetryConfig(
                        level=TelemetryLevel.DETAILED,
                        user_id="test-user-123",
                        first_seen="2024-01-01T00:00:00",
                    )
                    config.save()

                    # Verify file was created
                    assert config_file.exists()

                    # Load and verify
                    loaded = TelemetryConfig.load()
                    assert loaded.level == TelemetryLevel.DETAILED
                    assert loaded.user_id == "test-user-123"
                    assert loaded.first_seen == "2024-01-01T00:00:00"


class TestTelemetryClientSanitization:
    """Test parameter sanitization."""

    def test_sanitize_sensitive_keys(self):
        """Test that sensitive keys are redacted."""
        client = TelemetryClient.__new__(TelemetryClient)
        client._initialized = True
        client.config = TelemetryConfig()

        params = {
            "name": "test",
            "file_path": "/secret/path.txt",
            "script": "print('hello')",
            "password": "secret123",
            "api_key": "key123",
        }

        sanitized = client._sanitize_params(params)

        assert sanitized["name"] == "test"
        assert sanitized["file_path"] == "[REDACTED]"
        assert sanitized["script"] == "[REDACTED]"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"

    def test_sanitize_paths(self):
        """Test that paths are detected and sanitized."""
        client = TelemetryClient.__new__(TelemetryClient)
        client._initialized = True
        client.config = TelemetryConfig()

        # Note: keys containing 'path' get [REDACTED], so use different key names
        params = {
            "output_dir": "C:\\Users\\test\\Documents",
            "location": "/home/user/files",
            "normal_string": "hello world",
        }

        sanitized = client._sanitize_params(params)

        assert sanitized["output_dir"] == "[PATH]"  # Contains backslash, detected as path
        assert sanitized["location"] == "[PATH]"  # Contains forward slash, detected as path
        assert sanitized["normal_string"] == "hello world"

    def test_sanitize_long_strings(self):
        """Test that long strings are truncated."""
        client = TelemetryClient.__new__(TelemetryClient)
        client._initialized = True
        client.config = TelemetryConfig()

        long_string = "x" * 300
        params = {"data": long_string}

        sanitized = client._sanitize_params(params)

        assert sanitized["data"] == f"[STRING len={len(long_string)}]"

    def test_sanitize_numeric_values(self):
        """Test that numeric values are preserved."""
        client = TelemetryClient.__new__(TelemetryClient)
        client._initialized = True
        client.config = TelemetryConfig()

        params = {
            "count": 42,
            "ratio": 3.14,
            "enabled": True,
        }

        sanitized = client._sanitize_params(params)

        # Values are converted to strings for consistency
        assert sanitized["count"] == "42"
        assert sanitized["ratio"] == "3.14"
        assert sanitized["enabled"] == "True"

    def test_sanitize_collections(self):
        """Test that collections show type and length."""
        client = TelemetryClient.__new__(TelemetryClient)
        client._initialized = True
        client.config = TelemetryConfig()

        params = {
            "items": [1, 2, 3],
            "config": {"a": 1, "b": 2},
        }

        sanitized = client._sanitize_params(params)

        assert sanitized["items"] == "[LIST len=3]"
        assert sanitized["config"] == "[DICT keys=2]"


class TestTrackedToolDecorator:
    """Test the @tracked_tool decorator."""

    @patch("src.telemetry.get_telemetry")
    def test_tracks_successful_call(self, mock_get_telemetry):
        """Test that successful calls are tracked."""
        mock_client = MagicMock()
        mock_get_telemetry.return_value = mock_client

        @tracked_tool
        def sample_tool(x: int, y: int):
            return {"success": True, "result": x + y}

        result = sample_tool(x=1, y=2)

        assert result["success"] is True
        assert result["result"] == 3
        mock_client.track_tool_call.assert_called_once()
        call_args = mock_client.track_tool_call.call_args
        assert call_args.kwargs["tool_name"] == "sample_tool"
        assert call_args.kwargs["success"] is True

    @patch("src.telemetry.get_telemetry")
    def test_tracks_failed_result(self, mock_get_telemetry):
        """Test that failed results are tracked."""
        mock_client = MagicMock()
        mock_get_telemetry.return_value = mock_client

        @tracked_tool
        def failing_tool():
            return {"success": False, "error": "Something went wrong", "error_type": "TestError"}

        result = failing_tool()

        assert result["success"] is False
        mock_client.track_tool_call.assert_called_once()
        call_args = mock_client.track_tool_call.call_args
        assert call_args.kwargs["success"] is False
        assert call_args.kwargs["error_type"] == "TestError"

    @patch("src.telemetry.get_telemetry")
    def test_tracks_exception(self, mock_get_telemetry):
        """Test that exceptions are tracked."""
        mock_client = MagicMock()
        mock_get_telemetry.return_value = mock_client

        @tracked_tool
        def crashing_tool():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            crashing_tool()

        mock_client.track_tool_call.assert_called_once()
        call_args = mock_client.track_tool_call.call_args
        assert call_args.kwargs["success"] is False
        assert call_args.kwargs["error_type"] == "ValueError"


class TestTelemetryStatus:
    """Test telemetry status functions."""

    def test_get_telemetry_status(self):
        """Test getting telemetry status."""
        # Reset singleton to get a fresh, properly initialized client
        TelemetryClient._instance = None

        status = get_telemetry_status()

        assert "enabled" in status
        assert "level" in status
        assert "posthog_available" in status
        assert "user_id_hash" in status
        assert "session_tool_calls" in status
        assert "session_errors" in status

    def test_set_telemetry_level_valid(self):
        """Test setting valid telemetry level."""
        result = set_telemetry_level("off")
        assert result is True

        result = set_telemetry_level("basic")
        assert result is True

        result = set_telemetry_level("detailed")
        assert result is True

    @patch("src.telemetry._telemetry", None)
    def test_set_telemetry_level_invalid(self):
        """Test setting invalid telemetry level."""
        result = set_telemetry_level("invalid")
        assert result is False

        result = set_telemetry_level("maximum")
        assert result is False
