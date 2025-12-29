import adsk.core, adsk.fusion, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import threading
import json
import time
import queue
from pathlib import Path
import math
import os

ModelParameterSnapshot = []
httpd = None
task_queue = queue.Queue()  # Queue for thread-safe actions
result_queue = queue.Queue()  # Queue for returning results to HTTP handlers
script_result = {"status": "idle", "result": None, "error": None}  # Storage for script execution results
script_result_lock = threading.Lock()

# Timeout for waiting on task results (seconds)
TASK_TIMEOUT = 10.0

# Event Handler variables
app = None
ui = None
design = None
handlers = []
stopFlag = None
myCustomEvent = 'MCPTaskEvent'
customEvent = None

#Event Handler Class
class TaskEventHandler(adsk.core.CustomEventHandler):
    """
    Custom Event Handler for processing tasks from the queue
    This is used, because Fusion 360 API is not thread-safe
    """
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        global task_queue, result_queue, ModelParameterSnapshot, design, ui
        try:
            if design:
                # Update parameter snapshot
                ModelParameterSnapshot = get_model_parameters(design)
                
                # Process task queue
                while not task_queue.empty():
                    try:
                        task = task_queue.get_nowait()
                        self.process_task(task)
                    except queue.Empty:
                        break
                        
        except Exception as e:

            pass
    
    def process_task(self, task):
        """Process a single task and put result in result_queue"""
        global design, ui, result_queue
        
        task_name = task[0]
        try:
            if task_name == 'set_parameter':
                set_parameter(design, task[1], task[2])
            elif task_name == 'draw_box':
                draw_Box(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
            elif task_name == 'export_stl':
                export_as_STL(design, task[1])
            elif task_name == 'fillet_edges':
                fillet_edges(design, task[1])
            elif task_name == 'export_step':
                export_as_STEP(design, task[1])
            elif task_name == 'draw_cylinder':
                draw_cylinder(design, task[1], task[2], task[3], task[4], task[5], task[6])
            elif task_name == 'shell_body':
                shell_existing_body(design, task[1], task[2])
            elif task_name == 'undo':
                undo(design)
            elif task_name == 'draw_lines':
                draw_lines(design, task[1], task[2])
            elif task_name == 'extrude_last_sketch':
                extrude_last_sketch(design, task[1], task[2])
            elif task_name == 'revolve_profile':
                revolve_profile(design, task[1])        
            elif task_name == 'arc':
                arc(design, task[1], task[2], task[3], task[4], task[5])
            elif task_name == 'draw_one_line':
                draw_one_line(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
            elif task_name == 'holes':
                holes(design, task[1], task[2], task[3], task[4])
            elif task_name == 'circle':
                draw_circle(design, task[1], task[2], task[3], task[4], task[5])
            elif task_name == 'extrude_thin':
                extrude_thin(design, task[1], task[2])
            elif task_name == 'select_body':
                select_body(design, task[1])
            elif task_name == 'select_sketch':
                select_sketch(design, task[1])
            elif task_name == 'spline':
                spline(design, task[1], task[2])
            elif task_name == 'sweep':
                sweep(design)
            elif task_name == 'cut_extrude':
                cut_extrude(design, task[1])
            elif task_name == 'circular_pattern':
                circular_pattern(design, task[1], task[2], task[3])
            elif task_name == 'offsetplane':
                offsetplane(design, task[1], task[2])
            elif task_name == 'loft':
                loft(design, task[1])
            elif task_name == 'ellipsis':
                draw_ellipis(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8], task[9], task[10])
            elif task_name == 'draw_sphere':
                create_sphere(design, task[1], task[2], task[3], task[4])
            elif task_name == 'threaded':
                create_thread(design, task[1], task[2])
            elif task_name == 'delete_everything':
                delete(design)
            elif task_name == 'boolean_operation':
                boolean_operation(design, task[1])
            elif task_name == 'draw_2d_rectangle':
                draw_2d_rect(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
            elif task_name == 'rectangular_pattern':
                rect_pattern(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
            elif task_name == 'draw_text':
                draw_text(design, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8], task[9], task[10])
            elif task_name == 'move_body':
                move_last_body(design, task[1], task[2], task[3])
            elif task_name == 'execute_script':
                execute_fusion_script(design, task[1])
            else:
                result_queue.put({"success": False, "error": f"Unknown task: {task_name}"})
                return
            
            # Task completed successfully
            result_queue.put({"success": True, "task": task_name})
            
        except Exception as e:
            # Task failed - put error in result queue
            error_msg = traceback.format_exc()
            result_queue.put({"success": False, "task": task_name, "error": error_msg})


class TaskThread(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        # Fire custom event every 200ms for task processing
        while not self.stopped.wait(0.2):
            try:
                app.fireCustomEvent(myCustomEvent, json.dumps({}))
            except:
                break



###Geometry Functions######

def draw_text(design, text, thickness,
              x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value, plane="XY"):
    
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    
    if plane == "XY":
        sketch = sketches.add(rootComp.xYConstructionPlane)
    elif plane == "XZ":
        sketch = sketches.add(rootComp.xZConstructionPlane)
    elif plane == "YZ":
        sketch = sketches.add(rootComp.yZConstructionPlane)
    point_1 = adsk.core.Point3D.create(x_1, y_1, z_1)
    point_2 = adsk.core.Point3D.create(x_2, y_2, z_2)

    texts = sketch.sketchTexts
    input = texts.createInput2(f"{text}", thickness)
    input.setAsMultiLine(point_1,
                         point_2,
                         adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
                         adsk.core.VerticalAlignments.TopVerticalAlignment, 0)
    sketchtext = texts.add(input)
    extrudes = rootComp.features.extrudeFeatures
    
    extInput = extrudes.createInput(sketchtext, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(extrusion_value)
    extInput.setDistanceExtent(False, distance)
    extInput.isSolid = True
    
    # Create the extrusion
    ext = extrudes.add(extInput)


def create_sphere(design, radius, x, y, z):
    rootComp = design.rootComponent
    component: adsk.fusion.Component = design.rootComponent
    # Create a new sketch on the xy plane.
    sketches = rootComp.sketches
    
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    # Draw a circle.
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(adsk.core.Point3D.create(x, y, z), radius)
    # Draw a line to use as the axis of revolution.
    lines = sketch.sketchCurves.sketchLines
    axisLine = lines.addByTwoPoints(
        adsk.core.Point3D.create(x - radius, y, z),
        adsk.core.Point3D.create(x + radius, y, z)
    )

    # Get the profile defined by half of the circle.
    profile = sketch.profiles.item(0)
    # Create an revolution input for a revolution while specifying the profile and that a new component is to be created
    revolves = component.features.revolveFeatures
    revInput = revolves.createInput(profile, axisLine, adsk.fusion.FeatureOperations.NewComponentFeatureOperation)
    # Define that the extent is an angle of 2*pi to get a sphere
    angle = adsk.core.ValueInput.createByReal(2*math.pi)
    revInput.setAngleExtent(False, angle)
    # Create the extrusion.
    ext = revolves.add(revInput)


def draw_Box(design, height, width, depth, x, y, z, plane=None):
    """
    Draws Box with given dimensions height, width, depth at position (x,y,z)
    z creates an offset construction plane
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    planes = rootComp.constructionPlanes
    
    # Choose base plane based on parameter
    if plane == 'XZ':
        basePlane = rootComp.xZConstructionPlane
    elif plane == 'YZ':
        basePlane = rootComp.yZConstructionPlane
    else:
        basePlane = rootComp.xYConstructionPlane
    
    # Create offset plane at z if z != 0
    if z != 0:
        planeInput = planes.createInput()
        offsetValue = adsk.core.ValueInput.createByReal(z)
        planeInput.setByOffset(basePlane, offsetValue)
        offsetPlane = planes.add(planeInput)
        sketch = sketches.add(offsetPlane)
    else:
        sketch = sketches.add(basePlane)
    
    lines = sketch.sketchCurves.sketchLines
    # addCenterPointRectangle: (center, corner-relative-to-center)
    lines.addCenterPointRectangle(
        adsk.core.Point3D.create(x, y, 0),
        adsk.core.Point3D.create(x + width/2, y + height/2, 0)
    )
    prof = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(depth)
    extInput.setDistanceExtent(False, distance)
    extrudes.add(extInput)


def draw_ellipis(design, x_center, y_center, z_center,
                 x_major, y_major, z_major, x_through, y_through, z_through, plane="XY"):
    """
    Draws an ellipse on the specified plane using three points.
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    if plane == "XZ":
        sketch = sketches.add(rootComp.xZConstructionPlane)
    elif plane == "YZ":
        sketch = sketches.add(rootComp.yZConstructionPlane)
    else:
        sketch = sketches.add(rootComp.xYConstructionPlane)
    # Always define the points and create the ellipse
    # Ensure all arguments are floats (Fusion API is strict)
    centerPoint = adsk.core.Point3D.create(float(x_center), float(y_center), float(z_center))
    majorAxisPoint = adsk.core.Point3D.create(float(x_major), float(y_major), float(z_major))
    throughPoint = adsk.core.Point3D.create(float(x_through), float(y_through), float(z_through))
    sketchEllipse = sketch.sketchCurves.sketchEllipses
    ellipse = sketchEllipse.add(centerPoint, majorAxisPoint, throughPoint)


def draw_2d_rect(design, x_1, y_1, z_1, x_2, y_2, z_2, plane="XY"):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    planes = rootComp.constructionPlanes

    if plane == "XZ":
        baseplane = rootComp.xZConstructionPlane
        if y_1 and y_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(y_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)
    elif plane == "YZ":
        baseplane = rootComp.yZConstructionPlane
        if x_1 and x_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(x_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)
    else:
        baseplane = rootComp.xYConstructionPlane
        if z_1 and z_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)

    rectangles = sketch.sketchCurves.sketchLines
    point_1 = adsk.core.Point3D.create(x_1, y_1, z_1)
    points_2 = adsk.core.Point3D.create(x_2, y_2, z_2)
    rectangles.addTwoPointRectangle(point_1, points_2)


def draw_circle(design, radius, x, y, z, plane="XY"):
    """
    Draws a circle with given radius at position (x,y,z) on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    For XY plane: circle at (x,y) with z offset
    For XZ plane: circle at (x,z) with y offset  
    For YZ plane: circle at (y,z) with x offset
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    planes = rootComp.constructionPlanes
    
    # Determine which plane and coordinates to use
    if plane == "XZ":
        basePlane = rootComp.xZConstructionPlane
        # For XZ plane: x and z are in-plane, y is the offset
        if y != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(y)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)
        centerPoint = adsk.core.Point3D.create(x, z, 0)
        
    elif plane == "YZ":
        basePlane = rootComp.yZConstructionPlane
        # For YZ plane: y and z are in-plane, x is the offset
        if x != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(x)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)
        centerPoint = adsk.core.Point3D.create(y, z, 0)
        
    else:  # XY plane (default)
        basePlane = rootComp.xYConstructionPlane
        # For XY plane: x and y are in-plane, z is the offset
        if z != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)
        centerPoint = adsk.core.Point3D.create(x, y, 0)

    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(centerPoint, radius)


def draw_sphere(design, radius, x, y, z):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    sketch = sketches.add(rootComp.xYConstructionPlane)
# USELESS  


##############################################################################################
###2D Geometry Functions######


def move_last_body(design, x, y, z):
    rootComp = design.rootComponent
    features = rootComp.features
    sketches = rootComp.sketches
    moveFeats = features.moveFeatures
    body = rootComp.bRepBodies
    bodies = adsk.core.ObjectCollection.create()
    
    if body.count > 0:
        latest_body = body.item(body.count - 1)
        bodies.add(latest_body)
    else:
        raise ValueError("No bodies found to move.")

    vector = adsk.core.Vector3D.create(x, y, z)
    transform = adsk.core.Matrix3D.create()
    transform.translation = vector
    moveFeatureInput = moveFeats.createInput2(bodies)
    moveFeatureInput.defineAsFreeMove(transform)
    moveFeats.add(moveFeatureInput)


def offsetplane(design, offset, plane="XY"):
    """
    Creates a new offset sketch which can be selected
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    offset = adsk.core.ValueInput.createByReal(offset)
    ctorPlanes = rootComp.constructionPlanes
    ctorPlaneInput1 = ctorPlanes.createInput()
    
    if plane == "XY":         
        ctorPlaneInput1.setByOffset(rootComp.xYConstructionPlane, offset)
    elif plane == "XZ":
        ctorPlaneInput1.setByOffset(rootComp.xZConstructionPlane, offset)
    elif plane == "YZ":
        ctorPlaneInput1.setByOffset(rootComp.yZConstructionPlane, offset)
    ctorPlanes.add(ctorPlaneInput1)


def create_thread(design, inside, sizes):
    """
    params:
    inside: boolean information if the face is inside or outside
    sizes : index of the size in the allsizes list
    """
    global ui
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    threadFeatures = rootComp.features.threadFeatures
    
    # Note: This still requires UI interaction for face selection
    face = ui.selectEntity("Select a face for threading", "Faces").entity
    faces = adsk.core.ObjectCollection.create()
    faces.add(face)
    
    threadDataQuery = threadFeatures.threadDataQuery
    threadTypes = threadDataQuery.allThreadTypes
    threadType = threadTypes[0]

    allsizes = threadDataQuery.allSizes(threadType)
    threadSize = allsizes[sizes]

    allDesignations = threadDataQuery.allDesignations(threadType, threadSize)
    threadDesignation = allDesignations[0]
    
    allClasses = threadDataQuery.allClasses(False, threadType, threadDesignation)
    threadClass = allClasses[0]
    
    # create the threadInfo according to the query result
    threadInfo = threadFeatures.createThreadInfo(inside, threadType, threadDesignation, threadClass)

    threadInput = threadFeatures.createInput(faces, threadInfo)
    threadInput.isFullLength = True
    
    # create the final thread
    thread = threadFeatures.add(threadInput)


def spline(design, points, plane="XY"):
    """
    Draws a spline through the given points on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    if plane == "XY":
        sketch = sketches.add(rootComp.xYConstructionPlane)
    elif plane == "XZ":
        sketch = sketches.add(rootComp.xZConstructionPlane)
    elif plane == "YZ":
        sketch = sketches.add(rootComp.yZConstructionPlane)
    
    splinePoints = adsk.core.ObjectCollection.create()
    for point in points:
        splinePoints.add(adsk.core.Point3D.create(point[0], point[1], point[2]))
    
    sketch.sketchCurves.sketchFittedSplines.add(splinePoints)


def arc(design, point1, point2, points3, plane="XY", connect=False):
    """
    This creates arc between two points on the specified plane
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane 
    if plane == "XZ":
        sketch = sketches.add(rootComp.xZConstructionPlane)
    elif plane == "YZ":
        sketch = sketches.add(rootComp.yZConstructionPlane)
    else:
        xyPlane = rootComp.xYConstructionPlane 
        sketch = sketches.add(xyPlane)
    
    start = adsk.core.Point3D.create(point1[0], point1[1], point1[2])
    alongpoint = adsk.core.Point3D.create(point2[0], point2[1], point2[2])
    endpoint = adsk.core.Point3D.create(points3[0], points3[1], points3[2])
    arcs = sketch.sketchCurves.sketchArcs
    arc_obj = arcs.addByThreePoints(start, alongpoint, endpoint)
    if connect:
        startconnect = adsk.core.Point3D.create(start.x, start.y, start.z)
        endconnect = adsk.core.Point3D.create(endpoint.x, endpoint.y, endpoint.z)
        lines = sketch.sketchCurves.sketchLines
        lines.addByTwoPoints(startconnect, endconnect)


def draw_lines(design, points, Plane="XY"):
    """
    User input: points = [(x1,y1), (x2,y2), ...]
    Plane: "XY", "XZ", "YZ"
    Draws lines between the given points on the specified plane
    Connects the last point to the first point to close the shape
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    if Plane == "XY":
        xyPlane = rootComp.xYConstructionPlane 
        sketch = sketches.add(xyPlane)
    elif Plane == "XZ":
        xZPlane = rootComp.xZConstructionPlane
        sketch = sketches.add(xZPlane)
    elif Plane == "YZ":
        yZPlane = rootComp.yZConstructionPlane
        sketch = sketches.add(yZPlane)
    for i in range(len(points)-1):
        start = adsk.core.Point3D.create(points[i][0], points[i][1], 0)
        end = adsk.core.Point3D.create(points[i+1][0], points[i+1][1], 0)
        sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    sketch.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(points[-1][0], points[-1][1], 0),
        adsk.core.Point3D.create(points[0][0], points[0][1], 0)
    )


def draw_one_line(design, x1, y1, z1, x2, y2, z2, plane="XY"):
    """
    Draws a single line between two points (x1, y1, z1) and (x2, y2, z2) on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    This function does not add a new sketch it is designed to be used after arc 
    This is how we can make half circles and extrude them
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    sketch = sketches.item(sketches.count - 1)
    
    start = adsk.core.Point3D.create(x1, y1, 0)
    end = adsk.core.Point3D.create(x2, y2, 0)
    sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)


#################################################################################



###3D Geometry Functions######
def loft(design, sketchcount):
    """
    Creates a loft between the last 'sketchcount' sketches
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    loftFeatures = rootComp.features.loftFeatures
    
    loftInput = loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    loftSectionsObj = loftInput.loftSections
    
    # Add profiles from the last 'sketchcount' sketches
    for i in range(sketchcount):
        sketch = sketches.item(sketches.count - 1 - i)
        profile = sketch.profiles.item(0)
        loftSectionsObj.add(profile)
    
    loftInput.isSolid = True
    loftInput.isClosed = False
    loftInput.isTangentEdgesMerged = True
    
    # Create loft feature
    loftFeatures.add(loftInput)


def boolean_operation(design, op):
    """
    This function performs boolean operations (cut, intersect, join)
    It is important to draw the target body first, then the tool body
    """
    app = adsk.core.Application.get()
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    # Get the root component of the active design.
    rootComp = design.rootComponent
    features = rootComp.features
    bodies = rootComp.bRepBodies
   
    targetBody = bodies.item(0)  # target body has to be the first drawn body
    toolBody = bodies.item(1)    # tool body has to be the second drawn body

    combineFeatures = rootComp.features.combineFeatures
    tools = adsk.core.ObjectCollection.create()
    tools.add(toolBody)
    input: adsk.fusion.CombineFeatureInput = combineFeatures.createInput(targetBody, tools)
    input.isNewComponent = False
    input.isKeepToolBodies = False
    if op == "cut":
        input.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    elif op == "intersect":
        input.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
    elif op == "join":
        input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        
    combineFeature = combineFeatures.add(input)


def sweep(design):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    sweeps = rootComp.features.sweepFeatures

    profsketch = sketches.item(sketches.count - 2)
    prof = profsketch.profiles.item(0)
    pathsketch = sketches.item(sketches.count - 1)
    # collect all sketch curves in an ObjectCollection
    pathCurves = adsk.core.ObjectCollection.create()
    for i in range(pathsketch.sketchCurves.count):
        pathCurves.add(pathsketch.sketchCurves.item(i))

    path = adsk.fusion.Path.create(pathCurves, 0)
    sweepInput = sweeps.createInput(prof, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    sweeps.add(sweepInput)


def extrude_last_sketch(design, value, taperangle):
    """
    Just extrudes the last sketch by the given value
    """
    rootComp = design.rootComponent 
    sketches = rootComp.sketches
    sketch = sketches.item(sketches.count - 1)
    prof = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(value)
    
    if taperangle != 0:
        taperValue = adsk.core.ValueInput.createByString(f'{taperangle} deg')
        extent_distance = adsk.fusion.DistanceExtentDefinition.create(distance)
        extrudeInput.setOneSideExtent(extent_distance, adsk.fusion.ExtentDirections.PositiveExtentDirection, taperValue)
    else:
        extrudeInput.setDistanceExtent(False, distance)
    
    extrudes.add(extrudeInput)


def shell_existing_body(design, thickness=0.5, faceindex=0):
    """
    Shells the body on a specified face index with given thickness
    """
    rootComp = design.rootComponent
    features = rootComp.features
    body = rootComp.bRepBodies.item(0)

    entities = adsk.core.ObjectCollection.create()
    entities.add(body.faces.item(faceindex))

    shellFeats = features.shellFeatures
    isTangentChain = False
    shellInput = shellFeats.createInput(entities, isTangentChain)

    thicknessVal = adsk.core.ValueInput.createByReal(thickness)
    shellInput.insideThickness = thicknessVal

    shellInput.shellType = adsk.fusion.ShellTypes.SharpOffsetShellType

    # Execute
    shellFeats.add(shellInput)


def fillet_edges(design, radius=0.3):
    rootComp = design.rootComponent

    bodies = rootComp.bRepBodies
    edgeCollection = adsk.core.ObjectCollection.create()
    for body_idx in range(bodies.count):
        body = bodies.item(body_idx)
        for edge_idx in range(body.edges.count):
            edge = body.edges.item(edge_idx)
            edgeCollection.add(edge)

    fillets = rootComp.features.filletFeatures
    radiusInput = adsk.core.ValueInput.createByReal(radius)
    filletInput = fillets.createInput()
    filletInput.isRollingBallCorner = True
    edgeSetInput = filletInput.edgeSetInputs.addConstantRadiusEdgeSet(edgeCollection, radiusInput, True)
    edgeSetInput.continuity = adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType
    fillets.add(filletInput)


def revolve_profile(design, angle=360):
    """
    This function revolves already existing sketch with drawn lines from the function draw_lines
    around the given axisLine by the specified angle (default is 360 degrees).
    """
    global ui
    rootComp = design.rootComponent
    # Note: Still requires UI interaction
    profile = ui.selectEntity('Select a profile to revolve.', 'Profiles').entity
    axis = ui.selectEntity('Select sketch line for axis.', 'SketchLines').entity
    operation = adsk.fusion.FeatureOperations.NewComponentFeatureOperation
    revolveFeatures = rootComp.features.revolveFeatures
    input = revolveFeatures.createInput(profile, axis, operation)
    input.setAngleExtent(False, adsk.core.ValueInput.createByString(str(angle) + ' deg'))
    revolveFeature = revolveFeatures.add(input)


##############################################################################################

###Selection Functions######
def rect_pattern(design, axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane="XY"):
    """
    Creates a rectangular pattern of the last body along the specified axis and plane
    There are two quantity parameters for two directions
    There are also two distance parameters for the spacing in two directions
    params:
    axis: "X", "Y", or "Z" axis for the pattern direction
    quantity_one: Number of instances in the first direction
    quantity_two: Number of instances in the second direction
    distance_one: Spacing between instances in the first direction
    distance_two: Spacing between instances in the second direction
    plane: Construction plane for the pattern ("XY", "XZ", or "YZ")
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    rectFeats = rootComp.features.rectangularPatternFeatures

    quantity_one = adsk.core.ValueInput.createByString(f"{quantity_one}")
    quantity_two = adsk.core.ValueInput.createByString(f"{quantity_two}")
    distance_one = adsk.core.ValueInput.createByString(f"{distance_one}")
    distance_two = adsk.core.ValueInput.createByString(f"{distance_two}")

    bodies = rootComp.bRepBodies
    if bodies.count > 0:
        latest_body = bodies.item(bodies.count - 1)
    else:
        raise ValueError("No bodies found for rectangular pattern.")
    
    inputEntites = adsk.core.ObjectCollection.create()
    inputEntites.add(latest_body)
    baseaxis_one = None    
    if axis_one == "Y":
        baseaxis_one = rootComp.yConstructionAxis 
    elif axis_one == "X":
        baseaxis_one = rootComp.xConstructionAxis
    elif axis_one == "Z":
        baseaxis_one = rootComp.zConstructionAxis

    baseaxis_two = None    
    if axis_two == "Y":
        baseaxis_two = rootComp.yConstructionAxis  
    elif axis_two == "X":
        baseaxis_two = rootComp.xConstructionAxis
    elif axis_two == "Z":
        baseaxis_two = rootComp.zConstructionAxis

    rectangularPatternInput = rectFeats.createInput(inputEntites, baseaxis_one, quantity_one, distance_one, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    rectangularPatternInput.setDirectionTwo(baseaxis_two, quantity_two, distance_two)
    rectangularFeature = rectFeats.add(rectangularPatternInput)


def circular_pattern(design, quantity, axis, plane):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    circularFeats = rootComp.features.circularPatternFeatures
    bodies = rootComp.bRepBodies

    if bodies.count > 0:
        latest_body = bodies.item(bodies.count - 1)
    else:
        raise ValueError("No bodies found for circular pattern.")
    
    inputEntites = adsk.core.ObjectCollection.create()
    inputEntites.add(latest_body)
    if plane == "XY":
        sketch = sketches.add(rootComp.xYConstructionPlane)
    elif plane == "XZ":
        sketch = sketches.add(rootComp.xZConstructionPlane)    
    elif plane == "YZ":
        sketch = sketches.add(rootComp.yZConstructionPlane)
    
    if axis == "Y":
        yAxis = rootComp.yConstructionAxis
        circularFeatInput = circularFeats.createInput(inputEntites, yAxis)
    elif axis == "X":
        xAxis = rootComp.xConstructionAxis
        circularFeatInput = circularFeats.createInput(inputEntites, xAxis)
    elif axis == "Z":
        zAxis = rootComp.zConstructionAxis
        circularFeatInput = circularFeats.createInput(inputEntites, zAxis)

    circularFeatInput.quantity = adsk.core.ValueInput.createByReal((quantity))
    circularFeatInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
    circularFeatInput.isSymmetric = False
    circularFeats.add(circularFeatInput)


def undo(design):
    app = adsk.core.Application.get()
    ui_local = app.userInterface
    
    cmd = ui_local.commandDefinitions.itemById('UndoCommand')
    cmd.execute()


def delete(design):
    """
    Remove every body and sketch from the design so nothing is left
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    bodies = rootComp.bRepBodies
    removeFeat = rootComp.features.removeFeatures

    # Delete from back to front
    for i in range(bodies.count - 1, -1, -1):
        body = bodies.item(i)
        removeFeat.add(body)


def export_as_STEP(design, Name):
    exportMgr = design.exportManager
          
    directory_name = "Fusion_Exports"
    FilePath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
    Export_dir_path = os.path.join(FilePath, directory_name, Name)
    os.makedirs(Export_dir_path, exist_ok=True) 
    
    stepOptions = exportMgr.createSTEPExportOptions(Export_dir_path + f'/{Name}.step')
    
    res = exportMgr.execute(stepOptions)
    if not res:
        raise RuntimeError("STEP export failed")


def cut_extrude(design, depth):
    rootComp = design.rootComponent 
    sketches = rootComp.sketches
    sketch = sketches.item(sketches.count - 1)
    prof = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(depth)
    extrudeInput.setDistanceExtent(False, distance)
    extrudes.add(extrudeInput)


def extrude_thin(design, thickness, distance):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    
    selectedFace = sketches.item(sketches.count - 1).profiles.item(0)
    exts = rootComp.features.extrudeFeatures
    extInput = exts.createInput(selectedFace, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Center,
                            adsk.core.ValueInput.createByReal(thickness))

    distanceExtent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(distance))
    extInput.setOneSideExtent(distanceExtent, adsk.fusion.ExtentDirections.PositiveExtentDirection)

    ext = exts.add(extInput)


def draw_cylinder(design, radius, height, x, y, z, plane="XY"):
    """
    Draws a cylinder with given radius and height at position (x,y,z)
    """
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    if plane == "XZ":
        sketch = sketches.add(rootComp.xZConstructionPlane)
    elif plane == "YZ":
        sketch = sketches.add(rootComp.yZConstructionPlane)
    else:
        sketch = sketches.add(xyPlane)

    center = adsk.core.Point3D.create(x, y, z)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)

    prof = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(height)
    extInput.setDistanceExtent(False, distance)
    extrudes.add(extInput)


def export_as_STL(design, Name):
    """
    Export model as STL
    """
    rootComp = design.rootComponent
    
    exportMgr = design.exportManager

    stlRootOptions = exportMgr.createSTLExportOptions(rootComp)
    
    directory_name = "Fusion_Exports"
    FilePath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
    Export_dir_path = os.path.join(FilePath, directory_name, Name)
    os.makedirs(Export_dir_path, exist_ok=True) 

    printUtils = stlRootOptions.availablePrintUtilities

    # export the root component to the print utility, instead of a specified file            
    for printUtil in printUtils:
        stlRootOptions.sendToPrintUtility = True
        stlRootOptions.printUtility = printUtil
        exportMgr.execute(stlRootOptions)

    # export the occurrence one by one in the root component to a specified file
    allOccu = rootComp.allOccurrences
    for occ in allOccu:
        Name = Export_dir_path + "/" + occ.component.name
        
        # create stl exportOptions
        stlExportOptions = exportMgr.createSTLExportOptions(occ, Name)
        stlExportOptions.sendToPrintUtility = False
        
        exportMgr.execute(stlExportOptions)

    # export the body one by one in the design to a specified file
    allBodies = rootComp.bRepBodies
    for body in allBodies:
        Name = Export_dir_path + "/" + body.parentComponent.name + '-' + body.name 
        
        # create stl exportOptions
        stlExportOptions = exportMgr.createSTLExportOptions(body, Name)
        stlExportOptions.sendToPrintUtility = False
        
        exportMgr.execute(stlExportOptions)


def get_model_parameters(design):
    model_params = []
    user_params = design.userParameters
    for param in design.allParameters:
        if all(user_params.item(i) != param for i in range(user_params.count)):
            try:
                wert = str(param.value)
            except Exception:
                wert = ""
            model_params.append({
                "Name": str(param.name),
                "Wert": wert,
                "Einheit": str(param.unit),
                "Expression": str(param.expression) if param.expression else ""
            })
    return model_params


def get_current_model_state(design):
    """Returns the current state of the model for validation purposes."""
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        sketches = rootComp.sketches
        
        # Get body information
        body_list = []
        for i in range(bodies.count):
            body = bodies.item(i)
            bb = body.boundingBox
            body_list.append({
                "name": body.name,
                "index": i,
                "volume_cm3": round(body.volume, 4),
                "bounding_box": {
                    "min": [round(bb.minPoint.x, 2), round(bb.minPoint.y, 2), round(bb.minPoint.z, 2)],
                    "max": [round(bb.maxPoint.x, 2), round(bb.maxPoint.y, 2), round(bb.maxPoint.z, 2)]
                }
            })
        
        # Get sketch information
        sketch_list = []
        for i in range(sketches.count):
            sketch = sketches.item(i)
            sketch_list.append({
                "name": sketch.name,
                "index": i,
                "profile_count": sketch.profiles.count,
                "is_visible": sketch.isVisible
            })
        
        return {
            "body_count": bodies.count,
            "sketch_count": sketches.count,
            "bodies": body_list,
            "sketches": sketch_list,
            "design_name": design.rootComponent.name
        }
    except Exception as e:
        return {"error": str(e)}

def get_faces_info(design, body_index=0):
    """Returns detailed face information for a body."""
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        
        if body_index >= bodies.count:
            return {"error": f"Body index {body_index} out of range (max {bodies.count-1})"}
        
        body = bodies.item(body_index)
        faces = body.faces
        
        face_list = []
        for i in range(faces.count):
            face = faces.item(i)
            # Get face centroid
            centroid = face.centroid
            # Get face area
            area = face.area
            # Get face type
            geom = face.geometry
            face_type = geom.objectType.split('::')[-1] if geom else "Unknown"
            
            face_list.append({
                "index": i,
                "type": face_type,
                "area_cm2": round(area, 4),
                "centroid": [round(centroid.x, 2), round(centroid.y, 2), round(centroid.z, 2)]
            })
        
        return {
            "body_name": body.name,
            "body_index": body_index,
            "face_count": faces.count,
            "faces": face_list
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def execute_fusion_script(design, ui, script_code):
    """Execute arbitrary Python code in Fusion 360 context."""
    global script_result, script_result_lock
    import sys
    from io import StringIO
    
    # Capture stdout
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
        # Create execution context with useful variables
        exec_globals = {
            "__builtins__": __builtins__,
            "adsk": adsk,
            "app": app,
            "ui": ui,
            "design": design,
            "rootComp": design.rootComponent if design else None,
            "math": math,
            "json": json,
        }
        exec_locals = {}
        
        # Execute the script
        exec(script_code, exec_globals, exec_locals)
        
        # Check if there's a 'result' variable in the script
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
        # Extract line number from traceback
        tb = traceback.extract_tb(sys.exc_info()[2])
        if tb:
            result["error_line"] = tb[-1].lineno
        result["traceback"] = traceback.format_exc()
    
    finally:
        # Capture output
        result["stdout"] = sys.stdout.getvalue()
        result["stderr"] = sys.stderr.getvalue()
        
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Add model state after execution
        result["model_state"] = get_current_model_state(design)
        
        # Store result thread-safely
        with script_result_lock:
            script_result = result

def set_parameter(design, name, value):
    param = design.allParameters.itemByName(name)
    param.expression = value


def holes(design, points, width=1.0, distance=1.0, faceindex=0):
    """
    Create one or more holes on a selected face.
    """
    rootComp = design.rootComponent
    holes = rootComp.features.holeFeatures
    sketches = rootComp.sketches
    
    bodies = rootComp.bRepBodies

    if bodies.count > 0:
        latest_body = bodies.item(bodies.count - 1)
    else:
        raise ValueError("No bodies found for holes.")
    
    entities = adsk.core.ObjectCollection.create()
    entities.add(latest_body.faces.item(faceindex))
    sk = sketches.add(latest_body.faces.item(faceindex))

    tipangle = 90.0
    for i in range(len(points)):
        holePoint = sk.sketchPoints.add(adsk.core.Point3D.create(points[i][0], points[i][1], 0))
        tipangle = adsk.core.ValueInput.createByString('180 deg')
        holedistance = adsk.core.ValueInput.createByReal(distance)
        
        holeDiam = adsk.core.ValueInput.createByReal(width)
        holeInput = holes.createSimpleInput(holeDiam)
        holeInput.tipAngle = tipangle
        holeInput.setPositionBySketchPoint(holePoint)
        holeInput.setDistanceExtent(holedistance)

        # Add the hole
        holes.add(holeInput)


def select_body(design, Bodyname):
    rootComp = design.rootComponent 
    target_body = rootComp.bRepBodies.itemByName(Bodyname)
    if target_body is None:
        raise ValueError(f"Body with the name: '{Bodyname}' could not be found.")

    return target_body


def select_sketch(design, Sketchname):
    rootComp = design.rootComponent 
    target_sketch = rootComp.sketches.itemByName(Sketchname)
    if target_sketch is None:
        raise ValueError(f"Sketch with the name: '{Sketchname}' could not be found.")

    return target_sketch


def wait_for_result(timeout=None):
    """Wait for a result from the result queue with optional timeout"""
    global result_queue, TASK_TIMEOUT
    if timeout is None:
        timeout = TASK_TIMEOUT
    try:
        result = result_queue.get(timeout=timeout)
        return result
    except queue.Empty:
        return {"success": False, "error": "Task timed out waiting for result"}


def send_task_and_wait(handler, task_tuple, success_message):
    """Helper to queue a task, wait for result, and send appropriate HTTP response"""
    global task_queue
    
    # Clear any stale results from queue
    while not result_queue.empty():
        try:
            result_queue.get_nowait()
        except queue.Empty:
            break
    
    # Queue the task
    task_queue.put(task_tuple)
    
    # Wait for result
    result = wait_for_result()
    
    if result.get("success"):
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps({"success": True, "message": success_message}).encode('utf-8'))
    else:
        handler.send_response(500)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        error_msg = result.get("error", "Unknown error")
        handler.wfile.write(json.dumps({"success": False, "error": error_msg}).encode('utf-8'))


# HTTP Server######
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global ModelParameterSnapshot, design
        try:
            if self.path == '/count_parameters':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"user_parameter_count": len(ModelParameterSnapshot)}).encode('utf-8'))
            elif self.path == '/list_parameters':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ModelParameter": ModelParameterSnapshot}).encode('utf-8'))
            elif self.path == '/model_state':
                # Return current model state for validation
                state = get_current_model_state(design)
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(state).encode('utf-8'))
            elif self.path.startswith('/faces_info'):
                # Get face info for a body
                import urllib.parse
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                body_idx = int(params.get('body_index', [0])[0])
                faces = get_faces_info(design, body_idx)
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(faces).encode('utf-8'))
            elif self.path == '/script_result':
                # Get the result of the last script execution
                global script_result, script_result_lock
                with script_result_lock:
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(script_result).encode('utf-8'))
            else:
                self.send_error(404,'Not Found')
        except Exception as e:
            self.send_error(500,str(e))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length',0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data) if post_data else {}
            path = self.path

            # Execute script endpoint
            if path == '/execute_script':
                script_code = data.get('script', '')
                if script_code:
                    # Reset result status
                    global script_result, script_result_lock
                    with script_result_lock:
                        script_result = {"status": "pending", "result": None, "error": None}
                    
                    send_task_and_wait(self, ('execute_script', script_code), "Script executed")
                else:
                    self.send_error(400, 'No script provided')
                return

            # Alle Aktionen in die Queue legen
            elif path.startswith('/set_parameter'):
                name = data.get('name')
                value = data.get('value')
                if name and value:
                    send_task_and_wait(self, ('set_parameter', name, value), f"Parameter {name} set")

            elif path == '/undo':
                send_task_and_wait(self, ('undo',), "Undo executed")

            elif path == '/Box':
                height = float(data.get('height', 5))
                width = float(data.get('width', 5))
                depth = float(data.get('depth', 5))
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                z = float(data.get('z', 0))
                Plane = data.get('plane', None)

                send_task_and_wait(self, ('draw_box', height, width, depth, x, y, z, Plane), "Box created")

            elif path == '/Export_STL':
                name = str(data.get('Name', 'Test.stl'))
                send_task_and_wait(self, ('export_stl', name), "STL export completed")

            elif path == '/Export_STEP':
                name = str(data.get('name', 'Test.step'))
                send_task_and_wait(self, ('export_step', name), "STEP export completed")

            elif path == '/fillet_edges':
                radius = float(data.get('radius', 0.3))
                send_task_and_wait(self, ('fillet_edges', radius), "Fillet edges completed")

            elif path == '/draw_cylinder':
                radius = float(data.get('radius'))
                height = float(data.get('height'))
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                z = float(data.get('z', 0))
                plane = data.get('plane', 'XY')
                send_task_and_wait(self, ('draw_cylinder', radius, height, x, y, z, plane), "Cylinder created")

            elif path == '/shell_body':
                thickness = float(data.get('thickness', 0.5))
                faceindex = int(data.get('faceindex', 0))
                send_task_and_wait(self, ('shell_body', thickness, faceindex), "Shell body created")

            elif path == '/draw_lines':
                points = data.get('points', [])
                Plane = data.get('plane', 'XY')
                send_task_and_wait(self, ('draw_lines', points, Plane), "Lines created")
            
            elif path == '/extrude_last_sketch':
                value = float(data.get('value', 1.0))
                taperangle = float(data.get('taperangle'))
                send_task_and_wait(self, ('extrude_last_sketch', value, taperangle), "Extrusion completed")
                
            elif path == '/revolve':
                angle = float(data.get('angle', 360))
                send_task_and_wait(self, ('revolve_profile', angle), "Revolve completed")

            elif path == '/arc':
                point1 = data.get('point1', [0, 0])
                point2 = data.get('point2', [1, 1])
                point3 = data.get('point3', [2, 0])
                connect = bool(data.get('connect', False))
                plane = data.get('plane', 'XY')
                send_task_and_wait(self, ('arc', point1, point2, point3, connect, plane), "Arc created")
            
            elif path == '/draw_one_line':
                x1 = float(data.get('x1', 0))
                y1 = float(data.get('y1', 0))
                z1 = float(data.get('z1', 0))
                x2 = float(data.get('x2', 1))
                y2 = float(data.get('y2', 1))
                z2 = float(data.get('z2', 0))
                plane = data.get('plane', 'XY')
                send_task_and_wait(self, ('draw_one_line', x1, y1, z1, x2, y2, z2, plane), "Line created")
            
            elif path == '/holes':
                points = data.get('points', [[0, 0]])
                width = float(data.get('width', 1.0))
                faceindex = int(data.get('faceindex', 0))
                distance = data.get('depth', None)
                if distance is not None:
                    distance = float(distance)
                through = bool(data.get('through', False))
                send_task_and_wait(self, ('holes', points, width, distance, faceindex), "Hole created")

            elif path == '/create_circle':
                radius = float(data.get('radius', 1.0))
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                z = float(data.get('z', 0))
                plane = data.get('plane', 'XY')
                send_task_and_wait(self, ('circle', radius, x, y, z, plane), "Circle created")

            elif path == '/extrude_thin':
                thickness = float(data.get('thickness', 0.5))
                distance = float(data.get('distance', 1.0))
                send_task_and_wait(self, ('extrude_thin', thickness, distance), "Thin extrusion created")

            elif path == '/select_body':
                name = str(data.get('name', ''))
                send_task_and_wait(self, ('select_body', name), "Body selected")

            elif path == '/select_sketch':
                name = str(data.get('name', ''))
                send_task_and_wait(self, ('select_sketch', name), "Sketch selected")

            elif path == '/sweep':
                send_task_and_wait(self, ('sweep',), "Sweep created")
            
            elif path == '/spline':
                points = data.get('points', [])
                plane = data.get('plane', 'XY')
                send_task_and_wait(self, ('spline', points, plane), "Spline created")

            elif path == '/cut_extrude':
                depth = float(data.get('depth', 1.0))
                send_task_and_wait(self, ('cut_extrude', depth), "Cut extrusion completed")
            
            elif path == '/circular_pattern':
                quantity = float(data.get('quantity',))
                axis = str(data.get('axis', "X"))
                plane = str(data.get('plane', 'XY'))
                send_task_and_wait(self, ('circular_pattern', quantity, axis, plane), "Circular pattern created")
            
            elif path == '/offsetplane':
                offset = float(data.get('offset', 0.0))
                plane = str(data.get('plane', 'XY'))
                send_task_and_wait(self, ('offsetplane', offset, plane), "Offset plane created")

            elif path == '/loft':
                sketchcount = int(data.get('sketchcount', 2))
                send_task_and_wait(self, ('loft', sketchcount), "Loft created")
            
            elif path == '/ellipsis':
                x_center = float(data.get('x_center', 0))
                y_center = float(data.get('y_center', 0))
                z_center = float(data.get('z_center', 0))
                x_major = float(data.get('x_major', 10))
                y_major = float(data.get('y_major', 0))
                z_major = float(data.get('z_major', 0))
                x_through = float(data.get('x_through', 5))
                y_through = float(data.get('y_through', 4))
                z_through = float(data.get('z_through', 0))
                plane = str(data.get('plane', 'XY'))
                send_task_and_wait(self, ('ellipsis', x_center, y_center, z_center,
                                 x_major, y_major, z_major, x_through, y_through, z_through, plane), "Ellipse created")
                 
            elif path == '/sphere':
                radius = float(data.get('radius', 5.0))
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                z = float(data.get('z', 0))
                plane = data.get('plane', 'XY')
                send_task_and_wait(self, ('draw_sphere', radius, x, y, z, plane), "Sphere created")

            elif path == '/threaded':
                inside = bool(data.get('inside', True))
                allsizes = int(data.get('allsizes', 30))
                send_task_and_wait(self, ('threaded', inside, allsizes), "Thread created")
                
            elif path == '/delete_everything':
                send_task_and_wait(self, ('delete_everything',), "All bodies deleted")
                
            elif path == '/boolean_operation':
                operation = data.get('operation', 'join')
                send_task_and_wait(self, ('boolean_operation', operation), "Boolean operation completed")
            
            elif path == '/test_connection':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Connection successful"}).encode('utf-8'))
            
            elif path == '/draw_2d_rectangle':
                x_1 = float(data.get('x_1', 0))
                y_1 = float(data.get('y_1', 0))
                z_1 = float(data.get('z_1', 0))
                x_2 = float(data.get('x_2', 1))
                y_2 = float(data.get('y_2', 1))
                z_2 = float(data.get('z_2', 0))
                plane = data.get('plane', 'XY')
                send_task_and_wait(self, ('draw_2d_rectangle', x_1, y_1, z_1, x_2, y_2, z_2, plane), "2D rectangle created")
            
            elif path == '/rectangular_pattern':
                quantity_one = float(data.get('quantity_one', 2))
                distance_one = float(data.get('distance_one', 5))
                axis_one = str(data.get('axis_one', "X"))
                quantity_two = float(data.get('quantity_two', 2))
                distance_two = float(data.get('distance_two', 5))
                axis_two = str(data.get('axis_two', "Y"))
                plane = str(data.get('plane', 'XY'))
                send_task_and_wait(self, ('rectangular_pattern', axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane), "Rectangular pattern created")
                 
            elif path == '/draw_text':
                text = str(data.get('text', "Hello"))
                x_1 = float(data.get('x_1', 0))
                y_1 = float(data.get('y_1', 0))
                z_1 = float(data.get('z_1', 0))
                x_2 = float(data.get('x_2', 10))
                y_2 = float(data.get('y_2', 4))
                z_2 = float(data.get('z_2', 0))
                extrusion_value = float(data.get('extrusion_value', 1.0))
                plane = str(data.get('plane', 'XY'))
                thickness = float(data.get('thickness', 0.5))
                send_task_and_wait(self, ('draw_text', text, thickness, x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value, plane), "Text created")
                 
            elif path == '/move_body':
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                z = float(data.get('z', 0))
                send_task_and_wait(self, ('move_body', x, y, z), "Body moved")
            
            else:
                self.send_error(404,'Not Found')

        except Exception as e:
            self.send_error(500,str(e))

def run_server():
    global httpd
    server_address = ('localhost',5000)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()


def run(context):
    global app, ui, design, handlers, stopFlag, customEvent
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)

        if design is None:
            ui.messageBox("No active design open!")
            return

        # Initial snapshot
        global ModelParameterSnapshot
        ModelParameterSnapshot = get_model_parameters(design)

        # Register custom event
        customEvent = app.registerCustomEvent(myCustomEvent)  # Every 200ms we create a custom event which doesn't interfere with Fusion main thread
        onTaskEvent = TaskEventHandler()  # If we have tasks in the queue, we process them in the main thread
        customEvent.add(onTaskEvent)  # Here we add the event handler
        handlers.append(onTaskEvent)

        # Start task thread
        stopFlag = threading.Event()
        taskThread = TaskThread(stopFlag)
        taskThread.daemon = True
        taskThread.start()

        ui.messageBox(f"Fusion HTTP Add-In started! Port 5000.\nParameters loaded: {len(ModelParameterSnapshot)} model parameters")

        # HTTP-Server starten
        threading.Thread(target=run_server, daemon=True).start()

    except:
        try:
            ui.messageBox('Fehler im Add-In:\n{}'.format(traceback.format_exc()))
        except:
            pass




def stop(context):
    global stopFlag, httpd, task_queue, handlers, app, customEvent
    
    # Stop the task thread
    if stopFlag:
        stopFlag.set()

    # Clean up event handlers
    for handler in handlers:
        try:
            if customEvent:
                customEvent.remove(handler)
        except:
            pass
    
    handlers.clear()

    # Clear the queue without processing (avoid freezing)
    while not task_queue.empty():
        try:
            task_queue.get_nowait() 
            if task_queue.empty(): 
                break
        except:
            break

    # Stop HTTP server
    if httpd:
        try:
            httpd.shutdown()
        except:
            pass

  
    if httpd:
        try:
            httpd.shutdown()
            httpd.server_close()
        except:
            pass
        httpd = None
    try:
        app = adsk.core.Application.get()
        if app:
            ui = app.userInterface
            if ui:
                ui.messageBox("Fusion HTTP Add-In gestoppt")
    except:
        pass
