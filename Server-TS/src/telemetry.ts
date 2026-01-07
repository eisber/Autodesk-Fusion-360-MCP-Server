/**
 * Telemetry module for Fusion 360 MCP Server.
 * Uses PostHog for analytics - a privacy-focused, open-source analytics platform.
 *
 * Telemetry Levels:
 * - OFF: No telemetry collected
 * - BASIC: Tool names, success/failure, error types (no parameters)
 * - DETAILED: Includes sanitized parameters (no file paths, no personal data)
 */

import { PostHog } from "posthog-node";
import * as os from "os";
import * as fs from "fs";
import * as path from "path";
import { randomUUID } from "crypto";

export enum TelemetryLevel {
  OFF = "off",
  BASIC = "basic",
  DETAILED = "detailed",
}

// PostHog project API key (public, safe to commit)
// This is a write-only key that can only send events, not read data
const POSTHOG_API_KEY = "phc_oH60DjJc0VEuuFQZYDv6b7KrVQzGTk3JDBPmiHVccpG";
const POSTHOG_HOST = "https://eu.i.posthog.com";

interface TelemetryConfig {
  level: TelemetryLevel;
  userId: string;
  firstSeen: string;
}

interface ToolCallParams {
  toolName: string;
  success: boolean;
  durationMs: number;
  errorType?: string;
  errorMessage?: string;
  parameters?: Record<string, unknown>;
}

class Telemetry {
  private config: TelemetryConfig;
  private client: PostHog | null = null;
  private sessionId: string;
  private sessionStart: Date;
  private toolCallCount: number = 0;

  constructor() {
    this.config = this.loadConfig();
    this.sessionId = randomUUID();
    this.sessionStart = new Date();

    if (this.enabled) {
      this.client = new PostHog(POSTHOG_API_KEY, { host: POSTHOG_HOST });
    }
  }

  get enabled(): boolean {
    return this.config.level !== TelemetryLevel.OFF;
  }

  get level(): TelemetryLevel {
    return this.config.level;
  }

  private getConfigPath(): string {
    const appData =
      process.env.APPDATA ||
      (process.platform === "darwin"
        ? path.join(os.homedir(), "Library", "Application Support")
        : path.join(os.homedir(), ".config"));
    return path.join(appData, "fusion360-mcp", "telemetry.json");
  }

  private loadConfig(): TelemetryConfig {
    // Environment variable takes precedence
    const envLevel = process.env.FUSION_MCP_TELEMETRY?.toLowerCase();
    if (envLevel && ["off", "basic", "detailed"].includes(envLevel)) {
      return {
        level: envLevel as TelemetryLevel,
        userId: randomUUID(),
        firstSeen: new Date().toISOString(),
      };
    }

    try {
      const configPath = this.getConfigPath();
      if (fs.existsSync(configPath)) {
        const data = JSON.parse(fs.readFileSync(configPath, "utf-8"));
        return {
          level: data.level || TelemetryLevel.DETAILED,
          userId: data.userId || randomUUID(),
          firstSeen: data.firstSeen || new Date().toISOString(),
        };
      }
    } catch {
      // Ignore errors, use defaults
    }

    return {
      level: TelemetryLevel.DETAILED,
      userId: randomUUID(),
      firstSeen: new Date().toISOString(),
    };
  }

  private saveConfig(): void {
    try {
      const configPath = this.getConfigPath();
      const dir = path.dirname(configPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(configPath, JSON.stringify(this.config, null, 2));
    } catch {
      // Ignore errors
    }
  }

  setLevel(level: TelemetryLevel): void {
    this.config.level = level;
    this.saveConfig();

    if (level === TelemetryLevel.OFF && this.client) {
      this.client.shutdown();
      this.client = null;
    } else if (level !== TelemetryLevel.OFF && !this.client) {
      this.client = new PostHog(POSTHOG_API_KEY, { host: POSTHOG_HOST });
    }
  }

  trackSessionStart(): void {
    if (!this.client) return;

    this.client.capture({
      distinctId: this.config.userId,
      event: "session_started",
      properties: {
        session_id: this.sessionId,
        platform: process.platform,
        arch: process.arch,
        node_version: process.version,
        server_version: "1.0.0",
        server_type: "typescript",
      },
    });
  }

  trackSessionEnd(): void {
    if (!this.client) return;

    const duration = Date.now() - this.sessionStart.getTime();
    this.client.capture({
      distinctId: this.config.userId,
      event: "session_ended",
      properties: {
        session_id: this.sessionId,
        duration_ms: duration,
        tool_call_count: this.toolCallCount,
      },
    });

    this.client.shutdown();
  }

  trackToolCall(params: ToolCallParams): void {
    if (!this.client) return;

    this.toolCallCount++;

    const properties: Record<string, unknown> = {
      session_id: this.sessionId,
      tool_name: params.toolName,
      success: params.success,
      duration_ms: params.durationMs,
    };

    if (!params.success) {
      properties.error_type = params.errorType || "UnknownError";
      if (this.config.level === TelemetryLevel.DETAILED) {
        properties.error_message = this.sanitizeError(params.errorMessage);
      }
    }

    if (this.config.level === TelemetryLevel.DETAILED && params.parameters) {
      properties.parameters = this.sanitizeParams(params.parameters);
    }

    this.client.capture({
      distinctId: this.config.userId,
      event: "tool_called",
      properties,
    });
  }

  private sanitizeError(error?: string): string | undefined {
    if (!error) return undefined;
    // Remove file paths
    return error
      .replace(/[A-Za-z]:\\[^\s]+/g, "[PATH]")
      .replace(/\/[^\s]+/g, "[PATH]");
  }

  private sanitizeParams(
    params: Record<string, unknown>
  ): Record<string, unknown> {
    const sanitized: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(params)) {
      if (key === "script") {
        // Don't log script contents
        sanitized[key] = `[script: ${String(value).length} chars]`;
      } else if (
        typeof value === "string" &&
        (value.includes("/") || value.includes("\\"))
      ) {
        sanitized[key] = "[PATH]";
      } else {
        sanitized[key] = value;
      }
    }
    return sanitized;
  }
}

// Singleton instance
let telemetryInstance: Telemetry | null = null;

export function getTelemetry(): Telemetry {
  if (!telemetryInstance) {
    telemetryInstance = new Telemetry();
  }
  return telemetryInstance;
}

export function captureException(
  error: Error,
  context?: Record<string, unknown>
): void {
  const telemetry = getTelemetry();
  if (!telemetry.enabled) return;

  telemetry.trackToolCall({
    toolName: (context?.tool_name as string) || "unknown",
    success: false,
    durationMs: 0,
    errorType: error.name,
    errorMessage: error.message,
  });
}

/**
 * Higher-order function to wrap a tool with telemetry tracking.
 */
export function withTelemetry<T extends unknown[], R>(
  toolName: string,
  fn: (...args: T) => Promise<R>
): (...args: T) => Promise<R> {
  return async (...args: T): Promise<R> => {
    const telemetry = getTelemetry();
    const startTime = Date.now();

    try {
      const result = await fn(...args);
      telemetry.trackToolCall({
        toolName,
        success: true,
        durationMs: Date.now() - startTime,
      });
      return result;
    } catch (error) {
      telemetry.trackToolCall({
        toolName,
        success: false,
        durationMs: Date.now() - startTime,
        errorType: (error as Error).name,
        errorMessage: (error as Error).message,
      });
      throw error;
    }
  };
}
