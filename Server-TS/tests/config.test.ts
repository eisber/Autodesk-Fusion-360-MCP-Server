/**
 * Tests for configuration module.
 */
import { describe, it, expect } from 'vitest';
import { BASE_URL, HEADERS, REQUEST_TIMEOUT, ENDPOINTS } from '../src/config';

describe('Config', () => {
  describe('BASE_URL', () => {
    it('should be set correctly', () => {
      expect(BASE_URL).toBe('http://localhost:5000');
    });
  });

  describe('HEADERS', () => {
    it('should include Content-Type', () => {
      expect(HEADERS['Content-Type']).toBe('application/json');
    });
  });

  describe('REQUEST_TIMEOUT', () => {
    it('should be a positive number', () => {
      expect(REQUEST_TIMEOUT).toBeGreaterThan(0);
    });
  });

  describe('ENDPOINTS', () => {
    it('should have test_connection endpoint', () => {
      expect(ENDPOINTS.test_connection).toBe('http://localhost:5000/test_connection');
    });

    it('should have model_state endpoint', () => {
      expect(ENDPOINTS.model_state).toBe('http://localhost:5000/model_state');
    });
  });
});
