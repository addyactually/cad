# Cutlery tray

## Goal

A cutlery tray for a kitchen drawer, printed on a Bambu Lab P2S, that is easy to pick cutlery out
of, like a standard moulded home cutlery tray.

## Requirements

- Drawer inside: 362 w × 416 d mm. The height is assumed to be about 100 mm. It only matters if
  it drops below about 55 mm, since the bins are 50 mm tall.
- Printer: Bambu Lab P2S, build volume 256 × 256 × 256 mm. Bins must fit within 250 mm, either
  flat or diagonally across the bed.
- Item lengths to fit: knives 230 mm, soup and regular spoons and forks 200 mm, teaspoons
  150 mm, chopsticks 250 mm. Each compartment is at least 10 mm longer than its item at the rim
  (`item_margin`), so the item lies almost flat, with its ends no more than about 4 mm up the
  end scoops.
- Curved interiors (scooped floor-to-wall transitions) so cutlery slides up and out easily.
- A wider bezel along the front and back edges of the tray.
- Symmetrical left to right.
- No sharp edges, and the joins between pieces should be hidden.
- Prints upright with no supports.

## Design

Every compartment is its own bin, printed separately and sized to its item. The bins sit side by
side in five columns and are held to their neighbours by magnets. Each column has a front bin
that is just long enough for its item and a back bin that takes the remaining depth. The layout
is mirrored left to right (`SYMMETRIC`): mirrored columns share a width, and each front bin is
as long as its mirror twin needs, so every join lines up symmetrically.

| Column | Front bin (outside / inside, mm) | Back bin (outside / inside, mm) |
| ------ | -------------------------------- | ------------------------------- |
| 1 | Knives: 64 × 272 / 60 × 260 | Small items: 64 × 139.5 / 60 × 127.5 |
| 2 | Forks: 76 × 222 / 72 × 210 | Teaspoons: 76 × 189.5 / 72 × 177.5 |
| 3 | Spoons: 76 × 222 / 72 × 210 | Spare: 76 × 189.5 / 72 × 177.5 |
| 4 | Soup spoons: 76 × 222 / 72 × 210 | Misc: 76 × 189.5 / 72 × 177.5 |
| 5 | Chopsticks: 64 × 272 / 60 × 260 | Odds and ends: 64 × 139.5 / 60 × 127.5 |

All bins are 50 mm tall. Labels are only names; any bin can hold anything that fits.

- **Bezels:** the front bins have a 10 mm front wall and the back bins a 10 mm back wall.
- **Symmetry:** the knife bin matches the chopstick bin, so it has 260 mm inside for 230 mm knives.
- **Scoops:** each bin's floor and corner edges have a 15 mm radius, leaving a flat floor strip
  down the middle.
- **Walls:** 2 mm, with a 2 mm floor. Neighbouring bins make a 4.5 mm double wall, including the
  0.5 mm gap between them.
- **Hidden joins:** every outside top edge has a 1 mm × 45° bevel. Where two bins meet, the
  bevels form a small V-groove, so the gap reads as a deliberate line. The inside top edges are
  rounded 0.6 mm.
- **Corners:** outside vertical corners are rounded 2 mm.
- **Magnets:** 6 × 3 mm disc magnets (N52 or similar), 42 in total, in 21 pairs. The holes are
  6.2 mm across and 3.2 mm deep, open on the outside of the wall, with their centres 4.5 mm above
  the bottom. That puts them in the solid plastic behind the scoop, with at least 1.7 mm between
  each hole and the compartment. The script places them only where two bins share a face: one
  magnet for a shared face under 120 mm long, two up to 260 mm, three beyond. Both sides of each
  pair are at the same spot. Outside faces against the drawer have none.
- **Printing:** open side up, no supports. The magnet holes are horizontal 6.2 mm circles, which
  print fine without support. The knife and chopstick bins are longer than 250 mm, so rotate
  them 45° on the plate (they fit diagonally). The other bins print square-on. The bottom edge
  has a 0.6 mm chamfer to counter elephant's foot.

## Assembly

1. Print all ten bins.
2. Glue the magnets into one bin with cyanoacrylate (superglue) or epoxy, flush with the wall.
3. For each neighbouring bin, let a loose magnet snap onto each glued one, mark its outward face,
   and glue it in that way round. This keeps every pair attracting. Work outwards from one bin.
4. Let the glue cure before snapping the bins together in the drawer.

## Parameters

Stored in the `Params` spreadsheet in `cutlery-tray.FCStd`. Edit them there and re-run
`scripts/build_tray.py` to rebuild. The arrangement of bins is `COLUMNS` in that script.

| Name | Value | Notes |
| ---- | ----- | ----- |
| drawer_w / drawer_d / drawer_h | 362 / 416 / 100 | Drawer inside |
| clearance | 2 | Gap to the drawer on each side |
| bin_gap | 0.5 | Gap between bins |
| tray_h | 50 | Bin height |
| wall / floor | 2.0 / 2.0 | Thicknesses |
| scoop_r | 15 | Interior floor-to-wall radius |
| rim_r | 0.6 | Inside top edge rounding |
| join_chamfer | 1.0 | Outside top edge bevel |
| corner_r | 2 | Outside vertical corners |
| foot_chamfer | 0.6 | Bottom outer edge |
| bed_max | 250 | Usable bed; longer bins must fit diagonally |
| front_bezel / back_bezel | 10 / 10 | Front wall of the front bins, back wall of the back bins |
| outer_w | 60 | Inside width of the two outer columns |
| knife_l / spoon_l / teaspoon_l / chopstick_l | 230 / 200 / 150 / 250 | Item lengths |
| item_margin | 10 | Compartment length beyond the item, at the rim |
| magnet_d / magnet_t / magnet_fit | 6 / 3 / 0.2 | Magnet size and hole allowance |
| magnet_z | 4.5 | Magnet centre height |
| magnet_inset | 25 | Outer magnets' distance from the ends of a shared face |
| min_skin | 0.8 | Least plastic allowed between a magnet hole and the compartment |

## Scripts

- `scripts/build_tray.py`: creates or updates the document, the Params sheet, the bins, the
  magnet holes and a see-through reference drawer. It checks that each item fits its bin, that
  each bin fits the bed (flat or diagonal) and the drawer, and that each magnet hole keeps its
  plastic skin.
- `scripts/export_tray.py`: writes one STL per bin and a STEP of the set. It removes STLs for bins
  that no longer exist.

## Decisions

- 2026-10-17: Changed the drawer size to 362 × 416, taking "416h" to mean depth. The height is
  confirmed as not critical.
- 2026-10-17: Item lengths set by the user: knives 230, spoons and forks 200, teaspoons 150,
  chopsticks 250.
- 2026-10-17: Switched from four multi-compartment modules to one bin per compartment with
  magnets, at the user's suggestion. Each bin is now sized to its item rather than to a shared
  row depth. Without the 250 mm module limit, the bezel went back to 10 mm, and the chopsticks
  have a 260 mm bin printed diagonally instead of a channel split across two modules.
- 2026-10-17: Walls are 2 mm, down from 2.4, because every joint is now a double wall.
- 2026-10-17: Outside top edges have a 1 mm bevel to hide the joins.
- 2026-10-17: Made the layout symmetrical left to right: both outer columns are 60 mm inside,
  and the knife column matches the chopstick column's lengths.
- 2026-10-17: Added a 10 mm bezel to the back wall of the back row, matching the front.
- 2026-10-17: Magnets sit in the thick plastic behind the scoops, low on the wall, glued in from
  outside. They need no print pause and are invisible once the bins are together.

## Open questions

- Magnet size: 6 × 3 mm is assumed. Change `magnet_d` and `magnet_t` if you buy different ones,
  and the build checks that the holes still fit.
- The middle columns are 72 mm inside and the outer ones 60 mm. They could be tuned to how much
  of each item you have.

## Exports

| File | Format | Purpose |
| ---- | ------ | ------- |
| exports/cutlery-tray-<bin>.stl | STL | One per bin, ten in total, placed at the origin |
| exports/cutlery-tray.step | STEP | All bins, in drawer position |
