"""Configuration for the Fusion 360 MCP Server."""

# Base URL for the Fusion 360 Add-In HTTP server
BASE_URL = "http://localhost:5000"

# API Endpoints mapping
ENDPOINTS = {
    # Model state and validation
    "model_state": f"{BASE_URL}/model_state",
    "faces_info": f"{BASE_URL}/faces_info",
    "test_connection": f"{BASE_URL}/test_connection",
    
    # Script execution
    "execute_script": f"{BASE_URL}/execute_script",
    "script_result": f"{BASE_URL}/script_result",
    
    # Parameters
    "count_parameters": f"{BASE_URL}/count_parameters",
    "list_parameters": f"{BASE_URL}/list_parameters",
    "change_parameter": f"{BASE_URL}/set_parameter",
    
    # 3D Primitives
    "draw_box": f"{BASE_URL}/Box",
    "draw_cylinder": f"{BASE_URL}/draw_cylinder",
    "draw_sphere": f"{BASE_URL}/sphere",
    
    # 2D Sketches
    "draw2Dcircle": f"{BASE_URL}/create_circle",
    "draw_lines": f"{BASE_URL}/draw_lines",
    "draw_one_line": f"{BASE_URL}/draw_one_line",
    "draw_arc": f"{BASE_URL}/arc",
    "draw_2d_rectangle": f"{BASE_URL}/draw_2d_rectangle",
    "ellipsie": f"{BASE_URL}/ellipsis",
    "spline": f"{BASE_URL}/spline",
    "draw_text": f"{BASE_URL}/draw_text",
    
    # Extrusion operations
    "extrude": f"{BASE_URL}/extrude_last_sketch",
    "extrude_thin": f"{BASE_URL}/extrude_thin",
    "cut_extrude": f"{BASE_URL}/cut_extrude",
    
    # 3D Operations
    "loft": f"{BASE_URL}/loft",
    "sweep": f"{BASE_URL}/sweep",
    "revolve": f"{BASE_URL}/revolve",
    "boolean_operation": f"{BASE_URL}/boolean_operation",
    "shell_body": f"{BASE_URL}/shell_body",
    "fillet_edges": f"{BASE_URL}/fillet_edges",
    "holes": f"{BASE_URL}/holes",
    "threaded": f"{BASE_URL}/threaded",
    
    # Patterns
    "circular_pattern": f"{BASE_URL}/circular_pattern",
    "rectangular_pattern": f"{BASE_URL}/rectangular_pattern",
    
    # Transform
    "move_body": f"{BASE_URL}/move_body",
    
    # Export
    "export_step": f"{BASE_URL}/Export_STEP",
    "export_stl": f"{BASE_URL}/Export_STL",
    
    # Utility
    "undo": f"{BASE_URL}/undo",
    "delete_everything": f"{BASE_URL}/delete_everything",
    "destroy": f"{BASE_URL}/destroy",
    
    # Measurement
    "measure_distance": f"{BASE_URL}/measure_distance",
    "measure_angle": f"{BASE_URL}/measure_angle",
    "measure_area": f"{BASE_URL}/measure_area",
    "measure_volume": f"{BASE_URL}/measure_volume",
    "measure_edge_length": f"{BASE_URL}/measure_edge_length",
    "measure_body_properties": f"{BASE_URL}/measure_body_properties",
    "measure_point_to_point": f"{BASE_URL}/measure_point_to_point",
    "edges_info": f"{BASE_URL}/edges_info",
    "vertices_info": f"{BASE_URL}/vertices_info",
    
    # Parametric - User Parameters
    "create_parameter": f"{BASE_URL}/create_parameter",
    "delete_parameter": f"{BASE_URL}/delete_parameter",
    
    # Parametric - Sketch Analysis
    "sketch_info": f"{BASE_URL}/sketch_info",
    "sketch_constraints": f"{BASE_URL}/sketch_constraints",
    "sketch_dimensions": f"{BASE_URL}/sketch_dimensions",
    
    # Parametric - Interference Detection
    "check_interference": f"{BASE_URL}/check_interference",
    "check_all_interferences": f"{BASE_URL}/check_all_interferences",
    
    # Parametric - Timeline / Feature History
    "timeline_info": f"{BASE_URL}/timeline_info",
    "rollback_to_feature": f"{BASE_URL}/rollback_to_feature",
    "rollback_to_end": f"{BASE_URL}/rollback_to_end",
    "suppress_feature": f"{BASE_URL}/suppress_feature",
    
    # Parametric - Mass Properties
    "mass_properties": f"{BASE_URL}/mass_properties",
    
    # Parametric - Construction Geometry
    "create_offset_plane": f"{BASE_URL}/create_offset_plane",
    "create_plane_at_angle": f"{BASE_URL}/create_plane_at_angle",
    "create_midplane": f"{BASE_URL}/create_midplane",
    "create_construction_axis": f"{BASE_URL}/create_construction_axis",
    "create_construction_point": f"{BASE_URL}/create_construction_point",
    "list_construction_geometry": f"{BASE_URL}/list_construction_geometry",
}

# Request Headers
HEADERS = {
    "Content-Type": "application/json"
}

# Timeouts (in seconds)
REQUEST_TIMEOUT = 30
SCRIPT_EXECUTION_TIMEOUT = 30
SCRIPT_POLL_INTERVAL = 0.3

# Test storage configuration
# Tests and snapshots are stored per-project in this directory
import os
TEST_STORAGE_PATH = os.path.join(
    os.environ.get('USERPROFILE', os.path.expanduser('~')),
    'Desktop',
    'Fusion_Tests'
)
