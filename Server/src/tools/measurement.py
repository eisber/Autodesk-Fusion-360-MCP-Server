"""Measurement tools for Fusion 360 MCP Server.

Contains functions for measuring distances, angles, areas, volumes, and other geometric properties.
Uses @fusion_tool decorator for automatic HTTP handling and telemetry.
"""

from .base import fusion_tool


@fusion_tool
def measure_distance(
    entity1_type: str,
    entity1_index: int,
    entity2_type: str,
    entity2_index: int,
    body1_index: int = 0,
    body2_index: int = 0,
):
    """
    Measure the minimum distance between two entities.

    Args:
        entity1_type: Type of first entity ("face", "edge", "vertex", "body", "point")
        entity1_index: Index of first entity (for face/edge/vertex within the body)
        entity2_type: Type of second entity ("face", "edge", "vertex", "body", "point")
        entity2_index: Index of second entity (for face/edge/vertex within the body)
        body1_index: Index of the body containing entity1 (default: 0)
        body2_index: Index of the body containing entity2 (default: 0)

    Returns:
        Dictionary with:
        - distance: Minimum distance in cm
        - point1: [x, y, z] closest point on entity1
        - point2: [x, y, z] closest point on entity2
    """


@fusion_tool
def measure_angle(
    entity1_type: str,
    entity1_index: int,
    entity2_type: str,
    entity2_index: int,
    body1_index: int = 0,
    body2_index: int = 0,
):
    """
    Measure the angle between two planar faces or linear edges.

    Args:
        entity1_type: Type of first entity ("face" or "edge")
        entity1_index: Index of first entity
        entity2_type: Type of second entity ("face" or "edge")
        entity2_index: Index of second entity
        body1_index: Index of the body containing entity1 (default: 0)
        body2_index: Index of the body containing entity2 (default: 0)

    Returns:
        Dictionary with:
        - angle_degrees: Angle in degrees
        - angle_radians: Angle in radians
    """


@fusion_tool
def measure_area(face_index: int, body_index: int = 0):
    """
    Measure the area of a specific face.

    Args:
        face_index: Index of the face to measure
        body_index: Index of the body containing the face (default: 0)

    Returns:
        Dictionary with:
        - area_cm2: Area in square centimeters
        - area_mm2: Area in square millimeters
        - face_type: Type of face (Plane, Cylinder, etc.)
    """


@fusion_tool
def measure_volume(body_index: int = 0):
    """
    Measure the volume of a body.

    Args:
        body_index: Index of the body to measure (default: 0)

    Returns:
        Dictionary with:
        - volume_cm3: Volume in cubic centimeters
        - volume_mm3: Volume in cubic millimeters
        - body_name: Name of the body
    """


@fusion_tool
def measure_edge_length(edge_index: int, body_index: int = 0):
    """
    Measure the length of a specific edge.

    Args:
        edge_index: Index of the edge to measure
        body_index: Index of the body containing the edge (default: 0)

    Returns:
        Dictionary with:
        - length_cm: Length in centimeters
        - length_mm: Length in millimeters
        - edge_type: Type of edge (Line, Arc, Circle, etc.)
        - start_point: [x, y, z] start point
        - end_point: [x, y, z] end point
    """


@fusion_tool
def measure_body_properties(body_index: int = 0):
    """
    Get comprehensive physical properties of a body.

    Args:
        body_index: Index of the body to measure (default: 0)

    Returns:
        Dictionary with:
        - volume_cm3: Volume in cubic centimeters
        - surface_area_cm2: Total surface area in square centimeters
        - bounding_box: {min: [x,y,z], max: [x,y,z], size: [dx,dy,dz]}
        - centroid: [x, y, z] center of mass
        - face_count: Number of faces
        - edge_count: Number of edges
        - vertex_count: Number of vertices
        - body_name: Name of the body
    """


@fusion_tool
def measure_point_to_point(point1: list, point2: list):
    """
    Measure the distance between two specific 3D points.

    Args:
        point1: [x, y, z] coordinates of first point (in cm)
        point2: [x, y, z] coordinates of second point (in cm)

    Returns:
        Dictionary with:
        - distance_cm: Distance in centimeters
        - distance_mm: Distance in millimeters
        - delta: [dx, dy, dz] difference vector
    """


@fusion_tool(method="GET")
def get_edges_info(body_index: int = 0):
    """
    Get detailed edge information for a body.

    Args:
        body_index: Index of the body to inspect (default: 0)

    Returns:
        Dictionary with:
        - edge_count: Number of edges
        - edges: List with details for each edge (index, type, length, start_point, end_point)
    """


@fusion_tool(method="GET")
def get_vertices_info(body_index: int = 0):
    """
    Get detailed vertex information for a body.

    Args:
        body_index: Index of the body to inspect (default: 0)

    Returns:
        Dictionary with:
        - vertex_count: Number of vertices
        - vertices: List with details for each vertex (index, position [x,y,z])
    """
