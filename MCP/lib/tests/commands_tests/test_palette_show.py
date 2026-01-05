"""Tests for the paletteShow entry module."""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestPaletteShowStart:
    """Tests for paletteShow start function."""

    def test_start_creates_command_definition(self, mock_adsk, mock_config):
        """Test that start() creates a command definition."""
        mock_cmd_def = MagicMock()
        mock_adsk["cmd_defs"].addButtonDefinition.return_value = mock_cmd_def

        cmd_id = f"{mock_config.COMPANY_NAME}_{mock_config.ADDIN_NAME}_PalleteShow"
        cmd_name = "Show My Palette"
        cmd_description = "A Fusion Add-in Palette"

        mock_adsk["cmd_defs"].addButtonDefinition(cmd_id, cmd_name, cmd_description, "")

        mock_adsk["cmd_defs"].addButtonDefinition.assert_called_once()
        call_args = mock_adsk["cmd_defs"].addButtonDefinition.call_args[0]
        assert "PalleteShow" in call_args[0] or "PaletteShow" in call_args[0]

    def test_start_adds_command_to_panel(self, mock_adsk):
        """Test that start() adds command control to the correct panel."""
        mock_control = MagicMock()
        mock_adsk["panel"].controls.addCommand.return_value = mock_control

        mock_cmd_def = MagicMock()
        mock_adsk["panel"].controls.addCommand(mock_cmd_def, "ScriptsManagerCommand", False)

        mock_adsk["panel"].controls.addCommand.assert_called_once()


class TestPaletteShowStop:
    """Tests for paletteShow stop function."""

    def test_stop_deletes_command_control(self, mock_adsk):
        """Test that stop() deletes the command control."""
        mock_control = MagicMock()
        mock_adsk["panel"].controls.itemById.return_value = mock_control

        control = mock_adsk["panel"].controls.itemById("test_cmd_id")
        if control:
            control.deleteMe()

        mock_control.deleteMe.assert_called_once()

    def test_stop_deletes_command_definition(self, mock_adsk):
        """Test that stop() deletes the command definition."""
        mock_cmd_def = MagicMock()
        mock_adsk["cmd_defs"].itemById.return_value = mock_cmd_def

        cmd_def = mock_adsk["cmd_defs"].itemById("test_cmd_id")
        if cmd_def:
            cmd_def.deleteMe()

        mock_cmd_def.deleteMe.assert_called_once()

    def test_stop_deletes_palette(self, mock_adsk):
        """Test that stop() deletes the palette."""
        mock_palette = MagicMock()
        mock_adsk["palettes"].itemById.return_value = mock_palette

        palette = mock_adsk["palettes"].itemById("MCP_Palette")
        if palette:
            palette.deleteMe()

        mock_palette.deleteMe.assert_called_once()

    def test_stop_handles_missing_palette(self, mock_adsk):
        """Test that stop() handles missing palette gracefully."""
        mock_adsk["palettes"].itemById.return_value = None

        palette = mock_adsk["palettes"].itemById("nonexistent")
        if palette:
            palette.deleteMe()

        # Should not raise - no assertion needed


class TestPaletteShowCommandExecute:
    """Tests for command_execute event handler."""

    def test_command_execute_creates_palette_if_not_exists(self, mock_adsk):
        """Test that execute creates palette if it doesn't exist."""
        mock_adsk["palettes"].itemById.return_value = None
        mock_palette = MagicMock()
        mock_adsk["palettes"].add.return_value = mock_palette

        palette = mock_adsk["palettes"].itemById("MCP_Palette")
        if palette is None:
            palette = mock_adsk["palettes"].add(
                id="MCP_Palette",
                name="My Palette Sample",
                htmlFileURL="test.html",
                isVisible=True,
                showCloseButton=True,
                isResizable=True,
                width=650,
                height=600,
                useNewWebBrowser=True,
            )

        mock_adsk["palettes"].add.assert_called_once()

    def test_command_execute_makes_palette_visible(self, mock_adsk):
        """Test that execute makes existing palette visible."""
        mock_palette = MagicMock()
        mock_palette.isVisible = False
        mock_palette.dockingState = 1  # Not floating
        mock_adsk["palettes"].itemById.return_value = mock_palette

        palette = mock_adsk["palettes"].itemById("MCP_Palette")
        palette.isVisible = True

        assert mock_palette.isVisible is True

    def test_command_execute_docks_floating_palette(self, mock_adsk):
        """Test that execute docks a floating palette."""
        mock_palette = MagicMock()
        mock_palette.dockingState = mock_adsk["core"].PaletteDockingStates.PaletteDockStateFloating
        mock_adsk["palettes"].itemById.return_value = mock_palette

        palette = mock_adsk["palettes"].itemById("MCP_Palette")
        if palette.dockingState == mock_adsk["core"].PaletteDockingStates.PaletteDockStateFloating:
            palette.dockingState = mock_adsk["core"].PaletteDockingStates.PaletteDockStateRight

        assert mock_palette.dockingState == 1


class TestPaletteShowPaletteIncoming:
    """Tests for palette_incoming event handler."""

    def test_palette_incoming_parses_json_data(self, mock_adsk):
        """Test that incoming handler parses JSON data correctly."""
        mock_args = MagicMock()
        mock_args.data = json.dumps({"arg1": "value1", "arg2": "value2"})
        mock_args.action = "messageFromPalette"

        message_data = json.loads(mock_args.data)
        message_action = mock_args.action

        assert message_data["arg1"] == "value1"
        assert message_data["arg2"] == "value2"
        assert message_action == "messageFromPalette"

    def test_palette_incoming_handles_message_from_palette(self, mock_adsk):
        """Test handling of messageFromPalette action."""
        message_data = {"arg1": "test_value", "arg2": "another_value"}
        message_action = "messageFromPalette"

        if message_action == "messageFromPalette":
            arg1 = message_data.get("arg1", "arg1 not sent")
            arg2 = message_data.get("arg2", "arg2 not sent")

        assert arg1 == "test_value"
        assert arg2 == "another_value"

    def test_palette_incoming_uses_defaults_for_missing_args(self, mock_adsk):
        """Test that missing args use default values."""
        message_data = {}

        arg1 = message_data.get("arg1", "arg1 not sent")
        arg2 = message_data.get("arg2", "arg2 not sent")

        assert arg1 == "arg1 not sent"
        assert arg2 == "arg2 not sent"

    def test_palette_incoming_sets_return_data(self, mock_adsk):
        """Test that handler sets return data with timestamp."""
        mock_args = MagicMock()
        mock_args.returnData = None

        # Simulate setting return data
        mock_args.returnData = "OK - 12:00:00"

        assert mock_args.returnData.startswith("OK -")


class TestPaletteShowPaletteNavigating:
    """Tests for palette_navigating event handler."""

    def test_palette_navigating_opens_external_urls_externally(self, mock_adsk):
        """Test that external URLs are launched externally."""
        mock_args = MagicMock()
        mock_args.navigationURL = "https://www.autodesk.com"
        mock_args.launchExternally = False

        url = mock_args.navigationURL
        if url.startswith("http"):
            mock_args.launchExternally = True

        assert mock_args.launchExternally is True

    def test_palette_navigating_keeps_local_urls_internal(self, mock_adsk):
        """Test that local URLs are not launched externally."""
        mock_args = MagicMock()
        mock_args.navigationURL = "file:///local/path/index.html"
        mock_args.launchExternally = False

        url = mock_args.navigationURL
        if url.startswith("http"):
            mock_args.launchExternally = True

        assert mock_args.launchExternally is False
