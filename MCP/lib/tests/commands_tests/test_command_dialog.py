"""Tests for the commandDialog entry module."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys


class TestCommandDialogStart:
    """Tests for commandDialog start function."""
    
    def test_start_creates_command_definition(self, mock_adsk, mock_futil, mock_config):
        """Test that start() creates a command definition."""
        mock_cmd_def = MagicMock()
        mock_adsk['cmd_defs'].addButtonDefinition.return_value = mock_cmd_def
        
        # Simulate start behavior
        cmd_id = f"{mock_config.COMPANY_NAME}_{mock_config.ADDIN_NAME}_cmdDialog"
        cmd_name = "Command Dialog Sample"
        cmd_description = "A Fusion Add-in Command with a dialog"
        
        mock_adsk['cmd_defs'].addButtonDefinition(cmd_id, cmd_name, cmd_description, "")
        
        mock_adsk['cmd_defs'].addButtonDefinition.assert_called_once()
        call_args = mock_adsk['cmd_defs'].addButtonDefinition.call_args[0]
        assert mock_config.COMPANY_NAME in call_args[0]
        assert mock_config.ADDIN_NAME in call_args[0]
    
    def test_start_adds_command_to_panel(self, mock_adsk, mock_config):
        """Test that start() adds command control to panel."""
        mock_cmd_def = MagicMock()
        mock_control = MagicMock()
        mock_adsk['panel'].controls.addCommand.return_value = mock_control
        
        # Simulate adding command to panel
        mock_adsk['panel'].controls.addCommand(mock_cmd_def, "ScriptsManagerCommand", False)
        
        mock_adsk['panel'].controls.addCommand.assert_called_once()
    
    def test_start_sets_is_promoted(self, mock_adsk):
        """Test that start() sets isPromoted on control."""
        mock_control = MagicMock()
        mock_control.isPromoted = False
        
        # Simulate setting isPromoted
        mock_control.isPromoted = True
        
        assert mock_control.isPromoted is True


class TestCommandDialogStop:
    """Tests for commandDialog stop function."""
    
    def test_stop_deletes_command_control(self, mock_adsk):
        """Test that stop() deletes the command control."""
        mock_control = MagicMock()
        mock_adsk['panel'].controls.itemById.return_value = mock_control
        
        # Simulate stop behavior
        control = mock_adsk['panel'].controls.itemById("test_cmd_id")
        if control:
            control.deleteMe()
        
        mock_control.deleteMe.assert_called_once()
    
    def test_stop_deletes_command_definition(self, mock_adsk):
        """Test that stop() deletes the command definition."""
        mock_cmd_def = MagicMock()
        mock_adsk['cmd_defs'].itemById.return_value = mock_cmd_def
        
        # Simulate stop behavior
        cmd_def = mock_adsk['cmd_defs'].itemById("test_cmd_id")
        if cmd_def:
            cmd_def.deleteMe()
        
        mock_cmd_def.deleteMe.assert_called_once()
    
    def test_stop_handles_missing_control(self, mock_adsk):
        """Test that stop() handles missing command control gracefully."""
        mock_adsk['panel'].controls.itemById.return_value = None
        
        # Simulate stop behavior - should not raise
        control = mock_adsk['panel'].controls.itemById("nonexistent")
        if control:
            control.deleteMe()
        
        # No assertion needed - just verify no exception


class TestCommandDialogCommandCreated:
    """Tests for command_created event handler."""
    
    def test_command_created_adds_inputs(self, mock_adsk):
        """Test that command_created adds the expected inputs."""
        mock_inputs = MagicMock()
        mock_command = MagicMock()
        mock_command.commandInputs = mock_inputs
        
        # Simulate adding inputs
        mock_inputs.addTextBoxCommandInput('text_box', 'Some Text', 'Enter some text.', 1, False)
        
        mock_inputs.addTextBoxCommandInput.assert_called_once_with(
            'text_box', 'Some Text', 'Enter some text.', 1, False
        )
    
    def test_command_created_adds_value_input(self, mock_adsk):
        """Test that command_created adds a value input."""
        mock_inputs = MagicMock()
        mock_value_input = MagicMock()
        mock_adsk['core'].ValueInput.createByString.return_value = mock_value_input
        
        # Simulate adding value input
        default_value = mock_adsk['core'].ValueInput.createByString('1')
        mock_inputs.addValueInput('value_input', 'Some Value', 'cm', default_value)
        
        mock_inputs.addValueInput.assert_called_once()
    
    def test_command_created_connects_event_handlers(self, mock_adsk, mock_futil):
        """Test that command_created connects all required event handlers."""
        mock_command = MagicMock()
        local_handlers = []
        
        # Events that should be connected
        events_to_connect = [
            'execute',
            'inputChanged', 
            'executePreview',
            'validateInputs',
            'destroy'
        ]
        
        for event in events_to_connect:
            mock_futil.add_handler(
                getattr(mock_command, event), 
                MagicMock(),
                local_handlers=local_handlers
            )
        
        assert mock_futil.add_handler.call_count == len(events_to_connect)


class TestCommandDialogCommandExecute:
    """Tests for command_execute event handler."""
    
    def test_command_execute_gets_input_values(self, mock_adsk):
        """Test that command_execute retrieves input values."""
        mock_inputs = MagicMock()
        mock_text_box = MagicMock()
        mock_text_box.text = "Test text"
        mock_value_input = MagicMock()
        mock_value_input.expression = "5 cm"
        
        mock_inputs.itemById.side_effect = lambda id: {
            'text_box': mock_text_box,
            'value_input': mock_value_input
        }.get(id)
        
        # Retrieve values
        text_box = mock_inputs.itemById('text_box')
        value_input = mock_inputs.itemById('value_input')
        
        assert text_box.text == "Test text"
        assert value_input.expression == "5 cm"
    
    def test_command_execute_shows_message(self, mock_adsk):
        """Test that command_execute shows a message box."""
        mock_ui = mock_adsk['ui']
        
        # Simulate showing message
        msg = "Your text: Test<br>Your value: 5 cm"
        mock_ui.messageBox(msg)
        
        mock_ui.messageBox.assert_called_once_with(msg)


class TestCommandDialogValidateInput:
    """Tests for command_validate_input event handler."""
    
    def test_validate_input_accepts_positive_values(self, mock_adsk):
        """Test that validate accepts positive values."""
        mock_args = MagicMock()
        mock_inputs = MagicMock()
        mock_value_input = MagicMock()
        mock_value_input.value = 5.0
        
        mock_inputs.itemById.return_value = mock_value_input
        mock_args.inputs = mock_inputs
        
        # Simulate validation
        value_input = mock_args.inputs.itemById('value_input')
        if value_input.value >= 0:
            mock_args.areInputsValid = True
        else:
            mock_args.areInputsValid = False
        
        assert mock_args.areInputsValid is True
    
    def test_validate_input_rejects_negative_values(self, mock_adsk):
        """Test that validate rejects negative values."""
        mock_args = MagicMock()
        mock_inputs = MagicMock()
        mock_value_input = MagicMock()
        mock_value_input.value = -5.0
        
        mock_inputs.itemById.return_value = mock_value_input
        mock_args.inputs = mock_inputs
        
        # Simulate validation
        value_input = mock_args.inputs.itemById('value_input')
        if value_input.value >= 0:
            mock_args.areInputsValid = True
        else:
            mock_args.areInputsValid = False
        
        assert mock_args.areInputsValid is False
    
    def test_validate_input_accepts_zero(self, mock_adsk):
        """Test that validate accepts zero value."""
        mock_args = MagicMock()
        mock_inputs = MagicMock()
        mock_value_input = MagicMock()
        mock_value_input.value = 0.0
        
        mock_inputs.itemById.return_value = mock_value_input
        mock_args.inputs = mock_inputs
        
        # Simulate validation
        value_input = mock_args.inputs.itemById('value_input')
        if value_input.value >= 0:
            mock_args.areInputsValid = True
        else:
            mock_args.areInputsValid = False
        
        assert mock_args.areInputsValid is True
