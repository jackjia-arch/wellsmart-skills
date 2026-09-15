# Operator prompt card — what the PM / operator types at each step

The detailed drawing requirements, calculation lists, standards, checks and formats are all inside this skill; the operator never pastes them into a prompt. The skill loads automatically when a Well Smart project, stage, gate, sheet, calc or review is mentioned. A good operator prompt therefore has four parts only: **project** (folder or project_id), **stage / task**, **scope** (levels, disciplines, sheets, systems), and **where the inputs are** (files, links, decisions). Everything else the AI expands itself: the sheet list, the per-sheet prompt skeleton (`references/drawing-prompts.md`), the coverage rows (`references/calc-coverage.md`), the coordination checks, the gate report format.

The AI's side of the bargain: it reads SKILL.md and the stage reference before working, answers every coverage row, runs the checks, and stops at the gate with the high-risk table. If it asks the PD a question that a bounded assumption would have covered, or presents work without the checks, that is a skill violation to report, not a prompt problem.

Prompts below are given in Chinese (what staff type) with the English equivalent. Replace the bracketed parts. `<项目>` is the project folder in the Drive sync directory or the ProjectBook project_id.

## Stages

| Step | Type this (中文) | English equivalent | What comes back / what to check |
|---|---|---|---|
| S0 kick-off | 新项目 <项目>，跑 S0。PD 的意图：[几句话]。地块资料在 [路径]。 | New project <project>, run S0. PD intent: […]. Site data at [path]. | Brief with every field filled or ASSUMED; site data pack index; regulatory basis; certification pathway; programme; Cost Plan 0; specialist matrix; handover matrix with PM and Operation Owner named; version lock; G0 gate report with coverage-S0. Check the ASSUMED list and the two names. |
| S1 concept | <项目> 跑 S1，[塔楼 / 别墅]，[层数 / 房间数]，[特殊要求]。 | <project> run S1, [tower / villa], [levels / keys], [special requirements]. | Concept plans per unique level, area schedule, systems space table, structural memo, fire strategy memo, specialist S1 outputs, Cost Plan 1, G1 report. Check the space table and the fire strategy departures list. |
| S2 interiors | <项目> 跑 S2。风格：[给了就写 / 没给就让 AI 出]。 | <project> run S2. Style: [given / propose]. | ID layouts, FF&E list, finishes concept, ID compliance report with exceptions, G2 report. Check the exceptions table. |
| S3 freeze | <项目> 跑 S3。热模型负荷版结果在 [results.json 版本链接]（如已跑）。 | <project> run S3. Loads-model results at [results.json revision link] (if run). | GA set, STR 2D, one schematic per system at HY-0040 depth, services-zoning plans with lanes and depth budgets, ceiling-zone sections, Load & Energy Report, façade option comparison with simple annual return, PBDB / FEB draft, Cost Plan 2, coverage-S3, G3 report. The PD decides the façade option. |
| S4 IFC | <项目> 出 S4 IFC 并发布网页模型。 | <project> build the S4 IFC and publish the viewer release. | IFC (ARCH + STR + ID + MEP reservations), model-check report, release id. Walk it; pick issues in the viewer. |
| S5 equipment | <项目> 跑 S5 选型。厂家回复在 [路径]。 | <project> run S5 selection. Vendor replies at [path]. | Equipment schedule with vendor_duty_check, comparisons with simple annual return, RFQ drafts, asset register, G4a report. Unconfirmed items stay TBC. |
| S6 detailed design | <项目> 跑 S6，专业 [MECH / ELEC / HYD / FIRE / STR / ARCH / ID / 专项]，楼层 [全部 / L22 机房]。 | <project> run S6, disciplines […], levels […]. | Per discipline: sheet list first (approve it), then sheets one per response with QA counts; calc pages and coverage-S6 (every row answered); coord_check per level before layouts; DBR, compliance matrix, PS / SiD entries, spec draft, commissioning tests, vendor handover requirements, BQ (ESTIMATE), G4 report. Check the coverage summary and the crossing reports. |
| S7 3D + clash | <项目> 跑 S7：MEP 进 IFC、碰撞、合规版热模型。 | <project> run S7: MEP into IFC, clash, compliance thermal model. | Detailed IFC, clash report (AI-resolved / open), penetration schedule, Energy Compliance Report, release sheets per package, G5 report. Then: 处理本版已确认的问题 / handle the confirmed issues on this release. |
| S8 review | <项目> 跑 S8 全包审阅。 | <project> run the S8 whole-package review. | Review rounds (≤ 5), issue register, high-risk table, G6 report with P0 / P1 = 0, FAIL = 0, expiring assumptions = 0. |
| S9 sign-off | <项目> 整理 S9 交付包，地区 [QLD / NSW / NZ]，委托包 [A / B / C]。 | <project> assemble the S9 package, region […], engagement package […]. | Certification pack with transmittal, index, manifest with hashes, `.e2k` + assumptions sheet; draft consultant brief with the ten contract items. Consultants are contacted only now. |
| S9 comments | <项目> 回复顾问意见：[文件 / 链接]。 | <project> answer the consultant comments: [file / link]. | Per comment: basis, affected objects, diff, reruns, closure evidence — not a full rewrite. |
| S9 endorsement | <项目> 登记顾问签署：[原件 / 函件]，签的是 [文件 / 版本]。 | <project> register the endorsement: [original / letter], covering [document / revision]. | Endorsement record bound to the exact revision and hash; "to be confirmed" if the scope is unclear. |
| S10 production | <项目> 准备 S10 交接包和采购 BQ，采购包 [清单]。 | <project> prepare the S10 hand-off pack and procurement BQ, packages […]. | Frozen IFC / DB / calc book, hand-off list for the drafting team and the MEP department (LOD 400 coordination), BQ (PROCUREMENT) itemised, RFQ packs, long-lead triggers, release sheets. |
| S10 write-back | <项目> 人工 Revit 改了 [图号 / 构件]，做差异比对并回写。 | <project> manual Revit changed [sheet / elements]; diff and write back. | "No design change" record, or write-back by element id with the affected calcs / sheets / BQ rerun and, where a signed scope is touched, the S9 re-confirmation list. |

## Tasks inside a stage

| Task | Type this | What comes back |
|---|---|---|
| One sheet | 画 <图号> <标题>，<楼层>，<比例>。数据 [db 路径]。 | The nine-part sheet prompt is expanded by the AI; one complete HTML sheet with manifest and QA counts; for MEP layouts the coord_check counts for the level first. |
| Split a sheet | 图 <图号> 太密，先给拆分方案。 | A / B split proposal with reason; draws the first part only after approval. |
| One calculation | 算 <什么>，<对象 / 楼层>，输入在 [路径]。 | A calc page (eleven fields) with calc ID, digest record ids, script and result; the coverage row it answers. |
| Calc coverage | <项目> 出 <阶段> 计算覆盖表；没做的写清为什么、缺什么、谁负责、到哪个 gate。 | `calcs/coverage-<stage>.csv` with every row answered; `check` result; HTML summary. |
| 2D coordination | <项目> 查 <楼层> 机电 2D 协调。 | coord_check CSV + SVG per level; the to-do list for the DB (route / band / RL changes, sections to draw); nothing is drawn until P0 / P1 = 0. |
| Review round | 跑 <G4-MECH> 的审阅。 / 回答 <任务> 的 open issues。 | Packet → blind pass → comparison → drawings pass → feedback.json; then responses.json to fill; state name and open issues by severity. |
| Change request | <项目> 变更：[改什么]。评估影响。 | Impact list (calcs / sheets / models / BQ lines to rerun), cost and programme effect, PD decision required before regeneration. |
| Decision | <项目> 决策：[方案 A / B / C]，持有期 [年]。 | Decision record with CAPEX, annual net OPEX, TCO, ΔCAPEX, simple annual return (≥ 15 % rule), payback, risks; PD decision line. |
| Upload (ProjectBook) | 把任务 <XXX> 的新增 / 修改产物加入项目 <YYY> 的原知识库，匹配 document_id，保留所有未改内容；先返回入库草稿链接和影响清单，正式生效按已有 gate 执行。 | The AI registers the files through the ProjectBook connector (ADD / REVISE / ATTACH) and returns the draft links and impact list; nothing becomes current until the gate / release. If the connector is not in the session it says so and leaves the batch in `kb-outbox/`. |
| EnergyPlus results | 读 [results.json 版本链接] 和 [report.md 版本链接]，核对同一批输入与运行结果，更新 gate report，S5 用这份负荷。 | Loads and façade comparison in the gate report; results.json fields quoted; run_status checked. |
| IFC issues | 处理本版已确认的问题。 | Per issue: source change, reruns, new release READY_FOR_REVIEW; NEEDS_RELOCATION where the element is gone. |
| Handover | <项目> 冻结 Handover Baseline，范围 [楼层 / 系统]。 | Scope, manifest with hashes, asset register completeness by the S0 matrix, open items with owners, retrieval test list. |

## What a prompt never needs

Standards clauses, drawing conventions, annotation rules, the status vocabulary, the calc-page format, the coverage list, the review rules, the region rules — the skill carries them. If a member of staff finds themselves typing a standard or a format into a prompt, either the skill is missing something (tell Jack; it becomes a reference update) or the AI ignored it (report as a defect with the response).
