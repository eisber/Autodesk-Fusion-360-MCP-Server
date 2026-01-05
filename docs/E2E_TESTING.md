# End-to-End (E2E) Testing Procedure

This document describes the comprehensive procedure for running E2E tests on the Fusion 360 MCP Server, covering all available tools and common use cases.

## Prerequisites

1. **Fusion 360** running with a design open
2. **MCP Add-In** loaded and running (HTTP server on port 5000)
3. **MCP Server** running (typically started by VS Code via `.vscode/mcp.json`)

## Quick Start

```bash
# Run unit tests (no Fusion required - uses mocks)
cd Server
python -m pytest tests/ -v

# Run live E2E tests (requires Fusion + Add-In running)
cd Server
FUSION_MCP_LIVE=1 python -m pytest tests/test_e2e.py -v
```

---

## Complete Tool Reference

### Infrastructure Tools

#### test_connection
Verify connection to Fusion 360 Add-In.
```
Tool: test_connection
Expected: {"success": true, "message": "Connection successful", "version": "1.0.0"}
```

#### get_model_state
Get current model information including bodies, sketches, and spatial relationships.
```
Tool: get_model_state
Expected:
{
  "body_count": 10,
  "sketch_count": 2,
  "bodies": [...],
  "sketches": [...],
  "spatial_summary": "...",
  "design_name": "(Unsaved)"
}
```

#### delete_all
Remove all bodies from the design.
```
Tool: delete_all
Expected: {"success": true, "task": "delete_all"}
```

#### undo
Undo the last operation.
```
Tool: undo
Expected: {"success": true}
```

---

### Scripting Tools

#### execute_fusion_script
Execute arbitrary Python code in Fusion 360 context. This is the most powerful tool.

**Available Variables:**
- `adsk`, `app`, `ui`, `design`, `rootComp` - Core Fusion objects
- `math`, `json` - Standard modules
- `XY`, `XZ`, `YZ` - Construction planes
- Helper functions: `sketch_on`, `point`, `vector`, `extrude`, `revolve`, etc.
- `progress(percent, message)` - Report progress (0-100)
- `is_cancelled()` - Check cancellation

**Simple Example:**
```python
sketch = sketch_on("XY")
sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(5, 3, 0))
box = extrude(sketch.profiles.item(0), 2)
result = "Created a 5x3x2 box"
```

**Complex Example with Progress:**
```python
progress(0, "Starting...")
# Create base
base = sketch_on("XY")
base.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 5)
extrude(base.profiles.item(0), 1)

progress(50, "Adding features...")
# Add cylinder on top
cyl = sketch_on("XY", offset=1)
cyl.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 2)
extrude(cyl.profiles.item(0), 3)

progress(100, "Done!")
result = {"bodies": 2, "description": "Base plate with cylinder"}
```

#### cancel_fusion_task
Cancel a running task by ID.
```
Tool: cancel_fusion_task
task_id: "abc12345"
```

---

### Inspection Tools

#### inspect_adsk_api
Explore Fusion 360 API documentation interactively.
```
Tool: inspect_adsk_api
path: "adsk.fusion.Sketch"
Expected: {
  "success": true,
  "path": "adsk.fusion.Sketch",
  "type": "class",
  "docstring": "Represents a sketch within a component.",
  "members": [...],
  "member_count": 65
}
```

**Common Paths:**
- `adsk` - Top-level module
- `adsk.core.Point3D` - 3D point class
- `adsk.fusion.Sketch` - Sketch class
- `adsk.fusion.ExtrudeFeatures` - Extrude operations
- `adsk.fusion.BRepBody` - Solid body class

#### get_adsk_class_info
Get detailed class documentation in docstring format.
```
Tool: get_adsk_class_info
class_path: "adsk.core.Point3D"
```

#### get_faces_info
Get information about all faces on a body.
```
Tool: get_faces_info
body_index: 0
Expected: {
  "body_name": "Body1",
  "face_count": 15,
  "faces": [
    {"index": 0, "type": "Cylinder", "area_cm2": 0.628, "centroid": [8.5, 6.5, 0.25]},
    {"index": 1, "type": "Plane", "area_cm2": 77.8, "centroid": [5.0, 4.0, 0.5]},
    ...
  ]
}
```

#### get_edges_info
Get information about all edges on a body.
```
Tool: get_edges_info
body_index: 0
Expected: {
  "body_name": "Body1",
  "edge_count": 34,
  "edges": [
    {"index": 0, "type": "Circle3D", "length_cm": 3.14, "start_point": [...], "end_point": [...]},
    {"index": 1, "type": "Line3D", "length_cm": 5.0, ...},
    ...
  ]
}
```

#### get_vertices_info
Get vertex positions on a body.
```
Tool: get_vertices_info
body_index: 0
Expected: {
  "vertex_count": 26,
  "vertices": [
    {"index": 0, "position": [0.0, 0.0, 0.0]},
    ...
  ]
}
```

---

### Measurement Tools

#### measure_volume
Measure body volume.
```
Tool: measure_volume
body_index: 0
Expected: {"volume_cm3": 38.9, "volume_mm3": 38906.0, "body_name": "Body1"}
```

#### measure_body_properties
Get comprehensive physical properties.
```
Tool: measure_body_properties
body_index: 0
Expected: {
  "volume_cm3": 38.9,
  "surface_area_cm2": 176.8,
  "bounding_box": {"min": [0,0,0], "max": [10,8,0.5], "size": [10,8,0.5]},
  "centroid": [5.0, 4.0, 0.25],
  "face_count": 15,
  "edge_count": 34,
  "vertex_count": 26
}
```

#### measure_distance
Measure distance between entities.
```
Tool: measure_distance
entity1_type: "face", entity1_index: 0
entity2_type: "face", entity2_index: 1
body1_index: 0, body2_index: 0
Expected: {
  "distance_cm": 4.6,
  "distance_mm": 46.0,
  "point1": [8.5, 6.3, 0.5],
  "point2": [8.5, 1.7, 0.5]
}
```

#### measure_angle
Measure angle between planar faces or linear edges.
```
Tool: measure_angle
entity1_type: "face", entity1_index: 0
entity2_type: "face", entity2_index: 1
Expected: {"angle_degrees": 90.0, "angle_radians": 1.5708}
```

#### measure_area
Measure area of a specific face.
```
Tool: measure_area
face_index: 0, body_index: 0
Expected: {"area_cm2": 0.628, "area_mm2": 62.8, "face_type": "Cylinder"}
```

#### measure_edge_length
Measure length of a specific edge.
```
Tool: measure_edge_length
edge_index: 0, body_index: 0
Expected: {"length_cm": 3.14, "length_mm": 31.4, "edge_type": "Circle3D"}
```

#### measure_point_to_point
Measure distance between two 3D points.
```
Tool: measure_point_to_point
point1: [0, 0, 0], point2: [5, 4, 3]
Expected: {"distance_cm": 7.07, "distance_mm": 70.7, "delta": [5, 4, 3]}
```

---

### Parameter Tools

#### list_parameters
List all model and user parameters.
```
Tool: list_parameters
Expected: [
  {"Name": "d1", "Value": "1.0", "Unit": "mm", "Expression": "10.00 mm"},
  {"Name": "wall_thickness", "Value": "0.25", "Unit": "mm", "Expression": "2.5 mm"},
  ...
]
```

#### create_user_parameter
Create a named parameter.
```
Tool: create_user_parameter
name: "wall_thickness", value: "2.5", unit: "mm", comment: "Wall thickness"
Expected: {"success": true, "parameter_name": "wall_thickness", "value": 0.25, "expression": "2.5 mm"}
```

#### set_parameter
Modify an existing parameter.
```
Tool: set_parameter
name: "wall_thickness", value: "3.0"
Expected: {"success": true, ...}
```

---

### Parametric Tools

#### check_all_interferences
Check for bounding box overlaps between bodies.
```
Tool: check_all_interferences
Expected: {
  "total_bodies": 10,
  "interference_count": 19,
  "interferences": [
    {"body1_index": 0, "body1_name": "Body1", "body2_index": 1, "body2_name": "Body2", 
     "overlap_volume_cm3": 4.0, "note": "Bounding box overlap..."}
  ],
  "method": "bounding_box_overlap"
}
```

#### list_construction_geometry
List all construction planes, axes, and points.
```
Tool: list_construction_geometry
Expected: {
  "plane_count": 10,
  "planes": [{"index": 0, "name": "Plane1"}, ...],
  "axis_count": 0,
  "point_count": 0
}
```

#### suppress_feature
Suppress or unsuppress a timeline feature.
```
Tool: suppress_feature
feature_index: 5, suppress: true
Expected: {"success": true, "feature_name": "Extrude1", "is_suppressed": true}
```

---

### Testing/Snapshot Tools

#### create_snapshot
Save current model state for later comparison.
```
Tool: create_snapshot
name: "before_changes"
Expected: {"success": true, "message": "Snapshot 'before_changes' created", ...}
```

#### list_snapshots
List all saved snapshots.
```
Tool: list_snapshots
Expected: {"snapshots": [{"name": "before_changes", "created_at": "...", ...}]}
```

#### restore_snapshot
Restore model to a previous snapshot state (uses undo).
```
Tool: restore_snapshot
name: "before_changes"
```

#### save_test / load_tests / run_tests / delete_test
Manage and run validation tests.
```
Tool: save_test
name: "check_body_count"
script: "assert_body_count(3); result = 'OK'"
description: "Verify 3 bodies exist"
```

---

### Telemetry Tools

#### configure_telemetry
Set telemetry level (off, basic, detailed).
```
Tool: configure_telemetry
level: "basic"
```

---

## Complex Model Examples

### Example 1: Mechanical Hub with Spokes
Creates a 10-body assembly with base plate, hub, spokes, pillars, and holes.

```python
progress(0, "Creating base plate...")
base = sketch_on("XY")
# Create rounded rectangle...
base_body = extrude(base.profiles.item(0), 0.5)

progress(20, "Adding central hub...")
hub = sketch_on("XY", offset=0.5)
hub.sketchCurves.sketchCircles.addByCenterRadius(point(5, 4, 0), 2)
hub_body = extrude(hub.profiles.item(0), 3)

progress(40, "Creating spokes...")
# 4 rectangular spokes connecting hub to edges

progress(60, "Adding corner pillars...")
corners = [(1.5, 1.5), (1.5, 6.5), (8.5, 1.5), (8.5, 6.5)]
for cx, cy in corners:
    pillar = sketch_on("XY", offset=0.5)
    pillar.sketchCurves.sketchCircles.addByCenterRadius(point(cx, cy, 0), 0.6)
    extrude(pillar.profiles.item(0), 2.5)

progress(80, "Creating shaft hole...")
# Cut through hub

progress(100, "Complete!")
```

### Example 2: Parametric Enclosure
```python
# Create outer shell
outer = sketch_on("XY")
outer.sketchCurves.sketchLines.addTwoPointRectangle(point(0,0,0), point(10,8,0))
shell = extrude(outer.profiles.item(0), 4)

# Shell operation to hollow out
bodies = rootComp.bRepBodies
main = bodies.item(0)
# Find top face and shell with wall thickness
```

### Example 3: Pattern Features
```python
# Create base with circular pattern of holes
base = sketch_on("XY")
base.sketchCurves.sketchCircles.addByCenterRadius(point(0,0,0), 5)
extrude(base.profiles.item(0), 1)

# Pattern of 6 holes around center
for i in range(6):
    angle = i * 60 * math.pi / 180
    x = 3 * math.cos(angle)
    y = 3 * math.sin(angle)
    hole = sketch_on("XY")
    hole.sketchCurves.sketchCircles.addByCenterRadius(point(x, y, 0), 0.3)
    # Cut through
```

---

## Test Checklist

| Category | Tool | Status | Notes |
|----------|------|--------|-------|
| **Infrastructure** | test_connection | ✅ | Basic connectivity |
| | get_model_state | ✅ | Body/sketch counts + spatial summary |
| | delete_all | ✅ | Clears all bodies |
| | undo | ✅ | Undo last operation |
| **Scripting** | execute_fusion_script | ✅ | With progress reporting |
| | cancel_fusion_task | ✅ | Cancel running tasks |
| **Inspection** | inspect_adsk_api | ✅ | API documentation |
| | get_adsk_class_info | ✅ | Class details |
| | get_faces_info | ✅ | Face geometry |
| | get_edges_info | ✅ | Edge geometry |
| | get_vertices_info | ✅ | Vertex positions |
| **Measurement** | measure_volume | ✅ | Body volume |
| | measure_body_properties | ✅ | Comprehensive properties |
| | measure_distance | ✅ | Entity distance |
| | measure_angle | ✅ | Entity angle |
| | measure_area | ✅ | Face area |
| | measure_edge_length | ✅ | Edge length |
| | measure_point_to_point | ✅ | Point distance |
| **Parameters** | list_parameters | ✅ | All parameters |
| | create_user_parameter | ✅ | Create parameter |
| | set_parameter | ✅ | Modify parameter |
| **Parametric** | check_all_interferences | ✅ | Bounding box overlap |
| | list_construction_geometry | ✅ | Planes/axes/points |
| | suppress_feature | ✅ | Timeline control |
| **Testing** | create_snapshot | ✅ | Save state |
| | list_snapshots | ✅ | List saved states |
| | restore_snapshot | ✅ | Restore state |
| | save_test / run_tests | ✅ | Validation tests |
| **Telemetry** | configure_telemetry | ✅ | Set level |

---

## Troubleshooting

### Add-In Not Responding

1. Check if Fusion 360 is running
2. Check Add-In is loaded: `Scripts and Add-Ins` > `Add-Ins` tab > `MCP`
3. Check debug log: `MCP/mcp_debug.log`
4. Try reloading the Add-In

### Module Changes Not Reflected

Python modules are cached. After editing files in `MCP/lib/`:
1. Stop the Add-In
2. Start the Add-In again

### Connection Timeouts

The MCP Server uses SSE (Server-Sent Events) for task streaming. If requests timeout:
1. Check the Add-In HTTP server is running on port 5000
2. Check no firewall blocking localhost:5000
3. Verify with: `curl http://localhost:5000/status`

### Script Execution Errors

If `execute_fusion_script` fails:
1. Check the `traceback` field in the response
2. Check `error_line` for the line number
3. Ensure you're using the helper functions (sketch_on, point, extrude, etc.)
4. Remember: 1 cm = 10 mm in Fusion units

---

## Architecture Notes

### Thread Safety

The MCP architecture uses SSE for thread-safe task correlation:

1. **POST requests** → Generate unique `task_id` → Return immediately
2. Client subscribes to `/events?task_id={task_id}`
3. Task completion routed back via SSE events

### GET vs POST Endpoints

- **GET endpoints**: Direct function calls (synchronous)
- **POST endpoints**: Task queue with SSE streaming (asynchronous)

GET endpoints like `list_parameters` and `check_all_interferences` call functions directly without using the task queue.

### Unit Conventions

- **Fusion 360 internal units**: Centimeters (cm)
- **1 cm = 10 mm**
- Always divide mm values by 10 when passing to Fusion API

---

## Running Full Test Suite

```bash
# Unit tests only (fast, uses mocks)
cd Server
python -m pytest tests/ -v

# Include live Fusion tests
cd Server
FUSION_MCP_LIVE=1 python -m pytest tests/ -v --live

# Specific test file
python -m pytest tests/test_e2e_sse.py -v

# With coverage
python -m pytest tests/ -v --cov=src --cov-report=html
```
