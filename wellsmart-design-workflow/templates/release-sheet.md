# Manufacturing Release Sheet — [Project] — Package [package id]

Project: · Package id: · Package scope (systems, levels, items): · Date: YYYY-MM-DD
Prepared by (AI operator): · Checked by: · Procurement lead: · PD:

One sheet per procurement package. Manufacturing is released only by this sheet; G4 is a detailed design baseline and G5 freezes the model — neither is a release. Every line carries a technical status from the fixed vocabulary (PASS · FAIL · NOT CALCULATED · TBC · N/A with reason). A FAIL on any line blocks the release; the PD cannot waive it. No version labels on this sheet — date only.

## 1. Revision set (all at the same revision)

| Item | Sheet / document | document_id | revision_id | SHA-256 (first 16) | Same revision as the BQ? |
|---|---|---|---|---|---|
| Production drawings | | | | | yes / no |
| BQ (PROCUREMENT) for this package | | | | | — |
| Specification section(s) | | | | | yes / no |
| Schedules / schematics referenced | | | | | yes / no |

Frozen release cited (`scripts/catalogue.py release`): project_release_id = 

## 2. Release conditions

| # | Condition | Evidence (document refs, calc IDs, release id, issue ids, task / round) | Status (PASS · FAIL · NOT CALCULATED · TBC · N/A) | Owner | Closes by |
|---|---|---|---|---|---|
| 1 | Vendor performance confirmed at project conditions (duty, capacity, power, noise, certification) | vendor confirmation document_id / revision_id; equipment ids | | | |
| 2 | Vendor dimensions, weights, connections and maintenance clearances confirmed | vendor drawing document_id / revision_id; equipment ids | | | |
| 3 | Calculations closed | calc IDs (`<DISC>-<NNN>`) and calc-book revision | | | |
| 4 | Interfaces closed (structure, penetrations, supports, power, controls, other packages) | interface register lines; sheets | | | |
| 5 | Clash and maintenance / replacement routes closed | release id; issue ids CLOSED; remaining NEEDS_RELOCATION = 0 | | | |
| 6 | Peer review closed | task, round, state (must be CLOSED); open P0 / P1 = 0 | | | |
| 7 | Approvals affecting this package | which approval / performance solution / authority item, and its status | | | |
| 8 | Production drawings, BQ and spec at the same revision (section 1) | | | | |
| 9 | Dual certification / local-only rule satisfied for the category | source certificate; NATA / ILAC report; scheme mark; or "local-only" | | | |
| 10 | Vendor handover requirements written into the RFQ / PO (O&M, as-built, serials, points list, commissioning, warranty basis, spares, training, contacts; asset ids and upload points) | RFQ / PO document_id / revision_id | | | |
| 11 | MEP packages only: final coordination completed in BIM to LOD 400 by the MEP department (fittings, supports, seismic restraint, sleeves, spools) against the frozen IFC / DB and the crossings register; design changes written back by element id | BIM model revision; MEP department sign-off; write-back diff reference | | | |

Counts: PASS · FAIL · NOT CALCULATED · TBC · N/A . Release requires FAIL = 0, NOT CALCULATED = 0 and no TBC on lines 1–8; MEP packages also require line 11 = PASS.

## 3. Decision

Tick one:

- [ ] RELEASE FOR MANUFACTURE — all lines 1–10 PASS or N/A with reason.
- [ ] RFQ ONLY — quotations may be obtained; no order, no production.
- [ ] CAPACITY RESERVATION WITH CANCELLATION CONDITION — amount reserved: · exit cost if cancelled: · cancellation condition (what must close, by when): · decision record id (`templates/decision-record.md`) where the amount and exit cost are recorded:

Items that must close before the next decision (line numbers, owners, dates):

## 4. Signatures

| Role | Name | Signature | Date |
|---|---|---|---|
| PD | | | YYYY-MM-DD |
| Procurement | | | YYYY-MM-DD |

This sheet is registered in the knowledge base against the package (`scripts/catalogue.py add … --doc-type release-sheet`) and cited in the gate report's releases table. A release is not an endorsement, not a publication and not a technical PASS; it is the fourth separate fact.
