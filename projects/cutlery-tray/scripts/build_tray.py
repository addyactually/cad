"""Build the cutlery tray bins in the running FreeCAD session.

Run inside FreeCAD (for example through the MCP execute_code tool):

    p = "<repo>/projects/cutlery-tray/scripts/build_tray.py"
    exec(compile(open(p).read(), p, "exec"), {"__file__": p, "__name__": "__main__"})

Every compartment is its own printed bin. Bins sit side by side in the drawer and are held to
their neighbours by disc magnets glued into holes in the outside of their walls.

Dimensions live in the document's Params spreadsheet, which is created with the defaults below
if it doesn't exist yet (new parameters are appended to an existing sheet). Edit Params and re-run
this script to rebuild. The arrangement of bins is defined in COLUMNS.

Coordinates: origin at the drawer's inside front-left floor corner, X across the drawer width,
Y from the front (opening side) to the back, Z up.
"""

import math
import os
import re

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
    ("bin_gap", 0.5, "Gap between neighbouring bins"),
    ("tray_h", 50, "Bin height"),
    ("wall", 2.0, "Bin wall thickness"),
    ("floor", 2.0, "Floor thickness"),
    ("scoop_r", 15, "Radius of the curved floor-to-wall scoop"),
    ("rim_r", 0.6, "Rounding on the inside top edges"),
    ("join_chamfer", 1.0, "Bevel on the outside top edges, hides the joins"),
    ("corner_r", 2, "Outside vertical corner radius"),
    ("foot_chamfer", 0.6, "Bottom outer chamfer against elephant's foot"),
    ("bed_max", 250, "Usable bed size; longer bins print diagonally"),
    ("front_bezel", 10, "Front wall (bezel) thickness of the front bins"),
    ("back_bezel", 10, "Back wall (bezel) thickness of the back bins"),
    ("knife_l", 230, "Longest knife"),
    ("spoon_l", 200, "Longest spoon or fork"),
    ("teaspoon_l", 150, "Longest teaspoon"),
    ("chopstick_l", 250, "Longest chopstick"),
    ("item_margin", 10, "Compartment length beyond the item, at the rim"),
    ("magnet_d", 6, "Magnet diameter"),
    ("magnet_t", 3, "Magnet thickness"),
    ("magnet_fit", 0.2, "Extra hole diameter and depth for the magnet"),
    ("magnet_z", 4.5, "Height of the magnet centres above the bin bottom"),
    ("magnet_inset", 25, "Distance from the ends of a joint to the outer magnets"),
    ("min_skin", 0.8, "Least plastic between a magnet hole and the compartment"),
]


def bin_(label, fits=None):
    """One bin. A bin with `fits` is made just long enough for that item; the last bin in a
    column takes the depth that is left."""
    return {"label": label, "fits": fits}


def column(*bins, width=None):
    """A column of bins from the front of the drawer to the back. `width` names an inside-width
    parameter; otherwise columns share the leftover width evenly."""
    return {"bins": bins, "width": width}


COLUMNS = [
    column(bin_("Knives", fits="knife_l"), bin_("Small items")),
    column(bin_("Forks", fits="spoon_l"), bin_("Teaspoons", fits="teaspoon_l")),
    column(bin_("Spoons", fits="spoon_l"), bin_("Spare")),
    column(bin_("Soup spoons", fits="spoon_l"), bin_("Misc")),
    column(bin_("Chopsticks", fits="chopstick_l"), bin_("Odds and ends")),
]

# Mirror the layout left to right: each bin is made as long as the bin in the same place in the
# mirrored column, so the joins line up symmetrically. Give mirrored columns the same width.
SYMMETRIC = True

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


def flat_at_z(edge, z):
    return abs(edge.BoundBox.ZMin - z) < 1e-6 and abs(edge.BoundBox.ZMax - z) < 1e-6


def tub(w, d, h, r):
    """Box with rounded vertical and bottom edges: the cutter for one compartment."""
    box = Part.makeBox(w, d, h)
    edges = [e for e in box.Edges if min(v.Point.z for v in e.Vertexes) < 1e-6]
    return box.makeFillet(r, edges)


def layout(p):
    """Place every bin. Returns dicts with the bin's rectangle in drawer coordinates."""
    tray_w = p["drawer_w"] - 2 * p["clearance"]
    tray_d = p["drawer_d"] - 2 * p["clearance"]
    gap, wall = p["bin_gap"], p["wall"]
    fixed = sum(p[c["width"]] + 2 * wall for c in COLUMNS if c["width"])
    flexible = [c for c in COLUMNS if not c["width"]]
    flex_w = (tray_w - fixed - (len(COLUMNS) - 1) * gap) / max(len(flexible), 1)

    def walls(col, row):
        last = row == len(COLUMNS[col]["bins"]) - 1
        return (p["front_bezel"] if row == 0 else wall), (p["back_bezel"] if last else wall)

    def depth(col, row):
        front_wall, back_wall = walls(col, row)
        return p[COLUMNS[col]["bins"][row]["fits"]] + p["item_margin"] + front_wall + back_wall

    bins = []
    x = p["clearance"]
    for col_index, col in enumerate(COLUMNS):
        w = p[col["width"]] + 2 * wall if col["width"] else flex_w
        mirror = len(COLUMNS) - 1 - col_index if SYMMETRIC else col_index
        y = p["clearance"]
        for row_index, b in enumerate(col["bins"]):
            front_wall, back_wall = walls(col_index, row_index)
            if row_index == len(col["bins"]) - 1:
                d = p["clearance"] + tray_d - y
            else:
                d = max(depth(col_index, row_index), depth(mirror, row_index))
            bins.append({**b, "x0": x, "y0": y, "x1": x + w, "y1": y + d,
                         "front_wall": front_wall, "back_wall": back_wall,
                         "col": col_index, "row": row_index,
                         "magnets": []})
            y += d + gap
        x += w + gap
    return bins


def joint_positions(length, p):
    n = 1 if length < 120 else 2 if length < 260 else 3
    if n == 1:
        return [length / 2]
    inset = p["magnet_inset"]
    return [inset + i * (length - 2 * inset) / (n - 1) for i in range(n)]


def place_magnets(bins, p):
    """Put matching magnet positions on both sides of every joint between neighbouring bins.

    Each magnet is (axis, side, position along the face) in drawer coordinates, where axis is
    the direction the face points ("x" or "y") and side is +1 or -1.
    """
    gap = p["bin_gap"]
    joints = 0
    for a in bins:
        for b in bins:
            if abs(a["x1"] + gap - b["x0"]) < 1e-6:  # b is to the right of a
                lo, hi = max(a["y0"], b["y0"]), min(a["y1"], b["y1"])
                if hi - lo > 2 * p["magnet_inset"]:
                    for t in joint_positions(hi - lo, p):
                        a["magnets"].append(("x", +1, lo + t))
                        b["magnets"].append(("x", -1, lo + t))
                        joints += 1
            if abs(a["y1"] + gap - b["y0"]) < 1e-6:  # b is behind a
                lo, hi = max(a["x0"], b["x0"]), min(a["x1"], b["x1"])
                if hi - lo > 2 * p["magnet_inset"]:
                    for t in joint_positions(hi - lo, p):
                        a["magnets"].append(("y", +1, lo + t))
                        b["magnets"].append(("y", -1, lo + t))
                        joints += 1
    return joints


def bin_shape(b, p):
    """Model one bin in drawer coordinates. Returns the shape, the compartment cutter, notes."""
    w, d = b["x1"] - b["x0"], b["y1"] - b["y0"]
    h, wall, floor, r = p["tray_h"], p["wall"], p["floor"], p["scoop_r"]
    front, back = b["front_wall"], b["back_wall"]
    notes = []

    body = Part.makeBox(w, d, h)
    body = body.makeFillet(p["corner_r"], [e for e in body.Edges if is_vertical(e)])
    body = body.makeChamfer(p["join_chamfer"], [e for e in body.Edges if flat_at_z(e, h)])

    cutter = tub(w - 2 * wall, d - front - back, h, r)
    cutter.translate(V(wall, front, floor))
    body = body.cut(cutter)

    rim = [e for e in body.Edges if flat_at_z(e, h)
           and e.BoundBox.XMin > wall - 1e-3 and e.BoundBox.XMax < w - wall + 1e-3
           and e.BoundBox.YMin > front - 1e-3 and e.BoundBox.YMax < d - back + 1e-3]
    try:
        body = body.makeFillet(p["rim_r"], rim)
    except Exception as exc:
        notes.append(f"rim fillet skipped: {exc}")
    try:
        body = body.makeChamfer(p["foot_chamfer"], [e for e in body.Edges if flat_at_z(e, 0)])
    except Exception as exc:
        notes.append(f"foot chamfer skipped: {exc}")

    hole_r = (p["magnet_d"] + p["magnet_fit"]) / 2
    depth = p["magnet_t"] + p["magnet_fit"]
    skins = []
    for axis, side, pos in b["magnets"]:
        if axis == "x":
            x = w if side > 0 else 0
            hole = Part.makeCylinder(hole_r, depth, V(x, pos - b["y0"], p["magnet_z"]),
                                     V(-side, 0, 0))
        else:
            y = d if side > 0 else 0
            hole = Part.makeCylinder(hole_r, depth, V(pos - b["x0"], y, p["magnet_z"]),
                                     V(0, -side, 0))
        skins.append(hole.distToShape(cutter)[0])
        body = body.cut(hole)
    if skins and min(skins) < p["min_skin"]:
        notes.append(f"magnet hole only {min(skins):.2f} mm from the compartment")

    body.translate(V(b["x0"], b["y0"], 0))
    return body, skins, notes


def print_fit(w, d, p):
    if max(w, d) <= p["bed_max"]:
        return "flat"
    if (w + d) / math.sqrt(2) <= p["bed_max"]:
        return "diagonal"
    return None


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


def object_name(label):
    return "Bin_" + re.sub(r"\W+", "_", label).strip("_")


def build():
    doc = get_document()
    p = read_params(doc)
    set_shape(doc, "Drawer", "Drawer (reference)", drawer_shape(p), (0.55, 0.45, 0.35), 80)

    bins = layout(p)
    joints = place_magnets(bins, p)
    names = {object_name(b["label"]) for b in bins}
    for obj in list(doc.Objects):
        if obj.Name.startswith(("Module_", "Bin_")) and obj.Name not in names:
            doc.removeObject(obj.Name)

    report, problems, all_skins = [], [], []
    for b in bins:
        shape, skins, notes = bin_shape(b, p)
        all_skins += skins
        set_shape(doc, object_name(b["label"]), b["label"], shape,
                  COLORS[(b["col"] + b["row"]) % len(COLORS)])

        w, d = b["x1"] - b["x0"], b["y1"] - b["y0"]
        rim_w, rim_l = w - 2 * p["wall"], d - b["front_wall"] - b["back_wall"]
        orientation = print_fit(w, d, p)
        line = (f"{b['label']}: bin {w:.1f} x {d:.1f}, inside {rim_w:.1f} x {rim_l:.1f}, "
                f"{len(b['magnets'])} magnets, prints {orientation or 'NOT ON THE BED'}")
        if b["fits"]:
            need = p[b["fits"]] + p["item_margin"]
            line += f", needs {need:.0f}"
            if rim_l < need - 1e-6:
                problems.append(f"{b['label']} is {rim_l:.1f} long, needs {need:.0f}")
        if not orientation or shape.BoundBox.ZLength > PRINT_VOLUME:
            problems.append(f"{b['label']} ({w:.1f} x {d:.1f}) doesn't fit the bed")
        if not shape.isValid():
            problems.append(f"{b['label']} shape is not valid")
        problems += [f"{b['label']}: {n}" for n in notes]
        report.append(line)

    extent_x = max(b["x1"] for b in bins) + p["clearance"]
    extent_y = max(b["y1"] for b in bins) + p["clearance"]
    if extent_x > p["drawer_w"] + 1e-6 or extent_y > p["drawer_d"] + 1e-6:
        problems.append(f"bins reach {extent_x:.1f} x {extent_y:.1f}, beyond the drawer")
    report.append(f"{len(bins)} bins, {joints} magnet pairs ({2 * joints} magnets), "
                  f"thinnest skin behind a magnet {min(all_skins):.2f} mm")

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
