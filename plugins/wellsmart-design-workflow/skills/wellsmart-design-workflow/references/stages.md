# Stages S0–S10 and after: inputs, what the AI does, outputs, what freezes, what people do

Every project runs the same stages. On a villa one operator runs them in sequence; on a tower the same operator runs three AI streams in parallel (ARCH+ID / STR / MEP+FIRE). The bottleneck is human reading and judgement time, not the AI. Programme target for the AI package: weeks 1–2 S0–S3, weeks 2–4 S4–S6, weeks 4–8 S7–S8, overlapping; a mature package then enters S9. Consultant response, statutory approvals, construction and handover have their own programmes and are never promised inside the 4–8 weeks.

Three ordering rules that differ from a conventional programme: fire strategy, structural system and MEP space reservation are done at S1, before interiors; the loads thermal model is done at S3, before equipment selection; MEP 3D is built only at S7, after equipment is selected — S4 models ARCH+STR+ID only. All seven specialist streams (fire engineering, wet fire, dry fire, DDA, façade, acoustics, traffic) start at S0 with everything else; VT, civil and ESD likewise (`references/disciplines.md` for what each produces).

A gate is a PD signature that freezes the stage's parameter set. Between gates nobody asks the PD anything: missing inputs become bounded assumptions with an expiry gate; work that does not depend on them continues; the affected part stays provisional. A freeze is the current traceable design baseline — it can be updated by a change request and does not promise no rework. A hard technical FAIL, or a critical calculation that is due at this gate and not done, cannot be turned into a pass by a signature (SKILL.md rule 15).

---

## S0 · Kick-off — G0 · brief frozen

**Input.** The PD's intended use and intent (a few sentences); site information.

**AI does.**

Expand the PD's sentences into a full brief, every field filled or `ASSUMED — TBC`: use and building class; type of construction; jurisdiction and code edition (NCC year + state variations, or NZBC clause editions), certification pathway; key count, room mix and area-schedule targets; GFA / FSR / height limits; target cost and cost/m²; programme and long-lead dates; brand / style / ID direction; structural system preference and DfMA (pod / module / precast / CLT); MEP system preference (hydronic / VRF, all-electric); ESD targets; operating model (staffing, F&B leased or not → BOH area); procurement constraints (owner-supply list, dual certification, China supply chain); DtS / PS appetite; exclusions.

Then, without waiting: the site data pack list, pulling public data itself (planning controls, flood, wind region, seismic parameters, EPW weather, IFD rainfall, BAL) and marking each item have / missing / to commission; a one-page regulatory basis; the certification pathway per region (`references/certification.md`); a feasibility area schedule and Cost Plan 0; a design programme with gate dates and long-lead order points.

**Discipline plan.** Build the specialist responsibility / input / output / interface matrix: fire engineering, wet fire, dry fire, DDA, façade, acoustics, traffic are all in from S0. List the site survey, fire-water supply, background noise, design vehicle, wind pressure and façade boundary conditions each needs. Identify where regulated engineering services begin in this jurisdiction and who carries them (in-house RPEQ, NSW registered practitioner, NZ CPEng — `references/certification.md`).

**Handover planning.** Create the project's Project Book page and the handover requirements matrix at S0 (`templates/handover-matrix.csv`): drawings / calcs, consultant endorsements and approvals, procurement / installation records, as-built drawings, O&M, commissioning records, asset register, warranties, training and maintenance requirements. Per discipline: owner, required format, fields, acceptance condition and due milestone. Name the Project Manager and the future Operation Owner (a person, not a department); the PM holds the Operation Owner's duties until one is appointed. Fix the ID schemes now: `document_id`, `asset_id`, `system_id` / `space_id` (`references/db-schema.md`). Define delivery requirements now; do not appoint design consultants now.

**Version lock.** Write into the brief: standard editions and state variations, standards-digest hash, library module versions, product-data dates, calculation script / tool versions. The project uses these fixed versions; library updates never overwrite a running project without an impact list and gate approval (`references/library-and-repos.md`).

**Outputs.** Brief · Site Data Pack index (have / missing / to commission) · Regulatory Basis · Certification Pathway · Programme · Cost Plan 0 · specialist matrix · handover matrix · Project Book project · version lock.

**Freeze (G0).** Every brief field has a value or an ASSUMED entry; jurisdiction, class, code edition, pathway, ID schemes, locked versions.

**People.** Commission the physical work: survey, geotech, services-availability applications, contamination, acoustic environment measurements. The PD confirms the brief.

---

## S1 · Architectural concept + systems space reservation — G1 · concept frozen

**AI does.** Massing and area schedule, floor-to-floor heights, cores, stairs and egress; draft fire strategy (compartments, travel distances, stair count, FRLs, sprinklers / hydrants, brigade access and booster position); structural system and grid (spans, transfer, lateral system, DfMA constraints); MEP space table (riser areas and positions, plant rooms, substation, tanks, generator and fuel tank, intake / exhaust louvres and their separations, waste room, loading dock, lift count and shaft sizes); VT traffic first pass; planning compliance check; Cost Plan 1; DA / resource-consent drawings if needed (site plan, shadow diagrams, materials board, streetscape). Sheets: `references/drawing-list.md` S1 block.

**Specialist outputs at S1.** Fire strategy and egress / compartment plans with the DtS / PS departure list; wet-fire hazard class, supply assumption, pump room / tank / booster space; dry-fire FIP / fire control room and EWIS architecture; DDA continuous route from street / drop-off to every function, accessible room distribution; façade system, WWR, cleaning / maintenance and combustibility route; acoustic receivers and insulation targets; traffic design vehicles, car / bicycle counts, loading / waste and entries. The DA report is drafted in parallel by the AI.

**Outputs.** Concept plan per unique level (DB → DXF / SVG) · area schedule · systems space table · structural scheme memo · fire strategy memo · Cost Plan 1 · DA drawings (optional).

**Freeze (G1).** Concept plans, space table, structural system, fire strategy.

**People.** The PD decides the concept. External planning or specialist appointments for DA / SSD start only when the corresponding AI package is mature; boundaries not yet formally approved stay provisional and later changes are written back by the AI.

---

## S2 · Interior layout + compliance — G2 · layout frozen

**AI does.** Room-type modules (company room library first), public-area layouts, first FF&E selection; style and palette only if the PD gave none (follow it if given); all compliance scripts: DDA (accessible SOU count, circulation and turning spaces, door widths, sanitary layout), sanitary fixture counts by occupancy, egress unaffected by layout, finish fire-hazard properties (group number / CRF), wet-area waterproofing extents, slip resistance, inter-room acoustic targets, illuminance targets; first FF&E procurement list.

**Specialist checks at S2.** DDA re-checks the whole route against real door leaves, hardware, furniture, gradients and installed clear dimensions; fire re-checks the interior layout's effect on occupancy / egress / compartments; acoustics fixes wall build-ups and flanking spaces; façade checks door / window to interior junctions; traffic checks drop-off / loading and pedestrian conflicts; wet / dry fire pre-lay sprinkler heads, detectors and speakers and coordinate with ceilings and luminaires.

**Outputs.** ID layouts (DB → DXF) · FF&E list · finishes concept · ID compliance report with the exceptions table.

**Freeze (G2).** Layout, room modules, public-area functions.

**People.** The PD reviews style and layout. The AI delivers compliance evidence and the exceptions table; a script that ran successfully is not an engineering PASS.

---

## S3 · Architecture frozen + 2D structure / MEP schematics + loads thermal model — G3 · geometry frozen

**AI does.** Architectural GA set finalised; structure in 2D (framing plans, preliminary members, load tables, foundation scheme); one MEP schematic per system (SA / RA / OA / EA, CHW / HHW / CDW, domestic CW / HW, sanitary and vent, stormwater, electrical SLD, communications, fire water, gas) at HY-0040 depth (`references/drawing-standards.md`); loads thermal model in EnergyPlus (zone geometry, floor heights, wall / glazing specifications, orientation, internal gains, schedules, weather → zone peak cooling / heating, annual energy, façade option ΔCAPEX / ΔOPEX); ceiling-zone section (beam depth + services zone + ceiling = clear height); Cost Plan 2.

The loads model uses explicit design days, indoor / outdoor conditions, outdoor air, sensible / latent split, diversity and sizing factors for zone and block selection loads; the EPW drives annual energy only — a recent weather year's maximum is never used as the selection load (`references/toolchain.md`, results.json v2).

**Specialist freeze items at S3.** Fire engineering: strategy finalised, egress calculation package, PBDB / FEB draft prepared by the AI (objectives, methods, acceptance criteria, consultation required). Wet fire: schematic, preliminary hydraulics, effective storage, pump duty, pressure zones, diesel / power / ventilation interfaces. Seismic (NZ always; AU where AS 1170.4 Section 8 applies): parts forces and drift demands per level from `STR-SEIS-01`, the restraint strategy per system family and the seismic-joint positions that every lane must cross with flexibility. Dry fire: detection / EWIS zoning, draft interlocks with MEP / lifts / access control. DDA: continuous route, ramps, rooms and toilets at 1:50 with clear dimensions. Façade: joint thermal + acoustic + wind + inter-storey movement option comparison and wall section. Acoustics: wall / glazing build-ups, plant positions, flanking control. Traffic: swept paths, ramp long-sections, vehicle headroom and waste flow.

**Outputs.** ARCH GA set · STR 2D · MEP schematics · Load & Energy Report (loads version) · ceiling-zone section · PBDB / FEB draft · Cost Plan 2.

**Freeze (G3).** Geometry and interfaces that have passed the specialist checks. Where a key input affecting clear height / cores / ramps / pump rooms / façade is missing, that part is explicitly provisional and does not block independent work. A hard technical FAIL is not frozen.

**People.** The PD decides the façade option — the single largest cost decision in the building — on the loads-model comparison with ΔCAPEX / ΔOPEX and simple annual return (`references/bq-and-calc-book.md`).

---

## S4 · First 3D model (IFC) — no gate

**AI does.** Generate IFC from the DB with IfcOpenShell: ARCH + STR + ID at LOD 300; MEP only as space reservations (riser volumes, plant rooms, main service corridors). Model-check scripts: storeys, grids, naming, units, coordinate system, classification (BIMForum LOD, ISO 19650 naming, Uniclass). Publish the release to the Project Book (IFC as attachments or Drive links, the model-check report as the body). The Project Book V1.1 has no 3D viewer: the PD walks the model in Blender + Bonsai driven by technical staff, or reviews the clash report and views published as images; issues are written as `wsg.issue/1` JSON files by the operator from the PD's comments and the clash report. The browser viewer with picking is a future Project Book feature (`UNVERIFIED — Project Book viewer`). `references/ifc-review.md`.

**Model scope.** Write the fixed fire compartments, accessible clearances, fire pump and pipe reservations, façade maintenance space, acoustic build-up thicknesses and vehicle envelopes into the IFC as check volumes. LOD is accepted per element on the information it actually carries; an IFC file is not automatically LOD 300.

**Not done.** MEP 3D — equipment is not selected, so it would be redrawn.

**People.** The PD walks the model; issues are picked in the viewer and land as UNTRIAGED.

---

## S5 · Key equipment selection — G4a · equipment frozen

**AI does.** From S3 loads and the product library select chillers / heat pumps / AHUs / FCUs (or VRF) / pumps / fans / hot water / switchboards / transformers / generators / UPS / lifts; per unit: duty, dimensions, weight, electrical load, noise, maintenance space, certification status, lead time. Comparisons with ΔCAPEX / ΔOPEX / simple annual return / payback (≥ 15 % rule). Equipment schedule and RFQ pack drafts. Vendor duty check: capacity and power at the project's actual conditions, not nominal ratings.

**Specialist selection.** Fire pumps / valve sets sized for the most disadvantaged point and the highest pressure, with real certification and test scope confirmed; detection / EWIS loops, sound pressure and intelligibility where applicable; DDA door hardware / rails / controls; façade glass / brackets / seals / inter-storey fire stopping systems; acoustics attenuators and isolators from vendor spectra; traffic dock levellers / doors / controls. When vendors return actual capacities, powers, dimensions and interfaces the model is updated; unanswered items stay TBC.

**Asset identity.** Give every maintainable unit a stable `asset_id` linked to system, level / room, equipment position, IFC / DB element and selection documents; a model or design revision never renumbers it. Record the confirmed vendor / model at procurement; physical serial numbers, install dates and warranty start dates are entered only when the goods and contract evidence arrive — unknown is `TBC`, never invented. A later physical replacement creates a new instance linked to the old one; the functional position stays traceable (`templates/asset-register.csv`).

**Outputs.** Equipment Schedule · selection comparison table · RFQ drafts · asset register (first fill).

**Freeze (G4a).** Vendor-confirmed brand / model / duty performance / dimensions / electrical load. Unconfirmed items freeze only the performance requirement and the space envelope and are no basis for manufacturing.

**People.** The PD approves selections; procurement issues RFQs, with the vendor handover requirements (S6) written into RFQ / PO.

---

## S6 · Detailed 2D per discipline + calc book + combined services — G4 · detailed design baseline

**Every discipline delivers.** Drawing set (100 plans / 300 sections / 400 details / 500 schedules / 600 schematics) · calc register · DBR · NCC / NZBC compliance matrix · PS register entries · SiD register entries · spec draft. Sheet families per level: `references/drawing-list.md`; content per sheet type: `references/sheet-content-checklists.md`.

**AI does (by discipline; methods and clauses in `references/disciplines.md`).**
- MECH: duct sizing and routing (equal friction), pipe sizing, insulation thickness (Section J / H1), ventilation rates (AS 1668.2), pressurisation and smoke exhaust (AS 1668.1), kitchen exhaust, refrigerant safety (small rooms with VRF, AS/NZS 5149), NR levels, control descriptions and BMS points list, fire-mode matrix.
- ELEC: maximum demand (AS/NZS 3000 App C), transformer / generator / UPS and essential-loads table, SLD, DB schedules, cables (AS/NZS 3008: current rating, voltage drop, short circuit), protection discrimination, fault current, earthing, tray sizing and segregation, lighting (lux, W/m², emergency), lightning protection, EV charging, metering, comms / security / GRMS / BMS interface table.
- HYD: demand and pipe sizes (AS/NZS 3500 fixture units), pressure zones / PRVs / tanks / boosting, hot water (storage, return balancing, temperature control, Legionella AS/NZS 3666), drainage and venting, stormwater and OSD, trade waste (grease arrestor by covers), gas, backflow prevention.
- FIRE: sprinkler density and hydraulics (AS 2118.1), hydrant hydraulics with pumps / tanks (AS 2419.1, AS 2941), detection and EWIS zoning (AS 1670), emergency lighting (AS/NZS 2293), fire dampers, fire-stopping schedule (every penetration → tested system), FIP / booster positions.
- STR: loads → OpenSees analysis → member design → foundations → penetration schedule; `.e2k` and modelling-assumptions sheet (`references/toolchain.md`). Pump logic: five deliverables per pumped system (`references/disciplines.md`).
- Others: VT, civil / stormwater, pool plant per the S0 scope; fire engineering, DDA, façade, acoustics and traffic per the specialist detail list below.

**Coordination.** Corridor / plant-room 2D coordination sections from the DB; ceiling-zone stacking rule (structure → fire → ducts → pipes → trays); lanes, crossings register and `scripts/coord_check.py` per level (`references/services-coordination-2d.md`). Seismic restraint of services: on every NZ project (NZS 4219 / NZS 1170.5, sprinklers NZS 4541) and on AU projects where AS 1170.4 Section 8 applies, S6 delivers restraint plans per level (brace types, spacing, anchor loads to structure, flexible connections, clearances at seismic joints) and the `*-SEIS-01` coverage rows; brace envelopes are reserved in the lanes so they do not appear as S7 clashes.

**Specialist detail at S6.** Fire engineering: executed smoke / egress analyses with convergence, sensitivity and acceptance results — not CFD input files. Wet fire: sprinkler / hydrant per level, pump-room details, detailed hydraulics with maximum / minimum pressures, supports and test schedules. Dry fire: devices / loops / cables, sound pressure and intelligibility where applicable, complete cause & effect. DDA: thresholds / rails / signage / tolerance details. Façade: brackets / movement / weatherproofing / condensation / fire edge seals and test plan. Acoustics: plant noise, vibration, penetrations and insulation details. Traffic: management / loading / CTMP / WMP. Every package carries its regulatory basis, calc IDs, sheets, interface list, procurement specification and acceptance requirements.

**Commissioning design.** Generate test procedures and pass criteria from the control descriptions (`templates/commissioning-tests.csv`): fire-mode interlocks, pump changeover, power-fail recovery, alarms, equipment failure modes, balancing. Each test lists preconditions, action, expected result, tolerance, record and owner; S10 issues the site version.

**Vendor handover requirements.** Write into spec / RFQ / PO deliverable lists: O&M, as-built drawings and original editable files, actual equipment list, serial numbers, control / BMS points and set-points, measured commissioning sheets, warranty and its start basis, service intervals, consumable / spare part numbers, training material and service contacts. Agree per item the `asset_id`, fields and upload point; accept against the S0 matrix; vendor uploads must bind to the equipment, system and document revision. S6 sets the requirements and blank tables; site results are filled after installation.

**Construction planning (builder role).** Site logistics plan 1:500, crane / lifting, staging, module and pod installation sequence, temporary works (propping, formwork, edge protection) drafted at S6, finalised at S10; temporary works signed by an engineer.

**BQ.** `BQ (ESTIMATE)` labelled as such, ratio rules for fittings allowed (`references/bq-and-calc-book.md`).

**Freeze (G4).** The detailed design baseline: RFQs and cancellable capacity reservations are allowed; this gate does not release manufacturing.

**People.** The checker reads the high-risk table; the PD reads the gate report.

---

## S7 · 3D detail + clash + thermal compliance model — G5 · model frozen

**AI does.** MEP + STR into IFC (main runs, equipment, penetrations, insulation and maintenance envelopes); clash scripts (hard clash + clearance: maintenance space, door swings, statutory headroom, penetrations vs structure) including installation, maintenance, inspection and replacement space, not just solid intersection; automatic re-route rules (small pipes first, then large ducts, never structure); residual clash report (AI-resolved / needs a person); thermal compliance model (Section J JV3 / NZ H1 report) rebuilt from the S7 IFC geometry.

**Issue loop.** Issues are raised against the frozen release as `wsg.issue/1` records (both GUIDs, DB ids, engineering coordinates, viewpoint, snapshot, release) — from the clash report, from Blender + Bonsai walks by technical staff, and from PD comments on the published release page; when the Project Book gains its browser viewer with picking (not in V1.1) the same records are created by clicking. The AI reads confirmed issues against the frozen IFC / DB, changes source parameters, reruns only the affected calcs / sheets / BQ, regenerates the IFC, reruns clash, publishes a new release marked READY_FOR_REVIEW; a person or independent review closes. Full contract: `references/ifc-review.md`.

**Specialist closure at S7.** Fire compartments and penetrations each matched to a tested system; wet fire maximum / minimum pressures and pump replacement route; dry fire, MEP, lifts and access control checked against one interlock matrix; DDA walks the whole final route; façade brackets vs structural deflection, BMU / cleaning space closed; acoustics checks every penetration and actual equipment spectra; traffic checks final vehicle envelopes and pedestrian routes.

**Manufacturing release.** Per procurement package, a release sheet (`templates/release-sheet.md`) is signed only when vendor performance / dimensions, calculations, interfaces, clash / maintenance, peer review and every approval affecting that package are closed and the production drawings and BQ are at the same revision. Until then only RFQ or capacity reservation with an explicit cancellation condition; amount and exit cost go into the decision record.

**Outputs.** Detailed IFC · clash report (AI-resolved / open) · penetration schedule · Energy Compliance Report · release sheets per package.

**Freeze (G5).** The model. The PD decides the direction for residual issues.

---

## S8 · Company peer review — G6 · review closed

**AI does.** The four layers (`references/review-and-gates.md`): script checks, blind re-calculation, LLM review, issue register; the gate report when everything is closed.

**Review scope.** The seven specialist streams enter the final review with ARCH / STR / MEP in the same batch. Exit criteria: P0 / P1 = 0; hard technical FAIL = 0; blocking assumptions expiring at this gate = 0; every closed item has a new revision and a re-verification record. 99 % is the seeded-defect detection target; the actual n and confidence lower bound are shown separately.

**People.** The checker reads the high-risk table (per item: done? / method / result / status); the PD signs G6.

---

## S9 · Consultant review + signatures + approvals — G7 · signed

**Package.** Drawings PDF / DWG · IFC (+ RVT if built) · calc package · structural `.e2k` + modelling-assumptions sheet · DBR · compliance matrix · PS register · SiD register · spec. Assembled by the AI with the transmittal and drawing index.

**Late appointment.** Consultants are engaged only now, against the frozen package: fixed fee quoted on the package, with the included review / feedback rounds, RFI and approval work written down; the AI answers and revises; only approved owner scope changes become variations. For performance solutions the AI-prepared PBDB / FEB enters statutory consultation first; the final report and signatures follow the feedback; other design work continues on stated assumptions, and later rework is never a reason to have appointed consultants earlier. Three packages A / B / C and the ten contract items: `references/certification.md`.

**AI does.** Assemble the package; draft replies to consultants, the certifier and authorities; produce diffs, affected recalculations and closure evidence for each consultant comment rather than full rewrites.

**People.** Consultants review substantively and sign per region (`references/certification.md`); the certifier / authorities process CC / BA / building consent, water, power and fire approvals. S9 duration follows the actual written responses; no fixed number of months is assumed and approval inside the 4–8 week design target is never promised.

**Endorsement archival.** Every endorsed / signed original and its covering letter is uploaded to the same project knowledge base within one working day of receipt (company target): signer, firm, discipline, date, `document_id`, exact `revision_id`, SHA-256 of the original, scope and attached approval conditions; a package-level signature also stores the per-file manifest. Originals are kept byte-for-byte; previews / OCR are linked copies. Only the revision the signature covers is marked "consultant-endorsed"; a later design change creates a new revision and never copies the old signature or inherits the endorsement (`templates/endorsement-record.json`, `references/project-knowledge-base.md`).

---

## S10 · LOD 400 production + BQ + procurement packages — delivery

**AI does.** Prepare the frozen IFC, DB, calc book / parameter tables and the manual-detailing handover list; `BQ (PROCUREMENT)` from IfcOpenShell quantities and the cost library with actual installation components (VE register manages BQ lines); RFQ packs (equipment schedule + spec + drawings + same-revision BQ + release conditions); long-lead order trigger table. Revit work is done by people; no automation development is scheduled for this stage.

**People.** The drafting team builds all Revit content manually — modelling, families, views, sheets, schedules, tags, dimensions, details, reinforcement coordination and drawing QA — against the frozen IFC / DB / drawings, maintaining the stable element id-map (`model/id-map.csv`: DB id ↔ IFC GlobalId ↔ Revit ElementId) and a per-version diff of design parameters and geometry; IFC and RVT are never assumed equivalent. The MEP department completes the final services coordination in BIM to LOD 400 — fittings, hangers and supports, seismic restraint (NZ: NZS 4219), penetration sleeves, fabrication spools, equipment connections — against the frozen IFC / DB and the S6 crossings register; the AI's S6 / S7 coordination is the design baseline it starts from, not the end state, and every MEP manufacturing release sheet carries the MEP department's LOD 400 coordination sign-off for that package. Procurement negotiates and signs. Villas and low-rise where the contractor does not need RVT, and where the approvals and installation / manufacturing depth are in place, can be built from the DXF / PDF / IFC package without entering Revit for the file format alone.

**Change write-back.** Every manual version is diffed against the previous one. Annotation / view / layout only, design unchanged → record "no design change", nothing is rerun. Changed dimensions, loads, materials, equipment, interfaces, controls or performance → write back to the DB by stable element ID, rerun only the affected calcs, regenerate the related sheets / model / BQ lines, and return to S9 for re-confirmation where a signed scope is affected. New anchors, brackets and penetrations are design changes. Generators never silently overwrite manual detailing (`references/db-schema.md` overrides register).

**Construction records and handover preparation.** Production drawings, approved changes, site RFIs / redlines, installed equipment, inspection / test / commissioning records are appended continuously to the same project knowledge base — only new or changed files, each linked to `document_id` / `asset_id`. Engineering changes found in Revit or on site follow the write-back rule; no engineering change, no rerun. As-built records exist only after construction is complete and verified; the S10 design package is never marked accepted as-built. 4–8 weeks remains the AI design target, not a construction or handover deadline.

---

## After S10 · construction → as-built → Handover Baseline → operations

The same Project Book page continues: construction records accumulate → as-built drawings / IFC / editable sources, O&M, asset and commissioning data are checked and accepted → the PM and the Operation Owner jointly freeze the Handover Baseline (scope, complete revision / hash manifest, asset register, acceptance records, known open items, responsibility transfer; per level / system batches each frozen separately, with handed-over vs pending shown on the home page) → the operations team keeps adding repair, replacement, maintenance and alteration records at the same address. Design basis, endorsements, procurement and construction history are all retained; the operations home page shows the accepted `current_operations` revisions and a design draft never replaces them.

Handover acceptance is quantitative, with the S0 matrix and the final applicable scope as the denominator: required records registered / accessible 100 %; maintainable assets with required fields and applicable O&M links 100 %; applicable test, commissioning, warranty and training evidence 100 %; known critical safety blockers 0. N/A needs a reason and an acceptor and is never silently removed from the denominator. Non-critical open items with owner and date allow conditional acceptance; a missing required item means "complete handover" is not declared. These are records metrics, not design correctness. The operations team runs a 20-question retrieval test (e.g. "AHU-01: belt model, service interval, where is the issued as-built?") — 20/20 must return the correct current source with page / entry, and an answer for missing data must say it is missing. Procedures: `references/project-knowledge-base.md`.

---

## Where the AI draws and where people go into Revit

| Stage | What | Who | Notes |
|---|---|---|---|
| S1 | Concept plans / elevations / sections, area schedule, massing 3D, DA drawings | AI | DB → DXF / SVG; massing IFC from the DB, rendered in Blender; a person may polish renders, not required |
| S2 | ID layouts 1:50, style / colour boards, FF&E schedule | AI | Sheets from the DB; boards with an image model |
| S3 | GA set, structural layouts, MEP schematics (HY-0040 type single lines), ceiling-zone section | AI | All DB → DXF / SVG |
| S4 | IFC 3D (ARCH + STR + ID, LOD 300) | AI, IfcOpenShell script | Release published to the Project Book; walked in Blender + Bonsai (browser viewer with picking is a future Project Book feature); issues as `wsg.issue/1` JSON with GUID, coordinates and release; nobody enters Revit |
| S6 | Discipline plans / sections / schedules, SLD, P&ID, control schematics, combined-services sections, joinery elevations, details | AI | Plans, sections, schedules from the DB; typical details from the details library; non-typical details drafted by the AI, buildability reviewed by a person |
| S7 | Detailed IFC (MEP main runs + equipment + penetrations) | AI, IfcOpenShell script | As S4 |
| S9 | Package (PDF / DWG / IFC / calcs) | AI | DWG converted from DXF; low-rise can build from this package once approvals and depth allow |
| S10 | Revit: walls / slabs / columns / beams / doors / windows / rooms / grids / levels / pipes / equipment placement | People in Revit | From the frozen IFC / DB; equipment placed and connected manually; id-map maintained; no automation development |
| S10 | Stairs, balustrades, curtain walls, complex roofs | People in Revit | Revit system families, manually |
| S10 | Families not in the library (special FCUs, pods, custom joinery) | People in Revit, or vendor RFA | A vendor RFA removes the modelling |
| S10 | Views, sheets, schedules, tags | People in Revit | Set up, laid out, annotated and checked manually |
| S10 | Dimensions, detail views | People in Revit | AI supplies DXF / PDF reference details; people import, annotate, develop and check dimensions and buildability |
| S10 | MEP coordination to LOD 400 (fittings, supports, seismic restraint, sleeves, spools) | MEP department in BIM | Against the frozen IFC / DB and the crossings register; signed per package on the release sheet; design changes written back by element id |
| S10 | Reinforcement LOD 400 | People / detailer | Usually the reinforcement subcontractor's shop drawings, not the design model |
| S10 | Drawing QA, worksharing, issue | People | |

## Interfaces that block a freeze

| Predecessor result | Affected geometry / systems | If missing |
|---|---|---|
| Fire strategy, accessible route, traffic envelope | Cores, doors, ramps, entries, driveways and headroom | Affected S3 geometry stays provisional; independent work continues |
| Wet-fire duty / storage, dry-fire interlocks | Pump / tank rooms, power / diesel ventilation, control points and risers | No final S5 selection and no manufacturing release on missing facts |
| Façade thermal / wind / movement, acoustic build-ups | Glass, brackets, slab edges, plant capacity, wall / floor thickness | Close the affected S7 checks, then release per package conditions |

## LOD, in one paragraph

LOD is an acceptance standard for element content and use, not a file format: S4 / S7 target measurable, coordinatable design geometry; S10 adds manufacturing, assembly and installation information per actual procurement package. IFC, RVT, mesh or IfcOpenShell are not LOD proof. Concept renders may use generative meshes; engineering models need traceable dimensions, positions, classification, properties and interfaces. Scripted IFC from the DB improves dimensional consistency but actual geometry, system connections, spatial relationships and installation information still have to be verified. Per element class the requirement runs design size / performance → fit and supports → manufacturing and assembly information, with vendor / detailer content and signing scope written into the deliverables table. A typical level passing does not stand in for plant rooms, transfer levels and roofs; pilot acceptance checks DB quantities, real sheets / sections, connections, clash and procurement usability together.

## Pilot before the first real project

Run the state machine and failure recovery with the mock reviewer first, then with real APIs: file hand-over → 3D issue → AI response → new draft → publish effective → history lookup → operations retrieval. Pilot on one typical level, one plant room and one riser through S0–S10, then rehearse the lifecycle with real construction records. Record person-hours, real model costs, review rounds, critical misses, false positives, consultant change volume, upload failures, records completeness and recovery results. Prove at least once each: "no engineering change, no rerun"; "a real engineering change updates only the affected DB / calcs / sheets / BQ and re-confirms the signed scope"; "a new upload loses nothing already there". Seeded-defect validation per `references/review-and-gates.md`, reporting target, n, detected, missed, false positives and the confidence lower bound separately. Test material is labelled DEMO and never presented as signed or built.
