"""Pattern tools for Fusion 360 MCP Server.

Contains functions for creating circular and rectangular patterns, and moving bodies.
"""

import logging
import requests

from ..client import send_request
from ..config import ENDPOINTS, HEADERS


def circular_pattern(plane: str, quantity: float, axis: str):
    """
    Create a circular pattern of the last body.
    
    Args:
        plane: Construction plane ("XY", "XZ", or "YZ")
        quantity: Number of instances in the pattern
        axis: Rotation axis ("X", "Y", or "Z")
    """
    try:
        endpoint = ENDPOINTS["circular_pattern"]
        data = {
            "plane": plane,
            "quantity": quantity,
            "axis": axis
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Circular pattern failed: %s", e)
        raise


def rectangular_pattern(plane: str, quantity_one: float, quantity_two: float,
                        distance_one: float, distance_two: float,
                        axis_one: str, axis_two: str):
    """
    Create a rectangular pattern of the last body.
    
    Args:
        plane: Construction plane ("XY", "XZ", or "YZ")
        quantity_one: Number of instances in first direction
        quantity_two: Number of instances in second direction
        distance_one: Spacing in first direction (multiply by 10 for Fusion units)
        distance_two: Spacing in second direction (multiply by 10 for Fusion units)
        axis_one: First axis direction ("X", "Y", or "Z")
        axis_two: Second axis direction ("X", "Y", or "Z")
    """
    try:
        endpoint = ENDPOINTS["rectangular_pattern"]
        data = {
            "plane": plane,
            "quantity_one": quantity_one,
            "quantity_two": quantity_two,
            "distance_one": distance_one,
            "distance_two": distance_two,
            "axis_one": axis_one,
            "axis_two": axis_two
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Rectangular pattern failed: %s", e)
        raise


def move_latest_body(x: float, y: float, z: float):
    """
    Move the last created body by the specified vector.
    
    Args:
        x: X translation distance
        y: Y translation distance
        z: Z translation distance
    """
    try:
        endpoint = ENDPOINTS["move_body"]
        data = {
            "x": x,
            "y": y,
            "z": z
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Move body failed: %s", e)
        raise
