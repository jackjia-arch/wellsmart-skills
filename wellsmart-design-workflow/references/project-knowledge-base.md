# Project knowledge base — ADD / REVISE / ATTACH, current by use, releases, endorsements, assets, handover

One project, one permanent URL, from design to operations. `/projects/<project_id>/` is created at S0 and is the address the operations team still opens years after handover. Files accumulate: every stage output, review round, consultant response, construction record and maintenance job is merged into the same catalogue by ID. Nothing is ever replaced by a new folder, a new site or a zip assembled at completion; the knowledge base is only ever added to or revised. Public browsing needs no login. Staff add, revise or attach through the project page; the AI registers its outputs through the same ingestion service the staff form uses — there is no private AI path into the catalogue. IT maintains the platform (`references/hosting.md`); the PM owns the catalogue until handover, the Operation Owner afterwards.

Status: the portal — ProjectBook workbench, Runner / API, PostgreSQL catalogue, S3 originals — is specified, not built; its end-to-end status is UNVERIFIED. Until it is live the AI uses `scripts/catalogue.py` on `catalogue.json` in the project repository with the same semantics, and the company-server runner in `deploy/` publishes the static book. Everything below that names the portal is the contract the pilot substitute imitates, so IDs created now carry over unchanged.

## Who owns what

| Role | Responsibility in the knowledge base |
|---|---|
| PM (named at S0) | The catalogue: S0 handover matrix, document identity decisions, endorsement registration, the monthly exception check (20-minute target), the Handover Baseline; acts as Operation Owner until one is appointed |
| Operation Owner (named at S0) | Co-freezes the Handover Baseline; owns `current_operations`, the monthly check, exceptions and backup oversight after handover |
| AI operator | Registers every stage output with the fixed sentence; returns draft links and impact lists; never publishes on its own |
| Person with process authority | Presses "Publish as current effective" for a use and scope, with the gate / issue / acceptance evidence |
| IT / Dong | Platform, scheduled jobs, backups, the monthly restore test, the WSG ingestion connector |
| Site / contractors / vendors | Construction records, installed equipment, serials, tests, O&M — against the asset and document IDs given to them in RFQ / PO |

## The staff procedure — only this task's new or changed content

1. **Open the project's original URL** and confirm the project name in the page header. "Open project workbench" is the bookmark IT delivered once, connected to the company's existing authorisation entry; day-to-day work uses the authorisation staff already have. No registration, no new login page; browsing stays public. (The short-lived workbench session is issued by the company's WSG ingestion connector — UNVERIFIED until that integration is connected.)
2. **Choose the action.** New material → "Upload new content" (creates a new entry). A change to an existing file → open that file's card → "Upload new version" (carries the original `document_id` automatically). Consultant letters, photos, approvals, test records → the card's "Add attachment" (evidence; never replaces the main file).
3. **Drag in only the files or folder this task added or changed.** Never the whole project. AI-produced HTML, calcs, drawings, IFC and BQ can go in together; a set of interdependent changes is one submission (one package). Output that is still on the company Runner is handed to the same ingestion interface by the AI directly — no download and re-upload.
4. **Check the AI-prefilled mapping**: project, discipline, level / system, file name and revision correspondence. Every item is labelled ADD / REVISE / ATTACH on screen. When the correspondence is uncertain, pick the existing document or confirm a new one; the system never overwrites on a filename match alone. A repeat submission of the same logical file shows "already exists" and creates no duplicate revision; identical bytes are reused by hash. A manual that now covers another asset, or a letter that covers another exact revision, still gets its own new attachment / scope relation.
5. **Read the merge preview**, e.g. "added 2 · revised 1 · attached 1 · retained 38 · deleted 0" (example), then "Submit to project". Retained items come from the existing catalogue and are not re-uploaded; chapters, models and history not in this submission stay as they were.
6. **The submission lands as a draft / pending item.** To make it effective, a person with the existing process authority presses "Publish as current effective" on the preview page; the system checks the corresponding gate, issue closure, construction-issue or acceptance basis before it switches anything.
7. **The hand-off has succeeded only when the server returns the document number and link.** The page shows separate status cards: "original stored", "converting", "awaiting review", "current effective", "failed". A failed conversion can be retried and is never shown as published; until the required derivatives and references exist, the previous current revision stays in force. Next time, come back to the same URL and add more.

## The fixed sentence for the AI

Staff say: "把任务 XXX 的新增 / 修改产物加入项目 YYY 的原知识库，匹配 document_id，保留所有未改内容；先返回入库草稿链接和影响清单，正式生效按已有 gate 执行。"

The AI then:

1. Reads `catalogue.json` (or the catalogue API) for project YYY and lists what task XXX produced or changed since its last registration.
2. Matches each output to an existing `document_id` by identity fields — sheet number, calc ID, model id, report type plus scope, asset id — never by filename alone. No match → ADD. Match with changed bytes → REVISE with the parent revision. Identical hash → "already exists", no new revision. Evidence → ATTACH to the exact revision or asset.
3. Writes the impact list for every REVISE: the calcs, sheets, models, BQ lines and signed scopes that depend on the changed object. Only an engineering change updates the DB and reruns dependents; a letter, a photo, a completed form or an annotation-only file triggers no recalculation.
4. Submits the batch as drafts and returns the draft links and the impact list. It does not publish. Publishing happens under the gate or release that governs the content, by the person with that authority (`publish_effective`, or `scripts/catalogue.py publish` in the pilot).

| Document family | Identity key for the match | Typical revision trigger |
|---|---|---|
| Drawing sheet | Sheet number (`A-…`, `M-…`, `HY-0040`) + project | Regenerated sheet with changed graphics or data; annotation-only changes are still a new revision, recorded "no design change" |
| Calculation page | Calc ID `<DISC>-<NNN>` | Rerun with changed inputs, method or clause |
| Stage calc book | `CALC-BOOK_<project>_<stage>` (one document per stage) | Each regeneration for that stage |
| Gate report | Gate id (G0–G7) | A re-issued report for the same gate |
| Decision record | `D-NNN` | A revised decision |
| IFC model / Fragments | `model_id` (ARCH / STR / MEP …) + release | Every release; the `.frag` is a derivative of the IFC revision, never a document of its own |
| BQ, RFQ pack, release sheet | Stage or package id (`BQ (ESTIMATE)` S6, `BQ (PROCUREMENT)` per package, `release-sheet <package>`) | Regeneration at the same revision as the drawings it prices |
| Review round | Task + round (`reviews/<task>/round-<n>`) | Never revised — each round is a new record attached to the frozen package |
| Endorsement, approval, test, photo | Always ATTACH to the exact `revision_id` or `asset_id` it covers | A second letter for another revision is a new attachment, not a revision |
| Asset | `asset_id` | Vendor confirmation, installation, commissioning, replacement (new instance) |

Scopes: a current pointer is addressed by (use, scope). Scope values come from a fixed set — whole project, a level id, a system id, a discipline, a procurement package id, or a named package such as "S9 package" — written exactly as the DB names them (`references/db-schema.md`), so a pointer for "L22 / CHW" cannot be confused with one for "L22 / HHW".

## Operations — the catalogue grows, identities stay stable

| Operation | System action | How old content is preserved |
|---|---|---|
| ADD | Creates `document_id` and the first immutable `revision_id`; indexes discipline, system, asset and task | Every other document, chapter and relation keeps its existing links |
| REVISE | Same `document_id`; new immutable `revision_id` with parent revision, reason, impact list and SHA-256 | The old revision is not overwritten; a use's current pointer moves only when the new revision is published for that use |
| ATTACH | Creates evidence (endorsement letter, photo, approval, test record) bound to an exact `revision_id` or `asset_id` | The main file and its existing endorsement state are unchanged; new evidence is checked for what it actually covers |
| Project release | Freezes `project_release_id` → the full list of included `document_id` / `revision_id` / SHA-256 | Unchanged files keep their existing revision; a release is not a re-issue of every file |

Identity rules: `document_id` is stable for the life of the project; `revision_id` is immutable and carries the SHA-256 of the original bytes; a derivative (HTML reading page, OCR text, Fragments) records the source hash and tool version it was made from; `asset_id` survives every design revision and model release; a physical replacement is a new asset instance linked to the old one.

## Catalogue structure and the reading layer

- The home page grows by area — Overview · Drawings / Models · Calculations · Endorsements / Approvals · Procurement / Construction · Assets / O&M · Issues / Decisions — with discipline, level, system and asset as the filter dimensions.
- HTML is the shared reading layer. Exact SVG keeps scale, sheet numbers, calc IDs and the visible data tables; PDF / DWG / IFC and the original editable files are linked to the same document.
- Originals and derivatives (OCR text, HTML reading pages, Fragments) are stored separately; every derivative records the hash of the original it was made from.
- The catalogue and every single-document reading page are HTML output by the API that a plain client can read: body text, tables and original-file links do not depend on JavaScript.
- Every project publishes `llms.txt`, `sitemap.xml` and `index.json`. The default index returns only the current documents of the selected use.
- Database search applies the same filters as the index and supports Chinese word segmentation, English full text and exact matches on engineering IDs (sheet numbers, calc IDs, asset IDs, GUIDs).
- History is shown only when the reader explicitly switches to "History"; it is never mixed into the default view or the default search.
- AI answers cite the document, the revision, the page or calc ID and the use for every fact taken from the catalogue; conflicts (two revisions claiming one scope; a design current contradicting a construction current) and gaps ("no O&M attached to this asset") are shown, never resolved silently. A value, date, signature or test result that is not in a registered record is reported as missing, not filled in.

How the AI answers a question from the catalogue:

| Question type | Default source | Answer must state |
|---|---|---|
| "What is the current …?" | The current revision for the use matching the project stage (or the use named), for the scope asked | Document, revision, use, effective date; whether other uses hold a different current |
| "Where is …?" (sheet, calc, manual, certificate) | The current revision's page or attachment, or the asset card | The exact link and the page / calc ID / entry; "not registered" when it is not there |
| "What changed since …?" | History, explicitly | Parent → child revisions with reasons and impact lists; which uses each is current for |
| "Is this signed / issued / accepted?" | The endorsement, construction-issue and acceptance records on that exact revision | Each fact separately with signer / issuer / acceptor, scope and date; never inferred from a technical PASS or a publish |
| "What does AHU-01 need?" (operations) | The asset card and its linked current operations records | O&M, interval, warranty, spares with their sources; `TBC` where the record is empty |

## current_by_use

"Current" is held per use and per scope. It is never the latest upload and never the highest number in a filename.

| Use | Default view | What cannot displace it |
|---|---|---|
| Design — `current_design` | The revision released by the design gate and applicable to the current design scope | An AI or human draft that has just been uploaded |
| Construction — `current_construction` | The revision issued for construction under the project's authority, applicable to that level / system | A revision that only has a technical PASS or a consultant endorsement and has not been issued for construction |
| Operations — `current_operations` | Accepted as-built records, O&M and later approved operational updates | The latest design proposal, an unaccepted as-built draft, an unconfirmed equipment change |

The home page selects the default use from the project stage; each logical document shows exactly one current revision for the selected use, older ones under "History (n)", pending items in the workbench. When a document's design revision moves on while its construction revision has not, the old construction revision stays current — a document is never archived across all uses at once. Where no effective revision exists the page says "awaiting issue" or "awaiting acceptance"; a draft is never shown in its place.

## Publishing an effective revision — one transaction, or nothing

1. Validate dependencies and the basis for this use: gate report, closed review round, issue closure, construction-issue authority or acceptance record; the complete revision manifest and every required derivative present.
2. In one database transaction: create the frozen manifest, switch the affected current pointers, record which revision superseded which, and write the publish event.
3. Refresh the default catalogue and the search index (outbox-driven, with retries). Search results are filtered against the current pointers before they are returned, so index lag can never present a superseded revision as current.

Nothing outside the affected scope changes. If any step fails the old revision stays current; a half-finished upload, a replayed request or a timeout never changes the effective package. Submissions carry `request_id` and `base_catalog_version`; changes to different documents merge, concurrent revisions of the same document are reported as a conflict (never last-writer-wins), and a retry with the same `request_id` is idempotent. Publishing a document never redeploys the website.

## History rules

- History is permanent: originals and old revision links stay; routine archiving deletes no file.
- An old revision's page shows its status per use and scope with the link to the corresponding current one — "Design: superseded by Rev 05; Construction: Rev 04 current" — and is never marked globally obsolete while another use still relies on it.
- A signed consultant PDF is never re-stamped and its bytes are never changed; notices and status live in the HTML around it.
- Rollback is a new publish event with the endorsement and scope evidence re-checked; history is never rewritten.

## Daily reconciliation, monthly exception report

Daily at 02:00 project-local time: check broken links, current-pointer conflicts, unfinished conversions, failed jobs, index lag and last night's backup result; reconcile and compensate. This is a safety net — archiving happens at publish time, not overnight.

Monthly at 09:00 on the first business day of the project calendar: the exception report. Before handover the PM reads it, afterwards the Operation Owner. Target 20 minutes. The report lists only exceptions, and each one leaves the check with an owner and a deadline:

| Exception | Default owner | Closed by |
|---|---|---|
| Draft pending beyond its gate or release | The submitting discipline lead | Publish under the governing gate, or withdraw with a reason |
| Endorsement missing for a signed scope | PM with the discipline lead | Endorsement record attached to the exact revision (`references/certification.md`) |
| As-built / O&M / commissioning record missing for an asset | Procurement (vendor) or site (contractor) | Record attached to the `asset_id`; unknown fields stay `TBC` |
| Dead link, failed conversion, index lag | IT | Reconciliation job result or a manual repair, recorded as an event |
| Item without an owner | PM assigns | Owner and date on the record |
| Backup or restore-test failure | IT | Successful rerun with hashes verified |

The PM never re-uploads the project and never moves old versions by hand. Both jobs are scheduled tasks inside the product, enabled only after IT has configured the project time zone, business-day calendar and PM / Operation Owner names. Both are part of the system still to be built.

## Archive versus backup

Archiving is the immutable revision path inside the system; backup is a separate copy outside it. Neither replaces the other.

| | Archive | Backup |
|---|---|---|
| What it is | Every original at a non-overwritable revision key; S3 Versioning on as the recovery layer; routine archiving deletes nothing | Database and originals copied daily to an independent company backup account |
| What it proves | A revision cited by id and hash can always be opened, and its supersession status is known per use | The catalogue and the originals can be rebuilt after loss of the primary account |
| Monthly test | The daily reconciliation reports broken links and pointer conflicts | IT restores 10 originals plus 1 frozen manifest (all originals if fewer than 10) and verifies hashes, links and revision relations |
| Targets | — | RPO ≤ 24 h, RTO ≤ 4 h — not yet tested; a restore drill must measure them |
| Does not count as | Netlify deploy history: it rolls back the web application only, and its non-retained deploys expire under the platform's retention rules | In pilot mode the box's `/srv/git` snapshots and Drive's version history are the only copies; neither is the independent backup account the target requires |

Every count and time here is an execution target, not an achievement.

## Endorsement registration

Within one working day of receipt (company target):

1. On the corresponding document or package press "Add consultant endorsement" (until the portal is live: `scripts/catalogue.py attach`, bound to the exact revision). Upload the received signed original, the endorsement letter or the original confirmation email, and the exact file list the consultant signed.
2. Record the fields: signer, firm, discipline, date, conditions, level / system and covered scope, `document_id`, `revision_id`, SHA-256 of the received original, covering letter. A package signature carries the per-file manifest, one line per signed file.
3. Confirm which revision was signed: the AI proposes the match between the received files and the catalogue by hash and identity; the PM verifies it. A manifest mismatch or an unclear scope stays "to be confirmed" and is not marked endorsed.
4. Where a digital signature exists, record the verification result. A scanned signature is never recorded as a verified digital signature.
5. Keep the original byte-for-byte; previews, OCR and search text are linked copies. A consultant's revised drawing is a new revision of the same `document_id`; only an actual engineering change reaches the DB and reruns dependents.

Endorsement, construction issue and as-built acceptance are three separate records: an endorsement applies only to the revision and scope it covers, a later revision never inherits it, and an endorsed design is not evidence of what was built. Fields and template: `templates/endorsement-record.json`, `references/certification.md`.

## Lifecycle — what must be filed from S0 to operations

| Point | Must be filed | Responsibility / basis of completion |
|---|---|---|
| S0 — build the catalogue | Handover requirements matrix, record categories, applicable scope, naming and IDs, per item the owner / format / acceptance requirement; the future Operation Owner named | PM leads; requirements are defined first, and no consultant is appointed to define them |
| S5–S6 — selection and procurement | Stable `asset_id` and system / room relations; vendor O&M, actual make / model, warranty, spares, points list / set-points, training and commissioning deliverables | Procurement and discipline leads write the requirements into RFQ / PO; nothing is chased after completion |
| S9 — final signatures | Consultant-signed originals, approvals, signed scope and revisions, open conditions | Discipline lead uploads; PM checks originals against the exact manifest |
| After S10 — construction | Construction-issued drawings, RFIs, variations, redlines, concealed-work photos, installed equipment and serials, site tests / commissioning, inspections and certificates | Site / contractor adds against the asset and document promptly; as-builts verified by a person |
| Formal handover | Accepted as-built drawings / IFC / editable sources, asset register, O&M / SOPs, service intervals, warranty-start evidence, spares and service contacts, training records, open items | PM and Operation Owner jointly confirm the Handover Baseline for the defined scope |
| Operations | Repairs, maintenance, tests, replacements, alterations and later approved revisions | Operation Owner holds `current_operations`; the delivered snapshot stays traceable forever |

Registration at the design gates, for the AI operator:

| Stage / gate | Registered as drafts during the stage | Published for `current_design` at the gate |
|---|---|---|
| S0 / G0 | Brief, site pack index, regulatory basis, certification pathway, programme, Cost Plan 0, specialist matrix, handover matrix, the catalogue itself | The G0 freeze set, scope "whole project" |
| S1–S3 / G1–G3 | Concept plans, area schedule, systems space table, memos, ID layouts, GA set, STR 2D, MEP schematics, Load & Energy Report, cost plans, gate reports | The frozen geometry and interfaces per gate; provisional parts stay drafts with their `ASSUMED — TBC` entries |
| S4 (no gate) | IFC per `model_id`, model-check report, viewer release | Nothing; the release is a draft the PD walks |
| S5 / G4a | Equipment schedule, comparison, RFQ drafts, asset register first fill | Vendor-confirmed items only; unconfirmed items keep envelope and performance brief |
| S6 / G4 | Discipline sheets, calc book, DBR, compliance matrix, spec, `BQ (ESTIMATE)`, Cx test schedule | The detailed design baseline — not a manufacturing release |
| S7 / G5 | Detailed IFC, clash report, penetration schedule, Energy Compliance Report, release sheets | The model; release sheets publish per package only when their evidence is closed |
| S8 / G6 | Issue register, review rounds (attached to the frozen package), gate report | The reviewed package |
| S9 / G7 | Certification pack, endorsement records (ATTACH), consultant correspondence | The signed package, scope "S9 package" |
| S10 and after | RVT exports, `BQ (PROCUREMENT)`, RFQ packs, id-map, construction records, as-builts, O&M, assets | `current_construction` per level / system on construction issue; `current_operations` on acceptance |

## Asset cards

The asset card is the operations entry point. Each maintainable item or system has: a stable `asset_id`; location (building / level / room); model GUID; actual manufacturer, model and serial; installation and commissioning dates; links to its design basis (calc IDs, selection record), consultant endorsement, final as-built, O&M, service intervals, warranty, spares and service contacts. Unknown fields read `TBC` — the AI never supplies a serial number, a date or a warranty from inference. A shared manual is stored once and linked to every asset it covers. The QR label on the equipment points to the stable asset page. A physical replacement creates a new instance linked to the old one; the maintenance history is never erased. Template: `templates/asset-register.csv`; asset identity is assigned at S5 (`references/stages.md`).

## Handover acceptance, the Handover Baseline and the retrieval test

Metrics, with the S0 matrix and the final applicable scope as the denominator:

| Metric | Target |
|---|---|
| Required records registered and accessible | 100 % |
| Maintainable assets with required fields and applicable O&M links | 100 % |
| Applicable test, commissioning, warranty and training evidence | 100 % |
| Known critical safety blockers | 0 |

N/A needs a reason and an acceptor and never silently leaves the denominator. Non-critical open items with owner and deadline allow conditional acceptance; a missing required item means "complete handover" is not declared. These are records metrics, not design correctness.

The PM and the Operation Owner freeze the Handover Baseline together: scope, full revision / hash manifest, asset register, acceptance records, known open items, responsibility transfer. Batches by level / system are frozen separately; the home page shows handed-over vs pending. The operations team then runs the 20-question retrieval test with real questions — "AHU-01: belt model, service interval, where is the issued as-built?" — and 20/20 must return the correct current source with page or entry; an answer for missing data must say it is missing. This test is separate from the seeded-defect detection rate in `references/review-and-gates.md`.

After handover the URL stays; the home page defaults to the operations use; the PM hands catalogue management, the monthly check, exception handling and backup oversight to the Operation Owner. Design decisions and history stay under "design history"; maintenance records never overwrite the delivered snapshot. Template for the matrix: `templates/handover-matrix.csv`.

## Draft → freeze → publish, and the review loop

- Ingestion only adds records. Working files form drafts; a dependent package whose files are incomplete stays WAITING_FOR_FILES. A successful upload is not a released design.
- A review round freezes its inputs against the complete manifest and hashes: design sources, files, standards and tool versions, submitter and time; unchanged items reference their existing revisions. Script results, data consistency and technical verdicts are recorded in separate columns.
- Issues keep their stable IDs, closure evidence and re-verification; the five-round limit stands (REQUESTED → VALIDATING → FROZEN → REVIEWING → RESPONSE_REQUIRED → CLOSED / HUMAN_REQUIRED; `references/review-hub.md`). Publishing checks the governing gate and the design / construction / operations use; a web state never substitutes for an endorsement or an acceptance.
- Technical package state is DRAFT → READY_FOR_RELEASE → PUBLISHED, bound to use, scope and current pointer. Ingestion never advances it; a CLOSED review round is an input to READY_FOR_RELEASE, not the publish itself. A tool that did not run stays UNVERIFIED; only an execution record shows success.
- Reproducibility: raw review replies, signatures, revisions, conditions, issues and original hashes are kept; withdrawal or supersession is a new event; routine archiving deletes nothing.

## The pilot substitute now — `scripts/catalogue.py` and the company-server runner

Until the portal exists, `scripts/catalogue.py` is the substitute for the catalogue API. It works on `catalogue.json` in the project repository — one file holding the documents, their immutable revisions, attachments, `current_by_use` pointers, releases and an append-only event log — and applies the portal's semantics, so the IDs it creates are imported into PostgreSQL unchanged when the portal is live (`references/hosting.md`, migration path). The script is being written; the commands below are the intended set and their semantics. Read the script's `--help` for the exact argument spelling before use and never assume an option that is not there.

| Command | Semantics |
|---|---|
| `add` | Registers a new document from a file: new stable `document_id`, first immutable `revision_id`, SHA-256, size, repository path, index fields (discipline, level / system, task, home-page area), submitter and timestamp. Bytes whose hash already exists elsewhere in the catalogue are reported; a new logical document is created only on explicit confirmation |
| `revise` | New immutable revision of an existing `document_id` with its parent revision, reason, impact list and SHA-256. A hash identical to the parent is "already exists" and creates nothing. No current pointer changes |
| `attach` | Binds evidence (endorsement, photo, test, approval, letter) with its own hash, type and scope to an exact `revision_id` or an `asset_id`; the main file is untouched |
| `publish` | The publish-effective transaction for one use (design / construction / operations) and one scope: checks the manifest and the gate / issue / acceptance evidence named, writes the frozen release manifest, switches the affected pointers, records which revision supersedes each old one, appends the publish event. Any check failing → nothing changes |
| `release` | Freezes a `project_release_id` → the full list of included `document_id` / `revision_id` / SHA-256 for a named scope (a viewer release, the S9 package, a procurement package) without moving any current pointer; a later `publish` can cite it |
| `list` | The current documents for a use and scope (default: the use that matches the project stage); drafts and history only when asked |
| `history` | Every revision of a `document_id` in order, with parent, reason, hash, attachments and the per-use supersession status |
| `check` | Catalogue integrity: every revision's file exists at its recorded path with a matching SHA-256, every pointer and attachment target resolves to an existing revision of the right document, every release manifest resolves, no two documents share an identity key; prints counts and exits non-zero on any failure |

`catalogue.json` shape, at the level SKILL.md fixes it (the exact field spelling is the script's): documents with stable `document_id`; revisions with immutable `revision_id`, parent, SHA-256 and original reference; attachments bound to exact revisions or assets; `current_by_use` with one head per use and per scope and the supersession record; releases with full manifests; events with `request_id` so a replayed command is recognised. Every command writes the whole catalogue atomically (a temporary file renamed over `catalogue.json`), so an interrupted run leaves the previous catalogue intact. The script never deletes a revision, never re-hashes a file in place and never moves a pointer as a side effect of `add`, `revise` or `attach`. Before every gate run `check`, `list` and `history` on the stage's documents and put the counts in the catalogue-integrity row of `templates/gate-report.md`; script success there is a data-consistency result, not an engineering PASS.

The company-server runner (`deploy/runner.py`) publishes the reading layer in pilot mode: whenever the project folder changes it rebuilds the project's static book — the library's `gen_book.py` if installed, otherwise its built-in index (home page, `index.json`, `llms.txt`, `robots.txt`, one page per sheet, calc, decision and review round) — and indexes it with Pagefind for the search box. The built-in index does not yet read `catalogue.json`: the pilot book shows the repository's files, and what is current per use is answered from `scripts/catalogue.py list` until a book generator renders the pointers. A pilot "publish" is therefore `scripts/catalogue.py publish` plus the book rebuild. What the pilot does not have, and must not be claimed: the workbench form, PostgreSQL, S3, the publish-effective API, the persistent issue API, per-use current views on the website, the scheduled reconciliation and monthly report, independent backups beyond the box's own copies and Drive's version history (`references/hosting.md`).

## API contract (minimum) and go-live tests

| Record / API | Minimum contract |
|---|---|
| document / revision / derivative | Stable logical ID; immutable revision with parent, hash and original reference; derivatives bound to source hash and tool version |
| current_by_use / project_release | One head per use (design / construction / operations) and per scope; a release is a fixed, complete manifest |
| endorsement / issue / asset / handover | Signature record with covered scope; issue coordinates / GUIDs / release with history; asset location and replacement chain; handover acceptance and exceptions |
| create_upload → commit_submission | Receives only this submission's files / `artifact_ref`; `request_id`, operation, `base_catalog_version`, hashes and expected files → `submission_id`, `job_id`, `draft_url` |
| publish_effective / get_job | `target_use`, `scope`, frozen manifest, gate / issue / acceptance evidence → current URL and revision / release URLs; pointers switch only when the job is READY |
| issue APIs / accept_handover | Existing create / list / get / respond / verify_issue; accept_handover freezes scope, matrix results, acceptors, exceptions and the complete manifest |

Large files go browser-direct to S3; the server verifies the real bytes, hashes and the expected file set before a submission commits. Long jobs (IFC conversion, recalculation, OCR) return a `job_id` because the portal proxy times out at 26 s. The go-live test list and the workbench acceptance target (four staff actions: choose the project, add files, check the summary, submit) are in `references/hosting.md`.

## Implementation status

Everything in this file that describes the portal — web picking, persistent issues, ingestion, publish-effective, scheduled reconciliation, asset / operations handover, Runner integration — is UNVERIFIED end to end. Verified facts about Netlify, S3 or PostgreSQL are facts about those platforms, not evidence that the company system exists.

Pilot order: a mock reviewer first, to test the state machine and failure recovery; then real APIs for file hand-off → 3D issue → AI response → new draft → publish → history query → operations retrieval; one typical level, one plant room and one riser through S0–S10; then a lifecycle rehearsal with real construction records. Measure human hours, real model cost, review rounds, critical misses, false positives, consultant change volume, upload failures, record completeness and restore results. Demonstrate at least once: "no engineering change → no rerun"; "one real engineering change → only the affected DB / calcs / sheets / BQ updated and the signature re-confirmed"; "a new upload loses no existing content". The 4–8 week AI design target is not a construction programme.

## Defects

- Letting upload time or a filename's version number decide what is current; showing a draft where no effective revision exists.
- Archiving a document for every use because one use moved on; marking a still-used revision globally obsolete.
- Copying an endorsement to a new revision; changing the bytes of a signed original; marking a design deliverable as accepted as-built.
- Re-uploading a whole project; replacing a folder; overwriting on a filename match; creating a duplicate revision for an identical hash — or skipping a new attachment / asset relation because the bytes already existed.
- Publishing from the AI's own session; treating "original stored" or "converting" as "published"; showing "AI has received it" for a draft saved locally.
- Filling a serial number, install date, warranty date or test result that is not in a registered record.
- Rerunning calculations because a letter or photo was attached; not rerunning them after a real engineering change.
- Claiming the portal, the scheduled jobs or the restore targets are proven; reporting the RPO / RTO targets as achieved; assuming a `catalogue.py` option that its `--help` does not list.
