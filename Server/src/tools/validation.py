"""Validation tools for Fusion 360 MCP Server.

Contains functions for testing connections, querying model state, and utility operations.
Uses @fusion_tool decorator for automatic HTTP handling and telemetry.
"""

from .base import fusion_tool


@fusion_tool
def test_connection():
    """Test the connection to the Fusion 360 Add-In server."""


@fusion_tool(method="GET")
def get_model_state():
    """
    Get the current state of the Fusion 360 model.

    Returns:
        Dictionary with:
        - body_count: Number of bodies in the model
        - sketch_count: Number of sketches
        - bodies: List with details for each body (name, volume, bounding box)
        - sketches: List with details for each sketch (name, profile count)
        - design_name: Name of the active design
    """


@fusion_tool(method="GET")
def get_faces_info(body_index: int = 0):
    """
    Get detailed face information for a body.

    Args:
        body_index: Index of the body to inspect

    Returns:
        Dictionary with:
        - face_count: Number of faces
        - faces: List with details for each face (index, type, area, centroid)
    """


@fusion_tool
def delete_all():
    """Delete all objects in the current Fusion 360 session."""


@fusion_tool
def undo():
    """Undo the last action."""
