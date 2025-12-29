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
}

# Request Headers
HEADERS = {
    "Content-Type": "application/json"
}

# Timeouts (in seconds)
REQUEST_TIMEOUT = 30
SCRIPT_EXECUTION_TIMEOUT = 30
SCRIPT_POLL_INTERVAL = 0.3
