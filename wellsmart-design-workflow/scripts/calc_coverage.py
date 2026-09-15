#!/usr/bin/env python3
"""
calc_coverage.py — the "no silent omission" tool for calculations.

Why it exists
-------------
An AI (like a person) tends to do the calculations it finds convenient and quietly skip the
rest. The master list `templates/calc-templates/calc-master-list.csv` names every calculation
a Well Smart project may need, per discipline, with the stage by which it is due. At every
gate the operator generates a coverage file from the master list and the AI must account for
EVERY row: PASS / FAIL with calc IDs and evidence, NOT CALCULATED with the missing input, an
owner and an expiry gate, TBC with an owner and expiry gate, or N/A with a reason and the person
who accepted it. A blank row, or a status without its required fields, fails `check`, and a gate
report without a passing coverage file is a defect (SKILL.md rule 15, `references/calc-coverage.md`).

Commands
--------
  init     --stage S6 [--disciplines MECH,ELEC] [--master FILE] [--carry calcs/coverage-S3.csv]
           [--out calcs/coverage-S6.csv]
           Write the coverage file for a stage: every master row due at or before the stage
           (cumulative), status blank; rows already answered in --carry are copied across so a
           later stage inherits earlier answers (which must still be re-confirmed at the gate).
  check    FILE [--stage S6] [--register calcs/calc-register.csv] [--master FILE] [--strict]
           Validate the coverage file. Exit 1 on any error. --strict also treats warnings as errors.
  summary  FILE   Counts per discipline and status.
  html     FILE --out FILE [--title T]   Render a coverage file as a standalone HTML page.
  blank    [--stage S6|ALL] [--disciplines ...] [--master FILE] --out FILE [--fragment]
           Render the blank template tables (the "forcing" page): every master row with empty
           status cells, bilingual titles, the fill-in rules at the top. --fragment writes only
           the inner HTML (a <div class="page">) for embedding in a drawing-set HTML.
  selftest        Run the built-in tests in a temp dir.

Coverage file columns
---------------------
calc_key, discipline, title_en, stage_due, status, calc_ids, result_summary, reason,
missing_input, owner, expiry_gate, accepted_by, evidence_ref, blind_checked, date

status ∈ PASS | FAIL | NOT CALCULATED | TBC | N/A  (blank = unaddressed = error)
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import html
import io
import os
import sys
import tempfile
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MASTER = os.path.join(HERE, "..", "templates", "calc-templates", "calc-master-list.csv")

STAGES = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"]
GATES = {"S0": "G0", "S1": "G1", "S2": "G2", "S3": "G3", "S5": "G4a", "S6": "G4", "S7": "G5", "S8": "G6", "S9": "G7"}
STATUSES = ["PASS", "FAIL", "NOT CALCULATED", "TBC", "N/A"]
COVERAGE_COLUMNS = [
    "calc_key", "discipline", "title_en", "stage_due", "status", "calc_ids", "result_summary",
    "reason", "missing_input", "owner", "expiry_gate", "accepted_by", "evidence_ref",
    "blind_checked", "date",
]
MASTER_COLUMNS = [
    "calc_key", "discipline", "group", "title_en", "title_zh", "stage_due", "inputs",
    "method_standard", "outputs", "acceptance", "na_condition", "deliverable_ref",
]


# ----------------------------------------------------------------------------- helpers

def stage_index(stage: str) -> int:
    s = (stage or "").strip().upper()
    if s not in STAGES:
        raise SystemExit(f"unknown stage '{stage}' (expected one of {', '.join(STAGES)})")
    return STAGES.index(s)


def gate_index(gate: str) -> int | None:
    g = (gate or "").strip()
    order = ["G0", "G1", "G2", "G3", "G4a", "G4", "G5", "G6", "G7"]
    if g in order:
        return order.index(g)
    return None


def read_csv(path: str, required: list[str]) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"{path}: empty")
    missing = [c for c in required if c not in rows[0]]
    if missing:
        raise SystemExit(f"{path}: missing columns {missing}")
    return rows


def write_csv(path: str, rows: list[dict], columns: list[str]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in columns})
    os.replace(tmp, path)


def load_master(path: str | None) -> list[dict]:
    path = path or DEFAULT_MASTER
    rows = read_csv(path, MASTER_COLUMNS)
    keys = [r["calc_key"] for r in rows]
    dupes = [k for k, c in Counter(keys).items() if c > 1]
    if dupes:
        raise SystemExit(f"master list has duplicate calc_key: {dupes}")
    for r in rows:
        stage_index(r["stage_due"])
    return rows


def select_master(master: list[dict], stage: str, disciplines: list[str] | None) -> list[dict]:
    si = stage_index(stage) if stage.upper() != "ALL" else len(STAGES)
    out = []
    for r in master:
        if stage.upper() != "ALL" and stage_index(r["stage_due"]) > si:
            continue
        if disciplines and r["discipline"].upper() not in disciplines:
            continue
        out.append(r)
    return out


def parse_disciplines(arg: str | None) -> list[str] | None:
    if not arg:
        return None
    return [d.strip().upper() for d in arg.split(",") if d.strip()]


# ----------------------------------------------------------------------------- init

def cmd_init(a: argparse.Namespace) -> int:
    master = load_master(a.master)
    rows = select_master(master, a.stage, parse_disciplines(a.disciplines))
    carry: dict[str, dict] = {}
    if a.carry:
        for r in read_csv(a.carry, COVERAGE_COLUMNS):
            carry[r["calc_key"]] = r
    out_rows = []
    for m in rows:
        r = {c: "" for c in COVERAGE_COLUMNS}
        r.update({"calc_key": m["calc_key"], "discipline": m["discipline"], "title_en": m["title_en"], "stage_due": m["stage_due"]})
        if m["calc_key"] in carry:
            prev = carry[m["calc_key"]]
            for c in COVERAGE_COLUMNS[4:]:
                r[c] = prev.get(c, "")
        out_rows.append(r)
    out = a.out or f"calcs/coverage-{a.stage.upper()}.csv"
    write_csv(out, out_rows, COVERAGE_COLUMNS)
    carried = sum(1 for r in out_rows if r["status"])
    print(f"wrote {out}: {len(out_rows)} rows due at or before {a.stage.upper()}"
          f" ({carried} carried from {a.carry})" if a.carry else f"wrote {out}: {len(out_rows)} rows due at or before {a.stage.upper()}")
    return 0


# ----------------------------------------------------------------------------- check

def check_rows(rows: list[dict], stage: str | None, master: list[dict] | None, register: dict[str, dict] | None,
               disciplines: list[str] | None) -> tuple[list[str], list[str], Counter]:
    errors: list[str] = []
    warnings: list[str] = []
    by_key = {r["calc_key"]: r for r in rows}
    current_gate = GATES.get(stage.upper()) if stage else None
    cg = gate_index(current_gate) if current_gate else None

    if master is not None and stage:
        expected = select_master(master, stage, disciplines)
        for m in expected:
            if m["calc_key"] not in by_key:
                errors.append(f"{m['calc_key']}: missing from the coverage file (due {m['stage_due']})")
        master_keys = {m["calc_key"] for m in master}
        for k in by_key:
            if k not in master_keys:
                warnings.append(f"{k}: not in the master list (project-specific row — fine if intended)")

    counts: Counter = Counter()
    for r in rows:
        k = r["calc_key"]
        st = (r.get("status") or "").strip().upper()
        counts[(r["discipline"], st or "BLANK")] += 1
        if not st:
            errors.append(f"{k}: status blank — unaddressed. Every row must be PASS, FAIL, NOT CALCULATED, TBC or N/A")
            continue
        if st not in STATUSES:
            errors.append(f"{k}: status '{r['status']}' is not one of {STATUSES}")
            continue
        ids = [x.strip() for x in (r.get("calc_ids") or "").replace(";", ",").split(",") if x.strip()]
        if st in ("PASS", "FAIL"):
            if not ids:
                errors.append(f"{k}: {st} without calc_ids — a calculation that has no calc ID is not a calculation")
            if not (r.get("result_summary") or "").strip():
                errors.append(f"{k}: {st} without result_summary (result vs limit)")
            if not (r.get("evidence_ref") or "").strip():
                errors.append(f"{k}: {st} without evidence_ref (calc book section / sheet / file)")
            if register is not None:
                for cid in ids:
                    if cid not in register:
                        errors.append(f"{k}: calc_id {cid} is not in the calc register")
                    else:
                        v = (register[cid].get("verdict") or "").strip().upper()
                        if st == "PASS" and v and v != "PASS":
                            errors.append(f"{k}: coverage says PASS but register {cid} verdict is {v}")
            if (r.get("blind_checked") or "").strip().upper() not in ("Y", "YES", "N", "NO", "N/A", ""):
                warnings.append(f"{k}: blind_checked should be Y / N / N/A")
            if st == "FAIL":
                warnings.append(f"{k}: FAIL — must close by design change or valid alternative solution; cannot be waived")
        elif st == "NOT CALCULATED":
            if not (r.get("reason") or "").strip():
                errors.append(f"{k}: NOT CALCULATED without a reason (why it could not be done)")
            if not (r.get("missing_input") or "").strip():
                errors.append(f"{k}: NOT CALCULATED without missing_input (what is needed to do it)")
            if not (r.get("owner") or "").strip():
                errors.append(f"{k}: NOT CALCULATED without an owner")
            eg = (r.get("expiry_gate") or "").strip()
            if not eg:
                errors.append(f"{k}: NOT CALCULATED without an expiry_gate")
            elif cg is not None and gate_index(eg) is not None and gate_index(eg) <= cg:
                errors.append(f"{k}: NOT CALCULATED with expiry_gate {eg} at or before the current gate {current_gate} — overdue, blocks the gate")
            if stage and stage_index(r["stage_due"]) < stage_index(stage):
                warnings.append(f"{k}: due at {r['stage_due']}, still NOT CALCULATED at {stage.upper()}")
        elif st == "TBC":
            if not (r.get("reason") or "").strip():
                errors.append(f"{k}: TBC without a reason (which input is unresolved)")
            if not (r.get("owner") or "").strip():
                errors.append(f"{k}: TBC without an owner")
            eg = (r.get("expiry_gate") or "").strip()
            if not eg:
                errors.append(f"{k}: TBC without an expiry_gate")
            elif cg is not None and gate_index(eg) is not None and gate_index(eg) <= cg:
                errors.append(f"{k}: TBC with expiry_gate {eg} at or before the current gate — blocks the gate")
        elif st == "N/A":
            reason = (r.get("reason") or "").strip()
            if len(reason) < 15:
                errors.append(f"{k}: N/A needs a specific reason (≥ 15 characters: which condition makes it inapplicable)")
            if not (r.get("accepted_by") or "").strip():
                errors.append(f"{k}: N/A without accepted_by (a person accepts every N/A)")
    return errors, warnings, counts


def load_register(path: str | None) -> dict[str, dict] | None:
    if not path:
        return None
    rows = read_csv(path, ["calc_id"])
    return {r["calc_id"].strip(): r for r in rows}


def print_summary(rows: list[dict]) -> None:
    disc = sorted({r["discipline"] for r in rows})
    cols = STATUSES + ["BLANK"]
    print(f"{'discipline':<12}{'rows':>6}" + "".join(f"{c:>16}" for c in cols))
    for d in disc:
        sub = [r for r in rows if r["discipline"] == d]
        c = Counter((r.get("status") or "BLANK").strip().upper() or "BLANK" for r in sub)
        print(f"{d:<12}{len(sub):>6}" + "".join(f"{c.get(s, 0):>16}" for s in cols))
    c = Counter((r.get("status") or "BLANK").strip().upper() or "BLANK" for r in rows)
    print(f"{'TOTAL':<12}{len(rows):>6}" + "".join(f"{c.get(s, 0):>16}" for s in cols))


def cmd_check(a: argparse.Namespace) -> int:
    rows = read_csv(a.file, COVERAGE_COLUMNS)
    master = load_master(a.master) if (a.stage or a.master) else None
    register = load_register(a.register)
    errors, warnings, _ = check_rows(rows, a.stage, master, register, parse_disciplines(a.disciplines))
    print_summary(rows)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    n_err = len(errors) + (len(warnings) if a.strict else 0)
    print(f"{len(errors)} errors, {len(warnings)} warnings — {'FAIL' if n_err else 'PASS'}")
    return 1 if n_err else 0


def cmd_summary(a: argparse.Namespace) -> int:
    rows = read_csv(a.file, COVERAGE_COLUMNS)
    print_summary(rows)
    return 0


# ----------------------------------------------------------------------------- html

CSS = """
<style>
.wscov{font-family:Arial,Helvetica,'Noto Sans','Noto Sans SC','Microsoft YaHei',sans-serif;font-size:8pt;line-height:1.3;color:#000}
.wscov h1{font-size:13pt;margin:0 0 1mm 0}.wscov h2{font-size:10pt;margin:5mm 0 2mm 0;color:#7030A0;border-bottom:1px solid #7030A0}
.wscov h3{font-size:9pt;margin:3mm 0 1mm 0}
.wscov p{margin:1mm 0}.wscov .rules{border:1px solid #7030A0;background:#f3eefa;padding:2mm 3mm;margin:2mm 0 4mm 0}
.wscov table{border-collapse:collapse;width:100%;table-layout:fixed;margin-bottom:3mm}
.wscov th,.wscov td{border:0.3mm solid #000;padding:1mm 1.5mm;vertical-align:top;text-align:left;word-wrap:break-word}
.wscov th{background:#E6E6E6;font-size:8pt}.wscov td.k{font-family:ui-monospace,Consolas,monospace;font-size:7.5pt}
.wscov td.st{font-weight:bold;text-align:center}.wscov td.cn{font-family:'Noto Sans SC','Microsoft YaHei',Arial,sans-serif;color:#333}
.wscov td.blank{background:#fff8e1}.wscov .PASS{background:#e6f4ea}.wscov .FAIL{background:#fdecea}.wscov .NA{background:#eee}
.wscov .NOTCALC{background:#fff3d6}.wscov .TBC{background:#eaf3ff}.wscov .small{font-size:7pt;color:#333}
.wscov .legend span{display:inline-block;padding:0 2mm;border:0.25mm solid #000;margin-right:2mm}
</style>
"""

RULES_EN = (
    "How this page is used. At every gate the AI must return this table with a status in every row for the "
    "rows due at or before the stage: PASS (done, meets the criterion — give calc IDs and where the evidence is); "
    "FAIL (done, does not meet it — the PD cannot waive it; say what design change or alternative solution closes it); "
    "NOT CALCULATED (not done — say why, which input is missing, who owns it and the gate by which it expires); "
    "TBC (input unresolved — owner and expiry gate); N/A (demonstrably inapplicable — the condition that makes it so, "
    "and the person who accepted that). A blank cell is a defect. 'To be verified manually', 'per manufacturer' or "
    "'standard practice' are not statuses. Rows are cumulative: an S3 row stays on the S6 table until it is PASS or N/A."
)
RULES_ZH = (
    "用法：每个 gate，AI 必须把这张表交回来，到期（stage_due 早于或等于本阶段）的每一行都要有状态：PASS（做了、满足——给 calc ID 和证据位置）；"
    "FAIL（做了、不满足——PD 不能豁免，写清用什么设计修改或替代论证关闭）；NOT CALCULATED（没做——写清原因、缺什么输入、责任人、到期 gate）；"
    "TBC（输入待定——责任人、到期 gate）；N/A（确实不适用——写清哪个条件导致不适用，以及谁接受）。空格算缺陷。"
    "“人工核对”“按厂家”“常规做法”都不是状态。表是累积的：S3 的行在 S6 的表里继续出现，直到 PASS 或 N/A。"
)


def _cls(status: str) -> str:
    s = (status or "").strip().upper()
    return {"PASS": "PASS", "FAIL": "FAIL", "N/A": "NA", "NOT CALCULATED": "NOTCALC", "TBC": "TBC"}.get(s, "blank")


def render_blank(master_rows: list[dict], stage: str, fragment: bool, title: str | None) -> str:
    title = title or f"CALCULATION TEMPLATES — MANDATORY CALCULATION LIST ({'ALL STAGES' if stage.upper() == 'ALL' else 'DUE BY ' + stage.upper()})"
    parts = []
    if not fragment:
        parts.append("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><title>" + html.escape(title) + "</title>" + CSS + "</head><body>")
    parts.append("<div class='page wscov'>" + (CSS if fragment else ""))
    parts.append(f"<h1>{html.escape(title)} &nbsp;·&nbsp; 计算书模板：必须完成的计算清单</h1>")
    parts.append("<div class='rules'><p><b>EN</b> " + html.escape(RULES_EN) + "</p><p class='cn'><b>中文</b> " + html.escape(RULES_ZH) + "</p>"
                 "<p class='small'>Master list: <code>templates/calc-templates/calc-master-list.csv</code> · generate the stage table with "
                 "<code>python3 scripts/calc_coverage.py init --stage S6</code> · validate with <code>check</code> · each PASS / FAIL row is one page in the "
                 "calc book (<code>templates/calc-templates/calc-page.md</code>). Rows are the company minimum; add project rows, never delete.</p></div>")
    parts.append("<p class='legend small'><span>PASS</span><span>FAIL</span><span>NOT CALCULATED</span><span>TBC</span><span>N/A</span> "
                 "Columns to fill: status · calc IDs · result vs limit · reason / missing input · owner · expiry gate · evidence ref · blind-checked Y/N · date</p>")
    disc_order = ["MECH", "ELEC", "HYD", "FIRE", "STR", "FAC", "ACU", "THM", "VT", "CIV", "ARC", "TRF", "CON"]
    names = {"MECH": "Mechanical / HVAC 暖通", "ELEC": "Electrical 电气", "HYD": "Hydraulic / plumbing 给排水", "FIRE": "Fire — wet, dry, engineering 消防",
             "STR": "Structure 结构", "FAC": "Façade & roof 幕墙与屋面", "ACU": "Acoustics 声学", "THM": "Thermal / ESD 热工与 ESD", "VT": "Vertical transport 垂直交通",
             "CIV": "Civil 场地土建", "ARC": "Architecture / ID compliance 建筑与室内合规", "TRF": "Traffic 交通", "CON": "Construction planning 施工组织"}
    groups: "OrderedDict[str, list[dict]]" = OrderedDict()
    for d in disc_order:
        groups[d] = [r for r in master_rows if r["discipline"] == d]
    for d, rows in groups.items():
        if not rows:
            continue
        parts.append(f"<h2>{html.escape(names.get(d, d))} — {len(rows)} calculations</h2>")
        parts.append("<table><colgroup><col style='width:9%'><col style='width:23%'><col style='width:5%'><col style='width:15%'><col style='width:14%'>"
                     "<col style='width:12%'><col style='width:5%'><col style='width:17%'></colgroup>"
                     "<thead><tr><th>Calc key</th><th>Calculation 计算</th><th>Due</th><th>Inputs needed 输入</th><th>Method / standard 方法 / 标准</th>"
                     "<th>Acceptance 通过条件</th><th>Status 状态</th><th>Calc IDs · result vs limit · reason / missing input · owner · expiry · evidence</th></tr></thead><tbody>")
        for r in rows:
            parts.append("<tr>"
                         f"<td class='k'>{html.escape(r['calc_key'])}</td>"
                         f"<td>{html.escape(r['title_en'])}<br><span class='cn small'>{html.escape(r['title_zh'])}</span>"
                         f"<br><span class='small'>N/A only if: {html.escape(r['na_condition'])} · ref {html.escape(r['deliverable_ref'])}</span></td>"
                         f"<td>{html.escape(r['stage_due'])}</td>"
                         f"<td class='small'>{html.escape(r['inputs'])}</td>"
                         f"<td class='small'>{html.escape(r['method_standard'])}</td>"
                         f"<td class='small'>{html.escape(r['acceptance'])}</td>"
                         "<td class='st blank'>&nbsp;</td><td class='blank'>&nbsp;</td></tr>")
        parts.append("</tbody></table>")
    parts.append("</div>")
    if not fragment:
        parts.append("</body></html>")
    return "\n".join(parts)


def render_coverage(rows: list[dict], title: str | None, master: list[dict] | None) -> str:
    title = title or "CALCULATION COVERAGE"
    mz = {m["calc_key"]: m for m in (master or [])}
    parts = ["<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><title>" + html.escape(title) + "</title>" + CSS + "</head><body><div class='page wscov'>"]
    parts.append(f"<h1>{html.escape(title)}</h1>")
    c = Counter((r.get("status") or "BLANK").strip().upper() or "BLANK" for r in rows)
    parts.append("<p class='legend small'>" + " ".join(f"<span class='{_cls(s)}'>{s}: {c.get(s, 0)}</span>" for s in STATUSES + ["BLANK"]) + f" total {len(rows)}</p>")
    for d in sorted({r["discipline"] for r in rows}):
        sub = [r for r in rows if r["discipline"] == d]
        parts.append(f"<h2>{html.escape(d)} — {len(sub)} rows</h2>")
        parts.append("<table><colgroup><col style='width:9%'><col style='width:20%'><col style='width:4%'><col style='width:8%'><col style='width:9%'>"
                     "<col style='width:14%'><col style='width:14%'><col style='width:7%'><col style='width:5%'><col style='width:10%'></colgroup>"
                     "<thead><tr><th>Calc key</th><th>Calculation</th><th>Due</th><th>Status</th><th>Calc IDs</th><th>Result vs limit</th>"
                     "<th>Reason / missing input</th><th>Owner</th><th>Expiry</th><th>Evidence · blind · date</th></tr></thead><tbody>")
        for r in sub:
            st = (r.get("status") or "").strip().upper()
            zh = mz.get(r["calc_key"], {}).get("title_zh", "")
            parts.append("<tr>"
                         f"<td class='k'>{html.escape(r['calc_key'])}</td>"
                         f"<td>{html.escape(r['title_en'])}" + (f"<br><span class='cn small'>{html.escape(zh)}</span>" if zh else "") + "</td>"
                         f"<td>{html.escape(r['stage_due'])}</td>"
                         f"<td class='st {_cls(st)}'>{html.escape(st or '—')}</td>"
                         f"<td class='k'>{html.escape(r.get('calc_ids', ''))}</td>"
                         f"<td class='small'>{html.escape(r.get('result_summary', ''))}</td>"
                         f"<td class='small'>{html.escape(r.get('reason', ''))}" + (f"<br><b>needs:</b> {html.escape(r['missing_input'])}" if r.get('missing_input') else "") +
                         (f"<br><b>accepted by:</b> {html.escape(r['accepted_by'])}" if r.get('accepted_by') else "") + "</td>"
                         f"<td class='small'>{html.escape(r.get('owner', ''))}</td>"
                         f"<td>{html.escape(r.get('expiry_gate', ''))}</td>"
                         f"<td class='small'>{html.escape(r.get('evidence_ref', ''))} · blind {html.escape(r.get('blind_checked', '') or '—')} · {html.escape(r.get('date', ''))}</td></tr>")
        parts.append("</tbody></table>")
    parts.append("</div></body></html>")
    return "\n".join(parts)


def cmd_html(a: argparse.Namespace) -> int:
    rows = read_csv(a.file, COVERAGE_COLUMNS)
    master = load_master(a.master) if os.path.exists(a.master or DEFAULT_MASTER) else None
    out = render_coverage(rows, a.title, master)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"wrote {a.out} ({len(rows)} rows)")
    return 0


def cmd_blank(a: argparse.Namespace) -> int:
    master = load_master(a.master)
    rows = select_master(master, a.stage, parse_disciplines(a.disciplines))
    out = render_blank(rows, a.stage, a.fragment, a.title)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"wrote {a.out} ({len(rows)} template rows, {'fragment' if a.fragment else 'standalone'})")
    return 0


# ----------------------------------------------------------------------------- selftest

def cmd_selftest(a: argparse.Namespace) -> int:
    results = []

    def ok(name, cond):
        results.append((name, bool(cond)))
        print(("PASS " if cond else "FAIL ") + name)

    master = load_master(None)
    ok("master list loads", len(master) > 100)
    with tempfile.TemporaryDirectory() as d:
        cov3 = os.path.join(d, "coverage-S3.csv")
        ns = argparse.Namespace(stage="S3", disciplines="MECH,HYD", master=None, carry=None, out=cov3)
        cmd_init(ns)
        rows = read_csv(cov3, COVERAGE_COLUMNS)
        ok("init S3 MECH,HYD only due ≤ S3", all(stage_index(r["stage_due"]) <= 3 and r["discipline"] in ("MECH", "HYD") for r in rows) and rows)
        errors, warnings, _ = check_rows(rows, "S3", master, None, ["MECH", "HYD"])
        ok("blank rows are errors", len(errors) == len(rows))
        # fill some rows
        for r in rows:
            if r["calc_key"] == "MECH-LOAD-01":
                r.update(status="PASS", calc_ids="M-001", result_summary="peak 412 kW vs plant 450 kW", evidence_ref="calc book S3 §M-001", blind_checked="Y", date="2026-09-15")
            elif r["calc_key"] == "HYD-CW-02":
                r.update(status="NOT CALCULATED", reason="authority letter not received", missing_input="Sydney Water pressure / flow letter", owner="PM", expiry_gate="G4a")
            elif r["calc_key"] == "MECH-SMK-01":
                r.update(status="N/A", reason="rise in storeys 2, effective height 7 m: pressurisation not required per NCC E2 (digest r-xxx)", accepted_by="PD")
            elif r["calc_key"] == "HYD-HW-01":
                r.update(status="PASS", calc_ids="", result_summary="x", evidence_ref="y")
            elif r["calc_key"] == "HYD-SAN-03":
                r.update(status="TBC", reason="connection point undecided", owner="PM", expiry_gate="G1")
            else:
                r.update(status="N/A", reason="villa without this system — see brief section 4", accepted_by="PD")
        errors, warnings, _ = check_rows(rows, "S3", master, None, ["MECH", "HYD"])
        ok("PASS without calc_ids is an error", any("HYD-HW-01" in e and "calc_ids" in e for e in errors))
        ok("TBC with expiry at/before current gate is an error", any("HYD-SAN-03" in e for e in errors))
        ok("valid NOT CALCULATED accepted", not any("HYD-CW-02" in e for e in errors))
        ok("valid N/A accepted", not any("MECH-SMK-01" in e for e in errors))
        # register cross-check
        reg = {"M-001": {"calc_id": "M-001", "verdict": "FAIL"}}
        errors2, _, _ = check_rows(rows, "S3", master, reg, ["MECH", "HYD"])
        ok("register verdict mismatch caught", any("MECH-LOAD-01" in e and "register" in e for e in errors2))
        write_csv(cov3, rows, COVERAGE_COLUMNS)
        cov6 = os.path.join(d, "coverage-S6.csv")
        cmd_init(argparse.Namespace(stage="S6", disciplines="MECH,HYD", master=None, carry=cov3, out=cov6))
        rows6 = read_csv(cov6, COVERAGE_COLUMNS)
        carried = {r["calc_key"]: r for r in rows6}
        ok("carry copies earlier answers", carried["MECH-LOAD-01"]["status"] == "PASS" and carried["HYD-CW-02"]["status"] == "NOT CALCULATED")
        ok("S6 file has more rows than S3", len(rows6) > len(rows))
        errors6, warnings6, _ = check_rows(rows6, "S6", master, None, ["MECH", "HYD"])
        ok("carried NOT CALCULATED expiring at G4a is overdue at G4", any("HYD-CW-02" in e and "overdue" in e for e in errors6))
        # missing row detection
        rows6b = [r for r in rows6 if r["calc_key"] != "MECH-DUCT-01"]
        errors6b, _, _ = check_rows(rows6b, "S6", master, None, ["MECH", "HYD"])
        ok("missing master row detected", any("MECH-DUCT-01" in e and "missing" in e for e in errors6b))
        # html renders
        frag = render_blank(select_master(master, "ALL", None), "ALL", True, None)
        ok("blank fragment renders all rows", frag.count("<tr>") >= len(master) and "<html" not in frag)
        full = render_coverage(rows6, "t", master)
        ok("coverage html renders", full.count("<tr>") >= len(rows6))
    n_fail = sum(1 for _, c in results if not c)
    print(f"{len(results) - n_fail} passed, {n_fail} failed")
    return 1 if n_fail else 0


# ----------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="write the coverage file for a stage from the master list")
    s.add_argument("--stage", required=True)
    s.add_argument("--disciplines", help="comma list, e.g. MECH,ELEC (default: all)")
    s.add_argument("--master", help=f"master list CSV (default {os.path.relpath(DEFAULT_MASTER)})")
    s.add_argument("--carry", help="earlier coverage file whose answers are copied across")
    s.add_argument("--out", help="output CSV (default calcs/coverage-<STAGE>.csv)")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("check", help="validate a coverage file; exit 1 on errors")
    s.add_argument("file")
    s.add_argument("--stage", help="current stage (enables master completeness and expiry checks)")
    s.add_argument("--disciplines")
    s.add_argument("--master")
    s.add_argument("--register", help="calc register CSV to cross-check calc_ids and verdicts")
    s.add_argument("--strict", action="store_true", help="warnings are errors")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("summary", help="counts per discipline and status")
    s.add_argument("file")
    s.set_defaults(fn=cmd_summary)

    s = sub.add_parser("html", help="render a coverage file as HTML")
    s.add_argument("file")
    s.add_argument("--out", required=True)
    s.add_argument("--title")
    s.add_argument("--master")
    s.set_defaults(fn=cmd_html)

    s = sub.add_parser("blank", help="render the blank template tables (forcing page)")
    s.add_argument("--stage", default="ALL")
    s.add_argument("--disciplines")
    s.add_argument("--master")
    s.add_argument("--out", required=True)
    s.add_argument("--fragment", action="store_true", help="inner HTML only, for embedding")
    s.add_argument("--title")
    s.set_defaults(fn=cmd_blank)

    s = sub.add_parser("selftest", help="run built-in tests")
    s.set_defaults(fn=cmd_selftest)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
