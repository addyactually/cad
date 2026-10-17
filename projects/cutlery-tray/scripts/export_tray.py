"""Export the cutlery tray modules: one STL per module for printing, plus a STEP of the set.

Run inside FreeCAD after build_tray.py:

    p = "<repo>/projects/cutlery-tray/scripts/export_tray.py"
    exec(compile(open(p).read(), p, "exec"), {"__file__": p, "__name__": "__main__"})
"""

import os

import FreeCAD as App
import Import
import Mesh
import MeshPart

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR = os.path.join(PROJECT_DIR, "exports")


def export():
    doc = App.getDocument("cutlery_tray")
    modules = [o for o in doc.Objects if o.Name.startswith("Module_")]
    for obj in modules:
        shape = obj.Shape.copy()
        bb = shape.BoundBox
        shape.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))  # sit on the bed at the origin
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05,
                                      AngularDeflection=0.0873, Relative=False)
        path = os.path.join(EXPORT_DIR, f"cutlery-tray-{obj.Label.lower()}.stl")
        Mesh.Mesh(mesh).write(path)
        print(f"{path}: {mesh.CountFacets} facets")
    step = os.path.join(EXPORT_DIR, "cutlery-tray.step")
    Import.export(modules, step)
    print(step)


if __name__ == "__main__":
    export()
