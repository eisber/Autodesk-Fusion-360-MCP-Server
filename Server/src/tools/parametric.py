"""Parametric modeling tools for Fusion 360 MCP Server.

Contains functions for advanced parametric design: parameters, sketches,
interference detection, timeline, mass properties, and construction geometry.
Uses @fusion_tool decorator for automatic HTTP handling and telemetry.
"""

from .base import fusion_tool

# =============================================================================
# User Parameters
# =============================================================================


@fusion_tool
def create_user_parameter(name: str, value: str, unit: str = "mm", comment: str = ""):
    """
    Create a new user parameter in the design.

    Args:
        name: Parameter name (must be unique, no spaces)
        value: Value expression (can reference other parameters, e.g., "width * 2")
        unit: Unit type ("mm", "cm", "in", "deg", "rad", or "" for unitless)
        comment: Optional description of the parameter

    Returns:
        Dictionary with:
        - success: True/False
        - parameter_name: Name of created parameter
        - value: Evaluated value
        - expression: The expression used
    """


@fusion_tool
def delete_user_parameter(name: str):
    """
    Delete a user parameter from the design.

    Args:
        name: Name of the parameter to delete

    Returns:
        Dictionary with:
        - success: True/False
        - message: Status message
    """


# =============================================================================
# Sketch Analysis
# =============================================================================


@fusion_tool(method="GET")
def get_sketch_info(sketch_index: int = -1):
    """
    Get detailed information about a sketch including geometry, constraints, and profiles.

    Args:
        sketch_index: Index of sketch to inspect (-1 for last sketch)

    Returns:
        Dictionary with:
        - sketch_name: Name of the sketch
        - sketch_index: Index in sketches collection
        - is_fully_constrained: Whether sketch is fully defined
        - profile_count: Number of closed profiles
        - curves: List of curves (lines, arcs, circles, splines) with geometry
        - constraints: List of geometric constraints
        - dimensions: List of sketch dimensions with values
        - points: List of sketch points
    """


@fusion_tool(method="GET")
def get_sketch_constraints(sketch_index: int = -1):
    """
    Get all geometric constraints in a sketch.

    Args:
        sketch_index: Index of sketch to inspect (-1 for last sketch)

    Returns:
        Dictionary with:
        - constraint_count: Number of constraints
        - constraints: List of constraints with type and referenced entities
    """


@fusion_tool(method="GET")
def get_sketch_dimensions(sketch_index: int = -1):
    """
    Get all dimensions in a sketch.

    Args:
        sketch_index: Index of sketch to inspect (-1 for last sketch)

    Returns:
        Dictionary with:
        - dimension_count: Number of dimensions
        - dimensions: List of dimensions with name, value, and expression
    """


# =============================================================================
# Interference Detection
# =============================================================================


@fusion_tool
def check_interference(body1_index: int, body2_index: int):
    """
    Check for interference (collision) between two specific bodies.

    Args:
        body1_index: Index of first body
        body2_index: Index of second body

    Returns:
        - has_interference: True if bodies intersect
        - interference_volume_cm3: Volume of interference region (if any)
        - body1_name: Name of first body
        - body2_name: Name of second body
    """


@fusion_tool(method="GET")
def check_all_interferences():
    """
    Check all bodies for potential interference using bounding box overlap.

    Note: This uses bounding box intersection as an approximation since Fusion 360 API
    doesn't expose a direct interference analysis feature. Bodies with overlapping
    bounding boxes may or may not actually intersect geometrically.

    Returns:
        - total_bodies: Number of bodies checked
        - interference_count: Number of potentially interfering pairs
        - interferences: List of body pairs with overlapping bounding boxes
        - method: "bounding_box_overlap"
    """


# =============================================================================
# Timeline / Feature History
# =============================================================================


@fusion_tool(method="GET")
def get_timeline_info():
    """
    Get information about the design timeline (feature history).

    Returns:
        Dictionary with:
        - feature_count: Number of features in timeline
        - current_position: Current rollback position
        - features: List of features with name, type, suppressed state, and index
    """


@fusion_tool
def rollback_to_feature(feature_index: int):
    """
    Roll back the timeline to a specific feature.

    Args:
        feature_index: Index of the feature to roll back to

    Returns:
        Dictionary with:
        - success: True/False
        - current_position: New timeline position
        - message: Status message
    """


@fusion_tool
def rollback_to_end():
    """
    Roll the timeline forward to the end (latest feature).

    Returns:
        Dictionary with:
        - success: True/False
        - current_position: New timeline position
    """


@fusion_tool
def suppress_feature(feature_index: int, suppress: bool = True):
    """
    Suppress or unsuppress a feature in the timeline.

    Args:
        feature_index: Index of the feature
        suppress: True to suppress, False to unsuppress

    Returns:
        Dictionary with:
        - success: True/False
        - feature_name: Name of the affected feature
        - is_suppressed: Current suppression state
    """


# =============================================================================
# Mass Properties
# =============================================================================


@fusion_tool
def get_mass_properties(body_index: int = 0, material_density: float | None = None):
    """
    Get mass properties of a body including center of gravity and moments of inertia.

    Args:
        body_index: Index of the body to analyze
        material_density: Optional density override in g/cm³ (default uses body's material)

    Returns:
        Dictionary with:
        - body_name: Name of the body
        - volume_cm3: Volume in cubic centimeters
        - density_g_cm3: Material density
        - mass_g: Mass in grams
        - center_of_gravity: [x, y, z] center of mass
        - moments_of_inertia: {Ixx, Iyy, Izz, Ixy, Iyz, Ixz} in g·cm²
        - principal_axes: Principal axes of inertia
        - radii_of_gyration: {kx, ky, kz} in cm
    """


# =============================================================================
# Construction Geometry
# =============================================================================


@fusion_tool
def create_offset_plane(offset: float, base_plane: str = "XY"):
    """
    Create a construction plane offset from a base plane.

    Args:
        offset: Distance to offset (in cm)
        base_plane: Base plane ("XY", "XZ", or "YZ")

    Returns:
        Dictionary with:
        - success: True/False
        - plane_name: Name of created construction plane
    """


@fusion_tool
def create_plane_at_angle(angle: float, base_plane: str = "XY", axis: str = "X"):
    """
    Create a construction plane at an angle to a base plane.

    Args:
        angle: Angle in degrees
        base_plane: Base plane ("XY", "XZ", or "YZ")
        axis: Rotation axis ("X", "Y", or "Z")

    Returns:
        Dictionary with:
        - success: True/False
        - plane_name: Name of created construction plane
    """


@fusion_tool
def create_midplane(body_index: int = 0, face1_index: int = 0, face2_index: int = 1):
    """
    Create a construction plane midway between two parallel faces.

    Args:
        body_index: Index of the body
        face1_index: Index of first face
        face2_index: Index of second face

    Returns:
        Dictionary with:
        - success: True/False
        - plane_name: Name of created construction plane
        - offset: Distance from each face
    """


@fusion_tool
def create_construction_axis(axis_type: str, **kwargs):
    """
    Create a construction axis.

    Args:
        axis_type: Type of axis to create:
            - "two_points": Through two points (requires point1, point2)
            - "edge": Along an edge (requires body_index, edge_index)
            - "normal": Normal to a face (requires body_index, face_index)
            - "cylinder": Axis of a cylindrical face (requires body_index, face_index)
        **kwargs: Additional arguments based on axis_type

    Returns:
        Dictionary with:
        - success: True/False
        - axis_name: Name of created construction axis
    """


@fusion_tool
def create_construction_point(point_type: str, **kwargs):
    """
    Create a construction point.

    Args:
        point_type: Type of point to create:
            - "coordinates": At specific coordinates (requires x, y, z)
            - "vertex": At a body vertex (requires body_index, vertex_index)
            - "center": At center of circular edge (requires body_index, edge_index)
            - "midpoint": At midpoint of edge (requires body_index, edge_index)
        **kwargs: Additional arguments based on point_type

    Returns:
        Dictionary with:
        - success: True/False
        - point_name: Name of created construction point
        - coordinates: [x, y, z] position
    """


@fusion_tool(method="GET")
def list_construction_geometry():
    """
    List all construction geometry in the design.

    Returns:
        Dictionary with:
        - planes: List of construction planes with name and type
        - axes: List of construction axes with name and direction
        - points: List of construction points with name and position
    """
