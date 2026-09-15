# Hosting — pilot mode (what runs today) and target platform (specified, not built)

Requirement (PD): every project lives at one permanent public address under the company domain; any AI model can fetch and index it; no login in front of reading; a search box for people; staff never deploy anything and never touch a hosting console, Git or a terminal. Adding calculations, drawings, IFC or consultant files never redeploys a site.

Two modes are described here and must never be confused in what the AI tells staff:

| Mode | Status | What it is |
|---|---|---|
| PILOT | Running today | One company Linux server running `deploy/`: a docker-compose runner, Caddy serving static project books, a Cloudflare Tunnel; folder-drop review requests; the static book with Pagefind search |
| TARGET | Specified in the handbook; UNVERIFIED — not built | The Netlify ProjectBook portal + company Runner / API + PostgreSQL catalogue + company AWS S3 originals |

Catalogue semantics for both modes are in `references/project-knowledge-base.md`. Anything in the TARGET half of this file is a contract for IT to build and test, not a description of something that exists.

## PILOT — the company server (`deploy/`)

One Linux machine (Ubuntu 22.04 / 24.04, 4 cores / 8 GB upwards, 5–20 GB disk per project including snapshots, outbound internet only, no inbound port) runs three containers from `deploy/docker-compose.yml`. One-time setup (about 40 minutes), daily operation and the acceptance test are in `deploy/README-IT.md`; the operational facts that matter to the AI are repeated here.

| Container | Image / code | Role |
|---|---|---|
| `runner` | `deploy/Dockerfile` (python:3.12-slim + git + Node 22 + Pagefind), runs `deploy/runner.py` | Polls every project folder (`POLL`, default 30 s); handles review requests, sheet QA and book builds; writes `STATUS.md` |
| `web` | `caddy:2` with `deploy/Caddyfile` | Serves `/srv/site` as static files on `127.0.0.1:8080` only (`file_server browse`, gzip, `Cache-Control: public, max-age=120`, `X-Robots-Tag: all`) |
| `tunnel` | `cloudflare/cloudflared` | Cloudflare Tunnel from `books.<company-domain>` to `http://web:8080`; no open ports, no public IP |

The connection between staff and the server is the shared Google Drive `Projects` folder, mounted at `/srv/projects` with rclone (`deploy/rclone-mount.service`, VFS full cache, 30 s poll). Staff keep Google Drive for desktop; Drive sharing decides who can write which project folder. No per-employee key, no login, nothing installed on a staff computer. Secrets stay on the box: in `.env` (mode 600) one reviewer API key (`WS_REVIEWER_PROVIDER` = openai / openai-compatible / gemini / mock, `WS_REVIEWER_MODEL`) and the Cloudflare Tunnel token, beside `WS_BOOK_BASE_URL` and `POLL`; the Drive credentials in the host's rclone configuration. Projects named in `PRIVATE_PROJECTS` get review and QA but no public book.

What `deploy/runner.py` does on every poll, for every project folder under `/srv/projects` (folders starting with `.` or `_` are skipped):

1. **Review requests.** `reviews/<task>/REQUEST.json` (`{"task": …, "stream": …}`; the stream defaults to the part of the task name after the first hyphen) → a server-side git snapshot of the project into `/srv/git/<project>` (bare repository with the project folder as work tree; packets and raw calls excluded; invisible to staff and never written into Drive) → `scripts/peer_review.py packet`, then `selfcheck` (blind isolation proven before any call), then `review`, then `respond` if the state is `RESPONSE_REQUIRED` → `feedback.json` and the responses template in the round folder → the request is renamed `REQUEST.done.json` with the commit, verdict and status, or `REQUEST.error.txt` with the pre-check list or the error (`references/review-hub.md`).
2. **Sheet QA.** Any new or changed `drawings/*.html` (detected by mtime and size) → `scripts/annotate.py check` → `drawings/qa/<sheet>.json` and `drawings/qa/SUMMARY.md` (pass, crossings, leaders through geometry, leaders over dimensions, text over line / text, outside border, label columns).
3. **Book rebuild.** Any change in the folder (a hash over path, mtime and size of every file, ignoring `reviews/`, `.git`, `site`, `_book`, `qa` and `STATUS.md`) or a completed review / QA run → the project's book is rebuilt into `/srv/site/<project>/`: the design library's `gen_book.py` (in `wellsmart-design-library/templates/`, not in this skill) if a library checkout is mounted at `/opt/library`, otherwise the runner's built-in index. Pagefind then indexes the site (the image always contains it) over everything marked `data-pagefind-body`, handling Chinese and English; the search box itself is part of the `gen_book.py` pages — the built-in index writes the index under `/pagefind/` but embeds no search UI, so with the built-in book the register pages are the human search.
4. **`STATUS.md`** in the project root: the last run's lines plus the previous forty, the one page a person opens to see what the server did.

The runner writes only its own files (`reviews/*/round-*`, `REQUEST.done.json` or `REQUEST.error.txt`, `drawings/qa/`, `STATUS.md`); it never deletes a staff file. Code updates on the box are `git pull` then `docker compose up -d --build`; a reviewer model change is an `.env` edit and a runner restart — IT actions, never staff ones. The book is public and read-only; it accepts no writes at all in pilot mode.

### Pilot book layout

Paths are relative to `books.<company-domain>/<project>/`. The built-in index produces the rows marked (built-in); the remaining rows exist only when `gen_book.py` is installed.

```
/                          (built-in) home: sections Drawings, Calculations, Reviews, Reports, BQ, Decisions, server status
/index.json                (built-in) machine index of every copied page, by section
/llms.txt                  (built-in) the AI index: one line per page with its absolute URL
/robots.txt                (built-in) allow all
/drawings/<NUMBER>.html    (built-in copy) one sheet = one page: inline SVG, QA overlay, manifest JSON, visible tag / calc-ID list
/drawings/qa/<NUMBER>.json (built-in copy) the QA result per sheet; /drawings/qa/SUMMARY.md
/calcs/…                   (built-in copy) calc pages and CALC-BOOK_<stage>.html; /reports/…, /bq/… likewise (.html .csv .json .md .pdf)
/decisions.md              (built-in copy) the decision log
/reviews/<task>/round-<n>.html   (built-in) verdict, checks, findings table and the raw feedback.json
/pagefind/                 (built-in) the Pagefind search index; the search box that uses it is on gen_book.py pages
/sitemap.xml, /model/, /thermal/, per-decision and per-calc pages   with gen_book.py only
```

A sheet number or calc ID is its URL for the life of the project; a new revision replaces the page, and the review round that read the old one cites it by the frozen manifest hash, not by the URL. Because Caddy sends `max-age=120`, a rebuilt page can take up to two minutes to appear for a repeat visitor; nothing in the pilot is a mutable API response, so the target's `no-store` rule has nothing to apply to yet.

After every rebuild, check: a plain HTTP client (no browser) gets the HTML; every sheet in `drawings/index.csv` resolves with HTTP 200; the manifest JSON parses; `llms.txt` and `index.json` list every page; where the search box exists, a search for a known tag returns the sheet; no page exceeds 16 MB. The first check is the AI-crawlability test.

### What the pilot does not have

No workbench upload form; no PostgreSQL; no S3; no publish-effective API; no persistent issue API (issues are `wsg.issue/1` files under `issues/`, review findings under `reviews/`); no per-use current views on the website; no scheduled reconciliation or monthly report; no independent backup beyond the box's own `/srv/git` snapshots, `.env` and Drive's version history. The catalogue is `catalogue.json` maintained with `scripts/catalogue.py`; the built-in index does not read it yet, so the book shows the repository's files and "current per use" is answered from `scripts/catalogue.py list`. A pilot "publish" is `scripts/catalogue.py publish` plus the book rebuild. None of the missing items may be claimed or shown as a working button.

### Fallback without the company server

An office with no Linux box can host the static book alone on Cloudflare Pages: one Pages project per building project, built from the project repository by `gen_book.py` + Pagefind, free plan with commercial use allowed, a custom domain per project, 20,000 files and 25 MiB per file per deployment (a tower's S9 set of ≈ 700 sheets plus calc books fits), no bandwidth charge, and the same AI-crawler settings as below. This is a static book only — it carries none of the catalogue semantics, so `scripts/catalogue.py` still runs in the repository and the AI still reports current-by-use from it. Not used: GitHub Pages (private repositories publish publicly only on an enterprise plan, and the site is tied to the repository host); any hosting that puts a password, SSO or challenge in front of reading.

## TARGET — the Netlify ProjectBook portal (UNVERIFIED, not built)

One stack, one portal. IT publishes the company's ProjectBook web application to the company Netlify Team through the official Netlify connector / CLI / API, with a stable domain and the route `/projects/{project_id}/`. A new project is a catalogue record created by the system, not a new deployment. Deploying the program and uploading design files are two different things: the first is IT operations, the second is what staff and the AI do every day at the project URL, and it never triggers a site deploy.

| System | Role | Operated by |
|---|---|---|
| Netlify portal | Serves the ProjectBook app; rewrites proxy the catalogue and reading APIs; holds nothing mutable itself | IT deploys app updates with the official connector; nobody else touches it |
| Runner / API | Ingestion, HTML reading pages, model conversion (IFC → Fragments), OCR, engineering jobs, scheduled reconciliation, publish-effective | IT / Dong; the staff workbench and the AI's connector are its only clients |
| PostgreSQL catalogue | The source of truth: documents, revisions, derivatives, current pointers, releases, endorsements, issues, assets, handover, events | IT; the PM sees it only as the catalogue on the project page |
| Company AWS S3 | Immutable originals, revisions and derivatives; Versioning on | IT; daily backup to an independent company backup account |

Staff never touch the four systems; their interface shows project, file, status and result, never an infrastructure noun. Netlify provides hosting and app deployment; revision, archive and handover logic is product work the company builds, not a connector feature. Netlify deploy history rolls the app back; it is not an engineering archive, and its non-retained deploys expire under platform retention rules.

### Pages the portal serves

All under `/projects/{project_id}/`; every page is server-rendered HTML from the catalogue API, readable without JavaScript.

| Page | Content | Mutable? |
|---|---|---|
| Project home | Areas (Overview, Drawings / Models, Calculations, Endorsements / Approvals, Procurement / Construction, Assets / O&M, Issues / Decisions), the default use for the stage, one current revision per document | Yes — `no-store` |
| Document page | The current revision for the selected use, its states as separate facts, "History (n)", attachments, original download | Yes — `no-store` |
| Revision page | One exact revision: reading HTML, embedded manifest, original link; supersession status per use fetched live | Content immutable, long cache; status live |
| Asset page | Asset card, linked documents by exact revision, maintenance history; the QR target | Yes — `no-store` |
| History view | All revisions of a document with supersession per use and scope; only on explicit navigation | Yes — `no-store` |
| 3D review page | That Open canvas on the release's `.frag`, issue panel (`references/ifc-review.md`) | `.frag` immutable per release; issues live |
| Workbench | Upload new content / new version / attachment, merge preview, submit, publish (authorised only) | Session-bound, never cached |
| `llms.txt`, `sitemap.xml`, `index.json` | Machine indexes of the current documents of the selected use | Yes — `no-store` |

### Storage: S3 keys and immutability

Key: `projects/{project_id}/documents/{document_id}/revisions/{revision_id}/{sha256}/{filename}`. Store the object version ID, byte count and the hash of the original; reads of an original pin the object version ID. The server refuses to overwrite an existing revision key, and routine flows never delete an original. Versioning is a recovery layer — switching it on is not by itself an immutability claim. Identical content is reused by hash while the business relation (attachment, asset link, scope) is stored separately; S3 versions are whole objects, so storage is never estimated as deltas. Permanent links point at the portal, which issues a fresh temporary transfer URL at download time; an expiring signed URL is never used as an archive address.

### Ingestion path

1. The workbench form or the AI's connector calls `create_upload` with the intended operation, target ids, expected files and hashes; the server answers with direct-to-S3 upload targets.
2. The browser or the Runner uploads the bytes straight to S3 under a staging key; nothing large passes through the Netlify proxy.
3. `commit_submission` carries `request_id`, `base_catalog_version`, the operation (ADD / REVISE / ATTACH), target ids and hashes; the server verifies the real bytes, hashes and the expected file set, moves the objects to their immutable revision keys and returns `submission_id`, `job_id` and `draft_url`.
4. Derivatives (reading HTML, OCR, Fragments) run as jobs; `get_job` reports each readiness separately; the catalogue marks IFC, Fragments and preview readiness independently. A failed job is retried; it never blocks the original being stored.
5. `publish_effective` — by an authorised person, with the gate / issue / acceptance evidence — locks the affected current pointers, re-validates the base version and the complete dependencies, switches the pointers in one transaction and writes the publish event; an outbox drives index updates and retries. Only step 5 changes what readers see as current. Failure, replay and a half-finished upload never change the effective revision.

Concurrency: different documents' changes merge; two concurrent revisions of the same document are reported as a conflict, never written last-wins; a retry with the same `request_id` is idempotent.

### Proxy time limit, jobs and caching

The Netlify rewrite proxy times out at 26 s. IFC conversion, recalculation, OCR and any other long work return a `job_id` and run asynchronously; the page polls `get_job`. Mutable responses — current pointers, catalogue listings, search, endorsement state — carry `Cache-Control: no-store` and `Netlify-CDN-Cache-Control: no-store`; the client re-reads `catalog_version` when a page is reopened, the use is switched or the window regains focus. Immutable revision content (a specific revision's HTML, PDF, IFC, `.frag`) may be cached long; its supersession status is fetched from the current API and never inferred from a cached page.

### Permission boundary

Public browsing and UNTRIAGED issue drafts need no login. Content writes, issue handling, paid compute and publishing use the company's existing authorisation: IT implements short-lived workbench session issuance inside the company's WSG ingestion connector and connects it to that authorisation. Until that company integration is connected it is labelled UNVERIFIED, and it is never described as a built-in Netlify capability. No new account or registration system. No server secret in public HTML. Uploaded HTML is kept as a faithful original and rendered through a controlled template so its scripts never run inside the portal.

| Action | Who | Authorisation |
|---|---|---|
| Read any page, download originals, use search | Anyone with the link, any AI fetcher | None |
| Save an issue draft from the 3D review page | Anyone | None; the draft is UNTRIAGED until a staff member confirms it |
| Upload new content / new version / attachment | Staff | Existing company authorisation via the workbench session |
| Confirm, process and verify issues; run paid compute | Staff, the AI operator | Existing company authorisation |
| Publish as current effective | The person with the process authority for that gate / issue / acceptance | Existing company authorisation; the evidence is checked server-side |
| Deploy the app, configure projects, enable scheduled jobs, run restore tests | IT | Netlify Team and company infrastructure access; never a staff action |

### Lifecycle records and scheduled tasks

Consultant endorsement, construction issue and as-built acceptance are independent records, each bound to a scope and an exact revision. The scheduled reconciliation (02:00 project-local) and monthly exception report (09:00, first business day), the independent backup, asset links and the Handover Baseline all use the same catalogue. IT configures the project time zone, business-day calendar and PM / Operation Owner before enabling the daily and monthly tasks. Before go-live IT also verifies on the real deployment: `no-store` on every current / catalogue / search / endorsement response; long cache only on revision content; a job longer than 26 s returns a `job_id` and completes; the project's largest real IFC uploads, converts and loads with the pinned worker / WASM versions; a plain HTTP fetch of the home page, a document page and `llms.txt` returns the content without JavaScript.

### Minimum data / interface contract

| Record / API | Minimum contract |
|---|---|
| document / revision / derivative | Stable logical ID; immutable revision with parent, hash and original reference; derivatives bound to source hash and tool version |
| current_by_use / project_release | One head per use (design / construction / operations) and per scope; a release is a fixed, complete manifest |
| endorsement / issue / asset / handover | Signature record with covered scope; issue coordinates / GUIDs / release with history; asset location and replacement chain; handover acceptance and exceptions |
| create_upload → commit_submission | Receives only this submission's files / `artifact_ref`; `request_id`, operation, `base_catalog_version`, hashes and expected files → `submission_id`, `job_id`, `draft_url` |
| publish_effective / get_job | `target_use`, `scope`, frozen manifest, gate / issue / acceptance evidence → current URL and revision / release URLs; pointers switch only when READY |
| issue APIs / accept_handover | Existing create / list / get / respond / verify_issue; accept_handover freezes scope, matrix results, acceptors, exceptions and the complete manifest |

### Go-live tests

1. Add A, add B, then revise A: B and every original chapter intact.
2. A draft of A does not displace A's construction current.
3. After A is published for design, only the new revision shows for that use; history links still resolve.
4. An older construction current and a newer design current coexist for the same document.
5. A consultant's signed scope is not copied to the new revision.
6. Concurrent revisions of one document, a dropped connection and a repeated identical request: no file lost, no duplicate created.
7. Ten IFC issues survive a refresh and a change of browser (`references/ifc-review.md`).
8. The stored SHA-256 equals the hash of the received file.
9. Restore 10 originals and 1 frozen manifest from backup, hashes verified.
10. Link one asset and run a simulated operations handover at the same URL.
11. The project's largest real IFC: transfer, worker / WASM, coordinates and performance.
12. One real file hand-off each from the staff's normal Claude and ChatGPT clients.

Workbench acceptance target: a staff submission needs four kinds of action — choose the project, add files, check the summary, submit — with no hosting console, Git or command line. Record real click counts, bytes uploaded, time taken and failure reasons. An integration that is not connected is labelled UNVERIFIED; a demo is not an integration acceptance.

## Migration — pilot to target

Nothing is renumbered. Migration replays the pilot's catalogue and files into the portal, verified by counts and hashes, one project at a time:

| Pilot | Target | Rule |
|---|---|---|
| `catalogue.json` (documents, revisions, attachments, `current_by_use`, releases, events) | PostgreSQL catalogue | Import as-is: the same `document_id`, `revision_id`, SHA-256, parents, reasons, impact lists, pointers and release manifests |
| Originals in the project folder (Drive) | S3 under the immutable key scheme | Upload each revision's file; verify the stored hash against the catalogue hash before the record is marked stored; a mismatch stops that document's migration |
| Static book pages | Portal reading pages under `/projects/{project_id}/` | Sheet numbers, calc IDs and decision ids stay the stable path elements; the old `books.` URLs redirect for at least the life of any review that cited them |
| `issues/` files (`wsg.issue/1`) | Issue API (create / list / get / respond / verify_issue) | Issue ids, release ids, model hashes, GUIDs and anchors carried over unchanged |
| `reviews/<task>/round-<n>/` | Records attached to the frozen revisions they reviewed | Raw replies, `feedback.json`, responses and input hashes retained |
| `REQUEST.json` folder-drop | `create_upload` → `commit_submission` through the AI's connector | The fixed sentence and the ADD / REVISE / ATTACH semantics do not change for staff or the AI |
| Book rebuild on every change | Publish-effective on evidence only | After migration, "current" is served from the pointers, never from a rebuild |

Cut-over per project: migrate, run the go-live tests above on the migrated copy, then switch the project's canonical URL. Until a project has passed them its pilot book remains the published address.

## AI-friendly rules — both modes

- No login, cookie wall, consent banner, interstitial or challenge in front of reading; no password, SSO or Access policy on the hostname; no rate limit below 60 requests per minute per client. A challenge page is a login by another name.
- Cloudflare in front (the pilot tunnel, or any zone later): in the zone's security settings turn **off** "Block AI bots / AI Scrapers and Crawlers" — it is on by default for new zones since 2025 — and do not enable Bot Fight Mode or a managed challenge on this hostname.
- Plain HTML with the content in the markup: body text, tables and original-file links readable without JavaScript. Search is the only script feature and it degrades to the register pages.
- Every page has one `<h1>` (sheet number + title, calc ID + title), a `<title>` and a `<meta name="description">`; the sheet manifest is embedded as `<script type="application/json" id="manifest">` and served as its own `.json`; tags, run labels, calc IDs and assumptions are also rendered as a visible text list under the SVG, because SVG text alone is not reliably indexed.
- `llms.txt` at the project root, `sitemap.xml`, `index.json`, `robots.txt` allowing all; no `noindex` unless the PD asks to stay out of search engines, which is a separate question from AI access.
- The default index and search list only the current documents of the selected use; history is behind an explicit history view, so a model that follows the index cites what is current.
- Stable URLs: project, document, exact revision and asset pages can be copied and keep working after later revisions.
- Small pages: a sheet page is 50–200 KB; images only as inline SVG; photographs on their own pages, never base64 inside sheet pages; one page per thing, so a model fetches exactly the sheet or calc it needs.
- Confidentiality is by obscurity only, on the PD's instruction: an unguessable project address, no links from the public company site, consultant PDFs watermarked at S9. The site accepts no writes except UNTRIAGED issue drafts (target mode); everything else goes through the ingestion service.

## Defects

- Describing the portal, the workbench, the publish API, the issue API or the scheduled jobs as existing; showing a fake "published" or "AI has received it" state in pilot mode.
- Redeploying a site to publish a document; using Netlify deploy history as the archive; using an expiring signed URL as a permanent link.
- Caching a current-pointer, catalogue or search response; inferring "current" from a cached revision page.
- Running a job longer than 26 s inside a proxied request instead of returning a `job_id`.
- Adding a login, registration page, challenge or Access policy in front of reading; leaving Cloudflare's AI-crawler block on; putting a server secret in public HTML.
- Overwriting an existing revision key; deleting an original in a routine flow; calling S3 Versioning "immutability".
- Migrating a project by re-hashing or renumbering; switching a project's canonical URL before its go-live tests pass.
- Telling staff an infrastructure noun (bucket, database, deploy, tunnel) when the page should say project, file, status and result.
