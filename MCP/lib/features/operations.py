"""3D Operations for Fusion 360.

This module contains functions for complex 3D operations like loft, sweep,
revolve, boolean operations, shell, fillet, holes, and threading.
"""

import adsk.core
import adsk.fusion
import traceback
import math


def loft(design, ui, sketchcount):
    """
    Creates a loft between the last 'sketchcount' sketches.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        sketchcount: Number of sketches to include in the loft
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        loftFeatures = rootComp.features.loftFeatures
        
        loftInput = loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        loftSectionsObj = loftInput.loftSections
        
        # Add profiles from the last 'sketchcount' sketches
        for i in range(sketchcount):
            sketch = sketches.item(sketches.count - 1 - i)
            profile = sketch.profiles.item(0)
            loftSectionsObj.add(profile)
        
        loftInput.isSolid = True
        loftInput.isClosed = False
        loftInput.isTangentEdgesMerged = True
        
        # Create loft feature
        loftFeatures.add(loftInput)
        
    except:
        if ui:
            ui.messageBox('Failed loft:\n{}'.format(traceback.format_exc()))


def sweep(design, ui):
    """
    Creates a sweep using the second-to-last sketch as profile and last sketch as path.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sweeps = rootComp.features.sweepFeatures

        profsketch = sketches.item(sketches.count - 2)  # Second to last sketch
        prof = profsketch.profiles.item(0)  # Profile (e.g., circle)
        pathsketch = sketches.item(sketches.count - 1)  # Last sketch as path
        
        # Collect all sketch curves in an ObjectCollection
        pathCurves = adsk.core.ObjectCollection.create()
        for i in range(pathsketch.sketchCurves.count):
            pathCurves.add(pathsketch.sketchCurves.item(i))

        path = adsk.fusion.Path.create(pathCurves, 0)
        sweepInput = sweeps.createInput(prof, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        sweeps.add(sweepInput)
    except:
        if ui:
            ui.messageBox('Failed sweep:\n{}'.format(traceback.format_exc()))


def revolve_profile(design, ui, angle=360):
    """
    Revolves a user-selected profile around a user-selected axis.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        angle: Revolution angle in degrees (default 360)
    """
    try:
        rootComp = design.rootComponent
        ui.messageBox('Select a profile to revolve.')
        profile = ui.selectEntity('Select a profile to revolve.', 'Profiles').entity
        ui.messageBox('Select sketch line for axis.')
        axis = ui.selectEntity('Select sketch line for axis.', 'SketchLines').entity
        operation = adsk.fusion.FeatureOperations.NewComponentFeatureOperation
        revolveFeatures = rootComp.features.revolveFeatures
        input = revolveFeatures.createInput(profile, axis, operation)
        input.setAngleExtent(False, adsk.core.ValueInput.createByString(str(angle) + ' deg'))
        revolveFeatures.add(input)
    except:
        if ui:
            ui.messageBox('Failed revolve_profile:\n{}'.format(traceback.format_exc()))


def boolean_operation(design, ui, op):
    """
    Performs boolean operations (cut, intersect, join) between bodies.
    The target body is the first created body, tool body is the second.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        op: Operation type ("cut", "intersect", or "join")
    """
    try:
        app = adsk.core.Application.get()
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        ui = app.userInterface

        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
       
        targetBody = bodies.item(0)  # Target body (first drawn)
        toolBody = bodies.item(1)    # Tool body (second drawn)

        combineFeatures = rootComp.features.combineFeatures
        tools = adsk.core.ObjectCollection.create()
        tools.add(toolBody)
        input = combineFeatures.createInput(targetBody, tools)
        input.isNewComponent = False
        input.isKeepToolBodies = False
        
        if op == "cut":
            input.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        elif op == "intersect":
            input.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        elif op == "join":
            input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            
        combineFeatures.add(input)
    except:
        if ui:
            ui.messageBox('Failed boolean_operation:\n{}'.format(traceback.format_exc()))


def shell_existing_body(design, ui, thickness=0.5, faceindex=0):
    """
    Shells a body on a specified face with given thickness.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        thickness: Shell wall thickness (default 0.5)
        faceindex: Index of the face to remove (default 0)
    """
    try:
        rootComp = design.rootComponent
        features = rootComp.features
        body = rootComp.bRepBodies.item(0)

        entities = adsk.core.ObjectCollection.create()
        entities.add(body.faces.item(faceindex))

        shellFeats = features.shellFeatures
        isTangentChain = False
        shellInput = shellFeats.createInput(entities, isTangentChain)

        thicknessVal = adsk.core.ValueInput.createByReal(thickness)
        shellInput.insideThickness = thicknessVal
        shellInput.shellType = adsk.fusion.ShellTypes.SharpOffsetShellType

        shellFeats.add(shellInput)
    except:
        if ui:
            ui.messageBox('Failed shell_existing_body:\n{}'.format(traceback.format_exc()))


def fillet_edges(design, ui, radius=0.3):
    """
    Creates fillets on all edges of all bodies in the design.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        radius: Fillet radius (default 0.3)
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        edgeCollection = adsk.core.ObjectCollection.create()
        for body_idx in range(bodies.count):
            body = bodies.item(body_idx)
            for edge_idx in range(body.edges.count):
                edge = body.edges.item(edge_idx)
                edgeCollection.add(edge)

        fillets = rootComp.features.filletFeatures
        radiusInput = adsk.core.ValueInput.createByReal(radius)
        filletInput = fillets.createInput()
        filletInput.isRollingBallCorner = True
        edgeSetInput = filletInput.edgeSetInputs.addConstantRadiusEdgeSet(
            edgeCollection, radiusInput, True
        )
        edgeSetInput.continuity = adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType
        fillets.add(filletInput)
    except:
        if ui:
            ui.messageBox('Failed fillet_edges:\n{}'.format(traceback.format_exc()))


def holes(design, ui, points, width=1.0, distance=1.0, faceindex=0):
    """
    Creates holes at specified points on a face.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        points: List of [x, y] coordinates for hole centers
        width: Hole diameter (default 1.0)
        distance: Hole depth (default 1.0)
        faceindex: Face index on the body (default 0)
    """
    try:
        rootComp = design.rootComponent
        holeFeatures = rootComp.features.holeFeatures
        sketches = rootComp.sketches
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("No bodies found.")
            return
            
        sk = sketches.add(latest_body.faces.item(faceindex))

        for i in range(len(points)):
            holePoint = sk.sketchPoints.add(
                adsk.core.Point3D.create(points[i][0], points[i][1], 0)
            )
            tipangle = adsk.core.ValueInput.createByString('180 deg')
            holedistance = adsk.core.ValueInput.createByReal(distance)
            holeDiam = adsk.core.ValueInput.createByReal(width)
            
            holeInput = holeFeatures.createSimpleInput(holeDiam)
            holeInput.tipAngle = tipangle
            holeInput.setPositionBySketchPoint(holePoint)
            holeInput.setDistanceExtent(holedistance)
            holeFeatures.add(holeInput)
    except:
        if ui:
            ui.messageBox('Failed holes:\n{}'.format(traceback.format_exc()))


def create_thread(design, ui, inside, sizes):
    """
    Creates a thread on a user-selected face.
    
    Args:
        design: Fusion 360 design object
        ui: Fusion 360 UI object
        inside: Boolean - True for internal thread, False for external
        sizes: Index of thread size in the available sizes list
    """
    try:
        rootComp = design.rootComponent
        threadFeatures = rootComp.features.threadFeatures
        
        ui.messageBox('Select a face for threading.')
        face = ui.selectEntity("Select a face for threading", "Faces").entity
        faces = adsk.core.ObjectCollection.create()
        faces.add(face)
        
        # Get thread info
        threadDataQuery = threadFeatures.threadDataQuery
        threadTypes = threadDataQuery.allThreadTypes
        threadType = threadTypes[0]

        allsizes = threadDataQuery.allSizes(threadType)
        threadSize = allsizes[sizes]

        allDesignations = threadDataQuery.allDesignations(threadType, threadSize)
        threadDesignation = allDesignations[0]
        
        allClasses = threadDataQuery.allClasses(False, threadType, threadDesignation)
        threadClass = allClasses[0]
        
        # Create thread info
        threadInfo = threadFeatures.createThreadInfo(inside, threadType, threadDesignation, threadClass)

        threadInput = threadFeatures.createInput(faces, threadInfo)
        threadInput.isFullLength = True
        
        # Create the thread
        threadFeatures.add(threadInput)
    except:
        if ui:
            ui.messageBox('Failed create_thread:\n{}'.format(traceback.format_exc()))
