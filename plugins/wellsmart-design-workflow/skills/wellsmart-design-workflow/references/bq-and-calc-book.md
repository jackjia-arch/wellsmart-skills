# BQ with spec, the calc book, and decision records (first principles · TCO · simple annual return)

Three "one file" deliverables. Each is generated from the repository, never typed: the BQ from the DB (plus ratio rules in the estimate, plus the installation detail in the procurement version), the calc book from `calcs/`, the decision records from `decisions.md`. All three are HTML readable without JavaScript (`references/project-book.md`), each with a JSON export for machines, and all three are registered in the project knowledge base by ID (`references/project-knowledge-base.md`). File names carry a date, never a revision label; the revision is the catalogue's `revision_id`.

## 1 BQ with spec — two versions

What the design hands to procurement is not a quantity list but a bill that can be priced and ordered from: main materials, installation consumables, specification, recommended supplier and alternative, certification status and lead time, per row. There are two versions and they are never confused:

| Version | When | Quantities | Label |
|---|---|---|---|
| `BQ (ESTIMATE)` | S6, with the G4 detailed design baseline; feeds the cost plan and the RFQ drafts | Main items taken off the DB; fittings and consumables by ratio or per-metre factors from `library/rules/bq-ratios.csv`, each such row labelled with its rule id | Every page and export is headed ESTIMATE |
| `BQ (PROCUREMENT)` | S10, or earlier per procurement package once that package is mature (release sheet closed, `templates/release-sheet.md`) | Actual itemised installation components generated from the DB and the installation detail; no percentage or per-metre factors anywhere | Headed PROCUREMENT, bound to the package id and the same revision as the drawings and spec it prices |

A ratio-based BQ presented as the procurement BQ is a defect (SKILL.md, defects list). An RFQ carries the same-revision BQ, specification chapter, drawings and the manufacturing-release conditions for that package; before the release sheet closes, the RFQ or a cancellable capacity reservation is the most that may be issued, with the exit cost recorded.

### Row schema

`bq/estimate.csv` (S6) and `bq/procurement-<package>.csv` (per package), rendered to `BQ-ESTIMATE_<project>_<date>.html` and `BQ-PROCUREMENT_<project>_<package>_<date>.html`. Every row carries, in this order:

`package, item_code, element_id, location, sheet_no, sheet_revision, description, material_grade, actual_size, interface, standard_certification, unit, net_qty, waste_qty, spares_qty, supplier_sku, supplier, alt_sku, alt_supplier, rate_fob, rate_landed, currency, lead_time_weeks, status`

plus the traceability columns `qty_source` (the DB query, the installation-detail record, or — estimate only — the ratio rule id), `consumable_of` (parent `item_code` for installation consumables), `calc_id`, `ve_ref`, `cert_status` (complete | pending | local-only) and `notes`.

- `element_id` is the stable DB id (or the run / penetration / support id) the quantity was taken from; `location` is level + room / grid zone; `sheet_no` + `sheet_revision` is the sheet and the catalogue revision that shows the item.
- `material_grade` and `actual_size` are values, never phrases: "insulation to code" is a defect; the row says `mineral wool, 38 mm, R 1.0, foil faced, AS/NZS 4859.1, NCC J6 [digest record id]`. Thicknesses come from the materials / support / insulation matrix (Pitt doc 26 pattern) and the Section J digest records, per service and per location (internal / external / plant room / concealed).
- `interface` names what the item connects to or is fixed into (flange standard and PN, substrate for anchors, the pod or cassette boundary, the fire-rated element for a penetration).
- `standard_certification` carries the product standard and the certification the row needs (WaterMark / RCM / WELS / ActivFire / NATA report / dual certification); `cert_status` says whether procurement holds it.
- `status` runs `estimate → rfq → quoted → reserved (cancellable, exit cost noted) → released (release sheet id) → ordered`; `released` is only ever written with a closed release sheet.
- Supplier from the product library only (`products/index.csv`); a SKU not in the library gets `cert_status = pending` and a procurement note; local-only categories (fire pumpsets, hydrant and sprinkler valves, fire-rated cables, smoke-control fans, essential switchboard sections, dry fire) carry `local-only` and an Australian / NZ supplier.
- The VE register governs the BQ lines: a VE item accepted at G3 / G4 changes the row; a VE item under discussion appears as an alternate row flagged `ve_ref`, never silently. No dollar VE figures in any consultant-facing export.

### Quantities in the ESTIMATE

Main items are taken off the DB: pipe and duct lengths per run with DN / size; fixtures, terminals and equipment from the element lists; areas from rooms and finishes zones; penetrations from the coordinated penetration schedule; `qty_source` names the query so a reviewer can reproduce it. Fittings and consumables may be added by ratio rules from `library/rules/bq-ratios.csv`:

`rule_id, applies_to (discipline, system, size range, location), consumable_code, description, spec, unit, ratio, ratio_basis (per m | per item | per m² | per penetration | % of parent), source (standard / manufacturer / company lesson), last_verified`

The categories the file must cover (values set by procurement from supplier data and the standards, kept current): pipe supports per metre by material and DN with anchors and rod per hanger; duct hangers per size, flexible connections per fan, fittings as a share of straight duct by system, access doors per damper and per kitchen-exhaust length, sealant per m²; insulation m² from the insulated OD or duct perimeter, vapour barrier and cladding for external runs; fire-stopping one tested system per penetration by service and element type; electrical terminations and glands per cable end, lugs, tray fittings, earth tails, labels, blanking plates; hydraulic fittings per metre, tundishes per relief point, inspection openings per bend and per length, bedding and marker tape for buried pipe; wet-fire fittings, hangers and seismic bracing per the standard's spacing, test and drain assemblies per zone; general sealants, fixings, coatings, lifting and rigging per heavy plant item, crane time, scaffold / EWP hours, commissioning hours per system, spares allowance per equipment class. Every ratio row carries `consumable_of` and the rule id, and the estimate's header states that these quantities are factored.

### Quantities in the PROCUREMENT version

Every installation consumable is an actual item generated from the run geometry and the installation detail, and the ratio file is not read:

- bends by angle and DN, one row per (angle, DN, material) from the route polylines (`db/services-routes.json`, `references/db-schema.md`); tees and reducers at each branch and size change;
- flanges / glands / joints per pipe length and jointing method, with the standard and PN / class;
- hangers and supports: type, spacing, the composition of one support (rod, channel, clamp, insert, isolation where required) and the substrate anchor by substrate (concrete, PT slab with no-drill zones respected, steel, block), one row per support type per run;
- insulation per run: material and thickness from the matrix, with the surface area and the cladding / vapour barrier as their own rows;
- fire-stopping: one tested system per penetration with its size, from the penetration schedule, named by the test report in `details/`;
- waste and spares as explicit quantities in `waste_qty` / `spares_qty` (waste from the cutting plan or the supplier's pack size, spares from the spares policy per equipment class), never as a percentage on the net quantity;
- testing and commissioning as their own rows in their own section (pressure tests, flushing, balancing, electrical tests, fire tests, witnessed commissioning per `templates/commissioning-tests.csv`).

The generator refuses a procurement row whose `qty_source` is a ratio rule, whose `actual_size` or `material_grade` is blank, or whose `sheet_revision` is not the revision the package freezes. Where the installation detail is not yet in the DB (supports not yet scheduled, penetrations not yet coordinated) the row is written with `net_qty` blank and `status = NOT CALCULATED` naming the missing input; it is never filled with a factor.

### The RFQ pack

One RFQ pack per procurement package, assembled by the generator at the same catalogue revision throughout, so a vendor never prices one revision against drawings of another:

| Item | Content | Source |
|---|---|---|
| BQ section | The package's rows of the current BQ version, headed ESTIMATE (from S5 / S6 drafts) or PROCUREMENT (from the mature package); vendor SKU, alternates and the `standard_certification` column visible; no VE dollar figures | `bq/…csv` |
| Specification chapter | The package's spec section with material, grade, standards, certification (dual certification for China-sourced categories), testing and commissioning requirements | The S6 specification, registered by package in the knowledge base |
| Drawings | Every sheet listed in the rows' `sheet_no` at the stated `sheet_revision`, plus the schedules and the P&ID / SLD / control schematic the package needs | `drawings/index.csv`, `drawings/level-sheet-matrix.csv` |
| Manufacturing-release conditions | What must be closed before the vendor may manufacture: the release sheet's open items for the package, vendor-confirmation fields still TBC, interfaces awaiting closure; before the release sheet closes the RFQ says so and offers at most a cancellable capacity reservation with its exit cost | `templates/release-sheet.md` |
| Vendor handover requirements | The asset ids the vendor's documents must cite, the O&M, spares, warranty-start basis and commissioning records due, in the fields of the asset register and handover matrix | `templates/asset-register.csv`, `templates/handover-matrix.csv` |

Supplier correspondence is in Chinese (SKILL.md language rule); the pack's technical documents — BQ, spec, drawings — are in English. An RFQ issued from an ESTIMATE BQ is a request for budget pricing and says so in its header; an order is placed only against a PROCUREMENT BQ and a closed release sheet.

### The generator

`gen_bq.py --version estimate --stage S6` or `gen_bq.py --version procurement --package <id>` reads the DB, the installation detail, `products/index.csv`, the VE register and the materials matrix (and, for the estimate only, `bq-ratios.csv`); writes the CSV and the HTML; refuses to run if any main item lacks a spec value, a SKU or an explicit `pending`; writes a difference report against the previous BQ of the same version (rows added / removed / changed, each with its reason — a design change with its change request, a VE item, a vendor confirmation, a write-back from manual detailing). The HTML opens with totals per package, then the rows grouped by package and section, consumables indented under their parent, with the difference report and the assumptions list at the end. Where an IfcOpenShell take-off exists (S10) or the drafting team's Revit take-off is supplied, the reconciliation against the DB quantities is attached and every difference is explained by element id; an unexplained difference is an issue.

## 2 The calc book

One per stage: `CALC-BOOK_<project>_<stage>_<date>.html`, generated by `gen_calcbook.py` from `calcs/`. It is the reviewer's entire calculation input and what the consultant reads before signing.

Structure:
1. Cover: project, stage, date, code editions and state variations, digest version and hash, script and tool versions (the S0 version lock); then the calc register as the index table (calc ID, title, discipline, standard, result, limit, verdict, blind re-calculation difference).
2. One section per calc ID, in register order:
   - title, discipline, purpose (one sentence: what decision this number feeds and which sheet / tag carries it);
   - inputs with sources (DB path and element id, digest record id, assumption id, product SKU, vendor `document_id` / `revision_id`);
   - method and formulae in plain text with units;
   - governing clause: standard · year · clause · digest record id (or `CLAUSE TO CONFIRM`);
   - the Python, collapsible (`<details>`), with its version hash and run date;
   - results with intermediate values; curves and charts as inline SVG (pump / fan curves with the duty point, load profiles, drift plots);
   - the check: result vs limit, margin, status PASS / FAIL / NOT CALCULATED / TBC / N/A;
   - assumptions used, each in the `ASSUMED — TBC` format;
   - blind re-calculation: the second model family's value, the difference, the arbitration note if any;
   - date, and the change log since the previous stage's book.
3. Appendix: the JSON export for the stage (`calcs.json`, machine-readable), the digest records cited (id, clause, verbatim text) and the script-check results.

Rules: every calc in the register appears; a calc without inputs, clause and status fails the generator; no number anywhere in the book without a source; the book is regenerated whole, never edited. Blind pass order: the second family works from the independent input package first (raw facts, brief, applicable standards — `references/review-and-gates.md`); the full book opens to it only after its independent answer is submitted and frozen. A consultant's signature is bound to an explicit catalogue revision of the book (`document_id` + `revision_id` + SHA-256); the signed original calculations are stored as immutable revisions linked to the book, and a later regeneration is a new revision that never inherits the signature (`templates/endorsement-record.json`).

## 3 Calculation coverage

Every gate report carries `calcs/coverage-<stage>.csv`, generated by `scripts/calc_coverage.py` from `templates/calc-templates/calc-master-list.csv` — the master list of the calculations each discipline owes, with the stage each is due. Every template row due at or before the stage must carry one status: `PASS`, `FAIL`, `NOT CALCULATED` (with the reason, the missing input, an owner and the expiry gate), `TBC`, or `N/A` (with the reason). A blank row is a defect and blocks the gate report; a row NOT CALCULATED past its expiry gate is a gate finding. The coverage file is the denominator the high-risk table is checked against — a calc that exists in the register but not in the master list is added to the list, not hidden. Details and the master-list schema: `references/calc-coverage.md`.

## 4 Decision records — first principles, TCO, simple annual return

Every design decision that changes cost, performance, risk or programme goes into `decisions.md` on `templates/decision-record.md`, and the gate report carries a "decisions this stage" section. A decision without a record cannot be frozen at a gate. The record holds, in the template's order: context; the assumptions people commonly make and which were stripped; the facts that are provably true, each with its source; the options A / B / C rebuilt from those facts with CAPEX, annual net OPEX, hold-period cash flows and TCO; the return against the baseline (ΔCAPEX, annual net saving, simple annual return, simple payback, NPV / IRR when needed); risks; the PD decision; the affected calcs, sheets, models and BQ lines.

Definitions, fixed so every record is comparable:
- Hold period from the brief; default 10 years. TCO = CAPEX + Σ annual net OPEX over the hold period − residual value, undiscounted by default; when discounting is used the record states the discount rate and the currency.
- CAPEX = supply + install + design allowance + certification. Annual net OPEX = energy + water + maintenance + consumables + the annual replacement provision (major components ÷ life) + staffing / operating effects, at the tariff and escalation in the brief.
- ΔCAPEX and annual net saving are against the baseline option A (normally the cheapest compliant option). Added maintenance and replacement cost of the option sits inside the net saving, not beside it.
- **Simple annual return = annual net operating saving ÷ incremental CAPEX.** The company threshold is ≥ 15 %, which is the same statement as simple payback = ΔCAPEX ÷ annual net saving ≤ 6.67 years.
- The threshold is not an IRR and is never called one. Handbook illustration: 100,000 extra CAPEX, 15,000 per year net saving for ten years, no residual → simple annual return 15 %, payback 6.67 years, IRR ≈ 8.14 %. When the PD asks for NPV / IRR they are computed from the full cash flows and stated beside the simple return, with the rate and currency.
- Below the threshold the PD may record a non-financial reason — compliance, operations, brand, programme — and the record says so. A technical FAIL is never waived by a financial argument; a FAIL option cannot be adopted whatever its return. Options that reduce CAPEX and keep performance are adopted unless they fail compliance or a stated brand standard.

The reviewer recomputes every record's arithmetic (`references/review-hub.md`).

Worked example (numbers illustrative): D-014 guest-room hot water — A: central gas-fired storage, CAPEX 380 k, net OPEX 96 k / yr; B: central heat-pump plant with storage, CAPEX 520 k, net OPEX 58 k / yr including its added maintenance and replacement provision. ΔCAPEX = 140 k; annual net saving = 38 k; simple annual return = 38 / 140 = 27 %; payback = 3.7 yr; TCO over 10 years: A = 380 + 960 = 1,340 k; B = 520 + 580 = 1,100 k. B adopted, rule met. Had the saving been 18 k / yr, the simple return would be 13 % < 15 %: not adopted unless the PD records a reason (for example the gas connection cost or the Section J route).

First-principles discipline in practice: the "assumptions stripped" table is the point. Typical inherited assumptions that fail when stripped: that a hotel corridor needs a 600 mm ceiling void (the 6 m corridor module showed it does not); that a 20 m² room needs an FCU (a ventilation-only room with a VRF cassette can meet the same comfort at lower TCO — checked by calc, not by habit); that every plant room must be a room (roof-mounted packaged plant with a screen); that supports are "by the contractor" (they are a real cost line and go into the BQ as itemised supports in the procurement version). The record shows what changed when the inherited thinking was removed.
