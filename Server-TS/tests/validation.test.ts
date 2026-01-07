/**
 * Tests for validation tools module.
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
  test_connection,
  get_model_state,
  undo,
  delete_all,
  get_faces_info,
} from "../src/tools/validation.js";
import { submitTaskAndWait, httpGet } from "../src/sse-client.js";

describe("test_connection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should test connection successfully", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      message: "Connected to Fusion 360",
    });

    const result = await test_connection();

    expect(result.success).toBe(true);
    expect(submitTaskAndWait).toHaveBeenCalledOnce();
  });

  it("should handle connection failure", async () => {
    (submitTaskAndWait as Mock).mockRejectedValue(
      new Error("Connection refused")
    );

    const result = await test_connection();

    expect(result.success).toBe(false);
  });
});

describe("get_model_state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should get model state successfully", async () => {
    (httpGet as Mock).mockResolvedValue({
      success: true,
      body_count: 2,
      sketch_count: 3,
      bodies: [
        { name: "Body1", volume: 10.5 },
        { name: "Body2", volume: 5.2 },
      ],
    });

    const result = await get_model_state();

    expect(result.success).toBe(true);
    expect(result.body_count).toBe(2);
    expect(result.sketch_count).toBe(3);
  });
});

describe("undo", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should undo successfully", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      message: "Undo successful",
    });

    const result = await undo();

    expect(result.success).toBe(true);
  });
});

describe("delete_all", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should delete all with default options", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      bodies_deleted: 5,
      sketches_deleted: 3,
    });

    const result = await delete_all();

    expect(result.success).toBe(true);
    expect(submitTaskAndWait).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        bodies: true,
        sketches: true,
        construction: true,
        parameters: false,
      }),
      expect.any(Number),
      undefined
    );
  });

  it("should delete with custom options", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({ success: true });

    await delete_all(true, false, false, true);

    expect(submitTaskAndWait).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        bodies: true,
        sketches: false,
        construction: false,
        parameters: true,
      }),
      expect.any(Number),
      undefined
    );
  });
});

describe("get_faces_info", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should get faces info with default body index", async () => {
    (httpGet as Mock).mockResolvedValue({
      success: true,
      face_count: 6,
      faces: [
        { index: 0, type: "Plane", area: 10.0 },
        { index: 1, type: "Plane", area: 10.0 },
      ],
    });

    const result = await get_faces_info();

    expect(result.success).toBe(true);
    expect(result.face_count).toBe(6);
  });

  it("should get faces info with specific body index", async () => {
    (httpGet as Mock).mockResolvedValue({
      success: true,
      face_count: 4,
    });

    await get_faces_info(2);

    expect(httpGet).toHaveBeenCalledWith(
      expect.stringContaining("body_index=2"),
      expect.any(Number)
    );
  });
});
