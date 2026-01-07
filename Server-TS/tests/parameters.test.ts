/**
 * Tests for parameter tools.
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

import { list_parameters, set_parameter, create_user_parameter } from '../src/tools/parameters.js';
import { submitTaskAndWait, httpGet } from '../src/sse-client.js';

describe('ParameterTools', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list_parameters', () => {
    it('should return parameters list', async () => {
      (httpGet as Mock).mockResolvedValue({
        success: true,
        parameters: [{ name: 'width', value: 10 }],
      });

      const result = await list_parameters();

      expect(result.success).toBe(true);
      expect(result.parameters).toHaveLength(1);
      expect(httpGet).toHaveBeenCalled();
    });

    it('should handle empty parameters', async () => {
      (httpGet as Mock).mockResolvedValue({
        success: true,
        parameters: [],
      });

      const result = await list_parameters();

      expect(result.success).toBe(true);
      expect(result.parameters).toEqual([]);
    });
  });

  describe('set_parameter', () => {
    it('should send correct request', async () => {
      (submitTaskAndWait as Mock).mockResolvedValue({
        success: true,
        parameter_name: 'width',
        value: 20,
      });

      const result = await set_parameter('width', '20');

      expect(result.success).toBe(true);
      expect(submitTaskAndWait).toHaveBeenCalled();
    });

    it('should handle parameter not found', async () => {
      (submitTaskAndWait as Mock).mockResolvedValue({
        success: false,
        error: 'Parameter not found',
      });

      const result = await set_parameter('nonexistent', '10');

      expect(result.success).toBe(false);
      expect(result.error).toContain('not found');
    });
  });

  describe('create_user_parameter', () => {
    it('should create parameter successfully', async () => {
      (submitTaskAndWait as Mock).mockResolvedValue({
        success: true,
        parameter_name: 'height',
        value: 30,
        expression: '30 mm',
      });

      const result = await create_user_parameter('height', '30', 'mm', 'Height of box');

      expect(result.success).toBe(true);
      expect(result.parameter_name).toBe('height');
    });

    it('should handle duplicate parameter', async () => {
      (submitTaskAndWait as Mock).mockResolvedValue({
        success: false,
        error: 'Parameter already exists',
      });

      const result = await create_user_parameter('width', '10', 'mm', '');

      expect(result.success).toBe(false);
      expect(result.error).toContain('exists');
    });
  });
});
