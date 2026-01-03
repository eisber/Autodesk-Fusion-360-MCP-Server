"""HTTP route handlers for Fusion 360 MCP Add-In.

Routes are auto-generated from shared.tool_definitions.TOOL_DEFINITIONS.
Special handlers (execute_fusion_script, etc.) are defined manually.
"""

import sys
import os

# Add project root to path for shared imports
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from .http_server import routes
from ..registry import build_task_args, get_registry
from ..utils import (
    get_model_parameters,
    get_current_model_state,
    get_faces_info,
    get_edges_info,
    get_vertices_info,
    measure_distance,
    measure_angle,
    measure_area,
    measure_volume,
    measure_edge_length,
    measure_body_properties,
    measure_point_to_point,
    create_user_parameter,
)

# Import shared definitions
try:
    from shared import TOOL_DEFINITIONS, get_tool
except ImportError:
    # Fallback if shared module not available
    TOOL_DEFINITIONS = []
    get_tool = lambda x: None


# =============================================================================
# Special Route Handlers (not auto-generated)
# =============================================================================

@routes.post('/test_connection')
def post_test_connection(handler, design, data):
    """Test connection to the Add-In."""
    handler.send_json({"success": True, "message": "Connection successful"})


@routes.post('/execute_script')
def post_execute_script(handler, design, data):
    """Execute a Python script in Fusion 360.
    
    This is special - handled by the main MCP.py with SSE streaming.
    Route registered here for completeness, actual handler in MCP.py.
    """
    # This handler is overridden in MCP.py for SSE streaming
    pass


@routes.post('/cancel_task')
def post_cancel_task(handler, design, data):
    """Cancel a running task.
    
    Also handled specially in MCP.py for task management.
    """
    pass


@routes.get('/telemetry_info')
def get_telemetry_info(handler, design):
    """Get telemetry status - placeholder, handled in MCP.py."""
    handler.send_json({"telemetry_enabled": False, "level": "off"})


@routes.post('/configure_telemetry')
def post_configure_telemetry(handler, design, data):
    """Configure telemetry - placeholder, handled in MCP.py."""
    handler.send_json({"success": True, "level": data.get("level", "off")})


@routes.post('/inspect_api')
def post_inspect_api(handler, design, data):
    """Inspect Fusion 360 API - handled specially in MCP.py."""
    pass


# =============================================================================
# GET Route Handlers - Direct function calls (no task queue)
# =============================================================================

@routes.get('/model_state')
def get_model_state(handler, design):
    """Get current model state."""
    state = get_current_model_state(design)
    handler.send_json(state)


@routes.get('/list_parameters')
def get_list_parameters(handler, design):
    """List all model parameters."""
    params = get_model_parameters(design)
    handler.send_json({"ModelParameter": params})


@routes.get('/faces_info')
def get_faces(handler, design):
    """Get face information for a body."""
    params = handler.parse_query_params()
    body_idx = int(params.get('body_index', [0])[0])
    faces = get_faces_info(design, body_idx)
    handler.send_json(faces)


@routes.get('/edges_info')
def get_edges(handler, design):
    """Get edge information for a body."""
    params = handler.parse_query_params()
    body_idx = int(params.get('body_index', [0])[0])
    edges = get_edges_info(design, body_idx)
    handler.send_json(edges)


@routes.get('/vertices_info')
def get_vertices(handler, design):
    """Get vertex information for a body."""
    params = handler.parse_query_params()
    body_idx = int(params.get('body_index', [0])[0])
    vertices = get_vertices_info(design, body_idx)
    handler.send_json(vertices)


# =============================================================================
# POST Route Handlers - Task-based (uses registry)
# =============================================================================

@routes.post('/undo')
def post_undo(handler, design, data):
    """Undo the last action."""
    task = build_task_args('undo', data)
    handler.send_task_and_wait(task, "Undo executed")


@routes.post('/delete_everything')
def post_delete_everything(handler, design, data):
    """Delete all bodies in the design."""
    task = build_task_args('delete_all', data)
    handler.send_task_and_wait(task, "All bodies deleted")


@routes.post('/set_parameter')
def post_set_parameter(handler, design, data):
    """Set a model parameter value."""
    name = data.get('name')
    value = data.get('value')
    if name and value:
        task = build_task_args('set_parameter', data)
        handler.send_task_and_wait(task, f"Parameter {name} set")
    else:
        handler.send_json({"error": "Missing name or value"}, status=400)


@routes.post('/create_parameter')
def post_create_parameter(handler, design, data):
    """Create a new user parameter."""
    name = data.get('name')
    value = data.get('value')
    unit = data.get('unit', 'mm')
    comment = data.get('comment', '')
    if name and value:
        result = create_user_parameter(design, name, value, unit, comment)
        handler.send_json(result)
    else:
        handler.send_json({"error": "Missing name or value"}, status=400)


# =============================================================================
# Measurement Route Handlers - Direct function calls
# =============================================================================

@routes.post('/measure_distance')
def post_measure_distance(handler, design, data):
    """Measure distance between two entities."""
    result = measure_distance(
        design,
        data.get('entity1_type'),
        data.get('entity1_index'),
        data.get('entity2_type'),
        data.get('entity2_index'),
        data.get('body1_index', 0),
        data.get('body2_index', 0),
    )
    handler.send_json(result)


@routes.post('/measure_angle')
def post_measure_angle(handler, design, data):
    """Measure angle between two entities."""
    result = measure_angle(
        design,
        data.get('entity1_type'),
        data.get('entity1_index'),
        data.get('entity2_type'),
        data.get('entity2_index'),
        data.get('body1_index', 0),
        data.get('body2_index', 0),
    )
    handler.send_json(result)


@routes.post('/measure_area')
def post_measure_area(handler, design, data):
    """Measure area of a face."""
    result = measure_area(
        design,
        data.get('face_index'),
        data.get('body_index', 0),
    )
    handler.send_json(result)


@routes.post('/measure_volume')
def post_measure_volume(handler, design, data):
    """Measure volume of a body."""
    result = measure_volume(
        design,
        data.get('body_index', 0),
    )
    handler.send_json(result)


@routes.post('/measure_edge_length')
def post_measure_edge_length(handler, design, data):
    """Measure length of an edge."""
    result = measure_edge_length(
        design,
        data.get('edge_index'),
        data.get('body_index', 0),
    )
    handler.send_json(result)


@routes.post('/measure_body_properties')
def post_measure_body_properties(handler, design, data):
    """Get comprehensive body properties."""
    result = measure_body_properties(
        design,
        data.get('body_index', 0),
    )
    handler.send_json(result)


@routes.post('/measure_point_to_point')
def post_measure_point_to_point(handler, design, data):
    """Measure distance between two points."""
    result = measure_point_to_point(
        design,
        data.get('point1'),
        data.get('point2'),
    )
    handler.send_json(result)
