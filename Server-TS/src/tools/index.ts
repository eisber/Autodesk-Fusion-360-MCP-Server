/**
 * Tools module exports for Fusion 360 MCP Server.
 * Re-exports all tools from submodules.
 */

// Validation/Infrastructure
export {
  test_connection,
  get_model_state,
  undo,
  delete_all,
  get_faces_info,
  testConnectionSchema,
  getModelStateSchema,
  undoSchema,
  deleteAllSchema,
  getFacesInfoSchema,
} from "./validation.js";

// Scripting
export {
  execute_fusion_script,
  cancel_fusion_task,
  executeFusionScriptSchema,
  cancelFusionTaskSchema,
} from "./scripting.js";

// Measurement
export {
  measure_distance,
  measure_angle,
  measure_area,
  measure_volume,
  measure_edge_length,
  measure_body_properties,
  measure_point_to_point,
  get_edges_info,
  get_vertices_info,
  measureDistanceSchema,
  measureAngleSchema,
  measureAreaSchema,
  measureVolumeSchema,
  measureEdgeLengthSchema,
  measureBodyPropertiesSchema,
  measurePointToPointSchema,
  getEdgesInfoSchema,
  getVerticesInfoSchema,
} from "./measurement.js";

// Inspection
export {
  inspect_adsk_api,
  get_adsk_class_info,
  inspectAdskApiSchema,
  getAdskClassInfoSchema,
} from "./inspection.js";

// Parameters
export {
  list_parameters,
  set_parameter,
  create_user_parameter,
  listParametersSchema,
  setParameterSchema,
  createUserParameterSchema,
} from "./parameters.js";

// Parametric
export {
  check_all_interferences,
  list_construction_geometry,
  suppress_feature,
  checkAllInterferencesSchema,
  listConstructionGeometrySchema,
  suppressFeatureSchema,
} from "./parametric.js";

// Testing
export {
  create_snapshot,
  list_snapshots,
  restore_snapshot,
  delete_snapshot,
  save_test,
  load_tests,
  run_tests,
  delete_test,
  createSnapshotSchema,
  listSnapshotsSchema,
  restoreSnapshotSchema,
  deleteSnapshotSchema,
  saveTestSchema,
  loadTestsSchema,
  runTestsSchema,
  deleteTestSchema,
} from "./testing.js";

// Re-export types
export type { ToolResult } from "./base.js";
