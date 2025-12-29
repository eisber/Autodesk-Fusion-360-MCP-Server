"""Features module for Fusion 360 MCP Add-In.

This module contains functions for creating 3D features like extrusions,
operations, patterns, and transformations.
"""

from .extrusion import (
    extrude_last_sketch,
    extrude_thin,
    cut_extrude,
)
from .operations import (
    loft,
    sweep,
    revolve_profile,
    boolean_operation,
    shell_existing_body,
    fillet_edges,
    holes,
    create_thread,
)
from .patterns import (
    circular_pattern,
    rectangular_pattern,
)
from .transform import (
    move_last_body,
    offsetplane,
)

__all__ = [
    # Extrusion
    "extrude_last_sketch",
    "extrude_thin",
    "cut_extrude",
    # Operations
    "loft",
    "sweep",
    "revolve_profile",
    "boolean_operation",
    "shell_existing_body",
    "fillet_edges",
    "holes",
    "create_thread",
    # Patterns
    "circular_pattern",
    "rectangular_pattern",
    # Transform
    "move_last_body",
    "offsetplane",
]
