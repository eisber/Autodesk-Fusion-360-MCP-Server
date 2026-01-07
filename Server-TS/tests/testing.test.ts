/**
 * Tests for the testing tools module.
 *
 * These tools are implemented as LOCAL file-based operations, only calling
 * the Add-In for model_state, undo, and execute_fusion_script.
 */
import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

// Mock the fs module
vi.mock('fs');

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

// Mock scripting module
vi.mock('../src/tools/scripting.js', () => ({
  execute_fusion_script: vi.fn(),
}));

import {
  create_snapshot,
  list_snapshots,
  restore_snapshot,
  delete_snapshot,
  save_test,
  load_tests,
  run_tests,
  delete_test,
} from '../src/tools/testing.js';
import { httpGet, httpPost } from '../src/sse-client.js';
import { execute_fusion_script } from '../src/tools/scripting.js';

// Test storage path
const TEST_DIR = path.join(os.homedir(), 'Desktop', 'Fusion_Tests', 'TestProject');
const SNAPSHOT_DIR = path.join(TEST_DIR, 'snapshots');

describe('Snapshots', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock model_state endpoint
    (httpGet as Mock).mockResolvedValue({
      design_name: 'TestProject',
      body_count: 2,
      sketch_count: 1,
    });
    // Mock fs.mkdirSync
    (fs.mkdirSync as Mock).mockImplementation(() => undefined);
  });

  describe('create_snapshot', () => {
    it('should create snapshot successfully', async () => {
      (fs.writeFileSync as Mock).mockImplementation(() => undefined);

      const result = await create_snapshot('before_changes');

      expect(result.success).toBe(true);
      expect(result.body_count).toBe(2);
      expect(result.sketch_count).toBe(1);
      expect(fs.writeFileSync).toHaveBeenCalled();
    });

    it('should handle invalid name', async () => {
      const result = await create_snapshot('');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid');
    });
  });

  describe('list_snapshots', () => {
    it('should list snapshots when empty', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.readdirSync as Mock).mockReturnValue([]);

      const result = await list_snapshots();

      expect(result.success).toBe(true);
      expect(result.snapshot_count).toBe(0);
      expect(result.snapshots).toEqual([]);
    });

    it('should list snapshots when some exist', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.readdirSync as Mock).mockReturnValue(['snap1.json', 'snap2.json']);
      (fs.readFileSync as Mock).mockImplementation((filePath: string) => {
        if (filePath.includes('snap1')) {
          return JSON.stringify({
            name: 'snap1',
            created_at: '2025-01-01T00:00:00',
            model_state: { body_count: 1, sketch_count: 0 },
          });
        }
        return JSON.stringify({
          name: 'snap2',
          created_at: '2025-01-01T01:00:00',
          model_state: { body_count: 2, sketch_count: 1 },
        });
      });

      const result = await list_snapshots();

      expect(result.success).toBe(true);
      expect(result.snapshot_count).toBe(2);
      expect(result.snapshots[0].name).toBe('snap1');
    });
  });

  describe('restore_snapshot', () => {
    it('should restore snapshot successfully', async () => {
      // Mock snapshot exists
      (fs.existsSync as Mock).mockImplementation((p: string) => {
        return p.includes('target.json') || p.includes('snapshots');
      });
      (fs.readdirSync as Mock).mockReturnValue(['target.json']);
      (fs.readFileSync as Mock).mockReturnValue(
        JSON.stringify({
          name: 'target',
          model_state: { body_count: 1, sketch_count: 0 },
        })
      );

      // Initial state has more bodies, need to undo
      let callCount = 0;
      (httpGet as Mock).mockImplementation(() => {
        callCount++;
        if (callCount <= 3) {
          return { design_name: 'TestProject', body_count: 4 - callCount, sketch_count: 0 };
        }
        return { design_name: 'TestProject', body_count: 1, sketch_count: 0 };
      });
      (httpPost as Mock).mockResolvedValue({ success: true });

      const result = await restore_snapshot('target');

      expect(result.success).toBe(true);
      expect(result.undo_count).toBeGreaterThanOrEqual(0);
    });

    it('should handle already at target state', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.readdirSync as Mock).mockReturnValue(['target.json']);
      (fs.readFileSync as Mock).mockReturnValue(
        JSON.stringify({
          name: 'target',
          model_state: { body_count: 2, sketch_count: 1 },
        })
      );

      const result = await restore_snapshot('target');

      expect(result.success).toBe(true);
      expect(result.undo_count).toBe(0);
    });

    it('should handle snapshot not found', async () => {
      (fs.existsSync as Mock).mockReturnValue(false);
      (fs.readdirSync as Mock).mockReturnValue([]);

      const result = await restore_snapshot('nonexistent');

      expect(result.success).toBe(false);
      expect(result.error).toContain('not found');
    });

    it('should accept max_undo_steps', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.readdirSync as Mock).mockReturnValue(['target.json']);
      (fs.readFileSync as Mock).mockReturnValue(
        JSON.stringify({
          name: 'target',
          model_state: { body_count: 2, sketch_count: 1 },
        })
      );

      const result = await restore_snapshot('target', 100);

      expect(result.success).toBe(true);
    });
  });

  describe('delete_snapshot', () => {
    it('should delete snapshot', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.unlinkSync as Mock).mockImplementation(() => undefined);

      const result = await delete_snapshot('to_delete');

      expect(result.success).toBe(true);
      expect(fs.unlinkSync).toHaveBeenCalled();
    });

    it('should handle not found', async () => {
      (fs.existsSync as Mock).mockReturnValue(false);

      const result = await delete_snapshot('nonexistent');

      expect(result.success).toBe(false);
      expect(result.error).toContain('not found');
    });
  });
});

describe('Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock model_state endpoint
    (httpGet as Mock).mockResolvedValue({
      design_name: 'TestProject',
      body_count: 1,
      sketch_count: 0,
    });
    // Mock fs.mkdirSync
    (fs.mkdirSync as Mock).mockImplementation(() => undefined);
  });

  describe('save_test', () => {
    it('should save test successfully', async () => {
      (fs.writeFileSync as Mock).mockImplementation(() => undefined);

      const result = await save_test('test_body_count', 'assert_body_count(1)', 'Verify one body exists');

      expect(result.success).toBe(true);
      expect(result.message).toContain('test_body_count');
      expect(fs.writeFileSync).toHaveBeenCalled();
    });

    it('should handle invalid name', async () => {
      const result = await save_test('', 'pass', '');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid');
    });
  });

  describe('load_tests', () => {
    it('should load tests when empty', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.readdirSync as Mock).mockReturnValue([]);

      const result = await load_tests();

      expect(result.success).toBe(true);
      expect(result.tests).toEqual([]);
      expect(result.test_count).toBe(0);
    });

    it('should load tests when some exist', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.readdirSync as Mock).mockReturnValue(['my_test.json', 'snapshots']);
      (fs.readFileSync as Mock).mockReturnValue(
        JSON.stringify({
          name: 'my_test',
          description: 'A test',
          script: 'pass',
          created_at: '2025-01-01',
        })
      );
      (fs.statSync as Mock).mockImplementation((p: string) => ({
        isDirectory: () => p.includes('snapshots'),
      }));

      const result = await load_tests();

      expect(result.success).toBe(true);
      expect(result.test_count).toBe(1);
      expect(result.tests[0].name).toBe('my_test');
    });
  });

  describe('run_tests', () => {
    it('should handle single test not found', async () => {
      (fs.existsSync as Mock).mockReturnValue(false);
      (fs.readdirSync as Mock).mockReturnValue([]);

      const result = await run_tests('nonexistent_test');

      expect(result.success).toBe(false);
      expect(result.passed).toBe(false);
      expect(result.error).toContain('not found');
    });

    it('should run single test successfully', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.readdirSync as Mock).mockReturnValue(['my_test.json']);
      (fs.readFileSync as Mock).mockReturnValue(
        JSON.stringify({
          name: 'my_test',
          script: 'result = "ok"',
          description: 'Test',
        })
      );
      (execute_fusion_script as Mock).mockResolvedValue({
        success: true,
        return_value: 'ok',
        model_state: { body_count: 1 },
      });

      const result = await run_tests('my_test');

      expect(result.success).toBe(true);
      expect(result.passed).toBe(true);
      expect(result.return_value).toBe('ok');
    });

    it('should run all tests when no name provided', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.readdirSync as Mock).mockReturnValue(['test1.json', 'test2.json', 'snapshots']);
      (fs.readFileSync as Mock).mockImplementation((filePath: string) => {
        if (filePath.includes('test1')) {
          return JSON.stringify({ name: 'test1', script: 'pass', description: '' });
        }
        return JSON.stringify({ name: 'test2', script: 'pass', description: '' });
      });
      (fs.statSync as Mock).mockImplementation((p: string) => ({
        isDirectory: () => p.includes('snapshots'),
      }));
      (execute_fusion_script as Mock).mockResolvedValue({
        success: true,
        return_value: 'ok',
        model_state: { body_count: 1 },
      });

      const result = await run_tests();

      expect(result.success).toBe(true);
      expect(result.total).toBe(2);
      expect(result.passed).toBe(2);
      expect(result.failed).toBe(0);
    });

    it('should handle test failure', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.readdirSync as Mock).mockReturnValue(['failing_test.json']);
      (fs.readFileSync as Mock).mockReturnValue(
        JSON.stringify({
          name: 'failing_test',
          script: 'raise AssertionError("test failed")',
          description: '',
        })
      );
      (execute_fusion_script as Mock).mockResolvedValue({
        success: false,
        error: 'AssertionError: test failed',
        model_state: { body_count: 0 },
      });

      const result = await run_tests('failing_test');

      expect(result.success).toBe(true);
      expect(result.passed).toBe(false);
    });
  });

  describe('delete_test', () => {
    it('should delete test', async () => {
      (fs.existsSync as Mock).mockReturnValue(true);
      (fs.unlinkSync as Mock).mockImplementation(() => undefined);

      const result = await delete_test('to_delete');

      expect(result.success).toBe(true);
      expect(fs.unlinkSync).toHaveBeenCalled();
    });

    it('should handle test not found', async () => {
      (fs.existsSync as Mock).mockReturnValue(false);

      const result = await delete_test('nonexistent');

      expect(result.success).toBe(false);
      expect(result.error).toContain('not found');
    });
  });
});
