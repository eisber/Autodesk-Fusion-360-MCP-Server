"""Scripting tools for Fusion 360 MCP Server.

Contains functions for executing arbitrary Python scripts in Fusion 360.
"""

import logging
import time
import traceback
import requests

from ..config import ENDPOINTS, HEADERS, SCRIPT_EXECUTION_TIMEOUT, SCRIPT_POLL_INTERVAL


def execute_fusion_script(script: str):
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
    
    Example Script:
    ```python
    # Create a box
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(5, 3, 0)
    )
    # Extrude
    profile = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    ext = extrudes.addSimple(profile, adsk.core.ValueInput.createByReal(2), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
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
        # Queue the script for execution
        endpoint = ENDPOINTS["execute_script"]
        response = requests.post(endpoint, json={"command": "execute_script", "script": script}, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Failed to queue script: {response.text}"}
        
        # Poll for result (script executes async in Fusion's main thread)
        result_endpoint = ENDPOINTS["script_result"]
        max_wait = SCRIPT_EXECUTION_TIMEOUT
        poll_interval = SCRIPT_POLL_INTERVAL
        waited = 0
        
        while waited < max_wait:
            time.sleep(poll_interval)
            waited += poll_interval
            
            result_response = requests.get(result_endpoint, timeout=10)
            if result_response.status_code == 200:
                result = result_response.json()
                # Check if execution completed (has success field)
                if "success" in result:
                    return result
        
        return {"success": False, "error": f"Script execution timed out after {max_wait} seconds"}
        
    except Exception as e:
        logging.error("Execute fusion script failed: %s", e)
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
