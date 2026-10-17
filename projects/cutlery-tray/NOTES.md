# Cutlery tray

## Goal

A cutlery tray for a kitchen drawer, printed on a Bambu Lab P2S, that is easy to pick cutlery out
of, like a standard moulded home cutlery tray.

## Requirements

- Drawer inside: 362 w × 416 d mm. The height is assumed to still be about 100 mm.
- Printer: Bambu Lab P2S, build volume 256 × 256 × 256 mm. Keep each piece to 250 mm or less per
  side to leave margin.
- Curved interiors (scooped floor-to-wall transitions) so cutlery slides up and out easily.
- Item lengths to fit: knives 230 mm, soup and regular spoons and forks 200 mm, teaspoons
  150 mm, chopsticks 250 mm. Each compartment is at least 10 mm longer than its item at the rim
  (`item_margin`), so the item lies almost flat, with its ends no more than about 4 mm up the
  end scoops.
- Space for long items such as chopsticks and straws.
- A wider bezel along the front edge of the tray.
- No sharp edges: rounded rims and corners.
- Prints upright with no supports.

## Design

The tray footprint (358 × 412 mm) is split into four modules, two rows of two:

| Module | Size (mm) | Compartments (inside, at the rim) |
| ------ | --------- | --------------------------------- |
| FrontLeft | 178.2 × 250 × 50 | Knives, forks, spoons: 56.2 wide × 240.1 long, front to back |
| FrontRight | 178.2 × 250 × 50 | Soup spoons, dessert forks: 61.8 × 240.1; long-items channel 45 wide, open at the back |
| BackLeft | 178.2 × 160.5 × 50 | Teaspoons, butter knives: 173.4 long × 76.6, side to side |
| BackRight | 178.2 × 160.5 × 50 | Small utensils, misc: 61.8 × 155.7; long-items channel 45 wide, open at the front |

- **Long items:** a 45 mm channel runs the full depth down the right-hand side. It is split
  across FrontRight and BackRight and left open where they meet, so it reads as one channel
  402 mm long at the rim. Both halves have the same cross-section, so the floor and walls line
  up at the joint. Chopsticks need 260 mm, which no 250 mm piece can hold, so the channel has to
  span two pieces; it also takes longer items such as straws, tongs and serving spoons.
- **Front bezel:** the front modules have a 7.5 mm front wall with a 4 mm rounded front edge.
  This is the most the 250 mm front pieces allow while keeping 240 mm for knives.
- **Scoops:** each compartment is a rounded tub. Every floor and corner edge has a 15 mm radius,
  leaving a flat floor strip down the middle.
- **Corners:** outside corners have a 4 mm radius, except where the long-items channel crosses
  between modules. Those corners are square so the wall ends stay full thickness and meet flush.
- **Spacing:** 1.5 mm between modules and 2 mm to the drawer on every side.
- **Print orientation:** as modelled, open side up. Every interior curve faces upward, so no
  supports are needed. The bottom edge has a 0.6 mm chamfer to counter elephant's foot.

## Parameters

Stored in the `Params` spreadsheet in `cutlery-tray.FCStd`. Edit them there and re-run
`scripts/build_tray.py` to rebuild. The module and compartment layout is `ROWS` and `MODULES`
in that script.

| Name | Value | Notes |
| ---- | ----- | ----- |
| drawer_w / drawer_d / drawer_h | 362 / 416 / 100 | Drawer inside |
| clearance | 2 | Gap to the drawer on each side |
| module_gap | 1.5 | Gap between modules |
| tray_h | 50 | Leaves 50 mm above the tray inside the drawer |
| front_row_d | 250 | Depth of the front modules |
| front_bezel | 7.5 | Front wall thickness of the front row |
| long_w | 45 | Long-items channel width |
| knife_l / spoon_l / teaspoon_l / chopstick_l | 230 / 200 / 150 / 250 | Item lengths each compartment must hold |
| item_margin | 10 | Compartment length beyond the item, at the rim |
| wall / divider / floor | 2.4 / 2.4 / 2.0 | Thicknesses |
| scoop_r | 15 | Interior floor-to-wall radius |
| rim_r | 1.0 | Top edge rounding |
| corner_r | 4 | Outer vertical corners and the bezel's front edge |
| foot_chamfer | 0.6 | Bottom outer edge |
| bed_max | 250 | Size limit checked for every module |

## Scripts

- `scripts/build_tray.py`: creates or updates the document, the Params sheet, the four modules
  and a see-through reference drawer. It checks each module against the bed size and each
  compartment against its item length.
- `scripts/export_tray.py`: writes the STLs and STEP below.

## Decisions

- 2026-10-17: Split into four modules (two rows of two) to fit the P2S bed.
- 2026-10-17: Tray height 50 mm, similar to commercial trays. It is shallow enough to reach into
  and leaves headroom in the 100 mm drawer.
- 2026-10-17: Changed the drawer size to 362 × 416. Took "416h" to mean depth.
- 2026-10-17: Added a full-depth long-items channel, split across two modules with open ends,
  because 370 mm is too long to print in one piece.
- 2026-10-17: Front bezel 10 mm, then reduced to 7.5 mm once knives were set at 230 mm. At
  10 mm the front compartments were 237.6 mm, short of the 240 mm needed.
- 2026-10-17: Item lengths set by the user: knives 230, spoons and forks 200, teaspoons 150,
  chopsticks 250. Kept the full-length channel because 260 mm still needs two pieces.
- 2026-10-17: Increased the gap between modules from 0.5 to 1.5 mm.
- 2026-10-17: Modules sit loose and the drawer walls hold them in place. They have no clips yet,
  so the two channel halves can drift sideways by up to about 2 mm.

## Open questions

- Whether "416h" was the depth (assumed) and whether the drawer height is still 100 mm.
- Whether to add clips between modules (which would also keep the channel halves aligned), or
  non-slip foot recesses.

## Exports

| File | Format | Purpose |
| ---- | ------ | ------- |
| exports/cutlery-tray-frontleft.stl | STL | Print |
| exports/cutlery-tray-frontright.stl | STL | Print |
| exports/cutlery-tray-backleft.stl | STL | Print |
| exports/cutlery-tray-backright.stl | STL | Print |
| exports/cutlery-tray.step | STEP | All four modules, in drawer position |
