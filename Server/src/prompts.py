"""Pre-defined prompts for common Fusion 360 operations."""

PROMPTS = {
    "weinglas": """
SCHRITT 1: Zeichne Linien
- Benutze Tool: draw_lines
- Ebene: XY
- Punkte: [[0, 0], [0, -8], [1.5, -8], [1.5, -7], [0.3, -7], [0.3, -2], [3, -0.5], [3, 0], [0, 0]]

SCHRITT 2: Drehe das Profil
- Benutze Tool: revolve
- Winkel: 360
- Der Nutzer wählt in Fusion das Profil und die Achse aus
""",

    "magnet": """
SCHRITT 1: Großer Zylinder oben
- Benutze Tool: draw_cylinder
- Radius: 1.59
- Höhe: 0.3
- Position: x=0, y=0, z=0.18
- Ebene: XY

SCHRITT 2: Kleiner Zylinder unten
- Benutze Tool: draw_cylinder
- Radius: 1.415
- Höhe: 0.18
- Position: x=0, y=0, z=0
- Ebene: XY

SCHRITT 3: Loch in die Mitte bohren
- Benutze Tool: draw_holes
- Punkte: [[0, 0]]
- Durchmesser (width): 1.0
- Tiefe (depth): 0.21
- faceindex: 2

SCHRITT 4: Logo drauf setzen
- Benutze Tool: draw_witzenmannlogo
- Skalierung (scale): 0.1
- Höhe (z): 0.28
""",

    "dna": """
Benutze nur die tools : draw2Dcircle , spline , sweep
Erstelle eine DNA Doppelhelix in Fusion 360

DNA STRANG 1:

SCHRITT 1: 
- Benutze Tool: draw2Dcircle
- Radius: 0.5
- Position: x=3, y=0, z=0
- Ebene: XY

SCHRITT 2: 
- Benutze Tool: spline
- Ebene: XY
- Punkte: [[3,0,0], [2.121,2.121,6.25], [0,3,12.5], [-2.121,2.121,18.75], [-3,0,25], [-2.121,-2.121,31.25], [0,-3,37.5], [2.121,-2.121,43.75], [3,0,50]]

SCHRITT 3: Kreis an der Linie entlang ziehen
- Benutze Tool: sweep


DNA STRANG 2:

SCHRITT 4: 
- Benutze Tool: draw2Dcircle
- Radius: 0.5
- Position: x=-3, y=0, z=0
- Ebene: XY

SCHRITT 5: 
- Benutze Tool: spline
- Ebene: XY
- Punkte: [[-3,0,0], [-2.121,-2.121,6.25], [0,-3,12.5], [2.121,-2.121,18.75], [3,0,25], [2.121,2.121,31.25], [0,3,37.5], [-2.121,2.121,43.75], [-3,0,50]]

SCHRITT 6: Zweiten Kreis an der zweiten Linie entlang ziehen
- Benutze Tool: sweep

FERTIG: Jetzt hast du eine DNA Doppelhelix!
""",

    "flansch": """
SCHRITT 1: 
- Benutze Tool: draw_cylinder
- Denk dir sinnvolle Maße aus (z.B. Radius: 5, Höhe: 1)
- Position: x=0, y=0, z=0
- Ebene: XY

SCHRITT 2: Löcher bohren
- Benutze Tool: draw_holes
- Mache 6-8 Löcher im Kreis verteilt
- Tiefe: Mehr als die Zylinderhöhe (damit sie durchgehen)
- faceindex: 1
- Beispiel Punkte für 6 Löcher: [[4,0], [2,3.46], [-2,3.46], [-4,0], [-2,-3.46], [2,-3.46]]

SCHRITT 3: Frage den Nutzer
- "Soll in der Mitte auch ein Loch sein?"

WENN JA:
SCHRITT 4: 
- Benutze Tool: draw2Dcircle
- Radius: 2 (oder was der Nutzer will)
- Position: x=0, y=0, z=0
- Ebene: XY

SCHRITT 5: 
- Benutze Tool: cut_extrude
- Tiefe: +2 (pos Wert! Größer als Zylinderhöhe)
""",

    "vase": """
SCHRITT 1: 
- Benutze Tool: draw2Dcircle
- Radius: 2.5
- Position: x=0, y=0, z=0
- Ebene: XY

SCHRITT 2: 
- Benutze Tool: draw2Dcircle
- Radius: 1.5
- Position: x=0, y=0, z=4
- Ebene: XY

SCHRITT 3:
- Benutze Tool: draw2Dcircle
- Radius: 3
- Position: x=0, y=0, z=8
- Ebene: XY

SCHRITT 4: 
- Benutze Tool: draw2Dcircle
- Radius: 2
- Position: x=0, y=0, z=12
- Ebene: XY

SCHRITT 5: 
- Benutze Tool: loft
- sketchcount: 4

SCHRITT 6: Vase aushöhlen (nur Wände übrig lassen)
- Benutze Tool: shell_body
- Wandstärke (thickness): 0.3
- faceindex: 1

FERTIG: Jetzt hast du eine schöne Designer-Vase!
""",

    "teil": """
SCHRITT 1: 
- Benutze Tool: draw_box
- Breite (width_value): "10"
- Höhe (height_value): "10"
- Tiefe (depth_value): "0.5"
- Position: x=0, y=0, z=0
- Ebene: XY

SCHRITT 2: Kleine Löcher bohren
- Benutze Tool: draw_holes
- 8 Löcher total: 4 in den Ecken + 4 näher zur Mitte
- Beispiel Punkte: [[4,4], [4,-4], [-4,4], [-4,-4], [2,2], [2,-2], [-2,2], [-2,-2]]
- Durchmesser (width): 0.5
- Tiefe (depth): 0.2
- faceindex: 4

SCHRITT 3: Kreis in der Mitte zeichnen
- Benutze Tool: draw2Dcircle
- Radius: 1
- Position: x=0, y=0, z=0
- Ebene: XY

SCHRITT 4: 
- Benutze Tool: cut_extrude
- Tiefe: +10 (MUSS Positiv SEIN!)

SCHRITT 5: Sage dem Nutzer
- "Bitte wähle jetzt in Fusion 360 die innere Fläche des mittleren Lochs aus"

SCHRITT 6: Gewinde erstellen
- Benutze Tool: create_thread
- inside: True (Innengewinde)
- allsizes: 10 (für 1/4 Zoll Gewinde)

FERTIG: Teil mit Löchern und Gewinde ist fertig!
""",

    "kompensator": """
Bau einen Kompensator in Fusion 360 mit dem MCP: Lösche zuerst alles.
Erstelle dann ein dünnwandiges Rohr: Zeichne einen 2D-Kreis mit Radius 5 in der XY-Ebene bei z=0, 
extrudiere ihn thin mit distance 10 und thickness 0.1. Füge dann 8 Ringe nacheinander übereinander hinzu (Erst Kreis dann Extrusion 8 mal): Für jeden Ring in
den Höhen z=1 bis z=8 zeichne einen 2D-Kreis mit Radius 5.1 in der XY-Ebene und extrudiere ihn thin mit distance 0.5 und thickness 0.5.
Verwende keine boolean operations, lass die Ringe als separate Körper. Runde anschließend die Kanten mit Radius 0.2 ab.
Mache schnell!!!!!!
""",
}


def get_prompt(name: str) -> str:
    """Get a prompt by name."""
    return PROMPTS.get(name, f"Unknown prompt: {name}")
