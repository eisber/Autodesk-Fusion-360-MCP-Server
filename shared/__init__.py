"""Shared definitions for Fusion 360 MCP Server and Add-In.

This package contains the single source of truth for tool definitions,
parameter schemas, and types used by both Server and MCP components.
"""

from .tool_definitions import (
    TOOL_DEFINITIONS,
    ParamDef,
    ParamType,
    ToolDef,
    get_tool,
    get_tool_by_endpoint,
    get_tools_by_category,
    list_categories,
    list_endpoints,
    list_tool_names,
)

__all__ = [
    "TOOL_DEFINITIONS",
    "ParamDef",
    "ParamType",
    "ToolDef",
    "get_tool",
    "get_tool_by_endpoint",
    "get_tools_by_category",
    "list_categories",
    "list_endpoints",
    "list_tool_names",
]
