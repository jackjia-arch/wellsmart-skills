# The ProjectBook — where every output is published, and how the AI uses it

The ProjectBook is Well Smart's own project knowledge base: one permanent page per project, from S0 through construction and operations, reached by staff in the browser and by the AI through the **ProjectBook connector** (a Well Smart plugin / MCP connector). It replaces every other way of publishing: no static site builds, no deployment, no separate hosting, no company server, no local catalogue. Whatever the AI produces — sheets, calc books, gate reports, coverage tables, IFC releases, BQ, decision records, endorsement records — reaches people only by being registered in the ProjectBook.

## What the connector does

The connector exposes the ProjectBook's operations as tools. Their exact names come from the plugin as installed in the session — read the tool list, never guess names. The operations the workflow relies on, and the rules that apply whichever tool implements them:

| Operation | Rule |
|---|---|
| ADD | Creates a new `document_id` with its first immutable `revision_id` and SHA-256. Used only for a document that does not exist yet; the AI checks for an existing `document_id` (same sheet number, calc ID, book, report) before adding. |
| REVISE | New immutable revision of an existing `document_id`, with parent, reason and impact list. Never overwrites; never moves a current pointer by itself. |
| ATTACH | Evidence bound to an exact revision or asset (endorsement letter, photo, approval, test record). The main file is unchanged; an endorsement marks only the covered revision `consultant-endorsed`. |
| Publish effective | Switches `current_design` / `current_construction` / `current_operations` for a scope to a revision, with the gate / issue / acceptance evidence named. Done only under the gate or release that governs it; a draft never becomes current on upload. |
| Release | Freezes a `project_release_id` → full list of `document_id` / `revision_id` / SHA-256 (viewer releases, package releases, the S9 package, the Handover Baseline). |
| Issues | `wsg.issue/1` records from the 3D viewer and their states (`references/ifc-review.md`). |
| Assets / handover | Asset cards, handover matrix status, Handover Baseline acceptance (`references/project-knowledge-base.md`). |

The fixed sentence staff say (and the AI executes through the connector): "把任务 XXX 的新增 / 修改产物加入项目 YYY 的原知识库，匹配 document_id，保留所有未改内容；先返回入库草稿链接和影响清单，正式生效按已有 gate 执行。"

## How the AI uses it at every stage

1. Before working: read the project's current records for the stage (last gate report, open issues, current revisions of the sheets and calcs in scope) from the ProjectBook, not from memory or a local copy.
2. After producing outputs: register them — ADD for new documents, REVISE for existing ones, ATTACH for evidence — with `document_id` matched, the impact list from the DB dependency graph, and the stage / task named. Return the draft links and the impact list to the operator.
3. Never publish as current: the gate or release does that. A PASS, an endorsement, a manufacturing release and a publication remain four different facts.
4. Every HTML the AI publishes is self-contained and readable without JavaScript (prose, tables and links in plain HTML; SVG inline with true scale, sheet number, calc IDs and visible data tables; the manifest JSON present but not required for reading), so the ProjectBook's index, search and other AI models can read it directly.
5. Reading back: cite `document_id`, `revision_id`, page / calc ID and the use (design / construction / operations); history only when explicitly asked; conflicts and gaps shown, never smoothed over.

## When the connector is not in the session

The outputs still get produced in the project repository; registration is reported as **not done**, never as done. The AI writes `kb-outbox/<task>/manifest.json` — for each file: path, SHA-256, intended operation (ADD / REVISE / ATTACH), the `document_id` to match where known, the stage and task, the impact list — and tells the operator that the batch is waiting to be registered through the ProjectBook. The next session with the connector registers the outbox first. Nothing else stands in for the ProjectBook: no local catalogue, no static site, no "published to Drive".

## What is not the skill's business

How the ProjectBook stores, hosts, backs up and renders is the product's concern (Jack's ProjectBook project), not the workflow's. The workflow only requires the semantics in the table above and in `references/project-knowledge-base.md`: stable ids, immutable revisions with hashes, current by use and scope, atomic publish, permanent history, endorsements bound to exact revisions, assets and handover records. If the ProjectBook cannot yet do one of them, the AI says so in the stage report as `UNVERIFIED — ProjectBook` and does not invent a substitute.
