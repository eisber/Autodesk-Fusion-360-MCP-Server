"""State management functions for Fusion 360.

This module contains functions for querying and modifying model state,
including parameters, model state inspection, and undo/delete operations.
"""

import adsk.core
import adsk.fusion
import traceback


def get_model_parameters(design):
    """
    Gets all model parameters (excluding user parameters).
    
    Args:
        design: Fusion 360 design object
        
    Returns:
        List of parameter dictionaries with Name, Wert, Einheit, Expression
    """
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
    """
    Get the current state of the model for validation purposes.

    Args:
        design: Fusion 360 design object

    Returns:
        Dictionary with body_count, sketch_count, bodies, sketches, design_name
    """
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
                    "max": [round(bb.maxPoint.x, 2), round(bb.maxPoint.y, 2), round(bb.maxPoint.z, 2)],
                },
            })

        # Get sketch information
        sketch_list = []
        for i in range(sketches.count):
            sketch = sketches.item(i)
            sketch_list.append({
                "name": sketch.name,
                "index": i,
                "profile_count": sketch.profiles.count,
                "is_visible": sketch.isVisible,
            })

        return {
            "body_count": bodies.count,
            "sketch_count": sketches.count,
            "bodies": body_list,
            "sketches": sketch_list,
            "design_name": design.rootComponent.name,
        }
    except Exception as e:
        return {"error": str(e)}


def get_faces_info(design, body_index=0):
    """
    Get detailed face information for a body.

    Args:
        design: Fusion 360 design object
        body_index: Index of the body to inspect (default 0)

    Returns:
        Dictionary with body_name, body_index, face_count, faces
    """
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
            centroid = face.centroid
            area = face.area
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


def set_parameter(design, ui, name, value):
    """
    Sets a parameter value by name.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        name: Parameter name
        value: New expression value
    """
    try:
        param = design.allParameters.itemByName(name)
        param.expression = value
    except:
        if ui:
            ui.messageBox('Failed set_parameter:\n{}'.format(traceback.format_exc()))


def undo(design, ui):
    """
    Executes an undo operation.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
    """
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        cmd = ui.commandDefinitions.itemById('UndoCommand')
        cmd.execute()
    except:
        if ui:
            ui.messageBox('Failed undo:\n{}'.format(traceback.format_exc()))


def delete_all(design, ui):
    """
    Removes all bodies from the design.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        removeFeat = rootComp.features.removeFeatures

        # Delete from back to front
        for i in range(bodies.count - 1, -1, -1):
            body = bodies.item(i)
            removeFeat.add(body)
    except:
        if ui:
            ui.messageBox('Failed delete_all:\n{}'.format(traceback.format_exc()))
