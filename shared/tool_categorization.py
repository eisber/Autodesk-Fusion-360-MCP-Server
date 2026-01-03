"""Tool categorization and analysis for Fusion 360 MCP.

This module analyzes which tools should remain as dedicated MCP tools vs
which could be replaced by execute_fusion_script.

Categories:
1. ESSENTIAL - Must remain as dedicated tools (special handling, UI interaction, etc.)
2. CONVENIENCE - Useful as tools but agent could use script instead
3. SCRIPTABLE - Should be removed; agent should use execute_fusion_script
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict


class ToolNecessity(Enum):
    """Classification of tool necessity."""
    ESSENTIAL = "essential"      # Must keep - special behavior or infrastructure
    CONVENIENCE = "convenience"  # Useful shortcut but scriptable
    SCRIPTABLE = "scriptable"    # Remove - agent should use execute_fusion_script


@dataclass
class ToolAnalysis:
    """Analysis of a single tool."""
    name: str
    necessity: ToolNecessity
    reason: str
    script_example: str = ""  # Example of how to do it via script


# =============================================================================
# Tool Analysis by Category
# =============================================================================

TOOL_ANALYSIS: Dict[str, List[ToolAnalysis]] = {
    # =========================================================================
    # GROUP 1: INFRASTRUCTURE - Must keep
    # These provide essential infrastructure that scripts can't replace
    # =========================================================================
    "infrastructure": [
        ToolAnalysis(
            name="execute_fusion_script",
            necessity=ToolNecessity.ESSENTIAL,
            reason="Core tool - this IS how agent runs arbitrary code",
        ),
        ToolAnalysis(
            name="test_connection",
            necessity=ToolNecessity.ESSENTIAL,
            reason="Infrastructure - verifies add-in is running",
        ),
        ToolAnalysis(
            name="get_model_state",
            necessity=ToolNecessity.ESSENTIAL,
            reason="Infrastructure - quick state check before/after operations",
        ),
        ToolAnalysis(
            name="undo",
            necessity=ToolNecessity.ESSENTIAL,
            reason="Infrastructure - core undo capability, needs app.executeCommand",
        ),
        ToolAnalysis(
            name="cancel_fusion_task",
            necessity=ToolNecessity.ESSENTIAL,
            reason="Infrastructure - cancel long-running scripts",
        ),
    ],
    
    # =========================================================================
    # GROUP 2: INSPECTION/QUERY - Keep for convenience
    # Quick queries that save token cost vs writing full scripts
    # =========================================================================
    "inspection": [
        ToolAnalysis(
            name="inspect_adsk_api",
            necessity=ToolNecessity.ESSENTIAL,
            reason="Meta-tool - helps agent learn API for writing scripts",
        ),
        ToolAnalysis(
            name="get_faces_info",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Quick lookup; saves writing inspection script",
            script_example="""
faces = []
body = rootComp.bRepBodies.item(0)
for i in range(body.faces.count):
    face = body.faces.item(i)
    faces.append({'index': i, 'area': face.area, 'type': face.geometry.objectType})
result = json.dumps(faces)
""",
        ),
        ToolAnalysis(
            name="get_edges_info",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Quick lookup; saves writing inspection script",
        ),
        ToolAnalysis(
            name="get_vertices_info",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Quick lookup; saves writing inspection script",
        ),
        ToolAnalysis(
            name="measure_distance",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Common operation; saves complex measureManager script",
        ),
        ToolAnalysis(
            name="measure_volume",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Quick lookup; body.volume is simple but this formats nicely",
        ),
        ToolAnalysis(
            name="measure_body_properties",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Comprehensive query; saves writing full inspection",
        ),
    ],
    
    # =========================================================================
    # GROUP 3: GEOMETRY CREATION - Mostly scriptable
    # Agent can write these as scripts; dedicated tools add token overhead
    # =========================================================================
    "geometry_creation": [
        ToolAnalysis(
            name="draw_box",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Simple API call; agent should learn to script this",
            script_example="""
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
sketch.sketchCurves.sketchLines.addCenterPointRectangle(
    adsk.core.Point3D.create(x, y, 0),
    adsk.core.Point3D.create(x + width/2, y + height/2, 0)
)
prof = sketch.profiles.item(0)
ext = rootComp.features.extrudeFeatures.addSimple(
    prof, adsk.core.ValueInput.createByReal(depth),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
result = f"Created box: {ext.bodies.item(0).name}"
""",
        ),
        ToolAnalysis(
            name="draw_cylinder",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Simple API call",
        ),
        ToolAnalysis(
            name="draw_sphere",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Simple revolve; good example for agent to learn",
        ),
        ToolAnalysis(
            name="draw_circle",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Single API call",
        ),
        ToolAnalysis(
            name="draw_ellipse",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Single API call",
        ),
        ToolAnalysis(
            name="draw_2d_rectangle",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Single API call",
        ),
        ToolAnalysis(
            name="draw_lines",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Simple loop; good learning example",
        ),
        ToolAnalysis(
            name="draw_one_line",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Single API call",
        ),
        ToolAnalysis(
            name="draw_arc",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Single API call",
        ),
        ToolAnalysis(
            name="draw_spline",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Single API call",
        ),
        ToolAnalysis(
            name="draw_text",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Moderately complex but scriptable",
        ),
    ],
    
    # =========================================================================
    # GROUP 4: FEATURE OPERATIONS - Mostly scriptable
    # Standard Fusion feature operations
    # =========================================================================
    "features": [
        ToolAnalysis(
            name="extrude_last_sketch",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Very common; agent should master this pattern",
            script_example="""
sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
prof = sketch.profiles.item(0)
ext = rootComp.features.extrudeFeatures.addSimple(
    prof, adsk.core.ValueInput.createByReal(distance),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
result = f"Extruded: {ext.bodies.item(0).name}"
""",
        ),
        ToolAnalysis(
            name="extrude_thin",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Scriptable thin extrusion",
        ),
        ToolAnalysis(
            name="cut_extrude",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Same as extrude but CutFeatureOperation",
        ),
        ToolAnalysis(
            name="loft",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Scriptable; good learning pattern",
        ),
        ToolAnalysis(
            name="sweep",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Scriptable sweep operation",
        ),
        ToolAnalysis(
            name="revolve_profile",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Requires UI selection - could be scriptable with indices",
        ),
        ToolAnalysis(
            name="boolean_operation",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Common pattern; agent should learn",
        ),
        ToolAnalysis(
            name="shell_existing_body",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Straightforward shell feature",
        ),
        ToolAnalysis(
            name="fillet_edges",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Common operation",
        ),
        ToolAnalysis(
            name="holes",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Hole feature creation",
        ),
        ToolAnalysis(
            name="create_thread",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Complex thread data query; convenient as tool",
        ),
        ToolAnalysis(
            name="circular_pattern",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Pattern feature",
        ),
        ToolAnalysis(
            name="rectangular_pattern",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Pattern feature",
        ),
        ToolAnalysis(
            name="move_last_body",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="MoveFeature with transform",
        ),
    ],
    
    # =========================================================================
    # GROUP 5: PARAMETERS - Keep for workflow
    # Quick parameter operations useful in iterative design
    # =========================================================================
    "parameters": [
        ToolAnalysis(
            name="set_parameter",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Quick param update for iterative design",
        ),
        ToolAnalysis(
            name="count_parameters",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Trivial query",
        ),
        ToolAnalysis(
            name="list_parameters",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Useful for understanding model state",
        ),
        ToolAnalysis(
            name="create_user_parameter",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Simple API call",
        ),
        ToolAnalysis(
            name="delete_user_parameter",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Simple API call",
        ),
    ],
    
    # =========================================================================
    # GROUP 6: UTILITY - Mixed
    # =========================================================================
    "utility": [
        ToolAnalysis(
            name="delete_all",
            necessity=ToolNecessity.CONVENIENCE,
            reason="Quick reset; useful but scriptable",
        ),
        ToolAnalysis(
            name="offsetplane",
            necessity=ToolNecessity.SCRIPTABLE,
            reason="Construction plane creation",
        ),
    ],
}


# =============================================================================
# Summary Functions
# =============================================================================

def get_essential_tools() -> List[str]:
    """Get list of tools that must remain."""
    result = []
    for tools in TOOL_ANALYSIS.values():
        for t in tools:
            if t.necessity == ToolNecessity.ESSENTIAL:
                result.append(t.name)
    return result


def get_convenience_tools() -> List[str]:
    """Get list of tools that are convenient but optional."""
    result = []
    for tools in TOOL_ANALYSIS.values():
        for t in tools:
            if t.necessity == ToolNecessity.CONVENIENCE:
                result.append(t.name)
    return result


def get_scriptable_tools() -> List[str]:
    """Get list of tools that should be removed (agent should script)."""
    result = []
    for tools in TOOL_ANALYSIS.values():
        for t in tools:
            if t.necessity == ToolNecessity.SCRIPTABLE:
                result.append(t.name)
    return result


def print_summary():
    """Print a summary of tool analysis."""
    essential = get_essential_tools()
    convenience = get_convenience_tools()
    scriptable = get_scriptable_tools()
    
    print("=" * 70)
    print("TOOL CATEGORIZATION SUMMARY")
    print("=" * 70)
    
    print(f"\n🔒 ESSENTIAL ({len(essential)} tools) - Must keep:")
    print("   These provide infrastructure or special capabilities")
    for name in essential:
        print(f"   • {name}")
    
    print(f"\n⚡ CONVENIENCE ({len(convenience)} tools) - Keep for efficiency:")
    print("   Useful shortcuts that save tokens vs writing scripts")
    for name in convenience:
        print(f"   • {name}")
    
    print(f"\n📜 SCRIPTABLE ({len(scriptable)} tools) - Agent should use script:")
    print("   Remove these; agent learns by writing execute_fusion_script")
    for name in scriptable:
        print(f"   • {name}")
    
    print(f"\n📊 TOTALS:")
    print(f"   Essential:   {len(essential):2d} tools")
    print(f"   Convenience: {len(convenience):2d} tools")  
    print(f"   Scriptable:  {len(scriptable):2d} tools")
    print(f"   TOTAL:       {len(essential) + len(convenience) + len(scriptable):2d} tools")
    
    print("\n💡 RECOMMENDATION:")
    print(f"   Keep {len(essential) + len(convenience)} tools")
    print(f"   Remove {len(scriptable)} tools (teach agent to script)")


if __name__ == "__main__":
    print_summary()
