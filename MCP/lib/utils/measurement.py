"""Measurement utility functions for Fusion 360.

This module contains functions for measuring distances, angles,
areas, volumes, and other geometric properties.
"""

import math
import traceback

import adsk.core
import adsk.fusion

from lib.registry import task


def get_entity_from_body(design, entity_type, entity_index, body_index=0):
    """Helper function to get an entity (face, edge, vertex) from a body.

    Args:
        design: Fusion 360 design object
        entity_type: Type of entity ("face", "edge", "vertex", "body")
        entity_index: Index of the entity in the body
        body_index: Index of the body (default 0)

    Returns:
        The requested entity object

    Raises:
        ValueError: If index is out of range or entity type is unknown
    """
    rootComp = design.rootComponent
    bodies = rootComp.bRepBodies

    if body_index >= bodies.count:
        raise ValueError(f"Body index {body_index} out of range (max {bodies.count - 1})")

    body = bodies.item(body_index)

    if entity_type == "face":
        if entity_index >= body.faces.count:
            raise ValueError(f"Face index {entity_index} out of range (max {body.faces.count - 1})")
        return body.faces.item(entity_index)
    elif entity_type == "edge":
        if entity_index >= body.edges.count:
            raise ValueError(f"Edge index {entity_index} out of range (max {body.edges.count - 1})")
        return body.edges.item(entity_index)
    elif entity_type == "vertex":
        if entity_index >= body.vertices.count:
            raise ValueError(
                f"Vertex index {entity_index} out of range (max {body.vertices.count - 1})"
            )
        return body.vertices.item(entity_index)
    elif entity_type == "body":
        return body
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")


@task
def measure_distance(
    design, entity1_type, entity1_index, entity2_type, entity2_index, body1_index=0, body2_index=0
):
    """Measure the minimum distance between two entities.

    Args:
        design: Fusion 360 design object
        entity1_type: Type of first entity ("face", "edge", "vertex")
        entity1_index: Index of first entity
        entity2_type: Type of second entity
        entity2_index: Index of second entity
        body1_index: Body index for first entity
        body2_index: Body index for second entity

    Returns:
        Dict with distance_cm, distance_mm, point1, point2
    """
    try:
        if design is None:
            return {"error": "No active design"}

        entity1 = get_entity_from_body(design, entity1_type, entity1_index, body1_index)
        entity2 = get_entity_from_body(design, entity2_type, entity2_index, body2_index)

        app = adsk.core.Application.get()
        measureMgr = app.measureManager

        result = measureMgr.measureMinimumDistance(entity1, entity2)

        return {
            "distance_cm": round(result.value, 6),
            "distance_mm": round(result.value * 10, 6),
            "point1": [
                round(result.positionOne.x, 4),
                round(result.positionOne.y, 4),
                round(result.positionOne.z, 4),
            ],
            "point2": [
                round(result.positionTwo.x, 4),
                round(result.positionTwo.y, 4),
                round(result.positionTwo.z, 4),
            ],
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@task
def measure_angle(
    design, entity1_type, entity1_index, entity2_type, entity2_index, body1_index=0, body2_index=0
):
    """Measure the angle between two planar faces or linear edges.

    Args:
        design: Fusion 360 design object
        entity1_type: Type of first entity ("face" or "edge")
        entity1_index: Index of first entity
        entity2_type: Type of second entity
        entity2_index: Index of second entity
        body1_index: Body index for first entity
        body2_index: Body index for second entity

    Returns:
        Dict with angle_degrees and angle_radians
    """
    try:
        if design is None:
            return {"error": "No active design"}

        entity1 = get_entity_from_body(design, entity1_type, entity1_index, body1_index)
        entity2 = get_entity_from_body(design, entity2_type, entity2_index, body2_index)

        # Get geometry for angle calculation
        if entity1_type == "face":
            geom1 = entity1.geometry
            if hasattr(geom1, "normal"):
                vec1 = geom1.normal
            else:
                return {"error": "Face 1 is not planar, cannot measure angle"}
        elif entity1_type == "edge":
            geom1 = entity1.geometry
            if hasattr(geom1, "direction"):
                vec1 = geom1.direction
            else:
                return {"error": "Edge 1 is not linear, cannot measure angle"}
        else:
            return {"error": f"Cannot measure angle for entity type: {entity1_type}"}

        if entity2_type == "face":
            geom2 = entity2.geometry
            if hasattr(geom2, "normal"):
                vec2 = geom2.normal
            else:
                return {"error": "Face 2 is not planar, cannot measure angle"}
        elif entity2_type == "edge":
            geom2 = entity2.geometry
            if hasattr(geom2, "direction"):
                vec2 = geom2.direction
            else:
                return {"error": "Edge 2 is not linear, cannot measure angle"}
        else:
            return {"error": f"Cannot measure angle for entity type: {entity2_type}"}

        # Calculate angle using dot product
        dot = vec1.x * vec2.x + vec1.y * vec2.y + vec1.z * vec2.z
        dot = max(-1.0, min(1.0, dot))
        angle_rad = math.acos(abs(dot))
        angle_deg = math.degrees(angle_rad)

        return {"angle_degrees": round(angle_deg, 4), "angle_radians": round(angle_rad, 6)}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@task
def measure_area(design, face_index, body_index=0):
    """Measure the area of a specific face.

    Args:
        design: Fusion 360 design object
        face_index: Index of the face
        body_index: Index of the body

    Returns:
        Dict with area_cm2, area_mm2, face_type
    """
    try:
        if design is None:
            return {"error": "No active design"}

        face = get_entity_from_body(design, "face", face_index, body_index)
        area = face.area

        geom = face.geometry
        face_type = geom.objectType.split("::")[-1] if geom else "Unknown"

        return {
            "area_cm2": round(area, 6),
            "area_mm2": round(area * 100, 6),
            "face_type": face_type,
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@task
def measure_volume(design, body_index=0):
    """Measure the volume of a body.

    Args:
        design: Fusion 360 design object
        body_index: Index of the body

    Returns:
        Dict with volume_cm3, volume_mm3, body_name
    """
    try:
        if design is None:
            return {"error": "No active design"}

        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if body_index >= bodies.count:
            return {"error": f"Body index {body_index} out of range (max {bodies.count - 1})"}

        body = bodies.item(body_index)
        volume = body.volume

        return {
            "volume_cm3": round(volume, 6),
            "volume_mm3": round(volume * 1000, 6),
            "body_name": body.name,
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@task
def measure_edge_length(design, edge_index, body_index=0):
    """Measure the length of a specific edge.

    Args:
        design: Fusion 360 design object
        edge_index: Index of the edge
        body_index: Index of the body

    Returns:
        Dict with length_cm, length_mm, edge_type, start_point, end_point
    """
    try:
        if design is None:
            return {"error": "No active design"}

        edge = get_entity_from_body(design, "edge", edge_index, body_index)
        length = edge.length

        geom = edge.geometry
        edge_type = geom.objectType.split("::")[-1] if geom else "Unknown"

        start_point = edge.startVertex.geometry if edge.startVertex else None
        end_point = edge.endVertex.geometry if edge.endVertex else None

        result = {
            "length_cm": round(length, 6),
            "length_mm": round(length * 10, 6),
            "edge_type": edge_type,
        }

        if start_point:
            result["start_point"] = [
                round(start_point.x, 4),
                round(start_point.y, 4),
                round(start_point.z, 4),
            ]
        if end_point:
            result["end_point"] = [
                round(end_point.x, 4),
                round(end_point.y, 4),
                round(end_point.z, 4),
            ]

        return result
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@task
def measure_body_properties(design, body_index=0):
    """Get comprehensive physical properties of a body.

    Args:
        design: Fusion 360 design object
        body_index: Index of the body

    Returns:
        Dict with volume, surface_area, bounding_box, centroid, face/edge/vertex counts
    """
    try:
        if design is None:
            return {"error": "No active design"}

        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if body_index >= bodies.count:
            return {"error": f"Body index {body_index} out of range (max {bodies.count - 1})"}

        body = bodies.item(body_index)

        physProps = body.physicalProperties
        volume = body.volume

        # Calculate surface area
        surface_area = 0
        for i in range(body.faces.count):
            surface_area += body.faces.item(i).area

        # Get bounding box
        bb = body.boundingBox
        bb_min = [round(bb.minPoint.x, 4), round(bb.minPoint.y, 4), round(bb.minPoint.z, 4)]
        bb_max = [round(bb.maxPoint.x, 4), round(bb.maxPoint.y, 4), round(bb.maxPoint.z, 4)]
        bb_size = [
            round(bb_max[0] - bb_min[0], 4),
            round(bb_max[1] - bb_min[1], 4),
            round(bb_max[2] - bb_min[2], 4),
        ]

        centroid = physProps.centerOfMass

        return {
            "volume_cm3": round(volume, 6),
            "volume_mm3": round(volume * 1000, 6),
            "surface_area_cm2": round(surface_area, 6),
            "surface_area_mm2": round(surface_area * 100, 6),
            "bounding_box": {"min": bb_min, "max": bb_max, "size": bb_size},
            "centroid": [round(centroid.x, 4), round(centroid.y, 4), round(centroid.z, 4)],
            "face_count": body.faces.count,
            "edge_count": body.edges.count,
            "vertex_count": body.vertices.count,
            "body_name": body.name,
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@task
def measure_point_to_point(design, point1, point2):
    """Measure the distance between two specific 3D points.

    Args:
        design: Fusion 360 design object (not used, for consistency)
        point1: [x, y, z] coordinates of first point (in cm)
        point2: [x, y, z] coordinates of second point (in cm)

    Returns:
        Dict with distance_cm, distance_mm, delta
    """
    try:
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        dz = point2[2] - point1[2]
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        return {
            "distance_cm": round(distance, 6),
            "distance_mm": round(distance * 10, 6),
            "delta": [round(dx, 6), round(dy, 6), round(dz, 6)],
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@task
def get_edges_info(design, body_index=0):
    """Returns detailed edge information for a body.

    Args:
        design: Fusion 360 design object
        body_index: Index of the body

    Returns:
        Dict with edge_count and edges list
    """
    try:
        if design is None:
            return {"error": "No active design"}

        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if body_index >= bodies.count:
            return {"error": f"Body index {body_index} out of range (max {bodies.count - 1})"}

        body = bodies.item(body_index)
        edges = body.edges

        edge_list = []
        for i in range(edges.count):
            edge = edges.item(i)
            geom = edge.geometry
            edge_type = geom.objectType.split("::")[-1] if geom else "Unknown"

            edge_info = {"index": i, "type": edge_type, "length_cm": round(edge.length, 4)}

            if edge.startVertex:
                sp = edge.startVertex.geometry
                edge_info["start_point"] = [round(sp.x, 4), round(sp.y, 4), round(sp.z, 4)]
            if edge.endVertex:
                ep = edge.endVertex.geometry
                edge_info["end_point"] = [round(ep.x, 4), round(ep.y, 4), round(ep.z, 4)]

            edge_list.append(edge_info)

        return {"body_name": body.name, "edge_count": edges.count, "edges": edge_list}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@task
def get_vertices_info(design, body_index=0):
    """Returns detailed vertex information for a body.

    Args:
        design: Fusion 360 design object
        body_index: Index of the body

    Returns:
        Dict with vertex_count and vertices list
    """
    try:
        if design is None:
            return {"error": "No active design"}

        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if body_index >= bodies.count:
            return {"error": f"Body index {body_index} out of range (max {bodies.count - 1})"}

        body = bodies.item(body_index)
        vertices = body.vertices

        vertex_list = []
        for i in range(vertices.count):
            vertex = vertices.item(i)
            geom = vertex.geometry
            vertex_list.append(
                {"index": i, "position": [round(geom.x, 4), round(geom.y, 4), round(geom.z, 4)]}
            )

        return {"body_name": body.name, "vertex_count": vertices.count, "vertices": vertex_list}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
