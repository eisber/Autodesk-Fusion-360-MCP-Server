/**
 * Scripting tools for Fusion 360 MCP Server.
 * Contains functions for executing arbitrary Python scripts in Fusion 360.
 */

import { z } from "zod";
import { ENDPOINTS } from "../config.js";
import {
  submitTaskAndWait,
  cancelTask as sseCancelTask,
  ProgressCallback,
} from "../sse-client.js";
import { getTelemetry } from "../telemetry.js";
import { ToolResult } from "./base.js";

// Zod schemas
export const executeFusionScriptSchema = z.object({
  script: z.string().describe("Python script to execute in Fusion 360"),
  timeout: z.number().default(300).describe("Timeout in seconds"),
});

export const cancelFusionTaskSchema = z.object({
  task_id: z.string().describe("The ID of the task to cancel"),
});

/**
 * Execute a Python script directly in Fusion 360.
 * This is the most powerful tool - you can execute arbitrary Fusion 360 API code.
 *
 * Available variables in the script:
 * - adsk: The Autodesk module
 * - app: The Fusion 360 Application
 * - ui: The User Interface
 * - design: The active Design
 * - rootComp: The Root Component
 * - math: The math module
 * - json: The json module
 * - progress(percent, message): Report progress (0-100)
 * - is_cancelled(): Check if task was cancelled
 *
 * Set a variable 'result' to return a value.
 */
export async function execute_fusion_script(
  script: string,
  timeout: number = 300,
  onProgress?: ProgressCallback
): Promise<ToolResult> {
  const telemetry = getTelemetry();
  const startTime = Date.now();

  try {
    const endpoint = ENDPOINTS.execute_script;
    const result = (await submitTaskAndWait(
      endpoint,
      { command: "execute_script", script },
      timeout * 1000,
      onProgress
    )) as ToolResult;

    telemetry.trackToolCall({
      toolName: "execute_fusion_script",
      success: result.success !== false,
      durationMs: Date.now() - startTime,
      parameters: { script_length: script.length, timeout },
    });

    return result;
  } catch (error) {
    telemetry.trackToolCall({
      toolName: "execute_fusion_script",
      success: false,
      durationMs: Date.now() - startTime,
      errorType: (error as Error).name,
      errorMessage: (error as Error).message,
    });

    return {
      success: false,
      error: (error as Error).message,
    };
  }
}

/**
 * Cancel a running task in Fusion 360.
 */
export async function cancel_fusion_task(task_id: string): Promise<ToolResult> {
  try {
    const result = await sseCancelTask(task_id);
    return result as ToolResult;
  } catch (error) {
    return {
      success: false,
      error: (error as Error).message,
    };
  }
}
