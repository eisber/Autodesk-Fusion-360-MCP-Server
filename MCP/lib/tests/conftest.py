"""Shared pytest fixtures for Fusion 360 MCP Add-In tests.

These fixtures mock the Fusion 360 API objects since we cannot run
actual Fusion 360 in a test environment.
"""

import sys
from unittest.mock import MagicMock, PropertyMock

import pytest


# Create mock adsk module before importing our modules
def create_mock_adsk():
    """Create a comprehensive mock of the adsk module."""
    mock_adsk = MagicMock()

    # Mock adsk.core
    mock_core = MagicMock()
    mock_adsk.core = mock_core

    # Mock Point3D
    def create_point3d(x, y, z):
        point = MagicMock()
        point.x = x
        point.y = y
        point.z = z
        return point

    mock_core.Point3D = MagicMock()
    mock_core.Point3D.create = create_point3d

    # Mock Vector3D
    def create_vector3d(x, y, z):
        vector = MagicMock()
        vector.x = x
        vector.y = y
        vector.z = z
        return vector

    mock_core.Vector3D = MagicMock()
    mock_core.Vector3D.create = create_vector3d

    # Mock Matrix3D
    mock_core.Matrix3D = MagicMock()
    mock_core.Matrix3D.create = MagicMock(return_value=MagicMock())

    # Mock ValueInput
    mock_core.ValueInput = MagicMock()
    mock_core.ValueInput.createByReal = MagicMock(side_effect=lambda v: MagicMock(value=v))
    mock_core.ValueInput.createByString = MagicMock(side_effect=lambda s: MagicMock(expression=s))

    # Mock ObjectCollection
    def create_object_collection():
        collection = MagicMock()
        collection._items = []
        collection.add = lambda item: collection._items.append(item)
        collection.count = property(lambda self: len(self._items))
        return collection

    mock_core.ObjectCollection = MagicMock()
    mock_core.ObjectCollection.create = create_object_collection

    # Mock Alignments
    mock_core.HorizontalAlignments = MagicMock()
    mock_core.HorizontalAlignments.LeftHorizontalAlignment = "left"
    mock_core.VerticalAlignments = MagicMock()
    mock_core.VerticalAlignments.TopVerticalAlignment = "top"

    # Mock Application
    mock_core.Application = MagicMock()
    mock_core.Application.get = MagicMock()

    # Mock adsk.fusion
    mock_fusion = MagicMock()
    mock_adsk.fusion = mock_fusion

    # Mock FeatureOperations
    mock_fusion.FeatureOperations = MagicMock()
    mock_fusion.FeatureOperations.NewBodyFeatureOperation = "NewBodyFeatureOperation"
    mock_fusion.FeatureOperations.NewComponentFeatureOperation = "NewComponentFeatureOperation"
    mock_fusion.FeatureOperations.CutFeatureOperation = "CutFeatureOperation"
    mock_fusion.FeatureOperations.JoinFeatureOperation = "JoinFeatureOperation"
    mock_fusion.FeatureOperations.IntersectFeatureOperation = "IntersectFeatureOperation"

    # Mock ExtentDirections
    mock_fusion.ExtentDirections = MagicMock()
    mock_fusion.ExtentDirections.PositiveExtentDirection = "PositiveExtentDirection"

    # Mock ThinExtrudeWallLocation
    mock_fusion.ThinExtrudeWallLocation = MagicMock()
    mock_fusion.ThinExtrudeWallLocation.Center = "Center"

    # Mock DistanceExtentDefinition
    mock_fusion.DistanceExtentDefinition = MagicMock()
    mock_fusion.DistanceExtentDefinition.create = MagicMock(return_value=MagicMock())

    # Mock PatternDistanceType
    mock_fusion.PatternDistanceType = MagicMock()
    mock_fusion.PatternDistanceType.SpacingPatternDistanceType = "SpacingPatternDistanceType"

    # Mock ShellTypes
    mock_fusion.ShellTypes = MagicMock()
    mock_fusion.ShellTypes.SharpOffsetShellType = "SharpOffsetShellType"

    # Mock SurfaceContinuityTypes
    mock_fusion.SurfaceContinuityTypes = MagicMock()
    mock_fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType = "TangentSurfaceContinuityType"

    # Mock Design
    mock_fusion.Design = MagicMock()
    mock_fusion.Design.cast = MagicMock()

    # Mock Path
    mock_fusion.Path = MagicMock()
    mock_fusion.Path.create = MagicMock(return_value=MagicMock())

    return mock_adsk


@pytest.fixture(autouse=True)
def mock_adsk_module():
    """Automatically mock adsk module for all tests."""
    mock_adsk = create_mock_adsk()
    sys.modules["adsk"] = mock_adsk
    sys.modules["adsk.core"] = mock_adsk.core
    sys.modules["adsk.fusion"] = mock_adsk.fusion
    yield mock_adsk
    # Cleanup
    if "adsk" in sys.modules:
        del sys.modules["adsk"]
    if "adsk.core" in sys.modules:
        del sys.modules["adsk.core"]
    if "adsk.fusion" in sys.modules:
        del sys.modules["adsk.fusion"]


@pytest.fixture
def mock_design():
    """Create a mock Fusion 360 design object."""
    design = MagicMock()
    root_comp = MagicMock()
    design.rootComponent = root_comp

    # Mock sketches collection
    sketches = MagicMock()
    sketch_items = []
    sketches.add = MagicMock(return_value=MagicMock())
    sketches.count = 0
    sketches.item = MagicMock(
        side_effect=lambda i: sketch_items[i] if i < len(sketch_items) else MagicMock()
    )
    sketches.itemByName = MagicMock(return_value=MagicMock())
    root_comp.sketches = sketches

    # Mock construction planes
    root_comp.xYConstructionPlane = MagicMock(name="XYPlane")
    root_comp.xZConstructionPlane = MagicMock(name="XZPlane")
    root_comp.yZConstructionPlane = MagicMock(name="YZPlane")

    # Mock construction axes
    root_comp.xConstructionAxis = MagicMock(name="XAxis")
    root_comp.yConstructionAxis = MagicMock(name="YAxis")
    root_comp.zConstructionAxis = MagicMock(name="ZAxis")

    # Mock construction planes collection
    planes = MagicMock()
    planes.createInput = MagicMock(return_value=MagicMock())
    planes.add = MagicMock(return_value=MagicMock())
    root_comp.constructionPlanes = planes

    # Mock bodies collection
    bodies = MagicMock()
    body_items = []
    bodies.count = 0
    bodies.item = MagicMock(
        side_effect=lambda i: body_items[i] if i < len(body_items) else MagicMock()
    )
    bodies.itemByName = MagicMock(return_value=MagicMock())
    root_comp.bRepBodies = bodies

    # Mock features
    features = MagicMock()
    root_comp.features = features

    # Mock extrude features
    extrude_features = MagicMock()
    extrude_features.createInput = MagicMock(return_value=MagicMock())
    extrude_features.add = MagicMock(return_value=MagicMock())
    features.extrudeFeatures = extrude_features

    # Mock revolve features
    revolve_features = MagicMock()
    revolve_features.createInput = MagicMock(return_value=MagicMock())
    revolve_features.add = MagicMock(return_value=MagicMock())
    features.revolveFeatures = revolve_features

    # Mock sweep features
    sweep_features = MagicMock()
    sweep_features.createInput = MagicMock(return_value=MagicMock())
    sweep_features.add = MagicMock(return_value=MagicMock())
    features.sweepFeatures = sweep_features

    # Mock loft features
    loft_features = MagicMock()
    loft_input = MagicMock()
    loft_input.loftSections = MagicMock()
    loft_input.loftSections.add = MagicMock()
    loft_features.createInput = MagicMock(return_value=loft_input)
    loft_features.add = MagicMock(return_value=MagicMock())
    features.loftFeatures = loft_features

    # Mock fillet features
    fillet_features = MagicMock()
    fillet_input = MagicMock()
    fillet_input.edgeSetInputs = MagicMock()
    fillet_input.edgeSetInputs.addConstantRadiusEdgeSet = MagicMock(return_value=MagicMock())
    fillet_features.createInput = MagicMock(return_value=fillet_input)
    fillet_features.add = MagicMock(return_value=MagicMock())
    features.filletFeatures = fillet_features

    # Mock shell features
    shell_features = MagicMock()
    shell_features.createInput = MagicMock(return_value=MagicMock())
    shell_features.add = MagicMock(return_value=MagicMock())
    features.shellFeatures = shell_features

    # Mock hole features
    hole_features = MagicMock()
    hole_features.createSimpleInput = MagicMock(return_value=MagicMock())
    hole_features.add = MagicMock(return_value=MagicMock())
    features.holeFeatures = hole_features

    # Mock thread features
    thread_features = MagicMock()
    thread_data_query = MagicMock()
    thread_data_query.allThreadTypes = ["ISO Metric"]
    thread_data_query.allSizes = MagicMock(return_value=["M3", "M4", "M5"])
    thread_data_query.allDesignations = MagicMock(return_value=["M3x0.5"])
    thread_data_query.allClasses = MagicMock(return_value=["6H"])
    thread_features.threadDataQuery = thread_data_query
    thread_features.createThreadInfo = MagicMock(return_value=MagicMock())
    thread_features.createInput = MagicMock(return_value=MagicMock())
    thread_features.add = MagicMock(return_value=MagicMock())
    features.threadFeatures = thread_features

    # Mock combine features
    combine_features = MagicMock()
    combine_features.createInput = MagicMock(return_value=MagicMock())
    combine_features.add = MagicMock(return_value=MagicMock())
    features.combineFeatures = combine_features

    # Mock move features
    move_features = MagicMock()
    move_features.createInput2 = MagicMock(return_value=MagicMock())
    move_features.add = MagicMock(return_value=MagicMock())
    features.moveFeatures = move_features

    # Mock circular pattern features
    circular_pattern_features = MagicMock()
    circular_pattern_features.createInput = MagicMock(return_value=MagicMock())
    circular_pattern_features.add = MagicMock(return_value=MagicMock())
    features.circularPatternFeatures = circular_pattern_features

    # Mock rectangular pattern features
    rect_pattern_features = MagicMock()
    rect_input = MagicMock()
    rect_input.setDirectionTwo = MagicMock()
    rect_pattern_features.createInput = MagicMock(return_value=rect_input)
    rect_pattern_features.add = MagicMock(return_value=MagicMock())
    features.rectangularPatternFeatures = rect_pattern_features

    # Mock remove features
    remove_features = MagicMock()
    remove_features.add = MagicMock()
    features.removeFeatures = remove_features

    # Mock export manager
    export_mgr = MagicMock()
    export_mgr.createSTEPExportOptions = MagicMock(return_value=MagicMock())
    export_mgr.createSTLExportOptions = MagicMock(return_value=MagicMock())
    export_mgr.execute = MagicMock(return_value=True)
    design.exportManager = export_mgr

    # Mock user parameters
    user_params = MagicMock()
    user_params.count = 0
    user_params.item = MagicMock(return_value=None)
    design.userParameters = user_params

    # Mock all parameters as a MagicMock with itemByName
    all_params = MagicMock()
    all_params.__iter__ = MagicMock(return_value=iter([]))
    design.allParameters = all_params

    return design


@pytest.fixture
def mock_ui():
    """Create a mock Fusion 360 UI object."""
    ui = MagicMock()
    ui.messageBox = MagicMock()
    ui.selectEntity = MagicMock(return_value=MagicMock(entity=MagicMock()))

    # Mock command definitions for undo
    cmd_defs = MagicMock()
    cmd_defs.itemById = MagicMock(return_value=MagicMock())
    ui.commandDefinitions = cmd_defs

    return ui


@pytest.fixture
def mock_sketch(mock_design):
    """Create a mock sketch object."""
    sketch = MagicMock()

    # Mock sketch curves
    sketch_curves = MagicMock()
    sketch.sketchCurves = sketch_curves

    # Mock sketch lines
    sketch_lines = MagicMock()
    sketch_lines.addByTwoPoints = MagicMock(return_value=MagicMock())
    sketch_lines.addCenterPointRectangle = MagicMock(return_value=MagicMock())
    sketch_lines.addTwoPointRectangle = MagicMock(return_value=MagicMock())
    sketch_curves.sketchLines = sketch_lines

    # Mock sketch circles
    sketch_circles = MagicMock()
    sketch_circles.addByCenterRadius = MagicMock(return_value=MagicMock())
    sketch_curves.sketchCircles = sketch_circles

    # Mock sketch arcs
    sketch_arcs = MagicMock()
    sketch_arcs.addByThreePoints = MagicMock(return_value=MagicMock())
    sketch_curves.sketchArcs = sketch_arcs

    # Mock sketch ellipses
    sketch_ellipses = MagicMock()
    sketch_ellipses.add = MagicMock(return_value=MagicMock())
    sketch_curves.sketchEllipses = sketch_ellipses

    # Mock sketch splines
    sketch_splines = MagicMock()
    sketch_splines.add = MagicMock(return_value=MagicMock())
    sketch_curves.sketchFittedSplines = sketch_splines

    # Mock sketch count for iteration
    sketch_curves.count = 1
    sketch_curves.item = MagicMock(return_value=MagicMock())

    # Mock profiles
    profiles = MagicMock()
    profiles.item = MagicMock(return_value=MagicMock())
    profiles.count = 1
    sketch.profiles = profiles

    # Mock sketch texts
    sketch_texts = MagicMock()
    text_input = MagicMock()
    text_input.setAsMultiLine = MagicMock()
    sketch_texts.createInput2 = MagicMock(return_value=text_input)
    sketch_texts.add = MagicMock(return_value=MagicMock())
    sketch.sketchTexts = sketch_texts

    # Mock sketch points
    sketch_points = MagicMock()
    sketch_points.add = MagicMock(return_value=MagicMock())
    sketch.sketchPoints = sketch_points

    # Configure the design to return this sketch
    mock_design.rootComponent.sketches.add.return_value = sketch
    mock_design.rootComponent.sketches.item.return_value = sketch
    mock_design.rootComponent.sketches.count = 1

    return sketch


@pytest.fixture
def mock_body(mock_design):
    """Create a mock body object."""
    body = MagicMock()
    # Use PropertyMock for name since 'name' is special in MagicMock
    type(body).name = PropertyMock(return_value="Body1")
    body.volume = 100.0

    # Mock bounding box
    bounding_box = MagicMock()
    min_point = MagicMock()
    min_point.x = 0
    min_point.y = 0
    min_point.z = 0
    max_point = MagicMock()
    max_point.x = 5
    max_point.y = 5
    max_point.z = 5
    bounding_box.minPoint = min_point
    bounding_box.maxPoint = max_point
    body.boundingBox = bounding_box

    # Mock faces
    faces = MagicMock()
    face = MagicMock()
    face.centroid = MagicMock(x=2.5, y=2.5, z=2.5)
    face.area = 25.0
    face.geometry = MagicMock(objectType="adsk::fusion::Plane")
    faces.count = 6
    faces.item = MagicMock(return_value=face)
    body.faces = faces

    # Mock edges
    edges = MagicMock()
    edge = MagicMock()
    edges.count = 12
    edges.item = MagicMock(return_value=edge)
    body.edges = edges

    # Configure the design to return this body
    mock_design.rootComponent.bRepBodies.item.return_value = body
    mock_design.rootComponent.bRepBodies.count = 1

    return body
