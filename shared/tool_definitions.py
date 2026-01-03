"""Shared tool definitions for Fusion 360 MCP Server and Add-In.

This module defines all tools in a single place. Both the Server-side
@fusion_tool stubs and MCP-side @task handlers should match these definitions.

Only ESSENTIAL and CONVENIENCE tools are defined here.
SCRIPTABLE operations (geometry creation, features, patterns) should use
execute_fusion_script instead. See shared/tool_categorization.py for analysis.

Usage:
    from shared import ToolDef, ParamDef, TOOL_DEFINITIONS, get_tool
    
    # Get a specific tool definition
    tool = get_tool("measure_distance")
    
    # List tools by category
    measurement_tools = get_tools_by_category("measurement")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union


class ParamType(Enum):
    """Supported parameter types."""
    FLOAT = "float"
    INT = "int"
    STR = "str"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"


@dataclass
class ParamDef:
    """Definition of a tool parameter.
    
    Attributes:
        name: Parameter name (must match in both Server and MCP)
        param_type: Python type for the parameter
        description: Human-readable description for documentation
        default: Default value (None means required)
        required: Whether the parameter is required (auto-computed if default is None)
    """
    name: str
    param_type: ParamType
    description: str
    default: Any = None
    required: bool = True
    
    def __post_init__(self) -> None:
        """Auto-compute required based on default."""
        if self.default is not None:
            self.required = False
    
    @property
    def python_type(self) -> type:
        """Get the Python type for this parameter."""
        type_map = {
            ParamType.FLOAT: float,
            ParamType.INT: int,
            ParamType.STR: str,
            ParamType.BOOL: bool,
            ParamType.LIST: list,
            ParamType.DICT: dict,
        }
        return type_map[self.param_type]
    
    @property
    def type_hint(self) -> str:
        """Get the type hint string for code generation."""
        type_map = {
            ParamType.FLOAT: "float",
            ParamType.INT: "int",
            ParamType.STR: "str",
            ParamType.BOOL: "bool",
            ParamType.LIST: "list",
            ParamType.DICT: "dict",
        }
        return type_map[self.param_type]


@dataclass
class ToolDef:
    """Definition of a tool/task.
    
    Attributes:
        name: Internal function name (used in registry and code)
        endpoint: HTTP endpoint name (defaults to name)
        category: Category for grouping tools
        description: Docstring for the tool
        params: List of parameter definitions
        returns: Description of return value
        http_method: HTTP method ("POST" or "GET")
        use_sse: Whether to use SSE for streaming (POST only)
        needs_ui: Whether MCP handler needs UI parameter
        streaming: Whether this tool streams responses (e.g., execute_fusion_script)
        is_special: Whether this tool has custom handling (not auto-generated)
    """
    name: str
    category: str
    description: str
    params: List[ParamDef] = field(default_factory=list)
    returns: str = ""
    endpoint: Optional[str] = None
    http_method: Literal["POST", "GET"] = "POST"
    use_sse: bool = True
    needs_ui: bool = True
    streaming: bool = False
    is_special: bool = False
    
    def __post_init__(self) -> None:
        """Set endpoint to name if not specified."""
        if self.endpoint is None:
            self.endpoint = self.name
    
    def get_signature_params(self) -> str:
        """Generate parameter signature for function definition."""
        parts = []
        # Required params first
        for p in self.params:
            if p.required:
                parts.append(f"{p.name}: {p.type_hint}")
        # Optional params with defaults
        for p in self.params:
            if not p.required:
                default_repr = repr(p.default)
                parts.append(f"{p.name}: {p.type_hint} = {default_repr}")
        return ", ".join(parts)
    
    def get_param_names(self) -> List[str]:
        """Get list of parameter names in order."""
        return [p.name for p in self.params]
    
    def get_docstring(self) -> str:
        """Generate formatted docstring."""
        lines = [self.description, ""]
        
        if self.params:
            lines.append("Args:")
            for p in self.params:
                default_note = "" if p.required else f" (default: {p.default})"
                lines.append(f"    {p.name}: {p.description}{default_note}")
            lines.append("")
        
        if self.returns:
            lines.append("Returns:")
            lines.append(f"    {self.returns}")
        
        return "\n".join(lines)


# =============================================================================
# Tool Definitions - Single Source of Truth
# =============================================================================
# Only ESSENTIAL and CONVENIENCE tools are defined here.
# SCRIPTABLE operations should use execute_fusion_script instead.
# See shared/tool_categorization.py for the full analysis.

TOOL_DEFINITIONS: List[ToolDef] = [
    # =========================================================================
    # INFRASTRUCTURE - Essential tools that must exist
    # =========================================================================
    ToolDef(
        name="execute_fusion_script",
        endpoint="execute_script",
        category="infrastructure",
        description="Execute a Python script directly in Fusion 360. This is the primary tool for geometry creation, features, and complex operations.",
        params=[
            ParamDef("script", ParamType.STR, "Python script to execute in Fusion 360"),
            ParamDef("timeout", ParamType.FLOAT, "Timeout in seconds", default=300.0),
        ],
        returns="Dictionary with success, return_value, stdout, stderr, model_state",
        streaming=True,
        is_special=True,
    ),
    
    ToolDef(
        name="test_connection",
        endpoint="test_connection",
        category="infrastructure",
        description="Test the connection to the Fusion 360 Add-In.",
        params=[],
        returns="Dictionary with success and message",
        needs_ui=False,
    ),
    
    ToolDef(
        name="get_model_state",
        endpoint="model_state",
        category="infrastructure",
        description="Get the current state of the model including body count, sketch count, etc.",
        params=[],
        returns="Dictionary with body_count, sketch_count, component_count, bodies, sketches",
        http_method="GET",
        needs_ui=False,
    ),
    
    ToolDef(
        name="undo",
        endpoint="undo",
        category="infrastructure",
        description="Undo the last action in Fusion 360.",
        params=[],
        returns="Success message",
        needs_ui=False,
    ),
    
    ToolDef(
        name="delete_all",
        endpoint="delete_everything",
        category="infrastructure",
        description="Delete all bodies in the design. Use with caution.",
        params=[],
        returns="Success message",
    ),
    
    ToolDef(
        name="cancel_fusion_task",
        endpoint="cancel_task",
        category="infrastructure",
        description="Cancel a running task in Fusion 360.",
        params=[
            ParamDef("task_id", ParamType.STR, "The ID of the task to cancel"),
        ],
        returns="Dictionary with success status",
        http_method="POST",
        is_special=True,
    ),
    
    ToolDef(
        name="inspect_adsk_api",
        endpoint="inspect_api",
        category="infrastructure",
        description="Inspect the Autodesk Fusion 360 API to discover classes, methods, and properties.",
        params=[
            ParamDef("path", ParamType.STR, "Dot-separated path to inspect (e.g., 'adsk.fusion.Sketch')", default="adsk.fusion"),
        ],
        returns="Dictionary with type, docstring, signature, members, example",
        http_method="POST",
        needs_ui=False,
    ),
    
    # =========================================================================
    # INSPECTION - Query tools for model information
    # =========================================================================
    ToolDef(
        name="get_faces_info",
        endpoint="faces_info",
        category="inspection",
        description="Get detailed face information for a body including area, type, and geometry.",
        params=[
            ParamDef("body_index", ParamType.INT, "Index of the body to inspect", default=0),
        ],
        returns="Dictionary with face_count and list of face details",
        http_method="GET",
        needs_ui=False,
    ),
    
    ToolDef(
        name="get_edges_info",
        endpoint="edges_info",
        category="inspection",
        description="Get detailed edge information for a body including length, type, and endpoints.",
        params=[
            ParamDef("body_index", ParamType.INT, "Index of the body to inspect", default=0),
        ],
        returns="Dictionary with edge_count and list of edge details",
        http_method="GET",
        needs_ui=False,
    ),
    
    ToolDef(
        name="get_vertices_info",
        endpoint="vertices_info",
        category="inspection",
        description="Get detailed vertex information for a body including positions.",
        params=[
            ParamDef("body_index", ParamType.INT, "Index of the body to inspect", default=0),
        ],
        returns="Dictionary with vertex_count and list of vertex positions",
        http_method="GET",
        needs_ui=False,
    ),
    
    # =========================================================================
    # MEASUREMENT - Measurement tools
    # =========================================================================
    ToolDef(
        name="measure_distance",
        endpoint="measure_distance",
        category="measurement",
        description="Measure the minimum distance between two entities (faces, edges, vertices, or bodies).",
        params=[
            ParamDef("entity1_type", ParamType.STR, "Type: 'face', 'edge', 'vertex', or 'body'"),
            ParamDef("entity1_index", ParamType.INT, "Index of first entity"),
            ParamDef("entity2_type", ParamType.STR, "Type: 'face', 'edge', 'vertex', or 'body'"),
            ParamDef("entity2_index", ParamType.INT, "Index of second entity"),
            ParamDef("body1_index", ParamType.INT, "Body index for first entity", default=0),
            ParamDef("body2_index", ParamType.INT, "Body index for second entity", default=0),
        ],
        returns="Dictionary with distance_cm, distance_mm, point1, point2",
        http_method="POST",
        needs_ui=False,
    ),
    
    ToolDef(
        name="measure_angle",
        endpoint="measure_angle",
        category="measurement",
        description="Measure the angle between two planar faces or linear edges.",
        params=[
            ParamDef("entity1_type", ParamType.STR, "Type: 'face' or 'edge'"),
            ParamDef("entity1_index", ParamType.INT, "Index of first entity"),
            ParamDef("entity2_type", ParamType.STR, "Type: 'face' or 'edge'"),
            ParamDef("entity2_index", ParamType.INT, "Index of second entity"),
            ParamDef("body1_index", ParamType.INT, "Body index for first entity", default=0),
            ParamDef("body2_index", ParamType.INT, "Body index for second entity", default=0),
        ],
        returns="Dictionary with angle_degrees, angle_radians",
        http_method="POST",
        needs_ui=False,
    ),
    
    ToolDef(
        name="measure_area",
        endpoint="measure_area",
        category="measurement",
        description="Measure the area of a specific face.",
        params=[
            ParamDef("face_index", ParamType.INT, "Index of the face"),
            ParamDef("body_index", ParamType.INT, "Index of the body", default=0),
        ],
        returns="Dictionary with area_cm2, area_mm2, face_type",
        http_method="POST",
        needs_ui=False,
    ),
    
    ToolDef(
        name="measure_volume",
        endpoint="measure_volume",
        category="measurement",
        description="Measure the volume of a body.",
        params=[
            ParamDef("body_index", ParamType.INT, "Index of the body", default=0),
        ],
        returns="Dictionary with volume_cm3, volume_mm3, body_name",
        http_method="POST",
        needs_ui=False,
    ),
    
    ToolDef(
        name="measure_edge_length",
        endpoint="measure_edge_length",
        category="measurement",
        description="Measure the length of a specific edge.",
        params=[
            ParamDef("edge_index", ParamType.INT, "Index of the edge"),
            ParamDef("body_index", ParamType.INT, "Index of the body", default=0),
        ],
        returns="Dictionary with length_cm, length_mm, edge_type, start_point, end_point",
        http_method="POST",
        needs_ui=False,
    ),
    
    ToolDef(
        name="measure_body_properties",
        endpoint="measure_body_properties",
        category="measurement",
        description="Get comprehensive physical properties of a body including volume, surface area, bounding box, and centroid.",
        params=[
            ParamDef("body_index", ParamType.INT, "Index of the body", default=0),
        ],
        returns="Dictionary with volume, surface_area, bounding_box, centroid, face/edge/vertex counts",
        http_method="POST",
        needs_ui=False,
    ),
    
    ToolDef(
        name="measure_point_to_point",
        endpoint="measure_point_to_point",
        category="measurement",
        description="Measure the distance between two specific 3D points.",
        params=[
            ParamDef("point1", ParamType.LIST, "[x, y, z] coordinates of first point in cm"),
            ParamDef("point2", ParamType.LIST, "[x, y, z] coordinates of second point in cm"),
        ],
        returns="Dictionary with distance_cm, distance_mm, delta vector",
        http_method="POST",
        needs_ui=False,
    ),
    
    # =========================================================================
    # PARAMETERS - Model parameter tools
    # =========================================================================
    ToolDef(
        name="list_parameters",
        endpoint="list_parameters",
        category="parameters",
        description="List all model parameters with their values and expressions.",
        params=[],
        returns="Dictionary with ModelParameter list",
        http_method="GET",
        needs_ui=False,
    ),
    
    ToolDef(
        name="set_parameter",
        endpoint="set_parameter",
        category="parameters",
        description="Set a model parameter value. Useful for parametric design iteration.",
        params=[
            ParamDef("name", ParamType.STR, "Parameter name"),
            ParamDef("value", ParamType.STR, "Parameter value or expression"),
        ],
        returns="Success message",
    ),
    
    ToolDef(
        name="create_user_parameter",
        endpoint="create_parameter",
        category="parameters",
        description="Create a new user parameter in the design.",
        params=[
            ParamDef("name", ParamType.STR, "Parameter name (must be unique, no spaces)"),
            ParamDef("value", ParamType.STR, "Value expression (can reference other parameters)"),
            ParamDef("unit", ParamType.STR, "Unit type: 'mm', 'cm', 'in', 'deg', 'rad', or ''", default="mm"),
            ParamDef("comment", ParamType.STR, "Optional description", default=""),
        ],
        returns="Dictionary with parameter_name, value, expression",
    ),
    
    # =========================================================================
    # TELEMETRY - Telemetry tools
    # =========================================================================
    ToolDef(
        name="get_telemetry_info",
        endpoint="telemetry_info",
        category="telemetry",
        description="Get current telemetry status and configuration.",
        params=[],
        returns="Dictionary with telemetry_enabled, level, session_stats",
        http_method="GET",
        needs_ui=False,
    ),
    
    ToolDef(
        name="configure_telemetry",
        endpoint="configure_telemetry",
        category="telemetry",
        description="Configure the telemetry level.",
        params=[
            ParamDef("level", ParamType.STR, "Telemetry level: 'off', 'basic', or 'detailed'"),
        ],
        returns="Success status and new configuration",
    ),
]


# =============================================================================
# Lookup Functions
# =============================================================================

# Build lookup dictionaries for fast access
_TOOLS_BY_NAME: Dict[str, ToolDef] = {t.name: t for t in TOOL_DEFINITIONS}
_TOOLS_BY_ENDPOINT: Dict[str, ToolDef] = {t.endpoint: t for t in TOOL_DEFINITIONS}


def get_tool(name: str) -> Optional[ToolDef]:
    """Get a tool definition by function name.
    
    Args:
        name: The internal function name (e.g., "measure_distance")
        
    Returns:
        ToolDef or None if not found
    """
    return _TOOLS_BY_NAME.get(name)


def get_tool_by_endpoint(endpoint: str) -> Optional[ToolDef]:
    """Get a tool definition by HTTP endpoint.
    
    Args:
        endpoint: The HTTP endpoint name (e.g., "Box")
        
    Returns:
        ToolDef or None if not found
    """
    return _TOOLS_BY_ENDPOINT.get(endpoint)


def get_tools_by_category(category: str) -> List[ToolDef]:
    """Get all tools in a category.
    
    Args:
        category: Category name (e.g., "primitives", "sketches", "operations")
        
    Returns:
        List of ToolDef objects in that category
    """
    return [t for t in TOOL_DEFINITIONS if t.category == category]


def list_tool_names() -> List[str]:
    """Get list of all tool names."""
    return list(_TOOLS_BY_NAME.keys())


def list_categories() -> List[str]:
    """Get list of all unique categories."""
    return sorted(set(t.category for t in TOOL_DEFINITIONS))


def list_endpoints() -> List[str]:
    """Get list of all HTTP endpoints."""
    return list(_TOOLS_BY_ENDPOINT.keys())
