/**
 * Tests for the inspection tools module.
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

import { inspect_adsk_api, get_adsk_class_info } from '../src/tools/inspection.js';
import { submitTaskAndWait } from '../src/sse-client.js';

describe('InspectAdskApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should inspect module successfully', async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      path: 'adsk.fusion',
      type: 'module',
      members: [
        { name: 'Sketch', type: 'class' },
        { name: 'BRepBody', type: 'class' },
      ],
      member_count: 2,
    });

    const result = await inspect_adsk_api('adsk.fusion');

    expect(result.success).toBe(true);
    expect(result.path).toBe('adsk.fusion');
    expect(result.type).toBe('module');
    expect(result.members).toHaveLength(2);
    expect(submitTaskAndWait).toHaveBeenCalled();
  });

  it('should use default path', async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      path: 'adsk.fusion',
      type: 'module',
      members: [],
    });

    const result = await inspect_adsk_api();

    expect(result.success).toBe(true);
    expect(submitTaskAndWait).toHaveBeenCalled();
  });

  it('should handle errors', async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: false,
      error: 'Invalid path',
    });

    const result = await inspect_adsk_api('invalid.path');

    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
  });

  it('should inspect a class', async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      path: 'adsk.fusion.Sketch',
      type: 'class',
      members: [{ name: 'sketchCurves', type: 'property' }],
      docstring: 'Sketch class',
    });

    const result = await inspect_adsk_api('adsk.fusion.Sketch');

    expect(result.success).toBe(true);
    expect(result.type).toBe('class');
  });
});

describe('GetAdskClassInfo', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should get class info successfully', async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      class_name: 'Sketch',
      path: 'adsk.fusion.Sketch',
      docstring: 'class Sketch:\n    # Properties\n    # sketchCurves\n',
      properties: [{ name: 'sketchCurves', summary: 'Returns curves' }],
      methods: [{ name: 'add', signature: '(plane)', summary: 'Add sketch' }],
      property_count: 1,
      method_count: 1,
    });

    const result = await get_adsk_class_info('adsk.fusion.Sketch');

    expect(result.success).toBe(true);
    expect(result.class_name).toBe('Sketch');
    expect(result.properties).toBeDefined();
    expect(result.methods).toBeDefined();
  });

  it('should handle errors', async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: false,
      error: 'Invalid class path',
    });

    const result = await get_adsk_class_info('invalid.path');

    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
  });

  it('should return detailed class information', async () => {
    (submitTaskAndWait as Mock).mockResolvedValue({
      success: true,
      class_name: 'Point3D',
      path: 'adsk.core.Point3D',
      docstring: 'Represents a 3D point',
      properties: [
        { name: 'x', summary: 'X coordinate' },
        { name: 'y', summary: 'Y coordinate' },
        { name: 'z', summary: 'Z coordinate' },
      ],
      methods: [
        { name: 'create', signature: '(x, y, z)', summary: 'Create point' },
        { name: 'copy', signature: '()', summary: 'Copy point' },
      ],
      property_count: 3,
      method_count: 2,
    });

    const result = await get_adsk_class_info('adsk.core.Point3D');

    expect(result.success).toBe(true);
    expect(result.property_count).toBe(3);
    expect(result.method_count).toBe(2);
  });
});
