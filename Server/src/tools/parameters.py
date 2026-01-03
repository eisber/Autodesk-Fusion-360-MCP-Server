"""Parameter tools for Fusion 360 MCP Server.

Contains functions for managing model parameters.
Uses @fusion_tool decorator for automatic HTTP handling and telemetry.
"""

from .base import fusion_tool


@fusion_tool(method="GET")
def list_parameters():
    """List all parameters in the current model."""


@fusion_tool
def set_parameter(name: str, value: str):
    """
    Change the value of a parameter.
    
    Args:
        name: Parameter name
        value: New value expression
    """
