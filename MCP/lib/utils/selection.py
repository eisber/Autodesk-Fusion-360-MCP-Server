"""Selection functions for Fusion 360.

This module contains functions for selecting bodies and sketches by name.
"""

import adsk.core
import adsk.fusion
import traceback


def select_body(design, ui, body_name):
    """
    Selects a body by name.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        body_name: Name of the body to select
        
    Returns:
        The body object if found, None otherwise
    """
    try:
        rootComp = design.rootComponent
        target_body = rootComp.bRepBodies.itemByName(body_name)
        if target_body is None:
            if ui:
                ui.messageBox(f"Body with name '{body_name}' not found.")
        return target_body
    except:
        if ui:
            ui.messageBox('Failed select_body:\n{}'.format(traceback.format_exc()))
        return None


def select_sketch(design, ui, sketch_name):
    """
    Selects a sketch by name.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        sketch_name: Name of the sketch to select
        
    Returns:
        The sketch object if found, None otherwise
    """
    try:
        rootComp = design.rootComponent
        target_sketch = rootComp.sketches.itemByName(sketch_name)
        if target_sketch is None:
            if ui:
                ui.messageBox(f"Sketch with name '{sketch_name}' not found.")
        return target_sketch
    except:
        if ui:
            ui.messageBox('Failed select_sketch:\n{}'.format(traceback.format_exc()))
        return None
