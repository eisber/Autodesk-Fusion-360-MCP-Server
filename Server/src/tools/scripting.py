"""Scripting tools for Fusion 360 MCP Server.

Contains functions for executing arbitrary Python scripts in Fusion 360.
Uses SSE for real-time progress updates and eliminates timeout issues.
"""

import asyncio
import logging
import traceback
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from ..config import ENDPOINTS
from ..sse_client import cancel_task as sse_cancel_task, submit_task_and_wait
from ..telemetry import tracked_tool

# Thread pool for running sync HTTP calls
_executor = ThreadPoolExecutor(max_workers=4)


def _execute_script_sync(
    script: str,
    timeout: float = 300.0,
    on_progress: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """
    Internal sync version of execute_fusion_script.

    Used by other tools that need to execute scripts synchronously.
    """
    try:
        endpoint = ENDPOINTS["execute_script"]
        result = submit_task_and_wait(
            endpoint,
            {"command": "execute_script", "script": script},
            timeout=timeout,
            on_progress=on_progress or (lambda pct, msg: None),
        )
        return result
    except Exception as e:
        logging.error("Execute fusion script failed: %s", e)
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@tracked_tool
async def execute_fusion_script(
    script: str, ctx: Context[ServerSession, Any], timeout: float = 300.0
):
    """
    Execute a Python script directly in Fusion 360.
    This is the most powerful tool - you can execute arbitrary Fusion 360 API code.

    Available variables in the script:
    - adsk: The Autodesk module
    - app: The Fusion 360 Application
    - ui: The User Interface
    - design: The active Design
    - rootComp: The Root Component
    - math: The math module
    - json: The json module
    - progress(percent, message): Report progress (0-100)
    - is_cancelled(): Check if task was cancelled

    Example Script:
    ```python
    progress(0, "Starting...")

    # Create a box
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(5, 3, 0)
    )

    progress(50, "Extruding...")

    # Extrude
    profile = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    ext = extrudes.addSimple(
        profile,
        adsk.core.ValueInput.createByReal(2),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )

    progress(100, "Done!")
    result = f"Created body: {ext.bodies.item(0).name}"
    ```

    Set a variable 'result' to return a value.

    Returns:
    - success: True/False
    - return_value: Value of the 'result' variable (if set)
    - stdout: Print outputs
    - stderr: Error outputs
    - error: Error message (if failed)
    - error_type: Type of error (SyntaxError, RuntimeError, etc.)
    - error_line: Line number of error
    - traceback: Full traceback
    - model_state: Model state after execution
    """

    # Progress callback that reports to MCP via the context
    async def report_progress(percent: float, message: str):
        """Report progress to MCP client."""
        logging.info("MCP Progress: %.0f%% - %s", percent, message)
        try:
            await ctx.report_progress(
                progress=percent / 100.0,  # MCP uses 0.0-1.0
                total=1.0,
                message=message,
            )
            await ctx.info(f"Progress: {percent:.0f}% - {message}")
        except Exception as e:
            logging.warning("Progress report to MCP failed: %s", e)

    # Sync progress wrapper for the sync SSE client
    progress_queue: asyncio.Queue[tuple[float, str]] = asyncio.Queue()

    def sync_on_progress(percent: float, message: str):
        """Sync callback that queues progress for async reporting."""
        try:
            progress_queue.put_nowait((percent, message))
        except asyncio.QueueFull:
            pass  # Drop if queue full

    try:
        endpoint = ENDPOINTS["execute_script"]

        # Run the sync HTTP call in thread pool, but process progress async
        loop = asyncio.get_event_loop()

        async def run_with_progress():
            """Run the task while processing progress updates."""
            # Start the sync task in executor
            future = loop.run_in_executor(
                _executor,
                lambda: submit_task_and_wait(
                    endpoint,
                    {"command": "execute_script", "script": script},
                    timeout=timeout,
                    on_progress=sync_on_progress,
                ),
            )

            # Process progress updates while waiting for completion
            while not future.done():
                try:
                    # Check for progress updates
                    percent, message = await asyncio.wait_for(
                        progress_queue.get(), timeout=0.1
                    )
                    await report_progress(percent, message)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logging.debug("Progress processing error: %s", e)

            # Drain any remaining progress updates
            while not progress_queue.empty():
                try:
                    percent, message = progress_queue.get_nowait()
                    await report_progress(percent, message)
                except asyncio.QueueEmpty:
                    break

            return await future

        result = await run_with_progress()
        return result

    except Exception as e:
        logging.error("Execute fusion script failed: %s", e)
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@tracked_tool
def cancel_fusion_task(task_id: str):
    """
    Cancel a running task in Fusion 360.

    Use this to stop long-running operations like complex scripts or exports.

    Args:
        task_id: The ID of the task to cancel (returned when task was submitted)

    Returns:
        - success: True if task was cancelled
        - error: Error message if cancellation failed
    """
    try:
        return sse_cancel_task(task_id)
    except Exception as e:
        logging.error("Cancel task failed: %s", e)
        return {"success": False, "error": str(e)}
