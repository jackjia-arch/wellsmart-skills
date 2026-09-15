# Company library, repositories and the knowledge base

The library does not live inside this skill. The skill is operating instructions plus small templates and must stay small; the library is data that changes all the time. Three repositories and one knowledge base; this skill holds only their paths and schemas. Anyone can change the library without touching the skill. On a new project the skill reads `library/index.md` first and queries the knowledge base before citing any clause.

## What the library is

The company's own parts bin, rule book and memory: when the AI gets a new project it looks here first, uses what exists and designs only what does not. Jack maintains it; the seed is the 372 Pitt Street documents 01–27, the bathroom pod set P7, the cassette set P4 and the Lindeman modular work.

| Part | Content | Each entry is |
|---|---|---|
| 1 Design modules (kit of parts) | Room modules (the 20 m² room with the BAR finishes version, villa room types), bathroom pods, the 6 m corridor services module, riser cassettes, plant-room typicals (pump room, switchroom, fire pump room, AHU level), core / stair typicals, loading-dock typical | DB fragment + drawings + IFC + spec + cost |
| 2 Product library (preferred products) | The selected product per category with datasheet, curves, dimensions and weight, price (FOB / landed), lead time, certification status (WaterMark / RCM / WELS / ActivFire / NATA reports) and supplier; Kaiquan pumps, Gree FCUs and the MOS modules go in first | One row in `products/index.csv` + a folder per SKU; maintained by procurement |
| 3 Typical details (with test reports) | Fire stopping (firebox), waterproofing, façade interfaces, pod interfaces, supports | A detail linked to its test report and its dual-certification status |
| 4 Rules and check scripts | Discipline design rules (20 / 18 L/s ventilation, NR38, the 250–500 kPa pressure window …), check scripts, compliance checklists, the drawing content standards | A rule with its source, a script with its test; the most valuable part of the skill |
| 5 Templates | Brief, DBR, calc register (one page per calc), gate report, compliance matrix, issue register, RFQ, specification sections, certification pack; drawing templates, DXF layer standard, sheet generator | Copied, never re-invented |
| 6 Decisions and lessons | Situation + decision + reason (the VE register governs BQ lines; a supplier having stock is not a design decision; grease arrestors are sized by covers) | One file per lesson |
| 7 Standards text (knowledge base) | The full AS/NZS set from Jack's Google Drive + NCC + NZBC AS / VM in the Dify / Claude Project knowledge base, with the standards digest built on top (`references/standards-digest.md`) | A clause the AI may cite only because it has source text |

## Repositories and the knowledge base

```
wellsmart-skills/                      (GitHub) — this skill and future ones; the planned implementation package
└── wellsmart-design-workflow/
    ├── SKILL.md
    ├── references/   templates/   scripts/   deploy/   evals/

wellsmart-design-library/              (GitHub) — the company library
├── index.md                           what exists, one line each, with paths and versions
├── modules/                           kit of parts: <module>/  db.json · drawings/ · model.ifc · spec.md · cost.csv · README.md
├── details/                           typical details with test reports and dual-cert status
├── products/
│   ├── index.csv                      one row per SKU (schema below); datasheet links point to Drive
│   └── <sku>/                         curves.csv · dimensions.json · certs.md
├── checks/                            deterministic check scripts, each with a test
├── templates/                         drawing templates, DXF layer standard, the generators (gen_*.py)
├── rules/                             discipline design rules with source; bq-ratios.csv
├── lessons/                           situation + decision + reason, one file per lesson
├── cost/                              cost library used by the BQ and cost plans
└── standards/                         the digest: index/ digest/ text/ tests/ digest_query.py

<project-code>/                        one repository per project
├── brief/  site/  db/  calcs/  drawings/  model/  thermal/  reports/  issues/  reviews/
├── decisions.md
└── catalogue.json                     the project knowledge-base catalogue (scripts/catalogue.py)
```

Where the project repository lives: the working files sit in the shared Google Drive `Projects` sync folder, so Cowork (through the Drive connector or the linked computer) and Claude Code (local shell) see the same files, and the company server mounts the same folder for the runner (`references/hosting.md`). Git lives on the server — the runner keeps the repository as a bare snapshot in `/srv/git/<project>` — and the `.git` directory is never synced through Drive; staff never run git. Formal records (every stage output, revision and endorsement) are registered in the project knowledge base by ID (`references/project-knowledge-base.md`); the Drive folder is the working copy, not the record.

Knowledge base (Dify / Claude Project): the AS/NZS standards, NCC volumes with state variations, NZBC acceptable solutions and verification methods, product datasheets, test reports and the lessons folder, indexed by standard number and year. Standards ingestion is Dong's task: the PDFs are shared from Jack's Drive to the company account, loaded and indexed. Citing rule: query the knowledge base (or the digest, `references/standards-digest.md`) before citing any clause; every citation carries standard number, year, clause and the digest record id where one exists; text not found → `CLAUSE TO CONFIRM`, listed in the gate report — never a clause from memory.

## Product index schema (`products/index.csv`)

`sku, category, description, supplier, origin, datasheet_url, curve_file, dimensions_json, weight_kg, electrical_kW, noise_dBA, price_fob, price_landed, currency, lead_time_weeks, cert_watermark, cert_rcm, cert_wels, cert_activfire, nata_report, dual_cert_status, last_verified, notes`

Rules: design with what procurement can buy — a product not in the index needs a procurement note before it is specified; dual-certification status must be `complete` before an item is written into an S6 schedule; fire pumpsets, hydrant / sprinkler valves, fire-rated cables, smoke-control fans, essential switchboard sections and dry fire are local-only categories; `last_verified` is the product-data date the project's version lock records.

## Project version lock

At S0 the brief records, and G0 freezes, every version the project depends on: standard editions and amendments, state variations, the digest version and hash per standard, the library module versions (`modules/<module>/README.md` version), the product-data dates (`last_verified` per selected SKU), and the calculation script / tool versions (checks, generators, IfcOpenShell, EnergyPlus, OpenSeesPy, the annotation engine). The same list sits in `db/project.json` `version_lock{}` (`references/db-schema.md`) and on the cover of every calc book.

The project uses these fixed versions. Library updates — a new digest edition, a revised module, a product whose datasheet or price changed, a corrected check script — never overwrite a running project. The update produces an **impact list**: which locked items changed, and which calcs, sheets, models, selections and BQ lines of the project cite them (from `depends_on` and the digest record ids in `calcs.json`). Migration happens only after the gate that governs the affected items approves it, and then only the affected content is rerun and regenerated; the gate report records the new lock. A project may finish on its locked versions with the impact list filed as a known difference. A corrected check script that would change a PASS to a FAIL is never held back by this rule: it is raised as an issue at once, and the project decides at the gate how to close it.

Two-model extraction agreement in the digest is recorded as agreement, not truth: the key clauses, applicability conditions, table notes and exceptions are verified on the source page before a digest version is released, and the project locks a released version only (`references/standards-digest.md`).

The update procedure, in order:

1. The library owner (procurement for products, the PD for rules and lessons, Dong for the digest, whoever wrote a check for its test) releases the new version in the library with a change note; the running project's lock is untouched.
2. The AI operator runs the impact check for the project: locked item → new version → every project object that cites it (`depends_on`, `digest_record_id`, `sku`, `module_ref`), listed as calcs / sheets / models / selections / BQ lines / signed scopes, with the value that would change where it is known.
3. The impact list goes into the next gate report under "decisions this stage" with a recommendation: migrate now, migrate at a named later gate, or finish on the locked versions.
4. On the PD's approval at that gate, the lock is rewritten in the brief and `db/project.json`, the affected content only is rerun and regenerated, the outputs are registered as new revisions with the impact list as the reason, and any affected signed scope returns to S9 for re-confirmation.
5. Nothing migrates without steps 3 and 4; a library change applied to a project "because it is newer" is a defect, and so is a gate report that omits a known impact list.

## How the skill uses the library

- At S0 read `library/index.md`, record which modules, products, rules and digest versions apply to the project, and write the version lock.
- At S1 / S2 place room modules and typicals from `modules/` before designing anything new; new modules created for a project are contributed back with a README and a version.
- At S5 select only from `products/index.csv`; anything else is an RFQ to procurement first; the selected SKUs' `last_verified` dates go into the lock.
- At S6 pull typical details from `details/` (each with its test report and dual-cert status); non-typical details are drafted and flagged for human buildability review.
- At S8 run every script in `checks/` that applies to the stage; a new check written during the project goes back into `checks/` with a test.
- After every project, add lessons to `lessons/`: situation, decision, reason.

## Seeding the library

Start from what already exists: the 372 Pitt Street documents 01–27 (ventilation, cassettes, corridor module, materials matrix, wall types, basement ventilation), the bathroom pod set P7, the cassette set P4, the Lindeman modular work, the Kaiquan pump curves (digitised into `products/<sku>/curves.csv` before the first pump selection), the Gree FCU parameters, the MOS riser modules. Procurement owns `products/`; the PD owns `rules/` and `lessons/`; whoever writes a check owns its test; Dong owns `standards/` ingestion and the digest builds.
