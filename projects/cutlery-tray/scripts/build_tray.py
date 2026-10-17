"""Build the cutlery tray modules in the running FreeCAD session.

Run inside FreeCAD (for example through the MCP execute_code tool):

    p = "<repo>/projects/cutlery-tray/scripts/build_tray.py"
    exec(compile(open(p).read(), p, "exec"), {"__file__": p, "__name__": "__main__"})

Dimensions live in the document's Params spreadsheet, which is created with the defaults below
if it doesn't exist yet (new parameters are appended to an existing sheet). Edit Params and re-run
this script to rebuild. The split into modules and compartments is defined in ROWS and MODULES.

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
    ("drawer_w", 362, "Drawer inside width"),
    ("drawer_d", 416, "Drawer inside depth"),
    ("drawer_h", 100, "Drawer inside height"),
    ("clearance", 2, "Gap between tray and drawer, each side"),
    ("module_gap", 1.5, "Gap between neighbouring modules"),
    ("tray_h", 50, "Tray height"),
    ("front_row_d", 250, "Depth of the front row of modules"),
    ("wall", 2.4, "Outer wall thickness"),
    ("divider", 2.4, "Divider thickness"),
    ("floor", 2.0, "Floor thickness"),
    ("scoop_r", 15, "Radius of the curved floor-to-wall scoop"),
    ("rim_r", 1.0, "Rounding on the top edges"),
    ("corner_r", 4, "Outer corner radius, also the bezel's front edge"),
    ("foot_chamfer", 0.6, "Bottom outer chamfer against elephant's foot"),
    ("bed_max", 250, "Largest module side allowed on the bed"),
    ("front_bezel", 7.5, "Front wall (bezel) thickness of the front row"),
    ("long_w", 45, "Width of the long-items channel"),
    ("knife_l", 230, "Longest knife"),
    ("spoon_l", 200, "Longest spoon or fork"),
    ("teaspoon_l", 150, "Longest teaspoon"),
    ("chopstick_l", 250, "Longest chopstick or other long item"),
    ("item_margin", 10, "Compartment length beyond the item, at the rim"),
]

# Rows run from the front of the drawer to the back; a row's depth is a parameter, and the last
# row (None) takes what is left. Columns share the width evenly.
ROWS = ["front_row_d", None]
COLUMNS = 2


def lane(*labels, width=None, open_end=None, fits=None):
    """A strip of a module running front to back.

    One label makes a single compartment along the strip; several labels split it into
    compartments running side to side. `width` names a parameter, otherwise lanes share the
    leftover width evenly. `open_end` ("front" or "back") leaves out that end wall, so the
    compartment carries on into the neighbouring module. `fits` names the item-length parameter
    each compartment must hold (plus item_margin).
    """
    return {"labels": labels, "width": width, "open": open_end, "fits": fits}


# (row, column) -> (name, lanes left to right)
MODULES = {
    (0, 0): ("FrontLeft", [lane("Knives", fits="knife_l"), lane("Forks", fits="spoon_l"),
                           lane("Spoons", fits="spoon_l")]),
    (0, 1): ("FrontRight", [lane("Soup spoons", fits="spoon_l"),
                            lane("Dessert forks", fits="spoon_l"),
                            lane("Long items", width="long_w", open_end="back",
                                 fits="chopstick_l")]),
    (1, 0): ("BackLeft", [lane("Teaspoons", "Butter knives", fits="teaspoon_l")]),
    (1, 1): ("BackRight", [lane("Small utensils"), lane("Misc"),
                           lane("Long items", width="long_w", open_end="front",
                                fits="chopstick_l")]),
}

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
    row = 1 + max(int("".join(c for c in cell if c.isdigit())) for cell in sheet.getUsedCells())
    for alias, value, desc in DEFAULTS:
        if sheet.getCellFromAlias(alias) is None:
            sheet.set(f"A{row}", desc)
            sheet.set(f"B{row}", str(value))
            sheet.setAlias(f"B{row}", alias)
            row += 1
    doc.recompute()
    return {alias: float(sheet.get(alias)) for alias, _, _ in DEFAULTS}


def is_vertical(edge):
    a, b = edge.Vertexes[0].Point, edge.Vertexes[-1].Point
    return abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) < 1e-6 and abs(a.z - b.z) > 1e-6


def is_sharp(shape, edge):
    """True unless the two faces meeting at the edge are tangent (already blended)."""
    faces = shape.ancestorsOfType(edge, Part.Face)
    if len(faces) != 2:
        return False
    pt = edge.valueAt((edge.FirstParameter + edge.LastParameter) / 2)
    n1, n2 = (f.normalAt(*f.Surface.parameter(pt)) for f in faces)
    return abs(n1.dot(n2)) < 0.999


def edges_at_z(shape, z):
    return [e for e in shape.Edges
            if abs(e.BoundBox.ZMin - z) < 1e-6 and abs(e.BoundBox.ZMax - z) < 1e-6
            and is_sharp(shape, e)]


def tub(w, d, h, r):
    """Box with rounded vertical and bottom edges: the cutter for one compartment."""
    box = Part.makeBox(w, d, h)
    edges = [e for e in box.Edges if min(v.Point.z for v in e.Vertexes) < 1e-6]
    return box.makeFillet(r, edges)


def module_shape(w, d, p, lanes, front_wall):
    h = p["tray_h"]
    wall, div, floor, r = p["wall"], p["divider"], p["floor"], p["scoop_r"]
    open_ends = {ln["open"] for ln in lanes if ln["open"]}

    # Round the outside corners, except on a side where a compartment runs on into the next
    # module (rounding there would thin the wall ends). A front bezel gets a rounded top edge.
    body = Part.makeBox(w, d, h)
    rounded = []
    for e in body.Edges:
        y = e.Vertexes[0].Point.y
        side = "front" if y < 1e-6 else "back"
        if is_vertical(e) and side not in open_ends:
            rounded.append(e)
        elif (front_wall > wall and e.BoundBox.YMax < 1e-6 and e.BoundBox.ZMin > h - 1e-6):
            rounded.append(e)
    body = body.makeFillet(p["corner_r"], rounded)

    fixed = sum(p[ln["width"]] for ln in lanes if ln["width"])
    flexible = [ln for ln in lanes if not ln["width"]]
    flex_w = (w - 2 * wall - (len(lanes) - 1) * div - fixed) / max(len(flexible), 1)
    y0, y1 = front_wall, d - wall
    x = wall
    compartments = []
    for ln in lanes:
        lw = p[ln["width"]] if ln["width"] else flex_w
        n = len(ln["labels"])
        if n == 1:
            start = y0 - (front_wall + r + 1) if ln["open"] == "front" else y0
            end = y1 + (wall + r + 1) if ln["open"] == "back" else y1
            cutter = tub(lw, end - start, h, r)
            cutter.translate(V(x, start, floor))
            body = body.cut(cutter)
            length = min(end, d) - max(start, 0)
            compartments.append({"label": ln["labels"][0], "width": lw, "length": length,
                                 "open": ln["open"], "fits": ln["fits"]})
        else:
            size = (y1 - y0 - (n - 1) * div) / n
            for i, label in enumerate(ln["labels"]):
                cutter = tub(lw, size, h, r)
                cutter.translate(V(x, y0 + i * (size + div), floor))
                body = body.cut(cutter)
                compartments.append({"label": label, "width": size, "length": lw,
                                     "open": None, "fits": ln["fits"], "cross": True})
        x += lw + div

    notes = []
    try:
        body = body.makeFillet(p["rim_r"], edges_at_z(body, h))
    except Exception as exc:
        notes.append(f"rim fillet skipped: {exc}")
    try:
        body = body.makeChamfer(p["foot_chamfer"], edges_at_z(body, 0))
    except Exception as exc:
        notes.append(f"foot chamfer skipped: {exc}")
    return body, compartments, notes


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


def check_fit(label, width, length, fits, p, report, problems, note=""):
    line = f"  {label}: {width:.1f} wide x {length:.1f} long{note}"
    if fits:
        need = p[fits] + p["item_margin"]
        line += f", needs {need:.0f} for {p[fits]:.0f} mm items"
        if length < need - 1e-6:
            problems.append(f"{label} is {length:.1f} long, needs {need:.0f}")
    report.append(line)


def build():
    doc = get_document()
    p = read_params(doc)
    tray_w = p["drawer_w"] - 2 * p["clearance"]
    tray_d = p["drawer_d"] - 2 * p["clearance"]
    gap = p["module_gap"]

    set_shape(doc, "Drawer", "Drawer (reference)", drawer_shape(p), (0.55, 0.45, 0.35), 80)

    fixed_rows = sum(p[r] for r in ROWS if r)
    rest = (tray_d - fixed_rows - (len(ROWS) - 1) * gap) / max(ROWS.count(None), 1)
    row_depths = [p[r] if r else rest for r in ROWS]
    col_w = (tray_w - (COLUMNS - 1) * gap) / COLUMNS

    report, problems, channels = [], [], {}
    for (row, col), (name, lanes) in MODULES.items():
        d = row_depths[row]
        x = p["clearance"] + col * (col_w + gap)
        y = p["clearance"] + sum(row_depths[:row]) + row * gap
        front_wall = p["front_bezel"] if row == 0 else p["wall"]
        shape, compartments, notes = module_shape(col_w, d, p, lanes, front_wall)
        shape.translate(V(x, y, 0))
        set_shape(doc, f"Module_{name}", name, shape, COLORS[(row + col) % len(COLORS)])

        bb = shape.BoundBox
        if max(bb.XLength, bb.YLength) > p["bed_max"] or bb.ZLength > PRINT_VOLUME:
            problems.append(f"{name} is {bb.XLength:.1f} x {bb.YLength:.1f} x "
                            f"{bb.ZLength:.1f}, too big for the bed")
        if not shape.isValid():
            problems.append(f"{name} shape is not valid")
        problems += [f"{name}: {n}" for n in notes]
        report.append(f"{name}: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm, "
                      f"{shape.Volume / 1000:.0f} cm3")
        for c in compartments:
            if c["open"]:
                channels.setdefault(c["label"], []).append(c)
            else:
                check_fit(c["label"], c["width"], c["length"], c["fits"], p, report, problems,
                          " (side to side)" if c.get("cross") else "")
    for label, parts in channels.items():
        length = sum(c["length"] for c in parts) + (len(parts) - 1) * gap
        check_fit(label, parts[0]["width"], length, parts[0]["fits"], p, report, problems,
                  f" (across {len(parts)} modules)")

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
