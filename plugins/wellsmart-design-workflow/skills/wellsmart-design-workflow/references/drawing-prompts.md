# Drawing prompts — how to make the AI draw more sheets, and draw them carefully

Two steps, always. Step 1: generate the sheet list for the stage and get it glanced at. Step 2: draw one sheet per response, run the extended QA overlay after each, report the counts, move on. Never ask for "the mechanical drawings"; ask for M-131. Every prompt below ends with the same annotation rules and the same output contract, so the model never has to remember them.

## Step 1 — the sheet-list prompt

```
Stage <S6>. Read db/levels.json, db/<discipline>.json for every level, and references/drawing-list.md.
Produce drawings/index.csv for the <MECH> discipline: one sheet per unique level type per family
(air layouts M-101…, pipework layouts M-121…, plant rooms 1:50 M-141…), then schedules, details,
sections and schematics per drawing-list.md. For each sheet estimate the annotated item count from
the DB (terminals + equipment + runs + tags on that level and system). Any sheet above the density
threshold (60 items on A3, 150 on A1) is pre-split by system, then by grid zone (west/east with a key
plan), then by scale — write the split as separate rows (M-131A, M-131B) with split_of set.
Every plant room is its own 1:50 sheet. Do not merge families to save sheets.
Output the CSV only, then three lines: total sheets, sheets split, sheets you are unsure about and why.
```

The PD reads the totals and the "unsure" lines. Then step 2.

## Step 2 — the per-sheet prompt skeleton

Every sheet prompt has nine parts. Fill all nine; leave none to the model's memory.

```
Draw sheet <NUMBER> — <TITLE>, <LEVEL(S)>, <SCALE> @ <SIZE>.
1 SOURCE: db/<file>.json filtered to <level id> and <system(s)>; grids from db/grids.json; base plan
  from db/walls.json + openings.json as grey halftone (0.18 mm, #B3B3B3). Read nothing else.
2 SHOW: <the content list for this sheet type — copy from references/sheet-content-checklists.md
  section <n>; list the items explicitly>.
3 TAGS AND NUMBERS: every equipment item with its tag from the DB; every run label with size and flow
  repeated every 150 paper mm; every design value with its calc ID; no number without a calc ID.
  On M / E / H / F layouts also: the RL (bottom of duct / tray, pipe centreline) at every change and at
  every crossing, the crossing id bubble with its C-300 section reference, the zone envelope in the
  title area, and the CROSSINGS ON THIS SHEET table from db/crossings.json; run
  `python3 scripts/coord_check.py check --routes db/services-routes.json --crossings db/crossings.json
  --stage <S>` for the level first and quote its P0 / P1 / P2 counts — a level with P0 / P1 is not drawn.
4 SHEET FURNITURE: key design-data box (<the 3–6 numbers that drive this sheet> with calc IDs),
  assumptions box (ASSUMED — TBC lines from db/assumptions.json for this level/system), legend with a
  swatch for every colour and symbol used, north point, scale bar, drawing index cross-references
  (SEE <sheet> for …), title block with date only (no revision label).
5 ANNOTATIONS — DECLARE, DO NOT PLACE: list every label as text → target tag → side and every
  dimension as a → b → band → side; lay them out with scripts/annotate.py (generated sheet) or, on a
  chat-drawn sheet, write the layout in the LAYOUT PLAN comment: column x per side, labels sorted by
  target y with slot y values, shoulder and anchor points, and a written intersection check of every
  leader against every other leader, dimension line and solid object. Unreachable targets become
  keyed notes. Labels in one aligned column per side; dimensions in bands on the other sides; leaders
  ≤ 45 mm (A3) / 60 mm (A1); text ≥ 2.5 mm, ≥ 1 mm clear of everything; dimensions and notes black,
  run labels and tags in their service colour; classes leader/label/dim/ext/outline on the elements;
  one grid, one north, one datum. Full rules: references/annotation-rules.md.
6 DENSITY: if the view exceeds the threshold (60 items A3 / 150 items A1) with these rules, STOP,
  propose the split (<NUMBER>A / <NUMBER>B by <zone or system>) with a one-line reason, and draw the
  first part only.
7 CROSS-CHECKS before output: <the cross-check lines for this sheet type from
  sheet-content-checklists.md §11> — list each as PASS/FAIL in the response.
8 QA: run `python3 scripts/annotate.py check <sheet>` (or read the embedded overlay's counts):
  outside border, text overlap, outside sheet, palette, leader crossings, leader through object,
  leader over dimension, text over lines, density, label columns — report every count; fix every
  listed item and re-run until all are zero before the sheet is issued.
9 OUTPUT: one complete self-contained HTML sheet (inline SVG, paper mm, no external resources,
  QA script included) with the manifest JSON in a <script type="application/json" id="manifest">
  block; then the QA counts; then the cross-check PASS/FAIL list; nothing else.
```

The manifest (read by the reviewer instead of the full SVG):

```json
{"sheet": "M-131", "title": "...", "stage": "S6", "date": "2026-09-14", "scale": "1:50", "size": "A1",
 "levels": ["L22"], "systems": ["SA", "RA"], "source": ["db/mech.json#L22"],
 "tags": ["AHU-22-01", "AHU-22-02", "FD-22-01"…], "run_labels": ["SA 1200×600 8500 L/s"…],
 "calc_ids": ["M-041", "M-042"], "assumptions": ["ASSUMED — TBC: …"], "cross_refs": ["M-604", "C-112"],
 "item_count": 138, "qa": {"outside_border": 0, "text_overlap": 0, "outside_sheet": 0, "palette": 0,
 "leader_crossings": 0, "text_over_lines": 0, "density": "OK"}, "cross_checks": {"...": "PASS"}}
```

## Per-sheet-type SHOW lists (part 2 of the skeleton)

Copy the matching block into part 2. Each names the checklist section that carries the full item list; the lines here are the items most often missed.

**A GA plan (1:100).** Grids and grid dimensions; wall types tagged; every door and window tagged to the schedule; room names, numbers and areas; FFL and SSL per zone; set-downs; stairs with riser count and direction; lifts with car numbers; risers named by service; fire-rated walls in red with FRL tags; travel-distance arrows to exits with the governing distances and their calc IDs; section and detail marks; north. (Checklist §1.)

**A enlarged wet area / kitchen / BoH (1:50).** Fixture setout from finished faces (state which); waterproofing extent hatch and membrane upturns; floor falls with arrows and grades to every floor waste; hob and set-down dimensions; wall types and tiles; door swings; grab-rail zones on accessible rooms; penetrations. (§1, §7.)

**I room-type set (plan 1:20 + four elevations).** Furniture and joinery with JN- and FF&E numbers; finishes hexagon tags FL-/WF-/CL-/PT-; power, data, lighting and switch positions coordinated with E sheets and listed by height; wall-mounted items with mounting heights; ceiling heights; skirting, cornice, bulkheads; mirror, TV, curtain and pelmet setouts; DDA variants where applicable. (§2.)

**I / A RCP (1:50).** Ceiling types and heights per zone; bulkheads with dimensions; every luminaire from E-12x with tag and circuit; diffusers and grilles from M-10x with size and airflow; sprinkler heads from F-10x; detectors, speakers, exit signs; access panels with sizes at every valve, damper and FCU; setout lines; the ceiling-zone stacking rule stated. (§2.)

**S framing plan (1:100).** Member tags (B1, C1, W1, S1) with sizes and levels; slab thicknesses and set-downs; steps, upstands, thickenings; openings and trimming; transfer elements; connection references; load diagrams referenced; column schedule sheet reference; concrete grade and cover per element on the sheet. (§3.)

**S penetration plan (1:100).** Every service penetration through slabs, walls and beams from the coordinated DB with size, tag, discipline colour and the fire-stopping detail reference; exclusion zones; sleeves cast-in vs cored; the check that no penetration crosses a transfer element. (§3, §11.)

**M air layout (1:100).** Double-line ducts with size, airflow and insulation type per run; flow arrows; fire and smoke dampers with tags and access; VAV / VCD / attenuators; diffusers, grilles, louvres with size and airflow; FCUs / AHUs / fans with tags and duties; riser openings with sizes; condensate direction; fire-mode notes; OA intake and EA discharge positions with separation distances. (§4.)

**M pipework layout (1:100).** CHWS/CHWR, HHWS/HHWR, CDW, refrigerant, condensate single-line with DN, flow and insulation; balancing and isolation valves; drains and vents at high / low points; expansion; supports and anchor points on risers; FCU connections; refrigerant charge zones vs room volumes with the check result. (§4.)

**M / E / H / F plant room (1:50).** Every item with tag, dimensions, weight and its maintenance clearance drawn; access and lifting routes; door sizes; plinths; drains, bunds, floor wastes; ventilation; acoustic treatment; combined with the other disciplines on the C sheet, but this sheet shows the discipline's own items fully. (§4–7, §8.)

**E power (1:100).** Boards with tags and locations; every outlet, isolator and mechanical / hydraulic / fire connection with circuit reference and load; cable trays and risers with sizes; sub-mains routes with cable sizes; EV charging provision; metering; earthing bonds in wet areas. (§5.)

**E lighting (1:100).** Luminaires tagged to the luminaire schedule with circuit and switching zone; controls (sensors, dimming, scenes); emergency and exit luminaires on the F-22x sheet, cross-referenced; external lighting; the lux level per zone with its calc ID. (§5.)

**E DB schedule + board elevation (one board per sheet).** Board elevation (chassis layout) and the schedule list the same devices in the same order; per way: circuit number, description, protective device type and rating, curve, RCD, poles, phase, cable size and type, length, voltage drop, load; incoming supply with size, direction and origin; every outgoing cable with direction arrow and destination; busbar rating; fault level; form of separation; spare ways; metering. (§5 — the "alignment rule" is the most frequent past defect: check it explicitly.)

**E SLD (NTS).** From the supply authority point to every board: every switch rating and type, cable size / type / length / installation method, fault level and voltage drop per level, metering, generator and changeover, UPS, essential and non-essential sections, earthing. (§5, depth per drawing-standards.md.)

**H water layout (1:100).** CW / HW / HWR / gas single-line with DN, flow and material; isolation valves; PRVs with settings; backflow devices with hazard rating; meters; TMVs; insulation; pipe supports at risers; connections to every fixture and every mechanical / fire / kitchen item; the pressure at the level from H-60x. (§6.)

**H drainage layout (1:100).** Every fixture connected; pipe sizes and gradients with fall arrows; stacks tagged; **floor waste gullies in every wet room** with the charging fixture or trap primer named; **tundishes** under every relief valve, TMV and condensate discharge; **ORG** location and levels on the ground sheet; inspection openings; vents (stack, relief, group) with sizes; trade waste and grease arrestor; pump-outs; fire collars at every penetration with the detail reference; jump-ups; the drainage schematic reference. (§6 — floor traps and tundishes are the most frequent past miss: list them on the sheet.)

**H stormwater (1:100 / 1:200).** Catchments with areas; gutters, sumps, rainheads, overflows; downpipe sizes; pits with grate and invert levels; OSD with volume and orifice; subsoil drainage; pumped systems; connection to the street with IL. (§6.)

**Any system schematic / riser (NTS, HY-0040 depth).** Every level with RL; the pressure / static / flow at every level; pipe or duct size per segment; every branch to every user; every meter, valve set, PRV, pump, tank tagged with duty and calc ID; where the water / air / power goes; controls in one line; notes with mains conditions; the assumptions box. (drawing-standards.md.)

**F sprinkler layout (1:100).** Head positions with type, K-factor, temperature and coverage; pipe sizes; valve set and flow switch; hazard class per zone; obstructions and clearance notes; concealed-space heads; the hydraulic most-disadvantaged point; head count per zone in the key data box. (§7.)

**F hydrant / hose reel layout (1:100).** Hydrants and hose reels with coverage arcs at hose length; booster and block plan reference; pipe sizes; valves; pressures at the level; signage. (§7.)

**F detection (1:100).** Detector types and spacing; MCPs; sounders / strobes; interfaces (doors, dampers, lifts); zone boundaries; loop numbers; FIP location and mimic reference; cable classification. (§7.)

**F EWIS / emergency lighting (1:100).** Speakers with tap settings; WIPs; exit and emergency luminaires with spacing and the illuminance check; evacuation zone; interfaces. (§7.)

**C combined corridor (1:50) and section (1:20).** All services in their colours stacked in the ceiling zone with heights (underside of slab, top of ceiling, each service's soffit level); cassette or module boundaries; access panel positions; the crossing points; fire and smoke dampers; the clash script result on the sheet. (§8.)

**Detail (1:10 / 1:5).** Components named with material, size, fixing and finish; sequence of installation where it matters; tolerances; test report / certification reference; the library detail ID if from `details/`; "NON-TYPICAL — HUMAN BUILDABILITY REVIEW" banner if not. (§1–§7 detail lines, and the details library.)

**Schedule sheet.** One family per sheet; every row from the DB with tag, description, duty / rating, size, weight, electrical load, noise, supplier SKU and certification status, location, calc ID; totals; no blank cells — "N/A" or "TBC (why)". (§10.)

## The split response protocol

When part 6 triggers, the model answers exactly: `SPLIT PROPOSED: <NUMBER> → <NUMBER>A (<zone/system>, ≈ n items) + <NUMBER>B (<zone/system>, ≈ n items). Reason: <one line>. Drawing <NUMBER>A now.` Then the sheet. The operator adds the B row to the index and prompts for it; the generator updates `drawings/index.csv`.

## QA report format (after every sheet)

```
QA <NUMBER>: outside_border 0 · text_overlap 0 · outside_sheet 0 · palette 0 · leader_crossings 0 ·
text_over_lines 0 · density 138/150 OK
CROSS-CHECKS: <name> PASS · <name> PASS · <name> FAIL (<what>) …
```

A sheet with any non-zero QA count or any FAIL is redrawn in the same response cycle before the next sheet is started. Never issue a sheet with a red badge.

## Reviewer drawing prompt (second model family; this is what pass 3 of `scripts/peer_review.py` asks)

```
You are reviewing sheet <NUMBER> from the project <code>. Read the manifest JSON first; open the full
SVG only for the checks that need geometry. Check, and report each as PASS / FAIL with the item:
1 every tag in the manifest exists in db/<file>.json for that level, and every DB item on that level
  and system appears on the sheet (list missing tags);
2 every design value on the sheet has a calc ID that exists in calcs/calc-register.csv and the value
  matches the register;
3 content completeness against references/sheet-content-checklists.md section <n> (list absent items);
4 the three hard drawing rules: no leader crossings, no text over lines or text, density under the
  threshold — count them yourself from the SVG; do not trust the badge;
5 cross-checks in §11 that involve another sheet (e.g. luminaires on the RCP = luminaires on E-12x;
  DB schedule devices = board elevation devices; floor wastes on H-12x = wet rooms on A-1xx);
6 anything a fitter could not build from this sheet without asking.
Severity: blocker (wrong or missing design value, missing fixture, rule 4 failure), major (missing
tag or cross-reference), minor (labels, wording), suggestion. Output the issue list in the review-round
issue schema; no prose.
```

## Common failure modes and the prompt line that prevents each

| Failure seen before | Line to keep in the prompt |
|---|---|
| Floor traps / tundishes / ORG missing on drainage sheets | "List every wet room from rooms.json and place an FWG in each; tundish under every relief / TMV / condensate; ORG on the ground sheet with levels." |
| DB schedule and board elevation disagree; no cable directions or sizes | "Generate the elevation and the schedule from the same circuits[] array in one pass; every cable carries size and a direction arrow with origin / destination." |
| Leaders crossing, labels stacked, leaders through other objects, labels on lines | Part 5: annotations declared and laid out by annotate.py; the checker loop in part 8; keyed notes for unreachable targets. |
| Two levels or two systems on one sheet | "One level, one system family, one scale — refuse otherwise." |
| Numbers typed from memory | "No number without a calc ID; unknown → ASSUMED — TBC in the assumptions box." |
| Plant room squeezed into a floor plan | "Plant rooms are their own 1:50 sheets; on the floor plan show the room outline and SEE M-14x." |
| Sheet 'looks complete' but a DB item is missing | Reviewer check 1 (tag reconciliation against the DB) and `check_sheets.py`. |
