# Drawing standards and the depth benchmark

Drawings are generated from the design database, never hand-drawn: 2D as DXF (ezdxf) and as self-contained HTML/SVG sheets (the company generator, gen.py pattern, with the built-in QA overlay); 3D as IFC (IfcOpenShell); production drawings in Revit at S10 (revit-mcp). A sheet whose numbers are typed in by hand is a defect, because it can drift from the DB.

## Numbering and sheets

- Drawing numbers: discipline letter A / S / M / E / H / F / I + series — 000 general and legends, 100 plans, 200 elevations, 300 sections, 400 details, 500 schedules, 600 schematics (e.g. `M-101`, `H-604`, `E-601`). Preliminary revisions P1, P2…; issued A, B, C… — but while a document is in draft, date only, no revision label, unless the PD asks.
- Sheet furniture and layout follow the company drafting specification (AS 1100 series lineweights and line types, colour-coded services palette, A3 default, A1 on request, title block, legend, north point, scale bars). The HTML generator enforces it; DXF exports mirror the same layer and colour standard.
- Text: English uppercase; Chinese only as a second line on sheet and view titles for internal sets.
- Every sheet carries: a key design-data box (the numbers that drive this sheet), an assumptions box (`ASSUMED — TBC` lines), and calc IDs beside every design value. Full calculations live in the calc register, not on the sheet.
- One grid, one north, one level datum for all disciplines. Services and ID sheets show the architectural plan as grey halftone and dimension only discipline-critical setout.

## Scales

Plans, elevations, services layouts and structural GA 1:100; sections and plant rooms 1:50; ID plans 1:50; joinery 1:20, details 1:10 / 1:5; site 1:200 / 1:500; schematics NTS.

## The depth benchmark: HY-0040

WSP's 372 Pitt Street cold-water schematic (HY-0040, A1, full-height riser) is the minimum depth for every system schematic. It shows: every level with RL; static pressure at every level; pipe size per segment with GRAV. / PRESS.; a Ø20 branch to every room; every user meter tagged (CW-M1…M26); pumps and tanks tagged with duties in the equipment schedule sheet; PRV zones; where the water goes (fire hose reels, fire-tank top-up, rainwater-tank top-up, hot-water plants, kitchens, mechanical equipment); the notes that state mains pressure and the required pump outlet pressure.

We add, on the sheet: design flow and its basis (fixture-unit summation, diversity); velocity and pressure drop per segment; residual pressure at the most disadvantaged point; pump duty point with calc ID; tank volume and hours of storage; a one-line control description; backflow prevention and isolation valves; Legionella / hot-water temperature regime; the assumptions box.

The same depth applies to every system:
- CHW / HHW: flow per level, ΔT, pipe size, balancing valves, differential bypass, plant-room heat-exchanger breaks on tall buildings.
- Supply / exhaust air: airflow per level, duct size, velocity, static pressure, fire-damper positions, intake / discharge positions.
- Electrical SLD: every switch rating, cable specification, fault level, voltage drop at each level, metering.
- Comms backbone: fibre counts, distributor locations.
- Fire: hydrant and sprinkler flow / pressure per level, valve sets, pumps and tanks with duties, booster.
- Drainage: stack sizes, fixture units, venting method, pump stations.
- Stormwater: catchments, downpipe sizes, overflow, OSD.
- Gas: loads, pipe sizes, meter.

## Drawing set per stage

- S1: concept plans per level, site plan, massing views; DA set if required (site plan, plans, elevations, sections, shadow diagrams, materials board).
- S2: ID layouts 1:50, style boards, FF&E schedule.
- S3: architectural GA set; structural framing plans; one schematic per MEP system; ceiling-zone section.
- S6: discipline sets (100/300/400/500/600 series), SLDs, P&IDs, control schematics, combined-services sections, joinery elevations, typical details from the details library, non-typical details drafted for human buildability review, penetration schedule.
- S9: the same sets issued as PDF + DWG.
- S10: Revit production set; details from the DXF library imported as drafting views.

Counts per level, per checkpoint, numbering families and the split rule are in `drawing-list.md`; per-sheet prompts in `drawing-prompts.md`; what each sheet type must contain in `sheet-content-checklists.md`.

## Annotations are declared, then laid out

Leaders, labels and dimensions are never placed by hand: the generator (or the model, on a chat-drawn sheet, in its LAYOUT PLAN comment) declares `label(text, target, side)` and `dim(a, b, ref, band, side)`; `scripts/annotate.py` lays them out — one aligned column per side, label order = target order, leaders anchored on the outline and routed through nothing but the target, dimensions in bands on the sides that carry no labels, keyed notes when a target is unreachable. The twelve rules and the defect catalogue are in `annotation-rules.md`. SVG classes `leader / label / dim / ext / dimtext / outline / bubble` let the checker and the overlay see the roles.

## Three hard drawing-quality rules

1. No leader crossings: no leader may cross another leader or a dimension line; a label goes in the nearest clear zone, or the sheet is split.
2. No text over lines, no text over text: any stroke through a text box fails (a halo does not fix it); text-on-text overlap above 0.3 mm fails; text keeps ≥ 1 mm clear of linework.
3. No crowding: a view over the density threshold (≈ 60 annotated items on A3, ≈ 150 on A1) is split before drawing — by system family, then by grid zone with a key plan, then by scale. One level, one system family, one scale per sheet; plant rooms on their own 1:50 sheets.

## QA overlay (extended)

Every generated HTML sheet includes the QA script. The four original checks — text outside the border, overlapping text, elements outside the sheet, colours outside the palette — plus five: leader crossing a leader or a dimension line, leader through a solid object other than its target, linework through text, the density count against the threshold, and label-column alignment. The canonical script is `templates/qa-overlay.js` (embed it unchanged as the only script in the sheet); `scripts/annotate.py check <sheet.html>` runs the same checks without a browser, for the draw → check → fix loop in Claude Code. Badge "QA: PASS" or a red count; the counts are also written into the sheet manifest JSON. A sheet is not issued with issues. The same idea extends to DB consistency, model checks and clash: every output ships with its check result.

## Sheet manifest

Each sheet HTML carries `<script type="application/json" id="manifest">` (sheet, title, stage, date, scale, size, levels, systems, DB source, tags, run labels, calc IDs, assumptions, cross-references, item count, QA counts, cross-check results) and the same content as a visible text block under the drawing. Reviewers and the project-book search read the manifest; the full SVG is opened only when geometry matters.
