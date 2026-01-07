/**
 * Tests for the prompts module.
 */
import { describe, it, expect } from 'vitest';
import { PROMPTS } from '../src/prompts';

describe('Prompts', () => {
  describe('PROMPTS object', () => {
    it('should be a record/object', () => {
      expect(typeof PROMPTS).toBe('object');
      expect(PROMPTS).not.toBeNull();
    });

    it('should not be empty', () => {
      expect(Object.keys(PROMPTS).length).toBeGreaterThan(0);
    });

    it('should have wineglass prompt', () => {
      expect(PROMPTS['wineglass']).toBeDefined();
    });

    it('should have magnet prompt', () => {
      expect(PROMPTS['magnet']).toBeDefined();
    });

    it('should have box prompt', () => {
      expect(PROMPTS['box']).toBeDefined();
    });
  });

  describe('prompt content', () => {
    it('should return existing prompt content', () => {
      const prompt = PROMPTS['wineglass'];
      expect(prompt).toBeDefined();
      expect(prompt.length).toBeGreaterThan(0);
    });

    it('should return undefined for nonexistent prompt', () => {
      const prompt = PROMPTS['nonexistent_prompt_xyz'];
      expect(prompt).toBeUndefined();
    });

    it('should return a string for existing prompts', () => {
      const prompt = PROMPTS['wineglass'];
      expect(typeof prompt).toBe('string');
    });
  });
});
