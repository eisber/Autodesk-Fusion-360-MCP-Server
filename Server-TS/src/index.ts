/**
 * Fusion 360 MCP Server - TypeScript Entry Point
 *
 * This MCP server provides tools for interacting with Autodesk Fusion 360.
 * It communicates with a Fusion 360 Add-In via HTTP/SSE.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";

import { SYSTEM_INSTRUCTIONS } from "./instructions.js";
import { PROMPTS } from "./prompts.js";
import { getTelemetry } from "./telemetry.js";
import * as tools from "./tools/index.js";

// =============================================================================
// Tool Definitions for MCP
// =============================================================================

export const TOOL_DEFINITIONS: Tool[] = [
  // Infrastructure
  {
    name: "test_connection",
    description: "Test the connection to the Fusion 360 Add-In server.",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "get_model_state",
    description:
      "Get the current state of the Fusion 360 model.\n\nReturns:\n- body_count: Number of bodies in the model\n- sketch_count: Number of sketches\n- bodies: List with details for each body (name, volume, bounding box)\n- sketches: List with details for each sketch (name, profile count)\n- design_name: Name of the active design",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "undo",
    description: "Undo the last action.",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "delete_all",
    description: "Delete all objects in the current Fusion 360 session.",
    inputSchema: {
      type: "object",
      properties: {
        bodies: {
          type: "boolean",
          default: true,
          description: "Delete all bodies (default: true)",
        },
        sketches: {
          type: "boolean",
          default: true,
          description: "Delete all sketches (default: true)",
        },
        construction: {
          type: "boolean",
          default: true,
          description: "Delete non-origin construction geometry (default: true)",
        },
        parameters: {
          type: "boolean",
          default: false,
          description: "Delete user parameters (default: false)",
        },
      },
      required: [],
    },
  },

  // Scripting (most powerful)
  {
    name: "execute_fusion_script",
    description: `Execute a Python script directly in Fusion 360.
This is the most powerful tool - you can execute arbitrary Fusion 360 API code.

Available variables in the script:
- adsk: The Autodesk module
- app: The Fusion 360 Application
- ui: The User Interface
- design: The active Design
- rootComp: The Root Component
- math: The math module
- json: The json module
- progress(percent, message): Report progress (0-100)
- is_cancelled(): Check if task was cancelled

Example Script:
\`\`\`python
progress(0, "Starting...")

# Create a box
sketches = rootComp.sketches
xyPlane = rootComp.xYConstructionPlane
sketch = sketches.add(xyPlane)
sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(5, 3, 0)
)

progress(50, "Extruding...")

# Extrude
profile = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
ext = extrudes.addSimple(
    profile,
    adsk.core.ValueInput.createByReal(2),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
)

progress(100, "Done!")
result = f"Created body: {ext.bodies.item(0).name}"
\`\`\`

Set a variable 'result' to return a value.

Returns:
- success: True/False
- return_value: Value of the 'result' variable (if set)
- stdout: Print outputs
- stderr: Error outputs
- error: Error message (if failed)
- error_type: Type of error (SyntaxError, RuntimeError, etc.)
- error_line: Line number of error
- traceback: Full traceback
- model_state: Model state after execution`,
    inputSchema: {
      type: "object",
      properties: {
        script: { type: "string", description: "Python script to execute" },
        timeout: {
          type: "number",
          default: 300,
          description: "Timeout in seconds (default: 300)",
        },
      },
      required: ["script"],
    },
  },
  {
    name: "cancel_fusion_task",
    description: `Cancel a running task in Fusion 360.

Use this to stop long-running operations like complex scripts or exports.

Args:
    task_id: The ID of the task to cancel (returned when task was submitted)

Returns:
    - success: True if task was cancelled
    - error: Error message if cancellation failed`,
    inputSchema: {
      type: "object",
      properties: {
        task_id: {
          type: "string",
          description: "The ID of the task to cancel",
        },
      },
      required: ["task_id"],
    },
  },

  // Inspection
  {
    name: "inspect_adsk_api",
    description: `Inspect the Autodesk Fusion 360 API to discover classes, methods, properties,
and their signatures/docstrings. Use this to learn about the API before
writing scripts for execute_fusion_script.

Args:
    path: Dot-separated path to inspect. Examples:
        - "adsk" - Top-level module (lists submodules: core, fusion, cam)
        - "adsk.fusion" - Fusion module (lists all classes)
        - "adsk.fusion.Sketch" - Specific class (shows methods, properties, docstrings)
        - "adsk.fusion.Sketch.sketchCurves" - Specific property
        - "adsk.core.Point3D.create" - Specific method (shows signature)

Returns:
    Dictionary with:
    - path: The inspected path
    - type: "module", "class", "method", "property", etc.
    - docstring: Documentation string if available
    - signature: Method signature if applicable
    - members: List of child members with their types (for modules/classes)
    - example: Usage example if available`,
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          default: "adsk.fusion",
          description: "Dot-separated path to inspect",
        },
      },
      required: [],
    },
  },
  {
    name: "get_adsk_class_info",
    description: `Get detailed documentation for a specific adsk class in docstring format,
suitable for understanding how to use the class in scripts.

Args:
    class_path: Full path to the class, e.g., "adsk.fusion.Sketch",
        "adsk.core.Point3D", "adsk.fusion.ExtrudeFeatures"

Returns:
    Dictionary containing:
    - class_name: Name of the class
    - docstring: Formatted docstring with class overview, methods, and properties
    - methods: List of methods with signatures and docstrings
    - properties: List of properties with types and docstrings
    - example: Usage example if extractable`,
    inputSchema: {
      type: "object",
      properties: {
        class_path: {
          type: "string",
          description: "Full path to the class (e.g., 'adsk.fusion.ExtrudeFeatures')",
        },
      },
      required: ["class_path"],
    },
  },
  {
    name: "get_faces_info",
    description: `Get detailed face information for a body.

Args:
    body_index: Index of the body to inspect (default: 0)

Returns:
    Dictionary with:
    - face_count: Number of faces
    - faces: List with details for each face (index, type, area, centroid)`,
    inputSchema: {
      type: "object",
      properties: {
        body_index: {
          type: "number",
          default: 0,
          description: "Index of the body to inspect",
        },
      },
      required: [],
    },
  },
  {
    name: "get_edges_info",
    description: `Get detailed edge information for a body.

Args:
    body_index: Index of the body to inspect (default: 0)

Returns:
    Dictionary with:
    - edge_count: Number of edges
    - edges: List with details for each edge (index, type, length, start_point, end_point)`,
    inputSchema: {
      type: "object",
      properties: {
        body_index: {
          type: "number",
          default: 0,
          description: "Index of the body to inspect",
        },
      },
      required: [],
    },
  },
  {
    name: "get_vertices_info",
    description: `Get detailed vertex information for a body.

Args:
    body_index: Index of the body to inspect (default: 0)

Returns:
    Dictionary with:
    - vertex_count: Number of vertices
    - vertices: List with details for each vertex (index, position [x,y,z])`,
    inputSchema: {
      type: "object",
      properties: {
        body_index: {
          type: "number",
          default: 0,
          description: "Index of the body to inspect",
        },
      },
      required: [],
    },
  },

  // Measurement
  {
    name: "measure_distance",
    description: `Measure the minimum distance between two entities.

Args:
    entity1_type: Type of first entity ("face", "edge", "vertex", "body", "point")
    entity1_index: Index of first entity (for face/edge/vertex within the body)
    entity2_type: Type of second entity ("face", "edge", "vertex", "body", "point")
    entity2_index: Index of second entity (for face/edge/vertex within the body)
    body1_index: Index of the body containing entity1 (default: 0)
    body2_index: Index of the body containing entity2 (default: 0)

Returns:
    Dictionary with:
    - distance: Minimum distance in cm
    - point1: [x, y, z] closest point on entity1
    - point2: [x, y, z] closest point on entity2`,
    inputSchema: {
      type: "object",
      properties: {
        entity1_type: {
          type: "string",
          description: "Type: 'face', 'edge', 'vertex', or 'body'",
        },
        entity1_index: { type: "number", description: "Index of first entity" },
        entity2_type: {
          type: "string",
          description: "Type: 'face', 'edge', 'vertex', or 'body'",
        },
        entity2_index: { type: "number", description: "Index of second entity" },
        body1_index: {
          type: "number",
          default: 0,
          description: "Body index for first entity",
        },
        body2_index: {
          type: "number",
          default: 0,
          description: "Body index for second entity",
        },
      },
      required: ["entity1_type", "entity1_index", "entity2_type", "entity2_index"],
    },
  },
  {
    name: "measure_angle",
    description: `Measure the angle between two planar faces or linear edges.

Args:
    entity1_type: Type of first entity ("face" or "edge")
    entity1_index: Index of first entity
    entity2_type: Type of second entity ("face" or "edge")
    entity2_index: Index of second entity
    body1_index: Index of the body containing entity1 (default: 0)
    body2_index: Index of the body containing entity2 (default: 0)

Returns:
    Dictionary with:
    - angle_degrees: Angle in degrees
    - angle_radians: Angle in radians`,
    inputSchema: {
      type: "object",
      properties: {
        entity1_type: { type: "string", description: "Type: 'face' or 'edge'" },
        entity1_index: { type: "number", description: "Index of first entity" },
        entity2_type: { type: "string", description: "Type: 'face' or 'edge'" },
        entity2_index: { type: "number", description: "Index of second entity" },
        body1_index: {
          type: "number",
          default: 0,
          description: "Body index for first entity",
        },
        body2_index: {
          type: "number",
          default: 0,
          description: "Body index for second entity",
        },
      },
      required: ["entity1_type", "entity1_index", "entity2_type", "entity2_index"],
    },
  },
  {
    name: "measure_area",
    description: `Measure the area of a specific face.

Args:
    face_index: Index of the face to measure
    body_index: Index of the body containing the face (default: 0)

Returns:
    Dictionary with:
    - area_cm2: Area in square centimeters
    - area_mm2: Area in square millimeters
    - face_type: Type of face (Plane, Cylinder, etc.)`,
    inputSchema: {
      type: "object",
      properties: {
        face_index: { type: "number", description: "Index of the face" },
        body_index: {
          type: "number",
          default: 0,
          description: "Index of the body",
        },
      },
      required: ["face_index"],
    },
  },
  {
    name: "measure_volume",
    description: `Measure the volume of a body.

Args:
    body_index: Index of the body to measure (default: 0)

Returns:
    Dictionary with:
    - volume_cm3: Volume in cubic centimeters
    - volume_mm3: Volume in cubic millimeters
    - body_name: Name of the body`,
    inputSchema: {
      type: "object",
      properties: {
        body_index: {
          type: "number",
          default: 0,
          description: "Index of the body",
        },
      },
      required: [],
    },
  },
  {
    name: "measure_edge_length",
    description: `Measure the length of a specific edge.

Args:
    edge_index: Index of the edge to measure
    body_index: Index of the body containing the edge (default: 0)

Returns:
    Dictionary with:
    - length_cm: Length in centimeters
    - length_mm: Length in millimeters
    - edge_type: Type of edge (Line, Arc, Circle, etc.)
    - start_point: [x, y, z] start point
    - end_point: [x, y, z] end point`,
    inputSchema: {
      type: "object",
      properties: {
        edge_index: { type: "number", description: "Index of the edge" },
        body_index: {
          type: "number",
          default: 0,
          description: "Index of the body",
        },
      },
      required: ["edge_index"],
    },
  },
  {
    name: "measure_body_properties",
    description: `Get comprehensive physical properties of a body.

Args:
    body_index: Index of the body to measure (default: 0)

Returns:
    Dictionary with:
    - volume_cm3: Volume in cubic centimeters
    - surface_area_cm2: Total surface area in square centimeters
    - bounding_box: {min: [x,y,z], max: [x,y,z], size: [dx,dy,dz]}
    - centroid: [x, y, z] center of mass
    - face_count: Number of faces
    - edge_count: Number of edges
    - vertex_count: Number of vertices
    - body_name: Name of the body`,
    inputSchema: {
      type: "object",
      properties: {
        body_index: {
          type: "number",
          default: 0,
          description: "Index of the body",
        },
      },
      required: [],
    },
  },
  {
    name: "measure_point_to_point",
    description: `Measure the distance between two specific 3D points.

Args:
    point1: [x, y, z] coordinates of first point (in cm)
    point2: [x, y, z] coordinates of second point (in cm)

Returns:
    Dictionary with:
    - distance_cm: Distance in centimeters
    - distance_mm: Distance in millimeters
    - delta: [dx, dy, dz] difference vector`,
    inputSchema: {
      type: "object",
      properties: {
        point1: {
          type: "array",
          items: { type: "number" },
          description: "[x, y, z] of first point",
        },
        point2: {
          type: "array",
          items: { type: "number" },
          description: "[x, y, z] of second point",
        },
      },
      required: ["point1", "point2"],
    },
  },

  // Parameters
  {
    name: "list_parameters",
    description: "List all parameters in the current model.",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "set_parameter",
    description: `Change the value of a parameter.

Args:
    name: Parameter name
    value: New value expression`,
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Parameter name" },
        value: { type: "string", description: "New value expression" },
      },
      required: ["name", "value"],
    },
  },
  {
    name: "create_user_parameter",
    description: `Create a new user parameter in the design.

Args:
    name: Parameter name (must be unique, no spaces)
    value: Value expression (can reference other parameters, e.g., "width * 2")
    unit: Unit type ("mm", "cm", "in", "deg", "rad", or "" for unitless)
    comment: Optional description of the parameter

Returns:
    Dictionary with:
    - success: True/False
    - parameter_name: Name of created parameter
    - value: Evaluated value
    - expression: The expression used`,
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Parameter name" },
        value: { type: "string", description: "Value expression" },
        unit: {
          type: "string",
          default: "mm",
          description: "Unit type: 'mm', 'cm', 'in', 'deg', 'rad', or ''",
        },
        comment: { type: "string", default: "", description: "Optional description" },
      },
      required: ["name", "value"],
    },
  },

  // Parametric
  {
    name: "check_all_interferences",
    description: `Check all bodies for potential interference using bounding box overlap.

Note: This uses bounding box intersection as an approximation since Fusion 360 API
doesn't expose a direct interference analysis feature. Bodies with overlapping
bounding boxes may or may not actually intersect geometrically.

Returns:
    - total_bodies: Number of bodies checked
    - interference_count: Number of potentially interfering pairs
    - interferences: List of body pairs with overlapping bounding boxes
    - method: "bounding_box_overlap"`,
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "list_construction_geometry",
    description: `List all construction geometry in the design.

Returns:
    Dictionary with:
    - planes: List of construction planes with name and type
    - axes: List of construction axes with name and direction
    - points: List of construction points with name and position`,
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "suppress_feature",
    description: `Suppress or unsuppress a feature in the timeline.

Args:
    feature_index: Index of the feature
    suppress: True to suppress, False to unsuppress

Returns:
    Dictionary with:
    - success: True/False
    - feature_name: Name of the affected feature
    - is_suppressed: Current suppression state`,
    inputSchema: {
      type: "object",
      properties: {
        feature_index: { type: "number", description: "Index of the feature" },
        suppress: {
          type: "boolean",
          default: true,
          description: "True to suppress, false to unsuppress",
        },
      },
      required: ["feature_index"],
    },
  },

  // Testing/Snapshots
  {
    name: "create_snapshot",
    description: `Create a snapshot of the current model state.

Snapshots capture body_count, sketch_count, and body details (volumes, bounding boxes).
Use this BEFORE making changes to enable rollback verification.

Args:
    name: Name for the snapshot (alphanumeric and underscores recommended)

Returns:
    Dictionary with snapshot details and file path`,
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Name for the snapshot" },
      },
      required: ["name"],
    },
  },
  {
    name: "list_snapshots",
    description: `List all snapshots for the current Fusion project.

Returns:
    Dictionary with list of snapshot metadata`,
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "restore_snapshot",
    description: `Attempt to restore model to a previous snapshot state using undo.

**WARNING**: Fusion's undo is sequential - this will undo operations one by one
until the model state matches the snapshot (body_count and sketch_count).

- Cannot skip forward in history
- Cannot restore if snapshot state requires more bodies/sketches than current
- May not perfectly restore all geometry details, only counts are verified

Args:
    name: Name of the snapshot to restore
    max_undo_steps: Maximum undo operations to attempt (default 50)

Returns:
    Dictionary with:
    - success: True if state was restored
    - undo_count: Number of undo operations performed
    - warning: Any warnings about limitations
    - current_state: Model state after restore attempt`,
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Name of the snapshot to restore" },
        max_undo_steps: {
          type: "number",
          default: 50,
          description: "Maximum undo operations to attempt",
        },
      },
      required: ["name"],
    },
  },
  {
    name: "delete_snapshot",
    description: `Delete a snapshot by name.

Args:
    name: Name of the snapshot to delete

Returns:
    Dictionary with success status`,
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Name of the snapshot to delete" },
      },
      required: ["name"],
    },
  },
  {
    name: "save_test",
    description: `Save a validation test to disk for the current Fusion project.

Tests are saved to: ~/Desktop/Fusion_Tests/{project_name}/{name}.json

The script can use assertion helpers available in execute_fusion_script:
- assert_body_count(expected): Verify number of bodies
- assert_sketch_count(expected): Verify number of sketches
- assert_volume(body_index, expected_cm3, tolerance=0.1): Verify body volume
- assert_bounding_box(body_index, min_point, max_point, tolerance=0.1): Verify bounds

Example script:
    '''
    # Create a box and verify
    assert_body_count(1)
    body = rootComp.bRepBodies.item(0)
    assert body.volume > 0, "Body should have positive volume"
    result = "Test passed"
    '''

Args:
    name: Test name (used as filename, alphanumeric and underscores recommended)
    script: Python script with assertions to execute in Fusion
    description: Human-readable description of what the test validates

Returns:
    Dictionary with save status and file path`,
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Test name" },
        script: { type: "string", description: "Python script with assertions" },
        description: {
          type: "string",
          default: "",
          description: "Description of what the test validates",
        },
      },
      required: ["name", "script"],
    },
  },
  {
    name: "load_tests",
    description: `List all saved tests for the current Fusion project.

Returns:
    Dictionary with:
    - success: True/False
    - project_name: Current project name
    - tests: List of test metadata (name, description, created_at)
    - test_dir: Path to test directory`,
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "run_tests",
    description: `Run validation tests for the current Fusion project.

If name is provided, runs that specific test.
If name is omitted, runs ALL saved tests for the project.

Args:
    name: Name of specific test to run (optional, omit to run all)

Returns:
    If running single test:
    - success: True if test passed, False if failed or error
    - test_name: Name of the test
    - passed: True/False based on script execution
    - return_value: Value of 'result' variable from script
    - stdout: Print outputs from script
    - error: Error message if test failed
    - execution_time_ms: How long the test took
    - model_state: Model state after test execution

    If running all tests:
    - success: True if all tests passed
    - project_name: Current project name
    - total: Total number of tests
    - passed: Number of tests that passed
    - failed: Number of tests that failed
    - results: List of individual test results
    - total_execution_time_ms: Total time for all tests`,
    inputSchema: {
      type: "object",
      properties: {
        name: {
          type: "string",
          description: "Name of specific test to run (omit to run all)",
        },
      },
      required: [],
    },
  },
  {
    name: "delete_test",
    description: `Delete a saved test by name.

Args:
    name: Name of the test to delete

Returns:
    Dictionary with success status`,
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Name of the test to delete" },
      },
      required: ["name"],
    },
  },
];

// =============================================================================
// Tool Handler Mapping
// =============================================================================

type ToolHandler = (args: Record<string, unknown>) => Promise<unknown>;

export const toolHandlers: Record<string, ToolHandler> = {
  // Infrastructure
  test_connection: async () => tools.test_connection(),
  get_model_state: async () => tools.get_model_state(),
  undo: async () => tools.undo(),
  delete_all: async (args) =>
    tools.delete_all(
      (args.bodies as boolean) ?? true,
      (args.sketches as boolean) ?? true,
      (args.construction as boolean) ?? true,
      (args.parameters as boolean) ?? false
    ),

  // Scripting
  execute_fusion_script: async (args) =>
    tools.execute_fusion_script(
      args.script as string,
      (args.timeout as number) ?? 300
    ),
  cancel_fusion_task: async (args) =>
    tools.cancel_fusion_task(args.task_id as string),

  // Inspection
  inspect_adsk_api: async (args) =>
    tools.inspect_adsk_api((args.path as string) ?? "adsk.fusion"),
  get_adsk_class_info: async (args) =>
    tools.get_adsk_class_info(args.class_path as string),
  get_faces_info: async (args) =>
    tools.get_faces_info((args.body_index as number) ?? 0),
  get_edges_info: async (args) =>
    tools.get_edges_info((args.body_index as number) ?? 0),
  get_vertices_info: async (args) =>
    tools.get_vertices_info((args.body_index as number) ?? 0),

  // Measurement
  measure_distance: async (args) =>
    tools.measure_distance(
      args.entity1_type as string,
      args.entity1_index as number,
      args.entity2_type as string,
      args.entity2_index as number,
      (args.body1_index as number) ?? 0,
      (args.body2_index as number) ?? 0
    ),
  measure_angle: async (args) =>
    tools.measure_angle(
      args.entity1_type as string,
      args.entity1_index as number,
      args.entity2_type as string,
      args.entity2_index as number,
      (args.body1_index as number) ?? 0,
      (args.body2_index as number) ?? 0
    ),
  measure_area: async (args) =>
    tools.measure_area(
      args.face_index as number,
      (args.body_index as number) ?? 0
    ),
  measure_volume: async (args) =>
    tools.measure_volume((args.body_index as number) ?? 0),
  measure_edge_length: async (args) =>
    tools.measure_edge_length(
      args.edge_index as number,
      (args.body_index as number) ?? 0
    ),
  measure_body_properties: async (args) =>
    tools.measure_body_properties((args.body_index as number) ?? 0),
  measure_point_to_point: async (args) =>
    tools.measure_point_to_point(
      args.point1 as number[],
      args.point2 as number[]
    ),

  // Parameters
  list_parameters: async () => tools.list_parameters(),
  set_parameter: async (args) =>
    tools.set_parameter(args.name as string, args.value as string),
  create_user_parameter: async (args) =>
    tools.create_user_parameter(
      args.name as string,
      args.value as string,
      (args.unit as string) ?? "mm",
      (args.comment as string) ?? ""
    ),

  // Parametric
  check_all_interferences: async () => tools.check_all_interferences(),
  list_construction_geometry: async () => tools.list_construction_geometry(),
  suppress_feature: async (args) =>
    tools.suppress_feature(
      args.feature_index as number,
      (args.suppress as boolean) ?? true
    ),

  // Testing
  create_snapshot: async (args) => tools.create_snapshot(args.name as string),
  list_snapshots: async () => tools.list_snapshots(),
  restore_snapshot: async (args) =>
    tools.restore_snapshot(
      args.name as string,
      (args.max_undo_steps as number) ?? 50
    ),
  delete_snapshot: async (args) => tools.delete_snapshot(args.name as string),
  save_test: async (args) =>
    tools.save_test(
      args.name as string,
      args.script as string,
      (args.description as string) ?? ""
    ),
  load_tests: async () => tools.load_tests(),
  run_tests: async (args) => tools.run_tests(args.name as string | undefined),
  delete_test: async (args) => tools.delete_test(args.name as string),
};

// =============================================================================
// Main Server Setup
// =============================================================================

const TELEMETRY_WARNING = `
================================================================================
                          TELEMETRY NOTICE
================================================================================
  This is an open source project maintained by volunteers. Telemetry helps us:

    WHY we collect data:
    - Understand which tools are most useful (to prioritize development)
    - Find and fix bugs faster (error tracking)
    - Know if the server is actually being used (motivation to keep improving!)

    WHAT we collect:
    - Tool names and success/failure rates
    - Error types and sanitized messages
    - Session duration and tool call counts
    - Platform info (OS, Node version)

    WHAT we DON'T collect:
    - Your Fusion 360 models or designs
    - File paths or script contents  
    - Any personal or identifiable information

    HOW we use it:
    - Analytics via PostHog (privacy-focused, open source)
    - Data is anonymous and aggregated
    - Helps us write better documentation for common errors

  To opt out: set FUSION_MCP_TELEMETRY=off environment variable
  We respect your choice, but hope you'll help us improve! 
================================================================================
`;

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const serverType = args.includes("--server_type=stdio") ? "stdio" : "sse";

  const telemetry = getTelemetry();

  // Show telemetry warning if enabled (only for non-stdio to avoid protocol issues)
  if (telemetry.enabled && serverType !== "stdio") {
    console.error(TELEMETRY_WARNING);
  }

  telemetry.trackSessionStart();

  // Handle graceful shutdown
  process.on("exit", () => telemetry.trackSessionEnd());
  process.on("SIGINT", () => {
    telemetry.trackSessionEnd();
    process.exit(0);
  });
  process.on("SIGTERM", () => {
    telemetry.trackSessionEnd();
    process.exit(0);
  });

  const server = new Server(
    {
      name: "Fusion360",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
        prompts: {},
      },
    }
  );

  // List tools handler
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: TOOL_DEFINITIONS,
  }));

  // Call tool handler
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: toolArgs } = request.params;
    const handler = toolHandlers[name];

    if (!handler) {
      return {
        content: [{ type: "text", text: `Unknown tool: ${name}` }],
        isError: true,
      };
    }

    try {
      const result = await handler(toolArgs || {});
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${(error as Error).message}` }],
        isError: true,
      };
    }
  });

  // List prompts handler
  server.setRequestHandler(ListPromptsRequestSchema, async () => ({
    prompts: Object.keys(PROMPTS).map((name) => ({
      name,
      description: `Create a ${name} in Fusion 360`,
    })),
  }));

  // Get prompt handler
  server.setRequestHandler(GetPromptRequestSchema, async (request) => {
    const { name } = request.params;
    const content = PROMPTS[name];

    if (!content) {
      throw new Error(`Unknown prompt: ${name}`);
    }

    return {
      messages: [{ role: "user", content: { type: "text", text: content } }],
    };
  });

  // Start server with stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error(`Fusion 360 MCP Server (TypeScript) running on ${serverType}`);
  console.error(`Instructions loaded: ${SYSTEM_INSTRUCTIONS.length} chars`);
  console.error(`Tools registered: ${TOOL_DEFINITIONS.length}`);
  console.error(`Prompts registered: ${Object.keys(PROMPTS).length}`);
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
