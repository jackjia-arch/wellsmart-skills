# Sheet content checklists, cross-checks and the never-again list

What every sheet type must show, what is habitually missed, and what must agree between drawing, schedule, schematic, DB and calc. Use it three times: when planning the sheet list (`drawing-list.md`), when drawing (put every applicable item on the sheet or in its schedule), and when reviewing (a missing item is a `major` issue; a mismatch between two documents is a `blocker`).

Numeric limits below are the design-driving values to check; where a value is marked **(verify)** confirm it against the standards digest / knowledge base before relying on it, and cite standard, year and clause. Never quote a number from memory on a sheet.

Contents: 1 Architecture · 2 Interiors · 3 Structure · 4 Mechanical · 5 Electrical · 6 Hydraulic · 7 Fire wet / dry · 8 Combined services · 9 Specialist · 10 Schedules and schematics · 11 Cross-check matrix · 12 Never-again list

---

## 1 Architecture (A)

**Plans (1:100 GA, 1:50 enlarged)**: grids with bubbles; overall and grid-to-grid dimensions; opening setouts; levels (SSL, FFL) with set-downs (wet areas 20–50 mm typical); room names, numbers and areas; wall-type tags carrying FRL and Rw; door and window tags; fire compartment boundaries and FRLs; egress paths with travel distances (Class 2/3: 20 m to a point of choice, 40 m to an exit — verify NCC D2); accessible paths; waterproofing extents; ceiling heights; finishes tags; furniture for sizing only; north; key plan on enlarged sheets.

**Sections / elevations**: levels, floor-to-floor, ceiling zones, structural depths, façade build-ups with material tags, FRL of floors, balustrade heights (1,000 mm at floors, 865 mm on stairs — verify NCC D3), roof falls and overflows, plant screens, BMU and roof anchor points.

**Details (1:10 / 1:5)**: waterproofing at thresholds, hobs, balconies and planters; window and door head/sill/jamb with flashings and drainage; roof edges and box gutters; movement joints; fire stopping at slab edge and service penetrations; balustrade fixings; stair nosings and tactile indicators; slip-resistance classes by location.

**Schedules**: wall types (build-up, thickness, FRL, Rw, wet-area facing); doors (size, fire rating, hardware set, closer, hold-open, seals, accessible clear width 850 mm — verify AS 1428.1, vision panel, threshold); windows (size, glazing type, safety glass, U/SHGC, restrictors); finishes; room data sheets.

Commonly missed: door hardware sets and closers on fire doors; hold-open devices tied to detection; threshold heights at accessible doors; balustrade climbability zone; roof access and anchor points; plant replacement routes; bike parking dimensions; bin room wash-down; acoustic seals on SOU doors.

## 2 Interiors (I)

**Room plans / elevations (1:50 / 1:20)**: setout dimensions to grid or finished face (state which); joinery tags; FF&E numbers; finishes tags (FL-/WF-/CL-/PT-/JN-); power and data positions coordinated with ELEC; luminaire positions coordinated with RCP; mirrors, TVs, blinds; bathroom fixture setouts (pan centreline 450–460 mm from wall in accessible rooms — verify AS 1428.1); TMV locations; accessible room circulation.

**RCP (1:50)**: ceiling types and heights; bulkheads; access panels (size, location, what they serve); luminaires; diffusers and grilles; sprinkler heads; detectors; speakers; strobes; curtain tracks; setout dimensions.

**Schedules**: finishes with fire-hazard properties (group number, CRF) and slip rating; FF&E with supplier, dimensions, lead time; joinery with materials and hardware.

Commonly missed: access panels under every damper, valve and FCU; fire-hazard properties of wall and ceiling linings; slip rating of bathroom floors; blind pockets vs sprinkler coverage; TV/mirror power positions.

## 3 Structure (S)

**GA plans**: grids; member tags (B, C, W, F, P) matching schedules; slab thickness, set-downs and steps; SSL levels; PT tendon zones and no-drill areas; penetrations with size, location and trimming; movement joints; holding-down bolts; edge details references; construction joints; camber; propping and backpropping notes.

**Sections / details**: reinforcement or PT layout, laps, cover; connection details; core wall reinforcement; transfer members; stair flights and landings; lift pit and overrun; footings and piles with cut-off levels; retaining walls with drainage.

**Schedules and notes**: member schedules with sizes and reinforcement; concrete grade and cover per exposure class and FRL (AS 3600 — verify tables); steel grades and coatings; bolts and welds; design loads and code references; deflection limits; durability; construction sequence and temporary works assumptions.

Cross-checks: every penetration on MEP sheets exists on the structural penetration plan; slab thickness matches ceiling-zone section; FRL of structural elements matches the fire strategy; foundation levels match geotech; loads match `db/loads.json`.

## 4 Mechanical (M)

**Air layouts (per level, 1:100 A1)**: ducts double-line with size (W×H or Ø) and airflow labels every 150 paper mm; velocity within limits; fittings drawn (radius elbows, turning vanes, transitions); volume control dampers at every branch; fire dampers at every rated penetration with tag, FRL and access panel on both sides (AS 1682); smoke and motorised dampers; access panels; flexible duct with maximum length (6 m — verify AS 4254); diffusers and grilles with type, size, airflow, throw and NC; OA intakes and exhaust discharges with separation distances (AS 1668.2 Table 3.4 — 6 m intake-to-discharge as the general case, verify per category); insulation type and thickness per NCC Part J6 tables (verify); external duct weatherproofing; attenuators and acoustic lining; duct supports; FCU/AHU tags and schedule references; condensate drains with fall, trap and tundish; drain trays; maintenance clearances (filter withdrawal length, coil pull); fire-mode operation notes; kitchen exhaust hoods, grease duct (welded, cleanouts, fire rating, slope) and discharge.

**Pipework layouts (CHW / HHW / CDW / refrigerant)**: DN per segment with flow arrows; isolation valves at every branch and item; balancing or PICVs; strainers; flexible connectors and check valves at pumps; test points; air vents at high points and drains at low points; expansion tanks and anchors / guides; insulation and vapour barrier; refrigerant pipe sizes per manufacturer with maximum length and elevation; leak detection where charge limits apply (AS/NZS 5149 — verify); condensate routes.

**Plant rooms (1:50)**: equipment footprints with maintenance clearances; replacement route for the largest component; plinths; vibration isolation; drains and bunds; ventilation; lighting and power; acoustic treatment; sections.

**Controls**: control schematic per system; points list; sequence of operation; fire-mode matrix; interfaces (BMS, GRMS, fire, lifts).

**Coordination content on every M (and E / H / F) layout** (`references/services-coordination-2d.md`): zone envelope in the title area (soffit RL, ceiling RL, available depth, band order); bottom-of-duct / tray RL and pipe centreline RL at every change of level and at every crossing; crossing ids in bubbles with the C-300 section reference; access clearances hatched at dampers, boxes, valves, strainers, PRVs and tray pull points; riser exit straight lengths dimensioned; drains with invert RLs and fall; a CROSSINGS ON THIS SHEET table from `db/crossings.json`; `coord_check` counts in the manifest with the CSV in the packet.

Commonly missed: VCDs on every branch; access panels; condensate traps at draw-through coils; fire dampers where ducts cross rated walls in ceiling voids; intake/exhaust separation to substation and generator; kitchen exhaust cleanouts; refrigerant charge limits in small rooms; drain and vent points; plant replacement route; RLs at crossings; a large duct and a DN ≥ 100 main crossing with no registered section.

## 5 Electrical (E)

**Power / lighting layouts**: every outlet, luminaire and item with circuit reference (board/circuit); switching groups; isolators at every mechanical item; emergency luminaires and exit signs (AS/NZS 2293 spacing — verify); cable trays and ladders with size and segregation; penetrations; DB locations with access clearance; comms outlets with numbering; lightning down conductors and test points; EV chargers; metering.

**Single-line diagram**: every switchboard with incoming supply (source, cable size, type, cores, length, protective device upstream, fault level at the board), main switch rating, busbar rating, fault rating and form of separation (AS/NZS 61439), phase / neutral / earth conductor sizes, all sub-mains with size and length, all protective devices with rating, curve and RCD sensitivity, metering CTs, surge protection, generator changeover and ATS, UPS with bypass, fire-rated (WS) circuits marked, labels, and the physical entry direction of supply and outgoing cables (top / bottom / side) annotated with arrows.

**DB schedule (one sheet per board)**: header block — board tag, location, fed from, feeder cable (size, type, cores, length, VD), main switch rating, busbar rating and fault rating, form, IP rating, mounting, entry direction, MEN/earthing arrangement, surge device. Rows sorted by circuit number with: phase assignment (L1/L2/L3), CB rating and curve, RCD (type and mA), cable size / type / installation method, length, voltage drop %, load VA, description, location served, notes. Footer: load per phase and balance, total with diversity, spare ways (25% minimum — verify company rule), fire-rated circuits, control circuits.

**The alignment rule**: the board elevation (chassis layout) and the DB schedule list the same devices in the same order, and each device's pole positions line up with the busbar phase sequence drawn on the elevation. Incoming supply and every outgoing cable are annotated with direction arrows and cable size at the terminal. A schedule whose rows do not match the elevation, or a board with no in/out direction and cable sizes, is a blocker.

Cross-checks: sum of loads with diversity ≤ main switch ≤ busbar; fault level at the board ≤ busbar and device fault ratings; discrimination between upstream and downstream devices; cable current rating ≥ device rating (AS/NZS 3008.1.1, with derating); cumulative voltage drop from MSB ≤ project limit (5% total — verify AS/NZS 3000); phase imbalance within 10–15%; every circuit on layouts appears in the schedule and vice versa; sub-main sizes identical at both ends; earthing conductor sizes; RCD provisions (AS/NZS 3000 cl 2.6.3 — verify); WS classification for fire pumps, lifts, EWIS and stair pressurisation (AS/NZS 3013).

Commonly missed: in/out direction; cable sizes at terminals; RCDs; spare ways; earth bar and neutral sizing; isolators at FCUs; emergency lighting in plant rooms; exit signs at every exit door; lightning protection test points; generator essential-loads list; shunt trips for fire mode.

## 6 Hydraulic (H)

**Cold and hot water layouts**: DN per segment with material per the materials matrix; flow arrows; isolation valves at every floor branch, fixture group and item of plant; PRV stations with settings and bypass; water meters (authority, NABERS sub-metering, tenancy); backflow prevention by hazard rating — containment at the boundary, zone at fire services, irrigation, cooling towers and kitchens, individual at hose taps and bidets (AS/NZS 2845, AS/NZS 3500.1 — verify ratings); TMVs (locations; 50 °C at personal-hygiene outlets, 45 °C in care facilities — verify AS/NZS 3500.4); hot water flow and return with balancing valves (dynamic on tall risers); dead-leg limits; heat trace where no return; storage temperature ≥ 60 °C and Legionella regime (AS/NZS 3666); expansion loops / bellows / anchors / guides on risers; air vents at high points, drains at low points; water hammer arrestors at quick-closing valves; insulation type and thickness (NCC Part J8 for heated water — verify); pipe supports and spacing; sleeves and fire-stopped penetrations; labels every 150 paper mm; drinking-water points; hose taps with vacuum breakers; test pressure notes; fixture schedule reference.

**Sanitary drainage layouts (per level)**: every fixture with a trap; trap seal depths (verify AS/NZS 3500.2); floor waste gullies in every wet room — bathrooms, laundries, kitchens, bin rooms, plant rooms, pool plant, car wash bays — with grade arrows to the FWG and the charging fixture named where the trap could dry out (or a trap-seal primer); floor grades and set-downs; DN of every pipe; minimum grades (DN100 1:60, DN150 1:100 — verify); invert levels at every change; inspection openings at the head of each drain, at junctions, at changes of direction and at the boundary, at the spacing required (verify); cleanouts; stacks with tags; vents (stack vent, relief vent, cross vent, group vent) with termination position (above roof, distance from openings and intakes — verify); overflow relief gully on every sanitary drain, grate at least 150 mm below the lowest fixture outlet and at least 75 mm above finished ground, outside the building — verify; boundary trap or IO where the authority requires; tundishes with air gap for every condensate, PRV, TPR valve, HWU relief and plant drain discharge; condensate drains from FCUs and AHUs with falls and traps; trade waste — grease arrestor sized by covers, location with pump-out access, vent; sewer pump stations — duty/standby, wet-well volume, level controls, non-return and isolation valves, vent, alarm to BMS, emergency storage, power source; pool backwash to sewer with cooling and air gap; car-park drains through an oil / silt separator; lift-pit sump with pump (never a direct sewer connection); plant-room floor drains with bunds; expansion joints; fire-rated collars at penetrations; acoustic wrap above habitable rooms; supports; access panels.

**Stormwater layouts**: roof falls; gutters with grades; downpipes with DN and catchment area (AS/NZS 3500.3 tables — verify); box gutter overflow devices sized for the full flow; rainheads and sumps with overflow; syphonic systems as a performance solution with the designer named; stormwater pits with cover and invert levels; OSD tank with orifice and overflow; connection point; rainwater tank with first flush, overflow, backflow protection and top-up; subsoil drainage.

**Gas**: meter position and ventilation; pipe sizes; isolation; appliance connections and flues; test points (AS/NZS 5601).

**Schematics (600 series)**: to the HY-0040 depth — every level with RL and static pressure; DN per segment with GRAV./PRESS.; branch to every SOU; every meter; pumps and tanks with tags and duties; PRV zones; destinations; plus our additions (design flow and basis, velocity and pressure drop per segment, residual at the most disadvantaged point, pump duty point with calc ID, storage hours, one-line control, backflow and isolation, Legionella regime, assumptions).

**P&IDs**: one per pumped system with the five pump-logic deliverables.

## 7 Fire — wet (F-1xx) and dry (F-2xx)

**Sprinkler layouts**: hazard class per area; heads with type, K-factor, temperature rating and coverage; spacing and distance to walls within limits (verify AS 2118.1 tables); obstructions; pipes with DN; hangers; floor control valve assemblies (isolation, flow switch, test and drain); pressure gauges; drain points; riser tags; the hydraulically most remote area marked; heads in concealed spaces where required; head counts per level.

**Hydrant and hose-reel layouts**: hydrant valves with coverage (verify AS 2419.1: hose-lay coverage), hose reels with coverage (verify AS 2441), booster assembly with brigade access, block plan, fire brigade signage, pipe materials and pressure class, thrust blocks and anchors, test points, isolation.

**Pump rooms and tanks (1:50)**: pumps with duties, suction and delivery, test lines, relief, fuel storage and bunding, ventilation and exhaust, access, tank volumes and levels, fill and overflow, drain-down, level indication.

**Detection / EWIS / emergency lighting layouts**: detectors with type and spacing (verify AS 1670.1), manual call points at exits, sounders / strobes / speakers with coverage, FIP, mimic, fire fan control, WIP phones, zone boundaries, interfaces (lifts, AC shutdown, door holders, dampers, flow switches), cable types (WS class), loop and zone schedule, cause and effect matrix.

Commonly missed: heads in ceiling voids and under obstructions; test and drain at floor control valves; hydrant coverage of plant rooms and car parks; booster location vs brigade access; MCPs at every exit; sounder coverage in guest rooms (75 dBA at the bedhead — verify); interfaces list; WS cable classes.

## 8 Combined services (C)

Corridor coordination plans 1:50 per corridor type and sections 1:20 every 8–12 m and at every large × large crossing: every service with size and height (underside), the ceiling-zone layering rule respected (structure → fire → ducts → pipes → trays), clearances to structure, penetrations with sleeves, fire-stopping at rated walls, access panels vs services above, module and cassette boundaries, support rails. Plant-room combined 1:50 with equipment, all services and maintenance zones. The C-sheets are generated from the same `db/services-routes.json` as the discipline layouts — never drawn separately — and every C-300 section is referenced from a `db/crossings.json` entry; the sheet carries the zone depth budget and the `coord_check` result for the level (`references/services-coordination-2d.md`).

## 9 Specialist

**DDA**: accessible paths with widths and gradients; door circulation spaces; accessible toilet and bathroom setouts (pan, grab rails, basin, mirror, door swing, alarm); ramps and landings (1:14 — verify AS 1428.1); TGSIs; handrails; signage and braille; hearing augmentation; lift car and control dimensions; accessible parking.

**Façade**: panel types and setout; joints and movement; primary and secondary weatherproofing lines; drainage paths; fixings and brackets; fire edge seals and cavity barriers; combustibility statement; BMU restraint points; glazing types and safety glass; wind pressures by zone.

**Acoustics**: wall and floor types with Rw + Ctr; door seals; attenuators; vibration isolation; plant enclosures; boundary noise limits.

**Traffic**: swept paths with the design vehicle named; ramp gradients and transitions; headroom (2.2 m general, 2.5 m accessible — verify); sight lines; signage; loading dock equipment.

**VT**: shaft dimensions, pit, overrun, machine room, lobby, fire service lift features, accessible controls.

**Civil**: site levels, stormwater pits and pipes with IL and cover, OSD, pavements, kerbs, retaining walls with drainage, erosion controls.

## 10 Schedules and schematics — general rules

Every equipment schedule: tag, location, duty, dimensions, weight, electrical load, noise, supplier SKU, certification status, lead time, calc ID for the duty. Every schematic: all tags present on layouts, riser tags consistent, calc IDs on design values, key design-data box, assumptions box. A tag appearing on a layout must appear on a schedule and in the DB; a schematic value must trace to a calc ID.

## 11 Cross-check matrix (run before every gate)

| Check | Between |
|---|---|
| Every tag | layout ↔ schedule ↔ DB ↔ schematic |
| Circuit references | layouts ↔ DB schedule ↔ SLD |
| DN / duct size | layout ↔ schematic ↔ calc |
| FRL | wall types ↔ fire strategy plan ↔ penetration schedule ↔ door schedule |
| Levels and grids | every sheet ↔ levels.json / grids.json |
| Door numbers | plans ↔ door schedule ↔ hardware ↔ FRL ↔ DDA clear width |
| Equipment locations | layout ↔ plant room 1:50 ↔ electrical isolator ↔ drainage tundish |
| Riser sizes | cassette / shaft ↔ structural penetration plan ↔ duct sizes |
| Airflow sums per level | diffusers ↔ AHU duty ↔ thermal loads |
| Fixture units per stack | drainage layout ↔ stack DN ↔ calc |
| Head and hydrant counts | layouts ↔ hydraulic calc ↔ BQ |
| Loads | DB schedules ↔ maximum demand ↔ transformer / generator |
| Voltage drop | cumulative from MSB ≤ limit |
| Fire dampers | every rated-wall crossing ↔ damper schedule ↔ access panel |
| Wet rooms | every wet room ↔ an FWG ↔ a charging fixture or primer |
| Reliefs and condensate | every relief / condensate ↔ a tundish |
| Sanitary drains | every drain ↔ an ORG; every stack ↔ a vent |
| Quantities | DB take-off ↔ BQ ↔ drawings (sample) |

## 12 Never-again list

Annotation (added 2026-09-14 from the cable-pit and pillar sheets): leaders crossing each other; a leader through other cables or objects; a leader across a dimension or extension line; labels at scattered heights instead of one aligned column per side; label order different from target order; the 240 mm² label on the 25 mm² cable; four leaders to four identical cables; text on a dashed line or touching a bus; a dimension put on the label side. All of these are counted by `scripts/annotate.py check` and the overlay, and a non-zero count is not issued.

Floor waste gullies in every wet area and plant room, charged or primed. Tundishes for every relief, PRV, TPR and condensate. Overflow relief gully on every sanitary drain. Inspection openings where required. Stack vents and their terminations. TMVs where required. Isolation valves at every floor branch. PRVs with bypass. Water hammer arrestors. Backflow devices at every hazard point. Expansion provisions on risers. Fire dampers with access panels on both sides. VCDs at every branch. Condensate traps at draw-through coils. Air vents and drains. DB schedule with in/out direction and cable sizes, aligned with the board elevation. RCDs and spare ways. Earth bars and neutral sizing. Emergency lighting in plant rooms. Exit signs at every exit door. Hose-reel and hydrant coverage of plant rooms. Sprinkler heads in ceiling voids where required. Fire door hardware and hold-opens. Accessible door circulation. Hearing augmentation. TGSIs. Balustrade climbability. Box-gutter overflows. Roof access and anchor points. Plant replacement routes. Refrigerant leak detection. Kitchen exhaust cleanouts. Grease-arrestor pump-out access. Bin room wash-down tap and drain. Car-park oil separator. Lift-pit sump pump. Stair pressurisation relief. Lift fire-service recall. Generator fuel bund and vent. Substation ventilation separation. EV charging distribution. BMU restraint points.
