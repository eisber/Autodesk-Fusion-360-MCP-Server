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
        List of parameter dictionaries with Name, Value, Unit, Expression
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
                "Value": wert,
                "Unit": str(param.unit),
                "Expression": str(param.expression) if param.expression else ""
            })
    return model_params


def get_current_model_state(design):
    """
    Get the current state of the model with spatial descriptions.

    Only includes visible bodies and sketches in the response.
    Includes human-readable spatial_summary aligned with Fusion ViewCube.

    Args:
        design: Fusion 360 design object

    Returns:
        Dictionary with body_count, sketch_count, bodies, sketches, spatial_summary, design_name
    """
    try:
        if design is None:
            return {"error": "No active design"}

        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        sketches = rootComp.sketches

        # Collect body data (only visible bodies)
        # Use isLightBulbOn for user's explicit visibility setting
        body_list = []
        body_data = []  # For spatial calculations

        for i in range(bodies.count):
            body = bodies.item(i)
            if not body.isLightBulbOn:
                continue
            bb = body.boundingBox

            # Dimensions (W×D×H aligned with Fusion axes)
            width = round(bb.maxPoint.x - bb.minPoint.x, 2)   # X = left-right
            depth = round(bb.maxPoint.y - bb.minPoint.y, 2)   # Y = front-back
            height = round(bb.maxPoint.z - bb.minPoint.z, 2)  # Z = bottom-top

            # Centers
            cx = round((bb.minPoint.x + bb.maxPoint.x) / 2, 2)
            cy = round((bb.minPoint.y + bb.maxPoint.y) / 2, 2)
            cz = round((bb.minPoint.z + bb.maxPoint.z) / 2, 2)

            body_info = {
                "name": body.name,
                "index": i,
                "size": f"{width}x{depth}x{height}",  # W×D×H in cm
                "center": [cx, cy, cz],
                "z_range": [round(bb.minPoint.z, 2), round(bb.maxPoint.z, 2)],
            }
            body_list.append(body_info)

            # Store for relationship calculations
            body_data.append({
                "index": i, "name": body.name,
                "min": (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z),
                "max": (bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z),
                "center": (cx, cy, cz),
                "width": width, "depth": depth, "height": height
            })

        # Generate spatial summary
        spatial_summary = _generate_spatial_summary(body_data)

        # Get sketch information (only visible sketches, minimal)
        # Use isLightBulbOn instead of isVisible - isLightBulbOn reflects the
        # user's explicit visibility toggle in the browser, while isVisible
        # can be True even when the sketch appears hidden due to parent visibility
        sketch_list = []
        for i in range(sketches.count):
            sketch = sketches.item(i)
            if not sketch.isLightBulbOn:
                continue
            sketch_list.append({
                "name": sketch.name,
                "index": i,
            })

        return {
            "body_count": len(body_list),
            "sketch_count": len(sketch_list),
            "bodies": body_list,
            "sketches": sketch_list,
            "spatial_summary": spatial_summary,
            "design_name": rootComp.name,
        }
    except Exception as e:
        return {"error": str(e)}


def _generate_spatial_summary(body_data):
    """Generate concise spatial description aligned with Fusion ViewCube.

    Fusion coordinate system:
    - X: LEFT (-) to RIGHT (+)
    - Y: FRONT (-) to BACK (+)
    - Z: BOTTOM (-) to TOP (+)
    """
    if not body_data:
        return "Empty model"

    lines = []

    # Sort by Z (bottom to top) for logical reading order
    sorted_bodies = sorted(body_data, key=lambda b: b['min'][2])

    for bd in sorted_bodies:
        # Size in human terms
        size_desc = f"{bd['width']}x{bd['depth']}x{bd['height']}cm (WxDxH)"

        # Orientation description based on dominant dimension
        orientation = _describe_orientation(bd['width'], bd['depth'], bd['height'])

        # Position description
        pos_parts = []

        # Horizontal position (X): LEFT/RIGHT
        if bd['center'][0] > 0.05:
            pos_parts.append(f"{bd['center'][0]:.1f}cm right")
        elif bd['center'][0] < -0.05:
            pos_parts.append(f"{abs(bd['center'][0]):.1f}cm left")

        # Depth position (Y): FRONT/BACK (note: +Y is BACK in Fusion)
        if bd['center'][1] > 0.05:
            pos_parts.append(f"{bd['center'][1]:.1f}cm back")
        elif bd['center'][1] < -0.05:
            pos_parts.append(f"{abs(bd['center'][1]):.1f}cm front")

        # Vertical position (Z): ground reference
        if bd['min'][2] > 0.05:
            pos_parts.append(f"at Z={bd['min'][2]:.1f}")
        elif bd['min'][2] < -0.05:
            pos_parts.append(f"at Z={bd['min'][2]:.1f} (below origin)")
        else:
            pos_parts.append("on ground")

        pos_str = ", ".join(pos_parts) if pos_parts else "at origin"

        # Relationships to other bodies (max 2)
        relations = []
        for other in sorted_bodies:
            if other['index'] == bd['index']:
                continue
            rel = _get_spatial_relationship(bd, other)
            if rel:
                relations.append(rel)

        # Build line
        rel_str = f" [{'; '.join(relations[:2])}]" if relations else ""
        lines.append(f"- {bd['name']}: {orientation}, {size_desc}, {pos_str}{rel_str}")

    return "\n".join(lines)


def _describe_orientation(width, depth, height):
    """Describe the orientation/shape of a body based on its dimensions.
    
    Returns a human-readable description like:
    - "flat horizontal plate" (thin in Z, spread in XY)
    - "tall vertical column" (thin in XY, tall in Z)
    - "elongated left-right" (longest in X)
    - "elongated front-back" (longest in Y)
    - "roughly cubic" (similar dimensions)
    """
    # Avoid division by zero
    w = max(width, 0.001)
    d = max(depth, 0.001)
    h = max(height, 0.001)
    
    max_dim = max(w, d, h)
    min_dim = min(w, d, h)
    
    # Check if roughly cubic (all dimensions within 2x of each other)
    if max_dim / min_dim < 2.0:
        return "roughly cubic"
    
    # Find dominant and smallest dimensions
    dims = [('width', w), ('depth', d), ('height', h)]
    dims_sorted = sorted(dims, key=lambda x: x[1], reverse=True)
    longest_name, longest_val = dims_sorted[0]
    shortest_name, shortest_val = dims_sorted[2]
    
    # Check aspect ratio for classification
    ratio = longest_val / shortest_val
    
    # Flat plate: height is much smaller than width and depth
    if shortest_name == 'height' and ratio > 3:
        return "flat horizontal plate"
    
    # Tall column: height is dominant, width and depth are small
    if longest_name == 'height' and ratio > 3:
        if w < h * 0.5 and d < h * 0.5:
            return "tall vertical column"
        else:
            return "vertically oriented"
    
    # Elongated in specific direction
    if longest_name == 'width' and ratio > 2:
        return "elongated left-right (X)"
    if longest_name == 'depth' and ratio > 2:
        return "elongated front-back (Y)"
    if longest_name == 'height' and ratio > 2:
        return "elongated vertically (Z)"
    
    # Default for irregular shapes
    return "irregular shape"


def _get_spatial_relationship(body_a, body_b):
    """Describe relationship from body_a's perspective to body_b.

    Uses Fusion ViewCube directions:
    - TOP/BOTTOM = Z axis
    - FRONT/BACK = Y axis (FRONT = -Y, BACK = +Y)
    - LEFT/RIGHT = X axis
    """
    a_min, a_max = body_a['min'], body_a['max']
    b_min, b_max = body_b['min'], body_b['max']
    b_name = body_b['name']

    # Vertical (Z) - most important for assembly understanding
    if a_min[2] >= b_max[2] - 0.01:  # A is above B
        gap = a_min[2] - b_max[2]
        if gap < 0.02:
            return f"on top of {b_name}"
        else:
            return f"{gap:.1f}cm above {b_name}"

    if a_max[2] <= b_min[2] + 0.01:  # A is below B
        gap = b_min[2] - a_max[2]
        if gap < 0.02:
            return f"below {b_name}"
        else:
            return f"{gap:.1f}cm below {b_name}"

    # Horizontal relationships (only if not vertically separated)
    # X axis: LEFT/RIGHT
    if a_max[0] <= b_min[0] - 0.01:
        return f"left of {b_name}"
    if a_min[0] >= b_max[0] + 0.01:
        return f"right of {b_name}"

    # Y axis: FRONT/BACK (remember +Y = BACK in Fusion)
    if a_max[1] <= b_min[1] - 0.01:
        return f"in front of {b_name}"
    if a_min[1] >= b_max[1] + 0.01:
        return f"behind {b_name}"

    # Check for containment
    if (a_min[0] >= b_min[0] and a_max[0] <= b_max[0] and
        a_min[1] >= b_min[1] and a_max[1] <= b_max[1] and
        a_min[2] >= b_min[2] and a_max[2] <= b_max[2]):
        return f"inside {b_name}"

    # Overlapping - don't clutter output
    return None


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
