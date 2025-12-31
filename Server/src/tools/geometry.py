"""Geometry tools for Fusion 360 MCP Server.

Contains functions for creating 3D primitives, 2D sketches, extrusions, and operations.
"""

import logging
import requests

from ..client import send_request
from ..config import ENDPOINTS, HEADERS


# =============================================================================
# 3D Primitives
# =============================================================================

def draw_box(height_value: str, width_value: str, depth_value: str, 
             x_value: float, y_value: float, z_value: float, plane: str = "XY"):
    """
    Draw a box with given dimensions at the specified position.
    
    Args:
        height_value: Height of the box (string)
        width_value: Width of the box (string)
        depth_value: Depth/extrusion distance in z direction (string)
        x_value: X coordinate of center
        y_value: Y coordinate of center
        z_value: Z coordinate (creates offset plane)
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        endpoint = ENDPOINTS["draw_box"]
        data = {
            "height": height_value,
            "width": width_value,
            "depth": depth_value,
            "x": x_value,
            "y": y_value,
            "z": z_value,
            "Plane": plane
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw box failed: %s", e)
        return None


def draw_cylinder(radius: float, height: float, x: float, y: float, z: float, plane: str = "XY"):
    """
    Draw a cylinder with given radius and height at the specified position.
    
    Args:
        radius: Radius of the cylinder
        height: Height of the cylinder
        x: X coordinate of center
        y: Y coordinate of center
        z: Z coordinate of center
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        endpoint = ENDPOINTS["draw_cylinder"]
        data = {
            "radius": radius,
            "height": height,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw cylinder failed: %s", e)
        return None


def draw_sphere(x: float, y: float, z: float, radius: float):
    """
    Draw a sphere at the specified position.
    
    Args:
        x: X coordinate of center
        y: Y coordinate of center
        z: Z coordinate of center
        radius: Radius of the sphere
    """
    try:
        endpoint = ENDPOINTS["draw_sphere"]
        data = {
            "x": x,
            "y": y,
            "z": z,
            "radius": radius
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw sphere failed: %s", e)
        raise


# =============================================================================
# 2D Sketches
# =============================================================================

def draw2Dcircle(radius: float, x: float, y: float, z: float, plane: str = "XY"):
    """
    Draw a 2D circle on the specified plane.
    
    Args:
        radius: Radius of the circle
        x: X coordinate
        y: Y coordinate
        z: Z coordinate (offset for XY plane)
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        endpoint = ENDPOINTS["draw2Dcircle"]
        data = {
            "radius": radius,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw 2D circle failed: %s", e)
        raise


def draw_lines(points: list, plane: str):
    """
    Draw connected lines between points.
    
    Args:
        points: List of [x, y, z] coordinates
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        endpoint = ENDPOINTS["draw_lines"]
        data = {
            "points": points,
            "plane": plane
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw lines failed: %s", e)
        return None


def draw_one_line(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, plane: str = "XY"):
    """
    Draw a single line between two points.
    
    Args:
        x1, y1, z1: Start point coordinates
        x2, y2, z2: End point coordinates
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        endpoint = ENDPOINTS["draw_one_line"]
        data = {
            "x1": x1, "y1": y1, "z1": z1,
            "x2": x2, "y2": y2, "z2": z2,
            "plane": plane
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw one line failed: %s", e)
        raise


def draw_arc(point1: list, point2: list, point3: list, plane: str):
    """
    Draw an arc through three points.
    
    Args:
        point1: Start point [x, y, z]
        point2: Through point [x, y, z]
        point3: End point [x, y, z]
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        endpoint = ENDPOINTS["draw_arc"]
        data = {
            "point1": point1,
            "point2": point2,
            "point3": point3,
            "plane": plane
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw arc failed: %s", e)
        raise


def draw_2d_rectangle(x_1: float, y_1: float, z_1: float, x_2: float, y_2: float, z_2: float, plane: str):
    """
    Draw a 2D rectangle for loft/sweep operations.
    
    Args:
        x_1, y_1, z_1: First corner coordinates
        x_2, y_2, z_2: Second corner coordinates
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        endpoint = ENDPOINTS["draw_2d_rectangle"]
        data = {
            "x_1": x_1, "y_1": y_1, "z_1": z_1,
            "x_2": x_2, "y_2": y_2, "z_2": z_2,
            "plane": plane
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw 2D rectangle failed: %s", e)
        raise


def ellipsie(x_center: float, y_center: float, z_center: float,
             x_major: float, y_major: float, z_major: float,
             x_through: float, y_through: float, z_through: float, plane: str):
    """
    Draw an ellipse using center, major axis, and through point.
    
    Args:
        x_center, y_center, z_center: Center point coordinates
        x_major, y_major, z_major: Major axis point coordinates
        x_through, y_through, z_through: Point on the ellipse
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        endpoint = ENDPOINTS["ellipsie"]
        data = {
            "x_center": x_center, "y_center": y_center, "z_center": z_center,
            "x_major": x_major, "y_major": y_major, "z_major": z_major,
            "x_through": x_through, "y_through": y_through, "z_through": z_through,
            "plane": plane
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw ellipse failed: %s", e)
        raise


def spline(points: list, plane: str):
    """
    Draw a spline curve through points.
    
    Args:
        points: List of [x, y, z] coordinates
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        endpoint = ENDPOINTS["spline"]
        data = {
            "points": points,
            "plane": plane
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Spline failed: %s", e)
        raise


def draw_text(text: str, plane: str, x_1: float, y_1: float, z_1: float,
              x_2: float, y_2: float, z_2: float, thickness: float, value: float):
    """
    Draw text and optionally extrude it.
    
    Args:
        text: Text string to draw
        plane: Construction plane
        x_1, y_1, z_1: First corner of text bounds
        x_2, y_2, z_2: Second corner of text bounds
        thickness: Text height
        value: Extrusion distance (0 for no extrusion)
    """
    try:
        endpoint = ENDPOINTS["draw_text"]
        data = {
            "text": text,
            "plane": plane,
            "x_1": x_1, "y_1": y_1, "z_1": z_1,
            "x_2": x_2, "y_2": y_2, "z_2": z_2,
            "thickness": thickness,
            "extrusion_value": value
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw text failed: %s", e)
        raise


# =============================================================================
# Extrusion Operations
# =============================================================================

def extrude(value: float, angle: float):
    """
    Extrude the last sketch by the given value.
    
    Args:
        value: Extrusion distance
        angle: Taper angle in degrees
    """
    try:
        endpoint = ENDPOINTS["extrude"]
        data = {"distance": value, "operation": angle}
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Extrude failed: %s", e)
        raise


def extrude_thin(thickness: float, distance: float):
    """
    Create a thin-wall extrusion from the last sketch.
    
    Args:
        thickness: Wall thickness
        distance: Extrusion distance
    """
    try:
        endpoint = ENDPOINTS["extrude_thin"]
        data = {
            "thickness": thickness,
            "distance": distance
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Extrude thin failed: %s", e)
        raise


def cut_extrude(depth: float):
    """
    Create a cut extrusion from the last sketch.
    
    Args:
        depth: Cut depth (should be negative for downward cut)
    """
    try:
        endpoint = ENDPOINTS["cut_extrude"]
        data = {"depth": depth}
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Cut extrude failed: %s", e)
        raise


# =============================================================================
# 3D Operations
# =============================================================================

def loft(sketchcount: int):
    """
    Create a loft between the last N sketches.
    
    Args:
        sketchcount: Number of sketches to include in the loft
    """
    try:
        endpoint = ENDPOINTS["loft"]
        data = {"sketchcount": sketchcount}
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Loft failed: %s", e)
        raise


def sweep():
    """
    Create a sweep using the second-to-last sketch as profile and last sketch as path.
    """
    try:
        endpoint = ENDPOINTS["sweep"]
        return send_request(endpoint, {}, {})
    except requests.RequestException as e:
        logging.error("Sweep failed: %s", e)
        raise


def revolve(angle: float):
    """
    Revolve a user-selected profile around a user-selected axis.
    
    Args:
        angle: Revolution angle in degrees
    """
    try:
        endpoint = ENDPOINTS["revolve"]
        data = {"angle": angle}
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Revolve failed: %s", e)
        raise


def boolean_operation(operation: str):
    """
    Perform a boolean operation between bodies.
    
    Args:
        operation: Operation type ("cut", "join", or "intersect")
    """
    try:
        endpoint = ENDPOINTS["boolean_operation"]
        data = {"operation": operation}
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Boolean operation failed: %s", e)
        raise


def shell_body(thickness: float, faceindex: int):
    """
    Shell a body on a specified face.
    
    Args:
        thickness: Shell wall thickness
        faceindex: Index of the face to remove
    """
    try:
        endpoint = ENDPOINTS["shell_body"]
        data = {
            "thickness": thickness,
            "faceindex": faceindex
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Shell body failed: %s", e)
        return None


def fillet_edges(radius: str):
    """
    Create fillets on all edges.
    
    Args:
        radius: Fillet radius
    """
    try:
        endpoint = ENDPOINTS["fillet_edges"]
        data = {"radius": radius}
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Fillet edges failed: %s", e)
        raise


def draw_holes(points: list, depth: float, width: float, faceindex: int = 0):
    """
    Create holes at specified points on a face.
    
    Args:
        points: List of [x, y] coordinates for hole centers
        depth: Hole depth
        width: Hole diameter
        faceindex: Face index on the body
    """
    try:
        endpoint = ENDPOINTS["holes"]
        data = {
            "points": points,
            "width": width,
            "depth": depth,
            "faceindex": faceindex
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Draw holes failed: %s", e)
        raise


def create_thread(inside: bool, allsizes: int):
    """
    Create a thread on a user-selected face.
    
    Args:
        inside: True for internal thread, False for external
        allsizes: Index of thread size (0-22)
    """
    try:
        endpoint = ENDPOINTS["threaded"]
        data = {
            "inside": inside,
            "allsizes": allsizes
        }
        return send_request(endpoint, data, HEADERS)
    except requests.RequestException as e:
        logging.error("Create thread failed: %s", e)
        raise

