/**
 * Tests for the instructions module.
 */
import { describe, it, expect } from 'vitest';
import { SYSTEM_INSTRUCTIONS } from '../src/instructions';

describe('SystemInstructions', () => {
  it('should not be empty', () => {
    expect(SYSTEM_INSTRUCTIONS).toBeDefined();
    expect(SYSTEM_INSTRUCTIONS.length).toBeGreaterThan(0);
  });

  it('should be a string', () => {
    expect(typeof SYSTEM_INSTRUCTIONS).toBe('string');
  });

  it('should contain key elements about Fusion 360', () => {
    const lower = SYSTEM_INSTRUCTIONS.toLowerCase();
    expect(lower).toContain('fusion');
  });

  it('should mention units', () => {
    expect(
      SYSTEM_INSTRUCTIONS.includes('mm') || SYSTEM_INSTRUCTIONS.includes('cm')
    ).toBe(true);
  });
});
