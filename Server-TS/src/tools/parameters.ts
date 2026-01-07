/**
 * Parameter tools for Fusion 360 MCP Server.
 * Tools for managing model parameters.
 */

import { z } from "zod";
import { createGetTool, createPostTool, ToolResult } from "./base.js";

// Zod schemas
export const listParametersSchema = z.object({});

export const setParameterSchema = z.object({
  name: z.string().describe("Parameter name"),
  value: z.string().describe("Parameter value or expression"),
});

export const createUserParameterSchema = z.object({
  name: z.string().describe("Parameter name (must be unique, no spaces)"),
  value: z.string().describe("Value expression (can reference other parameters)"),
  unit: z
    .string()
    .default("mm")
    .describe("Unit type: 'mm', 'cm', 'in', 'deg', 'rad', or ''"),
  comment: z.string().default("").describe("Optional description"),
});

// Tool implementations
const _listParameters = createGetTool("list_parameters");
const _setParameter = createPostTool("set_parameter", "set_parameter", true);
const _createUserParameter = createPostTool(
  "create_parameter",
  "create_parameter",
  true
);

/**
 * List all model parameters with their values and expressions.
 */
export async function list_parameters(): Promise<ToolResult> {
  return _listParameters();
}

/**
 * Set a model parameter value. Useful for parametric design iteration.
 */
export async function set_parameter(
  name: string,
  value: string
): Promise<ToolResult> {
  return _setParameter({ name, value });
}

/**
 * Create a new user parameter in the design.
 */
export async function create_user_parameter(
  name: string,
  value: string,
  unit: string = "mm",
  comment: string = ""
): Promise<ToolResult> {
  return _createUserParameter({ name, value, unit, comment });
}
