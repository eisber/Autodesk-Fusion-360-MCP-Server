/**
 * Tests for measurement tools module.
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
  measure_distance,
  measure_angle,
  measure_area,
  measure_volume,
  measure_edge_length,
  measure_body_properties,
  measure_point_to_point,
  get_edges_info,
  get_vertices_info,
} from "../src/tools/measurement.js";
import { submitTaskAndWait, httpGet } from "../src/sse-client.js";

describe("measure_distance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should measure distance between two faces", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      distance: 5.0,
      point1: [0, 0, 0],
      point2: [5, 0, 0],
    });

    const result = await measure_distance("face", 0, "face", 1, 0, 0);

    expect(result.success).toBe(true);
    expect(result.distance).toBe(5.0);
    expect(submitTaskAndWait).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        entity1_type: "face",
        entity1_index: 0,
        entity2_type: "face",
        entity2_index: 1,
      }),
      expect.any(Number),
      undefined
    );
  });

  it("should measure distance between bodies", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      distance: 2.5,
    });

    const result = await measure_distance("body", 0, "body", 1, 0, 1);

    expect(result.success).toBe(true);
    expect(submitTaskAndWait).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body1_index: 0,
        body2_index: 1,
      }),
      expect.any(Number),
      undefined
    );
  });
});

describe("measure_angle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should measure angle between two faces", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      angle_degrees: 90.0,
      angle_radians: 1.5708,
    });

    const result = await measure_angle("face", 0, "face", 1);

    expect(result.success).toBe(true);
    expect(result.angle_degrees).toBe(90.0);
  });
});

describe("measure_area", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should measure face area", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      area_cm2: 25.0,
      area_mm2: 2500.0,
      face_type: "Plane",
    });

    const result = await measure_area(0, 0);

    expect(result.success).toBe(true);
    expect(result.area_cm2).toBe(25.0);
  });
});

describe("measure_volume", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should measure body volume", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      volume_cm3: 125.0,
      volume_mm3: 125000.0,
      body_name: "Body1",
    });

    const result = await measure_volume(0);

    expect(result.success).toBe(true);
    expect(result.volume_cm3).toBe(125.0);
  });
});

describe("measure_edge_length", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should measure edge length", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      length_cm: 5.0,
      length_mm: 50.0,
      edge_type: "Line",
      start_point: [0, 0, 0],
      end_point: [5, 0, 0],
    });

    const result = await measure_edge_length(0, 0);

    expect(result.success).toBe(true);
    expect(result.length_cm).toBe(5.0);
  });
});

describe("measure_body_properties", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should get body properties", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      volume_cm3: 125.0,
      surface_area_cm2: 150.0,
      centroid: [2.5, 1.5, 1.0],
      face_count: 6,
      edge_count: 12,
      vertex_count: 8,
    });

    const result = await measure_body_properties(0);

    expect(result.success).toBe(true);
    expect(result.face_count).toBe(6);
    expect(result.edge_count).toBe(12);
  });
});

describe("measure_point_to_point", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should measure distance between points", async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      distance_cm: 5.0,
      distance_mm: 50.0,
      delta: [3, 4, 0],
    });

    const result = await measure_point_to_point([0, 0, 0], [3, 4, 0]);

    expect(result.success).toBe(true);
    expect(result.distance_cm).toBe(5.0);
  });
});

describe("get_edges_info", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should get edges info", async () => {
    (httpGet as Mock).mockResolvedValue({
      success: true,
      edge_count: 12,
      edges: [{ index: 0, type: "Line", length: 5.0 }],
    });

    const result = await get_edges_info(0);

    expect(result.success).toBe(true);
    expect(result.edge_count).toBe(12);
  });
});

describe("get_vertices_info", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should get vertices info", async () => {
    (httpGet as Mock).mockResolvedValue({
      success: true,
      vertex_count: 8,
      vertices: [{ index: 0, position: [0, 0, 0] }],
    });

    const result = await get_vertices_info(0);

    expect(result.success).toBe(true);
    expect(result.vertex_count).toBe(8);
  });
});
