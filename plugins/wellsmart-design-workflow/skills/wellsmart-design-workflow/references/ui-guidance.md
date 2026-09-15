# UI guidance — for every HTML the AI publishes, and for judging a ProjectBook page

Part II of the handbook (UI Guidance 1.0) defines the product interface for design, review, procurement, the knowledge base and operations: Apple-like restraint, hierarchy and familiarity. The ProjectBook is Jack's product and implements this guidance; the AI uses it in two ways: every HTML it produces (sheets, calc books, gate reports, coverage tables) follows the engineering-content and status rules below so the ProjectBook can present them unchanged, and when asked to judge a ProjectBook page it checks the page against this file. The handbook's own demo screens are static examples; nothing in them is connected to a real project or backend, and every demo value is labelled DEMO.

## Three principles

1. **See what needs deciding first.** Current stage, version, key open items and the next step are always on the first layer.
2. **Details open when needed.** From the conclusion into inputs, calculations, drawings and review basis; the evidence stays complete.
3. **Status states actual facts.** AI review, professional signature, manufacturing release and publication are shown separately, never merged into one tick.

## Foundations

Quiet interface, precise rules: system fonts, thin borders, restrained white space; tables and drawings get enough room; ordinary content stays highly readable.

Semantic palette (light theme): background `#f5f5f7`, surface `#ffffff`, primary text `#1d1d1f`, secondary text `#626267`, action `#0066cc`, separator `#dedee3`. These values are Well Smart's product choice. Neutral borders separate; input controls use the stronger `control-border`. Light and dark use independent semantic values so content stays readable in both.

CSS tokens, to be copied to the developer verbatim:

```css
:root {
 color-scheme:light;
 --font:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;
 --mono:ui-monospace,SFMono-Regular,Consolas,monospace;
 --bg:#f5f5f7;
 --surface:#fff;
 --ink:#1d1d1f;
 --muted:#626267;
 --blue:#0066cc;
 --border:#dedee3;
 --control-border:#777780;
 --blue-soft:#eaf3ff;
 --green:#246842;
 --green-soft:#eaf6ee;
 --amber:#845000;
 --amber-soft:#fff3d6;
 --red:#b42329;
 --red-soft:#fff0f0;
 --purple:#6840a1;
 --purple-soft:#f4eefc;
 --s1:4px;
 --s2:8px;
 --s3:12px;
 --s4:16px;
 --s6:24px;
 --s8:32px;
 --s12:48px;
 --s16:64px;
 --r1:8px;
 --r2:12px;
 --r3:18px;
 --sidebar:248px;
 --toolbar:64px;
 --reading-width:1000px;
 --target:44px
}
[data-theme='dark'] {
 color-scheme:dark;
 --bg:#161617;
 --surface:#202023;
 --ink:#f5f5f7;
 --muted:#a8a8b0;
 --blue:#6aaaff;
 --border:#38383d;
 --control-border:#92929b;
 --blue-soft:#183148;
 --green:#8bddaa;
 --green-soft:#1c3527;
 --amber:#f1c16e;
 --amber-soft:#3d3019;
 --red:#ffadb0;
 --red-soft:#42252a;
 --purple:#c6a7ff;
 --purple-soft:#322743
}
body { font-family: var(--font); color: var(--ink); background: var(--bg); }
button, input, select { font: inherit; min-height: var(--target); }
:focus-visible { outline: 3px solid var(--blue); outline-offset: 3px; }
.number { font-variant-numeric: tabular-nums; }
.primary { background: var(--blue); color: #fff; }
[data-theme="dark"] .primary { color: #102238; }
@media (prefers-reduced-motion: reduce) {
 *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}
```

### Typography

| Element | Size |
|---|---|
| Chinese body text | 16 px, line height 1.65 |
| Page title | 36 px desktop / 28 px narrow |
| Section heading | 24 px |
| Component title | 17 px |
| Table text | 14 px |
| Helper text | 13 px |

English and numerals use the system font stack. Engineering IDs are copyable text (`CHW-001 · 24.60 kW · v1.2` is the handbook's example); numbers use tabular figures so digits align in columns.

### Space and layout

- Sidebar 248 px, toolbar 64 px, reading width about 1000 px; drawings and tables may fill the whole content area.
- Spacing scale 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64; radii 8 / 12 / 18; every click target at least 44 × 44 px.
- Desktop uses a fixed sidebar; below 1180 px it collapses into a table of contents; at 390 px (phone) the outer margin is 16 px.
- The whole page scrolls vertically only; wide tables and drawings scroll inside their own containers, never the page.

## The six work views

One system, six switchable, filterable, expandable views. Header pattern from the demo: product / project name, "DEMO · read-only example" when demo data is shown, then the view tabs.

| View | First layer must show | Next layer |
|---|---|---|
| Overview | Current stage, key open items, current version, real metrics | Discipline packages, milestones, quality evidence |
| Stages | Inputs, outputs, specialist interfaces, dependencies and freeze conditions | Each output, its calculations and review record |
| Drawings | Sheet number, revision, actual applicable levels, legend, a generous drawing area | Element properties, related calculations, version overlay |
| Calc book | Conclusion, operating case, key inputs, assumptions, verification status | Formulae, code basis, raw inputs, run record |
| Review issues | ID, severity, discipline, the specific problem, version, status | Evidence, reply, change, re-verification and closure history |
| BQ / procurement | Quantity, unit, specification, measurement type, procurement stage | Component / vendor detail, quotes, interfaces and release conditions |

Overview cards from the demo, to be reproduced with real data: "Design programme target 4–8 weeks — target range, not an achieved duration"; "Critical-defect detection target 99 % — a detection-rate metric, not a zero-defect probability"; "Verified detection rate — · initial n = 0 · no validation sample yet". The stages view carries the specialist front-loading table (fire strategy, wet / dry fire, DDA, façade / acoustics, traffic: what each produces at S0–S1 and which building parameters it drives) and the three stage rules: AI first completes strategy, drawings, calcs and internal review; consultants enter against a mature package, never as a default early step; missing inputs are bounded assumptions and only closed dependencies freeze. The calc view leads with the result, then inputs and assumptions, then the run / review record (run ID, input version, model and script versions, run time, result files, review scope — never a fictitious log or signature), then "if manual detailing changed something": engineering change → compare fields, list affected dependants, update only the related calcs, sheets, models and BQ; no engineering change → "no design change, original verification stands"; layout and annotation moves keep a version diff and trigger no unrelated calculation. The issues view is a searchable, status-filterable table with an evidence panel: issue → input or drawing evidence → designer reply → change diff → independent re-verification → closure record, each step citing an explicit version. The BQ view shows the procurement stage as enquiry → capacity reservation → manufacturing release; real lines carry dimensions, angles, interfaces, installation and fixing requirements; estimate, actual take-off, waste and spares are listed apart; manufacturing release binds to that package's closed evidence and never follows from "published".

## Status semantics

One green tick cannot stand for every fact. Every status carries text, scope, version and basis; colour assists recognition and never carries the meaning alone.

Document status badges: draft ○ · in review ◷ · needs change ! · owner approved ✓ · published ▣.

Separate facts, each with its own record:

| Fact | Meaning | Must show |
|---|---|---|
| AI-reviewed ✓ | The named version passed AI review of an explicit scope | Review layers, issue closure, validation evidence |
| Professionally signed ✦ | A real professional signature exists | Signer, scope, version and file; never inferred from AI review |
| Manufacturable ↗ | The named procurement package met its manufacturing conditions and was formally released | Recorded apart from enquiry and capacity reservation |
| Published ▣ | A complete immutable version was published | A file state; it does not replace technical compliance, signature or procurement authority |

Implementation: store `scope`, `version`, `evidence`, `actor / role` and `timestamp` per fact. Never one `approved: true` for everything; an old version's signature is never moved to a new version.

Detection-rate cards: "Critical-defect detection rate · target 99 %" (keep the quantified target, define the defect categories); "Verified detection rate —" (no sample yet, never shown as achieved); "Validation samples · initial state n = 0" (once results exist show detected / total and the confidence lower bound). The denominator is explicit: detection rate = critical defects detected ÷ critical defects seeded in the validation set; it is not "the probability the whole design is correct", and the front end never derives a 99 % or 95 % confidence from "four review layers".

| Display status | Condition of use |
|---|---|
| PASS | This engineering judgement meets an explicit criterion with a checkable result |
| FAIL | The criterion is not met; the technical conclusion stands; commercial acceptance is listed separately and never converts it to PASS |
| Not calculated / assumed | No execution result yet, or a provisional input; state the affected scope and the closing condition |
| N/A · not applicable | Genuinely inapplicable, with the basis written; never used for "not yet done" |

## Components and behaviour

- **Buttons.** One task, one primary action: solid blue for the area's main action, neutral border for secondary actions, 44 px targets. A demo page's buttons act only on local example data and say so.
- **Disclosure.** The conclusion is visible; the evidence expands (why only the affected calcs were rerun: engineering field changed → dependants rerun by object dependency; no engineering change → original verification kept; the impact judgement and the version diff are stored as records). Prefer native keyboard-operable controls; important problems are never hidden in a collapsed section by default.
- **Tables are real work surfaces.** Frozen first column with the engineering ID; units in the column header; numbers right-aligned; filters show the result count; wide tables scroll horizontally; returning to a list restores filters, sort and position.
- **States.** Success, loading, failure and empty are all designed. Distinguish no data yet, no results for this filter, load failure and stale data; an error states the reason and offers retry. Unknown progress shows elapsed time or completed items, never an invented percentage.
- **No floating buttons.** A write action with no connected backend is labelled "demo" or not shown. Design files offer read-only browsing, download, versions and evidence; a new issue draft can be submitted as UNTRIAGED. No login screen is added this period.
- **Keyboard and touch parity.** Tab order, visible focus, named icons; tabs respond to arrow keys and Home / End; dialogs close on Esc and return focus. No key content is reachable only by hover.
- **Task feedback.** A real task shows its start time, input version and the link to the result; a failure shows an actionable reason. "Running · unknown percentage" is an acceptable state; a fake bar is not.

## Engineering content rules

- **Discipline colours are separate from UI semantics.** A theme switch never changes what chilled water, fire or electrical means. Every line carries the system abbreviation, a line type and a legend entry; formal projects reuse the approved discipline legends (`references/drawing-standards.md`).
- **Drawing display boundaries.** Original coordinates and aspect ratio are kept by uniform `viewBox` scaling; no element, annotation or system relation is moved for looks. Dark mode changes only the toolbar and surrounding interface — the drawing keeps its white ground, original colours and line weights, and a whole-drawing CSS invert is forbidden. Exports are generated by sheet size and data source; screen fit is not physical scale, and a schematic is labelled "not for construction".
- **Drawing page facts.** A formal sheet shows sheet number, immutable revision, the actual applicable levels, legend and output sheet size; selecting an element opens its stable object ID, related calculations, issues and source.
- **Evidence chain.** Result → calculation → input → original file → revision, every layer navigable back.
- **Manual changes update by impact.** An engineering change identifies the fields and dependants and reruns the related calcs, sheets, models and BQ; no change keeps the original verification.
- **Publishing binds a full snapshot.** Drafts may update automatically; a formal package is checked complete and published once; the old version stays and is marked superseded.
- **Implementation details stay out of the main path.** Hashes, script commands and library versions live in the "version basis" or "run record" disclosure, not in the user's task path.

## The IFC review page and ingestion / publish feedback

The 3D review page: the 3D canvas, a 320 px issue panel (bottom sheet on phones), the toolbar (level / discipline, clipping, walk, select, mark issue, issue list) at 44 px, the "click a component surface" prompt in mark mode, a form of one sentence plus type with everything else captured automatically, a location preview before submit, a server-issued issue ID on success, a kept draft with retry / export JSON on failure, never "AI has received it" for a local save, list clicks that restore release / clipping / highlight / camera, before and after bound to their own releases, "needs relocation" when the original object is gone. Full contract: `references/ifc-review.md`.

Ingestion and publish feedback: show project, document number, revision, use, the submitted task and the real result links. Status is one of "original stored / converting / awaiting review / current effective / failed", with the counts added / revised / attached / retained / deleted. No invented percentage. A staff upload never triggers a site deploy; program updates are IT operations. The public entry browses and submits UNTRIAGED drafts; writes, issue handling and publishing use the staff's existing company authorisation; "Upload new version" and "Publish as current effective" are separate actions and the second exists only in the workbench for those with the authority. Stable project, document / asset and exact revision links are copyable. Procedures: `references/project-knowledge-base.md`.

## Knowledge-lifecycle UI — behaviours to implement

| Area | Required behaviour and evidence |
|---|---|
| Upload card | The original URL stays the single entry. The project comes from the current page; the AI pre-fills discipline and type; the person confirms "new file / revise existing file / add evidence". Revise opens from the existing file card and carries the document number; evidence binds to a specific revision. The confirmation page shows the impact summary first, then preview and publishing use. Missing files, duplicates and concurrent revisions are explained; a failure keeps the pending content and the existing pages stay usable. Copy: "existing content will be kept"; "stored" and "current effective" are shown apart |
| Current revision card | Use filter: design coordination / construction / operations; each document shows one current per selected use. The card always shows sheet number, title, revision, use, status and effective date — e.g. `HY-0040 · cold water schematic · construction · Rev 04 · current effective · consultant signed`, with Rev 05 as a new draft still in the pending list that does not replace construction Rev 04. Signature, construction issue and as-built acceptance are shown separately and never inferred from "upload succeeded" |
| History drawer | Opens from the file card; lists revisions by time with change summary and supersession. Publishing a new effective revision archives the old one for that use at once; revisions still used elsewhere stay effective. Default search excludes the selected use's history. An old link shows supersession per use and scope with the link to the current one — "Design: superseded by Rev 05; Construction: Rev 04 current" — never a global "obsolete" |
| Endorsement evidence | Keeps the signed original and covering letter; the evidence layer shows signer, date, exact revision, full file hash and applicable scope; a new revision does not inherit the old signature |
| Monthly project check | The PM's (after handover the Operation Owner's) home page lists unassigned files, missing evidence, overdue tasks and handover gaps; exceptions are handled monthly with no manual moving of old versions |
| Operations home page | After handover defaults to asset and system search, location, as-built drawings, O&M, commissioning, warranty and maintenance plan; keeps adding fault, service and alteration records; design history and the frozen handover baseline are retained |

Development convention: the platform is the ProjectBook (`references/project-book.md`); technical components appear in developer notes only, the staff interface shows project, file, status and result. Handover completeness is shown as "completed / required" against the confirmed list, with the reason and confirming person kept for every N/A.

## Builder prompt

Hand this block, unchanged in substance, to the developer or the AI that builds a page:

> Implement the engineering project pages for the Well Smart AI Design Workflow, strictly following this UI Guidance. The style is close to Apple: system fonts, a light-grey ground with white content surfaces, clear hierarchy, restrained blue, thin borders; dark mode uses the corresponding tokens; body width about 1000 px, tables and drawings may be wider. Desktop sidebar 248 px, toolbar 64 px, spacing 4/8/12/16/24/32/48/64, radii 8/12/18, control click targets 44 px. Chinese-first interface text; engineering IDs, units and versions stay exact.
>
> Implement the Overview, Stages, Drawings, Calc book, Review issues and BQ modes: searchable, filterable, version comparison, evidence expanding level by level, with empty / loading / failure states. All demo data is labelled DEMO. The AI designs first, 4–8 weeks is the scheduling target, consultants enter after the package is mature. AI-reviewed, professionally signed, owner-approved, manufacturing-released and published are stored and displayed separately, each with scope / version / evidence; they never substitute for one another.
>
> Critical-defect detection target 99 %; the measured rate and the sample count are listed separately, initial n = 0, never fabricate a success rate. When manual detailing makes an engineering change, rerun only the affected outputs; without a change keep the original verification. The public project book needs no login this period; design files are read-only, and UNTRIAGED issue drafts can be submitted. Engineering drawings keep their own legends, original coordinates and scale; dark mode does not invert drawings; generative images never replace exact drawings.
>
> Support keyboard, focus, 390 px phones, 4.5:1 text contrast, reduced motion and complete printing. No meaningless animation, large gradients, fake progress, colour-only status or fake buttons. Implement interactions by real function; a write without a connected backend is clearly labelled demo; before delivery check desktop, phone, dark mode, print and the evidence chain.
>
> Add IFC 3D review: picking saves both IFC GlobalIds, DB IDs, engineering coordinates in metres, the coordinate-transform snapshot, camera / clipping / snapshot and release / hash; issues persist, the ID mapping is kept across releases, and a missing component never auto-closes an issue. The AI edits source data with IfcOpenShell; Revit production detailing is entirely manual. ADD / REVISE / ATTACH ingestion with stable document_id and immutable revision / hash; the merge summary lists added / revised / attached / retained / deleted, and unsubmitted content is retained. Integrity verification and model conversion run asynchronously; a failure does not change the current effective revision. Current / index / search responses are never served stale. Repeated submission of the same logical item is idempotent; content-hash deduplication must not skip new attachments or asset relations. Do not show infrastructure nouns in the staff interface.
>
> Add the knowledge-base mode: a current per design / construction / operations use and scope; show only the current effective revision by default with drafts listed separately; publishing a new effective revision immediately archives the old one for that use, while revisions still applicable to other uses stay effective. The history drawer shows supersession by use and scope and keeps the original links and evidence. Daily 02:00 automatic reconciliation and backup; monthly exception report at 09:00 on the first business day (project time zone / business-day calendar); PM monthly check target 20 minutes; after handover the Operation Owner takes over; no manual moving of versions. Store endorsement, construction-issue and as-built acceptance evidence separately; consultant signed originals keep their bytes, the scope is bound to the exact revision / hash and is not inherited by new revisions.
>
> Build the handover matrix from S0 and keep adding construction records, assets, as-builts, O&M, commissioning, warranty, spares and training. The operations home page searches by asset / system / location; QR codes link to the stable asset page. The PM and the Operation Owner freeze the Handover Baseline; required records and applicable asset fields / evidence are accepted against an explicit denominator, and missing items are never called 100 %. Handover happens at the same URL; the original design and the handover snapshot are retained; later operations append new records.
>
> Core reading HTML and original-file links are readable without JavaScript; the AI queries the selected use's current revisions by default and cites revision / page / source; history only on explicit request; missing data is never fabricated. Browsing and UNTRIAGED issue drafts need no login; writes, processing and publishing use the existing company authorisation. Where a formal integration is not connected, label it UNVERIFIED clearly and build no fake success button.

## Verification table

| Check | Pass condition |
|---|---|
| 390 / 768 / 1440 px | Body and controls complete; no whole-page horizontal overflow; tables and drawings scroll inside their containers |
| Contrast and legibility | Body text at least 4.5:1; large text at least 3:1; necessary control boundaries at least 3:1; every status has text |
| Operation and zoom | Fully keyboard-operable; visible focus never obscured; readable at 200 % browser zoom; click targets 44 × 44 px |
| Dark / reduced motion | Theme preference switchable and remembered; works when storage is unavailable; drawing colours unchanged; reduced motion honoured |
| Version and engineering status | Scope, version and evidence checkable; AI review, signature, procurement and publication never substitute for one another; n = 0 shows no fabricated result |
| Print | White ground; every page and its evidence fully expanded; long tables repeat headers; no clipped columns; version and date visible |
| Functional completeness | Search, filters, tabs, copy and evidence panels really work; parts without data show DEMO or an empty state |
| Add and retain | Add A, add B, then revise A: the original B and chapters are intact; the same logical submission creates no duplicate revision; a new attachment / asset relation for the same file is kept; a concurrent conflict is recoverable |
| Current vs history | A draft never replaces an effective revision; publishing archives the same-use old revision at once; switching use shows the right revision; history and signed scope are traceable |
| Operations handover | The same URL opens asset-linked records, exact signed / as-built revisions and the handover snapshot; open items and real record completeness are visible |

44 px is the company's uniform requirement. WCAG 2.2 AA's general minimum target size is 24 × 24 CSS px with exceptions; this specification deliberately uses the larger target. Formal printing of engineering drawings is exported separately at the original sheet size and scale. Colour values, layout dimensions and engineering workflow rules are Well Smart's implementation choices; hierarchy, adaptation and readability follow Apple's Human Interface Guidelines and W3C's contrast and target-size guidance.

## Defects a page review must flag

- One `approved: true`; a green tick without scope, version, evidence, actor and timestamp; a signature shown on a version it does not cover.
- A percentage, a success rate or a "95 % confidence" the data does not contain; n = 0 displayed as achieved.
- A dark theme that inverts a drawing; a drawing rescaled non-uniformly or with elements moved; a generative image standing in for an exact drawing.
- A button that writes nowhere and is not labelled demo; "AI has received it" for a local save; an infrastructure noun on a staff screen.
- Hover-only content; a target under 44 px; a page that scrolls horizontally; a print that clips columns or hides evidence.
- A default view that mixes history with current; a draft shown as effective; a supersession notice that declares a revision obsolete for every use.
