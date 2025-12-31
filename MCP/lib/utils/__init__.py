"""Utils module for Fusion 360 MCP Add-In.

This module contains utility functions for state management, selection,
export operations, measurements, and parametric modeling.
"""

from .state import (
    get_model_parameters,
    get_current_model_state,
    get_faces_info,
    set_parameter,
    undo,
    delete_all,
)
from .selection import (
    select_body,
    select_sketch,
)
from .export import (
    export_as_step,
    export_as_stl,
)
from .measurement import (
    get_entity_from_body,
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
    create_user_parameter,
    delete_user_parameter,
    get_sketch_info,
    get_sketch_constraints,
    get_sketch_dimensions,
    check_interference,
    check_all_interferences,
    get_timeline_info,
    rollback_to_feature,
    rollback_to_end,
    suppress_feature,
    get_mass_properties,
    create_offset_plane,
    create_plane_at_angle,
    create_midplane,
    create_construction_axis,
    create_construction_point,
    list_construction_geometry,
)

__all__ = [
    # State
    "get_model_parameters",
    "get_current_model_state",
    "get_faces_info",
    "set_parameter",
    "undo",
    "delete_all",
    # Selection
    "select_body",
    "select_sketch",
    # Export
    "export_as_step",
    "export_as_stl",
    # Measurement
    "get_entity_from_body",
    "measure_distance",
    "measure_angle",
    "measure_area",
    "measure_volume",
    "measure_edge_length",
    "measure_body_properties",
    "measure_point_to_point",
    "get_edges_info",
    "get_vertices_info",
    # Parametric
    "create_user_parameter",
    "delete_user_parameter",
    "get_sketch_info",
    "get_sketch_constraints",
    "get_sketch_dimensions",
    "check_interference",
    "check_all_interferences",
    "get_timeline_info",
    "rollback_to_feature",
    "rollback_to_end",
    "suppress_feature",
    "get_mass_properties",
    "create_offset_plane",
    "create_plane_at_angle",
    "create_midplane",
    "create_construction_axis",
    "create_construction_point",
    "list_construction_geometry",
]
