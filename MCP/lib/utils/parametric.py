"""Parametric modeling utility functions for Fusion 360.

This module contains functions for managing parameters, sketches,
timeline, and construction geometry.
"""

import adsk.core
import adsk.fusion
import traceback
import math


# =============================================================================
# User Parameters
# =============================================================================

def create_user_parameter(design, name, value, unit="mm", comment=""):
    """Create a new user parameter in the design.
    
    Args:
        design: Fusion 360 design object
        name: Parameter name
        value: Parameter value (as string expression)
        unit: Unit type (default "mm")
        comment: Optional comment
        
    Returns:
        Dict with success status and parameter details
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        userParams = design.userParameters
        
        # Check if parameter already exists
        existingParam = userParams.itemByName(name)
        if existingParam:
            return {"error": f"Parameter '{name}' already exists"}
        
        # Create the parameter
        unitType = unit if unit else ""
        valueInput = adsk.core.ValueInput.createByString(str(value) + " " + unitType if unitType else str(value))
        
        newParam = userParams.add(name, valueInput, unitType, comment)
        
        return {
            "success": True,
            "parameter_name": newParam.name,
            "value": newParam.value,
            "expression": newParam.expression,
            "unit": newParam.unit
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def delete_user_parameter(design, name):
    """Delete a user parameter from the design.
    
    Args:
        design: Fusion 360 design object
        name: Parameter name to delete
        
    Returns:
        Dict with success status and message
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        userParams = design.userParameters
        param = userParams.itemByName(name)
        
        if param is None:
            return {"error": f"Parameter '{name}' not found"}
        
        if param.isDeletable:
            param.deleteMe()
            return {"success": True, "message": f"Parameter '{name}' deleted"}
        else:
            return {"error": f"Parameter '{name}' cannot be deleted (may be in use)"}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# =============================================================================
# Sketch Analysis
# =============================================================================

def get_sketch_info(design, sketch_index=-1):
    """Get detailed information about a sketch.
    
    Args:
        design: Fusion 360 design object
        sketch_index: Index of the sketch (-1 for last sketch)
        
    Returns:
        Dict with sketch details including curves, dimensions, and constraints
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if sketches.count == 0:
            return {"error": "No sketches in the design"}
        
        if sketch_index < 0:
            sketch_index = sketches.count + sketch_index
        
        if sketch_index >= sketches.count or sketch_index < 0:
            return {"error": f"Sketch index {sketch_index} out of range"}
        
        sketch = sketches.item(sketch_index)
        
        # Get curves
        curves = []
        for i in range(sketch.sketchCurves.count):
            curve = sketch.sketchCurves.item(i)
            curve_type = curve.objectType.split('::')[-1]
            curve_info = {"index": i, "type": curve_type}
            
            if hasattr(curve, 'startSketchPoint') and curve.startSketchPoint:
                curve_info["start"] = [round(curve.startSketchPoint.geometry.x, 4),
                                       round(curve.startSketchPoint.geometry.y, 4),
                                       round(curve.startSketchPoint.geometry.z, 4)]
            if hasattr(curve, 'endSketchPoint') and curve.endSketchPoint:
                curve_info["end"] = [round(curve.endSketchPoint.geometry.x, 4),
                                     round(curve.endSketchPoint.geometry.y, 4),
                                     round(curve.endSketchPoint.geometry.z, 4)]
            if hasattr(curve, 'length'):
                curve_info["length"] = round(curve.length, 4)
            
            curves.append(curve_info)
        
        # Get dimensions
        dimensions = []
        for i in range(sketch.sketchDimensions.count):
            dim = sketch.sketchDimensions.item(i)
            dim_info = {
                "index": i,
                "type": dim.objectType.split('::')[-1],
            }
            if hasattr(dim, 'parameter') and dim.parameter:
                dim_info["name"] = dim.parameter.name
                dim_info["value"] = dim.parameter.value
                dim_info["expression"] = dim.parameter.expression
            dimensions.append(dim_info)
        
        # Get constraints
        constraints = []
        for i in range(sketch.geometricConstraints.count):
            constraint = sketch.geometricConstraints.item(i)
            constraints.append({
                "index": i,
                "type": constraint.objectType.split('::')[-1]
            })
        
        return {
            "sketch_name": sketch.name,
            "sketch_index": sketch_index,
            "is_fully_constrained": sketch.isFullyConstrained,
            "profile_count": sketch.profiles.count,
            "curve_count": len(curves),
            "curves": curves,
            "dimension_count": len(dimensions),
            "dimensions": dimensions,
            "constraint_count": len(constraints),
            "constraints": constraints
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def get_sketch_constraints(design, sketch_index=-1):
    """Get all geometric constraints in a sketch.
    
    Args:
        design: Fusion 360 design object
        sketch_index: Index of the sketch (-1 for last sketch)
        
    Returns:
        Dict with constraint information
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if sketches.count == 0:
            return {"error": "No sketches in the design"}
        
        if sketch_index < 0:
            sketch_index = sketches.count + sketch_index
        
        if sketch_index >= sketches.count or sketch_index < 0:
            return {"error": f"Sketch index {sketch_index} out of range"}
        
        sketch = sketches.item(sketch_index)
        
        constraints = []
        for i in range(sketch.geometricConstraints.count):
            constraint = sketch.geometricConstraints.item(i)
            constraints.append({
                "index": i,
                "type": constraint.objectType.split('::')[-1]
            })
        
        return {
            "sketch_name": sketch.name,
            "constraint_count": len(constraints),
            "constraints": constraints
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def get_sketch_dimensions(design, sketch_index=-1):
    """Get all dimensions in a sketch.
    
    Args:
        design: Fusion 360 design object
        sketch_index: Index of the sketch (-1 for last sketch)
        
    Returns:
        Dict with dimension information
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        
        if sketches.count == 0:
            return {"error": "No sketches in the design"}
        
        if sketch_index < 0:
            sketch_index = sketches.count + sketch_index
        
        if sketch_index >= sketches.count or sketch_index < 0:
            return {"error": f"Sketch index {sketch_index} out of range"}
        
        sketch = sketches.item(sketch_index)
        
        dimensions = []
        for i in range(sketch.sketchDimensions.count):
            dim = sketch.sketchDimensions.item(i)
            dim_info = {
                "index": i,
                "type": dim.objectType.split('::')[-1],
            }
            if hasattr(dim, 'parameter') and dim.parameter:
                dim_info["name"] = dim.parameter.name
                dim_info["value"] = dim.parameter.value
                dim_info["expression"] = dim.parameter.expression
                dim_info["unit"] = dim.parameter.unit
            dimensions.append(dim_info)
        
        return {
            "sketch_name": sketch.name,
            "dimension_count": len(dimensions),
            "dimensions": dimensions
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# =============================================================================
# Interference Check
# =============================================================================

def check_interference(design, body1_index=0, body2_index=1):
    """Check for interference between two bodies.
    
    Args:
        design: Fusion 360 design object
        body1_index: Index of first body
        body2_index: Index of second body
        
    Returns:
        Dict with interference status and volume
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        
        if bodies.count < 2:
            return {"error": "Need at least 2 bodies for interference check"}
        
        if body1_index >= bodies.count:
            return {"error": f"Body1 index {body1_index} out of range"}
        if body2_index >= bodies.count:
            return {"error": f"Body2 index {body2_index} out of range"}
        
        body1 = bodies.item(body1_index)
        body2 = bodies.item(body2_index)
        
        interferenceInput = rootComp.features.interferenceFeatures.createInput([body1], [body2])
        interferenceInput.areCoincidentFacesIncluded = False
        
        results = rootComp.features.interferenceFeatures.analyze(interferenceInput)
        
        has_interference = results.count > 0
        interference_volume = 0
        
        if has_interference:
            for i in range(results.count):
                result = results.item(i)
                if result.interferenceBody:
                    interference_volume += result.interferenceBody.volume
        
        return {
            "has_interference": has_interference,
            "interference_volume_cm3": round(interference_volume, 6),
            "body1_name": body1.name,
            "body2_name": body2.name
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def check_all_interferences(design):
    """Check for interference between all bodies.
    
    Args:
        design: Fusion 360 design object
        
    Returns:
        Dict with all interference pairs and volumes
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        
        if bodies.count < 2:
            return {"error": "Need at least 2 bodies for interference check", "total_bodies": bodies.count}
        
        interferences = []
        
        for i in range(bodies.count):
            for j in range(i + 1, bodies.count):
                body1 = bodies.item(i)
                body2 = bodies.item(j)
                
                try:
                    interferenceInput = rootComp.features.interferenceFeatures.createInput([body1], [body2])
                    interferenceInput.areCoincidentFacesIncluded = False
                    results = rootComp.features.interferenceFeatures.analyze(interferenceInput)
                    
                    if results.count > 0:
                        volume = 0
                        for k in range(results.count):
                            result = results.item(k)
                            if result.interferenceBody:
                                volume += result.interferenceBody.volume
                        
                        interferences.append({
                            "body1_index": i,
                            "body1_name": body1.name,
                            "body2_index": j,
                            "body2_name": body2.name,
                            "volume_cm3": round(volume, 6)
                        })
                except:
                    pass
        
        return {
            "total_bodies": bodies.count,
            "interference_count": len(interferences),
            "interferences": interferences
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# =============================================================================
# Timeline Management
# =============================================================================

def get_timeline_info(design):
    """Get information about the design timeline.
    
    Args:
        design: Fusion 360 design object
        
    Returns:
        Dict with timeline features and current position
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        timeline = design.timeline
        
        features = []
        for i in range(timeline.count):
            item = timeline.item(i)
            feature_info = {
                "index": i,
                "name": item.name if hasattr(item, 'name') else f"Feature{i}",
                "is_suppressed": item.isSuppressed if hasattr(item, 'isSuppressed') else False,
                "is_rolled_back": item.isRolledBack if hasattr(item, 'isRolledBack') else False,
            }
            
            if hasattr(item, 'entity') and item.entity:
                feature_info["type"] = item.entity.objectType.split('::')[-1]
            
            features.append(feature_info)
        
        current_position = timeline.count
        for i in range(timeline.count):
            if timeline.item(i).isRolledBack:
                current_position = i
                break
        
        return {
            "feature_count": timeline.count,
            "current_position": current_position,
            "features": features
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def rollback_to_feature(design, feature_index):
    """Roll back the timeline to a specific feature.
    
    Args:
        design: Fusion 360 design object
        feature_index: Index of the feature to roll back to
        
    Returns:
        Dict with success status
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        timeline = design.timeline
        
        if feature_index < 0 or feature_index >= timeline.count:
            return {"error": f"Feature index {feature_index} out of range (0-{timeline.count-1})"}
        
        markerPosition = timeline.item(feature_index)
        timeline.markerPosition = markerPosition
        
        return {
            "success": True,
            "current_position": feature_index,
            "message": f"Rolled back to feature {feature_index}"
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def rollback_to_end(design):
    """Roll the timeline forward to the end.
    
    Args:
        design: Fusion 360 design object
        
    Returns:
        Dict with success status
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        timeline = design.timeline
        timeline.moveToEnd()
        
        return {
            "success": True,
            "current_position": timeline.count
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def suppress_feature(design, feature_index, suppress=True):
    """Suppress or unsuppress a feature in the timeline.
    
    Args:
        design: Fusion 360 design object
        feature_index: Index of the feature
        suppress: True to suppress, False to unsuppress
        
    Returns:
        Dict with success status and feature state
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        timeline = design.timeline
        
        if feature_index < 0 or feature_index >= timeline.count:
            return {"error": f"Feature index {feature_index} out of range"}
        
        item = timeline.item(feature_index)
        item.isSuppressed = suppress
        
        return {
            "success": True,
            "feature_name": item.name if hasattr(item, 'name') else f"Feature{feature_index}",
            "is_suppressed": item.isSuppressed
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# =============================================================================
# Mass Properties
# =============================================================================

def get_mass_properties(design, body_index=0, material_density=None):
    """Get mass properties of a body.
    
    Args:
        design: Fusion 360 design object
        body_index: Index of the body
        material_density: Optional density in g/cm³ (default 7.85 for steel)
        
    Returns:
        Dict with mass, center of gravity, moments of inertia
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        
        if body_index >= bodies.count:
            return {"error": f"Body index {body_index} out of range"}
        
        body = bodies.item(body_index)
        physProps = body.physicalProperties
        
        density = material_density if material_density else 7.85
        volume = body.volume
        mass = volume * density
        
        cog = physProps.centerOfMass
        principal_moments = physProps.principalMoments
        
        return {
            "body_name": body.name,
            "volume_cm3": round(volume, 6),
            "density_g_cm3": density,
            "mass_g": round(mass, 4),
            "center_of_gravity": [round(cog.x, 4), round(cog.y, 4), round(cog.z, 4)],
            "moments_of_inertia": {
                "Ixx": round(principal_moments.x * density, 6),
                "Iyy": round(principal_moments.y * density, 6),
                "Izz": round(principal_moments.z * density, 6)
            },
            "radii_of_gyration": {
                "kx": round(math.sqrt(principal_moments.x / volume), 4) if volume > 0 else 0,
                "ky": round(math.sqrt(principal_moments.y / volume), 4) if volume > 0 else 0,
                "kz": round(math.sqrt(principal_moments.z / volume), 4) if volume > 0 else 0
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# =============================================================================
# Construction Geometry
# =============================================================================

def create_offset_plane(design, offset, base_plane="XY"):
    """Create a construction plane offset from a base plane.
    
    Args:
        design: Fusion 360 design object
        offset: Offset distance in cm
        base_plane: Base plane ("XY", "XZ", or "YZ")
        
    Returns:
        Dict with success status and plane name
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        planes = rootComp.constructionPlanes
        planeInput = planes.createInput()
        
        if base_plane == "XY":
            basePlane = rootComp.xYConstructionPlane
        elif base_plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
        elif base_plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
        else:
            return {"error": f"Invalid base plane: {base_plane}"}
        
        offsetValue = adsk.core.ValueInput.createByReal(offset)
        planeInput.setByOffset(basePlane, offsetValue)
        
        newPlane = planes.add(planeInput)
        
        return {
            "success": True,
            "plane_name": newPlane.name
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def create_plane_at_angle(design, angle, base_plane="XY", axis="X"):
    """Create a construction plane at an angle to a base plane.
    
    Args:
        design: Fusion 360 design object
        angle: Angle in degrees
        base_plane: Base plane ("XY", "XZ", or "YZ")
        axis: Rotation axis ("X", "Y", or "Z")
        
    Returns:
        Dict with success status and plane name
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        planes = rootComp.constructionPlanes
        planeInput = planes.createInput()
        
        if base_plane == "XY":
            basePlane = rootComp.xYConstructionPlane
        elif base_plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
        elif base_plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
        else:
            return {"error": f"Invalid base plane: {base_plane}"}
        
        if axis == "X":
            axisLine = rootComp.xConstructionAxis
        elif axis == "Y":
            axisLine = rootComp.yConstructionAxis
        elif axis == "Z":
            axisLine = rootComp.zConstructionAxis
        else:
            return {"error": f"Invalid axis: {axis}"}
        
        angleValue = adsk.core.ValueInput.createByString(f"{angle} deg")
        planeInput.setByAngle(axisLine, angleValue, basePlane)
        
        newPlane = planes.add(planeInput)
        
        return {
            "success": True,
            "plane_name": newPlane.name
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def create_midplane(design, body_index, face1_index, face2_index):
    """Create a construction plane midway between two faces.
    
    Args:
        design: Fusion 360 design object
        body_index: Index of the body
        face1_index: Index of first face
        face2_index: Index of second face
        
    Returns:
        Dict with success status and plane name
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        
        if body_index >= bodies.count:
            return {"error": f"Body index {body_index} out of range"}
        
        body = bodies.item(body_index)
        faces = body.faces
        
        if face1_index >= faces.count:
            return {"error": f"Face1 index {face1_index} out of range"}
        if face2_index >= faces.count:
            return {"error": f"Face2 index {face2_index} out of range"}
        
        face1 = faces.item(face1_index)
        face2 = faces.item(face2_index)
        
        planes = rootComp.constructionPlanes
        planeInput = planes.createInput()
        planeInput.setByTwoPlanes(face1, face2)
        
        newPlane = planes.add(planeInput)
        
        return {
            "success": True,
            "plane_name": newPlane.name
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def create_construction_axis(design, axis_type, body_index=0, edge_index=0, 
                             face_index=0, point1=None, point2=None):
    """Create a construction axis.
    
    Args:
        design: Fusion 360 design object
        axis_type: Type of axis ("two_points", "edge", "normal", "cylinder")
        body_index: Index of the body (for edge/normal/cylinder types)
        edge_index: Index of the edge (for edge type)
        face_index: Index of the face (for normal/cylinder types)
        point1: First point [x, y, z] (for two_points type)
        point2: Second point [x, y, z] (for two_points type)
        
    Returns:
        Dict with success status and axis name
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        axes = rootComp.constructionAxes
        axisInput = axes.createInput()
        
        if axis_type == "two_points":
            if point1 is None or point2 is None:
                return {"error": "two_points type requires point1 and point2"}
            p1 = adsk.core.Point3D.create(point1[0], point1[1], point1[2])
            p2 = adsk.core.Point3D.create(point2[0], point2[1], point2[2])
            axisInput.setByTwoPoints(adsk.fusion.ConstructionPointInput.createByPoint(p1),
                                     adsk.fusion.ConstructionPointInput.createByPoint(p2))
        elif axis_type == "edge":
            body = rootComp.bRepBodies.item(body_index)
            edge = body.edges.item(edge_index)
            axisInput.setByLine(edge)
        elif axis_type == "normal":
            body = rootComp.bRepBodies.item(body_index)
            face = body.faces.item(face_index)
            axisInput.setByNormalToFaceAtPoint(face, face.centroid)
        elif axis_type == "cylinder":
            body = rootComp.bRepBodies.item(body_index)
            face = body.faces.item(face_index)
            if face.geometry.objectType == 'adsk::core::Cylinder':
                axisInput.setByCircularFace(face)
            else:
                return {"error": "Face is not cylindrical"}
        else:
            return {"error": f"Unknown axis type: {axis_type}"}
        
        newAxis = axes.add(axisInput)
        
        return {
            "success": True,
            "axis_name": newAxis.name
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def create_construction_point(design, point_type, x=0, y=0, z=0, 
                              body_index=0, vertex_index=0, edge_index=0):
    """Create a construction point.
    
    Args:
        design: Fusion 360 design object
        point_type: Type of point ("coordinates", "vertex", "center", "midpoint")
        x, y, z: Coordinates (for coordinates type)
        body_index: Index of the body
        vertex_index: Index of the vertex (for vertex type)
        edge_index: Index of the edge (for center/midpoint types)
        
    Returns:
        Dict with success status, point name, and coordinates
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        points = rootComp.constructionPoints
        pointInput = points.createInput()
        
        if point_type == "coordinates":
            point = adsk.core.Point3D.create(x, y, z)
            pointInput.setByPoint(point)
            coords = [x, y, z]
        elif point_type == "vertex":
            body = rootComp.bRepBodies.item(body_index)
            vertex = body.vertices.item(vertex_index)
            pointInput.setByPoint(vertex)
            coords = [vertex.geometry.x, vertex.geometry.y, vertex.geometry.z]
        elif point_type == "center":
            body = rootComp.bRepBodies.item(body_index)
            edge = body.edges.item(edge_index)
            pointInput.setByCenter(edge)
            geom = edge.geometry
            if hasattr(geom, 'center'):
                coords = [geom.center.x, geom.center.y, geom.center.z]
            else:
                coords = [0, 0, 0]
        elif point_type == "midpoint":
            body = rootComp.bRepBodies.item(body_index)
            edge = body.edges.item(edge_index)
            evaluator = edge.evaluator
            _, startParam, endParam = evaluator.getParameterExtents()
            midParam = (startParam + endParam) / 2
            _, midPoint = evaluator.getPointAtParameter(midParam)
            pointInput.setByPoint(midPoint)
            coords = [midPoint.x, midPoint.y, midPoint.z]
        else:
            return {"error": f"Unknown point type: {point_type}"}
        
        newPoint = points.add(pointInput)
        
        return {
            "success": True,
            "point_name": newPoint.name,
            "coordinates": [round(c, 4) for c in coords]
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def list_construction_geometry(design):
    """List all construction geometry in the design.
    
    Args:
        design: Fusion 360 design object
        
    Returns:
        Dict with planes, axes, and points
    """
    try:
        if design is None:
            return {"error": "No active design"}
        
        rootComp = design.rootComponent
        
        # List planes
        planes = []
        for i in range(rootComp.constructionPlanes.count):
            plane = rootComp.constructionPlanes.item(i)
            planes.append({
                "index": i,
                "name": plane.name
            })
        
        # List axes
        axes = []
        for i in range(rootComp.constructionAxes.count):
            axis = rootComp.constructionAxes.item(i)
            geom = axis.geometry
            direction = [round(geom.direction.x, 4), round(geom.direction.y, 4), 
                        round(geom.direction.z, 4)] if geom else None
            axes.append({
                "index": i,
                "name": axis.name,
                "direction": direction
            })
        
        # List points
        points = []
        for i in range(rootComp.constructionPoints.count):
            point = rootComp.constructionPoints.item(i)
            geom = point.geometry
            position = [round(geom.x, 4), round(geom.y, 4), round(geom.z, 4)] if geom else None
            points.append({
                "index": i,
                "name": point.name,
                "position": position
            })
        
        return {
            "plane_count": len(planes),
            "planes": planes,
            "axis_count": len(axes),
            "axes": axes,
            "point_count": len(points),
            "points": points
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
