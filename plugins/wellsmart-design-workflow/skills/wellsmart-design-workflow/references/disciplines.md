# Discipline design content and calculation checklists

What each discipline must produce at S3 (schematic) and S6 (detailed), which calculations are mandatory, and the governing standards to cite (always with year and clause from the knowledge base — never from memory). Every calculation gets a calc ID `<DISC>-<NNN>` and a row in the calc register.

Discipline codes: A architecture, I interiors, S structure, M mechanical, E electrical, H hydraulic, F fire, V vertical transport, C civil, X ESD/thermal, Q façade, N acoustics.

---

## Architecture (A)

S1/S3: massing, area schedule, floor-to-floor, core, egress, ceiling-zone section, GA set.
Mandatory calcs: occupant numbers per area; egress widths and travel distances per NCC Part D; sanitary fixture counts (NCC Part F4 tables, by occupants); accessible SOU counts (NCC Part D4 tables for Class 3); car and bicycle parking counts per planning controls; GFA / FSR.
S6 extras: door and window schedules, wall-type schedule with FRL and Rw, waterproofing extents, finishes fire-hazard properties, glazing compliance (AS 1288, AS 2047), slip resistance (AS 4586 classes by location), SiD register entries.

## Interiors (I)

S2: room modules, public areas, FF&E shortlist, style board if none given.
Mandatory checks: DDA per AS 1428.1 (circulation, turning spaces, door clear widths, accessible bathroom layouts, reach ranges); finishes group numbers and CRF per NCC Spec 7; acoustic targets between SOUs (NCC Part F7); illuminance targets (AS/NZS 1680 series); wet-area waterproofing per AS 3740 / NCC F1.
S6: joinery elevations 1:20 and sections 1:5, RCP coordinated with ELEC and MECH, finishes schedule, FF&E schedule with item numbers and supplier data.

## Structure (S)

S1: system and grid, spans, transfers, lateral system, DfMA constraints.
S3: framing plans, preliminary member sizes (span/depth rules and hand calcs), load tables, foundation scheme.
S6 — the structural workflow in six steps (software path in `references/toolchain.md`); the 3D model is the analysis model, and the physical model comes from the same DB:
1. Loads: dead, live (AS/NZS 1170.1), wind (AS/NZS 1170.2 — region, terrain, Cpe/Cpi), earthquake (AS 1170.4 or NZS 1170.5), snow where relevant (AS/NZS 1170.3), construction and temporary loads. Regional cases are site-pack fields, not afterthoughts: the Whitsundays are a cyclonic wind region, Queenstown is seismic, Niseko carries snow load. Load tables go into the calc register.
2. Analysis model: scripts generate the OpenSeesPy 3D model from the DB (columns, beams, slab shells, walls, core, foundation springs), run the combinations per AS/NZS 1170.0 and output forces, displacements, periods and drifts. PyNite is enough for small projects. Model checks: equilibrium (sum of reactions = applied loads), no unconstrained nodes, mesh convergence for shells, stiffness modifiers stated.
3. Member design: concrete to AS 3600 (NZ: NZS 3101), steel to AS 4100 (NZS 3404), timber to AS 1720 (NZS 3603), cold-formed steel to AS/NZS 4600, masonry to AS 3700; sections with sectionproperties / concreteproperties; outputs member schedules (B1, C1, F1…), reinforcement ratios, deflection (short and long term), crack control, vibration, slenderness, connections.
4. Foundations: from geotech parameters (people commission the report) — piles (AS 2159), rafts, pad footings; uplift on cyclonic sites is a pass/fail embedment question.
5. Coordination: the penetration schedule (position, size and trimming of every services penetration through beams, slabs and walls), no-drill zones in PT slabs, beam depth vs duct routes. This is the main source of clashes between structural 3D and MEP 3D, so it is settled in the DB (`db/crossings.json`, `references/db-schema.md`) before S7.
6. Outputs: GA, member schedules, typical connections, the calc package, the physical IFC model (IfcBeam / IfcColumn / IfcSlab / IfcWall with profiles and materials), the ETABS `.e2k` text model plus a one-page modelling assumptions sheet (stiffness modifiers, diaphragm assumption, mass source, load combinations). Reinforcement LOD 400 is the drafting team's / detailer's work at S10.

OpenSees answers; ETABS compares. OpenSees produces the results the design uses. The `.e2k` and the assumptions sheet go into the S9 package so the signing engineer opens the complete model without rebuilding it, runs it and compares: on the same model the two solvers are expected to differ by about 1–3 % (modelling choices — cracked-stiffness modifiers, diaphragm rigidity, the P-Δ method, wall / slab shell mesh, mass source, spectrum combination — not the solver); reactions, periods, inter-storey drifts and key member forces within 5 % count as agreement. The first project verifies once that the `.e2k` opens in ETABS on a machine that has it; afterwards it is routine. Towers use the same process, nothing separate; wind tunnel, geotech and temporary works are physical or contractor work.

Verification of the verification: closed-form benchmarks (simply supported beam, cantilever, single column) against the scripts; the second solver on the same model as above; unit tests of every code-check function against worked examples from the standard's commentary or a design handbook; blind re-implementation of critical clauses by a second model family. The dual-solver boundary: OpenSees–ETABS agreement on a model generated from the same DB proves solver consistency only; the blind pass separately checks the raw geometry, loads, boundary conditions, units and modelling basis from the fact inputs, because two consistent models can share the same wrong input.

## Mechanical (M)

S1: MEP space table (plant rooms, risers, intake / exhaust positions and separations).
S3: one schematic per air and water system; loads from the thermal model.
S6 mandatory: duct sizing and routing (equal-friction method, AS 4254 construction classes), pipe sizing (CHW / HHW / condenser water; velocity and friction limits stated), insulation thickness (NCC 2022 Section J Part J6 for ducts and pipework, J8 for heated-water pipework / NZ H1), ventilation rates (AS 1668.2 — outdoor air per person, exhaust for toilets, kitchens, car parks; intake-to-discharge separation per Table 3.4), stair pressurisation and smoke control (AS 1668.1), kitchen exhaust hoods and grease, refrigerant safety for VRF in small rooms (AS/NZS 5149 charge limits per room volume), noise (NR targets per AS/NZS 2107; plant noise to boundaries), controls: control descriptions, BMS points list, fire-mode matrix, functional descriptions for every AHU, FCU, fan and pump.
Company rules on file: guest-room OA 20 L/s sold / 7 L/s unsold, ensuite exhaust 18 L/s continuous, NR38 in rooms (Pitt Street) — check the library for the current values before reusing.

## Electrical (E)

S1: substation, MSB, generator, UPS and comms-room space; DNSP connection route.
S3: single-line diagram, load estimate, supply application data.
S6 mandatory: maximum demand (AS/NZS 3000 Appendix C or measured data), transformer / generator / UPS sizing with an essential-loads table, SLD, DB schedules with circuit references, cable sizing (AS/NZS 3008.1.1 — current rating, voltage drop within the project limits e.g. 0.5 % / 2.0 % / 2.5 %, short-circuit withstand), protection discrimination from device curves, fault levels (IEC 60909 method; state source impedance assumptions), earthing (AS/NZS 3000 Section 5), cable-tray sizing (fill ratio) and segregation (power / comms / fire-rated), fire-rated cabling classifications (AS/NZS 3013) for fire pumps, lifts, EWIS, stair pressurisation, lighting (lux per AS/NZS 1680, W/m² per Section J, emergency and exit lighting per AS/NZS 2293), lightning protection risk assessment (AS/NZS 1768), EV-charging provision (NCC 2022 Part J9), metering and embedded-network strategy, comms / security / GRMS / BMS interface tables.

## Hydraulic (H)

S3: one schematic each for cold water, hot water, drainage, stormwater, gas, fire water, to the HY-0040 depth (`drawing-standards.md`).
S6 mandatory: water demand and pipe sizing (AS/NZS 3500.1 loading units, velocity limits), pressure zoning (outlet window typically 250–500 kPa → about 25 m per gravity zone), PRV settings, storage and boosting (state hours of storage; break tanks), hot water (AS/NZS 3500.4 — storage and recovery per key, return balancing with dynamic valves on tall risers, temperature regime: storage ≥60 °C, tempering, TMVs; Legionella management per AS/NZS 3666), sanitary drainage and venting (AS/NZS 3500.2 fixture units, stack sizing, fully vented vs single stack), stormwater (AS/NZS 3500.3, IFD rainfall from BoM, overflow, OSD per council), trade waste (grease arrestor sized by covers to the water authority's method), gas (AS/NZS 5601), backflow prevention (AS/NZS 2845), and the pump logic for every pumped system (next section).

## Pump logic — five deliverables per pumped system

Applies to every pumped system in the building, whichever discipline owns it: domestic water transfer / boosting, hot-water return, chilled / heating water primary and secondary, condenser water, sewage / sump / lift (ejector) pumps, stormwater / OSD, pool / spa, irrigation, rainwater reuse. Fire pumps are designed by the local fire contractor; we provide the duty check (flow, pressure, tank and the interlock interfaces) and it goes into the calc register like any other calc. Each system delivers five things, all generated from the DB and the product library, each number with a calc ID:

1. Hydraulics: flow (fixture units or load), static head, friction and fitting losses, residual pressure at the end, NPSHa; the system curve.
2. Selection: the product-library pump curves overlaid on the system curve — duty point, efficiency at duty, VSD minimum speed, motor kW and efficiency class (IE3 / IE5). The Kaiquan curves are digitised into the library before the first selection; a pump whose curve is not in the library goes to procurement first, like any product outside `products/index.csv` (`references/library-and-repos.md`).
3. Configuration: duty / standby / assist, N+1, tanks and break tanks (intermediate tanks on tall risers), pressure zones and PRVs, water-hammer protection.
4. Control description: start / stop conditions, setpoint mode (constant pressure / proportional pressure / differential pressure / level), staging (pump add / remove), rotation, alarms, failure modes, the BMS points list, power supply (normal / essential / generator), fire-mode interlock.
5. Deliverables: P&ID, pump schedule, control schematic, points list, functional description, and the riser schematic with the pressure at every level (HY-0040 depth, `references/drawing-standards.md`).

The control description is what the commissioning tests (`templates/commissioning-tests.csv`) are written from; a pumped system without a functional description has no commissioning test, and its pump-logic rows in `calcs/coverage-<stage>.csv` cannot read PASS (`references/bq-and-calc-book.md`, calculation coverage).

## Fire (F)

S1: fire strategy draft (with ARCH). S3: fire-water schematic, detection zoning concept.
S6 mandatory: sprinkler hazard classes, densities and hydraulic calculations (AS 2118.1; residential heads in SOUs), hydrant hydraulics with pump and tank sizing (AS 2419.1; AS 2941 pumpsets), hose reels (AS 2441), detection and EWIS zoning and sound levels (AS 1670.1 / .4), emergency lighting (AS/NZS 2293), fire dampers (AS 1682), penetration schedule mapping every penetration through a rated element to a tested system (AS 1530.4 / AS 4072.1), FIP and booster locations per the fire brigade, fire-mode matrix with MECH and ELEC. NZ: C/AS2 or C/VM2, NZS 4541, NZS 4512.
Performance solutions run through the fire engineer at S9; allow months.

## Vertical transport (V)

S1: lift count and shaft sizes from a traffic calculation (CIBSE Guide D method: 5-minute handling capacity, interval); accessible lift (AS 1735.12), fire / stretcher lift requirements; pit and overrun from the supplier.

## Civil (C)

S1–S6 as required: site stormwater and OSD, WSUD, driveway grades and swept paths, retaining walls (platform geometry on sloped sites — centre the platform on the slope midpoint to split cut and fill), pavements, earthworks, sewer and water connections. Large scope on resort sites.

## ESD / thermal (X)

Two thermal models, accepted separately (runbook and prompts in `references/toolchain.md`):

- **Loads version at S3**, before equipment selection. Inputs: zone geometry, floor heights, wall and glazing U-values and SHGC, orientation, internal gains, schedules, the EPW — a 2D plan plus one section has all of it — and, locked with the run, the design days (source and conditions), indoor temperature and RH, outdoor air, the latent basis, diversity and the sizing factor. Outputs: zone and block design loads (`design_cooling_kW`, `design_heating_kW`), the annual energy from the EPW as a separate figure (never the annual maximum of recent weather used as the sizing load), and the façade comparison (WWR, glazing, shading, insulation) with ΔCAPEX / ΔOPEX for the PD's G3 decision. S5 selects from these design loads and checks the vendor's capacity and power at the project's conditions, not the nominal rating.
- **Compliance version at S7**, rebuilt from the S7 IFC geometry: NCC Section J JV3 reference building (NZ: H1 modelling or verification method; Japan: BEI), PASS / FAIL with the margin, parameters retained with the result, shading and self-shading checked on the real geometry.

Signatures: the ESD consultant verifies and signs the Section J / H1 report at S9. NatHERS for Class 1 / 2 housing is issued by an accredited assessor with accredited software (FirstRate5 itself is free) — the AI prepares the model, a person presses the button. Daylight with Radiance where required. Green Star / NABERS credits only where the brief targets them. A failed or not-run simulation is reported as such (`run_status`), never as PASS.

## Façade (Q)

Wind pressures on cladding (AS/NZS 1170.2), glazing (AS 1288, AS 2047), thermal and condensation (Section J; AS/NZS 4859.1), non-combustibility (NCC C2D10 for Type A/B external walls), weatherproofing (NCC F3; AS 4284 testing), BMU / maintenance access. A façade engineer signs; the package is prepared like any other.

## Acoustics (N)

SOU separation (NCC Part F7: Rw + Ctr targets), plant noise to neighbours (council conditions), external noise intrusion (AS/NZS 2107 internal levels), restaurant / lounge noise. Mass-law and composite-Rw scripts; an acoustic consultant signs where the DA requires a report.

## Seismic restraint of services (all disciplines; NZ always)

Non-structural parts — ducts, pipes, cable trays, busway, switchboards, transformers, generators, tanks, pumps, AHUs, sprinkler pipework, ceilings and façade attachments — are designed for earthquake actions like any other element, not left to the contractor. NZ: NZS 4219 (seismic performance of engineering systems in buildings) with NZS 1170.5 Section 8 for the part forces; sprinklers to NZS 4541; proprietary brace systems with their tested capacities and a producer statement (PS1) for the restraint design. AU: AS 1170.4 Section 8 (parts and components) where it applies to the building and part category — record the clause and importance level where it does not. The workflow is the same as for everything else: `STR-SEIS-01` at S3 issues the part forces and drift demands per level; at S6 each discipline delivers restraint plans per level (brace type, spacing per run size, anchor loads to structure via `STR-LOAD-06`, flexible connections at equipment and at every seismic-joint crossing, clearances at penetrations) and the `MECH / ELEC / HYD / FIRE-SEIS-01` coverage rows; brace envelopes are reserved in the 2D lanes (`references/services-coordination-2d.md`) and modelled in the S7 IFC so they do not surface as clashes; the MEP department details them in BIM at S10 to LOD 400; quantities go into the procurement BQ as itemised brace assemblies and anchors, never as a percentage.
