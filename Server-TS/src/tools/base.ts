/**
 * Base utilities for Fusion 360 tool functions.
 * Provides factory functions for creating HTTP-based tools.
 */

import { BASE_URL, REQUEST_TIMEOUT } from "../config.js";
import {
  submitTaskAndWait,
  httpGet,
  httpPost,
  ProgressCallback,
} from "../sse-client.js";
import { getTelemetry, captureException } from "../telemetry.js";

export interface ToolResult {
  success: boolean;
  error?: string;
  [key: string]: unknown;
}

/**
 * Create a tool that makes an HTTP GET request.
 */
export function createGetTool(
  endpoint: string
): (params?: Record<string, unknown>) => Promise<ToolResult> {
  const url = `${BASE_URL}/${endpoint}`;

  return async (params?: Record<string, unknown>): Promise<ToolResult> => {
    const telemetry = getTelemetry();
    const startTime = Date.now();

    try {
      let requestUrl = url;
      if (params && Object.keys(params).length > 0) {
        const searchParams = new URLSearchParams();
        for (const [k, v] of Object.entries(params)) {
          searchParams.append(k, String(v));
        }
        requestUrl = `${url}?${searchParams.toString()}`;
      }

      const result = (await httpGet(requestUrl, REQUEST_TIMEOUT)) as ToolResult;

      telemetry.trackToolCall({
        toolName: endpoint,
        success: result.success !== false,
        durationMs: Date.now() - startTime,
        parameters: params,
      });

      return result;
    } catch (error) {
      telemetry.trackToolCall({
        toolName: endpoint,
        success: false,
        durationMs: Date.now() - startTime,
        errorType: (error as Error).name,
        errorMessage: (error as Error).message,
        parameters: params,
      });
      captureException(error as Error, { tool_name: endpoint });
      return { success: false, error: (error as Error).message };
    }
  };
}

/**
 * Create a tool that makes an HTTP POST request with SSE.
 */
export function createPostTool(
  endpoint: string,
  command?: string,
  useSSE: boolean = true,
  timeout: number = 300000
): (
  params?: Record<string, unknown>,
  onProgress?: ProgressCallback
) => Promise<ToolResult> {
  const url = `${BASE_URL}/${endpoint}`;
  const cmd = command || endpoint;

  return async (
    params?: Record<string, unknown>,
    onProgress?: ProgressCallback
  ): Promise<ToolResult> => {
    const telemetry = getTelemetry();
    const startTime = Date.now();

    try {
      const requestData = { command: cmd, ...params };
      let result: ToolResult;

      if (useSSE) {
        result = (await submitTaskAndWait(
          url,
          requestData,
          timeout,
          onProgress
        )) as ToolResult;
      } else {
        result = (await httpPost(
          url,
          requestData,
          REQUEST_TIMEOUT
        )) as ToolResult;
      }

      telemetry.trackToolCall({
        toolName: endpoint,
        success: result.success !== false,
        durationMs: Date.now() - startTime,
        parameters: params,
      });

      return result;
    } catch (error) {
      telemetry.trackToolCall({
        toolName: endpoint,
        success: false,
        durationMs: Date.now() - startTime,
        errorType: (error as Error).name,
        errorMessage: (error as Error).message,
        parameters: params,
      });
      captureException(error as Error, { tool_name: endpoint });

      if ((error as Error).name === "AbortError") {
        return { success: false, error: `Task timed out after ${timeout}ms` };
      }
      return { success: false, error: (error as Error).message };
    }
  };
}
