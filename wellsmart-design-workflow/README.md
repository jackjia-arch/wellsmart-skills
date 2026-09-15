# wellsmart-skills

Skills for Well Smart's AI-operated design workflow. Each folder is one skill: a `SKILL.md` (instructions the AI reads when the skill triggers) plus `references/` (read on demand), `templates/`, `scripts/` and, for the company-server pilot, `deploy/`.

## Install

**Claude Code (desktop app Code feature or terminal)** — clone this repository and copy or symlink the skill folder into a skills directory:

- personal: `~/.claude/skills/wellsmart-design-workflow/`
- per project: `<project-repo>/.claude/skills/wellsmart-design-workflow/`

Claude Code lists it under available skills; it triggers on design-workflow requests automatically, or on request by name.

**Claude.ai / Cowork** — upload the packaged `wellsmart-design-workflow.skill` file (Settings → Capabilities → Skills, or the Save skill button on a shared skill file). Repackage after editing with the skill-creator packager or by zipping the folder.

## Layout

```
wellsmart-design-workflow/
├── SKILL.md                     the workflow: 18 hard rules, roles, stage map, output formats
├── references/
│   ├── stages.md                S0–S10 and after: inputs, AI work, outputs, freezes, people; manual Revit; write-back; handover
│   ├── disciplines.md           what each discipline produces and calculates; pump logic; structural steps; thermal split
│   ├── review-and-gates.md      four review layers, high-risk table (v2 columns and statuses), seeded-defect validation, review states
│   ├── review-hub.md            the two-model review loop: blind / full packets, passes, states, retention, server and CI variants
│   ├── certification.md         regions (QLD RPEQ, NSW DBP, NZ PS1/PS2, Japan), packages A / B / C, ten contract items, endorsements
│   ├── calc-coverage.md         the "no silent omission" rule: master list, coverage file, statuses, filling rules
│   ├── operator-prompts.md      what the PM / operator types at each step (中文 + English); the skill carries the rest
│   ├── services-coordination-2d.md  2D clash avoidance before 3D: lanes, ceiling-zone budget, crossings register, per-stage MEP drawing spec
│   ├── drawing-standards.md     numbering, depth benchmark (HY-0040), annotation, QA overlay, manifest
│   ├── drawing-list.md          sheets per checkpoint and per level; level–sheet–revision matrix
│   ├── drawing-prompts.md       sheet-list prompt, per-sheet prompt skeleton, reviewer drawing prompt
│   ├── sheet-content-checklists.md  what every sheet type must show, coordination content, cross-checks, never-again list
│   ├── annotation-rules.md      twelve annotation rules, the defect catalogue, declare → lay out → check
│   ├── bq-and-calc-book.md      BQ ESTIMATE vs PROCUREMENT, stage calc book, decision records (simple annual return)
│   ├── ifc-review.md            IfcOpenShell / That Open / Bonsai, coordinate contract, wsg.issue/1, states, acceptance, manual Revit hand-off
│   ├── project-knowledge-base.md  ADD / REVISE / ATTACH, current_by_use, publish-effective, endorsements, assets, handover
│   ├── hosting.md               PILOT (company server, deploy/) vs TARGET (Netlify portal + Runner / API + PostgreSQL + S3, UNVERIFIED)
│   ├── ui-guidance.md           Part II: tokens, six views, status semantics, components, engineering content, builder prompt, verification
│   ├── toolchain.md             open-source toolchain; EnergyPlus staff guide and results.json v2; OpenSees / .e2k
│   ├── library-and-repos.md     company library, repositories, knowledge base, project version lock
│   ├── standards-digest.md      standards digest levels, extraction agreement, version lock
│   └── db-schema.md             design database, IDs, dependencies, overrides register, id-map, services routes
├── scripts/
│   ├── peer_review.py           review loop: pre-check → blind packet → review passes → responses; states; P0–P3; demo / selfcheck
│   ├── catalogue.py             knowledge-base catalogue (pilot): add / revise / attach / publish / release / list / history / check
│   ├── calc_coverage.py         coverage file per stage from the calc master list: init / check / summary / html / blank
│   ├── coord_check.py           2D services coordination checker: envelope, crossings, depth budget, parallel clearance, drains; SVG
│   └── annotate.py              annotation engine (aligned columns, non-crossing leaders, keyed notes) + sheet checker
├── templates/
│   ├── calc-templates/          calc-master-list.csv (223 rows, 13 disciplines), calc-page.md (the per-calc page format)
│   ├── brief.md · design-basis-report.md · calc-register.csv · compliance-matrix.csv · gate-report.md
│   ├── issue-register.csv · issue.schema.json · decision-record.md · release-sheet.md · endorsement-record.json
│   ├── handover-matrix.csv · asset-register.csv · commissioning-tests.csv · results.schema.json
│   ├── services-routes.example.json · crossings.example.json
│   ├── qa-overlay.js            the in-sheet QA script
│   └── review-on-tag.yml        optional GitHub Actions review trigger
├── deploy/                      company server pilot: docker-compose (runner + Caddy + Cloudflare Tunnel), runner.py (folder-drop review
│                                requests, sheet QA, book builds), rclone mount unit, README-IT (中文)
└── evals/evals.json             test prompts
```

## What lives elsewhere

The company library (`wellsmart-design-library`: modules, products, details, checks, rules, lessons, cost, standards digest), the standards knowledge base (AS/NZS, NCC, NZBC PDFs in Dify / the Claude Project) and the project knowledge base (ProjectBook portal, UNVERIFIED until built; `scripts/catalogue.py` and `deploy/` in the meantime) are separate. The skill references their paths and schemas; they change without touching the skill.

## Maintaining

Edit Markdown, commit, re-copy or re-package. Keep `SKILL.md` under about 500 lines; put detail in `references/`. Record decisions that change the process in the handbook first, then here. Run the script self-tests before packaging: `python3 scripts/peer_review.py demo <dir> --run`, `python3 scripts/catalogue.py selftest`, `python3 scripts/calc_coverage.py selftest`, `python3 scripts/coord_check.py selftest`, `python3 scripts/annotate.py demo <out.html>`.
