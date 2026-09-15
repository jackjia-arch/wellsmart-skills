# WELLSMART PROJECTBOOK (Well Smart Project Book) — the single publishing path, and how the AI uses it

The Well Smart Project Book is the company's own information platform (IT development brief V1.1, 2026-09-15): one company entry point where every announcement, project design output and design-progress note is published, revised, discussed and searched. It runs in Docker on the company Linux box (Python FastAPI + MCP service, PostgreSQL, Caddy, Cloudflare Tunnel, originals on a persistent mount) under the company domain. Staff sign in with their company email (magic-link verification; accounts created by IT from the HR list, no open registration); the boss and IT are administrators. The AI reaches it through **one connector — "Well Smart Project Book"** — an MCP server the staff member authorises once under their own identity (built first for the OpenAI connector; the same MCP endpoint is what Claude uses as a custom connector). Nothing else publishes: no static sites, no deployments, no Drive folders as "the record", no local catalogues. A page being published is a document fact; it never means engineering PASS, endorsement, construction issue or acceptance.

## The three entries

| Entry | What goes there | The workflow's use |
|---|---|---|
| Company announcements 公司公告 | Notices, policies, internal arrangements; effective dates; withdrawn items keep their history | Not a workflow output (the PD / PM post these) |
| Project design 项目设计 | Schemes, HTML reports, drawings, calculations, consultant-signed files and their attachments | Every stage output: sheets, calc books, coverage tables, gate reports, decision records, BQ, release sheets, IFC releases, endorsement records, asset and handover records |
| Design progress 设计进展 | Done / next / blockers / owner / target date, each linked to the outputs | One entry per gate (and per review round that changes state), written by the AI from the gate report |

## The connector's tools and what the workflow does with them

Tool names as specified in the brief (V1.1); read the live tool list before calling — names may differ slightly in the build.

| Tool | Workflow use |
|---|---|
| `list_projects` | Find the `project_id` for the project named in the prompt; never guess. |
| `search`, `fetch` | Read back current content before a stage (last gate report, current revisions of the sheets and calcs in scope, open comment threads); cite `document_id`, `revision_id` and section. History only when explicitly asked. |
| `create_draft` | Start a new document (ADD) or a revision of an existing one (REVISE — from the existing `document_id`, never a new document for a changed file). The HTML body, the discipline / stage / use fields and the title go here. |
| `upload_attachment` | Files ≤ 20,000,000 bytes (exactly 20 MB allowed), one file at a time, bound to the draft revision; the server records name, type, bytes, uploader and SHA-256. |
| `add_drive_link` | Files > 20 MB: upload to the company Google Drive first, then register the link with name, size and description; the Project Book stores the link record only and flags "external, body not indexed". A file that will be overwritten in Drive is not a record — register a stable version file / file ID. |
| `publish_revision` | Publish with the mandatory revision note (below). Refused when the note or the author is missing; the author is the authorised staff identity (the operator), never a name typed by the AI. Returns the stable link and the revision link; nothing is "published" until they come back. |
| `list_history`, `restore_revision` | Read the revision chain; a restore is a new revision with author and reason, never a silent rewind. |
| `create_review_link` | After a gate report or a package is published: a link bound to that revision, addressed to the PD (or the checker), registered with submitter and revision — this is how the human layer is asked to read. |
| `list_comments`, `add_comment`, `reply_comment`, `update_comment_status` | Read the PD's / colleagues' comments on a page; draft and post replies under the operator's identity, marked AI-assisted; set status only to "replied" — "resolved" is set by the person who raised the comment or the named PD, never by the AI. |

## The mandatory revision note (`templates/revision-note.md`)

Every `publish_revision` carries: R01 — "first publication" plus the main content; later revisions — what changed, why, and which content it affects (the impact list from the DB dependency graph: calcs, sheets, models, BQ lines, signed scopes), plus the stage / task, the AI-assisted flag and the checks run. An empty or generic note ("updated", "minor changes") is refused by the platform and is a defect in the workflow. Attachment-only changes are still a revision with a note. Comments never create revisions; a design change raised in a comment thread is answered by a new revision linked from the thread.

## What a published HTML must be

Self-contained: inline CSS, inline SVG for drawings and charts, no script needed to read it, no local file paths, no links to the operator's computer; raster images either as attachments referenced by their Project Book URLs or as small data URIs; the sheet manifest and the QA counts present but not required for reading. The Project Book adds the outer page (author, time, revision history, attachment cards, the comments section) around the HTML — the AI never builds its own comment or header UI into a document. Attachments (PDF, DWG, IFC, CSV, JSON) are uploaded as files, not embedded.

## Where the workflow's records live in V1.1

| Workflow record | In the Project Book (V1.1) |
|---|---|
| `document_id` / `revision_id` / SHA-256 / current per use (design · construction · operations) | Native: stable document links, revisions with notes, current-by-use with automatic archiving of the superseded effective revision, permanent history, conflict detection on concurrent edits |
| Gate report, calc book, coverage table, sheets, BQ, decision records | Project-design documents (HTML + attachments) |
| Design-progress entry per gate | Design-progress entry |
| Human review at a gate (PD reads the high-risk table) | `create_review_link` → PD comments → threads with status; the comment thread is the record of the human layer |
| Consultant endorsement record (`templates/endorsement-record.json`) | A revision of the signed document with the signed original and covering letter as attachments (or Drive links > 20 MB) and the endorsement fields in the revision note; V1.1 has no separate endorsement object — the record JSON is attached as a file, and "consultant-endorsed" is stated in the note for that exact revision only |
| Project release manifest (`project_release_id`, list of document / revision / hash) | Published as a document ("Release <id>") whose body is the manifest; V1.1 has no release operation — `UNVERIFIED — Project Book release` until one exists |
| IFC issues (`wsg.issue/1`), 3D viewer with picking | Not in V1.1. Issues are JSON files under `issues/` in the repository published as attachments of the release document; the viewer is a future Project Book feature — every reference to it is `UNVERIFIED — Project Book viewer` |
| Asset cards, O&M, handover matrix status, Handover Baseline | Documents and attachments in V1.1; dedicated asset records are a later phase (the brief lists operations records as "continue later") |
| Search / RAG answers | The Project Book's search over current bodies, attachments as extracted, comments as "discussion"; Drive-linked files are metadata only until read |

## How the AI uses it at every stage

1. Before working: `list_projects` → `search` / `fetch` the current records for the stage; read open comment threads on the last gate report and on the sheets in scope; unresolved PD comments are inputs.
2. After producing outputs: for each output decide ADD or REVISE by identity (sheet number, calc ID, book, report, decision id) — never by filename; `create_draft` with the self-contained HTML; `upload_attachment` / `add_drive_link` for files; `publish_revision` with the full revision note; collect the stable and revision links into the gate report.
3. Publish the design-progress entry for the gate (done / next / blockers / owner / date, with links), then `create_review_link` to the PD for the gate report. Report back: what was published (links), what the PD must decide, which comment threads are open.
4. Answering comments: read the thread, change the DB and regenerate if a design change is needed, publish the revision, `reply_comment` with the revision link and the closure evidence under the operator's identity marked AI-assisted, set status "replied". Never set "resolved". Never treat a comment as an endorsement or a signature.
5. Reading back for any question: cite document, revision, section; say "not registered" when it is not there.

The fixed sentence staff say: "把任务 XXX 的新增 / 修改产物加入项目 YYY 的原知识库，匹配 document_id，保留所有未改内容；先返回入库草稿链接和影响清单，正式生效按已有 gate 执行。" In V1.1 terms: drafts through `create_draft`, the impact list in the revision note, `publish_revision` only for the outputs the current gate governs.

## When the connector is not in the session

Outputs are still produced in the project repository; registration is reported as **not done**. The AI writes `kb-outbox/<task>/manifest.json` (per file: path, SHA-256, ADD / REVISE, the `document_id` to match where known, stage, task, the revision note text, the impact list) and says the batch is waiting for the Project Book. The next session with the connector publishes the outbox first. No other channel stands in.

## Defects

Publishing under a name the operator did not authorise; a revision note that does not say what changed and what it affects; splitting one logical document into new documents on each update; embedding attachments as base64 or leaving local paths in the HTML; treating a page, a comment or a "replied" status as an endorsement, a construction issue or an acceptance; setting a comment to "resolved"; claiming a Project Book feature (viewer, release object, asset records, RAG over Drive files) that V1.1 does not have.
