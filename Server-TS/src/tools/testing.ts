/**
 * Testing tools for Fusion 360 MCP Server.
 * Tools for creating and running validation tests.
 *
 * These tools are implemented locally (file-based) and only call the Add-In
 * for model_state, undo, and execute_fusion_script operations.
 */

import { z } from "zod";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { ToolResult } from "./base.js";
import { httpGet, httpPost } from "../sse-client.js";
import { BASE_URL, REQUEST_TIMEOUT } from "../config.js";
import { execute_fusion_script } from "./scripting.js";

// Storage path for tests and snapshots
const TEST_STORAGE_PATH = path.join(os.homedir(), "Desktop", "Fusion_Tests");

// Zod schemas
export const createSnapshotSchema = z.object({
  name: z.string().describe("Name for the snapshot (alphanumeric and underscores)"),
});

export const listSnapshotsSchema = z.object({});

export const restoreSnapshotSchema = z.object({
  name: z.string().describe("Name of the snapshot to restore"),
  max_undo_steps: z
    .number()
    .default(50)
    .describe("Maximum undo operations to attempt"),
});

export const deleteSnapshotSchema = z.object({
  name: z.string().describe("Name of the snapshot to delete"),
});

export const saveTestSchema = z.object({
  name: z.string().describe("Test name (alphanumeric and underscores)"),
  script: z.string().describe("Python script with assertions to execute"),
  description: z.string().default("").describe("Description of what the test validates"),
});

export const loadTestsSchema = z.object({});

export const runTestsSchema = z.object({
  name: z
    .string()
    .optional()
    .describe("Name of specific test to run (omit to run all)"),
});

export const deleteTestSchema = z.object({
  name: z.string().describe("Name of the test to delete"),
});

// Helper functions

function sanitizeName(name: string): string {
  return name.replace(/[^a-zA-Z0-9_-]/g, "").trim();
}

async function getProjectName(): Promise<string> {
  try {
    const state = await httpGet(`${BASE_URL}/get_model_state`, REQUEST_TIMEOUT);
    return (state as { design_name?: string }).design_name || "UnnamedProject";
  } catch {
    return "UnnamedProject";
  }
}

function getTestDir(projectName: string): string {
  const safeName = sanitizeName(projectName) || "UnnamedProject";
  const testDir = path.join(TEST_STORAGE_PATH, safeName);
  fs.mkdirSync(testDir, { recursive: true });
  return testDir;
}

function getSnapshotDir(projectName: string): string {
  const testDir = getTestDir(projectName);
  const snapshotDir = path.join(testDir, "snapshots");
  fs.mkdirSync(snapshotDir, { recursive: true });
  return snapshotDir;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// =============================================================================
// Snapshot Tools - Local file-based implementation
// =============================================================================

/**
 * Create a snapshot of the current model state.
 *
 * Snapshots capture body_count, sketch_count, and body details (volumes, bounding boxes).
 * Use this BEFORE making changes to enable rollback verification.
 */
export async function create_snapshot(name: string): Promise<ToolResult> {
  try {
    const projectName = await getProjectName();
    const snapshotDir = getSnapshotDir(projectName);

    const safeName = sanitizeName(name);
    if (!safeName) {
      return { success: false, error: "Invalid snapshot name" };
    }

    // Get current model state from Add-In
    const modelState = await httpGet(`${BASE_URL}/get_model_state`, REQUEST_TIMEOUT);

    const snapshotData = {
      name,
      project_name: projectName,
      created_at: new Date().toISOString(),
      model_state: modelState,
    };

    const filePath = path.join(snapshotDir, `${safeName}.json`);
    fs.writeFileSync(filePath, JSON.stringify(snapshotData, null, 2));

    const state = modelState as { body_count?: number; sketch_count?: number };
    return {
      success: true,
      message: `Snapshot '${name}' created`,
      file_path: filePath,
      body_count: state.body_count ?? 0,
      sketch_count: state.sketch_count ?? 0,
    };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

/**
 * List all snapshots for the current Fusion project.
 */
export async function list_snapshots(): Promise<ToolResult> {
  try {
    const projectName = await getProjectName();
    const snapshotDir = getSnapshotDir(projectName);

    const snapshots: Array<{
      name: string;
      created_at: string;
      body_count: number;
      sketch_count: number;
    }> = [];

    if (fs.existsSync(snapshotDir)) {
      const files = fs.readdirSync(snapshotDir);
      for (const filename of files) {
        if (filename.endsWith(".json")) {
          try {
            const filePath = path.join(snapshotDir, filename);
            const data = JSON.parse(fs.readFileSync(filePath, "utf-8"));
            const state = data.model_state || {};
            snapshots.push({
              name: data.name || filename.replace(".json", ""),
              created_at: data.created_at || "",
              body_count: state.body_count ?? 0,
              sketch_count: state.sketch_count ?? 0,
            });
          } catch {
            // Skip invalid files
          }
        }
      }
    }

    return {
      success: true,
      project_name: projectName,
      snapshots,
      snapshot_count: snapshots.length,
    };
  } catch (e) {
    return { success: false, error: String(e), snapshots: [] };
  }
}

/**
 * Attempt to restore model to a previous snapshot state using undo.
 *
 * WARNING: Fusion's undo is sequential - this will undo operations one by one
 * until the model state matches the snapshot (body_count and sketch_count).
 *
 * - Cannot skip forward in history
 * - Cannot restore if snapshot state requires more bodies/sketches than current
 * - May not perfectly restore all geometry details, only counts are verified
 */
export async function restore_snapshot(
  name: string,
  max_undo_steps: number = 50
): Promise<ToolResult> {
  try {
    const projectName = await getProjectName();
    const snapshotDir = getSnapshotDir(projectName);

    const safeName = sanitizeName(name);
    const filePath = path.join(snapshotDir, `${safeName}.json`);

    if (!fs.existsSync(filePath)) {
      return {
        success: false,
        error: `Snapshot '${name}' not found. Use list_snapshots() to see available.`,
      };
    }

    const snapshotData = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    const targetState = snapshotData.model_state || {};
    const targetBodyCount = targetState.body_count ?? 0;
    const targetSketchCount = targetState.sketch_count ?? 0;

    // Get current state
    let currentState = (await httpGet(`${BASE_URL}/get_model_state`, REQUEST_TIMEOUT)) as {
      body_count?: number;
      sketch_count?: number;
    };
    let currentBodyCount = currentState.body_count ?? 0;
    let currentSketchCount = currentState.sketch_count ?? 0;

    // Check if restoration is possible
    if (
      targetBodyCount > currentBodyCount ||
      targetSketchCount > currentSketchCount
    ) {
      return {
        success: false,
        error:
          "Cannot restore: snapshot has more bodies/sketches than current state. " +
          "Undo cannot add items, only remove them.",
        target_body_count: targetBodyCount,
        target_sketch_count: targetSketchCount,
        current_body_count: currentBodyCount,
        current_sketch_count: currentSketchCount,
      };
    }

    // Already at target state?
    if (
      currentBodyCount === targetBodyCount &&
      currentSketchCount === targetSketchCount
    ) {
      return {
        success: true,
        message: "Model is already at snapshot state",
        undo_count: 0,
        current_state: currentState,
      };
    }

    // Perform undo operations
    let undoCount = 0;

    for (let i = 0; i < max_undo_steps; i++) {
      await httpPost(`${BASE_URL}/undo`, {}, REQUEST_TIMEOUT);
      undoCount++;

      // Small delay for Fusion to process
      await sleep(100);

      // Check new state
      currentState = (await httpGet(`${BASE_URL}/get_model_state`, REQUEST_TIMEOUT)) as {
        body_count?: number;
        sketch_count?: number;
      };
      currentBodyCount = currentState.body_count ?? 0;
      currentSketchCount = currentState.sketch_count ?? 0;

      if (
        currentBodyCount === targetBodyCount &&
        currentSketchCount === targetSketchCount
      ) {
        return {
          success: true,
          message: `Restored to snapshot '${name}'`,
          undo_count: undoCount,
          current_state: currentState,
          warning:
            "Geometry details may differ - only body/sketch counts are verified.",
        };
      }

      // Went too far
      if (
        currentBodyCount < targetBodyCount ||
        currentSketchCount < targetSketchCount
      ) {
        return {
          success: false,
          error: "Undo went past target state. Snapshot may not be reachable.",
          undo_count: undoCount,
          current_state: currentState,
          target_body_count: targetBodyCount,
          target_sketch_count: targetSketchCount,
        };
      }
    }

    return {
      success: false,
      error: `Could not reach snapshot state after ${max_undo_steps} undo operations`,
      undo_count: undoCount,
      current_state: currentState,
    };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

/**
 * Delete a snapshot by name.
 */
export async function delete_snapshot(name: string): Promise<ToolResult> {
  try {
    const projectName = await getProjectName();
    const snapshotDir = getSnapshotDir(projectName);

    const safeName = sanitizeName(name);
    const filePath = path.join(snapshotDir, `${safeName}.json`);

    if (!fs.existsSync(filePath)) {
      return { success: false, error: `Snapshot '${name}' not found` };
    }

    fs.unlinkSync(filePath);

    return {
      success: true,
      message: `Snapshot '${name}' deleted successfully`,
    };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

// =============================================================================
// Test Tools - Local file-based implementation
// =============================================================================

/**
 * Save a validation test to disk for the current Fusion project.
 *
 * The script can use assertion helpers:
 * - assert_body_count(expected): Verify number of bodies
 * - assert_sketch_count(expected): Verify number of sketches
 * - assert_volume(body_index, expected_cm3, tolerance=0.1): Verify body volume
 * - assert_bounding_box(body_index, min_point, max_point, tolerance=0.1): Verify bounds
 */
export async function save_test(
  name: string,
  script: string,
  description: string = ""
): Promise<ToolResult> {
  try {
    const projectName = await getProjectName();
    const testDir = getTestDir(projectName);

    const safeName = sanitizeName(name);
    if (!safeName) {
      return { success: false, error: "Invalid test name" };
    }

    const testData = {
      name,
      description,
      script,
      project_name: projectName,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    const filePath = path.join(testDir, `${safeName}.json`);
    fs.writeFileSync(filePath, JSON.stringify(testData, null, 2));

    return {
      success: true,
      message: `Test '${name}' saved successfully`,
      file_path: filePath,
      project_name: projectName,
    };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

/**
 * List all saved tests for the current Fusion project.
 */
export async function load_tests(): Promise<ToolResult> {
  try {
    const projectName = await getProjectName();
    const testDir = getTestDir(projectName);

    const tests: Array<{
      name: string;
      description: string;
      created_at: string;
      file_path: string;
    }> = [];

    if (fs.existsSync(testDir)) {
      const files = fs.readdirSync(testDir);
      for (const filename of files) {
        if (filename.endsWith(".json") && !filename.startsWith("snapshot")) {
          try {
            const filePath = path.join(testDir, filename);
            const data = JSON.parse(fs.readFileSync(filePath, "utf-8"));
            // Skip if it's a snapshot file (inside snapshots folder should be excluded already)
            if (data.model_state) continue;
            tests.push({
              name: data.name || filename.replace(".json", ""),
              description: data.description || "",
              created_at: data.created_at || "",
              file_path: filePath,
            });
          } catch {
            // Skip invalid files
          }
        }
      }
    }

    return {
      success: true,
      project_name: projectName,
      tests,
      test_count: tests.length,
      test_dir: testDir,
    };
  } catch (e) {
    return { success: false, error: String(e), tests: [] };
  }
}

/**
 * Run validation tests for the current Fusion project.
 *
 * If name is provided, runs that specific test.
 * If name is omitted, runs ALL saved tests for the project.
 */
export async function run_tests(name?: string): Promise<ToolResult> {
  try {
    const projectName = await getProjectName();
    const testDir = getTestDir(projectName);

    // If specific test name provided, run just that test
    if (name) {
      return await runSingleTest(testDir, name);
    }

    // Run all tests
    const results: Array<{
      name: string;
      passed: boolean;
      error?: string;
      execution_time_ms: number;
      stdout?: string;
      error_line?: number;
    }> = [];
    let passedCount = 0;
    let failedCount = 0;
    const totalStartTime = Date.now();

    if (!fs.existsSync(testDir)) {
      return {
        success: true,
        project_name: projectName,
        total: 0,
        passed: 0,
        failed: 0,
        results: [],
        message: "No tests found for this project",
        total_execution_time_ms: 0,
      };
    }

    const testFiles = fs
      .readdirSync(testDir)
      .filter((f) => f.endsWith(".json") && !f.startsWith("snapshot"));

    for (const filename of testFiles.sort()) {
      const testName = filename.replace(".json", "");
      const result = await runSingleTest(testDir, testName);

      const testResult: (typeof results)[0] = {
        name: testName,
        passed: result.passed === true,
        error: result.error as string | undefined,
        execution_time_ms: (result.execution_time_ms as number) || 0,
      };

      if (result.passed) {
        passedCount++;
      } else {
        failedCount++;
        testResult.stdout = result.stdout as string | undefined;
        testResult.error_line = result.error_line as number | undefined;
      }

      results.push(testResult);
    }

    const totalExecutionTimeMs = Date.now() - totalStartTime;

    return {
      success: failedCount === 0,
      project_name: projectName,
      total: results.length,
      passed: passedCount,
      failed: failedCount,
      results,
      total_execution_time_ms: totalExecutionTimeMs,
    };
  } catch (e) {
    return {
      success: false,
      error: String(e),
      total: 0,
      passed: 0,
      failed: 0,
      results: [],
    };
  }
}

async function runSingleTest(
  testDir: string,
  name: string
): Promise<ToolResult> {
  const safeName = sanitizeName(name);
  const filePath = path.join(testDir, `${safeName}.json`);

  if (!fs.existsSync(filePath)) {
    return {
      success: false,
      test_name: name,
      passed: false,
      error: `Test '${name}' not found. Use load_tests() to see available tests.`,
    };
  }

  try {
    const testData = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    const script = testData.script;

    if (!script) {
      return {
        success: false,
        test_name: name,
        passed: false,
        error: "Test has no script defined",
      };
    }

    const startTime = Date.now();
    const result = await execute_fusion_script(script);
    const executionTimeMs = Date.now() - startTime;

    const passed = result.success === true;

    return {
      success: true,
      test_name: name,
      description: testData.description || "",
      passed,
      return_value: result.return_value,
      stdout: result.stdout,
      stderr: result.stderr,
      error: passed ? undefined : result.error,
      error_type: result.error_type,
      error_line: result.error_line,
      execution_time_ms: executionTimeMs,
      model_state: result.model_state,
    };
  } catch (e) {
    return {
      success: false,
      test_name: name,
      passed: false,
      error: String(e),
    };
  }
}

/**
 * Delete a saved test by name.
 */
export async function delete_test(name: string): Promise<ToolResult> {
  try {
    const projectName = await getProjectName();
    const testDir = getTestDir(projectName);

    const safeName = sanitizeName(name);
    const filePath = path.join(testDir, `${safeName}.json`);

    if (!fs.existsSync(filePath)) {
      return { success: false, error: `Test '${name}' not found` };
    }

    fs.unlinkSync(filePath);

    return {
      success: true,
      message: `Test '${name}' deleted successfully`,
    };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}
