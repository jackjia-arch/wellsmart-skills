# Calculation coverage — forcing every calculation to be done, explained or ruled out

## The problem this solves

Left to itself, a model (like a person) does the calculations that are easy and interesting and drifts past the ones that are tedious, need an input it does not have, or that it does not know exist: the fixing spacing on the corner zone of the roof sheeting, the earth-fault loop on the furthest final circuit, the independent overflow on the tower roof, the transfer beam nobody sized because the geotech was late. It then presents a tidy calc book of forty items and the reader cannot see the sixty that are missing. Review layers do not fix this: a reviewer checks what is in front of it. The only defence is a fixed list of everything that could be required, and a rule that every row must be answered at every gate — done, failed, not done and why, or not applicable and why. That turns "the AI forgot" into a visible blank cell.

## The master list

`templates/calc-templates/calc-master-list.csv` is the company minimum: 218 calculation rows across MECH (39), ELEC (34), STR (29), HYD (27), FAC façade and roof (23), FIRE (18), ACU (10), THM (10), ARC (9), CIV (8), VT (5), TRF (4), CON (2). Each row: `calc_key` (stable, e.g. `FAC-FIX-02`), discipline, group, title in English and Chinese, `stage_due` (the stage by which it must be done, cumulative thereafter), the inputs it needs, the method / standard (names only — clause numbers and limits come from the standards digest by record id at calc time), the outputs it produces, the acceptance criterion, the only conditions under which `N/A` is acceptable, and the deliverable it feeds (sheet family, schedule, page). Rows are never deleted; a project adds rows (`<DISC>-PRJ-<NN>`) for anything specific to it, and Jack adds company rows when a project reveals a gap (record the lesson in the library at the same time).

The master list is deliberately wider than the disciplines a project may need. A villa answers the tower rows with `N/A — single storey, no pressurisation (NCC …)` and a person accepts that; the row still appears, so the omission is a decision, not an accident.

## The coverage file

At every gate the operator (or the AI, as the first step of the gate report) runs:

```
python3 scripts/calc_coverage.py init --stage S6 [--disciplines MECH,ELEC,HYD,FIRE] --carry calcs/coverage-S3.csv
python3 scripts/calc_coverage.py check calcs/coverage-S6.csv --stage S6 --register calcs/calc-register.csv
python3 scripts/calc_coverage.py html  calcs/coverage-S6.csv --out reports/coverage-S6.html
```

`init` writes `calcs/coverage-<stage>.csv` with every master row due at or before the stage; `--carry` copies the answers from the previous gate so a row answered at S3 is not retyped, but it is re-confirmed (a PASS at S3 whose inputs changed at S5 must be rerun and re-dated). The AI fills the columns:

| column | what goes in it |
|---|---|
| `status` | `PASS` · `FAIL` · `NOT CALCULATED` · `TBC` · `N/A` — nothing else, never blank |
| `calc_ids` | the calc register IDs that answer this row (PASS / FAIL require at least one; the register verdict must agree) |
| `result_summary` | result vs limit in one line (`412 kW vs 450 kW plant; margin 9 %`) |
| `reason` | for NOT CALCULATED: why it could not be done; for TBC: which input is unresolved; for N/A: the specific condition that makes it inapplicable (≥ 15 characters; "not required" is not a reason) |
| `missing_input` | for NOT CALCULATED: exactly what is needed and from whom (authority letter, geotech report, vendor curve, PD decision) |
| `owner` | the person who will obtain the input or make the decision |
| `expiry_gate` | the gate by which NOT CALCULATED / TBC must be resolved; a gate at or before the current one blocks the gate |
| `accepted_by` | for N/A: the person who accepted the inapplicability (defaults to the PD; never the AI) |
| `evidence_ref` | calc book section, sheet, file or document_id / revision where the evidence lives |
| `blind_checked` | Y / N / N/A — whether the second family re-calculated this item in the review round |
| `date` | date of the answer (no revision labels) |

`check` fails on: any blank status; PASS or FAIL without calc IDs, result and evidence; a calc ID missing from the register or whose register verdict contradicts the coverage status; NOT CALCULATED without reason, missing input, owner and expiry gate; TBC without reason, owner and expiry gate; N/A without a specific reason and an acceptor; any expiry gate at or before the current gate; any master row due at or before the stage that is missing from the file. Warnings (errors with `--strict`): rows overdue from an earlier stage, FAIL rows (they never pass a gate), unknown project rows. The summary (rows per discipline per status) and the rendered HTML go into the gate report's "Calculation coverage" section (`templates/gate-report.md`); a gate report whose coverage check fails is not a gate report.

## Rules for the AI when filling the file

1. Answer every row, in order, before writing any prose about the stage. Do not stop at the rows you find interesting.
2. `PASS` means the calculation exists as a calc page (`templates/calc-templates/calc-page.md`) with a calc ID, a script or worked steps, a limit from the digest and a technical status of PASS. A number typed into the table without a page is not a PASS.
3. `NOT CALCULATED` is honest and allowed between gates; it is a blocker only when its expiry gate arrives. Write what is missing precisely enough that the owner can act: "Sydney Water pressure / flow letter for 372 Pitt St — PM to request", not "authority data".
4. Never answer `N/A` because the calculation is hard, because a consultant "will do it", or because it is "standard practice". `N/A` is for a condition that removes the requirement (no gas, no basement, single storey below the pressurisation trigger, no commercial kitchen) and it names that condition and the clause where possible.
5. "To be verified manually", "per manufacturer", "by others", "by the contractor" are not statuses. If a vendor must supply a curve or a test value, the row is `TBC` with the vendor as owner and a gate; if a contractor designs it (fire detection detailing, reinforcement shop drawings), the row still needs our design intent calc (PASS) and a note of what the contractor adds.
6. When a row is answered `PASS` from a library typical (a tested detail, a standard module), say so in `evidence_ref` and confirm the typical's conditions apply (span, pressure zone, exposure); otherwise it is not a PASS.
7. Carry-forward rows are re-read at every gate: if any input listed on the calc page changed since the date on the row, the status is not PASS until the calc is rerun.
8. Rows outside the disciplines in scope for the stage stay in the file as `N/A — outside scope at this stage` only if the master `stage_due` is later; a row that is due is never excused by scope.
9. When the calc cannot be run because a tool is not available in the current environment (EnergyPlus, OpenSees, a vendor selection tool), the status is `NOT CALCULATED`, the missing input is the tool and the machine it runs on (`references/toolchain.md`), the owner is the operator, and the expiry gate is the current gate — this is the case Jack most wants surfaced, so it is never hidden inside a PASS.

## Where the discipline templates come from

The rows for MECH, ELEC and HYD follow the calculations already written up for 372 Pitt Street (C-01 … C-58: DHW energy and storage, heat-pump allocation, water flows and pipe sizes, pump power, roof stormwater with independent overflow, sanitary stacks, pressure zoning, break-tank pressure, insulation thickness on the cylindrical basis, pumping energy, full-load currents, breaker selection, cable capacity, volt drop, busway, transformer transfer, earthing, guest-room allowances, floor DB balance, lift and fire-pump starting, short-circuit, earth-fault loop, discrimination, busbar sizing and forces, switchboard losses, harmonics, switchroom clearances, metering, life-safety supply, lengths, arc flash, lightning, power factor, UPS, derating, system volume and expansion, riser expansion, plant-room heat, refrigerant safety, cooling towers, roof plant noise, potable storage, sumps and OSD, grease arrestor, hot-water zones, fire pump TCO) generalised into template rows. The FAC (façade and roof: wind pressure zones, glass, framing, brackets and anchors, **fixing spacing per zone**, cladding spans, movement, weatherproofing, combustibility, BMU, roof sheeting fixing patterns, purlins, roof drainage, condensation, roof safety, plant plinths, waterproofing, balustrades, openings, maintenance), STR (loads, systems, analysis, every member family, foundations, durability, fire, penetrations, temporary works, staged construction, serviceability, interfaces), ACU (external, internal, plant, ducts, vibration, pipes, room acoustics, EWIS, construction) and THM (loads results, façade options, energy, JV3 / H1, NatHERS, daylight, condensation, airtightness, water, carbon) blocks are new and are the ones Jack's previous sets did not force.

## Relationship to the other checks

The calc register (`templates/calc-register.csv`) lists the calcs that exist; the coverage file lists the calcs that must exist. The high-risk table in the gate report is the checker's half-day view of the twenty items that can hurt people or the programme; it is drawn from the coverage file, not written separately. The seeded-defect validation (`references/review-and-gates.md`) includes "row silently omitted" as a defect category: a validation sample can be a master row deleted from the coverage file to see whether the review catches it. The drawing checklists (`references/sheet-content-checklists.md`) force what is drawn; this file forces what is calculated; `references/services-coordination-2d.md` forces the two to meet before 3D.
