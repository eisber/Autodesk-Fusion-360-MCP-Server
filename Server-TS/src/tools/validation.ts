/**
 * Validation/Infrastructure tools for Fusion 360 MCP Server.
 */

import { z } from "zod";
import { createGetTool, createPostTool, ToolResult } from "./base.js";

// Tool implementations using factory functions
const _testConnection = createPostTool("test_connection", "test_connection", true);
const _getModelState = createGetTool("get_model_state");
const _undo = createPostTool("undo", "undo", true);
const _deleteAll = createPostTool("delete_everything", "delete_everything", true);
const _getFacesInfo = createGetTool("get_faces_info");

// Zod schemas for validation
export const testConnectionSchema = z.object({});

export const getModelStateSchema = z.object({});

export const undoSchema = z.object({});

export const deleteAllSchema = z.object({
  bodies: z.boolean().default(true).describe("Delete all bodies"),
  sketches: z.boolean().default(true).describe("Delete all sketches"),
  construction: z
    .boolean()
    .default(true)
    .describe("Delete construction geometry"),
  parameters: z.boolean().default(false).describe("Delete user parameters"),
});

export const getFacesInfoSchema = z.object({
  body_index: z.number().default(0).describe("Index of the body to inspect"),
});

// Exported tool functions

/**
 * Test the connection to the Fusion 360 Add-In.
 */
export async function test_connection(): Promise<ToolResult> {
  return _testConnection();
}

/**
 * Get the current state of the model including body count, sketch count, etc.
 */
export async function get_model_state(): Promise<ToolResult> {
  return _getModelState();
}

/**
 * Undo the last action in Fusion 360.
 */
export async function undo(): Promise<ToolResult> {
  return _undo();
}

/**
 * Delete all objects in the current Fusion 360 session.
 */
export async function delete_all(
  bodies: boolean = true,
  sketches: boolean = true,
  construction: boolean = true,
  parameters: boolean = false
): Promise<ToolResult> {
  return _deleteAll({ bodies, sketches, construction, parameters });
}

/**
 * Get detailed face information for a body.
 */
export async function get_faces_info(
  body_index: number = 0
): Promise<ToolResult> {
  return _getFacesInfo({ body_index });
}
