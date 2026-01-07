/**
 * Tests for tool registration.
 */
import { describe, it, expect } from 'vitest';
import { TOOL_DEFINITIONS, toolHandlers } from '../src/index';

describe('AllExportsExist', () => {
  it('should have all tool definitions', () => {
    expect(TOOL_DEFINITIONS).toBeDefined();
    expect(Array.isArray(TOOL_DEFINITIONS)).toBe(true);
    expect(TOOL_DEFINITIONS.length).toBeGreaterThan(0);
  });

  it('should have handlers for all tools', () => {
    const missingHandlers: string[] = [];
    
    for (const tool of TOOL_DEFINITIONS) {
      if (!toolHandlers[tool.name]) {
        missingHandlers.push(tool.name);
      }
    }
    
    expect(missingHandlers).toEqual([]);
  });

  it('should have no duplicate tool names', () => {
    const seen = new Set<string>();
    const duplicates: string[] = [];
    
    for (const tool of TOOL_DEFINITIONS) {
      if (seen.has(tool.name)) {
        duplicates.push(tool.name);
      }
      seen.add(tool.name);
    }
    
    expect(duplicates).toEqual([]);
  });
});

describe('ToolImports', () => {
  it('should import validation tools', async () => {
    const validation = await import('../src/tools/validation');
    expect(validation.test_connection).toBeDefined();
    expect(validation.get_model_state).toBeDefined();
  });

  it('should import parameter tools', async () => {
    const parameters = await import('../src/tools/parameters');
    expect(parameters.list_parameters).toBeDefined();
  });

  it('should import measurement tools', async () => {
    const measurement = await import('../src/tools/measurement');
    expect(measurement.measure_distance).toBeDefined();
  });

  it('should import scripting tools', async () => {
    const scripting = await import('../src/tools/scripting');
    expect(scripting.execute_fusion_script).toBeDefined();
  });
});

describe('ToolCallable', () => {
  it('should have callable test_connection', async () => {
    const { test_connection } = await import('../src/tools/validation');
    expect(typeof test_connection).toBe('function');
  });

  it('should have callable execute_fusion_script', async () => {
    const { execute_fusion_script } = await import('../src/tools/scripting');
    expect(typeof execute_fusion_script).toBe('function');
  });
});

describe('ToolDefinitionStructure', () => {
  it('should have required fields in all tool definitions', () => {
    for (const tool of TOOL_DEFINITIONS) {
      expect(tool.name).toBeDefined();
      expect(typeof tool.name).toBe('string');
      expect(tool.description).toBeDefined();
      expect(typeof tool.description).toBe('string');
      expect(tool.inputSchema).toBeDefined();
      expect(tool.inputSchema.type).toBe('object');
    }
  });
});
