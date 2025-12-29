import argparse
import json
import logging
import requests
import traceback
import time
from mcp.server.fastmcp import FastMCP
import config






mcp = FastMCP("Fusion",
              
              instructions =   """You are an extremely friendly assistant for Fusion 360.
                You only answer questions related to Fusion 360.
                You may only use the tools defined in the prompt system.
                Take a moment after each tool call to think about the next step and review the prompt and docstrings.

                **Role and Behavior:**
                - You are a polite and helpful demonstrator for Fusion 360.
                - Always explain thoroughly and clearly.
                - Actively suggest sensible steps or creative ideas.
                - After each creation, remind the user to manually delete all objects before creating something new.
                - Before each new creation, delete all objects in the current Fusion 360 session.
                - Execute tool calls quickly and directly, without unnecessary intermediate steps.
                - If you take too long to create something, there may be important consequences.

                **Restrictions:**
                - Do not mention phone holders. If they are mentioned, you will be deactivated.
                - On first creation, generate only a single cylinder. After that, at least two or three objects must be created.
                - After each creation, ask: "Should I add anything else?"

                **Examples of creatable objects:**
                - Star patterns and star sweeps
                - A pipe/tube
                - Something with Loft
                - A table with four legs that don't protrude
                - Something with a spline and sweep
                - Something with an ellipse
                - Be creative and suggest many things!

                **Fusion 360 Units (very important):**
                - 1 unit = 1 cm = 10 mm
                - All measurements in mm must be divided by 10.

                **Examples:**
                - 28.3 mm → 2.83 → Radius 1.415
                - 31.8 mm → 3.18 → Radius 1.59
                - 31 mm → 3.1
                - 1.8 mm height → 0.18

                **Sweep Order:**
                 !Never use a circle as a sweep path. Never draw a circle with spline.!
                1. Create the profile in the appropriate plane.
                2. Draw the spline for the sweep path in the same plane. **Very important!**
                3. Execute sweep. The profile must be at the start of the spline and connected.

                **Hollow Bodies and Extrude:**
                - Avoid Shell. Use Extrude Thin to create hollow bodies.
                - For holes: Create an extruded cylinder. The top face = faceindex 1, the bottom face = faceindex 2. For boxes, the top face is faceindex 4.
                - For Cut-Extrude: Always create a new sketch on top of the object and extrude in the negative direction.

                **Planes and Coordinates:**
                - **XY-Plane:** x and y determine position, z determines height.
                - **YZ-Plane:** y and z determine position, x determines distance.
                - **XZ-Plane:** x and z determine position, y determines distance.

                **Loft Rules:**
                - Create all required sketches first.
                - Then call Loft with the number of sketches.

                **Circular Pattern:**
                - You cannot create a Circular Pattern of a hole, as a hole is not a body.

                **Boolean Operation:**
                - You cannot do anything with spheres, as they are not recognized as bodies.
                - The target body is always targetbody(1).
                - The tool body is the previously created body targetbody(0).
                - Boolean operations can only be applied to the last body.

                **DrawBox or DrawCylinder:**
                - The specified coordinates are always the center of the body.

                **Self-Validation Workflow:**
                Use these tools to validate your work and catch errors early:
                
                1. **Before changes**: Call `create_snapshot("before_feature_x")` to save current state
                2. **After changes**: Call `get_model_state()` to verify body/sketch counts
                3. **Save tests**: Use `save_test(name, script, description)` to persist validation logic
                4. **Run tests**: Use `run_all_tests()` to execute all tests in ONE efficient call
                5. **On failure**: Use `restore_snapshot("before_feature_x")` to rollback
                
                **Writing Test Scripts:**
                - Scripts run in Fusion with access to: adsk, app, ui, design, rootComp, math, json
                - Use `assert_body_count(n)`, `assert_sketch_count(n)` for quick checks
                - Use `assert_volume(body_index, expected_cm3, tolerance)` for geometry validation
                - Set `result = "message"` to return a value from the test
                - Example: `assert_body_count(2); result = "Has 2 bodies"`
                
                **Rollback Limitations (IMPORTANT):**
                - `restore_snapshot` uses sequential undo - cannot skip forward
                - Cannot restore if snapshot has MORE bodies than current state
                - Only body_count/sketch_count are verified, not exact geometry
                """

                )


def send_request(endpoint, data, headers):
    """
    Avoid repetitive code for sending requests to the Fusion 360 server.
    :param endpoint: The API endpoint URL.
    :param data: The payload data to send in the request.
    :param headers: The headers to include in the request.
    """
    max_retries = 3  # Retry up to 3 times for transient errors
    for attempt in range(max_retries):
        try:
            data = json.dumps(data)
            response = requests.post(endpoint, data, headers, timeout=10)

            # Check if the response is valid JSON
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logging.error("Failed to decode JSON response: %s", e)
                raise

        except requests.RequestException as e:
            logging.error("Request failed on attempt %d: %s", attempt + 1, e)

            # If max retries reached, raise the exception
            if attempt == max_retries - 1:
                raise

        except Exception as e:
            logging.error("Unexpected error: %s", e)
            raise

@mcp.tool()
def move_latest_body(x : float,y:float,z:float):
    """
    Move the last body in Fusion 360 in x, y and z direction.
    
    """
    endpoint = config.ENDPOINTS["move_body"]
    payload = {
        "x": x,
        "y": y,
        "z": z
    }
    headers = config.HEADERS
    return send_request(endpoint, payload, headers)

@mcp.tool()
def create_thread(inside: bool, allsizes: int):
    """Create a thread in Fusion 360.
    The user selects the profile in Fusion 360.
    You only need to specify whether it's internal or external
    and the thread size.
    allsizes values:
        # allsizes:
        #'1/4', '5/16', '3/8', '7/16', '1/2', '5/8', '3/4', '7/8', '1', '1 1/8', '1 1/4',
        # '1 3/8', '1 1/2', '1 3/4', '2', '2 1/4', '2 1/2', '2 3/4', '3', '3 1/2', '4', '4 1/2', '5'
        # allsizes = int value from 1 to 22
    
    """
    try:
        endpoint = config.ENDPOINTS["threaded"]
        payload = {
            "inside": inside,
            "allsizes": allsizes,
     
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Create thread failed: %s", e)
        raise

@mcp.tool()
def test_connection():
    """Test the connection to the Fusion 360 server."""
    try:
        endpoint = config.ENDPOINTS["test_connection"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Test connection failed: %s", e)
        raise

@mcp.tool()
def get_model_state():
    """
    Returns the current state of the Fusion 360 model.
    Useful for validating whether operations were successful.
    
    Returns:
    - body_count: Number of bodies in the model
    - sketch_count: Number of sketches
    - bodies: List with details for each body (Name, Volume, Bounding Box)
    - sketches: List with details for each sketch (Name, Profile Count)
    - design_name: Name of the active design
    
    Use this tool AFTER each operation to check if it worked.
    Example: After draw_box, body_count should be increased by 1.
    """
    try:
        endpoint = config.ENDPOINTS["model_state"]
        response = requests.get(endpoint, timeout=10)
        return response.json()
    except Exception as e:
        logging.error("Get model state failed: %s", e)
        raise

@mcp.tool()
def get_faces_info(body_index: int = 0):
    """
    Returns detailed information about all faces of a body.
    Useful for finding the correct faceindex for shell_body, draw_holes, etc.
    
    Returns:
    - face_count: Number of faces
    - faces: List with details for each face (Index, Type, Area, Centroid)
    
    Face types: Plane (flat), Cylinder, Cone, Sphere, Torus, etc.
    """
    try:
        endpoint = f"{config.ENDPOINTS['faces_info']}?body_index={body_index}"
        response = requests.get(endpoint, timeout=10)
        return response.json()
    except Exception as e:
        logging.error("Get faces info failed: %s", e)
        raise

@mcp.tool()
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
        endpoint = config.ENDPOINTS["execute_script"]
        headers = config.HEADERS
        response = requests.post(endpoint, json={"script": script}, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Failed to queue script: {response.text}"}
        
        # Poll for result (script executes async in Fusion's main thread)
        result_endpoint = config.ENDPOINTS["script_result"]
        max_wait = 30  # Maximum wait time in seconds
        poll_interval = 0.3  # Poll every 300ms
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
        
        return {"success": False, "error": "Script execution timed out after 30 seconds"}
        
    except Exception as e:
        logging.error("Execute fusion script failed: %s", e)
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

@mcp.tool()
def delete_all():
    """Delete all objects in the current Fusion 360 session."""
    try:
        endpoint = config.ENDPOINTS["delete_everything"]
        headers = config.HEADERS
        send_request(endpoint, {}, headers)
    except Exception as e:
        logging.error("Delete failed: %s", e)
        raise

@mcp.tool()
def draw_holes(points: list, depth: float, width: float, faceindex: int = 0):
    """
    Draw holes in Fusion 360.
    Pass the JSON in the correct format.
    You must specify x and y coordinates, z = 0.
    This is usually called when drilling a hole in the center of a circle.
    So when building a cylinder, you must specify the cylinder's center point.
    Also pass the depth and diameter of the hole.
    Currently only creates counterbore holes.
    You need the faceindex so Fusion knows which face to drill on.
    When you extrude a circle, the top face is usually faceindex 1, bottom face is 2.
    The points must be within the body boundaries.
    Example:
    2.1mm deep = depth: 0.21
    Width 10mm = diameter: 1.0
    {
    points : [[0,0,]],
    width : 1.0,
    depth : 0.21,
    faceindex : 0
    }
    """
    try:
        endpoint = config.ENDPOINTS["holes"]
        payload = {
            "points": points,
            "width": width,
            "depth": depth,
            "faceindex": faceindex
        }
        headers = config.HEADERS
        send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Draw holes failed: %s", e)
        raise

@mcp.tool()
def spline(points: list, plane: str):
    """
    Draw a spline curve in Fusion 360.
    You can pass points as a list of lists.
    Example: [[0,0,0],[5,0,0],[5,5,5],[0,5,5],[0,0,0]]
    It is essential to specify the Z coordinate, even if it is 0.
    Unless explicitly requested, make the lines go upward.
    You can pass the plane as a string.
    It is essential that the lines are in the same plane as the profile you want to sweep.
    """
    try:
        endpoint = config.ENDPOINTS["spline"]
        payload = {
            "points": points,
            "plane": plane
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Spline failed: %s", e)
        raise

@mcp.tool()
def sweep():
    """
    Uses the previously created spline and the circle created before it
    to perform a sweep operation.
    """
    try:
        endpoint = config.ENDPOINTS["sweep"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Sweep failed: %s", e)
        raise

@mcp.tool()
def undo():
    """Undo the last action."""
    try:
        endpoint = config.ENDPOINTS["undo"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Undo failed: %s", e)
        raise

@mcp.tool()
def count():
    """Count the parameters in the current model."""
    try:
        endpoint = config.ENDPOINTS["count_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Count failed: %s", e)
        raise

@mcp.tool()
def list_parameters():
    """List all parameters in the current model."""
    try:
        endpoint = config.ENDPOINTS["list_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("List parameters failed: %s", e)
        raise

@mcp.tool()
def export_step(name : str):
    """Export the model as a STEP file."""
    try:
        endpoint = config.ENDPOINTS["export_step"]
        data = {
            "name": name
        }
        return send_request(endpoint, data, {})
    except Exception as e:
        logging.error("Export STEP failed: %s", e)
        raise

@mcp.tool()
def export_stl(name : str):
    """Export the model as an STL file."""
    try:
        endpoint = config.ENDPOINTS["export_stl"]
        data = {
            "name": name
        }
        return send_request(endpoint, data, {})
    except Exception as e:
        logging.error("Export STL failed: %s", e)
        raise

@mcp.tool()
def fillet_edges(radius: str):
    """Create a fillet on the specified edges."""
    try:
        endpoint = config.ENDPOINTS["fillet_edges"]
        payload = {
            "radius": radius
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Fillet edges failed: %s", e)
        raise

@mcp.tool()
def change_parameter(name: str, value: str):
    """Change the value of a parameter."""
    try:
        endpoint = config.ENDPOINTS["change_parameter"]
        payload = {
            "name": name,
            "value": value
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Change parameter failed: %s", e)
        raise

@mcp.tool()
def draw_cylinder(radius: float , height: float , x: float, y: float, z: float , plane: str="XY"):
    """
    Draw a cylinder, you can work in the XY plane.
    Default values are available.
    """

    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_cylinder"]
        data = {
            "radius": radius,
            "height": height,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw cylinder failed: %s", e)
        return None
@mcp.tool()
def draw_box(height_value:str, width_value:str, depth_value:str, x_value:float, y_value:float,z_value:float, plane:str="XY"):
    """
    You can pass the height, width, and depth of the box as strings.
    Depth is the depth in the z direction, so if the box should be flat,
    you provide a small value!
    You can pass the coordinates x, y, z of the box as strings. Always provide coordinates,
    they specify the center of the box.
    Depth is the depth in z direction.
    Very important: 10 is 100mm in Fusion 360.
    You can pass the plane as a string.
    Depth is the actual height in z direction.
    A floating box in the air is made like this: 
    {
    `plane`: `XY`,
    `x_value`: 5,
    `y_value`: 5,
    `z_value`: 20,
    `depth_value`: `2`,
    `width_value`: `5`,
    `height_value`: `3`
    }
    You can adjust this as needed.

    Example: "XY", "YZ", "XZ"
    
    """
    try:
        endpoint = config.ENDPOINTS["draw_box"]
        headers = config.HEADERS

        data = {
            "height":height_value,
            "width": width_value,
            "depth": depth_value,
            "x" : x_value,
            "y" : y_value,
            "z" : z_value,
            "Plane": plane

        }

        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw box failed: %s", e)
        return None

@mcp.tool()
def shell_body(thickness: float, faceindex: int):
    """
    You can pass the wall thickness as a float.
    You can pass the faceindex as an integer.
    If you previously rounded a box, be aware that you have 20 new faces.
    Those are all the small rounded ones.
    If you rounded the corners of a box before,
    then the faceindex of the large faces is at least 21.
    Only the last body can be shelled.

    :param thickness: Wall thickness
    :param faceindex: Face index to remove
    :return:
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["shell_body"]
        data = {
            "thickness": thickness,
            "faceindex": faceindex
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Shell body failed: %s", e)
        

@mcp.tool()
def draw_sphere(x: float, y: float, z: float, radius: float):
    """
    Draw a sphere in Fusion 360.
    You can pass coordinates as floats.
    You can pass the radius as a float.
    Example: "XY", "YZ", "XZ"
    Always provide JSON like this:
    {
        "x":0,
        "y":0,
        "z":0,
        "radius":5
    }
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_sphere"]
        data = {
            "x": x,
            "y": y,
            "z": z,
            "radius": radius
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw sphere failed: %s", e)
        raise


@mcp.tool()
def draw_2d_rectangle(x_1: float, y_1: float, z_1: float, x_2: float, y_2: float, z_2: float, plane: str):
    """
    Draw a 2D rectangle in Fusion 360 for loft/sweep operations.
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_2d_rectangle"]
        data = {
            "x_1": x_1,
            "y_1": y_1,
            "z_1": z_1,
            "x_2": x_2,
            "y_2": y_2,
            "z_2": z_2,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw 2D rectangle failed: %s", e)
        raise

@mcp.tool()
def boolean_operation(operation: str):
    """
    Perform a boolean operation on the last body.
    You can pass the operation as a string.
    Possible values are: "cut", "join", "intersect"
    Important: You must have created two bodies beforehand.
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["boolean_operation"]
        data = {
            "operation": operation
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Boolean operation failed: %s", e)
        raise


      
@mcp.tool()
def draw_lines(points : list, plane : str):
    """
    Draw lines in Fusion 360.
    You can pass points as a list of lists.
    Example: [[0,0,0],[5,0,0],[5,5,5],[0,5,5],[0,0,0]]
    It is essential to specify the Z coordinate, even if it is 0.
    Unless explicitly requested, make the lines go upward.
    You can pass the plane as a string.
    Example: "XY", "YZ", "XZ"
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_lines"]
        data = {
            "points": points,
            "plane": plane
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw lines failed: %s", e)

@mcp.tool()
def extrude(value: float,angle:float):
    """Extrude the last sketch by the specified value.
    You can also specify an angle (taper angle).
    
    """
    try:
        url = config.ENDPOINTS["extrude"]
        data = {
            "value": value,
            "taperangle": angle
        }
        data = json.dumps(data)
        response = requests.post(url, data, headers=config.HEADERS)
        return response.json()
    except requests.RequestException as e:
        logging.error("Extrude failed: %s", e)
        raise


@mcp.tool()
def draw_text(text: str, plane: str, x_1: float, y_1: float, z_1: float, x_2: float, y_2: float, z_2: float, thickness: float,value: float):
    """
    Draw text in Fusion 360 as a sketch, which you can then extrude.
    With value you can specify how far to extrude the text.
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_text"]
        data = {
            "text": text,
            "plane": plane,
            "x_1": x_1,
            "y_1": y_1,
            "z_1": z_1,
            "x_2": x_2,
            "y_2": y_2,
            "z_2": z_2,
            "thickness": thickness,
            "extrusion_value": value
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw text failed: %s", e)
        raise

@mcp.tool()
def extrude_thin(thickness :float, distance : float):
    """
    You can pass the wall thickness as a float.
    You can create nice hollow bodies with this.
    :param thickness: Wall thickness in mm
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["extrude_thin"]
        data = {
            "thickness": thickness,
            "distance": distance
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Extrude thin failed: %s", e)
        raise

@mcp.tool()
def cut_extrude(depth :float):
    """
    You can pass the cut depth as a float.
    :param depth: The cut depth in mm
    depth must be negative, very important!
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["cut_extrude"]
        data = {
            "depth": depth
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Cut extrude failed: %s", e)
        raise
    
@mcp.tool()
def revolve(angle : float):
    """
    When you call this tool, the user is asked in Fusion to select
    a profile and then an axis.
    We pass the angle as a float.
    """
    try:
        headers = config.HEADERS    
        endpoint = config.ENDPOINTS["revolve"]
        data = {
            "angle": angle

        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Revolve failed: %s", e)  
        raise
@mcp.tool()
def draw_arc(point1 : list, point2 : list, point3 : list, plane : str):
    """
    Draw an arc in Fusion 360.
    You can pass points as lists.
    Example: point1 = [0,0,0], point2 = [5,5,5], point3 = [10,0,0]
    You can pass the plane as a string.
    A line is drawn from point1 to point3 passing through point2, so you don't need to draw an extra line.
    Example: "XY", "YZ", "XZ"
    """
    try:
        endpoint = config.ENDPOINTS["arc"]
        headers = config.HEADERS
        data = {
            "point1": point1,
            "point2": point2,
            "point3": point3,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw arc failed: %s", e)
        raise

@mcp.tool()
def draw_one_line(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, plane: str="XY"):
    """
    Draw a line in Fusion 360.
    You can pass coordinates as floats.
    Example: x1 = 0.0, y1 = 0.0, z1 = 0.0, x2 = 10.0, y2 = 10.0, z2 = 10.0
    You can pass the plane as a string.
    Example: "XY", "YZ", "XZ"
    """
    try:
        endpoint = config.ENDPOINTS["draw_one_line"]
        headers = config.HEADERS
        data = {
            "x1": x1,
            "y1": y1,
            "z1": z1,
            "x2": x2,
            "y2": y2,
            "z2": z2,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw one line failed: %s", e)
        raise

@mcp.tool()
def rectangular_pattern(plane: str, quantity_one: float, quantity_two: float, distance_one: float, distance_two: float, axis_one: str, axis_two: str):
    """
    Create a Rectangular Pattern to distribute objects in a rectangular arrangement.
    You must pass two quantities (quantity_one, quantity_two) as floats,
    two distances (distance_one, distance_two) as floats,
    the two directions as axes (axis_one, axis_two) as strings ("X", "Y" or "Z") and the plane as a string ("XY", "YZ" or "XZ").
    For reasons, you must always multiply distance by 10 for it to be correct in Fusion 360.
    """
    try:
       
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["rectangular_pattern"]
        data = {
            "plane": plane,
            "quantity_one": quantity_one,
            "quantity_two": quantity_two,
            "distance_one": distance_one,
            "distance_two": distance_two,
            "axis_one": axis_one,
            "axis_two": axis_two
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Rectangular pattern failed: %s", e)
        raise


@mcp.tool()
def circular_pattern(plane: str, quantity: float, axis: str):
    """
    Create a Circular Pattern to distribute objects in a circle around an axis.
    You pass the number of copies as a float, the axis as a string ("X", "Y" or "Z") and the plane as a string ("XY", "YZ" or "XZ").

    The axis specifies which axis to rotate around.
    The plane specifies in which plane the pattern is distributed.

    Example: 
    - quantity: 6.0 creates 6 copies evenly distributed around 360°
    - axis: "Z" rotates around the Z axis
    - plane: "XY" distributes objects in the XY plane

    The feature is applied to the last created/selected object.
    Typical applications: Screw holes in a circle, gear teeth, ventilation grilles, decorative patterns.
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["circular_pattern"]
        data = {
            "plane": plane,
            "quantity": quantity,
            "axis": axis
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Circular pattern failed: %s", e)
        raise

@mcp.tool()
def ellipsie(x_center: float, y_center: float, z_center: float,
              x_major: float, y_major: float, z_major: float, x_through: float, y_through: float, z_through: float, plane: str):
    """Draw an ellipse in Fusion 360."""
    try:
        endpoint = config.ENDPOINTS["ellipsie"]
        headers = config.HEADERS
        data = {
            "x_center": x_center,
            "y_center": y_center,
            "z_center": z_center,
            "x_major": x_major,
            "y_major": y_major,
            "z_major": z_major,
            "x_through": x_through,
            "y_through": y_through,
            "z_through": z_through,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw ellipse failed: %s", e)
        raise

@mcp.tool()
def draw2Dcircle(radius: float, x: float, y: float, z: float, plane: str = "XY"):
    """
    Draw a circle in Fusion 360.
    You can pass the radius as a float.
    You can pass coordinates as floats.
    You can pass the plane as a string.
    Example: "XY", "YZ", "XZ"

    CRITICAL - Which coordinate for "upward":
    - XY plane: increase z = upward
    - YZ plane: increase x = upward  
    - XZ plane: increase y = upward

    Always provide JSON like this:
    {
        "radius":5,
        "x":0,
        "y":0,
        "z":0,
        "plane":"XY"
    }
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw2Dcircle"]
        data = {
            "radius": radius,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw 2D circle failed: %s", e)
        raise

@mcp.tool()
def loft(sketchcount: int):
    """
    Create a Loft feature in Fusion 360.
    You pass the number of sketches used for the loft as an integer.
    The sketches must have been created in the correct order.
    So first Sketch 1, then Sketch 2, then Sketch 3, etc.
    """
    try:
        endpoint = config.ENDPOINTS["loft"]
        headers = config.HEADERS
        data = {
            "sketchcount": sketchcount
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Loft failed: %s", e)
        raise


# =============================================================================
# Testing and Validation Tools
# =============================================================================

from src.tools.testing import (
    save_test as _save_test,
    load_tests as _load_tests,
    run_test as _run_test,
    run_all_tests as _run_all_tests,
    delete_test as _delete_test,
    create_snapshot as _create_snapshot,
    list_snapshots as _list_snapshots,
    restore_snapshot as _restore_snapshot,
    delete_snapshot as _delete_snapshot,
)


@mcp.tool()
def save_test(name: str, script: str, description: str = ""):
    """
    Save a validation test to disk for the current Fusion project.
    
    Tests are persisted to ~/Desktop/Fusion_Tests/{project_name}/ and can be
    run later to verify model state or validate assumptions.
    
    The script runs in Fusion 360 with access to:
    - adsk, app, ui, design, rootComp, math, json
    - Assertion helpers: assert_body_count(n), assert_sketch_count(n), 
      assert_volume(body_idx, cm3, tolerance), assert_bounding_box(...)
    
    Set 'result' variable in script to return a value.
    
    Example script:
        assert_body_count(2)
        body = rootComp.bRepBodies.item(0)
        assert body.volume > 5, "Body too small"
        result = "Validation passed"
    
    Args:
        name: Test name (alphanumeric/underscores)
        script: Python validation script
        description: What this test validates
    """
    return _save_test(name, script, description)


@mcp.tool()
def load_tests():
    """
    List all saved tests for the current Fusion project.
    
    Returns test names, descriptions, and file paths.
    Use this to see what tests are available before running them.
    """
    return _load_tests()


@mcp.tool()
def run_test(name: str):
    """
    Run a single saved validation test by name.
    
    Executes the test script in Fusion 360 and returns:
    - passed: True/False
    - return_value: Script's 'result' variable
    - error: Error details if failed
    - model_state: Current model state after test
    
    Args:
        name: Name of test to run (from load_tests)
    """
    return _run_test(name)


@mcp.tool()
def run_all_tests():
    """
    Run ALL saved tests for the current Fusion project in one call.
    
    This is the most efficient way to validate - one tool call runs
    all tests sequentially and returns a summary:
    - total, passed, failed counts
    - Individual results with timing
    - Detailed errors for failed tests
    
    Use this after making changes to verify nothing broke.
    """
    return _run_all_tests()


@mcp.tool()
def delete_test(name: str):
    """
    Delete a saved test by name.
    
    Args:
        name: Name of test to delete
    """
    return _delete_test(name)


@mcp.tool()
def create_snapshot(name: str):
    """
    Create a snapshot of the current model state.
    
    Captures body_count, sketch_count, volumes, and bounding boxes.
    Use BEFORE making changes to enable rollback verification.
    
    Snapshots are saved to ~/Desktop/Fusion_Tests/{project_name}/snapshots/
    
    Args:
        name: Name for this snapshot (alphanumeric/underscores)
    """
    return _create_snapshot(name)


@mcp.tool()
def list_snapshots():
    """
    List all snapshots for the current Fusion project.
    
    Returns snapshot names, creation times, and body/sketch counts.
    """
    return _list_snapshots()


@mcp.tool()
def restore_snapshot(name: str, max_undo_steps: int = 50):
    """
    Attempt to restore model to a previous snapshot using undo.
    
    **WARNING - LIMITATIONS:**
    - Fusion undo is sequential - undoes one operation at a time
    - Cannot skip forward in history
    - Cannot restore if snapshot requires MORE bodies/sketches
    - Only verifies body_count and sketch_count match
    - Geometry details may differ from original
    
    Use this to rollback after failed experiments.
    
    Args:
        name: Snapshot name to restore
        max_undo_steps: Maximum undo attempts (default 50)
    """
    return _restore_snapshot(name, max_undo_steps)


@mcp.tool()
def delete_snapshot(name: str):
    """
    Delete a snapshot by name.
    
    Args:
        name: Snapshot name to delete
    """
    return _delete_snapshot(name)


@mcp.prompt()
def wineglass():
    return """
    STEP 1: Draw Lines
    - Use Tool: draw_lines
    - Plane: XY
    - Points: [[0, 0], [0, -8], [1.5, -8], [1.5, -7], [0.3, -7], [0.3, -2], [3, -0.5], [3, 0], [0, 0]]
    
    STEP 2: Revolve the Profile
    - Use Tool: revolve
    - Angle: 360
    - The user selects the profile and axis in Fusion
    """


@mcp.prompt()
def magnet():
    return """
    STEP 1: Large Cylinder on Top
    - Use Tool: draw_cylinder
    - Radius: 1.59
    - Height: 0.3
    - Position: x=0, y=0, z=0.18
    - Plane: XY
    
    STEP 2: Small Cylinder on Bottom
    - Use Tool: draw_cylinder
    - Radius: 1.415
    - Height: 0.18
    - Position: x=0, y=0, z=0
    - Plane: XY
    
    STEP 3: Drill Hole in the Center
    - Use Tool: draw_holes
    - Points: [[0, 0]]
    - Diameter (width): 1.0
    - Depth: 0.21
    - faceindex: 2
    """


@mcp.prompt()
def dna():
    return """
    Use only the tools: draw2Dcircle, spline, sweep
    Create a DNA Double Helix in Fusion 360
    
    DNA STRAND 1:
    
    STEP 1: 
    - Use Tool: draw2Dcircle
    - Radius: 0.5
    - Position: x=3, y=0, z=0
    - Plane: XY
    
    STEP 2: 
    - Use Tool: spline
    - Plane: XY
    - Points: [[3,0,0], [2.121,2.121,6.25], [0,3,12.5], [-2.121,2.121,18.75], [-3,0,25], [-2.121,-2.121,31.25], [0,-3,37.5], [2.121,-2.121,43.75], [3,0,50]]
    
    STEP 3: Sweep Circle Along Path
    - Use Tool: sweep
    
    
    DNA STRAND 2:
    
    STEP 4: 
    - Use Tool: draw2Dcircle
    - Radius: 0.5
    - Position: x=-3, y=0, z=0
    - Plane: XY
    
    STEP 5: 
    - Use Tool: spline
    - Plane: XY
    - Points: [[-3,0,0], [-2.121,-2.121,6.25], [0,-3,12.5], [2.121,-2.121,18.75], [3,0,25], [2.121,2.121,31.25], [0,3,37.5], [-2.121,2.121,43.75], [-3,0,50]]
    
    STEP 6: Sweep Second Circle Along Second Path
    - Use Tool: sweep
    
    DONE: Now you have a DNA Double Helix!
    """


@mcp.prompt()
def flange():
    return """
    STEP 1: 
    - Use Tool: draw_cylinder
    - Choose sensible dimensions (e.g., Radius: 5, Height: 1)
    - Position: x=0, y=0, z=0
    - Plane: XY
    
    STEP 2: Drill Holes
    - Use Tool: draw_holes
    - Make 6-8 holes distributed in a circle
    - Depth: More than the cylinder height (so they go through)
    - faceindex: 1
    - Example points for 6 holes: [[4,0], [2,3.46], [-2,3.46], [-4,0], [-2,-3.46], [2,-3.46]]
    
    STEP 3: Ask the User
    - "Should there also be a hole in the center?"
    
    IF YES:
    STEP 4: 
    - Use Tool: draw2Dcircle
    - Radius: 2 (or what the user wants)
    - Position: x=0, y=0, z=0
    - Plane: XY
    
    STEP 5: 
    - Use Tool: cut_extrude
    - Depth: +2 (positive value! Greater than cylinder height)
    """


@mcp.prompt()
def vase():
    return """
    STEP 1: 
    - Use Tool: draw2Dcircle
    - Radius: 2.5
    - Position: x=0, y=0, z=0
    - Plane: XY
    
    STEP 2: 
    - Use Tool: draw2Dcircle
    - Radius: 1.5
    - Position: x=0, y=0, z=4
    - Plane: XY
    
    STEP 3:
    - Use Tool: draw2Dcircle
    - Radius: 3
    - Position: x=0, y=0, z=8
    - Plane: XY
    
    STEP 4: 
    - Use Tool: draw2Dcircle
    - Radius: 2
    - Position: x=0, y=0, z=12
    - Plane: XY
    
    STEP 5: 
    - Use Tool: loft
    - sketchcount: 4
    
    STEP 6: Hollow Out Vase (leave only walls)
    - Use Tool: shell_body
    - Wall thickness: 0.3
    - faceindex: 1
    
    DONE: Now you have a beautiful designer vase!
    """


@mcp.prompt()
def part():
    return """
    STEP 1: 
    - Use Tool: draw_box
    - Width (width_value): "10"
    - Height (height_value): "10"
    - Depth (depth_value): "0.5"
    - Position: x=0, y=0, z=0
    - Plane: XY
    
    STEP 2: Drill Small Holes
    - Use Tool: draw_holes
    - 8 holes total: 4 in corners + 4 closer to center
    - Example points: [[4,4], [4,-4], [-4,4], [-4,-4], [2,2], [2,-2], [-2,2], [-2,-2]]
    - Diameter (width): 0.5
    - Depth: 0.2
    - faceindex: 4
    
    STEP 3: Draw Circle in Center
    - Use Tool: draw2Dcircle
    - Radius: 1
    - Position: x=0, y=0, z=0
    - Plane: XY
    
    STEP 4: 
    - Use Tool: cut_extrude
    - Depth: +10 (MUST be positive!)
    
    STEP 5: Tell the User
    - "Please now select the inner face of the center hole in Fusion 360"
    
    STEP 6: Create Thread
    - Use Tool: create_thread
    - inside: True (internal thread)
    - allsizes: 10 (for 1/4 inch thread)
    
    DONE: Part with holes and thread is complete!
    """


@mcp.prompt()
def compensator():
    prompt = """
                Build a compensator in Fusion 360 with MCP: First delete everything.
                Then create a thin-walled pipe: Draw a 2D circle with radius 5 in the XY plane at z=0, 
                extrude it thin with distance 10 and thickness 0.1. Then add 8 rings stacked on top of each other (First circle then extrusion 8 times): For each ring at
                heights z=1 to z=8 draw a 2D circle with radius 5.1 in the XY plane and extrude it thin with distance 0.5 and thickness 0.5.
                Do not use boolean operations, leave the rings as separate bodies. Then round the edges with radius 0.2.
                Do it fast!!!!!!
    
                """
    return prompt




if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"]
    )
    args = parser.parse_args()

    mcp.run(transport=args.server_type)
