"""Build the cutlery tray modules in the running FreeCAD session.

Run inside FreeCAD (for example through the MCP execute_code tool):

    p = "<repo>/projects/cutlery-tray/scripts/build_tray.py"
    exec(compile(open(p).read(), p, "exec"), {"__file__": p, "__name__": "__main__"})

Dimensions live in the document's Params spreadsheet, which is created with the defaults below
if it doesn't exist yet. Edit Params and re-run this script to rebuild. The split into modules and
compartments is defined in LAYOUT.

Coordinates: origin at the drawer's inside front-left floor corner, X across the drawer width,
Y from the front (opening side) to the back, Z up.
"""

import os

import FreeCAD as App
import Part

V = App.Vector

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_NAME = "cutlery_tray"
DOC_PATH = os.path.join(PROJECT_DIR, "cutlery-tray.FCStd")
PRINT_VOLUME = 256  # Bambu Lab P2S, 256 x 256 x 256 mm

DEFAULTS = [  # alias, value, description
    ("drawer_w", 400, "Drawer inside width"),
    ("drawer_d", 400, "Drawer inside depth"),
    ("drawer_h", 100, "Drawer inside height"),
    ("clearance", 2, "Gap between tray and drawer, each side"),
    ("module_gap", 0.5, "Gap between neighbouring modules"),
    ("tray_h", 50, "Tray height"),
    ("front_row_d", 250, "Depth of the front row of modules"),
    ("wall", 2.4, "Outer wall thickness"),
    ("divider", 2.4, "Divider thickness"),
    ("floor", 2.0, "Floor thickness"),
    ("scoop_r", 15, "Radius of the curved floor-to-wall scoop"),
    ("rim_r", 1.0, "Rounding on the top edges"),
    ("corner_r", 4, "Outer vertical corner radius"),
    ("foot_chamfer", 0.6, "Bottom outer chamfer against elephant's foot"),
    ("bed_max", 250, "Largest module side allowed on the bed"),
]

# Rows run from the front of the drawer to the back. Each row is split evenly into modules across
# the width, and each module evenly into its compartments. "long" compartments run front to back,
# "cross" compartments run side to side. The last row takes the depth left over.
LAYOUT = [
    {"depth": "front_row_d", "direction": "long", "modules": [
        ("FrontLeft", ["Knives", "Forks", "Spoons"]),
        ("FrontRight", ["Dessert spoons", "Dessert forks", "Steak knives"]),
    ]},
    {"depth": None, "direction": "cross", "modules": [
        ("BackLeft", ["Teaspoons", "Butter knives"]),
        ("BackRight", ["Small utensils", "Misc"]),
    ]},
]

COLORS = [(0.90, 0.88, 0.82), (0.80, 0.84, 0.88)]


def get_document():
    if DOC_NAME in App.listDocuments():
        return App.getDocument(DOC_NAME)
    if os.path.exists(DOC_PATH):
        return App.openDocument(DOC_PATH)
    doc = App.newDocument(DOC_NAME)
    doc.saveAs(DOC_PATH)
    return doc


def read_params(doc):
    sheet = doc.getObject("Params")
    if sheet is None:
        sheet = doc.addObject("Spreadsheet::Sheet", "Params")
        sheet.set("A1", "Parameter (mm)")
        sheet.set("B1", "Value")
    for row, (alias, value, desc) in enumerate(DEFAULTS, start=2):
        if sheet.getCellFromAlias(alias) is None:
            sheet.set(f"A{row}", desc)
            sheet.set(f"B{row}", str(value))
            sheet.setAlias(f"B{row}", alias)
    doc.recompute()
    return {alias: float(sheet.get(alias)) for alias, _, _ in DEFAULTS}


def is_vertical(edge):
    a, b = edge.Vertexes[0].Point, edge.Vertexes[-1].Point
    return abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) < 1e-6 and abs(a.z - b.z) > 1e-6


def tub(w, d, h, r):
    """Box with rounded vertical and bottom edges: the cutter for one compartment."""
    box = Part.makeBox(w, d, h)
    edges = [e for e in box.Edges if min(v.Point.z for v in e.Vertexes) < 1e-6]
    return box.makeFillet(r, edges)


def edges_at_z(shape, z):
    return [e for e in shape.Edges if all(abs(v.Point.z - z) < 1e-6 for v in e.Vertexes)
            and abs(e.BoundBox.ZMin - z) < 1e-6 and abs(e.BoundBox.ZMax - z) < 1e-6]


def module_shape(w, d, p, direction, n):
    h = p["tray_h"]
    wall, div, floor, r = p["wall"], p["divider"], p["floor"], p["scoop_r"]

    body = Part.makeBox(w, d, h)
    body = body.makeFillet(p["corner_r"], [e for e in body.Edges if is_vertical(e)])

    across = w if direction == "long" else d  # the side the compartments are spread along
    along = (d if direction == "long" else w) - 2 * wall
    size = (across - 2 * wall - (n - 1) * div) / n
    for i in range(n):
        offset = wall + i * (size + div)
        if direction == "long":
            cutter = tub(size, along, h, r)
            cutter.translate(V(offset, wall, floor))
        else:
            cutter = tub(along, size, h, r)
            cutter.translate(V(wall, offset, floor))
        body = body.cut(cutter)

    notes = []
    try:
        body = body.makeFillet(p["rim_r"], edges_at_z(body, h))
    except Exception as exc:
        notes.append(f"rim fillet skipped: {exc}")
    try:
        body = body.makeChamfer(p["foot_chamfer"], edges_at_z(body, 0))
    except Exception as exc:
        notes.append(f"foot chamfer skipped: {exc}")
    return body, size, along, notes


def drawer_shape(p, t=10):
    w, d, h = p["drawer_w"], p["drawer_d"], p["drawer_h"]
    outer = Part.makeBox(w + 2 * t, d + 2 * t, h + t, V(-t, -t, -t))
    return outer.cut(Part.makeBox(w, d, h + 1))


def set_shape(doc, name, label, shape, color, transparency=0):
    obj = doc.getObject(name) or doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    if App.GuiUp:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Transparency = transparency
    return obj


def build():
    doc = get_document()
    p = read_params(doc)
    tray_w = p["drawer_w"] - 2 * p["clearance"]
    tray_d = p["drawer_d"] - 2 * p["clearance"]
    gap = p["module_gap"]

    set_shape(doc, "Drawer", "Drawer (reference)", drawer_shape(p), (0.55, 0.45, 0.35), 80)

    report, problems = [], []
    y = p["clearance"]
    for row_index, row in enumerate(LAYOUT):
        if row["depth"]:
            row_d = p[row["depth"]]
        else:
            row_d = p["clearance"] + tray_d - y
        modules = row["modules"]
        mod_w = (tray_w - (len(modules) - 1) * gap) / len(modules)
        x = p["clearance"]
        for mod_index, (name, compartments) in enumerate(modules):
            shape, size, along, notes = module_shape(mod_w, row_d, p, row["direction"],
                                                     len(compartments))
            shape.translate(V(x, y, 0))
            color = COLORS[(row_index + mod_index) % len(COLORS)]
            set_shape(doc, f"Module_{name}", name, shape, color)

            bb = shape.BoundBox
            if max(bb.XLength, bb.YLength) > p["bed_max"] or bb.ZLength > PRINT_VOLUME:
                problems.append(f"{name} is {bb.XLength:.1f} x {bb.YLength:.1f} x "
                                f"{bb.ZLength:.1f}, too big for the bed")
            if not shape.isValid():
                problems.append(f"{name} shape is not valid")
            problems += [f"{name}: {n}" for n in notes]
            report.append(
                f"{name}: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm, "
                f"{shape.Volume / 1000:.0f} cm3, {len(compartments)} {row['direction']} "
                f"compartments {size:.1f} wide x {along:.1f} long ({', '.join(compartments)})")
            x += mod_w + gap
        y += row_d + gap

    doc.recompute()
    doc.save()
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.ActiveDocument.ActiveView.viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    print("\n".join(report))
    print("Problems:\n" + "\n".join(problems) if problems else "No problems found")


if __name__ == "__main__":
    build()
