# Cutlery tray

## Goal

A cutlery tray for a kitchen drawer, printed on a Bambu Lab P2S, that is easy to pick cutlery out
of, like a standard moulded home cutlery tray.

## Requirements

- Drawer inside, roughly: 400 w × 400 d × 100 h mm.
- Printer: Bambu Lab P2S, build volume 256 × 256 × 256 mm. Keep each piece to 250 mm or less per
  side to leave margin.
- Curved interiors (scooped floor-to-wall transitions) so cutlery slides up and out easily.
- No sharp edges: rounded rims and corners.
- Prints upright with no supports.

## Design

The full tray footprint (396 × 396 mm) is too big for the bed, so it is split into four modules
that sit side by side in the drawer:

| Module | Size (mm) | Compartments |
| ------ | --------- | ------------ |
| FrontLeft | 197.8 × 250 × 50 | 3 running front to back, 62.7 wide × 245 long |
| FrontRight | 197.8 × 250 × 50 | 3 running front to back, 62.7 wide × 245 long |
| BackLeft | 197.8 × 145.5 × 50 | 2 running side to side, 69 wide × 193 long |
| BackRight | 197.8 × 145.5 × 50 | 2 running side to side, 69 wide × 193 long |

- The front row holds full-size cutlery (dinner knives about 230-240 mm, forks and spoons about
  190-205 mm). The back row holds shorter items: teaspoons, butter knives, small utensils.
- Each compartment is a rounded tub: every floor and corner edge has a 15 mm radius scoop,
  leaving a flat floor strip in the middle.
- The two front modules are identical, and so are the two back ones. The compartment names are
  only suggestions.
- Print orientation: as modelled, open side up. Every interior curve faces upward, so no supports
  are needed. The bottom edge has a 0.6 mm chamfer to counter elephant's foot.

## Parameters

Stored in the `Params` spreadsheet in `cutlery-tray.FCStd`. Edit them there and re-run
`scripts/build_tray.py` to rebuild. The module and compartment layout is `LAYOUT` in that script.

| Name | Value | Notes |
| ---- | ----- | ----- |
| drawer_w / drawer_d / drawer_h | 400 / 400 / 100 | Drawer inside |
| clearance | 2 | Gap to the drawer on each side |
| module_gap | 0.5 | Gap between modules |
| tray_h | 50 | Leaves 50 mm above the tray inside the drawer |
| front_row_d | 250 | Depth of the front modules |
| wall / divider / floor | 2.4 / 2.4 / 2.0 | Thicknesses |
| scoop_r | 15 | Interior floor-to-wall radius |
| rim_r | 1.0 | Top edge rounding |
| corner_r | 4 | Outer vertical corners |
| foot_chamfer | 0.6 | Bottom outer edge |
| bed_max | 250 | Size limit checked for every module |

## Scripts

- `scripts/build_tray.py`: creates or updates the document, the Params sheet, the four modules
  and a see-through reference drawer, and checks each module against the bed size.
- `scripts/export_tray.py`: writes the STLs and STEP below.

## Decisions

- 2026-10-17: Split into four modules (two rows of two) to fit the P2S bed. The front row is
  250 deep so dinner knives fit lengthwise, and the back row takes the remaining 145.5 mm, with
  compartments running side to side for shorter items.
- 2026-10-17: Tray height 50 mm, similar to commercial trays. It is shallow enough to reach into
  and leaves headroom in the 100 mm drawer.
- 2026-10-17: Modules butt together loosely and are held in place by the drawer walls (4 mm of
  total play). They have no clips or joints yet.

## Open questions

- Actual drawer dimensions and the user's longest knife and serving utensils.
- Whether to add clips between modules, or non-slip foot recesses.

## Exports

| File | Format | Purpose |
| ---- | ------ | ------- |
| exports/cutlery-tray-frontleft.stl | STL | Print |
| exports/cutlery-tray-frontright.stl | STL | Print (same as front left) |
| exports/cutlery-tray-backleft.stl | STL | Print |
| exports/cutlery-tray-backright.stl | STL | Print (same as back left) |
| exports/cutlery-tray.step | STEP | All four modules, in drawer position |
