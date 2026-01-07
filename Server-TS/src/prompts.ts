/**
 * Pre-defined prompts for common Fusion 360 operations.
 * All geometry creation uses execute_fusion_script with Python code.
 */

export const PROMPTS: Record<string, string> = {
  wineglass: `
Create a wine glass using execute_fusion_script with a revolve operation:

\`\`\`python
import adsk.core, adsk.fusion

# Get design and root component
design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
rootComp = design.rootComponent

# Create sketch on XY plane
sketches = rootComp.sketches
xyPlane = rootComp.xYConstructionPlane
sketch = sketches.add(xyPlane)

# Draw the wine glass profile (closed loop for revolve)
lines = sketch.sketchCurves.sketchLines
points = [
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(0, -8, 0),
    adsk.core.Point3D.create(1.5, -8, 0),
    adsk.core.Point3D.create(1.5, -7, 0),
    adsk.core.Point3D.create(0.3, -7, 0),
    adsk.core.Point3D.create(0.3, -2, 0),
    adsk.core.Point3D.create(3, -0.5, 0),
    adsk.core.Point3D.create(3, 0, 0),
]

# Draw lines connecting points
for i in range(len(points) - 1):
    lines.addByTwoPoints(points[i], points[i + 1])
# Close the profile
lines.addByTwoPoints(points[-1], points[0])

# Get profile and create revolve
profile = sketch.profiles.item(0)
revolves = rootComp.features.revolveFeatures

# Create axis along Y-axis through origin
yAxis = rootComp.yConstructionAxis

# Create revolve input
revolveInput = revolves.createInput(profile, yAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
angle = adsk.core.ValueInput.createByReal(2 * 3.14159)  # Full 360 degrees
revolveInput.setAngleExtent(False, angle)

# Execute revolve
revolves.add(revolveInput)

result = "Wine glass created!"
\`\`\`
`,

  magnet: `
Create a stepped magnet shape using execute_fusion_script:

\`\`\`python
import adsk.core, adsk.fusion, math

design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
rootComp = design.rootComponent
sketches = rootComp.sketches
extrudes = rootComp.features.extrudeFeatures

# Create XY plane sketch for large cylinder
xyPlane = rootComp.xYConstructionPlane
sketch1 = sketches.add(xyPlane)

# Draw large circle (radius 1.59 cm)
circles = sketch1.sketchCurves.sketchCircles
circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 1.59)

# Extrude large cylinder
profile1 = sketch1.profiles.item(0)
ext1 = extrudes.addSimple(profile1, adsk.core.ValueInput.createByReal(0.3), 
                          adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

# Create offset plane for small cylinder base
planes = rootComp.constructionPlanes
planeInput = planes.createInput()
planeInput.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(-0.18))
offsetPlane = planes.add(planeInput)

# Draw small circle on offset plane (radius 1.415 cm)
sketch2 = sketches.add(offsetPlane)
circles2 = sketch2.sketchCurves.sketchCircles
circles2.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 1.415)

# Extrude small cylinder
profile2 = sketch2.profiles.item(0)
ext2 = extrudes.addSimple(profile2, adsk.core.ValueInput.createByReal(0.18), 
                          adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

# Create center hole
sketch3 = sketches.add(xyPlane)
circles3 = sketch3.sketchCurves.sketchCircles
circles3.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 0.5)

profile3 = sketch3.profiles.item(0)
ext3 = extrudes.addSimple(profile3, adsk.core.ValueInput.createByReal(-0.5), 
                          adsk.fusion.FeatureOperations.CutFeatureOperation)

result = "Stepped magnet created with center hole!"
\`\`\`
`,

  flange: `
Create a flange with bolt holes using execute_fusion_script:

\`\`\`python
import adsk.core, adsk.fusion, math

design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
rootComp = design.rootComponent
sketches = rootComp.sketches
extrudes = rootComp.features.extrudeFeatures

# Create base flange cylinder
xyPlane = rootComp.xYConstructionPlane
sketch1 = sketches.add(xyPlane)
circles = sketch1.sketchCurves.sketchCircles
circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 5)  # 5cm radius

profile1 = sketch1.profiles.item(0)
ext1 = extrudes.addSimple(profile1, adsk.core.ValueInput.createByReal(1), 
                          adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

# Create bolt holes in a pattern
sketch2 = sketches.add(ext1.endFaces.item(0))  # Sketch on top face
holes = sketch2.sketchCurves.sketchCircles

# 6 holes at radius 4 from center
hole_radius = 0.3
bolt_circle_radius = 4
for i in range(6):
    angle = i * (2 * math.pi / 6)
    x = bolt_circle_radius * math.cos(angle)
    y = bolt_circle_radius * math.sin(angle)
    holes.addByCenterRadius(adsk.core.Point3D.create(x, y, 0), hole_radius)

# Cut the holes through
for i in range(sketch2.profiles.count):
    profile = sketch2.profiles.item(i)
    extrudes.addSimple(profile, adsk.core.ValueInput.createByReal(-2), 
                       adsk.fusion.FeatureOperations.CutFeatureOperation)

# Center hole
sketch3 = sketches.add(xyPlane)
circles3 = sketch3.sketchCurves.sketchCircles
circles3.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 2)

profile3 = sketch3.profiles.item(0)
extrudes.addSimple(profile3, adsk.core.ValueInput.createByReal(2), 
                   adsk.fusion.FeatureOperations.CutFeatureOperation)

result = "Flange with 6 bolt holes and center hole created!"
\`\`\`
`,

  vase: `
Create a vase using execute_fusion_script with loft:

\`\`\`python
import adsk.core, adsk.fusion

design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
rootComp = design.rootComponent
sketches = rootComp.sketches
lofts = rootComp.features.loftFeatures

xyPlane = rootComp.xYConstructionPlane
planes = rootComp.constructionPlanes

# Create 4 sketches at different heights with different radii
heights = [0, 4, 8, 12]  # cm
radii = [2.5, 1.5, 3, 2]  # cm

profiles = []
for i, (h, r) in enumerate(zip(heights, radii)):
    if h == 0:
        plane = xyPlane
    else:
        planeInput = planes.createInput()
        planeInput.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(h))
        plane = planes.add(planeInput)
    
    sketch = sketches.add(plane)
    circles = sketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), r)
    profiles.append(sketch.profiles.item(0))

# Create loft
loftInput = lofts.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
for profile in profiles:
    loftInput.loftSections.add(profile)
loftInput.isSolid = True
loft = lofts.add(loftInput)

# Shell to hollow out (0.3cm wall thickness)
shells = rootComp.features.shellFeatures
shellInput = shells.createInput([loft.faces.item(0)])  # Top face
shellInput.insideThickness = adsk.core.ValueInput.createByReal(0.3)
shells.add(shellInput)

result = "Vase with varying profile and hollow interior created!"
\`\`\`
`,

  box: `
Create a simple box using execute_fusion_script:

\`\`\`python
import adsk.core, adsk.fusion

design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
rootComp = design.rootComponent

# Create sketch on XY plane
sketches = rootComp.sketches
xyPlane = rootComp.xYConstructionPlane
sketch = sketches.add(xyPlane)

# Draw rectangle (5cm x 3cm)
lines = sketch.sketchCurves.sketchLines
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(5, 3, 0)
)

# Extrude to create box (2cm height)
profile = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
ext = extrudes.addSimple(
    profile,
    adsk.core.ValueInput.createByReal(2),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
)

result = f"Box created: {ext.bodies.item(0).name}"
\`\`\`
`,

  cylinder: `
Create a cylinder using execute_fusion_script:

\`\`\`python
import adsk.core, adsk.fusion

design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
rootComp = design.rootComponent

# Create sketch on XY plane
sketches = rootComp.sketches
xyPlane = rootComp.xYConstructionPlane
sketch = sketches.add(xyPlane)

# Draw circle (radius 2cm)
circles = sketch.sketchCurves.sketchCircles
circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 2)

# Extrude to create cylinder (5cm height)
profile = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
ext = extrudes.addSimple(
    profile,
    adsk.core.ValueInput.createByReal(5),
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
)

result = f"Cylinder created: {ext.bodies.item(0).name}"
\`\`\`
`,
};
