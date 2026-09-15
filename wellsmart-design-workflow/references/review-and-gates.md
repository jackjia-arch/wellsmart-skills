# Peer review, the high-risk table and gates

This file says what review must achieve and what counts as evidence at a gate: the four layers, the high-risk table, the technical status rules, the exit criteria, the quantitative acceptance and the seeded-defect validation, the review loop's passes and states, the issue register and the gate report. The mechanics of running a round — commands, packet contents, feedback schema, designer and reviewer rules, provider variables — live in `references/review-hub.md` and are executed by `scripts/peer_review.py`; nothing there is repeated here.

## Why four layers

A second model "having another look" cannot catch the mistakes it would make itself: a misremembered clause, a unit slip, a wrong spatial relationship, a detail that cannot be built. Two language models reviewing each other therefore share blind spots, and no number of extra rounds removes them. So the work is split by what each kind of checker is bad at: numbers go to scripts, answers go to a blind re-calculation by a different model family, judgement goes to an LLM review, and the last layer is a person who reads one fixed table and decides. Each layer is designed to catch what the previous one cannot, and each leaves evidence that can be read later without re-running anything.

Layers 2 and 3 run as a review loop bound to G1, G3, G4 (one task per discipline stream), G5 and the whole package at S8, and as a light loop at G4a; layers 1 and 4 run at every gate. No loop is bound to G0 or G2; an ad-hoc loop on one sheet or one calc may be run between gates but never replaces the gate loop.

## Layer 1 — deterministic script checks

What it catches: everything that is a matter of consistency or of a numeric limit. Evidence is the check output itself, copied into the review packet as `reports/checks.json` and quoted in the gate report by count.

| Check | What it compares | Failure means |
|---|---|---|
| DB ↔ drawings ↔ model ↔ schedules | Every tag on a drawing exists in the schedule and the DB; every DB element appears on the drawings; IFC quantities match the DB within the stated tolerance; units, levels and grids identical across disciplines | An output was hand-edited or a generator ran on a stale DB; fix the DB, regenerate |
| Code-limit tables | Every rule with a numeric limit (velocities, pressure drops, voltage drop, outdoor-air rates, illuminance, W/m², egress width per occupant, door and corridor clear widths, accessible circulation, FRL tags on rated elements, separation distances), evaluated from the DB against the digest record, not from memory | A limit is exceeded or the limit could not be fetched by record id (`CLAUSE TO CONFIRM`) |
| Clash | Hard clashes and clearance clashes: maintenance space, door swings, statutory headroom, penetrations versus structure | Unresolved geometry; an IFC issue per clash (`references/ifc-review.md`) |
| Calc-ID coverage | 100 % of numbers on drawings resolve to a calc register row; calculation coverage per discipline against the template rows due at the stage (`scripts/calc_coverage.py` → `calcs/coverage-<stage>.csv`) | A number without a calc ID, or a due calc still NOT CALCULATED |
| Sheet QA | `python3 scripts/annotate.py check <sheet>` and the embedded overlay counts: leader crossings, text on lines or text, density over threshold, content items missing for the sheet type | The sheet is not issued until the count is zero |
| Model and catalogue integrity | Model checks after every IFC generation (`references/toolchain.md`); `scripts/catalogue.py` ids, hashes and revision links | The package cannot be frozen against a complete manifest |

A version whose script checks fail is not packeted for review. Script success is a data-consistency result, never an engineering PASS: a sheet can be internally consistent and wrong, so the gate report keeps script results in their own section, separate from technical judgement.

## Layer 2 — blind re-calculation by a second model family

What it catches: a wrong answer — arithmetic, method, a misapplied clause, an input copied wrongly, an order-of-magnitude slip. The second family receives only the raw fact inputs, the brief, the applicable standards and the task. It never receives design answers, calculation code, selections, conclusive drawings or historic feedback. It computes the key numbers independently — demands, cooling and heating loads, pump duties, tank volumes, member actions and sizes, outdoor-air rates, egress widths and travel distances, fault currents — and submits its answer, which is frozen (hashed in the round folder) before the comparison package is opened. Reviewer sessions are separate from designer sessions.

| The blind pass receives | The blind pass never receives |
|---|---|
| Site pack facts (survey, geotech, authority data), the brief, the area schedule and occupancy inputs | Our results, verdicts and margins (stripped from `calcs.json`) |
| The applicable standards with edition and state variations, as digest records | Calculation scripts and their code |
| The calc's raw inputs (values, units, sources) and the quantity to compute — not our method, formula, clause choice or script (the packet's blind copy strips them; `peer_review.py selfcheck` proves it) | Selected products, equipment schedules, vendor data |
| The task: which quantities to compute and to what precision | Drawings that show the answer (sheets with sizes, schedules, key data boxes) |
| Nothing from earlier rounds | Earlier feedback, responses or issue history |

Evidence: per calc, the design value, the blind value, the difference and the tolerance, written into the stage calc book and summarised in the gate report. The tolerance is declared per calc in the packet before the blind pass (default 5 % general, exact for counts; 1–3 % is the expected spread between structural solvers on the same model, so a structural difference above that is a modelling difference to be explained, not noise). A difference over tolerance is a P1 finding on that calc; a disputed calc goes to a third model family running the same script, and if still disputed to the checker. Both values and the difference stay in the register even after the issue closes.

What it cannot catch: an error in the shared facts. If the survey level or the occupancy in the brief is wrong, both computations are wrong together; facts are therefore checked at layer 1 (site pack, digest source pages) and questioned at layer 3.

## Layer 3 — LLM review

What it catches: reasonableness of assumptions; code edition and state variations; buildability and construction sequence; procurement reality (is the product in the library, what is its certification status and lead time); maintenance access and equipment replacement routes; interfaces between disciplines; the actual graphics of every sheet in scope and the system connectivity and installation space they show; TCO and simple-annual-return arithmetic in decision records. A model family different from the designer's does this, in its own session, reading the packet only.

Evidence: `feedback.json` with the seven checks (`inputs`, `calculations`, `drawings_and_text`, `user_constraints`, `drawing_rules`, `calc_book`, `decision_roi`), each with `passed` and verifiable evidence, and findings with title, severity, location (sheet, tag, calc ID, decision ID), evidence and acceptance criterion. "Checked" without evidence is not a check. Manifests are used to navigate the package, never as proof that a drawing is correct; the SVG, the geometry and the rendered views are what the reviewer inspects, and the share of sheets actually inspected is recorded.

## Layer 4 — a person reads the high-risk table

People do not calculate. The checker (the PD by default) reads one fixed table, per item: done or not / method, inputs and calc ID / result against the limit / technical status / what closes it. About half a day per gate. The PD then decides what the gate report asks — the commercial trade-offs, the direction of any design change, the assumptions to carry — and signs the gate or does not.

## The high-risk list

The table covers these items, always, and nothing on the list is dropped because it "does not apply" without an N/A row stating why:

- Structure: load paths (vertical and lateral), foundations versus geotech, transfer structures, temporary conditions (propping, crane bases, construction-stage loads).
- Fire and egress: egress widths and travel distances, compartments, FRL, fire pumps and tanks, stair and lobby pressurisation, FIP and booster positions.
- Electrical: fault current versus switchgear rating, generator essential loads, earthing.
- Hydraulic: pressure zones and PRVs, Legionella regime, backflow prevention, flood level.
- Mechanical: intake / exhaust separations, refrigerant charge in small rooms, kitchen exhaust.
- General: clear heights, maintenance space, equipment replacement routes, shaft sizes, façade combustibility, waterproofing.

Specialist streams add their own rows when the brief includes them (acoustic, traffic, vertical transport, ESD, façade, civil, access); the columns do not change.

What each row's evidence must name, and when the row normally becomes calculable, is set out below. The right-hand column is planning guidance derived from the stage map in `SKILL.md`, not a rule from the handbook: the project's calc register and the coverage file (`calcs/coverage-<stage>.csv`) decide what is due at each gate. Before a row is calculable it reads NOT CALCULATED with the missing input named.

| Item | The evidence cell names | Normally first calculable |
|---|---|---|
| Load paths, vertical and lateral | Structural system (S1 memo), gravity and lateral actions, load combinations, member checks, drift, the modelling-assumptions sheet and the solver comparison | System G1; 2D members G3; full calcs G4 |
| Foundations vs geotech | The geotech report revision as a fact input; bearing / pile capacities against the structural loads; settlement; groundwater | G3 |
| Transfer structures | Spans, column loads above, transfer element actions and deflections, construction-stage sequence | G3; NOT CALCULATED until spans and loads exist |
| Temporary conditions | Propping and back-propping, crane and hoist bases, construction-stage loads and sequence | G4; revisited in S10 construction planning |
| Egress widths and distances | Actual occupant numbers per space, exit widths, travel distances measured on the GA, applicable clauses or the PS basis | Strategy G1; measured G2 / G3 |
| Compartments and FRL | Compartment boundaries, FRL per element with the tested-system reference, penetration treatment | Strategy G1; geometry G3; details G4 |
| Fire pumps and tanks | Supply basis, pressure zones, most-disadvantaged hydraulics, maximum pressure, effective storage, vendor curve | Space G1; duty G3; vendor-confirmed G4a |
| Pressurisation | Stair / lobby air quantities, door forces, relief paths, fan duty | Schematic G3; fan G4a; calc G4 |
| FIP / booster positions | Brigade access, block plan, distances, signage | Layout G2; G3 |
| Fault current vs switchgear rating | Source, impedance, tolerances, motor contribution, switchgear capacity, discrimination | Preliminary G3; equipment G4a; final G4 |
| Generator essential loads | Essential load schedule, generator sizing, step loads, fuel and ventilation | Schematic G3; selection G4a; G4 |
| Earthing | Earthing system, conductors, lightning-protection basis | G4 |
| Pressure zones / PRV | Static head per zone, outlet pressure window, PRV settings | G3 |
| Legionella regime | Storage and delivery temperatures, return, mixing-valve positions, flushing and maintenance regime | G4 |
| Backflow prevention | Hazard rating per connection, device type and location, testability | G4 |
| Flood level | Site flood level as a fact input; critical plant and openings above it | Site pack G0; G1 |
| Intake / exhaust separations | Distances between intakes and exhausts, cooling towers and flues per system, shown on the GA and elevations | G3 |
| Refrigerant charge in small rooms | Charge per circuit against room volume and occupancy class; ventilation or detection where required | G4a (needs the selected unit) |
| Kitchen exhaust | Hood capture, exhaust quantity, duct route and cleaning access, fire protection, discharge position | Route G3; fan G4a; G4 |
| Clear heights | The ceiling-zone section per zone: structure, services, ceiling, tolerance | G3 |
| Maintenance space | Clearances around plant per manufacturer and standard; access panels | G4a; clash G5 |
| Equipment replacement routes | Route from each plant room to outside for the largest replaceable item; door and lift sizes | Geometry G3; item size G4a |
| Shaft sizes | Space table against the actual services; riser sections | Space table G1; G3 |
| Façade combustibility | Façade system and materials, test evidence, attachments | Façade option G1 (PD); G3 |
| Waterproofing | Membranes, falls, thresholds, planters and wet areas, tested systems | G3 / G4 |

## The mandatory table format

Every gate report carries the table in these four columns and no others:

| Check item | Completion evidence / method (calc ID, inputs, clause) | Result vs limit and technical status | Gate handling |
|---|---|---|---|

The rows below are format examples taken from the handbook. They are not project results and must never be copied into a report as if they were.

| Check item | Completion evidence / method (calc ID, inputs, clause) | Result vs limit and technical status | Gate handling |
|---|---|---|---|
| Fire pumps / tanks | Complete supply basis, pressure zones, most-disadvantaged hydraulics, maximum pressure, effective storage and the vendor curve | TBC — project calculations not attached | Close before the affected fire selection and before manufacturing release |
| Egress / accessibility | Actual occupant numbers, routes and clear dimensions; applicable clauses / PS basis | TBC — a drawing tag alone does not prove PASS | Items affecting the geometry freeze close first |
| Fault current | Source, impedance, tolerances, motor contribution, switchgear capacity and discrimination evidence | TBC — a simplified calculation is not automatically the final design | Close before equipment manufacturing release |
| Transfer level | Missing spans / column loads; analysis incomplete | NOT CALCULATED | The affected structural freeze cannot pass |
| Hard technical failure | Completed calculation exceeds the applicable limit | FAIL | Change the design or complete a valid alternative solution |
| Demonstrably inapplicable item | Applicability basis and review record | N/A | Does not count as a passed calculation |

Rules for filling it in:

- The evidence cell names the calc ID(s), the two or three inputs that drive the result, the governing clause (standard, year, clause, digest record id) and the method. In a real report it reads like `F-012 · static head to highest hydrant, residual required, friction loss, effective tank volume · <standard>:<year> cl <n>, digest <id>`. A row whose evidence cell is empty is a NOT CALCULATED row, whatever the status cell says.
- The result cell shows the number against the limit, then the status word. "PASS" alone, without the number and the limit, is a defect.
- Never write "to be verified manually", "recommend review", "subject to confirmation" or "to be confirmed by the consultant". If it can be calculated, calculate it; if it cannot, name the missing input and write NOT CALCULATED or TBC.
- The gate-handling cell says what closes the item and before which freeze or release it must close (geometry freeze, equipment freeze, manufacturing release of a named package). "Ongoing" is not gate handling.
- One row per item on the list per gate; items that matured since the last gate keep their row so the PD sees the status change.

## Technical status rules and what the PD can and cannot do

- `PASS` — completed evidence meets the criterion. The evidence is a calc ID with inputs, method and clause, or a check output; never a tag on a drawing, a manifest entry or a script exit code.
- `FAIL` — the technical criterion is not met. Only a design change or a valid, completed alternative solution closes it. A FAIL can never be frozen and never converted to PASS by acceptance.
- `NOT CALCULATED` — not yet computed; the row names the missing input or reason.
- `TBC` / `ASSUMED` — the input is unresolved; the value in use is an `ASSUMED — TBC:` entry with range, affected objects, owner and expiry gate.
- `N/A` — demonstrably inapplicable, with the applicability basis and the review record. N/A is never used for "not yet done".

The PD decides commercial trade-offs, chooses the direction of a design change, records a non-financial reason for adopting extra CAPEX, accepts carrying a non-blocking assumption to a later gate, and signs or withholds the gate. The PD cannot convert a FAIL to PASS, waive a FAIL on a financial argument, freeze a hard FAIL or a critical calculation that is due at the gate, treat a script pass as an engineering PASS, or treat an AI pass as an endorsement. When an unresolved technical issue goes to HUMAN_REQUIRED, the same rules apply: the PD picks the way forward; the status stays what the evidence says.

## Gate exit criteria

A gate closes only when all of these hold:

1. Known P0 and P1 issues = 0.
2. Technical FAIL = 0 on the high-risk table and in the calc register for the calcs due at this gate.
3. Blocking assumptions expiring at this gate = 0.
4. Every closed item has a new revision and a re-verification record, not just a reply.

An assumption is blocking when a high-risk row's status, a freeze item or a release depends on it; a non-blocking assumption bounds work that can be redone cheaply if the value moves. An expired blocking assumption is resolved (the fact obtained, the calcs rerun), re-bounded to a later gate with the PD's recorded acceptance and the affected scope kept provisional, or the gate does not close. An assumption is never presented as a PASS.

P2 and P3 issues may remain open across a gate; they stay in the register with an owner and appear in the gate report's review-round summary. A freeze is the current traceable design baseline, changeable by revision; it is not a promise of no rework. With only non-blocking provisional inputs, bounded preparatory work continues on the stated scope. G4 is a detailed design baseline, not a manufacturing release; manufacturing release is per package by release sheet (`templates/release-sheet.md`) and needs the closed evidence for that package, not the gate signature.

## Quantitative acceptance: the 99 % target

The metric. Critical-defect detection rate = number of seeded critical defects correctly identified with locatable evidence ÷ number of seeded critical defects in the independent validation set. "Correctly identified with locatable evidence" means the finding names the object, calc or sheet and states what is wrong; a vague "check the loads" against a seeded missing load does not count. Critical means P0 or P1 under a fixed grading written before the test: errors that affect applicable compliance, structural / fire / access performance, an essential system's operation, or cause major manufacturing rework. False positives, recurrence after a fix and unverified closures are reported separately; the number of review rounds is never used as an accuracy measure.

Thresholds. With zero misses, the exact binomial one-sided 95 % lower confidence bound on the detection rate is 0.05^(1/n).

| Level | Zero-miss sample threshold | Claim that can be made |
|---|---|---|
| Pilot baseline | 59 independent representative critical defects, 59 / 59 detected | One-sided 95 % lower bound on detection ≥ 95 % within the tested distribution |
| Production target | 299 independent representative critical defects, 299 / 299 detected | One-sided 95 % lower bound on detection ≥ 99 % within the tested distribution |
| Current status | Validated n = 0; seeded testing not executed | Target ≥ 99 %; measured rate and lower bound: not established |

299 is a predeclared sample size, not a total to be extended after misses until the number passes. If any defect is missed, the report gives the actual detected and missed counts and the miss types, and recomputes the lower bound by the same exact binomial method; the zero-miss thresholds no longer apply. As arithmetic only: one miss in 299 gives a one-sided 95 % lower bound of about 98.4 %, one miss in 59 about 92.2 % — a single miss moves the claim down a level, which is why the sample is planned to be representative rather than easy.

Independence. Copies of one defect, five review rounds of the same defect, and a retest of the same item after a fix are one sample, not several. Coverage across design scenarios, disciplines, difficulty and severity is planned before seeding; correlated samples are counted as effective samples, not nominal ones. After any change to the review process (prompts, scripts, model, packet rules) the claim is re-established on a fresh hold-out set; the old set is spent.

Illustrations that are not measurements. If each layer detected 70 % of the defects remaining after the layers before it, combined detection would be 1 − 0.3⁴ = 99.19 %; at 50 % per layer it would be 93.75 %. These are conditional-rate arithmetic, and a layer's standalone accuracy cannot be substituted for its conditional rate; nothing in them is measured performance. Conversely, 99 % detection is not 99 % whole-design correctness: a design with 100 independent defects, each detected with probability 0.99, has only 0.99^100 = 36.6 % probability of having every one found. That is why the gate criteria are stated on the actual engineering register (known P0 / P1 = 0, FAIL = 0, expiring blocking assumptions = 0) and the detection validation is displayed beside them, never instead of them.

Reporting. Wherever the 99 % figure appears — gate report, project book, pilot report — it is shown as target versus measured, with n, detected, missed, false positives and the confidence lower bound as separate fields. "99 %" without those fields is a defect.

## Seeded-defect validation protocol

1. Freeze before the test: the reviewer model and version, the prompts, the script versions, the defect sampling rule and the sample size n. Record the hashes in the validation record.
2. Prepare the seeded set independently of the design and review sessions. The test items and their answers are kept from every designer and reviewer session; whoever seeds does not review, and the seeded packets are indistinguishable from real packets to the reviewer.
3. Seed across the categories below, with the distribution across scenarios, disciplines, difficulty and severity fixed in advance.
4. Run the full loop as it would run on a project: script checks, blind pass, comparison, drawings and interfaces. No hint that a packet is a test.
5. Score each seeded defect as detected only when the finding locates it (object, calc ID, sheet) and describes the actual error; record false positives separately with their cost in designer time.
6. Report: n, detected, missed (with the type of each miss and which layer should have caught it), false positives, the lower bound computed by the exact binomial method, and the process version the result belongs to. A miss is a finding against the process: fix the layer, then validate again on a fresh hold-out set; the earlier result stays on record.
7. Keep the validation record beside the project records it was run on (or the pilot's DEMO records); the gate report cites it by version and date.

| Category | Typical seed | Counts as detected only if the finding states | Layer expected to catch it |
|---|---|---|---|
| Wrong units | A DB input entered in the wrong unit (kPa for m head, mm for m, kW for kVA) | The calc ID and the unit error | 1 (unit check) or 2 (blind value differs) |
| Missing loads | A load case dropped from a combination; a plant load missing from a slab; a fixture group missing from a demand | The element or calc and the omitted load | 2 |
| Wrong clause applicability | A state variation, table note or exception applied to the wrong case; a superseded edition | The clause and the applicability condition that was misread | 3, verified on the source page |
| Geometric clash | A duct through a beam; a door swing into a clearance; headroom under a transfer beam | The two elements and the location | 1 (clash) and 3 (actual graphic) |
| Control omission | An interlock or sequence missing from the cause-and-effect matrix or pump logic | The system and the missing function | 3 |
| Procurement specification | A scheduled product that does not meet the duty, envelope or certification specified | The asset ID and the mismatch | 3 |
| Recurrence of a closed issue | A previously closed defect reintroduced by a regeneration or manual edit | The original `issue_id`, reopened | 3 (issue_updates) |
| Graphic deleted but tag kept | A shape removed from the SVG while its tag, manifest entry and schedule row survive | The sheet and the tag | 3 (SVG inspection); layer 1 must not report consistency from the manifest alone |

## Preventing the four layers from sharing one error

- The blind pass receives the raw fact inputs, the brief, the applicable standards and the task, nothing else: no design answers, no calculation code, no selections, no conclusive drawings, no historic feedback. Its independent answer and assumptions are submitted and frozen before the comparison package opens. Designer and reviewer sessions are separate; the designer never edits the round folder after review has run.
- Two solvers fed from one DB and agreeing prove solver consistency, not correctness. Geometry, boundary conditions, loads, units and modelling assumptions are checked independently of both solvers — against the site pack, the brief, the digest source pages and the modelling-assumptions sheet.
- A manifest indexes a sheet and lets quantities be compared; it never certifies the drawing. The reviewer inspects the SVG / geometry and the rendered views; the coverage actually inspected is recorded per round; the seeded set always includes a deleted-graphic-with-tag case so that a manifest-only review is caught.
- Two models extracting the same clause from a standard can share a missed table note. 100 % of the key clauses (those on which a high-risk row or a PASS depends) are checked back to the source page for applicability conditions, table notes and exceptions; the rest is sampled by risk and the coverage is written down. Extraction agreement is recorded as agreement, not as truth; missing source text is `CLAUSE TO CONFIRM`.
- Every closure records its evidence; recurrence of a closed issue is one of the seeded categories precisely so that "closed" is tested, not assumed.

## The review loop

Each loop runs at most five rounds on a frozen version. Round 6 is never built; what is still open after round 5 goes to HUMAN_REQUIRED. The passes within a round:

| Pass | Input and action | Output / constraint |
|---|---|---|
| Pre-check | File completeness, standards versions, actual graphics and data, reproducibility of every calc, references and units | Script results and technical judgement in separate columns; a hard technical FAIL is not released into review |
| First pass: blind re-calculation | An independent session reads only the raw facts, the brief, the applicable standards and the task; design answers, code, selections and historic feedback are withheld | Independent calculations and assumptions submitted and frozen before the design answers are opened |
| Second pass: design comparison | Compare the independent results with the design package; check applicable clauses, assumptions, calculation methods, TCO and simple annual return | Each difference located to an object / calc ID / sheet number with its actual size and impact; entered at a fixed severity |
| Third pass: drawings and interfaces | Inspect actual graphics, renders, system connectivity, maintenance and installation space and cross-discipline interfaces; manifests help navigation only | Full scope and actual coverage recorded; "read the manifests" is never reported as "all drawings checked" |
| Response and re-verification | The designer answers every open issue `accepted` / `partial` / `disputed` with the basis and the revised version; the reviewer verifies the closure evidence of older issues | Issue IDs kept across rounds; a fix that regresses reopens the issue; unresolved after round 5 → HUMAN_REQUIRED |

Round states, who acts and what each leaves behind:

| State | Meaning | Who acts | Record |
|---|---|---|---|
| REQUESTED | A review of `<gate>-<stream>` has been asked for | Operator (one sentence, or `REQUEST.json` on the company server) | The request with task, stream, note |
| VALIDATING | Pre-check running on the working tree | Scripts | `reports/checks.json`; a failing version is not frozen |
| FROZEN | Packet built from a commit and hashed | Script | `round-<n>/index.json` with commit, file hashes, packet hash |
| REVIEWING | Blind pass, comparison, drawings and interfaces | Reviewer family | `calls/*.raw.txt`, `feedback.json` |
| RESPONSE_REQUIRED | Required issues are open; the designer must answer each | Designer (Claude) — changes files, regenerates, commits | `round-<n+1>/responses.json` |
| CLOSED | Verdict pass; no required issue open; full check done | — | Final `feedback.json`; register updated |
| HUMAN_REQUIRED | Reviewer `needs_human`, designer `request_human`, two malformed replies, or round 5 without a pass | PD / checker | `state.json` reason; the gate report's "what the PD must decide" |

`scripts/peer_review.py` records these names in `state.json` (files written by the earlier version of the script are mapped on load); `status` prints them.

Technical packages carry a separate state, DRAFT → READY_FOR_RELEASE → PUBLISHED, bound to a use (design / construction / operations), a scope and the current pointer. Ingesting files never advances it; a CLOSED review is one of the inputs to READY_FOR_RELEASE, and publishing is a gate or release decision (`references/project-knowledge-base.md`). A tool that did not run stays UNVERIFIED; only an execution record shows success.

Loops bound to gates: G1 (concept), G3 (freeze), G4 as one task per discipline stream (`G4-ARCH`, `G4-STR`, `G4-MECH`, `G4-ELEC`, `G4-HYD`, `G4-FIRE`, `G4-COMB`), G5 (model), and the whole package at S8 for G6; G4a runs a light loop on the equipment schedule and selection comparisons. At S8 the specialist streams enter the final review in the same batch as ARCH / STR / MEP, each with its own high-risk rows. The packet emphasis per gate is tabulated in `references/review-hub.md`.

Retained per round, in `reviews/<task>/round-<n>/`: the raw reviewer responses (`calls/*.raw.txt`), `feedback.json`, the designer's `responses.json`, the model and tool versions used, the cost of the round, and the full input hashes (commit, per-file hashes, packet hash in `index.json`). A retry keeps the same request_id so that the record shows one request answered twice, not two requests. A timeout and a schema error are explicit recorded states, not silence; an empty or missing `feedback.json` is never read as "no issues". `feedback.json` is never edited after it is written; a round folder with feedback is never overwritten.

## The issue register

`issues/issue-register.csv` is written only by `scripts/peer_review.py` and has these columns: `issue_id, task, round_raised, severity, title, location, evidence, acceptance, status, round_closed, owner, closure_evidence, date`. `issue_id` (`I-NNNN`) is stable across rounds and tasks; `location` is a sheet, tag, calc ID or decision ID; `acceptance` says what evidence will close the issue, written when it is raised; `closure_evidence` is filled only by the reviewer's verification.

Severities: P0 blocker, P1 major, P2 minor, P3 suggestion. The reviewer schema's `blocker / major / minor / suggestion` map to these one to one. P0–P2 are required issues for the reviewer's pass verdict — the loop reaches CLOSED only when none is open — while the gate's own exit criterion is P0 / P1 = 0; a P2 still open when a loop ends in HUMAN_REQUIRED therefore goes to the PD at the gate with its owner and target round, and P3 is never dressed up as required. Fixed grading for P0 / P1: errors affecting applicable compliance, structural / fire / access performance, an essential system's operation, or causing major manufacturing rework; the grading is the same one used to score the seeded validation.

What closes an issue: an actual change to the DB, calc, sheet or model, regenerated and committed, plus the reviewer's verification of that change in a later round (`issue_updates` with evidence). The designer's reply is never closure evidence; "accepted" without a changed file is still open. A dispute carries a re-computable basis and goes to a third family or to the checker; agreeing with the reviewer to end the loop is a defect. A closed issue that recurs — the same defect reappearing after a regeneration or a manual edit — is reopened under its original `issue_id`, not raised as new, so that recurrence is visible in the register.

The gate report's review-round summary and the project book's review pages are generated from the register and the round folders; nobody edits them by hand.

## The checker's half-day

The checker reads the high-risk table and the open-issue summary; nothing else is required reading. Per row the checker confirms four things: that the evidence cell names a calc ID, inputs and clause; that the result cell shows a number against a limit with a status word; that the status is the one the evidence supports; and that the gate-handling cell names a closing action and a freeze or release. A row that fails any of the four is sent back before the gate meeting. Half a day per gate is the budget on a tower with three parallel AI streams; if the table needs longer, the table is wrong, not the budget.

## The gate report

One report per gate, from `templates/gate-report.md`, dated, no version label. It must contain: the outputs produced (with document_id / revision_id where registered); the script checks as data-consistency results, separate from technical judgement; the blind re-calculation summary (calc IDs compared, tolerance, differences over tolerance); the calculation coverage per discipline (`calcs/coverage-<stage>.csv` attached); findings by severity; the assumptions carried with their expiry gates; the cost movement against the previous cost plan; the decisions taken this stage, each with its simple annual return or recorded non-financial reason; the high-risk table in the four mandatory columns; the review-round summary (task, rounds used, state, open issues by severity); the status of each specialist stream; the manufacturing release sheets affected; what the PD must decide; the freeze list; and the provisional items. A report without the high-risk table, or with a row lacking a technical status, is not a gate report.

## Change after a freeze

A change request states what changes and why, which frozen parameters it touches, which calcs, sheets, models and BQ lines must be rerun (by calc ID, sheet number and element ID), and the cost and programme impact. Regeneration happens only after the PD approves; the approval goes into `decisions.md`, the affected calcs get new register rows or new results with the script version, and any signed scope the change touches returns to its S9 package as a new revision (`references/certification.md`). A change that arrives as a manual edit is diffed first: annotation-only changes are recorded as "no design change" and rerun nothing; a design change is written back to the DB by element ID and only its dependants are regenerated.

Re-review after a change is scoped by the same impact list: the regenerated calcs go through a blind pass again, the regenerated sheets and model parts through the drawings-and-interfaces pass, either as an ad-hoc loop (`--task ADHOC-<what>`) or inside the next gate loop, and every issue the change closes cites the new revision as its closure evidence. A change that touches a high-risk row resets that row's status to what the new evidence supports; the previous PASS does not carry over.

## Operating metrics

Per project, and first on the pilot, the review process records its own cost and yield so that the 99 % claim and the 4–8 week target are checked against facts rather than asserted: human hours per gate (operator and checker separately); real model cost per round and per task; rounds used per task; critical defects found later — by the consultant at S9, by the certifier, or on site — as misses against the layer that should have caught them; false positives and the designer time they consumed; the volume of consultant-requested changes; and the seeded-validation results with n, detected, missed, false positives and lower bound. These numbers go into the pilot report and the gate report's review-round summary; none of them is a substitute for the exit criteria.
