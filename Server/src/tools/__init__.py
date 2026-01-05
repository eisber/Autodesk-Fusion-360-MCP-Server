"""Tools module for Fusion 360 MCP Server.

This module exports all tools available via MCP.
SCRIPTABLE tools (geometry creation, features, patterns) have been removed -
use execute_fusion_script instead.

Tool categories:
- Infrastructure: test_connection, get_model_state, undo, delete_all
- Scripting: execute_fusion_script, cancel_fusion_task
- Inspection: inspect_adsk_api, get_faces_info, get_edges_info, get_vertices_info
- Measurement: measure_distance, measure_angle, measure_area, etc.
- Parameters: list_parameters, set_parameter, create_user_parameter
- Telemetry: configure_telemetry
"""

# Validation/Infrastructure tools
# Inspection tools
from .inspection import (
    get_adsk_class_info,
    inspect_adsk_api,
)

# Measurement tools
from .measurement import (
    get_edges_info,
    get_vertices_info,
    measure_angle,
    measure_area,
    measure_body_properties,
    measure_distance,
    measure_edge_length,
    measure_point_to_point,
    measure_volume,
)

# Parameter tools
from .parameters import (
    list_parameters,
    set_parameter,
)

# Parametric tools (convenience)
from .parametric import (
    # Kept for potential future use but not in shared defs
    check_all_interferences,
    create_user_parameter,
    list_construction_geometry,
    suppress_feature,
)

# Scripting tools (core functionality)
from .scripting import (
    cancel_fusion_task,
    execute_fusion_script,
)

# Telemetry tools
from .telemetry_tools import (
    configure_telemetry,
)

# Testing tools (kept for internal use, not in shared defs)
from .testing import (
    create_snapshot,
    delete_snapshot,
    delete_test,
    list_snapshots,
    load_tests,
    restore_snapshot,
    run_tests,
    save_test,
)
from .validation import (
    delete_all,
    get_faces_info,
    get_model_state,
    test_connection,
    undo,
)

__all__ = [
    # Infrastructure
    "test_connection",
    "get_model_state",
    "delete_all",
    "undo",
    # Scripting (most powerful)
    "execute_fusion_script",
    "cancel_fusion_task",
    # Inspection
    "inspect_adsk_api",
    "get_adsk_class_info",
    "get_faces_info",
    "get_edges_info",
    "get_vertices_info",
    # Measurement
    "measure_distance",
    "measure_angle",
    "measure_area",
    "measure_volume",
    "measure_edge_length",
    "measure_body_properties",
    "measure_point_to_point",
    # Parameters
    "list_parameters",
    "set_parameter",
    "create_user_parameter",
    # Telemetry
    "configure_telemetry",
    # Utility (kept for internal use)
    "check_all_interferences",
    "list_construction_geometry",
    "suppress_feature",
    # Testing (kept for internal use)
    "save_test",
    "load_tests",
    "run_tests",
    "delete_test",
    "create_snapshot",
    "list_snapshots",
    "restore_snapshot",
    "delete_snapshot",
]
