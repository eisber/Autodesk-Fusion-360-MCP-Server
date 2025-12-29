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
    run_test,
    run_all_tests,
    delete_test,
    create_snapshot,
    list_snapshots,
    restore_snapshot,
    delete_snapshot,
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
    "run_test",
    "run_all_tests",
    "delete_test",
    "create_snapshot",
    "list_snapshots",
    "restore_snapshot",
    "delete_snapshot",
]
