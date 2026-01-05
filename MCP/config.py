# Fusion 360 API Configuration
import os

# Add-In identity
COMPANY_NAME = "Autodesk"
ADDIN_NAME = "MCP"
sample_palette_id = "MCP_Palette"

# Port configuration - can be overridden via environment variable
FUSION_MCP_PORT = int(os.environ.get("FUSION_MCP_PORT", "5000"))

# Base URL for the Fusion 360 server
BASE_URL = f"http://localhost:{FUSION_MCP_PORT}"

# API Endpoints - Only essential endpoints, SCRIPTABLE tools use execute_script
ENDPOINTS = {
    # Infrastructure
    "test_connection": f"{BASE_URL}/test_connection",
    "model_state": f"{BASE_URL}/model_state",
    "undo": f"{BASE_URL}/undo",
    "delete_everything": f"{BASE_URL}/delete_everything",
    # Scripting
    "execute_script": f"{BASE_URL}/execute_script",
    "cancel_task": f"{BASE_URL}/cancel_task",
    # Inspection
    "faces_info": f"{BASE_URL}/faces_info",
    "edges_info": f"{BASE_URL}/edges_info",
    "vertices_info": f"{BASE_URL}/vertices_info",
    "inspect_api": f"{BASE_URL}/inspect_api",
    # Measurement
    "measure_distance": f"{BASE_URL}/measure_distance",
    "measure_angle": f"{BASE_URL}/measure_angle",
    "measure_area": f"{BASE_URL}/measure_area",
    "measure_volume": f"{BASE_URL}/measure_volume",
    "measure_edge_length": f"{BASE_URL}/measure_edge_length",
    "measure_body_properties": f"{BASE_URL}/measure_body_properties",
    "measure_point_to_point": f"{BASE_URL}/measure_point_to_point",
    # Parameters
    "list_parameters": f"{BASE_URL}/list_parameters",
    "set_parameter": f"{BASE_URL}/set_parameter",
    "create_parameter": f"{BASE_URL}/create_parameter",
    # Telemetry
    "telemetry_info": f"{BASE_URL}/telemetry_info",
    "configure_telemetry": f"{BASE_URL}/configure_telemetry",
}

# Request Headers
HEADERS = {"Content-Type": "application/json"}

# Timeouts (in seconds)
REQUEST_TIMEOUT = 30
