"""Tools module for Fusion 360 MCP Server.

This module contains organized tool functions grouped by category.
"""

from .geometry import (
    draw_box,
    draw_cylinder,
    draw_sphere,
    draw2Dcircle,
    draw_lines,
    draw_one_line,
    draw_arc,
    draw_2d_rectangle,
    ellipsie,
    spline,
    draw_text,
    extrude,
    extrude_thin,
    cut_extrude,
    loft,
    sweep,
    revolve,
    boolean_operation,
    shell_body,
    fillet_edges,
    draw_holes,
    create_thread,
)
from .patterns import (
    circular_pattern,
    rectangular_pattern,
    move_latest_body,
)
from .parameters import (
    count,
    list_parameters,
    change_parameter,
)
from .export import (
    export_step,
    export_stl,
)
from .validation import (
    test_connection,
    get_model_state,
    get_faces_info,
    delete_all,
    undo,
)
from .scripting import (
    execute_fusion_script,
)
from .testing import (
    save_test,
    load_tests,
    run_tests,
    delete_test,
    create_snapshot,
    list_snapshots,
    restore_snapshot,
    delete_snapshot,
)
from .measurement import (
    measure_distance,
    measure_angle,
    measure_area,
    measure_volume,
    measure_edge_length,
    measure_body_properties,
    measure_point_to_point,
    get_edges_info,
    get_vertices_info,
)
from .parametric import (
    # User Parameters
    create_parameter,
    delete_parameter,
    # Sketch Analysis
    get_sketch_info,
    get_sketch_constraints,
    get_sketch_dimensions,
    # Interference Detection
    check_interference,
    # Timeline / Feature History
    get_timeline_info,
    rollback_to_feature,
    rollback_to_end,
    suppress_feature,
    # Mass Properties
    get_mass_properties,
    # Construction Geometry
    create_offset_plane,
    create_plane_at_angle,
    create_midplane,
    create_construction_axis,
    create_construction_point,
    list_construction_geometry,
)

__all__ = [
    # Geometry - 3D Primitives
    "draw_box",
    "draw_cylinder",
    "draw_sphere",
    # Geometry - 2D Sketches
    "draw2Dcircle",
    "draw_lines",
    "draw_one_line",
    "draw_arc",
    "draw_2d_rectangle",
    "ellipsie",
    "spline",
    "draw_text",
    # Geometry - Extrusions
    "extrude",
    "extrude_thin",
    "cut_extrude",
    # Geometry - Operations
    "loft",
    "sweep",
    "revolve",
    "boolean_operation",
    "shell_body",
    "fillet_edges",
    "draw_holes",
    "create_thread",
    # Patterns
    "circular_pattern",
    "rectangular_pattern",
    "move_latest_body",
    # Parameters
    "count",
    "list_parameters",
    "change_parameter",
    # Export
    "export_step",
    "export_stl",
    # Validation
    "test_connection",
    "get_model_state",
    "get_faces_info",
    "delete_all",
    "undo",
    # Scripting
    "execute_fusion_script",
    # Testing
    "save_test",
    "load_tests",
    "run_tests",
    "delete_test",
    "create_snapshot",
    "list_snapshots",
    "restore_snapshot",
    "delete_snapshot",
    # Measurement
    "measure_distance",
    "measure_angle",
    "measure_area",
    "measure_volume",
    "measure_edge_length",
    "measure_body_properties",
    "measure_point_to_point",
    "get_edges_info",
    "get_vertices_info",
    # Parametric - User Parameters
    "create_parameter",
    "delete_parameter",
    # Parametric - Sketch Analysis
    "get_sketch_info",
    "get_sketch_constraints",
    "get_sketch_dimensions",
    # Parametric - Interference Detection
    "check_interference",
    # Parametric - Timeline / Feature History
    "get_timeline_info",
    "rollback_to_feature",
    "rollback_to_end",
    "suppress_feature",
    # Parametric - Mass Properties
    "get_mass_properties",
    # Parametric - Construction Geometry
    "create_offset_plane",
    "create_plane_at_angle",
    "create_midplane",
    "create_construction_axis",
    "create_construction_point",
    "list_construction_geometry",
]
