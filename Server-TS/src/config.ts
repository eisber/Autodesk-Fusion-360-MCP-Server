/**
 * Configuration for Fusion 360 MCP Server
 */

export const BASE_URL = process.env.FUSION_MCP_BASE_URL || "http://localhost:5000";
export const REQUEST_TIMEOUT = 30000; // 30 seconds
export const SSE_TIMEOUT = 300000; // 5 minutes for script execution

export const HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
};

export const ENDPOINTS = {
  // Infrastructure
  execute_script: `${BASE_URL}/execute`,
  test_connection: `${BASE_URL}/test_connection`,
  model_state: `${BASE_URL}/model_state`,
  undo: `${BASE_URL}/undo`,
  delete_everything: `${BASE_URL}/delete_everything`,
  cancel_task: `${BASE_URL}/cancel_task`,
  // Inspection
  inspect_api: `${BASE_URL}/inspect_api`,
  get_class_info: `${BASE_URL}/get_class_info`,
  faces_info: `${BASE_URL}/faces_info`,
  edges_info: `${BASE_URL}/edges_info`,
  vertices_info: `${BASE_URL}/vertices_info`,
  // Measurement
  measure_distance: `${BASE_URL}/measure_distance`,
  measure_angle: `${BASE_URL}/measure_angle`,
  measure_area: `${BASE_URL}/measure_area`,
  measure_volume: `${BASE_URL}/measure_volume`,
  measure_edge_length: `${BASE_URL}/measure_edge_length`,
  measure_body_properties: `${BASE_URL}/measure_body_properties`,
  measure_point_to_point: `${BASE_URL}/measure_point_to_point`,
  // Parameters
  list_parameters: `${BASE_URL}/list_parameters`,
  set_parameter: `${BASE_URL}/set_parameter`,
  create_parameter: `${BASE_URL}/create_parameter`,
  // Parametric
  check_interferences: `${BASE_URL}/check_interferences`,
  list_construction: `${BASE_URL}/list_construction`,
  suppress_feature: `${BASE_URL}/suppress_feature`,
  // Testing
  snapshot_create: `${BASE_URL}/snapshot_create`,
  snapshot_list: `${BASE_URL}/snapshot_list`,
  snapshot_restore: `${BASE_URL}/snapshot_restore`,
  snapshot_delete: `${BASE_URL}/snapshot_delete`,
  test_save: `${BASE_URL}/test_save`,
  test_load: `${BASE_URL}/test_load`,
  test_run: `${BASE_URL}/test_run`,
  test_delete: `${BASE_URL}/test_delete`,
} as const;

export type EndpointName = keyof typeof ENDPOINTS;
