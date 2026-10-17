"""Export the cutlery tray bins: one STL per bin for printing, plus a STEP of the set.

Run inside FreeCAD after build_tray.py:

    p = "<repo>/projects/cutlery-tray/scripts/export_tray.py"
    exec(compile(open(p).read(), p, "exec"), {"__file__": p, "__name__": "__main__"})

STLs left over from bins that no longer exist are removed.
"""

import glob
import os
import re

import FreeCAD as App
import Import
import Mesh
import MeshPart

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR = os.path.join(PROJECT_DIR, "exports")


def export():
    doc = App.getDocument("cutlery_tray")
    bins = [o for o in doc.Objects if o.Name.startswith("Bin_")]
    written = set()
    for obj in bins:
        shape = obj.Shape.copy()
        bb = shape.BoundBox
        shape.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))  # sit on the bed at the origin
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05,
                                      AngularDeflection=0.0873, Relative=False)
        slug = re.sub(r"\W+", "-", obj.Label.lower()).strip("-")
        path = os.path.join(EXPORT_DIR, f"cutlery-tray-{slug}.stl")
        Mesh.Mesh(mesh).write(path)
        written.add(path)
        print(f"{path}: {mesh.CountFacets} facets")
    for old in glob.glob(os.path.join(EXPORT_DIR, "cutlery-tray-*.stl")):
        if old not in written:
            os.remove(old)
            print(f"removed {old}")
    step = os.path.join(EXPORT_DIR, "cutlery-tray.step")
    Import.export(bins, step)
    print(step)


if __name__ == "__main__":
    export()
