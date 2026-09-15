# Gate Report — [Project] — S[x] → G[x]

Project: · Stage: S[x] · Gate: G[x] · Date: YYYY-MM-DD
Operator: · Checker: · PD:

One report per gate, dated. No version label anywhere in this document. Technical statuses use only PASS · FAIL · NOT CALCULATED · TBC / ASSUMED · N/A; script results are data-consistency results and never an engineering PASS.

## 1. Outputs produced

| Output | Path / sheet numbers | document_id | revision_id | Generated from DB commit |
|---|---|---|---|---|
| | | | | |

Library items reused (path, locked version): 

## 2. Checks run (data consistency)

| Check | Script / version | Result (counts) | Notes |
|---|---|---|---|
| DB ↔ drawings ↔ model ↔ schedules | | | |
| Code-limit tables (from digest records) | | | |
| Clash — hard / clearance | | | |
| Calc-ID coverage on drawings | | 100 % / n missing | |
| Sheet QA (`scripts/annotate.py check`) — crossings / text-on-line / density | | | |
| Model checks (IFC ↔ DB) | | | |
| Catalogue integrity (`scripts/catalogue.py`) | | | |

A passing row here says the data is consistent; the technical judgement is in sections 4, 5 and 9.

## 3. Blind re-calculation summary

Reviewer family / model / version: · Blind answer frozen at (hash, time): · Comparison opened at:

| Calc ID | Quantity | Design value | Blind value | Difference | Tolerance | Over tolerance? | Issue id |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Calc IDs compared: n of m due at this gate. Differences over tolerance: n (each has an issue id above). Third-family arbitration run on: 

## 4. Calculation coverage

| Discipline | Template rows due at this gate | DONE | NOT CALCULATED (with reason) | N/A (with reason) | FAIL |
|---|---|---|---|---|---|
| ARCH | | | | | |
| STR | | | | | |
| MECH | | | | | |
| ELEC | | | | | |
| HYD | | | | | |
| FIRE | | | | | |
| specialist streams | | | | | |

The coverage file `calcs/coverage-<stage>.csv` (produced by `scripts/calc_coverage.py`) is attached to this report. Every FAIL in this table also appears in section 9.

## 5. Findings by severity

| Severity | Raised this stage | Closed this stage | Open at gate |
|---|---|---|---|
| P0 blocker | | | |
| P1 major | | | |
| P2 minor | | | |
| P3 suggestion | | | |

Open P0 / P1 at the gate must be 0. List every open P0 / P1 by issue id with its acceptance criterion if the gate is being presented anyway (it will not close).

## 6. Assumptions carried (ASSUMED — TBC)

| Parameter | Value | Range | Affects (objects) | Owner | Expires at | Blocking? |
|---|---|---|---|---|---|---|
| | | | | | G[n] | yes / no |

Blocking assumptions expiring at this gate: n (must be 0). Assumptions re-bounded to a later gate with the PD's recorded acceptance: 

## 7. Cost movement

Cost Plan [n] (this gate) vs Cost Plan [n−1]: total, and the main drivers by discipline / package. BQ status: ESTIMATE / PROCUREMENT.

| Item | Previous | This gate | Δ | Driver |
|---|---|---|---|---|
| | | | | |

## 8. Decisions this stage

| Decision id | Subject | Option adopted | ΔCAPEX | Annual net saving | Simple annual return | Payback | Non-financial reason (if adopted below 15 %) | PD decision date |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

Each row points to its decision record (`templates/decision-record.md`). A technical FAIL is never resolved by a row in this table.

## 9. High-risk table (mandatory format)

One row per item on the high-risk list (`references/review-and-gates.md`) plus the specialist streams' rows. Never "to be verified manually". FAIL blocks the gate; the PD cannot convert a FAIL to PASS.

| Check item | Completion evidence / method (calc ID, inputs, clause) | Result vs limit and technical status | Gate handling |
|---|---|---|---|
| Load paths — vertical and lateral | | | |
| Foundations vs geotech | | | |
| Transfer structures | | | |
| Temporary conditions | | | |
| Egress widths and travel distances | | | |
| Compartments | | | |
| FRL | | | |
| Fire pumps / tanks | | | |
| Pressurisation | | | |
| FIP / booster positions | | | |
| Fault current vs switchgear rating | | | |
| Generator essential loads | | | |
| Earthing | | | |
| Pressure zones / PRV | | | |
| Legionella regime | | | |
| Backflow prevention | | | |
| Flood level | | | |
| Intake / exhaust separations | | | |
| Refrigerant charge in small rooms | | | |
| Kitchen exhaust | | | |
| Clear heights | | | |
| Maintenance space | | | |
| Equipment replacement routes | | | |
| Shaft sizes | | | |
| Façade combustibility | | | |
| Waterproofing | | | |

Counts: PASS n · FAIL n · NOT CALCULATED n · TBC n · N/A n. FAIL must be 0 for the gate to close.

## 10. Review-round summary

| Task | Rounds used (max 5) | State | Open P0 | Open P1 | Open P2 | Open P3 | Round folder |
|---|---|---|---|---|---|---|---|
| | | REQUESTED / VALIDATING / FROZEN / REVIEWING / RESPONSE_REQUIRED / CLOSED / HUMAN_REQUIRED | | | | | `reviews/<task>/round-<n>/` |

Seeded-defect validation cited (version, date): target ≥ 99 % · n = · detected = · missed = · false positives = · one-sided 95 % lower bound = (write "not established" if n = 0).

## 11. Specialist streams status

| Stream | Scope at this gate | Outputs at this gate | Open issues (P0 / P1) | Status |
|---|---|---|---|---|
| Acoustic | | | | |
| Traffic / civil | | | | |
| Vertical transport | | | | |
| ESD / thermal | | | | |
| Façade | | | | |
| Access | | | | |
| Fire engineering (PS) | | | | |

## 12. Releases and manufacturing release sheets affected

| Package | Release sheet (`templates/release-sheet.md`) | Status at this gate (RFQ only / capacity reservation / released) | Items in section 9 that must close first | Exit cost if cancelled |
|---|---|---|---|---|
| | | | | |

G4 is a detailed design baseline, not a manufacturing release; nothing is released without its sheet.

## 13. What the PD must decide

Numbered, one decision per line: the question, the options, the AI's recommendation with its basis, and what stays provisional under each option. Commercial trade-offs and the direction of design changes only — no technical FAIL is put here for acceptance.

1. 

## 14. Freeze list at this gate

| Parameter / object set | Value or revision frozen | Source (calc ID, sheet, DB commit) | Change route after freeze |
|---|---|---|---|
| | | | change request → PD approval → regenerate affected only |

A freeze is the current traceable baseline; a FAIL is never frozen.

## 15. Provisional items

| Item | Why provisional (assumption id / pending consultation / unconfirmed vendor data) | Affected objects | Owner | Resolves by |
|---|---|---|---|---|
| | | | | |

Gate result: CLOSED / NOT CLOSED — reason:
PD sign-off: ______________________ Date: __________
