"""Telemetry management tools for Fusion 360 MCP Server.

Allows users to control telemetry settings via MCP interface.
"""

from typing import Literal

from ..telemetry import (
    get_telemetry_status,
    set_telemetry_level,
    TelemetryLevel,
    get_telemetry,
)


def get_telemetry_info():
    """
    Get current telemetry status and configuration.
    
    Returns information about:
    - Whether telemetry is enabled
    - Current telemetry level (off, basic, detailed)
    - Session statistics (tool calls, errors)
    
    Telemetry helps improve the MCP Server by understanding:
    - Which tools are most useful
    - Which tools have issues
    - How the server is being used
    
    All data is anonymous and no personal information is collected.
    """
    return get_telemetry_status()


def configure_telemetry(level: Literal["off", "basic", "detailed"]):
    """
    Configure the telemetry level.
    
    Args:
        level: Telemetry level to set:
            - "off": No telemetry collected
            - "basic": Tool names, success/failure (no parameters)  
            - "detailed": Includes sanitized parameters (no file paths or scripts)
    
    Returns:
        Success status and new telemetry configuration
        
    Note: Your preference is saved and persists across sessions.
    All telemetry is anonymous - we never collect personal information.
    """
    success = set_telemetry_level(level)
    if success:
        return {
            "success": True,
            "message": f"Telemetry level set to '{level}'",
            "status": get_telemetry_status()
        }
    else:
        return {
            "success": False,
            "error": f"Invalid telemetry level: {level}. Use 'off', 'basic', or 'detailed'."
        }
