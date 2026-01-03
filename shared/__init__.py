"""Shared definitions for Fusion 360 MCP Server and Add-In.

This package contains the single source of truth for tool definitions,
parameter schemas, and types used by both Server and MCP components.
"""

from .tool_definitions import (
    ToolDef,
    ParamDef,
    ParamType,
    TOOL_DEFINITIONS,
    get_tool,
    get_tool_by_endpoint,
    get_tools_by_category,
    list_tool_names,
    list_categories,
    list_endpoints,
)

__all__ = [
    "ToolDef",
    "ParamDef",
    "ParamType",
    "TOOL_DEFINITIONS",
    "get_tool",
    "get_tool_by_endpoint",
    "get_tools_by_category",
    "list_tool_names",
    "list_categories",
    "list_endpoints",
]
