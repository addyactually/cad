# CAD repo

This repo builds CAD models in FreeCAD through the FreeCAD MCP server (`mcp__freecad__*` tools).
FreeCAD (1.1.x) runs as a local GUI app with the MCP addon's RPC server enabled; the tools drive
that running instance.

## Repo root

FreeCAD runs as its own process, so its working directory is not this repo and every path passed
to it must be absolute. Find the repo root with `git rev-parse --show-toplevel` (run in this repo)
at the start of a session and build paths from it. `<repo>` below means that path.

## Layout

```
README.md
CLAUDE.md
projects/              one folder per CAD project
  <project-name>/
    <project-name>.FCStd   the FreeCAD model
    NOTES.md               goal, requirements, parameters, decisions
    scripts/               Python that builds or modifies the model
    exports/               STEP, STL, DXF, PDF outputs
    references/            sketches, datasheets, photos, drawings
templates/project/     starting skeleton for a new project
lib/                   Python helpers shared across projects
```

## Projects

- Save every project to `projects/<project-name>/` in this repo, as
  `<repo>/projects/<project-name>/<project-name>.FCStd`.
- Project names are lowercase kebab-case (`phone-stand`, `pump-bracket`).
- Start a new project by copying `templates/project/` to `projects/<project-name>/`, then fill in
  `NOTES.md` with the requirements before modelling.
- One main `.FCStd` per project. Extra variants or sub-parts get their own descriptive file names
  in the same folder.
- Keep `NOTES.md` current: record parameter values and design decisions as they are made.

## Working with the FreeCAD MCP

- Check the connection with `get_rpc_status` before starting. If `gui_dispatch` reports `stuck`,
  FreeCAD may need a restart; tell the user rather than retrying blindly.
- If the RPC server isn't reachable, ask the user to start it: open FreeCAD, pick "MCP Addon" from
  the Workbench list, then click "Start RPC Server". The addon's install and setup guide is at
  https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md.
- Prefer `execute_code` with Python for anything beyond a single object. Save the code that builds
  a model to `projects/<project-name>/scripts/` so the model can be rebuilt.
- Set `include_screenshot: false` for steps that don't change the model's appearance, and pick the
  `view_name` that best shows a change when you do want a screenshot.
- Use `execute_code_async` for heavy pure-geometry work that touches neither the document nor the
  GUI; raise `timeout` for slow GUI-thread work such as large STEP imports or exports.
- Save the document (`doc.saveAs(path)` the first time, `doc.save()` after) after each meaningful
  change, and recompute (`doc.recompute()`) before saving or exporting.

## Modelling conventions

- Units are millimetres unless the project's `NOTES.md` says otherwise.
- Build parametrically: drive key dimensions from a `Spreadsheet` named `Params` (or object
  properties) rather than hard-coded numbers, so changes propagate.
- Prefer PartDesign Bodies (sketch, pad, pocket, fillet) for single solid parts and Part
  workbench or Assembly for multi-part work.
- Give objects meaningful labels (`BasePlate`, `MountHole_M4`), not `Pad001`.
- Check results: verify `shape.isValid()`, bounding box and volume after major operations, and
  look at a screenshot before reporting a model as done.

## Exports

- Write exports to `projects/<project-name>/exports/`, named `<project-name>[-<part>].<ext>`.
- STEP for CAD exchange, STL (or 3MF) for 3D printing, DXF for laser cutting or 2D drawings.

## Shared code

- Put helpers reused by more than one project in `lib/` and import them in FreeCAD by adding
  `<repo>/lib` to `sys.path`.
