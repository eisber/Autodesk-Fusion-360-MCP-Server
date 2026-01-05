"""Utils module for Fusion 360 MCP Add-In.

This module contains utility functions for state management, selection,
measurements, and parametric modeling.
"""

from .measurement import (
    get_edges_info,
    get_entity_from_body,
    get_vertices_info,
    measure_angle,
    measure_area,
    measure_body_properties,
    measure_distance,
    measure_edge_length,
    measure_point_to_point,
    measure_volume,
)
from .parametric import (
    check_all_interferences,
    check_interference,
    create_construction_axis,
    create_construction_point,
    create_midplane,
    create_offset_plane,
    create_plane_at_angle,
    create_user_parameter,
    delete_user_parameter,
    get_mass_properties,
    get_sketch_constraints,
    get_sketch_dimensions,
    get_sketch_info,
    get_timeline_info,
    list_construction_geometry,
    rollback_to_end,
    rollback_to_feature,
    suppress_feature,
)
from .selection import (
    select_body,
    select_sketch,
)
from .state import (
    delete_all,
    get_current_model_state,
    get_faces_info,
    get_model_parameters,
    set_parameter,
    undo,
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
