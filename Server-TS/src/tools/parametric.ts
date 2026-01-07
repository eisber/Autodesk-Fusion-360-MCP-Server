/**
 * Parametric tools for Fusion 360 MCP Server.
 * Tools for parametric modeling operations.
 */

import { z } from "zod";
import { createGetTool, createPostTool, ToolResult } from "./base.js";

// Zod schemas
export const checkAllInterferencesSchema = z.object({});

export const listConstructionGeometrySchema = z.object({});

export const suppressFeatureSchema = z.object({
  feature_index: z.number().describe("Index of the feature"),
  suppress: z.boolean().default(true).describe("True to suppress, false to unsuppress"),
});

// Tool implementations
const _checkAllInterferences = createGetTool("check_all_interferences");
const _listConstructionGeometry = createGetTool("list_construction_geometry");
const _suppressFeature = createPostTool(
  "suppress_feature",
  "suppress_feature",
  true
);

/**
 * Check all bodies for potential interference using bounding box overlap.
 *
 * Note: This uses bounding box intersection as an approximation since Fusion 360 API
 * doesn't expose a direct interference analysis feature. Bodies with overlapping
 * bounding boxes may or may not actually intersect geometrically.
 */
export async function check_all_interferences(): Promise<ToolResult> {
  return _checkAllInterferences();
}

/**
 * List all construction geometry in the design.
 *
 * Returns:
 * - planes: List of construction planes with name and type
 * - axes: List of construction axes with name and direction
 * - points: List of construction points with name and position
 */
export async function list_construction_geometry(): Promise<ToolResult> {
  return _listConstructionGeometry();
}

/**
 * Suppress or unsuppress a feature in the timeline.
 */
export async function suppress_feature(
  feature_index: number,
  suppress: boolean = true
): Promise<ToolResult> {
  return _suppressFeature({ feature_index, suppress });
}
