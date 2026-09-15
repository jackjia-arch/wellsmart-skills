# Design database schema (outline)

One JSON file per domain in `db/`. Units: millimetres for geometry in the DB, metres to three decimals for levels (RL, FFL, SSL), SI for engineering quantities. Coordinates in the project coordinate system with the base point recorded in `site/site.json` (MGA2020 zone for Australia, NZTM2000 for New Zealand). Every element has a stable `id`; drawings, IFC GlobalIds, Revit ElementIds, BQ rows and calc IDs reference these ids, never positions. The DB and the parameter scripts are the design source; everything else — DXF / SVG sheets, IFC, `.e2k`, EnergyPlus input, BQ, calc book — is generated from it, and a manual change to any output is diffed and written back here (below).

```
<project>/
├── db/
│   ├── project.json     code, name, jurisdiction, code_edition, state_variations, building_class,
│   │                    type_of_construction, effective_height_m, rise_in_storeys, units, base_point,
│   │                    north_rotation_deg, id_schemes{}, version_lock{}
│   ├── levels.json      [{id, name, rl_m, floor_to_floor_mm, ssl_m, ffl_m, ceiling_zone_mm, use, level_type}]
│   ├── grids.json       [{id, label, axis: "x"|"y", offset_mm}]
│   ├── rooms.json       [{id (space_id), level, name, use, module_ref, polygon_mm[], area_m2, occupants,
│   │                     finishes_ref, oa_l_s, exhaust_l_s, nr_target, lux_target, frl_boundary, sou: bool}]
│   ├── walls.json       [{id, level, type_ref, start_mm, end_mm, height_mm, frl, rw, fire_rated: bool}]
│   ├── openings.json    [{id, wall, kind: door|window|louvre, width_mm, height_mm, sill_mm, type_ref, fire_rated, accessible}]
│   ├── envelope.json    wall and glazing constructions: [{id, layers[], u_value, shgc, vlt, r_value}]
│   ├── structure.json   {system, grid_ref, members: [{id, kind: column|beam|slab|wall|pile|footing, section_ref,
│   │                     material_ref, nodes[], level, span_mm, tag}], loads_ref, stiffness_modifiers, diaphragms}
│   ├── loads.json       dead, live, wind (region, terrain, Vr), seismic (site class, Z, kp…), snow, combinations
│   ├── mech.json        systems (SA/RA/OA/EA/CHW/HHW/CDW/refrigerant/condensate) with system_id, equipment[], ducts[],
│   │                    pipes[], terminals[], dampers[], insulation refs, controls: {points[], sequences[]}
│   ├── elec.json        supply, boards[{id, tag, level, rating_A, fault_kA, form}], circuits[], cables[], trays[],
│   │                    lighting[], emergency[], metering[], comms/security interfaces
│   ├── hyd.json         systems (CW/HW/HWR/SAN/SW/GAS/RW) with system_id, tanks[], pumps[], zones[], prv[], pipes[],
│   │                    fixtures[], meters[]
│   ├── fire.json        strategy refs, compartments[], frl_map, sprinklers{hazard, density, heads[]}, hydrants[],
│   │                    pumps[], tanks[], detection zones[], ewis[], penetrations[]
│   ├── equipment.json   [{id, asset_id, tag, discipline, system_id, sku (products/index), duty, dims_mm, weight_kg, kW,
│   │                     noise_dBA, location: {level, x_mm, y_mm}, maintenance_clearance_mm, cert_status, lead_time_weeks}]
│   ├── services-routes.json   2D services-coordination runs (below)
│   ├── crossings.json         2D services-coordination crossings register (below)
│   ├── calcs.json       [{calc_id, discipline, title, inputs{}, method, standard, year, clause, digest_record_id,
│   │                     result, limit, status, script, version, date, assumed_inputs[]}]
│   ├── assumptions.json [{id, stage, parameter, value, range, affects[], owner, expires_at_gate,
│   │                     status: ASSUMED|CONFIRMED, source}]
│   └── issues.json      issue register mirror (see templates/issue-register.csv)
├── model/
│   └── id-map.csv       DB id ↔ IFC GlobalId ↔ Revit ElementId (below)
└── drawings/
    ├── index.csv                the sheet list (references/drawing-list.md)
    ├── level-sheet-matrix.csv   level → sheet / revision → difference (references/drawing-list.md)
    └── overrides/<sheet>.json   the overrides register (below)
```

Conventions:
- `*_ref` fields point to library entries (`modules/`, `products/`, wall types, finishes) so reuse is explicit and traceable.
- Element `tag` is the drawing tag (B1, C1, F1, AHU-01, CW-P1, CW-M14, DB-G1); tags are unique per discipline across the project.
- Every numeric design value that appears on a drawing must exist in `calcs.json` with a `calc_id`; generators refuse to print an untraced number.
- Freezes are recorded in `decisions.md` with the gate, date and the frozen fields; generators warn when a frozen field changes without a change-request reference.
- Generators live in `library/templates/`: `gen_sheetlist.py`, `gen_dxf.py`, `gen_sheets.py` (HTML / SVG with the QA overlay), `gen_ifc.py`, `gen_e2k.py`, `gen_energyplus.py`, `gen_bq.py`, `gen_calcbook.py`. All read the DB (and the overrides register) only. There is no Revit generator: Revit is manual at S10 (`references/toolchain.md`).

## ID schemes, fixed at S0

The brief's version lock (`references/library-and-repos.md`) also fixes the ID schemes, written into `db/project.json` `id_schemes{}` and never changed afterwards:

| ID | Format | Issued by | Notes |
|---|---|---|---|
| `document_id` | `DOC-<DISC>-<NNNN>` (e.g. `DOC-MECH-0034`) | the Project Book on ADD | One per logical document (a sheet number, a calc ID, a stage calc book, a gate report, a model + release …); identity keys in `references/project-knowledge-base.md` |
| `revision_id` | `R01`, `R02` … per document | The Project Book on ADD / REVISE | Immutable; each revision carries its parent, reason, impact list and SHA-256; never reused, never edited |
| `asset_id` | `AST-<DISC>-<NNNN>` (`templates/asset-register.csv`) | Assigned at S5 when equipment is selected | Follows the physical asset through procurement, installation and operations; a replacement is a new asset with `replaces_asset_id` |
| `system_id` | The system key as the discipline file names it, scoped where a system is per level or per zone (e.g. `CHW-P`, `SA-L22`, `CW-Z3`) | The DB at S1 / S3 | Used as a knowledge-base scope value, in the pump-logic deliverables and in `services-routes.json` |
| `space_id` | The room / space `id` in `rooms.json` | The DB at S2 | Rooms, corridors, plant rooms, risers and shafts are all spaces |
| Calc ID | `<DISC>-<NNN>` (e.g. `H-014`) | The calc register | One row per calculation; the key of `calcs.json`, the calc book and the coverage file |
| Element id | Per-domain stable id (`W-L22-014`, `B-L03-007`, `DUCT-SA-L22-031`) | The generator that creates the element | Stable for the life of the project and never renumbered |

Element ids are never renumbered: an element that is deleted has its id retired (never reused); an element that is split becomes two new ids with `split_from` pointing at the old one; an element that is replaced keeps the lineage in `replaced_by` / `replaces`. The id-map and the release impact list carry the same lineage, so an IFC issue anchored to an old GlobalId can be relocated (`NEEDS_RELOCATION`, `references/ifc-review.md`) rather than lost.

## Dependency tracking per object

Every object in the DB carries, beside its design fields:

- `owner` — the field responsibility: the discipline or role that may change it (ARCH, STR, MECH, ELEC, HYD, FIRE, ID, VT, procurement, drafting-team, site);
- `source_revision` — the Project Book revision or the change request / write-back record the current value came from;
- `depends_on[]` — the ids (elements, calc IDs, assumptions, product SKUs, digest record ids) whose change would invalidate this object.

Generators read `depends_on` to compute the impact list of any change: the calcs, sheets, models, BQ lines and signed scopes that depend on the changed object. A change reruns only those dependents — nothing else — and that same list is the impact list written into the REVISE record and the change request. A calc with no `depends_on` on its inputs, or a sheet whose manifest cites an element it does not depend on, fails the DB consistency check.

## The overrides register — `drawings/overrides/<sheet>.json`

Manual edits to a generated output (a sheet, a schedule, a model) are recorded here, never made silently. One file per sheet (or per model / schedule, named the same way), one record per edited value:

```json
{"element_id": "DUCT-SA-L22-031", "field": "label.insulation", "generated_value": "25 mm", "manual_value": "38 mm external",
 "reason": "external run over the loading dock roof; matrix row EXT-DUCT applies", "design_change": "Y",
 "written_back": "N", "date": "2026-09-14", "by": "drafting-team"}
```

Fields: `element_id`, `field`, `generated_value`, `manual_value`, `reason`, `design_change` (Y / N), `written_back` (Y / N), `date`, `by`. Rules:

- Generators read the register before writing. A record with `design_change = N` (annotation, layout, view, a keyed note moved) is applied on top of the generated output every time, so manual detailing survives regeneration; a generator that overwrites such a record silently is defective.
- A record with `design_change = Y` is a pending write-back: the generated output is regenerated only after the DB has been updated (`written_back = Y`), at which point the generated value equals the manual value and the record is retired to the change log. A `Y / N` record older than the current gate is a gate finding.
- The register is the diff's audit trail: the write-back procedure below produces its records; nobody types them from memory.

## The id-map — `model/id-map.csv`

`db_id, ifc_global_id, revit_element_id, release_id, status, replaces, replaced_by, notes`

- One row per element that carries a DB id, from the first IFC release; the Revit ElementId column is filled by the drafting team at S10 from the first element they model, and stays their responsibility.
- `release_id` is the IFC release the GlobalId was issued in; `status` is one of `active`, `split`, `replaced`, `retired`. `split` and `replaced` rows keep the lineage in `replaces` / `replaced_by`, so an issue, a BQ row or an endorsement scope anchored to the old id can be followed to the new one.
- The cross-release key is `model_id` + GlobalId + DB id; a Revit ElementId or an IFC Express / localId is never used as a key (`references/ifc-review.md`).
- An element without a row is not traceable and is a defect in the drawing QA; the id-map is part of every S10 hand-off and every construction-record upload.

## 2D services-coordination inputs — `db/services-routes.json` and `db/crossings.json`

The combined-services sheets (C family), the corridor sections and the penetration schedule are generated from two DB files rather than drawn. The detailed format, tolerances and the per-stage content are in `references/services-coordination-2d.md` (being written by others); the outline:

- `services-routes.json` — one record per run: `system_id`, `family` (duct, pipe, tray, conduit, drain, sprinkler main …), `path` as a polyline in metres in the project coordinate system (metres here, not millimetres, because these runs are shared with the IFC and the viewer, which work in metres internally), `width_m` / `depth_m` or `dn`, `insulation` (material, thickness), `top_rl_m`, `bottom_rl_m`, the level and the corridor / zone it runs in, and the element ids of the segments it represents.
- `crossings.json` — the crossings register: every point where two runs cross or share a ceiling-zone band, with the two `system_id`s and element ids, the location in metres, the vertical order decided (which passes over), the clearance, the `resolution` (re-route, drop, offset, sleeve, accepted with clearance), the section sheet that shows it (`section_ref`, a C-3xx sheet) and the status.

These two files are the source of the S6 coordination plans and sections and of the S7 clash inputs; a crossing that is in the IFC clash report but not in `crossings.json` is a DB defect, not only a model finding.

## Write-back procedure from a manual diff

Used after every manual version of an output — a Revit model, a hand-edited sheet, a site redline, a vendor drawing that changed an interface (`references/stages.md`, S10; `references/ifc-review.md`, manual Revit hand-off):

1. Diff the manual version against the previous one (for Revit: the exported IFC / schedules against the previous release, by id-map; for a sheet: the SVG manifest and the graphics; for a redline: the marked items). Classify every difference by element id.
2. Annotation / view / layout only, engineering parameters unchanged → record "no design change" in the overrides register (`design_change = N`); nothing is rerun. The changed output is registered as a new revision in the catalogue with reason "no design change".
3. A design change — a dimension, load, material, equipment, interface, control or performance value, or a new anchor, support or penetration — → write the new value into the DB field by stable element id, with `source_revision` set to the write-back record; then, from `depends_on`, rerun only the affected calcs, regenerate only the affected sheets, models and BQ lines, and set `written_back = Y` on the override record.
4. New design content created manually (a support the DB did not have, a penetration added on site) is added to the DB as a new element with a new id and its dependencies, not left only in the output.
5. If a signed scope is affected (an endorsement whose `scope` includes the changed object), return that part to the S9 package for re-confirmation; unaffected endorsements remain valid. A later revision never inherits an endorsement.
6. Register the outputs through the Project Book connector (REVISE), impact list attached; publish only under the gate or release that governs them.

A generator overwriting a manual value that is not in the register, a manual change that is not diffed, and a design change recorded as "no design change" are all defects.
