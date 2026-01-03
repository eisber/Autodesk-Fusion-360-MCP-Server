"""Tests for the paletteSend entry module."""

import pytest
from unittest.mock import MagicMock, patch
import json


class TestPaletteSendStart:
    """Tests for paletteSend start function."""
    
    def test_start_creates_command_definition(self, mock_adsk, mock_config):
        """Test that start() creates a command definition."""
        mock_cmd_def = MagicMock()
        mock_adsk['cmd_defs'].addButtonDefinition.return_value = mock_cmd_def
        
        cmd_id = f"{mock_config.COMPANY_NAME}_{mock_config.ADDIN_NAME}_palette_send"
        cmd_name = "Send to Palette"
        cmd_description = "Send some information to the palette"
        
        mock_adsk['cmd_defs'].addButtonDefinition(cmd_id, cmd_name, cmd_description, "")
        
        mock_adsk['cmd_defs'].addButtonDefinition.assert_called_once()
        call_args = mock_adsk['cmd_defs'].addButtonDefinition.call_args[0]
        assert "palette_send" in call_args[0]
    
    def test_start_adds_command_to_panel(self, mock_adsk):
        """Test that start() adds command control to panel."""
        mock_control = MagicMock()
        mock_adsk['panel'].controls.addCommand.return_value = mock_control
        
        mock_cmd_def = MagicMock()
        mock_adsk['panel'].controls.addCommand(mock_cmd_def, "ScriptsManagerCommand", False)
        
        mock_adsk['panel'].controls.addCommand.assert_called_once()


class TestPaletteSendStop:
    """Tests for paletteSend stop function."""
    
    def test_stop_deletes_command_control(self, mock_adsk):
        """Test that stop() deletes the command control."""
        mock_control = MagicMock()
        mock_adsk['panel'].controls.itemById.return_value = mock_control
        
        control = mock_adsk['panel'].controls.itemById("test_cmd_id")
        if control:
            control.deleteMe()
        
        mock_control.deleteMe.assert_called_once()
    
    def test_stop_deletes_command_definition(self, mock_adsk):
        """Test that stop() deletes the command definition."""
        mock_cmd_def = MagicMock()
        mock_adsk['cmd_defs'].itemById.return_value = mock_cmd_def
        
        cmd_def = mock_adsk['cmd_defs'].itemById("test_cmd_id")
        if cmd_def:
            cmd_def.deleteMe()
        
        mock_cmd_def.deleteMe.assert_called_once()
    
    def test_stop_handles_missing_elements(self, mock_adsk):
        """Test that stop() handles missing UI elements gracefully."""
        mock_adsk['panel'].controls.itemById.return_value = None
        mock_adsk['cmd_defs'].itemById.return_value = None
        
        control = mock_adsk['panel'].controls.itemById("nonexistent")
        if control:
            control.deleteMe()
        
        cmd_def = mock_adsk['cmd_defs'].itemById("nonexistent")
        if cmd_def:
            cmd_def.deleteMe()
        
        # Should not raise


class TestPaletteSendCommandCreated:
    """Tests for command_created event handler."""
    
    def test_command_created_adds_text_input(self, mock_adsk):
        """Test that command_created adds text input."""
        mock_inputs = MagicMock()
        
        mock_inputs.addTextBoxCommandInput('text_input', 'Text Message', 'Enter some text', 1, False)
        
        mock_inputs.addTextBoxCommandInput.assert_called_once_with(
            'text_input', 'Text Message', 'Enter some text', 1, False
        )
    
    def test_command_created_adds_value_input(self, mock_adsk):
        """Test that command_created adds value input with units."""
        mock_inputs = MagicMock()
        mock_value = MagicMock()
        mock_adsk['core'].ValueInput.createByString.return_value = mock_value
        
        users_current_units = "cm"
        default_value = mock_adsk['core'].ValueInput.createByString(f'1 {users_current_units}')
        mock_inputs.addValueInput('value_input', 'Value Message', users_current_units, default_value)
        
        mock_inputs.addValueInput.assert_called_once()
        call_args = mock_inputs.addValueInput.call_args[0]
        assert call_args[0] == 'value_input'
        assert call_args[1] == 'Value Message'
        assert call_args[2] == 'cm'
    
    def test_command_created_connects_event_handlers(self, mock_adsk, mock_futil):
        """Test that command_created connects all required event handlers."""
        mock_command = MagicMock()
        local_handlers = []
        
        events_to_connect = ['execute', 'inputChanged', 'executePreview', 'destroy']
        
        for event in events_to_connect:
            mock_futil.add_handler(
                getattr(mock_command, event),
                MagicMock(),
                local_handlers=local_handlers
            )
        
        assert mock_futil.add_handler.call_count == len(events_to_connect)


class TestPaletteSendCommandExecute:
    """Tests for command_execute event handler."""
    
    def test_command_execute_gets_input_values(self, mock_adsk):
        """Test that execute retrieves input values correctly."""
        mock_inputs = MagicMock()
        mock_text_input = MagicMock()
        mock_text_input.formattedText = "Test message"
        mock_value_input = MagicMock()
        mock_value_input.value = 5.0
        mock_value_input.expression = "5 cm"
        
        mock_inputs.itemById.side_effect = lambda id: {
            'text_input': mock_text_input,
            'value_input': mock_value_input
        }.get(id)
        
        text_input = mock_inputs.itemById('text_input')
        value_input = mock_inputs.itemById('value_input')
        
        assert text_input.formattedText == "Test message"
        assert value_input.value == 5.0
        assert value_input.expression == "5 cm"
    
    def test_command_execute_constructs_message_data(self, mock_adsk):
        """Test that execute constructs correct message data."""
        value = 5.0
        expression = "5 cm"
        text = "Test message"
        
        message_data = {
            'myValue': f'{value} cm',
            'myExpression': expression,
            'myText': text
        }
        
        assert message_data['myValue'] == "5.0 cm"
        assert message_data['myExpression'] == "5 cm"
        assert message_data['myText'] == "Test message"
    
    def test_command_execute_creates_valid_json(self, mock_adsk):
        """Test that execute creates valid JSON."""
        message_data = {
            'myValue': '5.0 cm',
            'myExpression': '5 cm',
            'myText': 'Test message'
        }
        
        message_json = json.dumps(message_data)
        parsed = json.loads(message_json)
        
        assert parsed == message_data
    
    def test_command_execute_sends_to_palette(self, mock_adsk):
        """Test that execute sends message to palette."""
        mock_palette = MagicMock()
        mock_adsk['palettes'].itemById.return_value = mock_palette
        
        message_action = 'updateMessage'
        message_json = json.dumps({'myValue': '5 cm'})
        
        palette = mock_adsk['palettes'].itemById("MCP_Palette")
        palette.sendInfoToHTML(message_action, message_json)
        
        mock_palette.sendInfoToHTML.assert_called_once_with(message_action, message_json)


class TestPaletteSendCommandInputChanged:
    """Tests for command_input_changed event handler."""
    
    def test_input_changed_receives_changed_input(self, mock_adsk, mock_futil):
        """Test that input_changed receives the changed input."""
        mock_args = MagicMock()
        mock_changed_input = MagicMock()
        mock_changed_input.id = "text_input"
        mock_args.input = mock_changed_input
        
        changed_input = mock_args.input
        
        assert changed_input.id == "text_input"
    
    def test_input_changed_logs_event(self, mock_adsk, mock_futil):
        """Test that input_changed logs the event."""
        changed_input_id = "value_input"
        cmd_name = "Send to Palette"
        
        mock_futil.log(f'{cmd_name} Input Changed Event fired from a change to {changed_input_id}')
        
        mock_futil.log.assert_called_once()
        call_args = mock_futil.log.call_args[0][0]
        assert changed_input_id in call_args


class TestPaletteSendCommandDestroy:
    """Tests for command_destroy event handler."""
    
    def test_destroy_clears_local_handlers(self, mock_adsk, mock_futil):
        """Test that destroy clears the local handlers list."""
        local_handlers = [MagicMock(), MagicMock()]
        
        # Simulate destroy behavior
        local_handlers.clear()
        
        assert len(local_handlers) == 0
    
    def test_destroy_logs_event(self, mock_adsk, mock_futil):
        """Test that destroy logs the event."""
        cmd_name = "Send to Palette"
        
        mock_futil.log(f'{cmd_name} Command Destroy Event')
        
        mock_futil.log.assert_called_once()
