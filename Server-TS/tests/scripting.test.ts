/**
 * Tests for scripting tools module.
 */

import { describe, it, expect, vi, beforeEach, Mock } from "vitest";

// Mock the SSE client before importing
vi.mock("../src/sse-client.js", () => ({
  submitTaskAndWait: vi.fn(),
  cancelTask: vi.fn(),
  httpGet: vi.fn(),
  httpPost: vi.fn(),
}));

// Mock telemetry
vi.mock("../src/telemetry.js", () => ({
  getTelemetry: vi.fn(() => ({
    trackToolCall: vi.fn(),
    enabled: false,
  })),
  captureException: vi.fn(),
}));

import {
  execute_fusion_script,
  cancel_fusion_task,
} from "../src/tools/scripting.js";
import { submitTaskAndWait, cancelTask } from "../src/sse-client.js";

describe("execute_fusion_script", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should execute script successfully", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      return_value: "test_result",
    });

    const result = await execute_fusion_script("result = 'test_result'");

    expect(result.success).toBe(true);
    expect(result.return_value).toBe("test_result");
    expect(submitTaskAndWait).toHaveBeenCalledOnce();
  });

  it("should handle connection errors", async () => {
    (submitTaskAndWait as Mock).mockRejectedValue(
      new Error("Connection refused")
    );

    const result = await execute_fusion_script("result = 1");

    expect(result.success).toBe(false);
    expect(result.error).toContain("Connection refused");
  });

  it("should handle script errors", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: false,
      error: "SyntaxError: invalid syntax",
      error_line: 1,
    });

    const result = await execute_fusion_script("def broken(");

    expect(result.success).toBe(false);
    expect(result.error).toContain("SyntaxError");
  });

  it("should use custom timeout", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({ success: true });

    await execute_fusion_script("result = 1", 60);

    expect(submitTaskAndWait).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ script: "result = 1" }),
      60000, // 60 seconds in milliseconds
      undefined
    );
  });
});

describe("cancel_fusion_task", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should cancel task successfully", async () => {
    (cancelTask as Mock).mockResolvedValue({
      success: true,
      task_id: "abc12345",
      status: "cancelled",
    });

    const result = await cancel_fusion_task("abc12345");

    expect(result.success).toBe(true);
    expect(cancelTask).toHaveBeenCalledWith("abc12345");
  });

  it("should handle cancellation errors", async () => {
    (cancelTask as Mock).mockRejectedValue(new Error("Task not found"));

    const result = await cancel_fusion_task("invalid_id");

    expect(result.success).toBe(false);
    expect(result.error).toContain("Task not found");
  });
});
