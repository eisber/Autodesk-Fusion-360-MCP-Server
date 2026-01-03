"""Fusion 360 MCP Server - Entry Point.

This is a thin wrapper that registers tools and prompts from the src/ library.
All implementation logic lives in src/tools/ modules.
"""

import argparse
import atexit
from mcp.server.fastmcp import FastMCP

from src.instructions import SYSTEM_INSTRUCTIONS
from src.prompts import PROMPTS
from src import tools
from src.telemetry import get_telemetry


# =============================================================================
# Initialize MCP Server
# =============================================================================

mcp = FastMCP("Fusion", instructions=SYSTEM_INSTRUCTIONS)


# =============================================================================
# Auto-Register All Tools from __all__
# =============================================================================

# Register all tools from __all__
for tool_name in tools.__all__:
    tool_func = getattr(tools, tool_name, None)
    if tool_func is not None and callable(tool_func):
        mcp.tool()(tool_func)


# =============================================================================
# Register Prompts
# =============================================================================

for name, content in PROMPTS.items():
    @mcp.prompt(name=name)
    def _prompt(content=content):
        return content


# =============================================================================
# Entry Point
# =============================================================================

TELEMETRY_WARNING = """
================================================================================
                          TELEMETRY NOTICE
================================================================================
  This MCP Server collects anonymous usage data to improve the tool.

  What we collect:
    - Tool names and success/failure rates
    - Error types (for debugging)
    - Sanitized parameters (no file paths, scripts, or personal data)

  What we DON'T collect:
    - File paths or model data
    - Script contents
    - Personal information

  To disable: set environment variable FUSION_MCP_TELEMETRY=off
  Or use the configure_telemetry("off") tool
================================================================================
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fusion 360 MCP Server")
    parser.add_argument(
        "--server_type", 
        type=str, 
        default="sse", 
        choices=["sse", "stdio"],
        help="Transport type for MCP server"
    )
    args = parser.parse_args()
    
    # Initialize telemetry and track session
    telemetry = get_telemetry()
    
    # Show telemetry warning if enabled (only for non-stdio to avoid protocol issues)
    if telemetry.enabled and args.server_type != "stdio":
        print(TELEMETRY_WARNING, flush=True)
    
    telemetry.track_session_start()
    atexit.register(telemetry.track_session_end)
    atexit.register(telemetry.flush)
    
    mcp.run(transport=args.server_type)
