# Decision Record D-[NNN] — [Project] — [subject]

Project: · Decision id: D-NNN · Stage / gate: S[x] / G[x] · Date: YYYY-MM-DD · Currency: · Hold period (from the brief; default 10 years): · Discount rate (only if NPV / IRR is used):
Prepared by (AI operator): · Checker: · PD:

First principles first, then TCO, then the return rule. A technical FAIL is never resolved by a financial argument; a FAIL option cannot be adopted. No version label on this record — date only.

## 1. Context

What is being decided, which objects it affects (levels, systems, equipment ids), what triggered it (brief, gate finding, issue id, vendor reply), and what is frozen around it.

## 2. Assumptions people commonly make — and which were stripped

| # | Common assumption | Stripped? | Why (what is actually known) |
|---|---|---|---|
| 1 | | yes / no | |
| 2 | | yes / no | |

## 3. Facts that are provably true

| # | Fact | Source (calc ID, standard · year · clause · digest id, vendor document_id / revision_id, measurement) |
|---|---|---|
| 1 | | |
| 2 | | |

Rebuilt from the facts alone, the requirement is:

## 4. Options

| | Option A (baseline) | Option B | Option C |
|---|---|---|---|
| Description | | | |
| Technical status (PASS · FAIL · NOT CALCULATED · TBC · N/A) with calc IDs | | | |
| CAPEX | | | |
| Annual energy cost | | | |
| Annual maintenance | | | |
| Annual replacement provision (major components ÷ life) | | | |
| Annual staffing / operating effect | | | |
| Annual net OPEX | | | |
| Hold-period cash flows (year 0 … year n; residual value if any) | | | |
| TCO over the hold period (CAPEX + Σ annual net OPEX − residual) | | | |

## 5. Return against the baseline

| Measure | Option B vs A | Option C vs A |
|---|---|---|
| ΔCAPEX (incremental) | | |
| Annual net saving (baseline net OPEX − option net OPEX; added maintenance and replacement already inside) | | |
| Simple annual return = annual net saving ÷ ΔCAPEX | | |
| Simple payback = ΔCAPEX ÷ annual net saving | | |
| Meets the company rule (≥ 15 %, i.e. payback ≤ 6.67 years)? | yes / no | yes / no |
| NPV at the discount rate (if needed; full cash flows) | | |
| IRR (if needed; full cash flows) | | |

The 15 % threshold is a simple annual return, not an IRR. Illustration from the handbook: 100,000 extra CAPEX, 15,000 per year net saving for 10 years, no residual → simple annual return 15,000 ÷ 100,000 = 15 %, simple payback 6.67 years, IRR ≈ 8.14 % (the rate at which Σ 15,000 ÷ (1 + r)^t for t = 1 … 10 equals 100,000). At any discount rate above 8.14 % that option's NPV is negative even though it meets the 15 % rule; state both when the PD asks for NPV / IRR.

## 6. Risks

| Risk | Option(s) | Effect on programme / cost / compliance | Mitigation | Owner |
|---|---|---|---|---|
| | | | | |

## 7. Decision

| Item | Entry |
|---|---|
| Option adopted | |
| Technical status of the adopted option | must be PASS (or NOT CALCULATED / TBC only on items with a named owner and expiry gate) |
| Financial basis | simple annual return ___ % · payback ___ years · rule met: yes / no |
| Non-financial reason (required when the rule is not met: compliance, operations, brand, programme) | |
| Decided by | PD · YYYY-MM-DD |

## 8. Affected calcs, sheets, models and BQ lines

| Calc IDs to rerun | Sheets to regenerate | Models / releases | BQ lines | Signed scopes affected (endorsement ids) |
|---|---|---|---|---|
| | | | | |

Change route: change request → PD approval → regenerate the affected items only; write the decision id into `decisions.md` and the gate report's decisions table.
