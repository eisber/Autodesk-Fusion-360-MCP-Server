"""Fusion 360 MCP Server - Entry Point.

This is a thin wrapper that registers tools and prompts from the src/ library.
All implementation logic lives in src/tools/ modules.
"""

import argparse
from mcp.server.fastmcp import FastMCP

from src.instructions import SYSTEM_INSTRUCTIONS
from src.prompts import PROMPTS
from src import tools


# =============================================================================
# Initialize MCP Server
# =============================================================================

mcp = FastMCP("Fusion", instructions=SYSTEM_INSTRUCTIONS)


# =============================================================================
# Register Tools - Geometry (DISABLED - use execute_fusion_script instead)
# =============================================================================

# mcp.tool()(tools.draw_box)
# mcp.tool()(tools.draw_cylinder)
# mcp.tool()(tools.draw_sphere)
# mcp.tool()(tools.draw2Dcircle)
# mcp.tool()(tools.draw_lines)
# mcp.tool()(tools.draw_one_line)
# mcp.tool()(tools.draw_arc)
# mcp.tool()(tools.draw_2d_rectangle)
# mcp.tool()(tools.ellipsie)
# mcp.tool()(tools.spline)
# mcp.tool()(tools.draw_text)
# mcp.tool()(tools.draw_holes)
# mcp.tool()(tools.create_thread)

# Extrusion Operations
# mcp.tool()(tools.extrude)
# mcp.tool()(tools.extrude_thin)
# mcp.tool()(tools.cut_extrude)

# 3D Operations
# mcp.tool()(tools.loft)
# mcp.tool()(tools.sweep)
# mcp.tool()(tools.revolve)
# mcp.tool()(tools.boolean_operation)
# mcp.tool()(tools.shell_body)
# mcp.tool()(tools.fillet_edges)


# =============================================================================
# Register Tools - Patterns & Transform
# =============================================================================

mcp.tool()(tools.circular_pattern)
mcp.tool()(tools.rectangular_pattern)
mcp.tool()(tools.move_latest_body)


# =============================================================================
# Register Tools - Parameters
# =============================================================================

mcp.tool()(tools.count)
mcp.tool()(tools.list_parameters)
mcp.tool()(tools.change_parameter)


# =============================================================================
# Register Tools - Export
# =============================================================================

mcp.tool()(tools.export_step)
mcp.tool()(tools.export_stl)


# =============================================================================
# Register Tools - Validation & Utility
# =============================================================================

mcp.tool()(tools.test_connection)
mcp.tool()(tools.get_model_state)
mcp.tool()(tools.get_faces_info)
mcp.tool()(tools.delete_all)
mcp.tool()(tools.undo)


# =============================================================================
# Register Tools - Scripting
# =============================================================================

mcp.tool()(tools.execute_fusion_script)


# =============================================================================
# Register Tools - Testing & Snapshots
# =============================================================================

mcp.tool()(tools.save_test)
mcp.tool()(tools.load_tests)
mcp.tool()(tools.run_tests)
mcp.tool()(tools.delete_test)
mcp.tool()(tools.create_snapshot)
mcp.tool()(tools.list_snapshots)
mcp.tool()(tools.restore_snapshot)
mcp.tool()(tools.delete_snapshot)


# =============================================================================
# Register Tools - Measurement
# =============================================================================

mcp.tool()(tools.measure_distance)
mcp.tool()(tools.measure_angle)
mcp.tool()(tools.measure_area)
mcp.tool()(tools.measure_volume)
mcp.tool()(tools.measure_edge_length)
mcp.tool()(tools.measure_body_properties)
mcp.tool()(tools.measure_point_to_point)
mcp.tool()(tools.get_edges_info)
mcp.tool()(tools.get_vertices_info)


# =============================================================================
# Register Tools - Parametric Modeling
# =============================================================================

# User Parameters
mcp.tool()(tools.create_parameter)
mcp.tool()(tools.delete_parameter)

# Sketch Analysis
mcp.tool()(tools.get_sketch_info)
mcp.tool()(tools.get_sketch_constraints)
mcp.tool()(tools.get_sketch_dimensions)

# Interference Detection
mcp.tool()(tools.check_interference)

# Timeline / Feature History
mcp.tool()(tools.get_timeline_info)
mcp.tool()(tools.rollback_to_feature)
mcp.tool()(tools.rollback_to_end)
mcp.tool()(tools.suppress_feature)

# Mass Properties
mcp.tool()(tools.get_mass_properties)

# Construction Geometry
mcp.tool()(tools.create_offset_plane)
mcp.tool()(tools.create_plane_at_angle)
mcp.tool()(tools.create_midplane)
mcp.tool()(tools.create_construction_axis)
mcp.tool()(tools.create_construction_point)
mcp.tool()(tools.list_construction_geometry)


# =============================================================================
# Register Prompts
# =============================================================================

for name, content in PROMPTS.items():
    @mcp.prompt(name=name)
    def _prompt(content=content):
        return content


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fusion 360 MCP Server")
    parser.add_argument(
        "--server_type", 
        type=str, 
        default="sse", 
        choices=["sse", "stdio"],
        help="Transport type for MCP server"
    )
    args = parser.parse_args()
    
    mcp.run(transport=args.server_type)
