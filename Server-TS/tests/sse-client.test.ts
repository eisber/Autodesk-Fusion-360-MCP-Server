/**
 * Tests for SSE client module.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

describe("SSE Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("submitTaskAndWait", () => {
    it("should handle legacy responses without task_id", async () => {
      // Mock fetch to return a response without task_id
      global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes("/events")) {
          // Return a never-resolving promise for SSE
          return new Promise(() => {});
        }
        // POST request
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, result: "direct" }),
        });
      });

      const { submitTaskAndWait } = await import("../src/sse-client.js");

      const result = await submitTaskAndWait(
        "http://localhost:5000/test",
        { command: "test" },
        1000
      );

      expect(result.success).toBe(true);
    });
  });

  describe("httpGet", () => {
    it("should make GET request successfully", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, data: "test" }),
      });

      const { httpGet } = await import("../src/sse-client.js");

      const result = await httpGet("http://localhost:5000/test");

      expect(result.success).toBe(true);
      expect(result.data).toBe("test");
    });

    it("should handle HTTP errors", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      });

      const { httpGet } = await import("../src/sse-client.js");

      await expect(httpGet("http://localhost:5000/test")).rejects.toThrow(
        "HTTP 500"
      );
    });
  });

  describe("httpPost", () => {
    it("should make POST request successfully", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      const { httpPost } = await import("../src/sse-client.js");

      const result = await httpPost("http://localhost:5000/test", {
        data: "value",
      });

      expect(result.success).toBe(true);
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:5000/test",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ data: "value" }),
        })
      );
    });
  });

  describe("cancelTask", () => {
    it("should cancel task successfully", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({ success: true, status: "cancelled" }),
      });

      const { cancelTask } = await import("../src/sse-client.js");

      const result = await cancelTask("task123");

      expect(result.success).toBe(true);
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/task/task123"),
        expect.objectContaining({ method: "DELETE" })
      );
    });
  });
});
