# 2D services coordination — clash avoidance before there is a 3D model, and the per-stage drawing specification for MEP

## Why in 2D, and why before S7

The S7 clash run finds what is left; it must not be the first time a 1000 × 500 supply duct and a DN150 chilled-water pair meet in a 900 mm ceiling zone. Big things are decided in 2D at S3 (which corridor carries what, at which band, with what depth) and fixed in 2D at S6 (every run has a size, a top / bottom RL and a declared crossing with the other systems). The rules below are deterministic and are checked by `scripts/coord_check.py` from `db/services-routes.json` and `db/crossings.json` per level; a level whose check has P0 / P1 findings does not get its M / E / H / F 100-series sheets issued, and a G4 gate report attaches the crossing reports.

The three sizes that cause most rework, in order: main ducts (supply, return, exhaust, smoke, kitchen), large water mains (CHW / HHW / CDW DN ≥ 100, fire mains DN ≥ 100, stormwater and sanitary DN ≥ 150, domestic risers), and cable trays / busways above 450 mm. Everything else fits around them.

## The ceiling zone is a budget

At S3 the ceiling-zone section (`ARC-CEIL-01`) fixes, per corridor type and per room type: structure soffit RL (beam or slab), the services zone, the ceiling build-up and the required clear height. The zone is written to `db/services-routes.json` as polygons with `structure_soffit_rl`, `ceiling_rl`, `hanger_allowance` (50 mm default), `ceiling_allowance` (30 mm) and the band order. The band order is the company rule and is only overridden per zone with a reason: **structure → fire sprinkler mains → ducts → pipes → trays**, top to bottom — sprinkler mains sit tight under the slab because they must not be blocked and rarely change; ducts next because they are the deepest and cannot be bent locally; pipes below ducts because they can be offset cheaply; trays lowest because they need top access for cable laying and are laid last. Gravity drains cut across the order because they must fall: they are routed first, in plan, along the corridor edge, and everything else crosses above them.

A zone's depth budget at any point is `sum of effective depths of the runs stacked there + vertical clearances (50 mm between each pair) + hanger allowance + ceiling allowance`. Effective depth includes insulation (duct 25–50 mm, pipe 25–38 mm each side). If the budget exceeds `structure_soffit_rl − ceiling_rl` the plan is wrong, not the section: move a run to another corridor, split a duct into two shallower ducts, drop the ceiling locally with a bulkhead drawn on the RCP, or raise the beam depth question with structure — all decided at S3 / S6, not by the S7 clash script.

## Corridor allocation rule (S3 services-zoning plans)

Each corridor and service corridor gets a plan (M/E/H-100 "services zoning", 1:100 per unique level) with lanes drawn in plan, like a road: duct lane(s) against one wall, wet lane (fire, CHW / HHW, domestic, drains) against the other wall, tray lane in the centre or under the duct lane at the low band, with the lane widths derived from the largest run each lane carries plus side clearances (100 mm between insulated surfaces; 300 mm on the access side of ducts with dampers, VAV boxes or attenuators, on the top of trays, and at flanges and valves). Crossings between lanes are allowed only at declared crossing points, which is what `db/crossings.json` registers. A corridor that cannot fit its lanes in width is split (services corridor + ceiling void), or the riser is relocated so the run is shorter; the decision is recorded and the zone polygon updated.

Seismic braces take space: a transverse or longitudinal brace on a duct or pipe is a 45° strut from the run to the structure, typically every 6–12 m per NZS 4219 tables or the tested system, and it occupies the lane beside the run at brace height. On NZ projects (and AU where AS 1170.4 Section 8 applies) the lane width includes a brace envelope on at least one side of every large run, the zone records `seismic: true`, and every brace crosses no other run — braces are declared as runs of family BRACE (same `system` as the run they brace, so they are checked against everything except their own run) in `db/services-routes.json` where they cross a lane, so `coord_check` sees them. Flexible connections at seismic joints are drawn on the zoning plan where a lane crosses the joint.

Risers follow the same logic vertically: each riser cassette lists its contents by size with access face and free area (`MECH-SPC-02`); a duct leaving a riser into a corridor must leave at the duct band with a straight length ≥ 1.5 × width before any elbow, and the riser position is chosen so that this straight run exists.

## The two files

`db/services-routes.json` (per level; metres; RLs are the bare element unless `rl_basis: "outside"`):

- zones: `id`, `polygon`, `structure_soffit_rl`, `ceiling_rl`, `hanger_allowance`, `ceiling_allowance`, `band_order`, `min_vertical_clearance` (0.05), `min_side_clearance` (0.10), `access_side_clearance` (0.30).
- runs: `id` (system tag + level + number), `system` (SA, RA, EA, SM, KE, CHW, HHW, CDW, CW, HW, FS, FH, SW, SAN, ELEC, COMMS…), `family` (DUCT, PIPE, TRAY, DRAIN, BUSWAY, CONDUIT, BRACE), `path` polyline, `width` / `depth` or `dn` / `od`, `insulation`, `top_rl` / `bottom_rl` (drains: `invert_start_rl` / `invert_end_rl`, `fall`), `sheet`, `needs_access` sides, `priority`. A run that changes level is two runs.

`db/crossings.json`: every planned crossing of two runs of different systems: `id`, the two `runs`, `at` [x, y], `resolution` in words ("pipe over duct"), `over_run` / `under_run`, `over_bottom_rl` / `under_top_rl`, `clearance`, `section_sheet` (the C-300 combined-services section that draws it), `status` RESOLVED / OPEN. Large-versus-large crossings (duct ≥ 600 wide or ≥ 400 deep; pipe DN ≥ 100; tray ≥ 450; any busway) must be registered with a section; small crossings are checked geometrically and need no register entry.

The generator writes both files from the DB when it lays out runs; the AI edits the DB (route, band, RL), never the report. Example files: `templates/services-routes.example.json`, `templates/crossings.example.json`.

## The check (`scripts/coord_check.py`)

```
python3 scripts/coord_check.py check --routes db/services-routes.json --crossings db/crossings.json --stage S6 \
        --out reports/crossings-L22.csv --svg reports/crossings-L22.svg
python3 scripts/coord_check.py demo <dir>      # builds a sample corridor and shows every finding type
```

Findings and severities: CLASH (vertical overlap at a crossing) and DEPTH BUDGET FAIL are P0; NEEDS SECTION (large × large crossing without a resolved register entry and section sheet), REGISTER MISMATCH (register RLs disagree with the run RLs by > 5 mm), TOO CLOSE (parallel runs closer than the side / access clearance while overlapping vertically), TIGHT (gap between 0 and the minimum clearance), envelope breach (run above the soffit allowance or below the ceiling allowance), FALL FAIL (a gravity drain that cannot fall) and a large run without RLs are P1; STALE register entries, band-order inversions and small runs without RLs at S6 are P2; everything else is INFO. At S3 small runs may be unplaced (INFO) but large runs must already have RLs. Exit code 1 on any P0 / P1. The CSV goes into the review packet (`reports/`) and the SVG is attached to the combined-services sheet as the crossing key plan.

Read the report as a to-do list for the DB: a CLASH means change the band or route of the lower-priority run (small pipes first, then large pipes, then ducts, never structure — the same order the S7 auto-router uses); NEEDS SECTION means draw the C-300 section for that point and register it; TOO CLOSE means widen the lane or stack the runs with the vertical clearance; DEPTH BUDGET FAIL goes back to the S3 zone decision.

## Per-stage MEP drawing specification (what each sheet must resolve before it is issued)

**S1 (space).** M/E/H-100 space-reservation plans 1:200 / 1:100 per unique level: riser positions with sizes, plant rooms with door and replacement route, louvre positions with separations (`MECH-SPC-03`), main service corridors marked with the intended lane widths, bulkhead-free zones (lobbies, restaurants) marked. No sizes yet, but the corridor widths and floor-to-floor heights that make the S3 zone possible are fixed here — the ceiling-zone section is drafted at S1 with assumed depths and frozen at S3.

**S3 (schematics + zoning).** One schematic per system at HY-0040 depth (every level: flow, pressure, size, valve sets; plant rooms; risers). Plus the services-zoning plans described above and the ceiling-zone sections per corridor / room type. The zoning plans carry: lane boundaries with widths; the largest run per lane with size and band; every planned lane crossing with a crossing id; riser exits with straight-length requirement; drains with fall direction; zones with depth budget and margin in a table on the sheet. `coord_check --stage S3` must report no P0 / P1 for large runs.

**S5 (equipment).** Equipment schedule updates the DB with vendor dimensions and connection positions; the zoning plan is rerun where a connection size changed (a chiller with DN200 connections instead of DN150 changes the plant-room lane).

**S6 (layouts).** Discipline 100-series per unique level, one system family per sheet (M-100 air, M-110 water, E-100 power, E-110 lighting, E-120 comms / security, H-100 water, H-110 drainage, F-100 sprinkler, F-110 hydrant, F-200 detection, F-210 EWIS / emergency lighting), each showing for every run: size, bottom-of-service RL (ducts and trays) or centreline RL (pipes) at every change and at every declared crossing, insulation type, flow / current / DN labels per the sheet checklist, damper / valve / access positions with access clearance drawn, hanger type reference. Crossings carry the crossing id and a section reference. The combined-services set (C-100 corridor plans 1:50 per corridor type, C-300 sections 1:20 every 8–12 m and at every large × large crossing, C-100 plant-room combined 1:50) is generated from the same DB and shows all systems together with the zone envelope, the band lines and the clearances dimensioned; every C-300 section is referenced from the crossings register. `coord_check --stage S6` must be clean (no P0 / P1) for the level before any of these sheets is issued; the report CSV and SVG are in the packet. Penetrations through structure come from the same runs (`STR-PEN-01`): the penetration plan is generated, not drawn.

**S7 (3D).** IFC built from the DB routes and RLs; the clash script then finds only what 2D could not represent (fittings, local drops, equipment connections, maintenance envelopes). A clash at S7 between two runs that were both on the S6 zoning plan is a process defect: record it as a lesson and add the case to `coord_check` or to the zone rules.

**S10 (production).** The drafting team models in Revit from the frozen IFC / DB and the C-sheets; a change of route or RL in Revit is a design change and is written back by stable run id (`references/db-schema.md`); the crossing register and the C-300 sections are regenerated and the check rerun before the sheet is reissued.

## Minimum content that every M / E / H / F layout sheet must carry for coordination (in addition to `references/sheet-content-checklists.md`)

- Zone envelope in the title block area: soffit RL, ceiling RL, available depth, band order, sheet-wide minimum clearances.
- Every run labelled with size and RL at both ends of each straight and at every crossing; crossing ids in a bubble; section references.
- Access clearances hatched at dampers, VAV / CAV boxes, valves, strainers, PRVs, tray pull points, busway tap-offs.
- Riser exit straight lengths dimensioned; duct aspect ratio noted where > 4:1.
- Drains: invert RLs at both ends, fall stated, the runs that cross above them referenced.
- A table: "CROSSINGS ON THIS SHEET" (id, other run, resolution, section) generated from the register, and "COORDINATION CHECK: coord_check <date>: P0 0 · P1 0 · P2 n" in the manifest — a badge without the CSV in the packet is not evidence.

## Defects

Sizing a duct on the schematic without a lane; a large × large crossing resolved "on site"; RLs only on the section but not on the plan; a clash found at S7 between two runs that had RLs at S6 and no register entry; a bulkhead added at S10 to solve an S3 zone budget; combined-services sections drawn by hand rather than generated from the same routes; a `coord_check` badge without the report in the packet.
