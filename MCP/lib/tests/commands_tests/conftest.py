"""Shared pytest fixtures for MCP commands tests.

These fixtures mock the Fusion 360 API objects since we cannot run
actual Fusion 360 in a test environment.

Note: These tests test the command logic in isolation, mocking the Fusion 360 API.
The actual commands module cannot be imported outside of Fusion 360 due to
relative import structure - these tests validate the behavioral patterns.
"""

import sys
from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture
def mock_adsk():
    """Create and install mock adsk module."""
    mock_adsk_module = MagicMock()
    
    # Mock adsk.core
    mock_core = MagicMock()
    mock_adsk_module.core = mock_core
    
    # Mock Application
    mock_app = MagicMock()
    mock_ui = MagicMock()
    mock_app.userInterface = mock_ui
    mock_core.Application.get.return_value = mock_app
    
    # Mock CommandDefinitions
    mock_cmd_defs = MagicMock()
    mock_ui.commandDefinitions = mock_cmd_defs
    
    # Mock Workspaces
    mock_workspace = MagicMock()
    mock_panel = MagicMock()
    mock_workspace.toolbarPanels.itemById.return_value = mock_panel
    mock_ui.workspaces.itemById.return_value = mock_workspace
    
    # Mock Palettes
    mock_palettes = MagicMock()
    mock_ui.palettes = mock_palettes
    
    # Mock CommandCreatedEventArgs
    mock_cmd_created_args = MagicMock()
    mock_command = MagicMock()
    mock_cmd_created_args.command = mock_command
    mock_core.CommandCreatedEventArgs = mock_cmd_created_args
    
    # Mock CommandEventArgs
    mock_cmd_event_args = MagicMock()
    mock_core.CommandEventArgs = mock_cmd_event_args
    
    # Mock PaletteDockingStates
    mock_core.PaletteDockingStates.PaletteDockStateRight = 1
    mock_core.PaletteDockingStates.PaletteDockStateFloating = 0
    
    # Mock LogLevels
    mock_core.LogLevels.InfoLogLevel = 2
    
    # Mock ValueInput
    mock_core.ValueInput.createByString.side_effect = lambda s: MagicMock(expression=s)
    
    # Install mock
    sys.modules['adsk'] = mock_adsk_module
    sys.modules['adsk.core'] = mock_core
    sys.modules['adsk.fusion'] = MagicMock()
    
    yield {
        'adsk': mock_adsk_module,
        'core': mock_core,
        'app': mock_app,
        'ui': mock_ui,
        'cmd_defs': mock_cmd_defs,
        'workspace': mock_workspace,
        'panel': mock_panel,
        'palettes': mock_palettes,
    }
    
    # Cleanup
    if 'adsk' in sys.modules:
        del sys.modules['adsk']
    if 'adsk.core' in sys.modules:
        del sys.modules['adsk.core']
    if 'adsk.fusion' in sys.modules:
        del sys.modules['adsk.fusion']


@pytest.fixture
def mock_futil():
    """Mock the fusionAddInUtils module."""
    mock = MagicMock()
    mock.add_handler = MagicMock()
    mock.log = MagicMock()
    return mock


@pytest.fixture
def mock_config():
    """Mock the config module."""
    mock = MagicMock()
    mock.COMPANY_NAME = "Autodesk"
    mock.ADDIN_NAME = "MCP"
    mock.sample_palette_id = "MCP_Palette"
    return mock
