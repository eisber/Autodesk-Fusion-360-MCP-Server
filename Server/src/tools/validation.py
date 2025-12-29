"""Validation tools for Fusion 360 MCP Server.

Contains functions for testing connections, querying model state, and utility operations.
"""

import logging
import requests

from ..client import send_request, send_get_request
from ..config import ENDPOINTS, HEADERS


def test_connection():
    """Test the connection to the Fusion 360 Add-In server."""
    try:
        endpoint = ENDPOINTS["test_connection"]
        return send_request(endpoint, {}, {})
    except requests.RequestException as e:
        logging.error("Test connection failed: %s", e)
        raise


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
    try:
        endpoint = ENDPOINTS["model_state"]
        return send_get_request(endpoint)
    except requests.RequestException as e:
        logging.error("Get model state failed: %s", e)
        raise


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
    try:
        endpoint = f"{ENDPOINTS['faces_info']}?body_index={body_index}"
        return send_get_request(endpoint)
    except requests.RequestException as e:
        logging.error("Get faces info failed: %s", e)
        raise


def delete_all():
    """Delete all objects in the current Fusion 360 session."""
    try:
        endpoint = ENDPOINTS["delete_everything"]
        return send_request(endpoint, {}, HEADERS)
    except requests.RequestException as e:
        logging.error("Delete failed: %s", e)
        raise


def undo():
    """Undo the last action."""
    try:
        endpoint = ENDPOINTS["undo"]
        return send_request(endpoint, {}, {})
    except requests.RequestException as e:
        logging.error("Undo failed: %s", e)
        raise
