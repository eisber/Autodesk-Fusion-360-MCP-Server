"""Testing and validation tools for Fusion 360 MCP Server.

Contains functions for creating, running, and managing validation tests,
as well as snapshot/rollback capabilities for model state.
"""

import json
import logging
import os
import time
from datetime import datetime

import requests

from ..client import send_request
from ..config import ENDPOINTS, TEST_STORAGE_PATH
from ..telemetry import tracked_tool


def _get_project_name() -> str:
    """Get the current Fusion project name from model state."""
    try:
        endpoint = ENDPOINTS["model_state"]
        response = requests.get(endpoint, timeout=10)
        state: dict[str, str] = response.json()
        return str(state.get("design_name", "UnnamedProject"))
    except Exception as e:
        logging.warning("Could not get project name: %s. Using 'UnnamedProject'", e)
        return "UnnamedProject"


def _get_test_dir(project_name: str | None = None) -> str:
    """Get the test directory for the current project, creating it if needed."""
    if project_name is None:
        project_name = _get_project_name()

    # Sanitize project name for filesystem
    safe_name = "".join(c for c in project_name if c.isalnum() or c in (" ", "-", "_")).strip()
    if not safe_name:
        safe_name = "UnnamedProject"

    test_dir = os.path.join(TEST_STORAGE_PATH, safe_name)
    os.makedirs(test_dir, exist_ok=True)
    return test_dir


def _get_snapshot_dir(project_name: str | None = None) -> str:
    """Get the snapshot directory for the current project, creating it if needed."""
    test_dir = _get_test_dir(project_name)
    snapshot_dir = os.path.join(test_dir, "snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)
    return snapshot_dir


# =============================================================================
# Test Management Tools
# =============================================================================


@tracked_tool
def save_test(name: str, script: str, description: str = "") -> dict:
    """
    Save a validation test to disk for the current Fusion project.

    Tests are saved to: ~/Desktop/Fusion_Tests/{project_name}/{name}.json

    The script can use assertion helpers available in execute_fusion_script:
    - assert_body_count(expected): Verify number of bodies
    - assert_sketch_count(expected): Verify number of sketches
    - assert_volume(body_index, expected_cm3, tolerance=0.1): Verify body volume
    - assert_bounding_box(body_index, min_point, max_point, tolerance=0.1): Verify bounds

    Example script:
        '''
        # Create a box and verify
        assert_body_count(1)
        body = rootComp.bRepBodies.item(0)
        assert body.volume > 0, "Body should have positive volume"
        result = "Test passed"
        '''

    Args:
        name: Test name (used as filename, alphanumeric and underscores recommended)
        script: Python script with assertions to execute in Fusion
        description: Human-readable description of what the test validates

    Returns:
        Dictionary with save status and file path
    """
    try:
        project_name = _get_project_name()
        test_dir = _get_test_dir(project_name)

        # Sanitize test name
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        if not safe_name:
            return {"success": False, "error": "Invalid test name"}

        test_data = {
            "name": name,
            "description": description,
            "script": script,
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        file_path = os.path.join(test_dir, f"{safe_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2)

        return {
            "success": True,
            "message": f"Test '{name}' saved successfully",
            "file_path": file_path,
            "project_name": project_name,
        }

    except Exception as e:
        logging.error("Save test failed: %s", e)
        return {"success": False, "error": str(e)}


@tracked_tool
def load_tests() -> dict:
    """
    List all saved tests for the current Fusion project.

    Returns:
        Dictionary with:
        - success: True/False
        - project_name: Current project name
        - tests: List of test metadata (name, description, created_at)
        - test_dir: Path to test directory
    """
    try:
        project_name = _get_project_name()
        test_dir = _get_test_dir(project_name)

        tests = []
        for filename in os.listdir(test_dir):
            if filename.endswith(".json") and not filename.startswith("snapshot_"):
                file_path = os.path.join(test_dir, filename)
                try:
                    with open(file_path, encoding="utf-8") as f:
                        test_data = json.load(f)
                        tests.append(
                            {
                                "name": test_data.get("name", filename[:-5]),
                                "description": test_data.get("description", ""),
                                "created_at": test_data.get("created_at", ""),
                                "file_path": file_path,
                            }
                        )
                except (OSError, json.JSONDecodeError) as e:
                    logging.warning("Could not load test %s: %s", filename, e)

        return {
            "success": True,
            "project_name": project_name,
            "tests": tests,
            "test_count": len(tests),
            "test_dir": test_dir,
        }

    except Exception as e:
        logging.error("Load tests failed: %s", e)
        return {"success": False, "error": str(e), "tests": []}


@tracked_tool
def run_tests(name: str | None = None) -> dict:
    """
    Run validation tests for the current Fusion project.

    If name is provided, runs that specific test.
    If name is omitted, runs ALL saved tests for the project.

    Args:
        name: Name of specific test to run (optional, omit to run all)

    Returns:
        If running single test:
        - success: True if test passed, False if failed or error
        - test_name: Name of the test
        - passed: True/False based on script execution
        - return_value: Value of 'result' variable from script
        - stdout: Print outputs from script
        - error: Error message if test failed
        - execution_time_ms: How long the test took
        - model_state: Model state after test execution

        If running all tests:
        - success: True if all tests passed
        - project_name: Current project name
        - total: Total number of tests
        - passed: Number of tests that passed
        - failed: Number of tests that failed
        - results: List of individual test results
        - total_execution_time_ms: Total time for all tests
    """
    # If no name provided, run all tests
    if name is None:
        return _run_all_tests_impl()

    # Otherwise run specific test
    return _run_single_test_impl(name)


def _run_single_test_impl(name: str) -> dict:
    """Internal implementation for running a single test."""
    try:
        project_name = _get_project_name()
        test_dir = _get_test_dir(project_name)

        # Sanitize and find test file
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        file_path = os.path.join(test_dir, f"{safe_name}.json")

        if not os.path.exists(file_path):
            return {
                "success": False,
                "test_name": name,
                "passed": False,
                "error": f"Test '{name}' not found. Use load_tests() to see available tests.",
            }

        with open(file_path, encoding="utf-8") as f:
            test_data = json.load(f)

        script = test_data.get("script", "")
        if not script:
            return {
                "success": False,
                "test_name": name,
                "passed": False,
                "error": "Test has no script defined",
            }

        # Execute the script via Fusion
        start_time = time.time()

        from .scripting import _execute_script_sync

        result = _execute_script_sync(script)

        execution_time_ms = int((time.time() - start_time) * 1000)

        passed = result.get("success", False)

        return {
            "success": True,
            "test_name": name,
            "description": test_data.get("description", ""),
            "passed": passed,
            "return_value": result.get("return_value"),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "error": result.get("error") if not passed else None,
            "error_type": result.get("error_type"),
            "error_line": result.get("error_line"),
            "execution_time_ms": execution_time_ms,
            "model_state": result.get("model_state"),
        }

    except Exception as e:
        logging.error("Run test failed: %s", e)
        return {
            "success": False,
            "test_name": name,
            "passed": False,
            "error": str(e),
        }


def _run_all_tests_impl() -> dict:
    """Internal implementation for running all tests."""
    try:
        project_name = _get_project_name()
        test_dir = _get_test_dir(project_name)

        results = []
        passed_count = 0
        failed_count = 0
        total_start_time = time.time()

        # Get all test files
        test_files = [
            f for f in os.listdir(test_dir) if f.endswith(".json") and not f.startswith("snapshot_")
        ]

        if not test_files:
            return {
                "success": True,
                "project_name": project_name,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "results": [],
                "message": "No tests found for this project",
                "total_execution_time_ms": 0,
            }

        for filename in sorted(test_files):
            test_name = filename[:-5]  # Remove .json
            result = _run_single_test_impl(test_name)

            test_result = {
                "name": test_name,
                "passed": result.get("passed", False),
                "error": result.get("error"),
                "execution_time_ms": result.get("execution_time_ms", 0),
            }

            if result.get("passed"):
                passed_count += 1
            else:
                failed_count += 1
                # Include more detail for failed tests
                test_result["stdout"] = result.get("stdout", "")
                test_result["error_line"] = result.get("error_line")

            results.append(test_result)

        total_execution_time_ms = int((time.time() - total_start_time) * 1000)

        return {
            "success": failed_count == 0,
            "project_name": project_name,
            "total": len(results),
            "passed": passed_count,
            "failed": failed_count,
            "results": results,
            "total_execution_time_ms": total_execution_time_ms,
        }

    except Exception as e:
        logging.error("Run all tests failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "total": 0,
            "passed": 0,
            "failed": 0,
            "results": [],
        }


@tracked_tool
def delete_test(name: str) -> dict:
    """
    Delete a saved test by name.

    Args:
        name: Name of the test to delete

    Returns:
        Dictionary with success status
    """
    try:
        project_name = _get_project_name()
        test_dir = _get_test_dir(project_name)

        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        file_path = os.path.join(test_dir, f"{safe_name}.json")

        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"Test '{name}' not found",
            }

        os.remove(file_path)

        return {
            "success": True,
            "message": f"Test '{name}' deleted successfully",
        }

    except Exception as e:
        logging.error("Delete test failed: %s", e)
        return {"success": False, "error": str(e)}


# =============================================================================
# Snapshot/Rollback Tools
# =============================================================================


@tracked_tool
def create_snapshot(name: str) -> dict:
    """
    Create a snapshot of the current model state.

    Snapshots capture body_count, sketch_count, and body details (volumes, bounding boxes).
    Use this BEFORE making changes to enable rollback verification.

    Args:
        name: Name for the snapshot (alphanumeric and underscores recommended)

    Returns:
        Dictionary with snapshot details and file path
    """
    try:
        project_name = _get_project_name()
        snapshot_dir = _get_snapshot_dir(project_name)

        # Get current model state
        endpoint = ENDPOINTS["model_state"]
        response = requests.get(endpoint, timeout=10)
        model_state = response.json()

        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        if not safe_name:
            return {"success": False, "error": "Invalid snapshot name"}

        snapshot_data = {
            "name": name,
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "model_state": model_state,
        }

        file_path = os.path.join(snapshot_dir, f"{safe_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=2)

        return {
            "success": True,
            "message": f"Snapshot '{name}' created",
            "file_path": file_path,
            "body_count": model_state.get("body_count", 0),
            "sketch_count": model_state.get("sketch_count", 0),
        }

    except Exception as e:
        logging.error("Create snapshot failed: %s", e)
        return {"success": False, "error": str(e)}


@tracked_tool
def list_snapshots() -> dict:
    """
    List all snapshots for the current Fusion project.

    Returns:
        Dictionary with list of snapshot metadata
    """
    try:
        project_name = _get_project_name()
        snapshot_dir = _get_snapshot_dir(project_name)

        snapshots = []
        if os.path.exists(snapshot_dir):
            for filename in os.listdir(snapshot_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(snapshot_dir, filename)
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            data = json.load(f)
                            state = data.get("model_state", {})
                            snapshots.append(
                                {
                                    "name": data.get("name", filename[:-5]),
                                    "created_at": data.get("created_at", ""),
                                    "body_count": state.get("body_count", 0),
                                    "sketch_count": state.get("sketch_count", 0),
                                }
                            )
                    except (OSError, json.JSONDecodeError) as e:
                        logging.warning("Could not load snapshot %s: %s", filename, e)

        return {
            "success": True,
            "project_name": project_name,
            "snapshots": snapshots,
            "snapshot_count": len(snapshots),
        }

    except Exception as e:
        logging.error("List snapshots failed: %s", e)
        return {"success": False, "error": str(e), "snapshots": []}


@tracked_tool
def restore_snapshot(name: str, max_undo_steps: int = 50) -> dict:
    """
    Attempt to restore model to a previous snapshot state using undo.

    **WARNING**: Fusion's undo is sequential - this will undo operations one by one
    until the model state matches the snapshot (body_count and sketch_count).

    - Cannot skip forward in history
    - Cannot restore if snapshot state requires more bodies/sketches than current
    - May not perfectly restore all geometry details, only counts are verified

    Args:
        name: Name of the snapshot to restore
        max_undo_steps: Maximum undo operations to attempt (default 50)

    Returns:
        Dictionary with:
        - success: True if state was restored
        - undo_count: Number of undo operations performed
        - warning: Any warnings about limitations
        - current_state: Model state after restore attempt
    """
    try:
        project_name = _get_project_name()
        snapshot_dir = _get_snapshot_dir(project_name)

        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        file_path = os.path.join(snapshot_dir, f"{safe_name}.json")

        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"Snapshot '{name}' not found. Use list_snapshots() to see available.",
            }

        with open(file_path, encoding="utf-8") as f:
            snapshot_data = json.load(f)

        target_state = snapshot_data.get("model_state", {})
        target_body_count = target_state.get("body_count", 0)
        target_sketch_count = target_state.get("sketch_count", 0)

        # Get current state
        endpoint = ENDPOINTS["model_state"]
        response = requests.get(endpoint, timeout=10)
        current_state = response.json()
        current_body_count = current_state.get("body_count", 0)
        current_sketch_count = current_state.get("sketch_count", 0)

        # Check if restoration is possible
        if target_body_count > current_body_count or target_sketch_count > current_sketch_count:
            return {
                "success": False,
                "error": "Cannot restore: snapshot has more bodies/sketches than current state. "
                "Undo cannot add items, only remove them.",
                "target_body_count": target_body_count,
                "target_sketch_count": target_sketch_count,
                "current_body_count": current_body_count,
                "current_sketch_count": current_sketch_count,
            }

        # Already at target state?
        if current_body_count == target_body_count and current_sketch_count == target_sketch_count:
            return {
                "success": True,
                "message": "Model is already at snapshot state",
                "undo_count": 0,
                "current_state": current_state,
            }

        # Perform undo operations
        undo_endpoint = ENDPOINTS["undo"]
        undo_count = 0

        for _ in range(max_undo_steps):
            send_request(undo_endpoint, {"command": "undo"}, {})
            undo_count += 1

            # Small delay for Fusion to process
            time.sleep(0.1)

            # Check new state
            response = requests.get(endpoint, timeout=10)
            current_state = response.json()
            current_body_count = current_state.get("body_count", 0)
            current_sketch_count = current_state.get("sketch_count", 0)

            if (
                current_body_count == target_body_count
                and current_sketch_count == target_sketch_count
            ):
                return {
                    "success": True,
                    "message": f"Restored to snapshot '{name}'",
                    "undo_count": undo_count,
                    "current_state": current_state,
                    "warning": "Geometry details may differ - only body/sketch counts are verified.",
                }

            # Went too far
            if current_body_count < target_body_count or current_sketch_count < target_sketch_count:
                return {
                    "success": False,
                    "error": "Undo went past target state. Snapshot may not be reachable.",
                    "undo_count": undo_count,
                    "current_state": current_state,
                    "target_body_count": target_body_count,
                    "target_sketch_count": target_sketch_count,
                }

        return {
            "success": False,
            "error": f"Could not reach snapshot state after {max_undo_steps} undo operations",
            "undo_count": undo_count,
            "current_state": current_state,
        }

    except Exception as e:
        logging.error("Restore snapshot failed: %s", e)
        return {"success": False, "error": str(e)}


@tracked_tool
def delete_snapshot(name: str) -> dict:
    """
    Delete a snapshot by name.

    Args:
        name: Name of the snapshot to delete

    Returns:
        Dictionary with success status
    """
    try:
        project_name = _get_project_name()
        snapshot_dir = _get_snapshot_dir(project_name)

        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        file_path = os.path.join(snapshot_dir, f"{safe_name}.json")

        if not os.path.exists(file_path):
            return {"success": False, "error": f"Snapshot '{name}' not found"}

        os.remove(file_path)
        return {"success": True, "message": f"Snapshot '{name}' deleted"}

    except Exception as e:
        logging.error("Delete snapshot failed: %s", e)
        return {"success": False, "error": str(e)}
