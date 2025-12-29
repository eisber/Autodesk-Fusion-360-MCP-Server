"""Transform functions for Fusion 360.

This module contains functions for moving bodies and creating offset planes.
"""

import adsk.core
import adsk.fusion
import traceback


def move_last_body(design, ui, x, y, z):
    """
    Moves the last created body by the specified vector.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        x: X translation distance
        y: Y translation distance
        z: Z translation distance
    """
    try:
        rootComp = design.rootComponent
        features = rootComp.features
        moveFeats = features.moveFeatures
        body = rootComp.bRepBodies
        bodies = adsk.core.ObjectCollection.create()
        
        if body.count > 0:
            latest_body = body.item(body.count - 1)
            bodies.add(latest_body)
        else:
            ui.messageBox("No bodies found.")
            return

        vector = adsk.core.Vector3D.create(x, y, z)
        transform = adsk.core.Matrix3D.create()
        transform.translation = vector
        moveFeatureInput = moveFeats.createInput2(bodies)
        moveFeatureInput.defineAsFreeMove(transform)
        moveFeats.add(moveFeatureInput)
    except:
        if ui:
            ui.messageBox('Failed move_last_body:\n{}'.format(traceback.format_exc()))


def offsetplane(design, ui, offset, plane="XY"):
    """
    Creates an offset construction plane.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        offset: Offset distance
        plane: Base plane ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        offset_val = adsk.core.ValueInput.createByReal(offset)
        ctorPlanes = rootComp.constructionPlanes
        ctorPlaneInput = ctorPlanes.createInput()
        
        if plane == "XY":
            ctorPlaneInput.setByOffset(rootComp.xYConstructionPlane, offset_val)
        elif plane == "XZ":
            ctorPlaneInput.setByOffset(rootComp.xZConstructionPlane, offset_val)
        elif plane == "YZ":
            ctorPlaneInput.setByOffset(rootComp.yZConstructionPlane, offset_val)
        else:
            ctorPlaneInput.setByOffset(rootComp.xYConstructionPlane, offset_val)
            
        ctorPlanes.add(ctorPlaneInput)
    except:
        if ui:
            ui.messageBox('Failed offsetplane:\n{}'.format(traceback.format_exc()))
