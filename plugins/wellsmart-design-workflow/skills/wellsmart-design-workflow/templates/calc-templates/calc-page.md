# Calc page — one page per calc ID (the format every calculation is written in)

Copy this block for every calc. The calc book (`gen_calcbook.py`) renders one section per page in this order; the JSON export at the end of the book carries the same fields. A field left empty is a defect: write `N/A — <reason>` or `ASSUMED — TBC: …` instead. Numbers come from the script, never typed from memory; every limit comes from the standards digest by record id.

---

**Calc ID** `<DISC>-<NNN>` · **Master key** `<calc_key from calc-master-list.csv>` · **Title** `<what is being calculated, EN>` `<中文>`
**Discipline** `<MECH | ELEC | HYD | FIRE | STR | FAC | ACU | THM | VT | CIV | ARC | TRF | CON>` · **Stage** `<S3 | S5 | S6 …>` · **Sheets referencing this calc** `<M-131, M-500 …>`

**1 Purpose 目的** — one sentence: what decision or sizing this calc supports and which objects it governs (element ids / tags).

**2 Standard / basis 依据** — standard, year, clause, digest record id for every limit or method used (`AS 1668.2:2012 cl 3.x · r-AS1668.2-2012/3.x/r1`); company rule ids from the checks library; `CLAUSE TO CONFIRM` if the source text is not in the knowledge base.

**3 Formula / method 公式与方法** — the formula(s) in symbols with units, or the named method (equal friction, IEC 60909, Hazen-Williams…). Solver and version if a tool is used (EnergyPlus 24.x, OpenSeesPy x.y).

**4 Inputs 输入** — table: symbol · value · unit · source (brief §, DB path `db/mech.json#…`, vendor datasheet document_id / revision, survey, authority letter) · status (confirmed / ASSUMED — TBC with range, affected objects, owner, expiry gate).

**5 Calculation 计算** — the steps with intermediate numbers (not only the answer); collapsible script (`scripts/<name>.py`, version, git hash) and its output; curves / charts as embedded SVG.

**6 Result 结果** — the result(s) with units, per object where relevant (per zone / per riser / per board / per member).

**7 Check against limit 校核** — result vs limit (value, source record id) → **technical status** `PASS | FAIL | NOT CALCULATED | TBC | N/A`. A FAIL states what design change or valid alternative solution closes it; it is never waived.

**8 Selection / consequence 选型与后续** — what this calc fixes: the selected size / model / rating / spacing, the DB fields written, the sheets and BQ lines affected, and the downstream calcs that depend on it (`depends_on` / `feeds`).

**9 Assumptions 假设** — every `ASSUMED — TBC` line used, with range, affected objects, owner and expiry gate; sensitivity where the result is close to the limit.

**10 Blind re-calculation 盲算** — second family's value(s), difference %, tolerance, disposition (agree / disputed / arbitrated); round and packet hash. Left empty until the review round; the coverage file records `blind_checked` Y/N.

**11 Record 记录** — date (no revision label while drafting); script version; author session; layer-2 check note; consultant signature binding (document_id / revision_id / SHA-256 when endorsed).

---

## Discipline-specific mandatory content (add to section 4–8 as applicable)

- **MECH** — airflow / water flow per object; velocity; pressure drop per metre and per run; equipment duty at project conditions (not nominal) with vendor_duty_check; NR at the receiver; insulation thickness with R conversion; control setpoints referenced to the sequence.
- **ELEC** — current per phase; derating factors listed individually; cable size and type; volt drop per segment and cumulative; fault level (max / min) at the point; device rating / curve / settings; discrimination statement; earth-fault loop value vs limit.
- **HYD** — fixture / loading units; probable simultaneous demand; static and residual pressures at the highest and lowest fixtures in every zone; velocities; storage turnover; temperatures at storage and at the furthest fixture; backflow hazard rating.
- **FIRE** — hazard class; design density / AMAO; most disadvantaged and most favourable points with pressures and flows; pump duty at both; tank effective volume; zone sizes; spacing rules applied; interface actions (cause & effect row ids).
- **STR** — load case table; combination governing; analysis result (force / moment / reaction / drift) with model version; capacity with factors; utilisation; deflection long-term; fire check; detailing consequence (reinforcement / section / connection).
- **FAC** — pressure zone and Kl; tributary area; fastener tested capacity and capacity factor; **fixing spacing per zone** (edge / corner / field) and edge distance; movement stack-up per joint; anchor edge distances; test plan clause.
- **ACU** — source levels by octave band; path attenuation items; receiver criterion; margin; isolator deflection and efficiency.
- **THM** — design-day basis; zone list; sizing factors; results.json fields quoted; option table for façade comparisons; JV3 reference vs proposed margins.
- **VT / CIV / ARC / TRF / CON** — the governing criterion, the value, the margin and the sheet where it is drawn.
