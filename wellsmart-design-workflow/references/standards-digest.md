# Standards digest — how the AS/NZS, NCC and NZBC rules become one file the skill reads instead of remembering

The problem: the model "knows" most Australian design rules, but knowing is not the same as reading, and a wrong number that looks right is the most expensive kind of error. The fix is a digest: every design-driving rule extracted once from the source text into structured data, with the clause reference attached, so a script can look a rule up in milliseconds and the model never has to guess. The full PDFs stay in the knowledge base for the cases the digest does not cover; the digest is the fast path.

Ownership: the digest lives in the company library at `wellsmart-design-library/standards/` (not in this skill). This file says how to build it, what goes in it and how to use it.

## Three levels, three sizes

| Level | File | Size | Who reads it | Purpose |
|---|---|---|---|---|
| 1 Index | `standards/index/<discipline>.md` — one per discipline (hyd, mech, elec, fire, str, arch, access, acoustic, traffic, energy) | 2–6 k tokens each | The model, at the start of any discipline task | The 40–120 rules that drive that discipline's design, one line each, with value, unit, condition and citation. This is what replaces memory. |
| 2 Digest | `standards/digest/<standard>-<year>.json` — one per standard | 5–50 k tokens each | `digest_query.py`, never the model directly | Every quantitative requirement, table and formula in the standard, machine-readable, with clause, page and the verbatim sentence it came from. |
| 3 Source | Knowledge base (Dify / Claude Project): the PDFs | full | Retrieval, when a clause is not in the digest or the wording matters | The authority. The digest is derived from it and cites into it. |

Rule of use: the model reads the level-1 index for its discipline at the start of the task; a script queries level 2 for every number that goes into a calc; level 3 is opened only when the query returns nothing, when a performance solution argument needs the exact wording, or when the reviewer challenges a citation. A number that appears in a calc must carry the digest record ID (`AS3500.2-2021/T6.1/r12`) or, failing that, `CLAUSE TO CONFIRM`.

## Digest record schema (level 2)

One JSON file per standard edition. Every record is one requirement.

```json
{
  "standard": "AS/NZS 3500.2", "year": 2021, "amendment": "A1 2022", "title": "Plumbing and drainage – Sanitary plumbing and drainage",
  "jurisdiction": ["AU", "NZ"], "referenced_by": ["NCC 2022 Vol 1 B1D3", "NCC 2022 Vol 3"],
  "records": [
    {
      "id": "AS3500.2-2021/4.5.2/r1",
      "clause": "4.5.2", "table": null, "figure": null, "page": 61,
      "topic": "drain gradient", "discipline": "hyd", "system": "SAN",
      "applies_when": "DN100 sanitary drain",
      "requirement": "minimum gradient",
      "value": 1.65, "unit": "%", "comparator": ">=",
      "alt_values": [{"applies_when": "DN150", "value": 1.0, "unit": "%"}],
      "formula": null,
      "text": "<verbatim sentence from the standard>",
      "notes": "state variation: none known",
      "design_critical": true,
      "extracted": "2026-09-14", "extracted_by": "model-family-A", "checked_by": "model-family-B", "check_status": "agree",
      "verification": "page-verified", "verified_by": "<person>", "verified_on": "2026-09-15"
    }
  ],
  "digest_version": "<edition>-<build date>", "digest_sha256": "<hash of this file as released>",
  "released_after_tests": true
}
```

Field rules: `value` is numeric or null; text-only requirements (e.g. "shall be provided") get `value: null` and the requirement in `requirement`; tables become one record per row with `table` set and `applies_when` carrying the row condition; formulas go in `formula` as Python-evaluable text with named variables and a `variables` map; `text` is always verbatim, because it is what the reviewer and the consultant check against. Two model families extract independently and a script diffs them — a record is `check_status: agree` only when both produced the same value, unit and clause. **Agreement is recorded as agreement, not as truth**: two extractions can share the same missed footnote, so `verification` says what was actually done — `page-verified` (a person read the source page), `sampled` (verified as part of the risk sample), or `agreement-only` (nobody has read the page). A `design_critical` record may not be released as `agreement-only`.

Level-1 index line format (Markdown, one rule per line):

```
- SAN drain min gradient: DN100 ≥ 1.65 %, DN150 ≥ 1.0 % — AS/NZS 3500.2:2021 cl 4.5.2 [AS3500.2-2021/4.5.2/r1]
```

## The extraction pipeline

1. **PDF → text.** `pdftotext -layout` for text PDFs; OCR (ocrmypdf) for scanned ones. Keep page numbers. Store as `standards/text/<standard>-<year>.txt`. Tables: use `pdfplumber` / `camelot` to pull tables into CSV beside the text; tables are where most design values live and free-text extraction mangles them.
2. **Chunk by clause.** Split on clause headings (regex on `^\d+(\.\d+)*\s`), keep the clause number, title and page with each chunk. Chunks of 300–1,500 tokens.
3. **Extract with model family A.** Per chunk, prompt: "From this clause of <standard> extract every quantitative or mandatory requirement as records in the schema. Verbatim `text`. Do not paraphrase numbers. If a table is referenced, extract each row. If nothing quantitative, return []." Temperature 0. Output JSON.
4. **Extract with model family B**, same prompt, independently.
5. **Diff.** Script matches records by clause + topic + applies_when; agreement on value/unit/comparator → `agree`; otherwise `disagree` with both values shown. Every disagreement goes back to the source page. The handbook's expectation is that disagreements are a few per cent of records (3–8 %); the actual extraction difference rate is recorded per run, not assumed.
6. **Verify on the source page.** Every disagreement, and 100 % of the design-critical records — the clauses that change a design value, size, count or pass / fail, their applicability conditions, the table notes and the exceptions — are verified by a person reading the source page, whatever the two extractions agreed on; the record gets `verification: page-verified` and `verified_by`. The remaining records are risk-sampled (higher sampling where the discipline's values drive procurement or safety), with the sample size and coverage recorded in the digest's release note. Two-family agreement alone never closes a design-critical record.
7. **Build the index** (`build_index.py`): pick records tagged `design_critical: true` (set during extraction by a second prompt: "Which of these records would change a design value, a size, a count or a pass/fail?") and render the discipline index files.
8. **Test, then release**: every record has clause + page + verbatim text; every index line resolves to a record; no record without a standard/year; no design-critical record without page verification; run the known-case tests in `standards/tests/` (known answers, e.g. "DN100 gradient → 1.65 %") and the boundary-value tests (the record's `applies_when` boundary on both sides: DN100 vs DN150, ≤ 25 m vs > 25 m, the edge of a climate zone). A digest version is released only after both test sets pass; the release writes `digest_version`, `digest_sha256` and the release note (difference rate, records verified, sample coverage, tokens, person-hours).
9. **Upgrade by edition**: digest files are tagged with the standard edition and amendment; when a new edition or amendment arrives, extract it as a new file and run `diff_editions.py` to list every changed value with its old and new record ids, then map that list onto the calcs that cite the old records (`calcs.json` `digest_record_id`) — the "affected calcs" list. A new digest version never replaces the one a running project has locked; the project migrates only through the version-lock procedure below.

Cost: the handbook's planning expectation is that a 200-page standard is roughly 150 k tokens of text, two extractions plus checks about 1–1.5 M tokens per standard, and the whole set the company uses (≈ 60 standards + NCC volumes) a few days of machine time and one person-week of checking. These are expectations until measured: the extraction difference rate, the tokens and the person-hours are recorded from the actual runs in each digest's release note, and the expectation is corrected from them. Do it once; maintain by edition.

## Query script (level 2)

`standards/digest_query.py`:

```
digest_query.py --std "AS/NZS 3500.2" --topic "drain gradient" --when "DN100"
digest_query.py --id AS3500.2-2021/4.5.2/r1
digest_query.py --discipline hyd --system SAN --topic vent
```

Returns the matching records (value, unit, comparator, applies_when, clause, page, text, id). Calc scripts import `digest.get(id)` and refuse to run with a hard-coded code value that has no record ID: `limit = digest.get("AS3500.1-2021/3.3.4/r2").value`.

## What to extract, by discipline — the design-driver checklist

This is the list of things the digest must carry so that no design value is ever recalled from memory. It names topics, not values; the values come from the source text and the digest, and where a figure is quoted here it is an expectation for the extractor to confirm, never a citation. Editions: use the edition the NCC edition in the brief calls up (NCC 2022 Schedule 2 referenced documents; NCC 2025 where adopted) — extract both editions when they differ.

### Hydraulic — water (AS/NZS 3500.1, AS/NZS 3500.4, AS 3500.5 where domestic; AS/NZS 2845 backflow; AS 4032 TMV; NCC B1/F/J8)
Fixture-unit ratings per fixture and the probable simultaneous demand tables and curves; pipe sizing method and the friction/velocity limits (expect a maximum velocity in the 3 m/s region for copper); maximum static pressure at any outlet (expect 500 kPa) and the PRV / zone rule that follows; minimum pressure and flow at fixtures; backflow prevention hazard ratings (high / medium / low) by connection type and the device required for each; isolation valve locations; pipe materials and jointing by service; cover and depth for buried pipes and separation from other services; water hammer control; insulation (freeze and NCC J8 heated water); metering; cross-connection control; tanks (break tanks, storage, air gaps); heated water: storage temperature (Legionella control, expect ≥ 60 °C storage) and delivery temperature at personal-hygiene fixtures (expect ≤ 50 °C; ≤ 45 °C in aged care, childcare, schools and similar); TMV vs tempering valve rules; HW return circulation and dead-leg limits; expansion, relief and drain provisions; solar / heat-pump requirements.

### Hydraulic — sanitary plumbing and drainage (AS/NZS 3500.2; NCC F1 floor wastes; NCC Vol 3)
Fixture-unit ratings; discharge pipe and stack sizing tables (by fixture units and number of storeys); branch sizing and graded discharge pipe lengths; **drain gradients by DN** (expect DN100 in the 1.65 % region and DN150 in the 1 % region — confirm); stack offsets and the rules for connecting near offsets; venting: stack vents, relief vents, group vents, branch vents, cross vents, sizes and the maximum unvented lengths; trap seal depths by fixture type and the loss limits; **floor waste gullies**: where required (NCC F1 for bathrooms and laundries above another SOU or public space — clause to confirm), charging (a charging fixture discharging through the FWG, or a trap primer) so the seal does not evaporate, riser heights; **overflow relief gully**: level relative to the lowest fixture and to finished surface (expect ≥ 150 mm below the lowest fixture outlet and ≥ 75 mm above the surrounding paved surface — confirm), grate type, location outside the building; inspection openings: spacing, at changes of direction, at the boundary; boundary traps where the network operator requires; jump-ups and drop connections; pumped systems: dual pumps, storage volume, vent, non-return and isolation; grease arrestors and trade waste (sizing by fixtures / covers per the water authority); pipe materials, supports and spacing (from the manufacturer and the standard), expansion joints on PVC stacks, fire-collar requirements at penetrations (NCC C4 / AS 4072.1); testing.

### Hydraulic — stormwater (AS/NZS 3500.3; AS 2200; council OSD policy)
Design rainfall intensities and the AEP the standard assigns to eaves gutters, box gutters and their overflows (box gutters carry the rarer event and always need an overflow device); gutter and downpipe sizing tables by catchment; roof drainage layouts, sumps and rainheads; overflow provisions; subsoil drainage; surface drainage and grated drains; pipe gradients and self-cleansing velocity; on-site detention (council DCP: permissible site discharge, storage volume, orifice); rainwater tanks (NCC / BASIX / council); pumped stormwater in basements (dual pumps, storage, flood-gate interfaces).

### Hydraulic — gas (AS/NZS 5601.1)
Appliance loads and diversity; pipe sizing tables by material, length and pressure drop; meter positions and clearances; ventilation of rooms with appliances; flueing; isolation and purge points; pipe-in-shaft and pipe-in-duct rules; separation from electrical services.

### Mechanical (AS 1668.2, AS 1668.1, AS/NZS 3666.1, AS 4254.1/.2, AS 1682.1/.2, AS/NZS 1677 refrigeration, AS/NZS 5149, NCC F6 / J6; AS/NZS 2107 for noise)
Outdoor-air rates per occupancy type and per person / per m² (tables), the effective-ventilation allowances for filtration and CO₂ control; exhaust rates for sanitary compartments, kitchens (hood types and face velocities, grease-duct construction and access), car parks (the formula by usage and the CO-controlled variant), laundries, bin rooms, plant rooms; natural ventilation openable-area rules (NCC F6); make-up air; duct construction pressure classes, leakage classes and testing; fire dampers and smoke dampers: where required, ratings, access; smoke control (AS 1668.1): stair pressurisation pressure and door-force limits, relief, zone smoke control, smoke exhaust rates and make-up, fire-mode operation; cooling-tower and warm-water Legionella controls (AS/NZS 3666); refrigerant charge limits per occupied space (AS/NZS 5149 / ISO 5149) — this drives VRF / split selection in guest rooms; NCC J6 duct and pipe insulation R-values by service and location, fan and pump power limits, economy cycle thresholds; internal design sound levels by room use (AS/NZS 2107) and the plant-noise-to-boundary method the council applies.

### Electrical (AS/NZS 3000, AS/NZS 3008.1.1, AS/NZS 61439, AS/NZS 3010, AS/NZS 2293.1, AS/NZS 1680 series, AS/NZS 1768, AS/NZS 3013, AS/NZS 3080, AS 2201, NCC E4 / J7 / J9; distributor service rules)
Maximum-demand method and the per-installation-type tables; cable current ratings by installation method and derating (grouping, ambient, thermal insulation) and the voltage-drop limit (expect 5 % overall from the point of supply, split sensibly between sub-mains and final subcircuits); short-circuit temperature limits and the minimum cable size for the fault level; earthing system, MEN, main earth sizes, equipotential bonding of wet areas; RCD requirements by circuit type and rating; switchboard form of separation, IP rating, clearances and access; discrimination / selectivity between protective devices; sub-metering (NCC J9 energy monitoring thresholds by floor area; embedded-network rules); EV charging provision (NCC J9: proportion of car spaces with distribution board capacity and infrastructure) and the AS/NZS 3000 EV clause; emergency lighting and exit signs (AS/NZS 2293.1: where required, illuminance along the path, spacing, testing regime, NCC E4); illuminance and glare by task (AS/NZS 1680: corridors, guest rooms, offices, kitchens, car parks, external) and NCC J7 lighting power density limits per space type; lightning protection risk assessment (AS/NZS 1768) and the component classes; fire-rated cable classifications (AS/NZS 3013 WS ratings) for the services that must survive fire (pumps, smoke fans, EWIS, lifts) and the NCC clauses that call them up; structured cabling and communications room rules (AS/NZS 3080, AS/CA S009, NBN / carrier requirements); security (AS 2201) and CCTV; lift electrical interfaces (AS 1735).

### Fire — wet (AS 2118.1 / 2118.4 / 2118.6, AS 2419.1, AS 2441, AS 2941, AS 2304 tanks, AS 1851 for maintainability, NCC E1 and Specifications; FPAA101D/H where used)
Where sprinklers, hydrants and hose reels are required (NCC E1 by class, effective height, floor area, rise in storeys); sprinkler hazard classification by occupancy; design density and area of operation per hazard class; head spacing and coverage per head, distance from walls, clearance to storage, obstruction rules, deflector distances, concealed-space rules; residential sprinkler alternatives for Class 2/3 (AS 2118.4 / 2118.6 / FPAA101D-H) and their height limits; water supply grade, duration and the tank / mains combinations; pump duties, pumpset construction (AS 2941), pump-room requirements; alarm valves, flow switches, monitoring and brigade interfaces; hydrant coverage (hose length and the "every part of the floor" rule), number of hydrants in simultaneous operation by building size, flow per hydrant and the residual pressure at the most disadvantaged outlet, booster assembly, block plans, pipe sizing and velocity limits, fire-brigade vehicle access; hose reels: coverage, flow and pressure at the nozzle, positions near exits; tanks: capacity, refill rate, materials (AS 2304); the local-only procurement rule for pumpsets and valves (company rule, not a standard).

### Fire — dry (AS 1670.1, AS 1670.4, AS 4428 series, AS 1668.1 interfaces, AS 3786 residential alarms, AS 7240 series, NCC E2 / Specification for smoke detection and EWIS; AS 2220 for hydrants signage; AS 2293 as above)
Where detection, EWIS and occupant warning are required (NCC E2 by class and height); detector types by space, spacing and ceiling-height factors, positions relative to walls, beams and air inlets; sampling / aspirating alternatives; FIP location, fire control room requirements for tall buildings, brigade panel and mimic; EWIS: zoning, speaker sound levels above ambient and intelligibility, WIP phones, evacuation sequence; interfaces and cause-and-effect: lifts, smoke control, doors, access control, gas, BMS, hold-open devices; cable classifications; residential smoke alarms in SOUs (AS 3786) and interconnection.

### Fire — NCC deemed-to-satisfy fabric (NCC Vol 1 Sections C, D, E, G, Specifications; AS 1530 series; AS 4072.1; AS 1905.1 fire doors; AS 5113 façade fire)
Type of construction by class and rise in storeys; FRLs by element and type (Specification 5 tables); compartment size limits; fire-source features and the separation distances; openings in fire-rated construction and their protection; service penetrations and the tested-system rule; fire-isolated stairs: where required, construction, pressurisation trigger height, discharge; egress: number of exits, travel distances (to a point of choice and to an exit), exit widths per occupant count, door swing and hardware, stair dimensions (risers, goings, handrails, balustrades); occupant load factors per use; lift requirements for fire (E3, stretcher lifts, fire-service controls); external wall combustibility and the tested façade systems (AS 5113, non-combustible for Type A / B); bushfire (AS 3959) where mapped.

### Structural (AS/NZS 1170.0/.1/.2/.3, AS 1170.4, AS 3600, AS 4100, AS/NZS 4600, AS 3700, AS 1720.1, AS 2159, AS 4678, AS 3735, AS 2870, AS 4055, AS 1684, AS 3610, AS/NZS 4671, AS 5216, AS/NZS 1554, AS 1657; NZ: NZS 1170.5, NZS 3101, NZS 3404)
Load combinations and importance levels; imposed loads by occupancy (hotel rooms, corridors, stairs, plant rooms, car parks, roofs, balustrade loads) and the reduction rules; wind: regions, terrain categories, shielding, topography, pressure coefficients for walls, roofs and internal pressure, and the serviceability wind; earthquake: hazard factor by location, site subsoil class, importance level, ductility and performance factors, the height and irregularity limits of each analysis method, drift limits, parts and components (this is what drives the plant-room anchorage schedule); concrete: strength grades and minimum grades by exposure, cover by exposure class and fire, crack-control and deflection limits (span/250 and the incremental limits), punching shear, minimum reinforcement, lap and anchorage lengths, slab-on-ground rules (AS 2870 for residential, AS 3600 otherwise); steel: section classification, member capacities, connection design, bolt categories and tightening, weld categories (AS/NZS 1554), corrosion protection categories (AS/NZS 2312) and fire protection of steel; masonry: wall types, robustness limits, lintels, control joints, ties; timber: grades, span tables (AS 1684), durability classes; piling: design methods, testing, tolerances; retaining walls and basement walls (AS 4678, water pressure, drainage); liquid-retaining structures for tanks (AS 3735); anchors (AS 5216) — post-installed anchors for services supports on towers are a frequent miss; formwork and temporary works (AS 3610, AS 3850 precast); walkways, ladders and platforms for plant access (AS 1657); robustness and progressive-collapse provisions; vibration limits for floors with gyms and plant.

### Architecture, amenity and energy (NCC Vol 1 Sections F, G, J; AS 1428.1 (access, also below); AS 3740 wet areas; AS 4654 waterproofing; AS 2047 / AS 1288 / AS 4284 façade; AS 3959; AS 1926 pools; AS 4586 slip; AS 1735 lifts; AS/NZS 4859 insulation)
Sanitary facility counts per class and occupancy (F4 tables — hotels count by guests and staff), accessible facility counts (D4 / F4), room heights, natural light and ventilation percentages, condensation management (F8: vapour permeance classes by climate zone, exhaust to outside), sound transmission and insulation between SOUs and from plant / lifts / corridors (F7: Rw + Ctr and Ln,w limits, the "with door" cases and the discontinuous-construction requirement for wet-area walls); wet-area waterproofing extents and falls (AS 3740 / AS 4654, NCC F1); slip resistance classifications by location (AS 4586, NCC D3 / F); stair and balustrade geometry (D3); glazing: human-impact, wind and safety glass (AS 1288), window performance grades and water-penetration resistance (AS 2047), façade testing (AS 4284); lifts: numbers, stretcher lift, accessible lift, fire service (E3, AS 1735 series); swimming pools and spas (AS 1926, G1); energy (J1–J9): the JV3 / elemental routes, fabric R-values and glazing limits by climate zone, building sealing, J6 HVAC (fan, pump, duct and pipe insulation, economiser), J7 lighting (power density and controls), J8 heated water and pool plant, J9 monitoring and EV; NZ H1 and its verification methods for New Zealand work.

### Access / DDA (AS 1428.1 edition called up by the NCC edition in the brief, AS 1428.2, AS 1428.4.1, AS 1428.5, AS 2890.6, AS 1735.12, NCC D4 and Premises Standards)
Number and distribution of accessible SOUs by class and room count (Class 3 hotel tables), accessible car spaces and their headroom and shared areas (AS 2890.6), continuous accessible path: widths, passing and turning spaces, door clear openings (expect 850 mm), latch-side and hinge-side clearances by approach, door forces and handle heights, thresholds; ramps: gradients and landing intervals, step ramps and kerb ramps; stairs: nosings, contrast strips, handrail extensions; accessible sanitary compartments: minimum dimensions, pan and basin setout, grab-rail geometry, door swing; showers; TGSIs (AS 1428.4.1) at stairs, ramps and hazards; luminance contrast minimums; signage and braille; hearing augmentation; accessible lifts (AS 1735.12); accessible adult change facilities where required; the PS route (Access Consultant sign-off).

### Acoustics (AS/NZS 2107, NCC F7, AS ISO 717.1/.2, AS 1191, AS/NZS 3671, AS 2021 aircraft, state road / rail noise policies)
Internal design sound levels by room and time (hotel guest rooms and suites, lounges, restaurants, offices, back of house); external noise intrusion methods and façade Rw + Ctr targets by external level; inter-tenancy and inter-room requirements (F7); plant noise limits at receivers (council DCP / EPA: background + margin, day / night); vibration isolation for plant and gyms; reverberation targets for public rooms; testing and verification methods.

### Traffic and parking (AS/NZS 2890.1, AS 2890.2, AS 2890.3, AS 2890.5, AS 2890.6; Austroads design vehicles and swept paths; council DCP rates)
Bay dimensions by user class, aisle widths by angle, headroom (general and accessible), column setbacks, ramp gradients and transition lengths, blind aisles, sight distance at the exit; commercial vehicles: design vehicle (SRV / MRV / HRV) by land use, dock dimensions and headroom, grades, turning templates, waste-vehicle access; bicycle parking rates, rack dimensions and end-of-trip facilities; parking rates and loading requirements from the council DCP; the requirement for a traffic report / CTMP at DA.

### Façade (AS 1288, AS 2047, AS 4284, AS/NZS 1170.2, AS 4055, AS 5113, AS 1530.1/.3, AS 3959, NCC C2D10 and F8; AS 1397 and AS/NZS 2728 for coated steel; AS 1418.13 for BMU loads)
Design wind pressures by zone and the serviceability / ULS ratios for testing; glazing thickness and type by pressure and human-impact location; water-penetration resistance test pressures and air-infiltration limits; combustibility of external walls, attachments and sarking; condensation risk and vapour control by climate zone; thermal breaks and Section J glazing limits; BMU / façade-access loads (AS 1418.13); cladding fixings and anchor design (AS 5216); tolerances and movement joints; the test sequence (AS 4284) and its timing in the programme.

### New Zealand differences (NZBC clauses B1, B2, C1–C6, D1, E1–E3, F, G, H1; NZS 4121 access; NZS 4404 land development; NZS 1170.5)
Where the NZ document replaces the Australian one: E1 surface water, E2 external moisture (the E2/AS1 risk matrix), E3 internal moisture, G4 ventilation, G7 natural light, H1 energy, C/AS2 fire, D1 access routes and NZS 4121; NZS 3604 timber-framed buildings; the CPEng PS1 route for structure.

## Project version lock

At S0 the brief records, and G0 freezes, every version the project's numbers depend on: the standard editions and amendments, the state variations (NCC state appendices, council and network-operator overrides), the digest version and `digest_sha256` per standard, the library module versions, the product-data dates (the `last_verified` of every SKU the project selects), and the calculation script / tool versions (check scripts, generators, IfcOpenShell, EnergyPlus, OpenSeesPy). `db/project.json` `version_lock{}` holds the same list (`references/db-schema.md`), and every calc register row and calc-book cover cites it.

The project uses these fixed versions for its whole life. A library or digest update never overwrites a running project: the update produces an impact list — which locked items changed, which records changed value, which calcs, sheets, selections and BQ lines cite them — and the project migrates only after the gate that governs those items approves the migration, rerunning only the affected content and recording the new lock in the gate report. A project may also decline to migrate and finish on its locked versions; the impact list is then filed with the gate report as a known difference. Full procedure and the same rule for modules and products: `references/library-and-repos.md`.

## Using the digest in a stage

- At S0 the regulatory basis lists the standards and editions the project will use; `digest_query.py --std … --year …` confirms each has a released digest at the edition the NCC / NZBC edition in the brief calls up; missing ones go on the extraction list before S1, and the digest versions and hashes go into the version lock.
- At S1–S3 the model reads the level-1 indices for the disciplines in play (arch, fire, str, mech, elec, hyd at S1; all at S3).
- At S6 every calc script fetches its limits from the digest by record ID; the calc register row carries the ID; `check_citations.py` fails a calc whose limit has no record ID.
- At S8 the reviewer re-derives a 10 % sample of the digest values used, from the source PDF pages, and any mismatch is a blocker on the digest, not only on the calc. The reviewer's sample is drawn across `agreement-only` and `sampled` records first; a mismatch there raises the verification level of that whole clause family.
- When a state variation, a council policy or a network-operator rule overrides a standard, it is added to the digest as its own record with `jurisdiction` set and `overrides` pointing at the record it replaces; the project's version lock names the state variations in force.
- When a calc script fetches a record whose `verification` is `agreement-only` and the record is design-critical for that calc, the calc's status is TBC until the record is page-verified; the calc register row says so.

## What the digest is not

Not a substitute for the source when wording matters (performance solutions, disputes with a certifier); not a place for the company's own rules (those go in `library/rules/`, cited as company rules); not a place for values the extractor "remembered" — a record without verbatim `text` and a page number fails validation and is deleted; not proof of correctness because two models agreed — agreement is a statistic about the extraction, and only the source page verifies a record.
