"""Pre-defined prompts for common Fusion 360 operations."""

PROMPTS = {
    "wineglass": """
STEP 1: Draw Lines
- Use Tool: draw_lines
- Plane: XY
- Points: [[0, 0], [0, -8], [1.5, -8], [1.5, -7], [0.3, -7], [0.3, -2], [3, -0.5], [3, 0], [0, 0]]

STEP 2: Revolve the Profile
- Use Tool: revolve
- Angle: 360
- The user selects the profile and axis in Fusion
""",

    "magnet": """
STEP 1: Large Cylinder on Top
- Use Tool: draw_cylinder
- Radius: 1.59
- Height: 0.3
- Position: x=0, y=0, z=0.18
- Plane: XY

STEP 2: Small Cylinder on Bottom
- Use Tool: draw_cylinder
- Radius: 1.415
- Height: 0.18
- Position: x=0, y=0, z=0
- Plane: XY

STEP 3: Drill Hole in the Center
- Use Tool: draw_holes
- Points: [[0, 0]]
- Diameter (width): 1.0
- Depth: 0.21
- faceindex: 2
""",

    "dna": """
Use only the tools: draw2Dcircle, spline, sweep
Create a DNA Double Helix in Fusion 360

DNA STRAND 1:

STEP 1: 
- Use Tool: draw2Dcircle
- Radius: 0.5
- Position: x=3, y=0, z=0
- Plane: XY

STEP 2: 
- Use Tool: spline
- Plane: XY
- Points: [[3,0,0], [2.121,2.121,6.25], [0,3,12.5], [-2.121,2.121,18.75], [-3,0,25], [-2.121,-2.121,31.25], [0,-3,37.5], [2.121,-2.121,43.75], [3,0,50]]

STEP 3: Sweep Circle Along Path
- Use Tool: sweep


DNA STRAND 2:

STEP 4: 
- Use Tool: draw2Dcircle
- Radius: 0.5
- Position: x=-3, y=0, z=0
- Plane: XY

STEP 5: 
- Use Tool: spline
- Plane: XY
- Points: [[-3,0,0], [-2.121,-2.121,6.25], [0,-3,12.5], [2.121,-2.121,18.75], [3,0,25], [2.121,2.121,31.25], [0,3,37.5], [-2.121,2.121,43.75], [-3,0,50]]

STEP 6: Sweep Second Circle Along Second Path
- Use Tool: sweep

DONE: Now you have a DNA Double Helix!
""",

    "flange": """
STEP 1: 
- Use Tool: draw_cylinder
- Choose sensible dimensions (e.g., Radius: 5, Height: 1)
- Position: x=0, y=0, z=0
- Plane: XY

STEP 2: Drill Holes
- Use Tool: draw_holes
- Make 6-8 holes distributed in a circle
- Depth: More than the cylinder height (so they go through)
- faceindex: 1
- Example points for 6 holes: [[4,0], [2,3.46], [-2,3.46], [-4,0], [-2,-3.46], [2,-3.46]]

STEP 3: Ask the User
- "Should there also be a hole in the center?"

IF YES:
STEP 4: 
- Use Tool: draw2Dcircle
- Radius: 2 (or what the user wants)
- Position: x=0, y=0, z=0
- Plane: XY

STEP 5: 
- Use Tool: cut_extrude
- Depth: +2 (positive value! Greater than cylinder height)
""",

    "vase": """
STEP 1: 
- Use Tool: draw2Dcircle
- Radius: 2.5
- Position: x=0, y=0, z=0
- Plane: XY

STEP 2: 
- Use Tool: draw2Dcircle
- Radius: 1.5
- Position: x=0, y=0, z=4
- Plane: XY

STEP 3:
- Use Tool: draw2Dcircle
- Radius: 3
- Position: x=0, y=0, z=8
- Plane: XY

STEP 4: 
- Use Tool: draw2Dcircle
- Radius: 2
- Position: x=0, y=0, z=12
- Plane: XY

STEP 5: 
- Use Tool: loft
- sketchcount: 4

STEP 6: Hollow Out Vase (leave only walls)
- Use Tool: shell_body
- Wall thickness: 0.3
- faceindex: 1

DONE: Now you have a beautiful designer vase!
""",

    "part": """
STEP 1: 
- Use Tool: draw_box
- Width (width_value): "10"
- Height (height_value): "10"
- Depth (depth_value): "0.5"
- Position: x=0, y=0, z=0
- Plane: XY

STEP 2: Drill Small Holes
- Use Tool: draw_holes
- 8 holes total: 4 in corners + 4 closer to center
- Example points: [[4,4], [4,-4], [-4,4], [-4,-4], [2,2], [2,-2], [-2,2], [-2,-2]]
- Diameter (width): 0.5
- Depth: 0.2
- faceindex: 4

STEP 3: Draw Circle in Center
- Use Tool: draw2Dcircle
- Radius: 1
- Position: x=0, y=0, z=0
- Plane: XY

STEP 4: 
- Use Tool: cut_extrude
- Depth: +10 (MUST be positive!)

STEP 5: Tell the User
- "Please now select the inner face of the center hole in Fusion 360"

STEP 6: Create Thread
- Use Tool: create_thread
- inside: True (internal thread)
- allsizes: 10 (for 1/4 inch thread)

DONE: Part with holes and thread is complete!
""",

    "compensator": """
Build a compensator in Fusion 360 with MCP: First delete everything.
Then create a thin-walled pipe: Draw a 2D circle with radius 5 in the XY plane at z=0, 
extrude it thin with distance 10 and thickness 0.1. Then add 8 rings stacked on top of each other (First circle then extrusion 8 times): For each ring at
heights z=1 to z=8 draw a 2D circle with radius 5.1 in the XY plane and extrude it thin with distance 0.5 and thickness 0.5.
Do not use boolean operations, leave the rings as separate bodies. Then round the edges with radius 0.2.
Do it fast!!!!!!
""",
    
    # Keep old German keys as aliases for backwards compatibility
    "weinglas": """
STEP 1: Draw Lines
- Use Tool: draw_lines
- Plane: XY
- Points: [[0, 0], [0, -8], [1.5, -8], [1.5, -7], [0.3, -7], [0.3, -2], [3, -0.5], [3, 0], [0, 0]]

STEP 2: Revolve the Profile
- Use Tool: revolve
- Angle: 360
- The user selects the profile and axis in Fusion
""",

    "flansch": """
STEP 1: 
- Use Tool: draw_cylinder
- Choose sensible dimensions (e.g., Radius: 5, Height: 1)
- Position: x=0, y=0, z=0
- Plane: XY

STEP 2: Drill Holes
- Use Tool: draw_holes
- Make 6-8 holes distributed in a circle
- Depth: More than the cylinder height (so they go through)
- faceindex: 1
- Example points for 6 holes: [[4,0], [2,3.46], [-2,3.46], [-4,0], [-2,-3.46], [2,-3.46]]

STEP 3: Ask the User
- "Should there also be a hole in the center?"

IF YES:
STEP 4: 
- Use Tool: draw2Dcircle
- Radius: 2 (or what the user wants)
- Position: x=0, y=0, z=0
- Plane: XY

STEP 5: 
- Use Tool: cut_extrude
- Depth: +2 (positive value! Greater than cylinder height)
""",

    "teil": """
STEP 1: 
- Use Tool: draw_box
- Width (width_value): "10"
- Height (height_value): "10"
- Depth (depth_value): "0.5"
- Position: x=0, y=0, z=0
- Plane: XY

STEP 2: Drill Small Holes
- Use Tool: draw_holes
- 8 holes total: 4 in corners + 4 closer to center
- Example points: [[4,4], [4,-4], [-4,4], [-4,-4], [2,2], [2,-2], [-2,2], [-2,-2]]
- Diameter (width): 0.5
- Depth: 0.2
- faceindex: 4

STEP 3: Draw Circle in Center
- Use Tool: draw2Dcircle
- Radius: 1
- Position: x=0, y=0, z=0
- Plane: XY

STEP 4: 
- Use Tool: cut_extrude
- Depth: +10 (MUST be positive!)

STEP 5: Tell the User
- "Please now select the inner face of the center hole in Fusion 360"

STEP 6: Create Thread
- Use Tool: create_thread
- inside: True (internal thread)
- allsizes: 10 (for 1/4 inch thread)

DONE: Part with holes and thread is complete!
""",
}


def get_prompt(name: str) -> str:
    """Get a prompt by name."""
    return PROMPTS.get(name, f"Unknown prompt: {name}")
