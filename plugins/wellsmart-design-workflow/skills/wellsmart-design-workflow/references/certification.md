# Certification pathways, the S9 package and consultant engagement

External consultants, certifiers and authorities enter at S9, against a mature package. The region decides how the package is prepared and who carries statutory responsibility; it never decides when consultants are engaged. This file is a process reference, not legal advice: the S0 Certification Pathway names the applicable instruments for the project, and contract wording is confirmed by lawyers before signature.

## The principle: consultants after a mature package

The AI completes every discipline first — design, calculations, drawings, DBR, specialist draft reports and the company's own four-layer review (S8 closed, G6 signed). Only then is one frozen, complete package handed to consultants at S9 to procure a fixed fee. The quote is made on the frozen package and states what it includes: the review and feedback rounds, the RFI work and the approval work.

Early design iterations, where most of the churn is, are handled by the AI, so the consultant is not paid round after round for changes that a premature appointment would have produced. During S9 the AI answers every comment and makes every revision; the consultant states the basis and the affected objects, the AI returns the diff, the affected recalculations and the closure evidence. Variations arise only from approved owner scope changes, out-of-scope new facts or rounds beyond those included, at agreed rates and with the amount and reason stated before the work starts.

Four to eight weeks is the target for the AI package. Consultant response, statutory consultation, certification and authority approvals run on their own programmes: S9 duration follows the actual written responses, no fixed number of months is assumed, and approval inside the design target is never promised. The 10-working-day review target per package is the starting quote, confirmed for the package's actual complexity.

Nobody contacts a consultant, certifier or authority before S9 — not to "check", not to "line them up", not "to be safe". Statutory responsibilities are met as each region requires and are never renamed away.

## Regional table

At S0 the AI fills this table for the project into the Certification Pathway; at S9 the package is handed over accordingly.

| Region | S0: what the AI establishes | S9: how the mature package is signed | Execution boundary |
|---|---|---|---|
| NSW | Building class; the regulated-design scope; whether the building is in a strata scheme; whether it contains serviced apartments. Lock the applicable edition by the actual declaration / lodgement date and the transitional provisions. | Check every condition of the hotel / motel exemption, not "non-strata" alone. Where DBP applies, the appropriately registered practitioners take responsibility for the regulated designs and make the declarations. | The hotel / motel exemption requires the building to be outside a strata scheme and to contain no serviced apartments. CC, fire performance solutions and the other authority processes are listed separately, each with its own programme. |
| QLD | The AI prepares requirements, facts, concepts and the engineering work plan. Identify the point at which regulated professional engineering services begin, and who provides them: a qualified RPEQ, or genuine direct supervision by one. | An external engineer may substantively review the package and issue the applicable certificates. "Verified" on Form 15 does not replace responsibility for the earlier professional engineering services. | A qualified in-house person can carry the supervision responsibility; this does not automatically require early external appointment. Checking finished work and signing it is not direct supervision. Renaming the work "owner's design development" does not change its substance. Without a qualified person, continue facts / concept preparation and do not present supposedly supervised formal engineering services. |
| NZ | Distinguish commercial design, residential restricted building work and the BCA's evidence requirements. The AI prepares the complete design basis and review package. | The engineer substantively evaluates the design proposed for adoption, takes responsibility for the accepted scope and supplies the corresponding PS1 / PS2 or other evidence; the BCA decides what evidence it accepts. | A complete AI package reduces the work but never guarantees a stamp-only service. Key recalculations and necessary revisions are inside the engagement scope. |
| Japan | Establish the separate kenchikushi and approval pathway for the project; do not transfer AU / NZ certificate rules. | The AI prepares the owner's technical package; appropriately qualified kenchikushi carry the statutory design, supervision and submission duties. | A final signature cannot replace the statutory design responsibility. |

Consequences for the package. NSW: a regulated design goes out in regulated-design format for the practitioner's declaration; an exempt building's package still lists the CC and the performance-solution route separately. QLD: the S0 pathway records who the RPEQ is and when supervision began; the S9 engineer's review is a separate record from that supervision. NZ: whether the BCA will accept a PS1 on an adopted design, a PS2 review, or something else is confirmed at S0 and written into the package B scope, not assumed at S9. Japan: the AI package is the owner's technical package used to brief and negotiate with the kenchikushi office; it does not replace their design.

## What the S0 Certification Pathway records

The pathway is an S0 output frozen at G0 with the brief. It is a short document with these fields, each with its source and the date it was established; anything not yet known is `TBC` with an owner and an expiry gate.

| Field | What is recorded |
|---|---|
| Jurisdiction and building class | State / country; class per the applicable code; mixed-class parts listed |
| Regulated-design scope | Which designs are regulated (NSW), which services are professional engineering services (QLD), which work is restricted building work (NZ) |
| Exemption conditions | NSW hotel / motel: strata status and serviced apartments, each as a fact with its source; never a label |
| Edition lock | Code edition, state variations, digest hash, the declaration / lodgement date that fixes the edition and the transitional provision relied on |
| Statutory engineering responsibility | QLD: the RPEQ (in-house or external) and the date supervision begins, or the statement that no qualified person is yet available and formal engineering services have not begun; NZ: PS1 / PS2 route per discipline as the BCA accepts; Japan: the kenchikushi route |
| Engagement package per discipline | A / B / C per discipline and region, with the reason |
| Authority processes | DA / CC / BA / building consent, fire performance-solution consultation, water, power, and any other authority process, each with its own line and programme |
| Retention and insurance | Retention periods for the evidence chain and the company's own insurance position for this project's contract and region |
| Programme | The S9 review programme (10 working days per package as the starting target) and the approvals programme, separate from the 4–8 week design target |

## Performance-based fire

Performance solutions follow the same rule — the AI designs first, the statutory consultation comes in the required order. From S3 the AI drafts the PBDB / FEB; by S6 it runs the smoke and egress analyses that can actually be executed with the frozen geometry. When the mature package enters S9, the applicable preliminary consultation is completed (in NSW the FRNSW performance-solution process), and the final report, the signatures and the CC conditions follow that feedback.

Until the consultation returns, the acceptance criteria, the boundaries and the affected geometry are labelled provisional (`ASSUMED — TBC:` with owner and expiry); everything that does not depend on them continues. Revisions the consultation requires are made by the AI, quickly; the need for them is never turned into a case for appointing the fire engineer early.

## The three engagement packages

Each package is a defined scope with a fixed fee on the frozen package. One project may combine them (A for structure, B for fire, C for the CC).

**A · Verify & certify** — independent review and certificates, where that pathway applies. The scope must specify: the exact drawing / calc / model versions (by `revision_id` and hash); a full check of the high-risk list; the sampling scope and rate for everything else; the certificates to be issued; the RFI deliverables; and the number of review rounds included. QLD direct supervision is never packaged into a retrospective review by default; if supervision was in-house, the record says so.

**B · Adopt & complete** — the consultant adopts the design and completes it, where the pathway needs a responsible designer (NZ PS1, NSW regulated designs). The scope must specify: the adoption scope; the recalculations the consultant will perform; the modifications the consultant may make and how they are returned (basis, affected objects, diff from the AI); the final signing responsibility; and the rounds included. The quote is made on the complete AI package; adoption is never treated as automatic acceptance.

**C · Application support** — submissions and authority replies, listed separately: DA / CC / BA / building consent, fire, water and power applications, and their RFIs. Starts when the relevant package is actually mature. Statutory fees, authority response periods and external waiting time are shown separately from the consultant's fee and never absorbed into the 4–8 week target.

## The ten mandatory contract items

Fixed scope. The annex lists the frozen versions (release id, `document_id` / `revision_id` / SHA-256 per file), the inputs, the deliverables, each certificate to be issued, the exclusions, and the responsibility for verify / adopt / application work separately.

Reliance on inputs and outputs. The consultant may rely on the factual inputs the company supplies — survey, geotechnical, authority data — and must substantively verify the design outputs. A certificate that relies on unverified design outputs is hollow and may void the insurance behind it; the contract says which is which.

Qualification and duty of care. Record the jurisdiction, the registration class, the responsible scope and the professional duty standard that applies. A signature that the region does not recognise for that scope is not promised, by either side.

Liability and insurance. PI cover, liability limits, the period of cover and the coverage for certifying designs prepared by others are negotiated against the project's actual size and the policy's actual scope. Written evidence of the insurance comes with the quote, before fees are discussed further.

Regional responsibility. QLD direct supervision is recorded separately from the final review; NZ adoption and evidence scope are explicit; NSW is written as regulated or exempt with the conditions that make it so.

Review plan. Each package starts with a quoted target of ten working days, then confirmed for its complexity. The fixed fee includes a stated number of rounds of normal review, replies and re-checks of revisions.

VO boundary. Ordinary compliance comments on the original package and re-checks within the agreed rounds are inside the fixed fee. Added owner scope, out-of-scope new facts and additional rounds follow agreed rates, with the amount and the reason stated before the work is done.

Design changes. The consultant states the basis of each requested change and the affected objects. The AI submits the diff, the affected recalculations and the closure evidence; a full rewrite of the package each round is never the deliverable.

IP and data. The company keeps the DB, the drawings and the models. The contract grants the ongoing right to use the consultant's calculations and feedback, the right to process them with AI, and open, transferable export formats, so that another consultant can pick up the same package if this one withdraws.

Payment and disputes. Payment follows milestones: package review, closure, signature. Technical disputes are recorded with reasons and go to an independent assessment route. Fees are what the quote says; no fixed discount on "normal design fees" is assumed, in either direction.

The reliance split in practice:

| The consultant may rely on | The consultant must substantively verify |
|---|---|
| Survey, levels, boundaries, easements as supplied in the site pack | Every calculation in the calc package, at least the high-risk list in full and the rest by the sampling rate in the scope |
| The geotechnical report and its parameters | Member sizes, load paths, foundation design derived from those parameters |
| Authority data: flood level, service pressures and capacities, network constraints | Pressure zoning, pump duties, switchgear ratings derived from them |
| The brief's occupancy, use and hold period | Egress, fire strategy, loads and system sizing derived from them |
| The locked code edition and state variations as recorded at S0 | Applicability of each clause to the design, including table notes and exceptions |

## The S9 package and how the AI assembles it

Contents, all at the frozen revision:

- Drawings as PDF and DWG (DWG converted from the DXF generators), full sets per discipline, with the level–sheet–revision matrix as the completeness evidence.
- IFC for all disciplines; RVT if S10 has started.
- The calc package: calc book (`CALC-BOOK_<project>_S8_<date>.html` with its JSON export), the calc register, the per-calc originals, the Load & Energy Report and the Energy Compliance Report with the model files.
- The structural `.e2k` text model with the modelling-assumptions sheet and the analysis results. The engineer runs the `.e2k` and compares reactions, periods, drifts and key member forces; differences between solvers on the same model are expected at the level `references/toolchain.md` states, and anything beyond that is a modelling difference the assumptions sheet must explain.
- The DBR, the compliance matrix, the PS register, the SiD register and the specification.
- The assumptions list with every remaining `ASSUMED — TBC:` and its owner, and the issue register showing every P0 / P1 closed with evidence.

Decision records with value-engineering dollar figures stay internal; the DBR states the adopted basis. Consultant-facing documents are in English, dated; drawings carry the key design-data box, the assumptions box and calc IDs.

The AI assembles it in this order:

1. Confirm S8 is CLOSED and G6 signed: no P0 / P1, no FAIL, no expired blocking assumption. If any is open the package is not built.
2. Register every output in the knowledge base (ADD / REVISE by `document_id`), then freeze a project release: `project_release_id` → the full list of `document_id` / `revision_id` / SHA-256 (`references/project-knowledge-base.md`; `scripts/catalogue.py` until the portal is live).
3. Generate from the catalogue, never by hand: the transmittal; the drawing index; the version manifest with hashes; the per-file list.
4. Write the transmittal: what is asked of each signatory and under which package (A / B / C); the responsibility split from the regional table; the review programme; how comments are returned (issue register ids, or the issue APIs when live); and that the PD is the contact for external correspondence.
5. Publish the release as `current_design` for the scope "S9 package" and hand over the URL and the manifest. The documents carry their date; revision identity comes from the manifest, never from a hand-typed label.
6. From then on, every consultant comment becomes an issue with a stable id; every revision is a new `revision_id` with parent, reason and impact list; the manifest is re-issued for the affected files only.

## Handling consultant comments during S9

Consultant comments are worked like review findings, in the same register and with the same rules (`references/review-and-gates.md`):

| Step | Who | What is produced |
|---|---|---|
| Log | AI | One issue per comment with severity, location (sheet, tag, calc ID), the consultant's basis and the affected objects; unclear basis is asked back through the PD, not guessed |
| Answer | AI | `accepted` / `partial` / `disputed` with evidence; a dispute carries a re-computable basis and is put to the consultant with the numbers, never argued by assertion |
| Change | AI | The DB edited by element ID; affected calcs, sheets, models and BQ lines regenerated; a diff, the reruns and the closure evidence returned — not a rewritten package |
| Re-check | Consultant | Within the included rounds; the re-check result is recorded against the issue |
| Close | Consultant's verification | An issue closes on verified change; a technical FAIL the consultant finds is a FAIL under the fixed status rules and is closed only by a design change or a valid alternative solution |
| Decide | PD | Direction of a change where options exist; owner scope changes that become variations; never a waiver of a FAIL |

Each round's correspondence, the consultant's marked-up files and the AI's replies are attached to the exact revisions they concern; the issue register is the single list of what is open.

## Authority processes

Each authority process is a separate line in the pathway and in the S9 programme, never folded into the consultant's fee or the design target:

| Process | Package | What the line records |
|---|---|---|
| DA (where required) and planning conditions | C | Lodgement basis, conditions that bind the design, dates |
| CC / BA / building consent | C, with A or B signatures as inputs | Certifier or BCA, the certificates and declarations required, statutory fees, response period, external waiting time |
| Fire performance-solution consultation | B or A as the pathway needs, C for the submission | PBDB / FEB revision submitted, consultation outcome, resulting conditions, provisional items closed |
| Water, power and other utility approvals | C | Application revision, authority requirements written back as facts, connection conditions |
| RFIs from any authority | C | Each RFI as an issue with a stable id, the AI's draft reply, the PD's release of it |

## Endorsement archival

Every endorsed or signed original and its covering letter go into the same project knowledge base, within one working day of receipt (company target). The procedure:

1. In the portal choose "Add consultant endorsement" against the record or the package (until the portal is live: `scripts/catalogue.py attach`, bound to the exact revision). Upload the received signed originals, the endorsement letter or the original confirmation email, and the exact file list.
2. Identify what was signed: bind `document_id`, `revision_id` and the SHA-256 of the original for each file; for a package signature keep the per-file manifest. The AI proposes the match, the PM verifies it. A mismatch or an unclear scope stays "pending" and is not marked endorsed.
3. Keep the originals byte-for-byte. Previews, OCR text and search extracts are linked derivatives. Where a digital signature exists, record its verification result; a scanned signature is never recorded as a verified digital signature.
4. Mark only the covered revision "consultant-endorsed", with the scope (floors, systems, disciplines) and any conditions. A later design change creates a new revision that never copies the old signature or inherits the endorsement; the affected signed scope goes back to its S9 package.
5. Consultant-issued revised drawings become new revisions in the catalogue; only actual engineering changes are written back to the DB and rerun.

The endorsement record (`templates/endorsement-record.json`) carries these fields:

| Field | Content |
|---|---|
| signer | The person who signed, as named on the document |
| firm | The signing firm |
| discipline | The discipline the signature covers |
| date | The date on the signature or covering letter |
| conditions | Conditions attached to the endorsement, verbatim or by reference to the letter |
| document_id | The stable knowledge-base id of the endorsed document |
| revision_id | The exact revision covered — the only revision that may be marked endorsed |
| SHA-256 | Hash of the received original, byte-for-byte |
| scope | Floors, systems, disciplines and package covered; for a package signature, the per-file manifest |
| covering letter | Reference to the attached original letter or confirmation email |

Endorsement, construction issue and as-built acceptance are three separate records with their own evidence: an endorsed design is not proof of what was built. `current_by_use` moves only through a publish with this evidence attached, never through the upload itself.

## Company records

The company keeps its own evidence chain regardless of who signs: the raw facts (survey, geotech, authority data with their revisions), the DB versions, the calculations with the blind re-calculation values, the issue register with closure evidence, the signing scope of every endorsement, and every later design change with its impact list. Retention periods and the company's own insurance position are decided at S0 for the project's contract and the region's obligations, and written into the brief.

Obtain comparable quotes on the mature package before negotiating multi-project rates; a firm quoting on a frozen, complete package is quoting on something it can inspect. The consultant's recalculation of key items is part of the signing responsibility, not a reversal of the AI-led process, and it is priced inside the package, not as a variation.

## Defects

- Contacting, "sounding out" or appointing a consultant, certifier or authority before S9.
- Renaming statutory engineering work as "owner's design development" or "concept" to avoid supervision.
- Treating "verified" on a Form 15 as if it were direct supervision of the earlier engineering services.
- Assuming the NSW hotel / motel exemption from "not strata" alone, without checking for serviced apartments and the other conditions.
- Copying an endorsement to a new revision, or altering the bytes of a signed original.
- Marking a revision "consultant-endorsed" when the manifest match is pending or the scope is unclear.
- Quoting or budgeting consultant fees as a fixed percentage of "normal design fees" instead of actual quotes on the package.
- Showing value-engineering dollar figures, or draft version labels, in consultant-facing documents.
- Promising an approval date inside the 4–8 week design target, or treating consultant rework as evidence that the appointment should have been earlier.
