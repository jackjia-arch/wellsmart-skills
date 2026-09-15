# Drawing list — how many sheets, per level, per checkpoint, at what scale

Principle: never economise on sheets. Tokens are cheap; a crowded sheet costs a review round, a missed item and sometimes a site error. One thing per sheet — one level, one system family, one scale. Plant rooms always on their own sheet at 1:50; risers and shafts at 1:20; anything a fitter has to build from at 1:20 or larger. When a view is dense, split it (by grid zone, by system, or by enlarging the scale) rather than shrinking text or stacking labels. The sheet list is generated from the DB before any sheet is drawn, and the PD glances at the list, not at 600 sheets.

Two documents come out of this file and they answer different questions. The **sheet list** (`drawings/index.csv`) and the count tables below answer "how many sheets do we plan to draw"; they are planning estimates. The **level–sheet–revision matrix** (`drawings/level-sheet-matrix.csv`) answers "which sheet, at which revision, applies to this physical level, and how does this level differ from the typical"; it, checked against the actual graphics, is the completeness evidence. Per-stage sheet specifications that carry the 2D services-coordination content (what a coordination plan or section must show at S3 / S6, and the route and crossing data behind it) are in `references/services-coordination-2d.md` (being written by others).

## Counting rule: unique level types × sheet families

Draw one sheet per **unique level type** during design (S1–S9); the title names every level it applies to ("TYPICAL GUEST LEVELS 6–56"); at S10 the Revit set has one sheet per physical level (the drafting team's job, manual). `L` below is the number of unique level types:

| Project | Levels | Unique level types L | Sheet size for plans |
|---|---|---|---|
| Villa / house | G, L1, roof | 3 | A3 (1:100; 1:50 where the plan is under 12 m) |
| Low-rise (3–8 storeys, motel, walk-up) | basement?, G, typical, top, roof | 4–6 | A3 1:100 (A1 if the plate exceeds 30 m) |
| Tower (372 Pitt profile: B2–L60) | B2, B1, G, L1, L2, L3 plant, L4, L5 first guest, L6–56 typical, L57 top guest, L58 sky lounge, L59–60 plant, roof, + transfer level | ≈ 14 | A1 1:100 (a 1:100 A1 holds ≈ 75 m of plan) |

If two "typical" floors differ (a transfer level, a refuge floor, a change of riser), they are two level types. "Differ" is judged per system family, not on the architectural plan alone: two levels with identical architectural plans are still two level types for the family in which they differ — a different pressure zone (H water), different pipe sizes on the riser take-offs (H / M), different electrical circuits or board (E), different reinforcement, loads or transfer (S), a different fire compartment boundary (A / F) or different penetrations (S / A). Adding a level type adds one sheet to every per-level family in which it differs — the generator does it from the DB; the operator does not decide it.

## Numbering

`<DISC>-<NNN>` with the series digit as in `drawing-standards.md` (0 general, 1 plans, 2 elevations, 3 sections, 4 details, 5 schedules, 6 schematics), plus a family block inside the 100 series so each layout family runs in level order. Block size = 20 on towers, 10 on low-rise, 5 on villas; the generator assigns blocks and writes the drawing index (`drawings/index.csv`), which is the truth for numbers. Split views take a letter suffix (M-131A west, M-131B east). Combined-services sheets use `C-`; specialist streams use `Q-` (façade), `N-` (acoustic), `T-` (traffic / civil), `X-` (thermal / ESD), `D-` (DDA / access), `K-` (construction planning and temporary works).

Families in the 100 series (tower block example, L = 14, block 20):

| Family | Block | Content | Scale |
|---|---|---|---|
| A-101… | A-100 | GA plans per level type; roof | 1:100 A1 |
| A-121… | A-120 | enlarged plans: core, lobby zones, wet areas, kitchens, BoH | 1:50 |
| A-141… | A-140 | wall-type / FRL / acoustic-rating plans per level type | 1:100 |
| A-161… | A-160 | waterproofing and set-down plans; fire-stopping / penetration plans per level type (owned by ARCH, coordinated with STR) | 1:100 |
| I-101… | I-100 | ID plans: room types 1:20 sets, public areas 1:50 | 1:50 / 1:20 |
| I-121… | I-120 | RCP per level type (guest levels by ID, BoH by ARCH) | 1:50 (A1) or 1:100 with enlargements |
| I-141… | I-140 | finishes setout per level type | 1:50 |
| S-101… | S-100 | framing / GA plans per level type; foundations; transfer | 1:100 |
| S-121… | S-120 | slab and wall reinforcement plans (typical at S6, all at S10) | 1:100 |
| S-141… | S-140 | structural penetration plans per level type (from the coordinated DB) | 1:100 |
| M-101… | M-100 | air layouts per level type (SA / RA / OA / EA, fire dampers, diffusers) | 1:100 |
| M-121… | M-120 | pipework layouts per level type (CHW / HHW / CDW / refrigerant / condensate) | 1:100 |
| M-141… | M-140 | plant rooms and plant levels, each room its own sheet | 1:50 |
| E-101… | E-100 | power per level type (boards, circuits, outlets, mechanical connections) | 1:100 |
| E-121… | E-120 | lighting per level type (luminaires, switching, controls) | 1:100 |
| E-141… | E-140 | comms / security / AV / BMS network per level type | 1:100 |
| E-161… | E-160 | switchrooms, substation, comms rooms, generator | 1:50 |
| H-101… | H-100 | water services per level type (CW / HW / HWR / gas) | 1:100 |
| H-121… | H-120 | sanitary drainage per level type (SAN, trade waste, floor wastes, vents) | 1:100 |
| H-141… | H-140 | stormwater: roof, podium, basement, site | 1:100 / 1:200 |
| H-161… | H-160 | pump rooms, tank rooms, hot-water plant, gas meter room | 1:50 |
| F-101… | F-100 | sprinklers per level type | 1:100 |
| F-121… | F-120 | hydrants and hose reels per level type | 1:100 |
| F-141… | F-140 | fire pump rooms, tanks, booster, sprinkler valve rooms | 1:50 |
| F-201… | F-200 | detection and alarm per level type | 1:100 |
| F-221… | F-220 | EWIS, emergency and exit lighting per level type | 1:100 |
| C-101… | C-100 | combined-services coordination: corridors per corridor type, plant rooms, BoH | 1:50 |
| C-301… | C-300 | combined-services sections at the tight points (8–12 on a tower) | 1:20 |

Villa and low-rise projects use the same families; families that have nothing on them (no sprinklers on a villa) are simply absent from the index, never merged into another sheet "to save a sheet". Merging is allowed in exactly one case: a villa level whose water and drainage together carry fewer than 25 annotated items may share one H sheet — and the title says both.

## Per-level minimum set at S6 (detailed design)

What every unique level type gets. ✓ = one sheet; ✓✓ = usually split in two on a tower plate; — = not applicable; (D) = discipline sheet drawn on the ID base. Add the split rule on top of this: any sheet over the density threshold becomes two.

| Family | Basement / car park | Ground (lobby, retail, dock) | Podium (lounge, hydro, restaurant, BoH) | Plant level | Typical guest level | Top guest / sky lounge | Roof |
|---|---|---|---|---|---|---|---|
| A GA plan | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| A enlarged 1:50 | core, dock | lobby, core, retail, dock, waste | per venue (2–4) | — | core + 2 room types | venue + core | — |
| A wall-type / FRL | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| A waterproofing / set-downs | ✓ (pits, ramps) | ✓ | ✓ (hydro, kitchens) | ✓ (plant) | ✓ (bathrooms) | ✓ | ✓ |
| A fire-stopping / penetration plan | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| I plan / finishes | — | ✓ | ✓✓ | — | ✓ (room-type sets separate) | ✓ | — |
| I RCP | — (ARCH RCP) | ✓ | ✓✓ | — | ✓ | ✓ | — |
| S framing | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| S reinforcement (typical) | ✓ | ✓ | — | — | ✓ | — | — |
| S penetration plan | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| M air | ✓ (car-park exhaust, supply) | ✓ | ✓✓ | plant rooms 1:50 instead | ✓ | ✓ | ✓ (fans, intakes) |
| M pipework | ✓ | ✓ | ✓ | plant rooms 1:50 instead | ✓ | ✓ | ✓ (cooling towers / condensers) |
| E power | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ |
| E lighting | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ (external) |
| E comms / security | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| H water + gas | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (tanks, HW plant if roof-mounted) |
| H drainage | ✓ (pump-out, ORG, pits) | ✓ | ✓✓ (kitchen trade waste) | ✓ | ✓ | ✓ | — |
| H stormwater | ✓ | ✓ (site, podium) | ✓ (terraces) | — | — (balconies if any) | ✓ | ✓ |
| F sprinklers | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ if plant enclosed |
| F hydrants / hose reels | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F detection | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F EWIS / EL / exit | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| C combined corridor 1:50 | dock / BoH corridor | BoH corridor | ✓ | — | ✓ (per corridor type) | ✓ | — |
| Sheets per level type (before splits) | ≈ 22 | ≈ 24 | ≈ 26–30 | ≈ 16 + plant rooms | ≈ 22 | ≈ 22 | ≈ 14 |

Plant rooms at 1:50, each on its own sheet, for every discipline that has content in the room: e.g. the L3 plant level on a tower produces M (AHU room, fan rooms), E (main switchroom, generator), H (pump room, HW plant, gas), F (fire pump room, tank) and C (combined) sheets — typically 12–20 sheets for one plant level.

## Per-checkpoint totals

Counts for the tower profile (L ≈ 14) and the villa profile (L ≈ 3). Minimums; the generator adds splits.

| Checkpoint | Content | Tower | Villa |
|---|---|---|---|
| S1 concept (G1) | A-000 cover, index, area schedule (3 / 2) · A-100 concept plans per level type + roof (L+1) · A-200/300 elevations, sections, massing (10 / 6) · F-100 fire strategy plans per level type (L) · M/E/H-100 MEP space reservation per level type + S-100 scheme plans (L+6 / 5) · DA pack if needed (8 / 4) | ≈ 70 | ≈ 25 |
| S2 interiors (G2) | I-100 room-type plan + four elevations per type (types × 3) · public areas 1:50 (16 / 4) · RCP concept per level type + finishes zoning (2L / 6) · style boards, FF&E schedule, DDA rooms and toilets 1:50 (12 / 6) | ≈ 75 | ≈ 25 |
| S3 freeze + schematics (G3) | A GA plans per level type, elevations, sections, roof (L+12 / 10) · core and stairs 1:50, ceiling-zone sections 1:20, wall types, door and window schedules (16 / 8) · S framing per level type, foundations, sections, member schedules, load diagrams (L+10 / 8) · M/E/H/F-600 schematics one per system: SA/RA/OA/EA, CHW/HHW/CDW, stair pressurisation, SLD, comms, BMS, CW, HW, SAN, SW, gas, wet fire, dry-fire block, pump P&IDs (36 / 16) · services zoning per level type: one MECH+HYD+FIRE, one ELEC+comms (2L / 6) + F-100 final strategy · thermal loads report figures, façade options, wind table, typical wall section 1:20 (8 / 4) | ≈ 140 | ≈ 50 |
| S6 detailed design (G4) | per-level set above × L, plus: A enlarged / details / façade / schedules (L+90 / 40) · ID full room-type sets, joinery 1:20 and 1:5, RCP 1:50, finishes, FF&E (90 / 30) · S sections, member schedules, typical details, core / transfer (2L+50 / 20) · M plant rooms 1:50, corridor sections, details, schedules, controls (2L+46 / 16) · E switchrooms 1:50, SLDs, DB schedules (one sheet per board), tray sections, lightning, luminaire schedule (3L+40 / 18) · H pump rooms 1:50, riser details 1:20, P&IDs, fixture schedules (2L+30 / 14) · F wet: pump rooms, tanks, hydraulic calc sheets (2L+16 / 8) · F dry: FIP block, cause and effect (2L+8 / 8) · C combined corridors 1:50, sections 1:20, plant combined (24 / 6) · specialist D / N / T / X / Q (40 / 16) · K construction planning and temporary works (10 / 4) · report figures (6 / 3) | ≈ 650 | ≈ 180 |
| S7 (G5) | no sheets — model viewpoints and the penetration schedule inside the clash report | — | — |
| S9 sign-off (G7) | full S6 set + cover, transmittal, drawing index; PDF printed from HTML + DWG | ≈ 700 | ≈ 200 |
| S10 LOD 400 + BQ | Revit production set by the drafting team, one sheet per physical level, reinforcement, more details | ≈ 900 | ≈ 250 |

**Counts are planning estimates, not completeness proof.** The totals (tower S1 ≈ 70, S2 ≈ 75, S3 ≈ 140, S6 ≈ 650; villa S1 ≈ 25, S2 ≈ 25, S3 ≈ 50, S6 ≈ 180) are "one sheet per unique level type" multiplied out and scaled by L; applicability and content decide completeness, and density adds sheets. Treating the count table as completeness evidence is a listed defect. Completeness is shown by the level–sheet–revision matrix below, with every listed sheet's actual graphics checked against its content checklist (`references/sheet-content-checklists.md`); the sheet manifest JSON and the QA badge are an index and a check summary, never the evidence that the sheet is complete or correct.

## Level → sheet / revision → difference matrix

`drawings/level-sheet-matrix.csv` maps every physical level of the building to the sheet and revision that applies to it, per sheet family, and records how that level differs from the typical level type it would otherwise be grouped with — which is the reason it has its own sheet. Columns:

`level, family, sheet_no, revision, differs_from_typical, notes`

- `level` is the physical level id from `db/levels.json` (B2, B1, G, L1 … roof), one row per level per applicable family — a row for L23 / M air, another for L23 / M pipework, another for L23 / E power, and so on. A level with no content in a family (no sprinklers on a villa level) has no row for that family, and the absence is explained once in the drawing index, not silently.
- `family` is the sheet family block from the numbering table above (A GA, A wall-type / FRL, S framing, S penetration, M air, M pipework, E power, E lighting, E comms, H water, H drainage, H stormwater, F sprinklers, F hydrants, F detection, F EWIS, C combined, I plan, I RCP …).
- `sheet_no` is the sheet that applies to this level, with any split suffix (M-131A). Several physical levels may point at the same typical sheet; the sheet title still names every level it covers.
- `revision` is the Project Book `revision_id` of that sheet (`references/project-knowledge-base.md`) — a catalogue fact, not a label printed on a drawing that is still in draft (date only on the sheet itself). The matrix is regenerated whenever a sheet is revised, so the matrix of a frozen package names the exact revisions the package contains.
- `differs_from_typical` is one or more of a fixed vocabulary: `pressure zone`, `pipe sizes`, `circuits`, `reinforcement`, `loads`, `compartments`, `penetrations`, or `none`. Any value other than `none` in a family means this level cannot share that family's typical sheet: it gets its own sheet, or a level-specific sheet in the same family, and the matrix row points at it. Identical architectural plans do not make identical services, structure or fire sheets: the pressure zone changes every gravity zone, riser take-off sizes change with the level, circuits and boards change, reinforcement and loads change at transfer, plant and roof levels, compartments change at refuge and podium levels, penetrations change wherever the services do. Where system applicability differs between two levels, the sheets are separate.
- `notes` says what exactly differs and where it comes from (the DB field — `hyd.json zones`, `elec.json boards`, `structure.json members`, `fire.json compartments`, the penetration schedule — or the change request id).

The matrix is proposed by the sheet-list generator from the DB (the difference columns are computed from the per-level system inventories, not typed) and confirmed by the operator before the sheets are drawn; `check_sheets.py` then verifies that every physical level has a row for every applicable family, that every referenced sheet exists at the stated revision, passed QA and carries a manifest, and that a sheet cited by a level whose `differs_from_typical` is not `none` is a level-specific sheet. The matrix is attached to every gate report from G3 on and is what the reviewer walks when checking coverage — reading the manifest of each sheet is navigation, not checking; the check is against the drawn graphics.

## Scale by view type

| View | Scale | Size |
|---|---|---|
| Site plan, swept paths, site logistics | 1:500 (large sites) / 1:200 | A1 / A3 |
| Floor plans, layouts, framing, services layouts | 1:100 | A1 tower, A3 villa |
| Enlarged plans (core, wet areas, kitchens, venues), plant rooms, ID plans, corridor coordination, switchrooms, pump rooms | 1:50 | A1 / A3 |
| Room-type sets, joinery elevations, risers and shafts, stairs, lifts, combined-services sections, typical wall sections | 1:20 | A3 |
| Details (waterproofing, fire-stopping, façade, supports, joinery sections) | 1:10 / 1:5 | A3 |
| Schematics, SLDs, P&IDs, block diagrams, cause-and-effect | NTS | A1 tower (HY-0040 depth needs it), A3 villa |
| Schedules (DB, luminaire, fixture, door, member) | — | A3, one board / one type family per sheet |

## Density threshold and the split rule

Count annotated items in the view (text elements + leaders + dimension strings): over ≈ 60 on an A3 view or ≈ 150 on an A1 view, the sheet is a "split" verdict before it is drawn. Split order of preference: (1) by system family (air vs pipework; power vs lighting; water vs drainage), (2) by grid zone (west / east, or per wing) with a key plan on each part, (3) by enlarging the scale (1:100 → 1:50 for the dense zone as an enlarged plan, the parent sheet keeps a hatched "SEE A-12x" box). Never (4) shrink text, (5) stack labels, (6) drop items. The generator applies the rule from the DB counts (items per level per system) and proposes the split in the sheet list; the operator does not have to notice crowding on a drawn sheet.

## The sheet-list generator

`gen_sheetlist.py --stage S6` reads `db/levels.json`, the system inventories per level (`mech.json`, `elec.json`, `hyd.json`, `fire.json`, `structure.json`, room and wall counts) and writes `drawings/index.csv`:

`number, title, level_types, family, scale, size, source_db_query, item_count_estimate, split_of, status, date_drawn, qa_result, manifest_path`

together with the proposed `drawings/level-sheet-matrix.csv` (one row per physical level per applicable family, difference columns computed from the same inventories). The list and the matrix are produced first, reviewed by the PD in a minute (does every level have every family; are the plant rooms on their own sheets; are the splits sensible; which levels are flagged as differing), then the sheets are drawn one per response with `references/drawing-prompts.md`. The index is also what the project book shows as the drawing register and what `check_sheets.py` uses to verify every listed sheet exists, passed QA and carries a manifest; the matrix is what it uses to verify that every physical level is covered. Neither the index nor the matrix is evidence that a sheet's content is right — that is the content checklist against the drawn graphics.
