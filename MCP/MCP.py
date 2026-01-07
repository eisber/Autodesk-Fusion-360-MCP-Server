"""
Fusion 360 MCP Add-In - Refactored Version

This module provides an HTTP server interface for Fusion 360,
enabling external tools to control the CAD application via REST API.

The module uses a modular architecture with functionality split into:
- lib/geometry/ - Primitives and sketches
- lib/features/ - Extrusions, operations, patterns
- lib/utils/ - State management, export, measurements
"""

import json
import math
import os
import queue
import sys
import threading
import time
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import StringIO
from socketserver import ThreadingMixIn

import adsk.core
import adsk.fusion


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTP Server that handles each request in a separate thread."""

    daemon_threads = True  # Don't wait for threads to finish on shutdown


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
    except OSError:
        pass


_log_debug(f"MCP.py loading, __file__={__file__}, _THIS_DIR={_THIS_DIR}")
_log_debug(f"sys.path={sys.path[:5]}...")

try:
    # Import the task registry for auto-discovered dispatch
    # Import modules to trigger @task registration
    from lib import features  # noqa: F401 - Registers feature tasks
    from lib.registry import (
        build_task_args,
        dispatch as registry_dispatch,
        list_tasks,
    )

    # Import SSE support for real-time task progress
    from lib.server.sse import format_sse, get_task_manager

    # Import specific functions still needed directly for GET routes
    from lib.utils import (  # noqa: F401 - Register util tasks
        get_current_model_state,
        get_edges_info,
        get_faces_info,
        get_model_parameters,
        get_vertices_info,
        measurement,
        parametric,
        selection,
        state,
    )
    from lib.utils.parametric import (
        check_all_interferences,
        get_sketch_constraints,
        get_sketch_dimensions,
        get_sketch_info,
        get_timeline_info,
        list_construction_geometry,
    )

    _log_debug("All lib imports successful")
    _log_debug(f"Registered tasks: {list_tasks()}")
except Exception as e:
    _log_debug(f"Import error: {e}\n{traceback.format_exc()}")
    raise


# =============================================================================
# Version
# =============================================================================
__version__ = "1.0.0"


# =============================================================================
# Script Execution (special handling - not a @task function)
# =============================================================================
# execute_script is handled separately since it needs special execution context


# Global state
ModelParameterSnapshot = []
httpd = None
task_queue = queue.Queue()
result_queue = queue.Queue()
script_result = {"status": "idle", "result": None, "error": None}
script_result_lock = threading.Lock()

# Task timeout - increased since SSE handles progress updates
TASK_TIMEOUT = 300.0  # 5 minutes

# Task manager for SSE streaming
task_manager = None  # Initialized after imports

# Event Handler variables
app = None
ui = None
design = None
handlers = []
stopFlag = None
myCustomEvent = "MCPTaskEvent"
customEvent = None


class TaskEventHandler(adsk.core.CustomEventHandler):
    """Custom Event Handler for processing tasks from the queue.

    This is used because Fusion 360 API is not thread-safe.
    Now supports SSE-based progress reporting and task cancellation.
    """

    def __init__(self):
        super().__init__()

    def notify(self, args):
        # Access module-level variables
        try:
            # Get active design - may be None if no document is open
            # Update global design reference so HTTP handlers can use it
            design = app.activeProduct if app else None
            if design and design.objectType == "adsk::fusion::Design":
                ModelParameterSnapshot = get_model_parameters(design)
            else:
                design = None  # Clear if not a valid design

            # Cleanup old completed tasks periodically
            if task_manager:
                task_manager.cleanup_old_tasks()

            while not task_queue.empty():
                try:
                    task = task_queue.get_nowait()
                    self.process_task(task)
                except queue.Empty:
                    break
        except Exception:
            pass

    def process_task(self, task):
        """Process a single task and broadcast result via SSE."""
        # Get the active design lazily - it may not exist at startup
        design = app.activeProduct
        if design is None or design.objectType != "adsk::fusion::Design":
            error_msg = "No active Fusion design. Please open or create a design first."
            # Check if task has task_id (new format: last element is 8-char ID)
            if len(task) > 1 and isinstance(task[-1], str) and len(task[-1]) == 8:
                task_id = task[-1]
                if task_manager:
                    task_manager.fail_task(task_id, error_msg)
            result_queue.put({"error": error_msg})
            return

        task_name = task[0]

        # Extract task_id if present (new format: last element is 8-char ID)
        task_id = None
        task_args = task
        if len(task) > 1 and isinstance(task[-1], str) and len(task[-1]) == 8:
            task_id = task[-1]
            task_args = task[:-1]  # Remove task_id from args

        # Mark task as started
        if task_id and task_manager:
            task_manager.start_task(task_id)

        try:
            # Check for cancellation before starting
            if task_id and task_manager and task_manager.is_cancelled(task_id):
                result_queue.put({"success": False, "task": task_name, "error": "Task cancelled"})
                return

            # Create progress function if we have task_id
            progress_fn = None
            if task_id and task_manager:
                progress_fn = lambda pct, msg="": task_manager.report_progress(task_id, pct, msg)

            # Use registry-based dispatch
            result = self._dispatch_task(task_name, design, task_args, progress_fn, task_id)

            # If the function returns a dict, use it; otherwise just report success
            if isinstance(result, dict):
                if task_id and task_manager:
                    if result.get("success", True):
                        task_manager.complete_task(task_id, result)
                    else:
                        task_manager.fail_task(task_id, result.get("error", "Unknown error"))
                result_queue.put(result)
            else:
                success_result = {"success": True, "task": task_name}
                if task_id and task_manager:
                    task_manager.complete_task(task_id, success_result)
                result_queue.put(success_result)

        except Exception:
            error_msg = traceback.format_exc()
            if task_id and task_manager:
                task_manager.fail_task(task_id, error_msg)
            result_queue.put({"success": False, "task": task_name, "error": error_msg})

    def _dispatch_task(self, task_name, design, task, progress_fn=None, task_id=None):
        """Dispatch a task using the auto-discovery registry.

        Args:
            task_name: Name of the task (= function name)
            design: Active Fusion design
            task: Full task tuple (task_name, arg1, arg2, ...)
            progress_fn: Optional progress callback (percent, message)
            task_id: Optional task ID for cancellation checking

        Returns:
            Result from the handler function

        Raises:
            ValueError: If task is not registered
        """
        # Special case: execute_script needs special handling
        if task_name == "execute_script":
            return execute_fusion_script(design, task[1], progress_fn, task_id)

        # Special case: inspect_api - run introspection script
        if task_name == "inspect_api":
            path = task[1] if len(task) > 1 else "adsk.fusion"
            return self._inspect_api(design, path, progress_fn, task_id)

        # Special case: get_class_info - run class info script
        if task_name == "get_class_info":
            class_path = task[1] if len(task) > 1 else "adsk.fusion.Sketch"
            return self._get_class_info(design, class_path, progress_fn, task_id)

        # Use registry dispatch - args are task[1:]
        args = list(task[1:]) if len(task) > 1 else []
        return registry_dispatch(task_name, design, ui, args)

    def _inspect_api(self, design, path, progress_fn=None, task_id=None):
        """Inspect Fusion 360 API at the given path."""
        inspection_script = (
            '''
import inspect

def get_type_name(obj):
    """Get a readable type name for an object."""
    t = type(obj).__name__
    if t == 'type':
        return 'class'
    elif t == 'module':
        return 'module'
    elif t == 'builtin_function_or_method':
        return 'method'
    elif t == 'property':
        return 'property'
    elif t == 'getset_descriptor':
        return 'property'
    elif t == 'method_descriptor':
        return 'method'
    elif callable(obj):
        return 'callable'
    else:
        return t

def get_signature_str(obj):
    """Try to get a signature string for a callable."""
    try:
        sig = inspect.signature(obj)
        return str(sig)
    except (ValueError, TypeError):
        doc = getattr(obj, '__doc__', '') or ''
        lines = doc.strip().split('\\n')
        if lines and '(' in lines[0] and ')' in lines[0]:
            return lines[0]
        return None

def get_member_info(name, obj, include_details=False):
    """Get info about a single member."""
    type_name = get_type_name(obj)
    info = {'name': name, 'type': type_name}

    if include_details:
        doc = getattr(obj, '__doc__', None)
        if doc:
            info['docstring'] = doc.strip()[:500]  # Truncate long docstrings

        if type_name in ('method', 'callable', 'builtin_function_or_method'):
            sig = get_signature_str(obj)
            if sig:
                info['signature'] = sig

    return info

def inspect_path(path):
    """Inspect an adsk module path and return detailed info."""
    parts = path.split('.')

    if parts[0] != 'adsk':
        return {'error': f'Path must start with "adsk", got: {path}'}

    obj = adsk
    traversed = ['adsk']

    for part in parts[1:]:
        try:
            obj = getattr(obj, part)
            traversed.append(part)
        except AttributeError:
            return {
                'error': f'"{part}" not found in {".".join(traversed)}',
                'path': path,
                'available': [m for m in dir(obj) if not m.startswith('_')][:50]
            }

    result = {
        'path': path,
        'type': get_type_name(obj),
    }

    doc = getattr(obj, '__doc__', None)
    if doc:
        result['docstring'] = doc.strip()[:1000]  # Truncate

    if result['type'] in ('method', 'callable', 'builtin_function_or_method', 'class'):
        sig = get_signature_str(obj)
        if sig:
            result['signature'] = f'{parts[-1]}{sig}' if not sig.startswith(parts[-1]) else sig

    if result['type'] in ('module', 'class', 'type'):
        members = []
        for name in dir(obj):
            if name.startswith('_'):
                continue
            try:
                member_obj = getattr(obj, name)
                member_info = get_member_info(name, member_obj, include_details=True)
                members.append(member_info)
            except Exception:
                members.append({'name': name, 'type': 'unknown'})

        result['members'] = members
        result['member_count'] = len(members)

    if result['type'] == 'property':
        doc = result.get('docstring', '')
        if 'Returns' in doc or 'returns' in doc:
            result['returns'] = doc

    return result

result = inspect_path('''
            + repr(path)
            + """)
"""
        )
        return execute_fusion_script(design, inspection_script, progress_fn, task_id)

    def _get_class_info(self, design, class_path, progress_fn=None, task_id=None):
        """Get detailed class documentation."""
        class_info_script = (
            """
import inspect

def get_type_name(obj):
    t = type(obj).__name__
    if t == 'type': return 'class'
    elif t == 'module': return 'module'
    elif t == 'builtin_function_or_method': return 'method'
    elif t in ('property', 'getset_descriptor'): return 'property'
    elif t == 'method_descriptor': return 'method'
    elif callable(obj): return 'callable'
    return t

def get_signature_str(obj):
    try:
        return str(inspect.signature(obj))
    except (ValueError, TypeError):
        doc = getattr(obj, '__doc__', '') or ''
        lines = doc.strip().split('\\n')
        if lines and '(' in lines[0] and ')' in lines[0]:
            return lines[0]
        return None

def get_class_info(class_path):
    parts = class_path.split('.')
    if parts[0] != 'adsk':
        return {'error': f'Path must start with "adsk"'}

    obj = adsk
    for part in parts[1:]:
        try:
            obj = getattr(obj, part)
        except AttributeError:
            return {'error': f'"{part}" not found in path'}

    class_name = parts[-1]
    result = {
        'class_name': class_name,
        'path': class_path,
        'methods': [],
        'properties': []
    }

    doc = getattr(obj, '__doc__', None)
    if doc:
        result['docstring'] = doc.strip()

    for name in sorted(dir(obj)):
        if name.startswith('_'):
            continue
        try:
            member = getattr(obj, name)
            type_name = get_type_name(member)

            member_info = {'name': name}
            member_doc = getattr(member, '__doc__', None)
            if member_doc:
                member_info['docstring'] = member_doc.strip()[:300]

            if type_name in ('method', 'callable', 'builtin_function_or_method'):
                sig = get_signature_str(member)
                if sig:
                    member_info['signature'] = f'{name}{sig}'
                result['methods'].append(member_info)
            elif type_name == 'property':
                result['properties'].append(member_info)
        except Exception:
            pass

    return result

result = get_class_info("""
            + repr(class_path)
            + """)
"""
        )
        return execute_fusion_script(design, class_info_script, progress_fn, task_id)


class TaskThread(threading.Thread):
    """Background thread that fires custom events for task processing."""

    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        while not self.stopped.wait(0.2):
            try:
                app.fireCustomEvent(myCustomEvent, json.dumps({}))
            except Exception:
                break


def execute_fusion_script(design, script_code, progress_fn=None, task_id=None):
    """Execute arbitrary Python code in Fusion 360 context with helper functions.

    Available in scripts:
    - Core: adsk, app, ui, design, rootComp, math, json
    - Construction: XY, XZ, YZ, X_AXIS, Y_AXIS, Z_AXIS
    - Helpers: sketch_on, point, vector, val, val_str, extrude, revolve,
               loft_profiles, sweep_path, fillet, chamfer, shell, move,
               combine, pattern_circular, pattern_rectangular, last_body,
               last_sketch, body, delete_all
    - Assertions: assert_body_count, assert_sketch_count, assert_volume
    - Progress: progress(percent, message) - report progress (0-100)
    - Cancellation: is_cancelled() - check if task was cancelled

    Set a 'result' variable to return a value.
    """
    global script_result  # This one IS assigned

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
        "model_state": None,
    }

    try:
        rootComp = design.rootComponent if design else None

        # =========================================================================
        # Progress and cancellation helpers for scripts
        # =========================================================================

        def progress(percent: float, message: str = ""):
            """Report script progress (0-100)."""
            if progress_fn:
                progress_fn(percent, message)

        def is_cancelled() -> bool:
            """Check if this script execution was cancelled."""
            if task_id and task_manager:
                return task_manager.is_cancelled(task_id)
            return False

        # =========================================================================
        # Helper functions available in scripts
        # =========================================================================

        def sketch_on(plane="XY", offset=0):
            """Create a sketch on a plane. Returns the sketch object."""
            sketches = rootComp.sketches
            if isinstance(plane, str):
                base = {
                    "XY": rootComp.xYConstructionPlane,
                    "XZ": rootComp.xZConstructionPlane,
                    "YZ": rootComp.yZConstructionPlane,
                }.get(plane, rootComp.xYConstructionPlane)

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
                if hasattr(path, "__iter__"):
                    for c in path:
                        curves.add(c)
                else:
                    curves.add(path)
                path = adsk.fusion.Path.create(
                    curves, adsk.fusion.ChainedCurveOptions.noChainedCurves
                )
            sweepInput = sweeps.createInput(
                profile, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            )
            return sweeps.add(sweepInput)

        def fillet(edges, radius):
            """Add fillets to edges."""
            fillets = rootComp.features.filletFeatures
            filletInput = fillets.createInput()
            if not isinstance(edges, adsk.core.ObjectCollection):
                coll = adsk.core.ObjectCollection.create()
                if hasattr(edges, "__iter__") and not hasattr(edges, "objectType"):
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
                if hasattr(edges, "__iter__") and not hasattr(edges, "objectType"):
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
                if hasattr(faces, "__iter__") and not hasattr(faces, "objectType"):
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
                if hasattr(bodies, "__iter__") and not hasattr(bodies, "objectType"):
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
                if hasattr(tools, "__iter__") and not hasattr(tools, "objectType"):
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
                if hasattr(entities, "__iter__") and not hasattr(entities, "objectType"):
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
                if hasattr(entities, "__iter__") and not hasattr(entities, "objectType"):
                    for e in entities:
                        coll.add(e)
                else:
                    coll.add(entities)
                entities = coll
            rectInput = rectFeats.createInput(
                entities,
                dir1,
                val(count1),
                val(spacing1),
                adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
            )
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

        def delete_all_bodies(bodies=True, sketches=True, construction=True, parameters=False):
            """Delete objects in the design."""
            deleted = {
                "bodies": 0,
                "sketches": 0,
                "planes": 0,
                "axes": 0,
                "points": 0,
                "parameters": 0,
            }

            if bodies:
                body_list = rootComp.bRepBodies
                removeFeats = rootComp.features.removeFeatures
                for i in range(body_list.count - 1, -1, -1):
                    removeFeats.add(body_list.item(i))
                    deleted["bodies"] += 1

            if sketches:
                sketch_list = rootComp.sketches
                for i in range(sketch_list.count - 1, -1, -1):
                    sketch_list.item(i).deleteMe()
                    deleted["sketches"] += 1

            if construction:
                # Origin element names to skip
                origin_planes = {"XY Plane", "XZ Plane", "YZ Plane"}
                origin_axes = {"X Axis", "Y Axis", "Z Axis"}
                origin_points = {"Origin"}

                # Construction planes (skip origin)
                planes = rootComp.constructionPlanes
                for i in range(planes.count - 1, -1, -1):
                    plane = planes.item(i)
                    if plane.name not in origin_planes:
                        plane.deleteMe()
                        deleted["planes"] += 1
                # Construction axes (skip origin)
                axes = rootComp.constructionAxes
                for i in range(axes.count - 1, -1, -1):
                    axis = axes.item(i)
                    if axis.name not in origin_axes:
                        axis.deleteMe()
                        deleted["axes"] += 1
                # Construction points (skip origin)
                points = rootComp.constructionPoints
                for i in range(points.count - 1, -1, -1):
                    point = points.item(i)
                    if point.name not in origin_points:
                        point.deleteMe()
                        deleted["points"] += 1

            if parameters:
                user_params = design.userParameters
                for i in range(user_params.count - 1, -1, -1):
                    user_params.item(i).deleteMe()
                    deleted["parameters"] += 1

            return deleted

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
        # Using single namespace so functions defined in script can call each other
        # =========================================================================
        exec_namespace = {
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
            # Progress and cancellation
            "progress": progress,
            "is_cancelled": is_cancelled,
        }

        exec(script_code, exec_namespace)

        if "result" in exec_namespace:
            script_result_value = exec_namespace["result"]
            # Keep dicts/lists as-is for proper JSON serialization
            # Convert other types to string representation
            if isinstance(script_result_value, dict | list):
                result["return_value"] = script_result_value
            else:
                result["return_value"] = str(script_result_value)

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

        # Get compact model state (just summary, not full details)
        full_state = get_current_model_state(design)
        result["model_state"] = {
            "body_count": full_state.get("body_count", 0),
            "sketch_count": full_state.get("sketch_count", 0),
            "design_name": full_state.get("design_name", ""),
            "spatial_summary": full_state.get("spatial_summary", ""),
        }

        # Filter out empty/null values to save tokens
        result = {k: v for k, v in result.items() if v is not None and v not in ("", [])}

        with script_result_lock:
            script_result = result

    return result


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for MCP commands with SSE support."""

    def log_message(self, format, *args):
        _log_debug(f"[HTTP] {format % args}")

    def _get_active_design(self):
        """Get the active Fusion design, or None if not available."""
        if not app:
            return None
        product = app.activeProduct
        if product and product.objectType == "adsk::fusion::Design":
            return product
        return None

    def _set_headers(self, status=HTTPStatus.OK, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests for status, model state, and SSE stream."""
        _log_debug(f"GET request: {self.path}")

        # Parse path and query parameters
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        def get_param(name, default=0):
            """Get query parameter as int."""
            vals = query.get(name, [str(default)])
            try:
                return int(vals[0])
            except (ValueError, IndexError):
                return default

        def get_str_param(name, default=""):
            """Get query parameter as string."""
            vals = query.get(name, [default])
            return vals[0] if vals else default

        # SSE Events endpoint
        if path == "/events":
            self._handle_sse_stream(get_str_param("task_id"))
            return

        # Task status endpoint
        if path == "/task_status":
            task_id = get_str_param("task_id")
            if task_id and task_manager:
                task = task_manager.get_task(task_id)
                if task:
                    self._set_headers()
                    self.wfile.write(
                        json.dumps(
                            {
                                "task_id": task.task_id,
                                "task_name": task.task_name,
                                "status": task.status.value,
                                "progress": task.progress,
                                "message": task.message,
                                "result": task.result,
                                "error": task.error,
                            }
                        ).encode()
                    )
                else:
                    self._set_headers(HTTPStatus.NOT_FOUND)
                    self.wfile.write(json.dumps({"error": f"Task {task_id} not found"}).encode())
            else:
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(json.dumps({"error": "task_id parameter required"}).encode())
            return

        if path == "/status":
            self._set_headers()
            self.wfile.write(json.dumps({"status": "running"}).encode())

        elif path == "/parameters":
            self._set_headers()
            self.wfile.write(json.dumps({"parameters": ModelParameterSnapshot}).encode())

        elif path == "/get_model_state":
            self._set_headers()
            active_design = self._get_active_design()
            state = (
                get_current_model_state(active_design)
                if active_design
                else {"error": "No active design"}
            )
            self.wfile.write(json.dumps(state).encode())

        elif path == "/script_result":
            self._set_headers()
            with script_result_lock:
                self.wfile.write(json.dumps(script_result).encode())

        elif path == "/get_faces_info":
            self._set_headers()
            result = get_faces_info(self._get_active_design(), get_param("body_index", 0))
            self.wfile.write(json.dumps(result).encode())

        elif path == "/get_edges_info":
            self._set_headers()
            result = get_edges_info(self._get_active_design(), get_param("body_index", 0))
            self.wfile.write(json.dumps(result).encode())

        elif path == "/get_vertices_info":
            self._set_headers()
            result = get_vertices_info(self._get_active_design(), get_param("body_index", 0))
            self.wfile.write(json.dumps(result).encode())

        elif path == "/get_timeline_info":
            self._set_headers()
            result = get_timeline_info(self._get_active_design())
            self.wfile.write(json.dumps(result).encode())

        elif path == "/get_sketch_info":
            self._set_headers()
            result = get_sketch_info(self._get_active_design(), get_param("sketch_index", -1))
            self.wfile.write(json.dumps(result).encode())

        elif path == "/get_sketch_constraints":
            self._set_headers()
            result = get_sketch_constraints(
                self._get_active_design(), get_param("sketch_index", -1)
            )
            self.wfile.write(json.dumps(result).encode())

        elif path == "/get_sketch_dimensions":
            self._set_headers()
            result = get_sketch_dimensions(self._get_active_design(), get_param("sketch_index", -1))
            self.wfile.write(json.dumps(result).encode())

        elif path == "/list_construction_geometry":
            self._set_headers()
            result = list_construction_geometry(self._get_active_design())
            self.wfile.write(json.dumps(result).encode())

        elif path == "/list_parameters":
            self._set_headers()
            result = get_model_parameters(self._get_active_design())
            self.wfile.write(json.dumps(result).encode())

        elif path == "/check_all_interferences":
            self._set_headers()
            result = check_all_interferences(self._get_active_design())
            self.wfile.write(json.dumps(result).encode())

        else:
            self._set_headers(HTTPStatus.NOT_FOUND)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def _handle_sse_stream(self, task_id_filter: str = ""):
        """Handle SSE event stream connection."""
        # Set SSE headers
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        if not task_manager:
            self.wfile.write(format_sse("error", {"message": "Task manager not initialized"}))
            self.wfile.flush()
            return

        # Subscribe to events
        subscriber_id = task_manager.subscribe()

        try:
            # Send initial connection event
            self.wfile.write(format_sse("connected", {"subscriber_id": subscriber_id}))
            self.wfile.flush()

            # Stream events
            event_queue = task_manager.get_event_queue(subscriber_id)
            while True:
                try:
                    event = event_queue.get(timeout=30.0)

                    # Filter by task_id if specified
                    if task_id_filter:
                        event_task_id = event.get("data", {}).get("task_id", "")
                        if event_task_id != task_id_filter:
                            continue

                    self.wfile.write(format_sse(event["event"], event["data"]))
                    self.wfile.flush()

                    # Close stream on task completion if filtering
                    if task_id_filter and event["event"] in (
                        "task_completed",
                        "task_failed",
                        "task_cancelled",
                    ):
                        break

                except queue.Empty:
                    # Send keepalive
                    self.wfile.write(format_sse("keepalive", {}))
                    self.wfile.flush()

        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # Client disconnected
        finally:
            task_manager.unsubscribe(subscriber_id)

    def do_POST(self):
        """Handle POST requests for commands."""
        _log_debug(f"POST request: {self.path}")

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        _log_debug(f"  POST content_length: {content_length}")

        try:
            data = json.loads(post_data.decode("utf-8"))
            _log_debug(f"  POST command: {data.get('command', 'unknown')}")
        except json.JSONDecodeError:
            _log_debug("  POST error: Invalid JSON")
            self._set_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return

        command = data.get("command")

        # Special case: test_connection doesn't need task queue
        if command == "test_connection":
            self._set_headers()
            self.wfile.write(
                json.dumps(
                    {"success": True, "message": "Connection successful", "version": __version__}
                ).encode()
            )
            return

        # Create tracked task
        task_id = None
        if task_manager:
            task_id = task_manager.create_task(command)

        # Special case: execute_script needs the raw script string
        if command == "execute_script":
            if task_id:
                task = ("execute_script", data.get("script", ""), task_id)
            else:
                task = ("execute_script", data.get("script", ""))
        # Special case: inspect_api - pass the path parameter
        elif command == "inspect_api":
            path = data.get("path", "adsk.fusion")
            if task_id:
                task = ("inspect_api", path, task_id)
            else:
                task = ("inspect_api", path)
        # Special case: get_class_info - pass the class_path parameter
        elif command == "get_class_info":
            class_path = data.get("class_path", "adsk.fusion.Sketch")
            if task_id:
                task = ("get_class_info", class_path, task_id)
            else:
                task = ("get_class_info", class_path)
        else:
            # Use registry to auto-build task args from request data
            try:
                base_task = build_task_args(command, data)
                # Append task_id to the task tuple if available
                if task_id:
                    task = base_task + (task_id,)
                else:
                    task = base_task
            except ValueError:
                if task_id and task_manager:
                    task_manager.fail_task(task_id, f"Unknown command: {command}")
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(
                    json.dumps(
                        {"error": f"Unknown command: {command}", "task_id": task_id}
                    ).encode()
                )
                return

        # Clear result queue (legacy support)
        while not result_queue.empty():
            try:
                result_queue.get_nowait()
            except queue.Empty:
                break

        task_queue.put(task)

        # Return task_id immediately - client should subscribe to SSE for result
        self._set_headers(HTTPStatus.ACCEPTED)
        self.wfile.write(
            json.dumps(
                {
                    "task_id": task_id,
                    "status": "queued",
                    "message": f"Subscribe to /events?task_id={task_id} for updates",
                }
            ).encode()
        )

    def do_DELETE(self):
        """Handle DELETE requests for task cancellation."""
        from urllib.parse import urlparse

        parsed = urlparse(self.path)
        path = parsed.path

        # Cancel task endpoint: DELETE /task/{task_id}
        if path.startswith("/task/"):
            task_id = path.split("/")[-1]
            if task_manager and task_manager.cancel_task(task_id):
                self._set_headers()
                self.wfile.write(
                    json.dumps(
                        {"success": True, "task_id": task_id, "status": "cancelled"}
                    ).encode()
                )
            else:
                self._set_headers(HTTPStatus.NOT_FOUND)
                self.wfile.write(
                    json.dumps(
                        {
                            "success": False,
                            "error": f"Task {task_id} not found or already completed",
                        }
                    ).encode()
                )
        else:
            self._set_headers(HTTPStatus.NOT_FOUND)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())


def run(context):
    """Start the MCP Add-In."""
    global app, ui, httpd, customEvent, task_manager, stopFlag  # These are assigned

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        # Note: design is fetched lazily when needed, not at startup
        # This avoids errors when no document is open

        # Initialize task manager for SSE
        task_manager = get_task_manager()

        # Register custom event
        customEvent = app.registerCustomEvent(myCustomEvent)
        eventHandler = TaskEventHandler()
        customEvent.add(eventHandler)
        handlers.append(eventHandler)

        # Start background thread
        stopFlag = threading.Event()
        taskThread = TaskThread(stopFlag)
        taskThread.start()

        # Start HTTP server (threaded to handle concurrent requests like SSE)
        from config import FUSION_MCP_PORT

        server_address = ("", FUSION_MCP_PORT)
        httpd = ThreadingHTTPServer(server_address, MCPRequestHandler)
        _log_debug(f"Starting ThreadingHTTPServer on port {FUSION_MCP_PORT}")

        serverThread = threading.Thread(target=httpd.serve_forever)
        serverThread.daemon = True
        serverThread.start()
    except Exception:
        if ui:
            ui.messageBox(f"Failed to start: {traceback.format_exc()}")


def stop(context):
    """Stop the MCP Add-In."""
    global httpd, customEvent, handlers  # These are assigned

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

    except Exception:
        if ui:
            ui.messageBox(f"Failed to stop: {traceback.format_exc()}")
