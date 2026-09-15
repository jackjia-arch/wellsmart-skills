# IFC development, web review and issues the AI can locate

Selected stack: Python + IfcOpenShell for design, the ProjectBook's 3D viewer for browser review, Blender + Bonsai for technical staff. Ordinary staff open only the project's ProjectBook page; nobody installs Blender to review a model. S4 puts architecture, structure, interiors and MEP space reservations online; S7 adds main runs, equipment, penetrations, insulation and maintenance envelopes. Browser picking of issues is the product development scope of this period: what follows is the implementation contract, not a connected project feature — its end-to-end status is UNVERIFIED. The design source is always the DB and the parameter scripts (`references/db-schema.md`); the IFC is the engineering model; the `.frag` is a web derivative; a web mesh is never edited as if it were the design.

## Tools and their roles

| Work | Tool | Required deliverable |
|---|---|---|
| Generate / revise IFC | Python + IfcOpenShell | Native IFC from the DB and parameter scripts with stable GlobalId, DB ID, storeys, systems, connections and element properties. The AI changes source parameters; it never treats the web mesh as the design source |
| Automatic clash and clearance | IfcClash + IfcOpenShell geometry tree | Per discipline combination: solid intersection, insulation outer envelope, maintenance / door-swing / replacement space; valid connections and opening rules listed separately. Output both GUIDs, location, the rule checked and the evidence |
| Staff web walk-through and picking | The ProjectBook 3D viewer (Jack's product; web IFC libraries are its implementation choice) | Level / discipline filters, clipping, walk, click-to-locate, the issue panel; picking returns model, element and point so the contract below can be met |
| Technical staff local check | Blender + Bonsai | IFC visualisation, offline diagnosis, necessary manual model repair; engineering changes go back to the DB by element ID. A plain Blender mesh does not replace IFC semantics |
| Web loading package | The ProjectBook's IFC → web-mesh conversion, tool versions pinned per release | Convert each release once and cache it; split by level / discipline; keep the original IFC for download and hash verification |

Engines and runbooks (OpenSees, EnergyPlus, structural `.e2k`) are in `references/toolchain.md`; the tool versions used for a release are written into the release record and the brief's version lock.

## What the models contain

| Release | Content | Check volumes carried in the IFC |
|---|---|---|
| S4 first IFC (no gate) | ARCH + STR + ID generated from the DB; MEP only as space reservations — riser volumes, plant rooms, main service corridors | Fixed fire compartments, accessible clearances, fire pump and pipe reservations, façade maintenance space, acoustic build-up thicknesses, vehicle envelopes |
| S7 detailed IFC (G5) | MEP main runs, equipment, penetrations / openings, insulation, maintenance and service envelopes; structural detail; thermal compliance model rebuilt from the same geometry | Installation, maintenance, inspection and replacement envelopes per equipment item; door swings; statutory headroom; penetration sleeves |

MEP 3D is not built before S5 equipment selection — it would be redrawn. Model-check scripts run after every IFC generation and their report is registered with the release:

| Check | What passes |
|---|---|
| Storeys | Every DB level exists as an IfcBuildingStorey with the DB name and elevation; no extra storeys |
| Grids | Grid lines, labels and offsets match `db/grids.json` |
| Naming | Files, models and elements named to ISO 19650; element tags equal the DB tags |
| Units | The file's declared units are recorded per model and match what the generator wrote (the DB is millimetres, `references/db-schema.md`) |
| Coordinate system | Project base point, north rotation and CRS as in `site/site.json` (MGA2020 for Australia, NZTM2000 for New Zealand) |
| Classification | Every element classified (Uniclass) and its LOD stated per element to BIMForum; no unclassified element |
| Counts and volumes | Element counts and volumes per class match the DB within the stated tolerance |
| Identity | Every element carries its DB id and a stable GlobalId that did not change from the previous release unless the element was replaced (then the id map says so) |

Script success here is a data-consistency result, never an engineering PASS.

## The staff procedure — four steps

1. Open this release's model, choose level and discipline, walk or clip to the place in question.
2. Press "Mark issue" and click a component surface. For a clash, click the second component too. For a clearance problem choose one component plus a check plane / envelope. A click on empty space cannot create an issue and never invents a component.
3. Type one sentence, for example "This duct hits the beam; prefer an east re-route and keep the corridor clear height." The system saves the components, coordinates, camera, clipping, snapshot and model release automatically.
4. Press "Submit" and receive a persistent issue ID. Then tell the AI "process the confirmed issues of this release"; after processing, open the same issue to compare the before / after viewpoints.

## Coordinate contract

- Raycaster hits return the model, a `localId` and a point; the model's mapping resolves the selection to the IFC GlobalId. `localId` / Express ID are valid only inside that file version; the key across releases is `model_id` + GlobalId + DB id. An intersection issue stores both components, never only screen pixels or a screenshot.
- Coordinates are metres internally. For every model the release records the items below; together they are the transform snapshot (`transform_snapshot_id`).

| Recorded per model | Content |
|---|---|
| Original units | The IFC file's length unit and the scale factor to metres (IfcOpenShell `calculate_unit_scale()`) |
| Engineering origin | The project base point and the model's own origin, in engineering coordinates |
| Axis directions | Which way X / Y / Z point in the file, including the north rotation |
| Geo-reference | The CRS and map conversion where present; handled with geolocation utilities where map conversion applies |
| Model → viewer matrix | The complete 4×4 matrix from model / project space to viewer-world: unit scale, rotation, Y/Z axis swap and the render relocation (large-coordinate offset), in one matrix |
| Inverse | The inverse matrix, stored, not recomputed on the client |

- A fixed-version adapter first normalises the raycaster hit to viewer-world, then applies the inverse to return engineering coordinates. The matrix is bound to the same release as the model; a matrix from another release is never applied.
- The anchor stored on an issue is therefore an engineering coordinate in metres plus the `transform_snapshot_id` that produced it, so the point can be re-projected into any later release's viewer and compared with the original within the round-trip tolerance.

## BCF exchange versus company issue data

BCF exchanges viewpoints, components, clipping, snapshots and comments and is the interchange with other tools. An arbitrary pin XYZ, the WSG DB id, the model hashes and the exact release binding are company issue data; do not assume a generic BCF pin field exists for them. A BCF export carries the issue link and may attach the issue JSON as a companion file. The company record is the `wsg.issue/1` JSON (`templates/issue.schema.json`).

## The issue record — `wsg.issue/1`

Development example from the handbook; IDs and coordinates are illustrative, not project data:

```json
{
  "schema_version": "wsg.issue/1",
  "issue_id": "DEMO-0042",
  "release_id": "DEMO-r017",
  "models": [
    { "model_id": "MEP", "sha256": "<full IFC SHA-256>" },
    { "model_id": "STR", "sha256": "<full IFC SHA-256>" }
  ],
  "components": [
    { "model_id": "MEP", "ifc_global_id": "<IFC GlobalId>", "db_id": "DUCT-021" },
    { "model_id": "STR", "ifc_global_id": "<IFC GlobalId>", "db_id": "BEAM-008" }
  ],
  "anchor": {
    "frame_id": "project-engineering-r017",
    "unit": "m",
    "xyz": [12.35, 8.62, 18.45],
    "transform_snapshot_id": "xf-r017"
  },
  "viewpoint_ref": "<camera / clipping / visible components>",
  "snapshot_ref": "<saved image>",
  "description": "DEMO: duct clashes with beam; prefer east reroute and retain corridor clear height.",
  "status": "UNTRIAGED"
}
```

| Field | Meaning and rule |
|---|---|
| `schema_version` | Always `wsg.issue/1`; a later schema is a new version, never a silent change |
| `issue_id` | Server-issued, persistent, stable across releases and rounds; the same id is cited by the review register and the gate report |
| `release_id` | The frozen release the issue was raised on; the before-view is bound to it |
| `models[]` | Every model involved, with `model_id` and the full SHA-256 of its IFC in that release; a hash mismatch means a different model, not the same one |
| `components[]` | One entry per component (two for a clash): `model_id`, `ifc_global_id`, `db_id`. The DB id is what the AI edits; the GlobalId is what the viewer highlights |
| `anchor` | `frame_id` = the engineering frame of that release; `unit` = "m"; `xyz` = engineering coordinates; `transform_snapshot_id` = the matrix set used to compute them |
| `viewpoint_ref` | Camera, clipping planes and visible-component set, restorable in the viewer and exportable to BCF |
| `snapshot_ref` | The saved image at submission time; evidence, never the anchor |
| `description` | The one sentence the person typed, plus the issue type when the form asks for it |
| `status` | UNTRIAGED → OPEN → READY_FOR_REVIEW → CLOSED / NEEDS_RELOCATION |

An issue draft can be saved by anyone without login as UNTRIAGED; confirming, processing and verifying use the company's existing authorisation in the ProjectBook. When the viewer is not available in a session, an issue is the same JSON as a file under `issues/` in the project repository, written by the AI operator from a person's description or from a confirmed clash-report line, and registered in the ProjectBook when the connector is present; the peer-review register `issues/issue-register.csv` stays the register that `scripts/peer_review.py` writes (`references/review-hub.md`).

## Issue states and AI handling

| State | Set by | Meaning and evidence |
|---|---|---|
| UNTRIAGED | Anyone who saves a draft from the viewer, without login | Recorded with components, anchor, viewpoint, snapshot and release; not yet a design task |
| OPEN | A staff member confirms it | The issue is real and assigned to the AI operator; the engineering change begins from the frozen release named in `release_id` |
| READY_FOR_REVIEW | The AI, when the new release is registered | The change is made in the DB, dependants rerun, IFC regenerated, clash rerun; the before / after viewpoints are bound to the two releases |
| CLOSED | A person or an independent review | Verified on the new release: the clash is gone or the clearance is met, the rerun calcs pass, the dependants are consistent; closure evidence stored on the issue |
| NEEDS_RELOCATION | The system, when the original component cannot be found in the new release | The issue stays open until a person re-anchors it; never auto-closed |

What the AI does with an OPEN issue, in order:

1. Read the issue and the frozen IFC / DB of `release_id`; resolve every component to its DB id; refuse to work from the web mesh or a screenshot.
2. Decide the change in the source parameters (route, level, size, support, opening) and write the impact list: the calcs, sheets, models, BQ lines and signed scopes that depend on the changed objects.
3. Change the DB by element id; record the change request if a frozen parameter moves (`references/db-schema.md`).
4. Rerun only the affected calcs; regenerate only the affected sheets and BQ lines; regenerate the IFC for the affected models.
5. Rerun the clash check on the new models against every other model in the release; every remaining or new clash is an issue.
6. Register the new release in the ProjectBook and mark the issue READY_FOR_REVIEW with the before / after releases; return the list of what changed.
7. Stop. Closure is a person's or an independent review's decision on verified evidence, never the AI's own.

Rules that hold in every case:

- A duct re-route usually changes resistance, fan duty and quantities: the pressure-drop calc, the fan selection check and the BQ lines are in the impact list, not only the geometry. The impact list is written before the rerun and recorded with the new release.
- Labels, comments and annotation-only edits never trigger an engineering rerun; they are recorded as "no design change".
- A split or replaced component keeps the old → new id mapping in the release record so the issue's components resolve in the new release.
- If the original component cannot be found in the new release the issue becomes NEEDS_RELOCATION; it is never auto-closed because the component disappeared, and a pin never drifts silently to a new position.
- An unfixed clash stays open; a clash that recurs after a fix reopens the same `issue_id`. Closure needs verified change on the new release, never the designer's reply alone.
- A gate does not close, and a technical package does not reach READY_FOR_RELEASE, while P0 / P1 issues on it are open (`references/review-and-gates.md`).

## Viewer completeness — acceptance before anyone reviews on the web

Web IFC converters do not convert every IFC class by default. The ProjectBook's conversion must have the required classes configured explicitly and verified after each conversion: MEP elements, equipment, openings and penetrations, proxies (IfcBuildingElementProxy) and the check volumes. Coverage of reviewable elements and their GUIDs must be 100 % — count the elements per class in the IFC and in the web mesh and reconcile the difference to zero or to a listed, justified exclusion. A missing element on the web is never evidence that there is no clash. Openings, clearances and other objects with no ordinary solid are shown on a separate check layer, and the quantity reconciliation states how each such object is represented.

## Acceptance targets — not yet executed

| Item | Pass condition |
|---|---|
| Coordinate round trip | Two combined models covering mm / m units, rotation and a large coordinate offset; 10 known points saved as issues, reopened, and every engineering coordinate within ≤ 1 mm. This verifies the coordinate conversion only, not engineering geometry accuracy |
| Issue reproducibility | 10 issues all restore their release, components, viewpoint, snapshot and clipping; after a change of browser they are recovered from the API; a BCF export reproduces viewpoint and components in another compatible tool, with the WSG pin kept in the JSON / issue link |
| Fix and regression | Fix one clash, keep one, replace one component: the three issues end as awaiting re-verification (READY_FOR_REVIEW), still open, and NEEDS_RELOCATION respectively; never all closed automatically |
| Change scope | One engineering change updates only its dependants; one annotation-only change triggers no recalculation |

These are acceptance targets for the development; none has been run. Results, when they exist, are recorded with the release and the tool versions.

## Clash checking scope

Clash checks run per discipline combination on the frozen release, not on a live model.

| Check class | What is tested | Typical rule source |
|---|---|---|
| Hard clash | Solid intersection between elements of different systems or disciplines | Geometry only |
| Insulation | The insulated outer envelope, not the bare pipe or duct | Insulation thickness from the spec |
| Maintenance space | The clearance envelope in front of and around each equipment item and access panel | Vendor data, equipment schedule |
| Installation space | Can the item be brought to its position and fixed there (route, lifting, fixing access) | Vendor data, construction planning |
| Inspection access | Reachability of valves, dampers, filters, fire-stopping, test points | Discipline rules |
| Replacement route | The largest replaceable component reaches its position and back out through doors and corridors | Equipment dimensions, door schedule |
| Door swings and headroom | Door swing arcs, statutory headroom in corridors, stairs and plant rooms | Compliance scripts (`references/disciplines.md`) |
| Penetrations vs structure | Every penetration has a sleeve, a tested fire-stopping system and a structural allowance; none through a member that forbids it | Penetration schedule, structural rules |
| Valid connections and openings | Joints, fittings and designed openings listed as permitted so they are not reported as clashes | The DB's connection data |

Automatic re-route rules: small pipes first, then large ducts, never structure. The residual clash report separates AI-resolved from needs-a-person, and every open line becomes an issue in the schema above. Each clash line cites the rule, both GUIDs, the location and the evidence; the count of open P0 / P1 clash issues is a row in the high-risk table of the gate report.

## Releases and the viewer package

A release is frozen as a set:

- `release_id`, and for each model its `model_id`, the IFC file and its full SHA-256;
- the transform snapshot (`transform_snapshot_id`) for every model;
- the model-check report and the clash report for this release;
- the impact list of what changed since the previous release, and the old → new id mapping for split or replaced elements;
- the web-mesh package per level / discipline with the converter version pinned, plus the required-class configuration used for the conversion and the element-count reconciliation;
- the tool versions (IfcOpenShell, IfcClash, the ProjectBook converter) and the DB commit the models were generated from.

The web mesh is a derivative of the IFC revision in the ProjectBook, never a document of its own; the original IFC stays downloadable for verification (`references/project-knowledge-base.md`). "Original stored" and "converting" are separate states, and a failed conversion is retried, never shown as a published viewer. Releases are registered through the ProjectBook connector and published to a use only through the gate that governs them; an S4 release is walked by the PD without any gate, an S7 release is what G5 freezes.

When the viewer is not yet available for a release, the IFC is inspected in Blender + Bonsai by technical staff, who can drive it for the PD; the clash report is read as a document; issues are written as files under `issues/` and registered later. A viewer capability the ProjectBook has not demonstrated stays UNVERIFIED, and no page may show it as working.

## Manual Revit hand-off at S10

The drafting team builds all Revit content by hand from the frozen IFC / DB / drawings; no automation development is scheduled for this (SKILL.md, roles). The MEP department completes the final services coordination in that BIM to LOD 400 — fittings, hangers and supports, seismic restraint, sleeves, fabrication spools, equipment connections — starting from the S6 crossings register and the S7 clash-free IFC, which are the design baseline and not the end state; each MEP release sheet carries that coordination sign-off (`templates/release-sheet.md` line 11). The contract between the two worlds:

- `model/id-map.csv` — DB id ↔ IFC GlobalId ↔ Revit ElementId — is maintained by the drafting team from the first element; every element that carries a DB id in the IFC has a row once it is modelled. An element without a row is not traceable and is a defect in the drawing QA.
- Every Revit version is diffed against the previous one for design parameters and geometry (dimensions, loads, materials, equipment, interfaces, controls, performance, new anchors / supports / penetrations). IFC and RVT are never assumed equivalent; equivalence is what the diff shows.
- Write-back rule: annotation / view / layout only → "no design change", nothing rerun. A design change → written back to the DB by stable element id, only the affected calcs, sheets, model and BQ lines regenerated, and back to S9 for re-confirmation where a signed scope is affected (`references/stages.md`, `references/db-schema.md` overrides register). Generators never silently overwrite manual detailing.
- Issues raised at S10 use the same schema: components cite the DB id and the IFC GlobalId; the Revit ElementId is resolved through the id-map, not stored as the key.

## The 3D review page — UI in brief

Full page rules: `references/ui-guidance.md`. The requirements specific to this page:

- Main area: the 3D canvas on the release's web mesh. Desktop: a 320 px issue panel on the right; mobile: a bottom sheet. Toolbar: level / discipline, clipping, walk, select, mark issue, issue list; the common controls keep 44 px targets.
- Entering mark mode shows the prompt "click a component surface", so an issue is never created by accident while walking. A selected component shows its id, system and level; a clash adds a second component.
- The form asks for one sentence and an issue type; coordinates, GUIDs, camera, clipping and release are captured automatically and shown in the evidence disclosure. A location preview is shown before submit.
- A successful submit must show a server-issued issue ID. On failure the draft is kept with "retry" and "export JSON". "Saved locally" is never displayed as "AI has received it".
- Clicking an issue in the list restores the model release, clipping, highlight and camera; the panel shows original text → AI reply → changed objects → calc / clash evidence → re-verification. Before and after are each bound to their own release. A missing original object shows "needs relocation"; a pin never drifts in the new release and never becomes "resolved" because it vanished.
- Stable links for the project, the release, the issue and the exact revision are copyable.

## LOD

LOD is an acceptance criterion on element content and intended use, per element class, not a property of a file format. S4 and S7 target measurable, coordinated design geometry; S10 adds fabrication, assembly and installation information for each actual procurement package. IFC, RVT, a mesh or the fact that IfcOpenShell was used are not evidence of LOD. Generative meshes may serve concept renders; an engineering model needs traceable dimensions, positions, classification, properties and interfaces. Generating IFC from the DB improves dimensional consistency, but actual geometry, system connectivity, spatial relationships and installation information are still verified. Requirements are listed per element class in three layers — design dimensions / performance → coordination and supports / hangers → fabrication and assembly information — and the vendor's or detailer's content and sign-off scope are written into the deliverables table. Pilot acceptance looks at DB quantities, actual views and sections, element connections, clashes and procurement usability together; a typical level passing does not stand in for the plant rooms, transfer levels and roof. A freeze is the current traceable design baseline and can change through a change request; it is not a promise of no rework. With only non-blocking provisional inputs, bounded preparation may continue within a stated scope; a hard technical FAIL or a critical calculation due at the gate is never turned into a pass by a PD signature. Final manufacturing release rests on closed evidence for that package (`templates/release-sheet.md`).

## Defects

- Editing the web mesh or a Blender mesh as if it were the design; changing geometry without the DB id.
- Storing an issue as a screenshot or screen pixels; storing a clash with one component; using `localId` as a cross-release key; applying a matrix from another release.
- Auto-closing an issue because the component disappeared; closing on the designer's reply; letting a pin drift; treating a viewer that dropped a class as proof of no clash.
- Rerunning every calculation for a comment, or no calculation for a duct re-route.
- Claiming the viewer, picking, issue API or acceptance results exist before the execution record shows it; showing "AI has received it" for a local save.
- Assuming IFC and RVT are equivalent; an element without an id-map row; a manual change not diffed and not written back.
- Calling an IFC "LOD 300" because it is an IFC; accepting a typical level as proof for plant rooms and the roof.
