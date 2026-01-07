/**
 * SSE Client for communicating with Fusion 360 Add-In.
 * Replaces polling with real-time event streaming for task updates.
 */

import { BASE_URL } from "./config.js";

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export type ProgressCallback = (percent: number, message: string) => void;

/**
 * Parse SSE event from raw text lines.
 */
function parseSSELines(
  lines: string[],
  state: { eventType: string | null; eventData: string[] }
): SSEEvent | null {
  for (const line of lines) {
    const trimmed = line.trim();

    if (trimmed.startsWith("event:")) {
      state.eventType = trimmed.slice(6).trim();
    } else if (trimmed.startsWith("data:")) {
      state.eventData.push(trimmed.slice(5).trim());
    } else if (trimmed === "" && state.eventType) {
      // End of event
      try {
        const data =
          state.eventData.length > 0
            ? JSON.parse(state.eventData.join(""))
            : {};
        const event = { event: state.eventType, data };
        state.eventType = null;
        state.eventData = [];
        return event;
      } catch {
        console.warn("Failed to parse SSE data:", state.eventData);
        state.eventType = null;
        state.eventData = [];
      }
    }
  }
  return null;
}

/**
 * Submit a task and wait for completion via SSE.
 * Uses SSE-first architecture to avoid race conditions:
 * 1. Connect to SSE stream (background)
 * 2. Submit the task via POST
 * 3. Match task_id from task_created event
 * 4. Wait for task_completed/task_failed
 */
export async function submitTaskAndWait(
  endpoint: string,
  data: Record<string, unknown>,
  timeout: number = 300000,
  onProgress?: ProgressCallback
): Promise<Record<string, unknown>> {
  const baseUrl = endpoint.substring(0, endpoint.lastIndexOf("/"));
  const eventsUrl = `${baseUrl}/events`;

  // Use AbortController for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  let taskId: string | null = null;

  try {
    // Create promise that resolves when task completes
    const eventPromise = new Promise<Record<string, unknown>>(
      (resolve, reject) => {
        const state = { eventType: null as string | null, eventData: [] as string[] };

        fetch(eventsUrl, { signal: controller.signal })
          .then(async (response) => {
            if (!response.ok) {
              throw new Error(`SSE connection failed: ${response.status}`);
            }
            if (!response.body) {
              throw new Error("No response body");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() || "";

              const event = parseSSELines(lines, state);
              if (!event) continue;

              const eventTaskId = event.data.task_id as string | undefined;

              // Filter events for our task
              if (eventTaskId && taskId && eventTaskId !== taskId) {
                continue;
              }

              switch (event.event) {
                case "task_created":
                  if (!taskId) {
                    taskId = event.data.task_id as string;
                  }
                  break;

                case "task_progress":
                  if (onProgress) {
                    onProgress(
                      (event.data.progress as number) || 0,
                      (event.data.message as string) || ""
                    );
                  }
                  break;

                case "task_completed":
                  resolve(
                    (event.data.result as Record<string, unknown>) || {
                      success: true,
                    }
                  );
                  return;

                case "task_failed":
                  resolve({
                    success: false,
                    error: (event.data.error as string) || "Task failed",
                  });
                  return;

                case "task_cancelled":
                  resolve({ success: false, error: "Task was cancelled" });
                  return;

                case "error":
                  reject(new Error(`SSE error: ${event.data.error}`));
                  return;

                case "keepalive":
                  // Ignore keepalive events
                  break;
              }
            }
          })
          .catch((err: Error) => {
            // Ignore abort errors - they're expected when timeout or cleanup happens
            if (err.name === 'AbortError') {
              resolve({ success: false, error: 'Request timed out or was aborted' });
            } else {
              reject(err);
            }
          });
      }
    );

    // Small delay for SSE to connect
    await new Promise((r) => setTimeout(r, 50));

    // Submit the task
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const submitResult = (await response.json()) as Record<string, unknown>;

    if (!submitResult.task_id) {
      // Legacy response without task_id
      return submitResult;
    }

    taskId = submitResult.task_id as string;

    // Wait for task completion via SSE
    return await eventPromise;
  } finally {
    clearTimeout(timeoutId);
    // Abort the controller to clean up any pending fetch requests.
    // We don't await this since abort() might cause rejections in flight.
    try {
      controller.abort();
    } catch {
      // Ignore abort errors - they're expected when cleaning up
    }
  }
}

/**
 * Cancel a running task.
 */
export async function cancelTask(
  taskId: string,
  baseUrl: string = BASE_URL
): Promise<Record<string, unknown>> {
  const response = await fetch(`${baseUrl}/task/${taskId}`, {
    method: "DELETE",
  });
  return (await response.json()) as Record<string, unknown>;
}

/**
 * Simple HTTP GET request.
 */
export async function httpGet(
  url: string,
  timeout: number = 30000
): Promise<Record<string, unknown>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return (await response.json()) as Record<string, unknown>;
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeout}ms`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Simple HTTP POST request (non-SSE).
 */
export async function httpPost(
  url: string,
  data: Record<string, unknown>,
  timeout: number = 30000
): Promise<Record<string, unknown>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return (await response.json()) as Record<string, unknown>;
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeout}ms`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}
