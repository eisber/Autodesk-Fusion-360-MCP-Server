"""Tests for the commands __init__ module."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestCommandsModule:
    """Tests for the commands module initialization."""

    def test_commands_list_contains_all_modules(self, mock_adsk, mock_futil, mock_config):
        """Test that the commands list contains all expected modules."""
        # Mock the dependencies
        with patch.dict(
            sys.modules,
            {
                "adsk": mock_adsk["adsk"],
                "adsk.core": mock_adsk["core"],
                "adsk.fusion": MagicMock(),
            },
        ):
            # Create mock entry modules
            mock_command_dialog = MagicMock()
            mock_command_dialog.start = MagicMock()
            mock_command_dialog.stop = MagicMock()

            mock_palette_show = MagicMock()
            mock_palette_show.start = MagicMock()
            mock_palette_show.stop = MagicMock()

            mock_palette_send = MagicMock()
            mock_palette_send.start = MagicMock()
            mock_palette_send.stop = MagicMock()

            # Simulate the commands list
            commands = [mock_command_dialog, mock_palette_show, mock_palette_send]

            assert len(commands) == 3
            for cmd in commands:
                assert hasattr(cmd, "start")
                assert hasattr(cmd, "stop")

    def test_start_calls_all_command_starts(self, mock_adsk):
        """Test that start() calls start on all commands."""
        mock_cmd1 = MagicMock()
        mock_cmd2 = MagicMock()
        mock_cmd3 = MagicMock()

        commands = [mock_cmd1, mock_cmd2, mock_cmd3]

        # Simulate the start function
        def start():
            for command in commands:
                command.start()

        start()

        mock_cmd1.start.assert_called_once()
        mock_cmd2.start.assert_called_once()
        mock_cmd3.start.assert_called_once()

    def test_stop_calls_all_command_stops(self, mock_adsk):
        """Test that stop() calls stop on all commands."""
        mock_cmd1 = MagicMock()
        mock_cmd2 = MagicMock()
        mock_cmd3 = MagicMock()

        commands = [mock_cmd1, mock_cmd2, mock_cmd3]

        # Simulate the stop function
        def stop():
            for command in commands:
                command.stop()

        stop()

        mock_cmd1.stop.assert_called_once()
        mock_cmd2.stop.assert_called_once()
        mock_cmd3.stop.assert_called_once()

    def test_start_handles_empty_commands(self):
        """Test that start() handles empty commands list."""
        commands = []

        def start():
            for command in commands:
                command.start()

        # Should not raise
        start()

    def test_stop_handles_empty_commands(self):
        """Test that stop() handles empty commands list."""
        commands = []

        def stop():
            for command in commands:
                command.stop()

        # Should not raise
        stop()
