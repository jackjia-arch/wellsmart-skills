# Toolchain and runbooks

Open source first; the company buys no design software beyond what it already licenses (Revit for the drafting team, ZWCAD). Engines run locally through Claude Code — the Claude desktop app's Code feature for staff, a terminal for technical staff — on the Mac mini or a staff Mac for Python / IFC / EnergyPlus / OpenSees / headless Blender. The Windows workstation runs Revit, operated manually by the drafting team at S10; an engineer's ETABS, where one exists, is used only to open and compare the `.e2k`. Dong sets the machines up.

Why engines run locally and not in a cloud Cowork session: the cloud sandbox cannot fetch the EnergyPlus installer (it is released on GitHub, which the sandbox cannot reach) and PyPI carries only the OpenStudio SDK, not the engine. Local Claude Code can use whatever is installed on that machine, so engine work — EnergyPlus, headless Blender, an ETABS API where an engineer has it — stays local, and Revit stays with the drafting team on the Windows workstation. Cowork reads results back from the project knowledge base, never from a sandbox run.

## Tools by task

| Task | Tool | Open source / free | Notes |
|---|---|---|---|
| Design database | JSON / YAML in git; schema set by this skill (`references/db-schema.md`) | Yes | Single source of truth |
| 2D drawings | ezdxf (DXF) + the company HTML / SVG generator (gen.py pattern) with the QA overlay | Yes | Sheet content standard: `references/drawing-standards.md`, `references/sheet-content-checklists.md`; annotation engine `scripts/annotate.py` |
| IFC / 3D | IfcOpenShell + Python to generate; the ProjectBook's 3D viewer in the browser; Blender + Bonsai for technical staff to inspect and, when unavoidable, repair | Yes | The DB and the parameter scripts are the design source; the IFC is the engineering model; the `.frag` is a web derivative and never a document of its own. Stable GUID, DB id and the transform matrix are bound to each release. Contract in `references/ifc-review.md` |
| Revit | Desktop Revit, used manually by the drafting team for modelling, detailing and production drawings | Licensed, already held | S10 manual production; no automation development is scheduled (below) |
| Clash | IfcClash / IfcOpenShell geometry tree; browser issue marking + BCF | Yes | Solids, insulation envelopes, clearances and maintenance envelopes; every open line becomes an issue and is re-verified per issue against the new release, never closed on a reply |
| Structure | OpenSeesPy (3D, seismic), PyNite (small frames), sectionproperties / concreteproperties, own code-check scripts, `.e2k` writer | Yes (all pip-installable) | OpenSees gives the answers; the `.e2k` goes to the signing engineer to compare in ETABS |
| Thermal / energy / daylight | EnergyPlus engine + OpenStudio SDK / eppy / Honeybee (Ladybug Tools); Radiance; EPW weather from climate.onebuilding.org | Yes | NatHERS certificates need an accredited assessor with accredited software (FirstRate5 itself is free) |
| HVAC sizing | EnergyPlus sizing runs or DA09-method scripts; equal-friction duct scripts; digitised fan / pump curves | Yes | |
| Hydraulics | Fixture-unit scripts (AS/NZS 3500), `fluids` (Python) for pipes and pumps, BoM IFD rainfall | Yes | |
| Electrical | Maximum demand, AS/NZS 3008 cable tables, IEC 60909 fault levels, discrimination scripts; lighting with Radiance or DIALux evo | Scripts open source; DIALux free, not open source | |
| Fire | Hazen-Williams sprinkler / hydrant scripts; egress calcs; stair-pressurisation calcs | Yes | The local fire contractor re-calculates at the end |
| VT · acoustics | CIBSE Guide D traffic scripts; mass-law / composite Rw; plant-noise propagation scripts | Yes | |
| BQ / cost | IfcOpenShell quantities → cost library (xlsx) → `gen_bq.py` | Yes | The VE register governs BQ lines (`references/bq-and-calc-book.md`) |
| Standards / knowledge | AS/NZS (Jack's Google Drive) + NCC + NZBC loaded into the Dify / Claude Project knowledge base; the standards digest on top (`references/standards-digest.md`) | Standards already held | No source text = hallucination risk; a clause without source text is `CLAUSE TO CONFIRM` |
| Review | Checks script library + second-model blind re-calculation + issue register (CSV / xlsx / BCF); `scripts/peer_review.py` | Yes | `references/review-and-gates.md`, `references/review-hub.md` |
| Runtime | Mac mini with Claude Code (Python / IFC / EnergyPlus / OpenSees / Blender headless); Windows workstation with Revit for manual use; ZWCAD plugin for CAD read-back | — | Dong sets it up |
| Project web / knowledge base | The ProjectBook (Well Smart's own product) through its connector | Company product | Every output is registered there; no other publishing path (`references/project-book.md`) |

Standards ingestion is one step: the AS/NZS PDFs on Jack's Google Drive are shared to the company account, Dong loads them into the knowledge base indexed by standard number + year, and this skill hard-codes the rule that every clause citation carries standard number, year and clause (and the digest record id where one exists).

## 3D: generated, not sculpted

Two ways an AI can make 3D. Generative (an LLM sculpting meshes, text-to-3D) produces plausible but dimensionally unreliable geometry with no IFC classes — usable for concept renders only. Scripted (IfcOpenShell from the DB) produces IfcWall / IfcSlab / IfcBeam / IfcColumn / IfcDuctSegment with exact dimensions, storeys, classes, properties and quantities. Always use the scripted path for anything that feeds drawings, clash, procurement or the drafting team. LOD is an acceptance criterion on element content and intended use per element class, not a property of the file: an IFC, an RVT or the fact that IfcOpenShell was used is not evidence of LOD (`references/ifc-review.md`, LOD section).

Model checks after every IFC generation, with the report registered against the release: storeys and grids match the DB; element counts and volumes per class match the DB within the stated tolerance; ISO 19650 naming and DB tags; units recorded per model (the file's declared length unit and the scale factor to metres, as the generator wrote them; the viewer works in metres internally — `references/ifc-review.md`, coordinate contract); coordinate system MGA2020 (AU) or NZTM2000 (NZ) with the project base point and north rotation from `site/site.json`; classification (Uniclass) on every element, LOD stated per element, no unclassified element; every element carries its DB id and a GlobalId unchanged since the previous release unless the id-map records a split or replacement. Script success here is a data-consistency result, never an engineering PASS.

## Structural runbook

1. Generate the analysis model from `db/structure.json`: nodes, members with sections and materials, slab and wall shells, supports and foundation springs, rigid or semi-rigid diaphragms as decided, stiffness modifiers for cracked concrete, mass source.
2. Loads from `db/loads.json` (AS/NZS 1170 series; NZS 1170.5 in NZ): combinations per AS/NZS 1170.0; wind per AS/NZS 1170.2 (region, terrain, height multipliers, Cpe / Cpi); earthquake per AS 1170.4 or NZS 1170.5 with the site parameters from the site pack; snow where the site pack says so. Regional cases are site-pack fields, not afterthoughts: the Whitsundays are a cyclonic wind region, Queenstown is seismic, Niseko has snow load. The load tables go into the calc register.
3. Run OpenSeesPy (or PyNite for small frames). Save reactions, member forces, displacements, periods, drifts.
4. Model checks: the sum of reactions equals the applied loads per combination; no unconstrained nodes; mesh convergence for shells (refine until the key results settle within the tolerance stated in the calc register row); a simply supported beam and a cantilever benchmarked against closed-form results in the same script run.
5. Member checks with the code scripts (AS 3600 / AS 4100 / AS 1720; NZ: NZS 3101 / 3404 / 3603); sections via sectionproperties / concreteproperties; outputs member schedules (B1 / C1 / F1…), reinforcement ratios, deflection, crack control, vibration. Every check function has a unit test against a worked example.
6. Write the `.e2k` ETABS text model (stories, grids, points, lines, areas, materials, frame and shell sections, restraints, diaphragms, load patterns, cases, combinations, loads) and the one-page modelling assumptions sheet (stiffness modifiers, diaphragm assumption, mass source, load combinations).
7. Outputs: calc register rows, member schedules, GA, penetration schedule, the physical IFC model (IfcBeam / IfcColumn / IfcSlab / IfcWall with profiles and materials), the `.e2k` and the assumptions sheet. Reinforcement LOD 400 is the drafting team's / detailer's work at S10.

**OpenSees vs ETABS.** On the same model (same geometry, sections, stiffness modifiers, supports, loads, diaphragm assumptions) linear static and modal results differ by about 1–3 %: both solve the same finite-element equations. Differences come from modelling choices, not the solver — cracked-stiffness modifiers, rigid vs semi-rigid diaphragms, the P-Δ method, the shell elements and mesh for walls and slabs, the mass source, the response-spectrum combination. What ETABS adds is built-in code design modules and automatic wind loading; both are done by our own scripts.

**Process.** OpenSees produces the answers: forces, displacements, periods, drifts, member checks. At the same time the DB writes the `.e2k`, which goes into the S9 package with the assumptions sheet. The signing engineer opens the `.e2k` and has the complete model without rebuilding it; he runs it and compares with our OpenSees results — reactions, periods, inter-storey drifts and key member forces within 5 % count as agreement. Calibrate once on the first project, then it is routine. We cannot validate the `.e2k` format ourselves because we do not have ETABS, so on the first project the file must be opened on a machine that has it before the package is sent. Towers follow the same process with nothing separate; wind tunnel, geotech and temporary works are physical or contractor work.

**The dual-solver boundary.** Agreement between OpenSees and ETABS on a model generated from the same DB is a solver-consistency check and nothing more. The blind pass (`references/review-and-gates.md`) independently checks the raw geometry, loads, boundary conditions, units and modelling basis from the fact inputs; two consistent models can share the same wrong input, and model agreement never proves the shared inputs correct.

## EnergyPlus runbook (staff version)

Two runs per project. The **loads version** at S3, before equipment selection: it needs only zone geometry, floor heights, wall and glazing U-values and SHGC, orientation, internal gains, schedules and a weather file — a 2D plan plus one section has all of it, which is why it runs before any 3D model exists. Façade options (WWR, glazing, shading, insulation) are compared in this run with ΔCAPEX / ΔOPEX and the PD decides at G3. The **compliance version** at S7 rebuilds the model from the S7 IFC geometry for the NCC Section J JV3 or NZ H1 reference-building report and checks shading and self-shading on the real geometry; its parameters are retained with the result. The only human steps are signatures: an ESD consultant verifies and signs the Section J / H1 report; a NatHERS certificate for Class 1 / 2 housing is issued by an accredited assessor with accredited software — the AI prepares the model, a person presses the button.

**Design loads and annual energy are accepted separately.** Besides the EPW, the loads run locks the design-day source and conditions (station, edition or digest record id; outdoor dry-bulb / coincident wet-bulb and percentile), indoor temperature and RH setpoints, the outdoor-air basis, the latent basis, the diversity applied to zone sums and the sizing factor. The EPW serves the annual energy figure; the annual maximum of recent weather is never taken as the sizing load. At S5 the vendor's capacity and input power are checked at the project's design conditions, not the nominal rating. A failed or not-run simulation is reported as exactly that, never as PASS. Script-only alternatives are not enough: degree-day methods ignore latent load, thermal mass, schedules and part load and cannot size peaks; steady-state peak-load scripts serve a quick S1 check but cannot run an annual dynamic simulation, cannot produce a Section J / H1 report and are not validated engines.

**`results.json` (v2, `templates/results.schema.json`).** Fixed fields recognised by both Claude Code and Cowork: `project` · `stage` (loads | compliance) · `run_status` (completed | failed | not_run) · `error_message` (required when failed or not_run) · `date` · `weather_file` · `energyplus_version` · `design_day_basis` {source, outdoor_conditions, indoor_setpoints, outdoor_air_basis, latent_basis, diversity, sizing_factor} · `zones[]` {name, level, area_m2, peak_cooling_kW, peak_cooling_time, peak_heating_kW, sensible_kW, latent_kW, design_cooling_kW, design_heating_kW} · `block_cooling_kW` · `block_heating_kW` · `design_cooling_kW` · `design_heating_kW` (the S5 selection basis, with diversity and sizing factor applied) · `annual_kWh` · `monthly_kWh[]` · `facade_options[]` {name, peak_kW, annual_kWh, capex_delta, opex_delta} · `compliance` {method, reference_building_kWh, proposed_building_kWh, margin_percent, verdict PASS | FAIL | NOT CALCULATED} · `vendor_duty_check[]` {equipment_id, design_duty_kW, nominal_kW, capacity_at_project_conditions_kW, power_at_project_conditions_kW, source, status} · `inputs_manifest[]` {file, sha256} · `assumptions[]`. Only a `completed` run may carry results; `failed` / `not_run` carry the error or the missing input, the compliance verdict reads NOT CALCULATED and the vendor check stays TBC / NOT CALCULATED. `thermal/report.md` is one page, conclusions first, and says "not run" or "failed" when that is the case.

**Install (once per computer, about five minutes).** EnergyPlus is free; any employee installs it. It has no user interface, so running it is handed entirely to the Code feature of the Claude desktop app: staff only type; no terminal, no computer use.

Mac:
1. Open energyplus.net in a browser → Download → pick the macOS installer. Apple silicon takes arm64, Intel takes x86_64; if unsure, Apple menu → About This Mac and read the "Chip" line.
2. Double-click the downloaded .dmg, double-click the installer inside, Continue / Agree / Install all the way. It installs to `/Applications/EnergyPlus-xx-x-x`.
3. Done. No brew, no terminal.

Windows:
1. energyplus.net → Download → the Windows .exe installer.
2. Double-click, Next all the way; it installs to `C:\EnergyPlusVxx-x-x`.
3. Windows also needs Python: search "Python 3.12" in the Microsoft Store and install it, or let Claude Code install it in the next step.

Python packages (openstudio, eppy) are not installed by hand; Claude Code installs them on the first run.

**Run (per project).** Claude desktop app → Code → choose the local project working folder, the one containing `db/`, `site/` and the other repository directories. Drive is used only for the standards sources and existing working files; new calculation outputs are registered on the original project page, never left in Drive as the record.

First time on this machine, send this first:
```
Check whether this computer has EnergyPlus, Python 3, and the openstudio and eppy Python packages. Install whatever is missing; if something cannot be installed, tell me what to click. When done, run one of the EnergyPlus example files to confirm results come out.
```
Claude Code finds the energyplus program itself, runs pip install itself and runs an example from ExampleFiles to verify.

Loads version (S3) — replace the square brackets with the project's values:
```
Run a loads-version thermal model for [project name] in EnergyPlus.
Inputs: the design database is in ./db/ (levels, rooms, walls, openings); wall and glazing parameters in ./db/envelope.json; orientation and site in ./site/site.json; the project is in [city], use the nearest EPW weather file (download from climate.onebuilding.org into ./thermal/weather/).
Room uses and schedules per the [hotel guest room / villa / public area] defaults, internal gains per the company library defaults; anything missing use ASHRAE defaults and mark ASSUMED.
Outputs: 1. peak cooling and peak heating load per zone (kW, with month/day/hour), sensible and latent separately; 2. whole-building block load (non-coincident by orientation) and monthly energy; 3. façade option comparison: [Option A: glazing U / SHGC / shading…], [Option B…], with peak load, annual energy, ΔCAPEX at procurement-library prices and ΔOPEX at [tariff] for each; 4. an assumptions list, each marked ASSUMED or with its source.
Files: ./thermal/model.idf, ./thermal/results.csv, ./thermal/results.json (company schema), ./thermal/report.md (one page, conclusions first).
When done, read me the conclusions from report.md.
```
The design-day basis, indoor setpoints, outdoor air, latent basis, diversity and sizing factor are read from the DB and the brief's version lock and written into `design_day_basis`; where one is missing it is written as ASSUMED with its range and expiry gate, not silently defaulted.

Compliance version (S7) — the same, with the first sentence replaced by:
```
Rebuild the model from the S7 IFC geometry in ./model/ and produce the reference-building comparison report to NCC Section J JV3 (H1 modelling method for NZ projects); state PASS / FAIL and the margin clearly in the conclusion.
```

If it fails: copy Claude Code's exact words to the PD or Dong. Do not edit the files yourself.

**Result return path.** Claude Code writes the results into the local `./thermal/` → the staff member opens the original project page and uploads them → the first time choose ADD (new document); afterwards choose REVISE on the same document (new revision, same `document_id`) (or Claude Code registers them itself through the ProjectBook connector) → the ProjectBook verifies the manifest, the file sizes and the SHA-256 hashes and returns the registered revision link → Cowork reads that revision. Nothing is pushed anywhere else by staff. Completeness of a file transfer is decided by the manifest, sizes and hashes — never by "wait 10–30 seconds and it will be synced". In Cowork say:

```
Read [the results.json revision link registered on the original project page for this run] and [the report.md revision link]. Check that both belong to the same input batch and run results; update the loads and the façade comparison in the gate report; use these registered loads for equipment selection (S5); keep the referenced document IDs, revisions and calc IDs.
```

That upload is the knowledge-base entry; no second copy is made anywhere. `report.md`, `results.json` / CSV, `model.idf` and the dependency manifest are linked to S3 or S7, to the calc IDs, the input revisions and the equipment IDs; the existing records and all revision history stay in place (`references/project-knowledge-base.md`). If the connector is not in the session, the files wait in `kb-outbox/` with a manifest and the report says they are not yet registered (`references/project-book.md`).

## Revit at S10 — manual by the drafting team

Revit work at S10 is done entirely by people. The drafting team builds all Revit content manually — modelling, families, views, sheets, schedules, tags, dimensions, details, reinforcement coordination, drawing QA, worksharing and issue — against the frozen IFC / DB / drawings. No automation development (no Revit driver, no MCP, no API scripting) is scheduled for this stage, and none may be promised.

What the AI prepares for the hand-off: the frozen IFC release and DB, the calc book and the parameter tables (equipment schedules, member schedules, DB schedules, pump schedules), reference details as DXF / PDF from the details library, the procurement data, and the manual-detailing handover list (which elements, which sheets, which reference details, which vendor families are expected). Families the library lacks (special FCUs, pods, custom joinery) are built by people or supplied as vendor RFA files — a vendor RFA removes the modelling.

The contract between the two worlds:
- `model/id-map.csv` — DB id ↔ IFC GlobalId ↔ Revit ElementId, with the release id and a status that records split / replaced lineage — is maintained by the drafting team from the first element; an element without a row is not traceable and is a defect in the drawing QA (`references/db-schema.md`).
- Every Revit version is diffed against the previous one for design parameters and geometry. IFC and RVT are never assumed equivalent; equivalence is what the diff shows.
- Write-back: annotation / view / layout only → "no design change", nothing rerun. A changed dimension, load, material, equipment, interface, control or performance value, or a new anchor / support / penetration → written back to the DB by stable element id, only the affected calcs, sheets, model and BQ lines regenerated, and back to S9 for re-confirmation where a signed scope is affected. Generators read the overrides register and never silently overwrite manual detailing (`references/db-schema.md`, `references/stages.md`).
- Villas and low-rise projects where the contractor does not need an RVT, and where approvals and the installation / manufacturing depth are in place, are built from the DXF / PDF / IFC package without entering Revit for the file format alone.

## CAD read-back

If an architect draws by hand in ZWCAD, the DXF must be readable back into the DB: fixed layer names per element type, rooms as closed polylines with a name attribute, doors and windows as blocks with type attributes, one grid and one datum. The ZWCAD plugin validates this before export; a DXF that fails validation is returned, not interpreted.
