"""Extrusion functions for Fusion 360.

This module contains functions for creating extrusions including regular,
thin-wall, and cut extrusions.
"""

import adsk.core
import adsk.fusion
import traceback


def extrude_last_sketch(design, ui, value, taperangle=0):
    """
    Extrudes the last sketch by the given value.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        value: Extrusion distance
        taperangle: Taper angle in degrees (default 0)
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)  # Last sketch
        prof = sketch.profiles.item(0)  # First profile
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(value)
        
        if taperangle != 0:
            taperValue = adsk.core.ValueInput.createByString(f'{taperangle} deg')
            extent_distance = adsk.fusion.DistanceExtentDefinition.create(distance)
            extrudeInput.setOneSideExtent(
                extent_distance,
                adsk.fusion.ExtentDirections.PositiveExtentDirection,
                taperValue
            )
        else:
            extrudeInput.setDistanceExtent(False, distance)
        
        extrudes.add(extrudeInput)
    except:
        if ui:
            ui.messageBox('Failed extrude_last_sketch:\n{}'.format(traceback.format_exc()))


def extrude_thin(design, ui, thickness, distance):
    """
    Creates a thin-wall extrusion from the last sketch.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        thickness: Wall thickness
        distance: Extrusion distance
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        selectedFace = sketches.item(sketches.count - 1).profiles.item(0)
        exts = rootComp.features.extrudeFeatures
        extInput = exts.createInput(selectedFace, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extInput.setThinExtrude(
            adsk.fusion.ThinExtrudeWallLocation.Center,
            adsk.core.ValueInput.createByReal(thickness)
        )

        distanceExtent = adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(distance)
        )
        extInput.setOneSideExtent(distanceExtent, adsk.fusion.ExtentDirections.PositiveExtentDirection)

        exts.add(extInput)
    except:
        if ui:
            ui.messageBox('Failed extrude_thin:\n{}'.format(traceback.format_exc()))


def cut_extrude(design, ui, depth):
    """
    Creates a cut extrusion from the last sketch.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        depth: Cut depth (should be negative for downward cut)
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sketch = sketches.item(sketches.count - 1)  # Last sketch
        prof = sketch.profiles.item(0)  # First profile
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(depth)
        extrudeInput.setDistanceExtent(False, distance)
        extrudes.add(extrudeInput)
    except:
        if ui:
            ui.messageBox('Failed cut_extrude:\n{}'.format(traceback.format_exc()))
