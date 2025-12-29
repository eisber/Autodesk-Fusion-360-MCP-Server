"""2D Sketch geometry functions for Fusion 360.

This module contains functions for creating 2D sketch elements like circles,
ellipses, rectangles, lines, arcs, splines, and text.
"""

import adsk.core
import adsk.fusion
import traceback


def draw_circle(design, ui, radius, x, y, z, plane="XY"):
    """
    Draws a circle with given radius at the specified position.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        radius: Radius of the circle
        x: X coordinate
        y: Y coordinate
        z: Z coordinate (offset for XY plane)
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes
        
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
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
    except:
        if ui:
            ui.messageBox('Failed draw_circle:\n{}'.format(traceback.format_exc()))


def draw_ellipse(design, ui, x_center, y_center, z_center,
                 x_major, y_major, z_major, x_through, y_through, z_through, plane="XY"):
    """
    Draws an ellipse on the specified plane using three points.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        x_center, y_center, z_center: Center point coordinates
        x_major, y_major, z_major: Major axis point coordinates
        x_through, y_through, z_through: Point on the ellipse
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        
        centerPoint = adsk.core.Point3D.create(float(x_center), float(y_center), float(z_center))
        majorAxisPoint = adsk.core.Point3D.create(float(x_major), float(y_major), float(z_major))
        throughPoint = adsk.core.Point3D.create(float(x_through), float(y_through), float(z_through))
        
        sketchEllipse = sketch.sketchCurves.sketchEllipses
        sketchEllipse.add(centerPoint, majorAxisPoint, throughPoint)
    except:
        if ui:
            ui.messageBox('Failed draw_ellipse:\n{}'.format(traceback.format_exc()))


def draw_2d_rectangle(design, ui, x_1, y_1, z_1, x_2, y_2, z_2, plane="XY"):
    """
    Draws a 2D rectangle on the specified plane.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        x_1, y_1, z_1: First corner coordinates
        x_2, y_2, z_2: Second corner coordinates
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes

        if plane == "XZ":
            baseplane = rootComp.xZConstructionPlane
            if y_1 != 0 and y_2 != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(y_1)
                planeInput.setByOffset(baseplane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(baseplane)
        elif plane == "YZ":
            baseplane = rootComp.yZConstructionPlane
            if x_1 != 0 and x_2 != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(x_1)
                planeInput.setByOffset(baseplane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(baseplane)
        else:
            baseplane = rootComp.xYConstructionPlane
            if z_1 != 0 and z_2 != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(z_1)
                planeInput.setByOffset(baseplane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(baseplane)

        rectangles = sketch.sketchCurves.sketchLines
        point_1 = adsk.core.Point3D.create(x_1, y_1, z_1)
        point_2 = adsk.core.Point3D.create(x_2, y_2, z_2)
        rectangles.addTwoPointRectangle(point_1, point_2)
    except:
        if ui:
            ui.messageBox('Failed draw_2d_rectangle:\n{}'.format(traceback.format_exc()))


def draw_lines(design, ui, points, plane="XY"):
    """
    Draws lines between the given points on the specified plane.
    Connects the last point to the first point to close the shape.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        points: List of points [(x1,y1,z1), (x2,y2,z2), ...]
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        
        for i in range(len(points) - 1):
            start = adsk.core.Point3D.create(points[i][0], points[i][1], 0)
            end = adsk.core.Point3D.create(points[i+1][0], points[i+1][1], 0)
            sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        
        # Close the shape
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points[-1][0], points[-1][1], 0),
            adsk.core.Point3D.create(points[0][0], points[0][1], 0)
        )
    except:
        if ui:
            ui.messageBox('Failed draw_lines:\n{}'.format(traceback.format_exc()))


def draw_one_line(design, ui, x1, y1, z1, x2, y2, z2, plane="XY"):
    """
    Draws a single line between two points on the last sketch.
    Designed to be used after arc to create closed shapes.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        x1, y1, z1: Start point coordinates
        x2, y2, z2: End point coordinates
        plane: Construction plane (not used, uses last sketch)
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)
        
        start = adsk.core.Point3D.create(x1, y1, 0)
        end = adsk.core.Point3D.create(x2, y2, 0)
        sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    except:
        if ui:
            ui.messageBox('Failed draw_one_line:\n{}'.format(traceback.format_exc()))


def draw_arc(design, ui, point1, point2, point3, plane="XY", connect=False):
    """
    Creates an arc between three points on the specified plane.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        point1: Start point [x, y, z]
        point2: Through point [x, y, z]
        point3: End point [x, y, z]
        plane: Construction plane ("XY", "XZ", or "YZ")
        connect: If True, connects start and end with a line
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        
        start = adsk.core.Point3D.create(point1[0], point1[1], point1[2])
        alongpoint = adsk.core.Point3D.create(point2[0], point2[1], point2[2])
        endpoint = adsk.core.Point3D.create(point3[0], point3[1], point3[2])
        
        arcs = sketch.sketchCurves.sketchArcs
        arcs.addByThreePoints(start, alongpoint, endpoint)
        
        if connect:
            lines = sketch.sketchCurves.sketchLines
            lines.addByTwoPoints(
                adsk.core.Point3D.create(start.x, start.y, start.z),
                adsk.core.Point3D.create(endpoint.x, endpoint.y, endpoint.z)
            )
    except:
        if ui:
            ui.messageBox('Failed draw_arc:\n{}'.format(traceback.format_exc()))


def draw_spline(design, ui, points, plane="XY"):
    """
    Draws a spline through the given points on the specified plane.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        points: List of points [[x1,y1,z1], [x2,y2,z2], ...]
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        
        splinePoints = adsk.core.ObjectCollection.create()
        for point in points:
            splinePoints.add(adsk.core.Point3D.create(point[0], point[1], point[2]))
        
        sketch.sketchCurves.sketchFittedSplines.add(splinePoints)
    except:
        if ui:
            ui.messageBox('Failed draw_spline:\n{}'.format(traceback.format_exc()))


def draw_text(design, ui, text, thickness, x_1, y_1, z_1, x_2, y_2, z_2, value, plane="XY"):
    """
    Draws text on a sketch and extrudes it.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        text: Text string to draw
        thickness: Text height/thickness
        x_1, y_1, z_1: First corner of text bounds
        x_2, y_2, z_2: Second corner of text bounds
        value: Extrusion distance
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        
        # Create text
        texts = sketch.sketchTexts
        textInput = texts.createInput2(text, thickness)
        
        corner1 = adsk.core.Point3D.create(x_1, y_1, z_1)
        corner2 = adsk.core.Point3D.create(x_2, y_2, z_2)
        textInput.setAsMultiLine(corner1, corner2, adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                                  adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
        
        texts.add(textInput)
        
        # Extrude if value is provided
        if value != 0 and sketch.profiles.count > 0:
            prof = sketch.profiles.item(0)
            extrudes = rootComp.features.extrudeFeatures
            extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            distance = adsk.core.ValueInput.createByReal(value)
            extInput.setDistanceExtent(False, distance)
            extrudes.add(extInput)
    except:
        if ui:
            ui.messageBox('Failed draw_text:\n{}'.format(traceback.format_exc()))
