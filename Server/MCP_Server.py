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
  This is an open source project maintained by volunteers. Telemetry helps us:

    WHY we collect data:
    - Understand which tools are most useful (to prioritize development)
    - Find and fix bugs faster (error tracking)
    - Know if the server is actually being used (motivation to keep improving!)

    WHAT we collect:
    - Tool names and success/failure rates
    - Error types and sanitized messages
    - Session duration and tool call counts
    - Platform info (OS, Python version)

    WHAT we DON'T collect:
    - Your Fusion 360 models or designs
    - File paths or script contents  
    - Any personal or identifiable information

    HOW we use it:
    - Analytics via PostHog (privacy-focused, open source)
    - Data is anonymous and aggregated
    - Helps us write better documentation for common errors

  To opt out: set FUSION_MCP_TELEMETRY=off or use configure_telemetry("off")
  We respect your choice, but hope you'll help us improve! 
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
