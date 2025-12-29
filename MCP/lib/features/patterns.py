"""Pattern functions for Fusion 360.

This module contains functions for creating circular and rectangular patterns.
"""

import adsk.core
import adsk.fusion
import traceback


def circular_pattern(design, ui, quantity, axis, plane):
    """
    Creates a circular pattern of the last body.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        quantity: Number of instances in the pattern
        axis: Rotation axis ("X", "Y", or "Z")
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        circularFeats = rootComp.features.circularPatternFeatures
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("No bodies found.")
            return
            
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(latest_body)
        
        if plane == "XY":
            sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketches.add(rootComp.yZConstructionPlane)
        
        if axis == "Y":
            axisObj = rootComp.yConstructionAxis
        elif axis == "X":
            axisObj = rootComp.xConstructionAxis
        elif axis == "Z":
            axisObj = rootComp.zConstructionAxis
        else:
            axisObj = rootComp.zConstructionAxis

        circularFeatInput = circularFeats.createInput(inputEntites, axisObj)
        circularFeatInput.quantity = adsk.core.ValueInput.createByReal(quantity)
        circularFeatInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
        circularFeatInput.isSymmetric = False
        circularFeats.add(circularFeatInput)
    except:
        if ui:
            ui.messageBox('Failed circular_pattern:\n{}'.format(traceback.format_exc()))


def rectangular_pattern(design, ui, axis_one, axis_two, quantity_one, quantity_two, 
                        distance_one, distance_two, plane="XY"):
    """
    Creates a rectangular pattern of the last body.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        axis_one: First axis direction ("X", "Y", or "Z")
        axis_two: Second axis direction ("X", "Y", or "Z")
        quantity_one: Number of instances in first direction
        quantity_two: Number of instances in second direction
        distance_one: Spacing in first direction
        distance_two: Spacing in second direction
        plane: Construction plane ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        rectFeats = rootComp.features.rectangularPatternFeatures

        quantity_one_val = adsk.core.ValueInput.createByString(f"{quantity_one}")
        quantity_two_val = adsk.core.ValueInput.createByString(f"{quantity_two}")
        distance_one_val = adsk.core.ValueInput.createByString(f"{distance_one}")
        distance_two_val = adsk.core.ValueInput.createByString(f"{distance_two}")

        bodies = rootComp.bRepBodies
        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("No bodies found.")
            return
            
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(latest_body)
        
        # Get first axis
        if axis_one == "Y":
            baseaxis_one = rootComp.yConstructionAxis
        elif axis_one == "X":
            baseaxis_one = rootComp.xConstructionAxis
        elif axis_one == "Z":
            baseaxis_one = rootComp.zConstructionAxis
        else:
            baseaxis_one = rootComp.xConstructionAxis

        # Get second axis
        if axis_two == "Y":
            baseaxis_two = rootComp.yConstructionAxis
        elif axis_two == "X":
            baseaxis_two = rootComp.xConstructionAxis
        elif axis_two == "Z":
            baseaxis_two = rootComp.zConstructionAxis
        else:
            baseaxis_two = rootComp.yConstructionAxis

        rectangularPatternInput = rectFeats.createInput(
            inputEntites,
            baseaxis_one,
            quantity_one_val,
            distance_one_val,
            adsk.fusion.PatternDistanceType.SpacingPatternDistanceType
        )
        rectangularPatternInput.setDirectionTwo(baseaxis_two, quantity_two_val, distance_two_val)
        rectFeats.add(rectangularPatternInput)
    except:
        if ui:
            ui.messageBox('Failed rectangular_pattern:\n{}'.format(traceback.format_exc()))
