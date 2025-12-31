"""HTTP client utilities for communicating with Fusion 360 Add-In server."""

import json
import logging
import requests
from typing import Any, Dict, Optional

from .config import HEADERS, REQUEST_TIMEOUT, BASE_URL

# Mapping from endpoint paths to command names expected by MCP add-in
ENDPOINT_TO_COMMAND = {
    # Geometry - 3D Primitives
    "/Box": "draw_box",
    "/draw_cylinder": "draw_cylinder",
    "/sphere": "draw_sphere",
    # Geometry - 2D Sketches
    "/create_circle": "circle",
    "/draw_lines": "draw_lines",
    "/draw_one_line": "draw_one_line",
    "/arc": "arc",
    "/draw_2d_rectangle": "draw_2d_rectangle",
    "/ellipsis": "ellipsis",
    "/spline": "spline",
    "/draw_text": "draw_text",
    # Extrusion Operations
    "/extrude_last_sketch": "extrude_last_sketch",
    "/extrude_thin": "extrude_thin",
    "/cut_extrude": "cut_extrude",
    # 3D Operations
    "/loft": "loft",
    "/sweep": "sweep",
    "/revolve": "revolve_profile",
    "/boolean_operation": "boolean_operation",
    "/shell_body": "shell_body",
    "/fillet_edges": "fillet_edges",
    "/holes": "holes",
    "/threaded": "threaded",
    # Patterns
    "/circular_pattern": "circular_pattern",
    "/rectangular_pattern": "rectangular_pattern",
    "/move_body": "move_body",
    # Parameters
    "/set_parameter": "set_parameter",
    "/count_parameters": "count_parameters",
    "/list_parameters": "list_parameters",
    # Export
    "/Export_STEP": "export_step",
    "/Export_STL": "export_stl",
    # Utility
    "/delete_everything": "delete_everything",
    "/undo": "undo",
    "/execute_script": "execute_script",
    "/test_connection": "test_connection",
    # Measurement
    "/measure_distance": "measure_distance",
    "/measure_angle": "measure_angle",
    "/measure_area": "measure_area",
    "/measure_volume": "measure_volume",
    "/measure_edge_length": "measure_edge_length",
    "/measure_body_properties": "measure_body_properties",
    "/measure_point_to_point": "measure_point_to_point",
    "/edges_info": "edges_info",
    "/vertices_info": "vertices_info",
    # Parametric
    "/create_parameter": "create_parameter",
    "/delete_parameter": "delete_parameter",
    "/sketch_info": "sketch_info",
    "/sketch_constraints": "sketch_constraints",
    "/sketch_dimensions": "sketch_dimensions",
    "/check_interference": "check_interference",
    "/timeline_info": "timeline_info",
    "/rollback_to_feature": "rollback_to_feature",
    "/rollback_to_end": "rollback_to_end",
    "/suppress_feature": "suppress_feature",
    "/mass_properties": "mass_properties",
    "/create_offset_plane": "create_offset_plane",
    "/create_plane_at_angle": "create_plane_at_angle",
    "/create_midplane": "create_midplane",
    "/create_construction_axis": "create_construction_axis",
    "/create_construction_point": "create_construction_point",
    "/list_construction_geometry": "list_construction_geometry",
}


def send_request(endpoint: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Send a POST request to the Fusion 360 server.
    
    Args:
        endpoint: The API endpoint URL
        data: The payload data to send in the request
        headers: Optional headers to include (defaults to JSON content-type)
        
    Returns:
        JSON response from the server
        
    Raises:
        requests.RequestException: If the request fails after retries
        json.JSONDecodeError: If the response is not valid JSON
    """
    max_retries = 3
    headers = headers or HEADERS
    
    # Extract path from endpoint and map to command
    path = endpoint.replace(BASE_URL, "")
    command = ENDPOINT_TO_COMMAND.get(path, path.lstrip("/"))
    
    # Add command to data
    request_data = {"command": command, **data}
    
    for attempt in range(max_retries):
        try:
            json_data = json.dumps(request_data)
            response = requests.post(endpoint, json_data, headers=headers, timeout=REQUEST_TIMEOUT)
            
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logging.error("Failed to decode JSON response: %s", e)
                raise
                
        except requests.RequestException as e:
            logging.error("Request failed on attempt %d: %s", attempt + 1, e)
            if attempt == max_retries - 1:
                raise
                
        except Exception as e:
            logging.error("Unexpected error: %s", e)
            raise


def send_get_request(endpoint: str, timeout: int = REQUEST_TIMEOUT) -> Dict[str, Any]:
    """
    Send a GET request to the Fusion 360 server.
    
    Args:
        endpoint: The API endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        JSON response from the server
        
    Raises:
        requests.RequestException: If the request fails
    """
    try:
        response = requests.get(endpoint, timeout=timeout)
        return response.json()
    except requests.RequestException as e:
        logging.error("GET request failed: %s", e)
        raise
