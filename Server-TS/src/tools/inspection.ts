/**
 * Inspection tools for Fusion 360 MCP Server.
 * Tools for inspecting the Fusion 360 API and model geometry.
 */

import { z } from "zod";
import { createPostTool, ToolResult } from "./base.js";

// Zod schemas
export const inspectAdskApiSchema = z.object({
  path: z
    .string()
    .default("adsk.fusion")
    .describe("Dot-separated path to inspect (e.g., 'adsk.fusion.Sketch')"),
});

export const getAdskClassInfoSchema = z.object({
  class_path: z
    .string()
    .describe("Full path to the class (e.g., 'adsk.fusion.ExtrudeFeatures')"),
});

// Tool implementations
const _inspectAdskApi = createPostTool("inspect_api", "inspect_api", true);
const _getAdskClassInfo = createPostTool("get_class_info", "get_class_info", true);

/**
 * Inspect the Autodesk Fusion 360 API to discover classes, methods, properties,
 * and their signatures/docstrings.
 *
 * Use this to learn about the API before writing scripts.
 *
 * @param path - Dot-separated path to inspect. Examples:
 *   - "adsk" - Top-level module (lists submodules: core, fusion, cam)
 *   - "adsk.fusion" - Fusion module (lists all classes)
 *   - "adsk.fusion.Sketch" - Specific class (shows methods, properties, docstrings)
 *   - "adsk.core.Point3D.create" - Specific method (shows signature)
 */
export async function inspect_adsk_api(
  path: string = "adsk.fusion"
): Promise<ToolResult> {
  return _inspectAdskApi({ path });
}

/**
 * Get detailed documentation for a specific adsk class in docstring format.
 *
 * @param class_path - Full path to the class, e.g., "adsk.fusion.Sketch",
 *   "adsk.core.Point3D", "adsk.fusion.ExtrudeFeatures"
 */
export async function get_adsk_class_info(
  class_path: string
): Promise<ToolResult> {
  return _getAdskClassInfo({ class_path });
}
