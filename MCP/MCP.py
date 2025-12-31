"""
Fusion 360 MCP Add-In - Refactored Version

This module provides an HTTP server interface for Fusion 360,
enabling external tools to control the CAD application via REST API.

The module uses a modular architecture with functionality split into:
- lib/geometry/ - Primitives and sketches
- lib/features/ - Extrusions, operations, patterns
- lib/utils/ - State management, export, measurements
"""

import adsk.core
import adsk.fusion
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import threading
import json
import time
import queue
from pathlib import Path
import math
import os
import sys
from io import StringIO

# Ensure lib/ is in the path for imports
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# Debug log file for troubleshooting startup issues
_DEBUG_LOG = os.path.join(_THIS_DIR, "mcp_debug.log")

def _log_debug(msg):
    """Write debug message to log file."""
    try:
        with open(_DEBUG_LOG, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except:
        pass

_log_debug(f"MCP.py loading, __file__={__file__}, _THIS_DIR={_THIS_DIR}")
_log_debug(f"sys.path={sys.path[:5]}...")

try:
    # Import modular functions from lib/
    from lib.geometry import (
        draw_box,
        draw_cylinder,
        create_sphere,
        draw_circle,
        draw_ellipse,
        draw_2d_rectangle,
        draw_lines,
        draw_one_line,
        draw_arc,
        draw_spline,
        draw_text,
    )
    from lib.features import (
        extrude_last_sketch,
        extrude_thin,
        cut_extrude,
        loft,
        sweep,
        revolve_profile,
        boolean_operation,
        shell_existing_body,
        fillet_edges,
        holes,
        create_thread,
        circular_pattern,
        rectangular_pattern,
        move_last_body,
        offsetplane,
    )
    from lib.utils import (
        get_model_parameters,
        get_current_model_state,
        get_faces_info,
        set_parameter,
        undo,
        delete_all,
        select_body,
        select_sketch,
        export_as_step,
        export_as_stl,
        measure_point_to_point,
        measure_distance,
        measure_angle,
        measure_area,
        measure_volume,
        measure_edge_length,
        measure_body_properties,
        get_edges_info,
        get_vertices_info,
        create_user_parameter,
        delete_user_parameter,
        get_sketch_info,
        get_sketch_constraints,
        get_sketch_dimensions,
        check_interference,
        get_timeline_info,
        rollback_to_feature,
        rollback_to_end,
        suppress_feature,
        get_mass_properties,
        create_offset_plane,
        create_plane_at_angle,
        create_midplane,
        create_construction_axis,
        create_construction_point,
        list_construction_geometry,
    )
    _log_debug("All lib imports successful")
except Exception as e:
    _log_debug(f"Import error: {e}\n{traceback.format_exc()}")
    raise


# Global state
ModelParameterSnapshot = []
httpd = None
task_queue = queue.Queue()
result_queue = queue.Queue()
script_result = {"status": "idle", "result": None, "error": None}
script_result_lock = threading.Lock()

TASK_TIMEOUT = 10.0

# Event Handler variables
app = None
ui = None
design = None
handlers = []
stopFlag = None
myCustomEvent = 'MCPTaskEvent'
customEvent = None


class TaskEventHandler(adsk.core.CustomEventHandler):
    """Custom Event Handler for processing tasks from the queue.
    
    This is used because Fusion 360 API is not thread-safe.
    """
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        global task_queue, result_queue, ModelParameterSnapshot, design, ui
        try:
            if design:
                ModelParameterSnapshot = get_model_parameters(design)
                
                while not task_queue.empty():
                    try:
                        task = task_queue.get_nowait()
                        self.process_task(task)
                    except queue.Empty:
                        break
        except Exception as e:
            pass
    
    def process_task(self, task):
        """Process a single task and put result in result_queue."""
        global design, ui, result_queue
        
        task_name = task[0]
        try:
            # Dispatch table for task processing
            # Functions that return data should return the result dict
            dispatch = {
                'set_parameter': lambda: set_parameter(design, task[1], task[2]),
                'draw_box': lambda: draw_box(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7]),
                'export_stl': lambda: export_as_stl(design, task[1]),
                'fillet_edges': lambda: fillet_edges(design, task[1]),
                'export_step': lambda: export_as_step(design, task[1]),
                'draw_cylinder': lambda: draw_cylinder(design, task[1], task[2], task[3], task[4], task[5], task[6]),
                'shell_body': lambda: shell_existing_body(design, task[1], task[2]),
                'undo': lambda: undo(design),
                'draw_lines': lambda: draw_lines(design, task[1], task[2]),
                'extrude_last_sketch': lambda: extrude_last_sketch(design, task[1], task[2]),
                'revolve_profile': lambda: revolve_profile(design, task[1]),
                'arc': lambda: draw_arc(design, task[1], task[2], task[3], task[4], task[5]),
                'draw_one_line': lambda: draw_one_line(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7]),
                'holes': lambda: holes(design, task[1], task[2], task[3], task[4]),
                'circle': lambda: draw_circle(design, task[1], task[2], task[3], task[4], task[5]),
                'extrude_thin': lambda: extrude_thin(design, task[1], task[2]),
                'select_body': lambda: select_body(design, task[1]),
                'select_sketch': lambda: select_sketch(design, task[1]),
                'spline': lambda: draw_spline(design, task[1], task[2]),
                'sweep': lambda: sweep(design),
                'cut_extrude': lambda: cut_extrude(design, task[1]),
                'circular_pattern': lambda: circular_pattern(design, task[1], task[2], task[3]),
                'offsetplane': lambda: offsetplane(design, task[1], task[2]),
                'loft': lambda: loft(design, task[1]),
                'ellipsis': lambda: draw_ellipse(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8], task[9], task[10]),
                'draw_sphere': lambda: create_sphere(design, task[1], task[2], task[3], task[4]),
                'threaded': lambda: create_thread(design, task[1], task[2]),
                'delete_everything': lambda: delete_all(design),
                'boolean_operation': lambda: boolean_operation(design, task[1]),
                'draw_2d_rectangle': lambda: draw_2d_rectangle(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7]),
                'rectangular_pattern': lambda: rectangular_pattern(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7]),
                'draw_text': lambda: draw_text(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8], task[9], task[10]),
                'move_body': lambda: move_last_body(design, task[1], task[2], task[3]),
                'execute_script': lambda: execute_fusion_script(design, task[1]),
                # Measurement commands (return data)
                'measure_distance': lambda: measure_distance(design, task[1], task[2], task[3], task[4], task[5], task[6]),
                'measure_angle': lambda: measure_angle(design, task[1], task[2], task[3], task[4], task[5], task[6]),
                'measure_area': lambda: measure_area(design, task[1], task[2]),
                'measure_volume': lambda: measure_volume(design, task[1]),
                'measure_edge_length': lambda: measure_edge_length(design, task[1], task[2]),
                'measure_body_properties': lambda: measure_body_properties(design, task[1]),
                'measure_point_to_point': lambda: measure_point_to_point(design, task[1], task[2]),
                'edges_info': lambda: get_edges_info(design, task[1]),
                'vertices_info': lambda: get_vertices_info(design, task[1]),
                # Parametric commands (return data)
                'create_parameter': lambda: create_user_parameter(design, task[1], task[2], task[3], task[4]),
                'delete_parameter': lambda: delete_user_parameter(design, task[1]),
                'sketch_info': lambda: get_sketch_info(design, task[1]),
                'sketch_constraints': lambda: get_sketch_constraints(design, task[1]),
                'sketch_dimensions': lambda: get_sketch_dimensions(design, task[1]),
                'check_interference': lambda: check_interference(design, task[1], task[2]) if len(task) > 2 else check_interference(design),
                'timeline_info': lambda: get_timeline_info(design),
                'rollback_to_feature': lambda: rollback_to_feature(design, task[1]),
                'rollback_to_end': lambda: rollback_to_end(design),
                'suppress_feature': lambda: suppress_feature(design, task[1], task[2]),
                'mass_properties': lambda: get_mass_properties(design, task[1], task[2] if len(task) > 2 else None),
                'create_offset_plane': lambda: create_offset_plane(design, task[1], task[2]),
                'create_plane_at_angle': lambda: create_plane_at_angle(design, task[1], task[2], task[3]),
                'create_midplane': lambda: create_midplane(design, task[1], task[2], task[3]),
                'create_construction_axis': lambda: create_construction_axis(design, task[1], task[2], task[3], task[4], task[5], task[6]),
                'create_construction_point': lambda: create_construction_point(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7]),
                'list_construction_geometry': lambda: list_construction_geometry(design),
            }
            
            if task_name in dispatch:
                result = dispatch[task_name]()
                # If the function returns a dict, use it; otherwise just report success
                if isinstance(result, dict):
                    result_queue.put(result)
                else:
                    result_queue.put({"success": True, "task": task_name})
            else:
                result_queue.put({"success": False, "error": f"Unknown task: {task_name}"})
            
        except Exception as e:
            error_msg = traceback.format_exc()
            result_queue.put({"success": False, "task": task_name, "error": error_msg})


class TaskThread(threading.Thread):
    """Background thread that fires custom events for task processing."""
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        while not self.stopped.wait(0.2):
            try:
                app.fireCustomEvent(myCustomEvent, json.dumps({}))
            except:
                break


def execute_fusion_script(design, script_code):
    """Execute arbitrary Python code in Fusion 360 context with helper functions.
    
    Available in scripts:
    - Core: adsk, app, ui, design, rootComp, math, json
    - Construction: XY, XZ, YZ, X_AXIS, Y_AXIS, Z_AXIS
    - Helpers: sketch_on, point, vector, val, val_str, extrude, revolve,
               loft_profiles, sweep_path, fillet, chamfer, shell, move,
               combine, pattern_circular, pattern_rectangular, last_body,
               last_sketch, body, delete_all
    - Assertions: assert_body_count, assert_sketch_count, assert_volume
    
    Set a 'result' variable to return a value.
    """
    global script_result, script_result_lock, ui
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    
    result = {
        "success": False,
        "return_value": None,
        "stdout": "",
        "stderr": "",
        "error": None,
        "error_type": None,
        "error_line": None,
        "traceback": None,
        "model_state": None
    }
    
    try:
        rootComp = design.rootComponent if design else None
        
        # =========================================================================
        # Helper functions available in scripts
        # =========================================================================
        
        def sketch_on(plane="XY", offset=0):
            """Create a sketch on a plane. Returns the sketch object."""
            sketches = rootComp.sketches
            if isinstance(plane, str):
                base = {"XY": rootComp.xYConstructionPlane,
                       "XZ": rootComp.xZConstructionPlane,
                       "YZ": rootComp.yZConstructionPlane}.get(plane, rootComp.xYConstructionPlane)
                
                if offset != 0:
                    planes = rootComp.constructionPlanes
                    planeInput = planes.createInput()
                    planeInput.setByOffset(base, adsk.core.ValueInput.createByReal(offset))
                    base = planes.add(planeInput)
                return sketches.add(base)
            return sketches.add(plane)
        
        def point(x, y, z=0):
            """Create a Point3D."""
            return adsk.core.Point3D.create(x, y, z)
        
        def vector(x, y, z):
            """Create a Vector3D."""
            return adsk.core.Vector3D.create(x, y, z)
        
        def val(value):
            """Create a ValueInput from a number (in cm)."""
            return adsk.core.ValueInput.createByReal(value)
        
        def val_str(expr):
            """Create a ValueInput from a string expression like '10 mm'."""
            return adsk.core.ValueInput.createByString(expr)
        
        def extrude(profile, distance, operation="new"):
            """Extrude a profile."""
            ops = {
                "new": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
                "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
                "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation,
            }
            extrudes = rootComp.features.extrudeFeatures
            extInput = extrudes.createInput(profile, ops.get(operation, ops["new"]))
            extInput.setDistanceExtent(False, val(distance))
            return extrudes.add(extInput)
        
        def revolve(profile, axis, angle=360, operation="new"):
            """Revolve a profile around an axis."""
            ops = {
                "new": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
                "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
                "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation,
            }
            revolves = rootComp.features.revolveFeatures
            revInput = revolves.createInput(profile, axis, ops.get(operation, ops["new"]))
            revInput.setAngleExtent(False, val_str(f"{angle} deg"))
            return revolves.add(revInput)
        
        def loft_profiles(*profiles):
            """Create a loft between profiles."""
            loftFeats = rootComp.features.loftFeatures
            loftInput = loftFeats.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            for prof in profiles:
                loftInput.loftSections.add(prof)
            loftInput.isSolid = True
            return loftFeats.add(loftInput)
        
        def sweep_path(profile, path):
            """Sweep a profile along a path."""
            sweeps = rootComp.features.sweepFeatures
            if not isinstance(path, adsk.fusion.Path):
                curves = adsk.core.ObjectCollection.create()
                if hasattr(path, '__iter__'):
                    for c in path:
                        curves.add(c)
                else:
                    curves.add(path)
                path = adsk.fusion.Path.create(curves, adsk.fusion.ChainedCurveOptions.noChainedCurves)
            sweepInput = sweeps.createInput(profile, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            return sweeps.add(sweepInput)
        
        def fillet(edges, radius):
            """Add fillets to edges."""
            fillets = rootComp.features.filletFeatures
            filletInput = fillets.createInput()
            if not isinstance(edges, adsk.core.ObjectCollection):
                coll = adsk.core.ObjectCollection.create()
                if hasattr(edges, '__iter__') and not hasattr(edges, 'objectType'):
                    for e in edges:
                        coll.add(e)
                else:
                    coll.add(edges)
                edges = coll
            filletInput.edgeSetInputs.addConstantRadiusEdgeSet(edges, val(radius), True)
            return fillets.add(filletInput)
        
        def chamfer(edges, distance):
            """Add chamfers to edges."""
            chamfers = rootComp.features.chamferFeatures
            if not isinstance(edges, adsk.core.ObjectCollection):
                coll = adsk.core.ObjectCollection.create()
                if hasattr(edges, '__iter__') and not hasattr(edges, 'objectType'):
                    for e in edges:
                        coll.add(e)
                else:
                    coll.add(edges)
                edges = coll
            chamferInput = chamfers.createInput2()
            chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, val(distance), True)
            return chamfers.add(chamferInput)
        
        def shell(faces, thickness, inside=True):
            """Shell a body by removing faces."""
            shellFeats = rootComp.features.shellFeatures
            if not isinstance(faces, adsk.core.ObjectCollection):
                coll = adsk.core.ObjectCollection.create()
                if hasattr(faces, '__iter__') and not hasattr(faces, 'objectType'):
                    for f in faces:
                        coll.add(f)
                else:
                    coll.add(faces)
                faces = coll
            shellInput = shellFeats.createInput(faces, False)
            if inside:
                shellInput.insideThickness = val(thickness)
            else:
                shellInput.outsideThickness = val(thickness)
            return shellFeats.add(shellInput)
        
        def move(bodies, x=0, y=0, z=0):
            """Move bodies by a vector."""
            moveFeats = rootComp.features.moveFeatures
            if not isinstance(bodies, adsk.core.ObjectCollection):
                coll = adsk.core.ObjectCollection.create()
                if hasattr(bodies, '__iter__') and not hasattr(bodies, 'objectType'):
                    for b in bodies:
                        coll.add(b)
                else:
                    coll.add(bodies)
                bodies = coll
            transform = adsk.core.Matrix3D.create()
            transform.translation = vector(x, y, z)
            moveInput = moveFeats.createInput2(bodies)
            moveInput.defineAsFreeMove(transform)
            return moveFeats.add(moveInput)
        
        def combine(target, tools, operation="join", keep_tools=False):
            """Combine bodies using boolean operations."""
            ops = {
                "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
                "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
                "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation,
            }
            combineFeats = rootComp.features.combineFeatures
            if not isinstance(tools, adsk.core.ObjectCollection):
                coll = adsk.core.ObjectCollection.create()
                if hasattr(tools, '__iter__') and not hasattr(tools, 'objectType'):
                    for t in tools:
                        coll.add(t)
                else:
                    coll.add(tools)
                tools = coll
            combineInput = combineFeats.createInput(target, tools)
            combineInput.operation = ops.get(operation, ops["join"])
            combineInput.isKeepToolBodies = keep_tools
            return combineFeats.add(combineInput)
        
        def pattern_circular(entities, axis, count, angle=360):
            """Create a circular pattern."""
            circFeats = rootComp.features.circularPatternFeatures
            if not isinstance(entities, adsk.core.ObjectCollection):
                coll = adsk.core.ObjectCollection.create()
                if hasattr(entities, '__iter__') and not hasattr(entities, 'objectType'):
                    for e in entities:
                        coll.add(e)
                else:
                    coll.add(entities)
                entities = coll
            circInput = circFeats.createInput(entities, axis)
            circInput.quantity = val(count)
            circInput.totalAngle = val_str(f"{angle} deg")
            return circFeats.add(circInput)
        
        def pattern_rectangular(entities, dir1, count1, spacing1, dir2=None, count2=1, spacing2=0):
            """Create a rectangular pattern."""
            rectFeats = rootComp.features.rectangularPatternFeatures
            if not isinstance(entities, adsk.core.ObjectCollection):
                coll = adsk.core.ObjectCollection.create()
                if hasattr(entities, '__iter__') and not hasattr(entities, 'objectType'):
                    for e in entities:
                        coll.add(e)
                else:
                    coll.add(entities)
                entities = coll
            rectInput = rectFeats.createInput(entities, dir1, val(count1), val(spacing1),
                                               adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
            if dir2 and count2 > 1:
                rectInput.setDirectionTwo(dir2, val(count2), val(spacing2))
            return rectFeats.add(rectInput)
        
        def last_body():
            """Get the most recently created body."""
            bodies = rootComp.bRepBodies
            return bodies.item(bodies.count - 1) if bodies.count > 0 else None
        
        def last_sketch():
            """Get the most recently created sketch."""
            sketches = rootComp.sketches
            return sketches.item(sketches.count - 1) if sketches.count > 0 else None
        
        def body(index_or_name):
            """Get a body by index or name."""
            bodies = rootComp.bRepBodies
            if isinstance(index_or_name, int):
                return bodies.item(index_or_name) if index_or_name < bodies.count else None
            return bodies.itemByName(index_or_name)
        
        def delete_all_bodies():
            """Delete all bodies in the design."""
            bodies = rootComp.bRepBodies
            removeFeats = rootComp.features.removeFeatures
            for i in range(bodies.count - 1, -1, -1):
                removeFeats.add(bodies.item(i))
        
        # Assertion helpers for validation
        def assert_body_count(expected):
            """Assert the number of bodies equals expected."""
            actual = rootComp.bRepBodies.count
            assert actual == expected, f"Expected {expected} bodies, got {actual}"
        
        def assert_sketch_count(expected):
            """Assert the number of sketches equals expected."""
            actual = rootComp.sketches.count
            assert actual == expected, f"Expected {expected} sketches, got {actual}"
        
        def assert_volume(body_index, expected_cm3, tolerance=0.01):
            """Assert body volume is within tolerance of expected value."""
            b = rootComp.bRepBodies.item(body_index)
            actual = b.volume
            diff = abs(actual - expected_cm3)
            assert diff <= tolerance, f"Expected volume {expected_cm3}, got {actual} (diff: {diff})"
        
        # =========================================================================
        # Create execution context
        # =========================================================================
        exec_globals = {
            "__builtins__": __builtins__,
            # Core Fusion objects
            "adsk": adsk,
            "app": app,
            "ui": ui,
            "design": design,
            "rootComp": rootComp,
            # Standard modules
            "math": math,
            "json": json,
            # Construction geometry shortcuts
            "XY": rootComp.xYConstructionPlane if rootComp else None,
            "XZ": rootComp.xZConstructionPlane if rootComp else None,
            "YZ": rootComp.yZConstructionPlane if rootComp else None,
            "X_AXIS": rootComp.xConstructionAxis if rootComp else None,
            "Y_AXIS": rootComp.yConstructionAxis if rootComp else None,
            "Z_AXIS": rootComp.zConstructionAxis if rootComp else None,
            # Helper functions
            "sketch_on": sketch_on,
            "point": point,
            "vector": vector,
            "val": val,
            "val_str": val_str,
            "extrude": extrude,
            "revolve": revolve,
            "loft_profiles": loft_profiles,
            "sweep_path": sweep_path,
            "fillet": fillet,
            "chamfer": chamfer,
            "shell": shell,
            "move": move,
            "combine": combine,
            "pattern_circular": pattern_circular,
            "pattern_rectangular": pattern_rectangular,
            "last_body": last_body,
            "last_sketch": last_sketch,
            "body": body,
            "delete_all": delete_all_bodies,
            # Assertions
            "assert_body_count": assert_body_count,
            "assert_sketch_count": assert_sketch_count,
            "assert_volume": assert_volume,
        }
        exec_locals = {}
        
        exec(script_code, exec_globals, exec_locals)
        
        if 'result' in exec_locals:
            result["return_value"] = str(exec_locals['result'])
        
        result["success"] = True
        
    except SyntaxError as e:
        result["error"] = str(e)
        result["error_type"] = "SyntaxError"
        result["error_line"] = e.lineno
        result["traceback"] = traceback.format_exc()
        
    except Exception as e:
        result["error"] = str(e)
        result["error_type"] = type(e).__name__
        tb = traceback.extract_tb(sys.exc_info()[2])
        if tb:
            result["error_line"] = tb[-1].lineno
        result["traceback"] = traceback.format_exc()
    
    finally:
        result["stdout"] = sys.stdout.getvalue()
        result["stderr"] = sys.stderr.getvalue()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        result["model_state"] = get_current_model_state(design)
        
        with script_result_lock:
            script_result = result


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for MCP commands."""
    
    def log_message(self, format, *args):
        pass  # Suppress logging
    
    def _set_headers(self, status=HTTPStatus.OK):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests for status and model state."""
        global design, ModelParameterSnapshot, script_result, script_result_lock
        
        # Parse path and query parameters
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        def get_param(name, default=0):
            """Get query parameter as int."""
            vals = query.get(name, [str(default)])
            try:
                return int(vals[0])
            except:
                return default
        
        if path == '/status':
            self._set_headers()
            self.wfile.write(json.dumps({"status": "running"}).encode())
        
        elif path == '/parameters':
            self._set_headers()
            self.wfile.write(json.dumps({"parameters": ModelParameterSnapshot}).encode())
        
        elif path == '/model_state':
            self._set_headers()
            state = get_current_model_state(design) if design else {"error": "No active design"}
            self.wfile.write(json.dumps(state).encode())
        
        elif path == '/script_result':
            self._set_headers()
            with script_result_lock:
                self.wfile.write(json.dumps(script_result).encode())
        
        elif path == '/faces_info':
            self._set_headers()
            result = get_faces_info(design, get_param('body_index', 0))
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/edges_info':
            self._set_headers()
            result = get_edges_info(design, get_param('body_index', 0))
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/vertices_info':
            self._set_headers()
            result = get_vertices_info(design, get_param('body_index', 0))
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/timeline_info':
            self._set_headers()
            result = get_timeline_info(design)
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/sketch_info':
            self._set_headers()
            result = get_sketch_info(design, get_param('sketch_index', -1))
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/sketch_constraints':
            self._set_headers()
            result = get_sketch_constraints(design, get_param('sketch_index', -1))
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/sketch_dimensions':
            self._set_headers()
            result = get_sketch_dimensions(design, get_param('sketch_index', -1))
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/list_construction_geometry':
            self._set_headers()
            result = list_construction_geometry(design)
            self.wfile.write(json.dumps(result).encode())
        
        else:
            self._set_headers(HTTPStatus.NOT_FOUND)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests for commands."""
        global task_queue, result_queue, design
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self._set_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return
        
        command = data.get('command')
        
        # Route commands
        routes = {
            'set_parameter': lambda d: ('set_parameter', d.get('name'), d.get('value')),
            'draw_box': lambda d: ('draw_box', d.get('width', 5), d.get('depth', 5), d.get('height', 5),
                                   d.get('x', 0), d.get('y', 0), d.get('z', 0), d.get('plane', 'XY')),
            'draw_cylinder': lambda d: ('draw_cylinder', d.get('radius', 1), d.get('height', 5),
                                        d.get('x', 0), d.get('y', 0), d.get('z', 0), d.get('plane', 'XY')),
            'draw_sphere': lambda d: ('draw_sphere', d.get('radius', 1), d.get('x', 0), d.get('y', 0), d.get('z', 0)),
            'export_stl': lambda d: ('export_stl', d.get('name', 'export')),
            'export_step': lambda d: ('export_step', d.get('name', 'export')),
            'fillet_edges': lambda d: ('fillet_edges', d.get('radius', 0.1)),
            'shell_body': lambda d: ('shell_body', d.get('thickness', 0.2), d.get('faceindex', 0)),
            'undo': lambda d: ('undo',),
            'delete_everything': lambda d: ('delete_everything',),
            'draw_lines': lambda d: ('draw_lines', d.get('points', []), d.get('plane', 'XY')),
            'draw_one_line': lambda d: ('draw_one_line', d.get('x1', 0), d.get('y1', 0), d.get('z1', 0),
                                        d.get('x2', 1), d.get('y2', 1), d.get('z2', 0), d.get('close', False), d.get('plane', 'XY')),
            'extrude_last_sketch': lambda d: ('extrude_last_sketch', d.get('distance', 1), d.get('operation', 0)),
            'revolve_profile': lambda d: ('revolve_profile', d.get('angle', 360)),
            'arc': lambda d: ('arc', d.get('center_x', 0), d.get('center_y', 0), d.get('radius', 1),
                              d.get('start_angle', 0), d.get('end_angle', 180)),
            'holes': lambda d: ('holes', d.get('points', []), d.get('width', 1), d.get('distance', 1), d.get('faceindex', 0)),
            'circle': lambda d: ('circle', d.get('x', 0), d.get('y', 0), d.get('z', 0),
                                 d.get('radius', 1), d.get('plane', 'XY')),
            'extrude_thin': lambda d: ('extrude_thin', d.get('distance', 1), d.get('thickness', 0.1)),
            'select_body': lambda d: ('select_body', d.get('name')),
            'select_sketch': lambda d: ('select_sketch', d.get('name')),
            'spline': lambda d: ('spline', d.get('points', []), d.get('plane', 'XY')),
            'sweep': lambda d: ('sweep',),
            'cut_extrude': lambda d: ('cut_extrude', d.get('distance', 1)),
            'circular_pattern': lambda d: ('circular_pattern', d.get('count', 4), d.get('angle', 360), d.get('axis', 'Z')),
            'offsetplane': lambda d: ('offsetplane', d.get('offset', 1), d.get('plane', 'XY')),
            'loft': lambda d: ('loft', d.get('count', 2)),
            'ellipsis': lambda d: ('ellipsis', d.get('x', 0), d.get('y', 0), d.get('z', 0),
                                   d.get('major', 2), d.get('minor', 1), d.get('direction_x', 1),
                                   d.get('direction_y', 0), d.get('direction_z', 0), d.get('height', 1), d.get('plane', 'XY')),
            'threaded': lambda d: ('threaded', d.get('inside', True), d.get('allsizes', 1)),
            'boolean_operation': lambda d: ('boolean_operation', d.get('operation', 'join')),
            'draw_2d_rectangle': lambda d: ('draw_2d_rectangle', d.get('x1', 0), d.get('y1', 0), d.get('z1', 0),
                                            d.get('x2', 5), d.get('y2', 5), d.get('z2', 0), d.get('plane', 'XY')),
            'rectangular_pattern': lambda d: ('rectangular_pattern', d.get('count_x', 2), d.get('spacing_x', 1),
                                              d.get('count_y', 2), d.get('spacing_y', 1),
                                              d.get('axis_x', 'X'), d.get('axis_y', 'Y'), d.get('body_index', -1)),
            'draw_text': lambda d: ('draw_text', d.get('text', 'Text'), d.get('thickness', 0.5),
                                    d.get('x1', 0), d.get('y1', 0), d.get('z1', 0),
                                    d.get('x2', 5), d.get('y2', 5), d.get('z2', 0),
                                    d.get('extrusion', 0.5), d.get('plane', 'XY')),
            'move_body': lambda d: ('move_body', d.get('x', 0), d.get('y', 0), d.get('z', 0)),
            'execute_script': lambda d: ('execute_script', d.get('script', '')),
            # Measurement routes
            'measure_distance': lambda d: ('measure_distance', d.get('entity1_type'), d.get('entity1_index'),
                                           d.get('entity2_type'), d.get('entity2_index'),
                                           d.get('body1_index', 0), d.get('body2_index', 0)),
            'measure_angle': lambda d: ('measure_angle', d.get('entity1_type'), d.get('entity1_index'),
                                        d.get('entity2_type'), d.get('entity2_index'),
                                        d.get('body1_index', 0), d.get('body2_index', 0)),
            'measure_area': lambda d: ('measure_area', d.get('face_index'), d.get('body_index', 0)),
            'measure_volume': lambda d: ('measure_volume', d.get('body_index', 0)),
            'measure_edge_length': lambda d: ('measure_edge_length', d.get('edge_index'), d.get('body_index', 0)),
            'measure_body_properties': lambda d: ('measure_body_properties', d.get('body_index', 0)),
            'measure_point_to_point': lambda d: ('measure_point_to_point', d.get('point1'), d.get('point2')),
            'edges_info': lambda d: ('edges_info', d.get('body_index', 0)),
            'vertices_info': lambda d: ('vertices_info', d.get('body_index', 0)),
            # Parametric routes
            'create_parameter': lambda d: ('create_parameter', d.get('name'), d.get('value'), d.get('unit', 'mm'), d.get('comment', '')),
            'delete_parameter': lambda d: ('delete_parameter', d.get('name')),
            'sketch_info': lambda d: ('sketch_info', d.get('sketch_index', -1)),
            'sketch_constraints': lambda d: ('sketch_constraints', d.get('sketch_index', -1)),
            'sketch_dimensions': lambda d: ('sketch_dimensions', d.get('sketch_index', -1)),
            'check_interference': lambda d: ('check_interference', d.get('body1_index'), d.get('body2_index')),
            'timeline_info': lambda d: ('timeline_info',),
            'rollback_to_feature': lambda d: ('rollback_to_feature', d.get('feature_index')),
            'rollback_to_end': lambda d: ('rollback_to_end',),
            'suppress_feature': lambda d: ('suppress_feature', d.get('feature_index'), d.get('suppress', True)),
            'mass_properties': lambda d: ('mass_properties', d.get('body_index', 0), d.get('material_density')),
            'create_offset_plane': lambda d: ('create_offset_plane', d.get('offset'), d.get('base_plane', 'XY')),
            'create_plane_at_angle': lambda d: ('create_plane_at_angle', d.get('angle'), d.get('base_plane', 'XY'), d.get('axis', 'X')),
            'create_midplane': lambda d: ('create_midplane', d.get('body_index', 0), d.get('face1_index', 0), d.get('face2_index', 1)),
            'create_construction_axis': lambda d: ('create_construction_axis', d.get('axis_type'), d.get('body_index', 0),
                                                   d.get('edge_index', 0), d.get('face_index', 0), d.get('point1'), d.get('point2')),
            'create_construction_point': lambda d: ('create_construction_point', d.get('point_type'), d.get('x', 0), d.get('y', 0), d.get('z', 0),
                                                    d.get('body_index', 0), d.get('vertex_index', 0), d.get('edge_index', 0)),
            'list_construction_geometry': lambda d: ('list_construction_geometry',),
        }
        
        if command in routes:
            task = routes[command](data)
            
            # Clear result queue
            while not result_queue.empty():
                try:
                    result_queue.get_nowait()
                except queue.Empty:
                    break
            
            task_queue.put(task)
            
            # Wait for result
            try:
                result = result_queue.get(timeout=TASK_TIMEOUT)
                self._set_headers()
                self.wfile.write(json.dumps(result).encode())
            except queue.Empty:
                self._set_headers(HTTPStatus.REQUEST_TIMEOUT)
                self.wfile.write(json.dumps({"error": "Task timeout"}).encode())
        else:
            self._set_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(json.dumps({"error": f"Unknown command: {command}"}).encode())


def run(context):
    """Start the MCP Add-In."""
    global app, ui, design, httpd, handlers, stopFlag, customEvent
    
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        
        # Register custom event
        customEvent = app.registerCustomEvent(myCustomEvent)
        eventHandler = TaskEventHandler()
        customEvent.add(eventHandler)
        handlers.append(eventHandler)
        
        # Start background thread
        stopFlag = threading.Event()
        taskThread = TaskThread(stopFlag)
        taskThread.start()
        
        # Start HTTP server
        server_address = ('', 5000)
        httpd = HTTPServer(server_address, MCPRequestHandler)
        
        serverThread = threading.Thread(target=httpd.serve_forever)
        serverThread.daemon = True
        serverThread.start()
        
        ui.messageBox('MCP Server started on port 5000')
        
    except Exception as e:
        if ui:
            ui.messageBox(f'Failed to start: {traceback.format_exc()}')


def stop(context):
    """Stop the MCP Add-In."""
    global httpd, stopFlag, customEvent, handlers
    
    try:
        if stopFlag:
            stopFlag.set()
        
        if httpd:
            httpd.shutdown()
            httpd = None
        
        if customEvent:
            app.unregisterCustomEvent(myCustomEvent)
            customEvent = None
        
        handlers = []
        
    except Exception as e:
        if ui:
            ui.messageBox(f'Failed to stop: {traceback.format_exc()}')
