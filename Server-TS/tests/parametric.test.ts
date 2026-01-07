/**
 * Tests for parametric tools.
 */
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';

// Mock the SSE client before importing
vi.mock('../src/sse-client.js', () => ({
  submitTaskAndWait: vi.fn(),
  cancelTask: vi.fn(),
  httpGet: vi.fn(),
  httpPost: vi.fn(),
}));

// Mock telemetry
vi.mock('../src/telemetry.js', () => ({
  getTelemetry: vi.fn(() => ({
    trackToolCall: vi.fn(),
    enabled: false,
  })),
  captureException: vi.fn(),
}));

import { check_all_interferences, list_construction_geometry, suppress_feature } from '../src/tools/parametric.js';
import { submitTaskAndWait, httpGet } from '../src/sse-client.js';

describe('ParametricTools', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('check_all_interferences', () => {
    it('should detect no interference', async () => {
      (httpGet as Mock).mockResolvedValue({
        success: true,
        total_bodies: 2,
        interference_count: 0,
        interferences: [],
      });

      const result = await check_all_interferences();

      expect(result.success).toBe(true);
      expect(result.interference_count).toBe(0);
      expect(httpGet).toHaveBeenCalled();
    });

    it('should detect interferences', async () => {
      (httpGet as Mock).mockResolvedValue({
        success: true,
        total_bodies: 3,
        interference_count: 1,
        interferences: [{ body1: 0, body2: 1 }],
      });

      const result = await check_all_interferences();

      expect(result.success).toBe(true);
      expect(result.interference_count).toBe(1);
    });
  });

  describe('list_construction_geometry', () => {
    it('should return empty lists', async () => {
      (httpGet as Mock).mockResolvedValue({
        success: true,
        planes: [],
        axes: [],
        points: [],
      });

      const result = await list_construction_geometry();

      expect(result.success).toBe(true);
      expect(result.planes).toEqual([]);
      expect(result.axes).toEqual([]);
      expect(result.points).toEqual([]);
    });

    it('should return construction geometry', async () => {
      (httpGet as Mock).mockResolvedValue({
        success: true,
        planes: [{ name: 'XY Plane', type: 'standard' }],
        axes: [{ name: 'X Axis', direction: [1, 0, 0] }],
        points: [{ name: 'Origin', position: [0, 0, 0] }],
      });

      const result = await list_construction_geometry();

      expect(result.success).toBe(true);
      expect(result.planes).toHaveLength(1);
      expect(result.axes).toHaveLength(1);
      expect(result.points).toHaveLength(1);
    });
  });

  describe('suppress_feature', () => {
    it('should suppress a feature', async () => {
      (submitTaskAndWait as Mock).mockResolvedValue({
        success: true,
        feature_name: 'Extrude1',
        is_suppressed: true,
      });

      const result = await suppress_feature(0, true);

      expect(result.success).toBe(true);
      expect(result.is_suppressed).toBe(true);
    });

    it('should unsuppress a feature', async () => {
      (submitTaskAndWait as Mock).mockResolvedValue({
        success: true,
        feature_name: 'Extrude1',
        is_suppressed: false,
      });

      const result = await suppress_feature(0, false);

      expect(result.success).toBe(true);
      expect(result.is_suppressed).toBe(false);
    });

    it('should handle invalid feature index', async () => {
      (submitTaskAndWait as Mock).mockResolvedValue({
        success: false,
        error: 'Invalid feature index',
      });

      const result = await suppress_feature(999, true);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid');
    });
  });
});
