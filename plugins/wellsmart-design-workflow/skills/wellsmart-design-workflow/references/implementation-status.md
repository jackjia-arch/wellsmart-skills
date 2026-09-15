# Implementation status — what the skill contains, what it describes but does not yet ship, and what to do when something named here is missing

The skill is the operating manual for the whole workflow: every stage, gate, rule, format, review layer, region rule, calculation row, drawing rule and knowledge-base procedure in the handbook (v2, 2026-09-14, plus the additions of 2026-09-15) has a home in `SKILL.md` or a reference file. It is not the whole company system: data, generators and the Project Book live elsewhere or are not built yet. This file says which is which so nobody mistakes a description for a tool.

## Ships inside the skill (runs today)

| Component | Where | Tested by |
|---|---|---|
| Two-model review loop: pre-check, blind / full packets, passes, states, severities, retention, coverage | `scripts/peer_review.py` | `demo <dir> --run`, mock provider |
| Calculation coverage: stage table from the master list, check, summary, HTML, blank template page | `scripts/calc_coverage.py` + `templates/calc-templates/` | `selftest` |
| 2D services coordination: envelope, crossings, depth budget, parallel clearance, drains, braces, SVG | `scripts/coord_check.py` + `templates/services-routes.example.json` / `crossings.example.json` | `selftest`, `demo` |
| Annotation engine and sheet checker; in-sheet QA overlay | `scripts/annotate.py`, `templates/qa-overlay.js` | `demo`, `check` |
| Every template named in `SKILL.md` (brief, DBR, calc register, gate report, compliance matrix, issue register and schema, decision record, release sheet, endorsement record, handover matrix, asset register, commissioning tests, results schema, CI workflow) | `templates/` | JSON validated; CSV headers fixed |

## Described in the skill, to be built in the company library or the project repo (not shipped)

These are named in the references because the workflow depends on them; they are scripts that read the design database and write outputs, and they belong in `wellsmart-design-library/` (shared) or `<project>/scripts/` (project-specific) — not in the skill, which stays small. Until they exist, the AI writes them in the project repo, following the schemas in `references/db-schema.md` and the formats in `templates/`, and the library takes them over once proven.

| Generator / checker | Purpose | Reference |
|---|---|---|
| `gen.py` family (`gen_sheets.py`, `gen_dxf.py`) | DB → HTML / SVG sheets with manifest and QA overlay; DB → DXF | `drawing-standards.md`, `drawing-list.md` |
| `gen_sheetlist.py` | stage sheet list and level–sheet–revision matrix from the DB | `drawing-list.md` |
| `gen_calcbook.py` | `calcs/` → stage calc book HTML + JSON export | `bq-and-calc-book.md` |
| `gen_bq.py` | IfcOpenShell quantities + installation detail → BQ (ESTIMATE / PROCUREMENT) | `bq-and-calc-book.md` |
| `gen_ifc.py` | DB → IFC with stable GlobalIds and DB ids; model checks | `ifc-review.md`, `toolchain.md` |
| `gen_energyplus.py` | DB → IDF, run, `results.json` v2 | `toolchain.md` |
| `check_sheets.py`, `check_citations.py` | sheet content cross-checks; every citation resolves to a digest record | `sheet-content-checklists.md`, `standards-digest.md` |
| `digest_query.py`, `build_index.py`, `diff_editions.py` | standards digest query, index and edition diff | `standards-digest.md` |
| discipline calc scripts (`mech_oa.py`, `mech_duct.py`, `elec_demand.py`, `hyd_zoning.py`, …) | the checks library — "the most valuable part of the skill" — one script per master-list row family | `calc-coverage.md`, `disciplines.md` |

Data that is never in the skill: the design library (modules, products, details, lessons, cost), the standards digest and source PDFs, project databases.

## Provided by the Well Smart Project Book (IT brief V1.1, 2026-09-15), not by the skill

In V1.1: company-email identity, the three entries (announcements, project design, design progress), documents with stable ids and revisions carrying mandatory notes, current-by-use with automatic archiving, permanent history and restore, attachments ≤ 20 MB and Drive links above, per-page comments with review links to the PD and email alerts, search, backups, the one MCP connector with `list_projects · search · fetch · create_draft · upload_attachment · add_drive_link · publish_revision · list_history · restore_revision · create_review_link · list_comments · add_comment · reply_comment · update_comment_status`. Not in V1.1 (report as `UNVERIFIED — Project Book <feature>`): a release object, a separate endorsement object, asset / O&M records, the 3D viewer with picking, RAG over Drive-linked files. The skill states the contract (`project-book.md`, `project-knowledge-base.md`, `ifc-review.md`, `ui-guidance.md`) and uses the connector; nothing is worked around with a substitute.

## Rule when something named here is missing

A missing generator is never a reason to skip the output or to hand-draw it. The AI states in the stage report which named tool is absent, writes the minimum script in `<project>/scripts/` that produces the output from the DB in the required format, runs it, and records the script name and version on the calc page or sheet manifest. A missing tool that cannot be written in the session (EnergyPlus engine, OpenSees, a vendor selection tool) makes the affected rows `NOT CALCULATED` with the tool as the missing input (`calc-coverage.md`, rule 9). A missing Project Book capability is reported as `UNVERIFIED — Project Book`; outputs wait in `kb-outbox/` until they can be registered (`project-book.md`).
