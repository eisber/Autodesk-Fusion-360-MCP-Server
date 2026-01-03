"""Scripting tools for Fusion 360 MCP Server.

Contains functions for executing arbitrary Python scripts in Fusion 360.
Uses SSE for real-time progress updates and eliminates timeout issues.
"""

import logging
import traceback

from ..config import ENDPOINTS, HEADERS
from ..telemetry import tracked_tool
from ..sse_client import submit_task_and_wait, cancel_task as sse_cancel_task


@tracked_tool
def execute_fusion_script(script: str, timeout: float = 300.0):
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
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(5, 3, 0)
    )
    
    progress(50, "Extruding...")
    
    # Extrude
    profile = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    ext = extrudes.addSimple(profile, adsk.core.ValueInput.createByReal(2), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    
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
    try:
        endpoint = ENDPOINTS["execute_script"]
        
        # Use SSE for streaming progress and results
        result = submit_task_and_wait(
            endpoint,
            {"command": "execute_script", "script": script},
            timeout=timeout,
            on_progress=lambda pct, msg: logging.debug("Script progress: %.1f%% - %s", pct, msg)
        )
        
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
