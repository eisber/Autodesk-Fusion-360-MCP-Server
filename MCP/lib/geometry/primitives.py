"""3D Primitive geometry functions for Fusion 360.

This module contains functions for creating 3D primitive shapes like boxes,
cylinders, and spheres.
"""

import adsk.core
import adsk.fusion
import traceback
import math


def draw_box(design, ui, height, width, depth, x, y, z, plane=None):
    """
    Draws a box with given dimensions at the specified position.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        height: Height of the box
        width: Width of the box
        depth: Depth of the box (extrusion distance)
        x: X coordinate of the center
        y: Y coordinate of the center
        z: Z offset (creates offset construction plane)
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
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
    except:
        if ui:
            ui.messageBox('Failed draw_box:\n{}'.format(traceback.format_exc()))


def draw_cylinder(design, ui, radius, height, x, y, z, plane="XY"):
    """
    Draws a cylinder with given radius and height at the specified position.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        radius: Radius of the cylinder
        height: Height of the cylinder
        x: X coordinate of the center
        y: Y coordinate of the center
        z: Z coordinate of the center
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

        center = adsk.core.Point3D.create(x, y, z)
        sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)

        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(height)
        extInput.setDistanceExtent(False, distance)
        extrudes.add(extInput)
    except:
        if ui:
            ui.messageBox('Failed draw_cylinder:\n{}'.format(traceback.format_exc()))


def create_sphere(design, ui, radius, x, y, z):
    """
    Creates a sphere by revolving a semicircle.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        radius: Radius of the sphere
        x: X coordinate of the center
        y: Y coordinate of the center
        z: Z coordinate of the center
    """
    try:
        rootComp = design.rootComponent
        component = design.rootComponent
        sketches = rootComp.sketches
        
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        
        # Draw a circle
        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(adsk.core.Point3D.create(x, y, z), radius)
        
        # Draw a line to use as the axis of revolution
        lines = sketch.sketchCurves.sketchLines
        axisLine = lines.addByTwoPoints(
            adsk.core.Point3D.create(x - radius, y, z),
            adsk.core.Point3D.create(x + radius, y, z)
        )

        # Get the profile defined by half of the circle
        profile = sketch.profiles.item(0)
        
        # Create a revolution input
        revolves = component.features.revolveFeatures
        revInput = revolves.createInput(
            profile, axisLine,
            adsk.fusion.FeatureOperations.NewComponentFeatureOperation
        )
        
        # Define that the extent is an angle of 2*pi to get a sphere
        angle = adsk.core.ValueInput.createByReal(2 * math.pi)
        revInput.setAngleExtent(False, angle)
        
        # Create the revolution
        revolves.add(revInput)
    except:
        if ui:
            ui.messageBox('Failed create_sphere:\n{}'.format(traceback.format_exc()))
