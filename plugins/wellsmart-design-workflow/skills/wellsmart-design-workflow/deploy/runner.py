#!/usr/bin/env python3
"""
runner.py — the company-server loop. One process, no API for employees, no logins.

The shared Drive folder is the connection. Each project is a folder under PROJECTS_ROOT (mounted from
Google Drive with rclone, or any synced share). Employees' Claude sessions write ordinary files into the
project folder; this loop notices them and does the work; results are written back as ordinary files
and appear on the employee's computer through the same sync, and on the project book website.

What it does, every POLL seconds, for every project folder:
  1. reviews/<task>/REQUEST.json          → freeze a snapshot (server-side git), then scripts/peer_review.py:
                                             packet (pre-check = VALIDATING, freeze = FROZEN) → selfcheck (the
                                             blind packet holds nothing conclusive; review is never called if it
                                             fails) → review (REVIEWING → RESPONSE_REQUIRED / CLOSED /
                                             HUMAN_REQUIRED) → respond when RESPONSE_REQUIRED; the request is
                                             renamed REQUEST.done.json, or REQUEST.error.txt with the pre-check
                                             list when the packet was blocked. The request may carry "stream",
                                             "full_share" and "allow_fail" (a reason, recorded on the round).
  2. drawings/*.html changed               → run the annotation / QA checker, write drawings/qa/<sheet>.json
                                             and drawings/qa/SUMMARY.md
  3. anything changed                      → rebuild the project book into SITE_ROOT/<project>/
                                             (gen_book.py from the library if present, else the built-in index),
                                             run pagefind if installed
  4. STATUS.md in the project root          → one page a person can open to see what the server did last

Environment (see .env.example): PROJECTS_ROOT, SITE_ROOT, GIT_ROOT, SKILL_ROOT, POLL, WS_REVIEWER_PROVIDER,
WS_REVIEWER_MODEL, OPENAI_API_KEY / GEMINI_API_KEY, WS_BOOK_BASE_URL.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

PROJECTS_ROOT = Path(os.environ.get("PROJECTS_ROOT", "/srv/projects"))
SITE_ROOT = Path(os.environ.get("SITE_ROOT", "/srv/site"))
GIT_ROOT = Path(os.environ.get("GIT_ROOT", "/srv/git"))
SKILL_ROOT = Path(os.environ.get("SKILL_ROOT", "/opt/skill"))
LIBRARY_ROOT = Path(os.environ.get("LIBRARY_ROOT", "/opt/library"))
POLL = int(os.environ.get("POLL", "30"))
BASE_URL = os.environ.get("WS_BOOK_BASE_URL", "").rstrip("/")
SCRIPTS = SKILL_ROOT / "scripts"
STATE_FILE = Path(os.environ.get("RUNNER_STATE", "/srv/runner-state.json"))
PRIVATE = {p.strip() for p in os.environ.get("PRIVATE_PROJECTS", "").split(",") if p.strip()}   # no public book for these


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(*a):
    print(now(), *a, flush=True)


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"projects": {}}


def save_state(st: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(st, indent=1))


def projects() -> list[Path]:
    if not PROJECTS_ROOT.exists():
        return []
    return sorted(p for p in PROJECTS_ROOT.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


SERVER_WRITTEN = {"STATUS.md"}


def tree_signature(root: Path, skip=("reviews", ".git", "site", "_book", "qa")) -> str:
    """Cheap change detector: hash of (path, mtime, size) for every file, skipping server-written folders."""
    h = hashlib.sha1()
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(s in p.parts for s in skip) and p.name not in SERVER_WRITTEN:
            try:
                st = p.stat()
            except OSError:
                continue
            h.update(f"{p.relative_to(root)}|{int(st.st_mtime)}|{st.st_size}".encode())
    return h.hexdigest()


# ----------------------------------------------------------------------------- git snapshot (server-side, invisible to employees)
def git_env(project: Path) -> dict:
    gd = GIT_ROOT / project.name
    env = dict(os.environ, GIT_DIR=str(gd), GIT_WORK_TREE=str(project))
    if not gd.exists():
        gd.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "--bare", str(gd)], check=True)
        subprocess.run(["git", "config", "core.bare", "false"], env=env, check=True)
        subprocess.run(["git", "config", "user.email", "runner@wellsmart"], env=env, check=True)
        subprocess.run(["git", "config", "user.name", "runner"], env=env, check=True)
    return env


def snapshot(project: Path, message: str) -> str:
    env = git_env(project)
    excl = GIT_ROOT / project.name / "info" / "exclude"
    excl.parent.mkdir(parents=True, exist_ok=True)
    excl.write_text("reviews/*/round-*/packet/\nreviews/*/round-*/calls/\n_book/\n.DS_Store\n")
    subprocess.run(["git", "add", "-A"], env=env, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message, "--allow-empty"], env=env, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], env=env, text=True).strip()


# ----------------------------------------------------------------------------- 1 review requests
OLD_STATES = {"open": "REQUESTED", "awaiting_review": "FROZEN", "awaiting_designer": "RESPONSE_REQUIRED",
              "designer_revising": "RESPONSE_REQUIRED", "completed": "CLOSED", "human_required": "HUMAN_REQUIRED"}


def review_state(task_dir: Path) -> dict:
    """state.json as written by peer_review.py v2 (field `state`); a v1 file's `status` is mapped to the v2 name."""
    try:
        st = json.loads((task_dir / "state.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    if "state" not in st:
        st["state"] = OLD_STATES.get(st.get("status", ""), "REQUESTED")
    return st


def precheck_report(task_dir: Path, with_table: bool) -> str:
    """The pre-check result of the round that was being built (its folder has precheck.json but no packet):
    the hard-FAIL list and what to do next, plus the full table when the caller did not already print it."""
    for rd in sorted(task_dir.glob("round-*"), key=lambda p: int(p.name.split("-")[1]), reverse=True):
        pc = rd / "precheck.json"
        if pc.exists() and not (rd / "packet").exists():
            try:
                rec = json.loads(pc.read_text(encoding="utf-8"))
            except Exception:
                return f"{pc} unreadable"
            lines = [f"pre-check {rd.name}: {'BLOCKED' if rec.get('blocked') else 'passed'} — record {pc.relative_to(task_dir.parent.parent)}"]
            if with_table:
                lines.append("check | script_result | detail | technical_judgement")
                lines += [f"{i['check']} | {i['script_result']} | {i['detail']} | {i['technical_judgement']}" for i in rec.get("items", [])]
            if rec.get("hard_fail"):
                lines.append("hard FAIL: " + "; ".join(rec["hard_fail"]))
                lines.append("next: fix the files and drop a new REQUEST.json, or add \"allow_fail\": \"<reason>\" to the request "
                             "(recorded on the round and shown to the reviewer; a missing required file cannot be overridden)")
            return "\n".join(lines)
    return ""


class Blocked(RuntimeError):
    """The pre-check or the selfcheck refused the round; recorded, not a crash."""


def handle_requests(project: Path, status: list[str]) -> bool:
    did = False
    for req in sorted(project.glob("reviews/*/REQUEST.json")):
        task_dir = req.parent
        task = task_dir.name
        try:
            body = json.loads(req.read_text(encoding="utf-8"))
        except Exception as e:
            req.rename(task_dir / "REQUEST.error.txt")
            (task_dir / "REQUEST.error.txt").write_text(f"{now()} bad JSON: {e}\n")
            continue
        stream = body.get("stream")          # optional: peer_review.py derives it from the task (G4-MECH → MECH, else ALL)
        log(f"[{project.name}] review request {task} stream={stream or '(from task)'}")
        pr = [sys.executable, str(SCRIPTS / "peer_review.py")]
        try:
            commit = snapshot(project, f"snapshot for {task} ({body.get('note', '')})")
            env = git_env(project)
            env.setdefault("WS_REVIEWER_PROVIDER", os.environ.get("WS_REVIEWER_PROVIDER", "openai"))
            common = dict(cwd=str(project), env=env, text=True, capture_output=True)
            packet_args = ["packet", "--task", task] + (["--stream", stream] if stream else []) \
                + (["--full-share", str(body["full_share"])] if body.get("full_share") is not None else []) \
                + (["--allow-fail", str(body["allow_fail"])] if body.get("allow_fail") else [])
            r1 = subprocess.run(pr + packet_args, **common)
            if r1.returncode:
                out = (r1.stdout + r1.stderr).strip()
                raise Blocked("packet not frozen (state VALIDATING):\n" + out + "\n\n"
                              + precheck_report(task_dir, with_table="pre-check round" not in out))
            r_sc = subprocess.run(pr + ["selfcheck", "--task", task], **common)
            if r_sc.returncode:
                raise Blocked("selfcheck FAILED — the blind packet is not clean, review NOT called:\n"
                              + (r_sc.stdout + r_sc.stderr).strip())
            r2 = subprocess.run(pr + ["review", "--task", task], **common)
            state = review_state(task_dir)
            if r2.returncode and state.get("state") != "HUMAN_REQUIRED":
                raise RuntimeError("review: " + (r2.stdout + r2.stderr).strip())
            if state.get("state") == "RESPONSE_REQUIRED":
                subprocess.run(pr + ["respond", "--task", task], **common)
            result = {"handled": now(), "commit": commit, "packet": r1.stdout.strip(), "selfcheck": r_sc.stdout.strip(),
                      "review": (r2.stdout + r2.stderr).strip(), "state": state.get("state"), "reason": state.get("reason"),
                      "verdict": state.get("last_verdict"), "round": state.get("rounds"), "request_id": state.get("request_id")}
            (task_dir / "REQUEST.done.json").write_text(json.dumps({**body, **result}, indent=1, ensure_ascii=False), encoding="utf-8")
            req.unlink()
            status.append(f"- review {task}: round {state.get('rounds')} → **{state.get('last_verdict') or state.get('state')}** "
                          f"(state {state.get('state')}" + (f": {state.get('reason')}" if state.get("reason") else "") + ")")
            log(f"[{project.name}] {task}: {state.get('last_verdict')} ({state.get('state')})")
        except Blocked as e:                 # an expected outcome of the pre-check or selfcheck: no traceback
            (task_dir / "REQUEST.error.txt").write_text(f"{now()}\n{e}\n", encoding="utf-8")
            req.unlink(missing_ok=True)
            status.append(f"- review {task}: BLOCKED — see reviews/{task}/REQUEST.error.txt (state {review_state(task_dir).get('state')})")
            log(f"[{project.name}] {task} blocked: {str(e).splitlines()[0]}")
        except Exception as e:
            (task_dir / "REQUEST.error.txt").write_text(f"{now()}\n{e}\n{traceback.format_exc()}", encoding="utf-8")
            req.unlink(missing_ok=True)
            status.append(f"- review {task}: ERROR — see reviews/{task}/REQUEST.error.txt (state {review_state(task_dir).get('state')})")
            log(f"[{project.name}] {task} error: {e}")
        did = True
    return did


# ----------------------------------------------------------------------------- 2 sheet QA
def check_sheets(project: Path, st: dict, status: list[str]) -> bool:
    qa_dir = project / "drawings" / "qa"
    seen = st.setdefault("sheets", {})
    changed = []
    for sheet in sorted(project.glob("drawings/*.html")):
        sig = f"{int(sheet.stat().st_mtime)}|{sheet.stat().st_size}"
        if seen.get(sheet.name) == sig:
            continue
        qa_dir.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([sys.executable, str(SCRIPTS / "annotate.py"), "check", str(sheet)], text=True, capture_output=True)
        out = r.stdout.strip() or json.dumps({"error": r.stderr.strip()[-500:]})
        (qa_dir / (sheet.stem + ".json")).write_text(out, encoding="utf-8")
        seen[sheet.name] = sig
        try:
            rep = json.loads(out)
            changed.append((sheet.stem, rep))
        except Exception:
            changed.append((sheet.stem, {"error": "unreadable"}))
    if changed:
        lines = ["# Sheet QA summary", f"updated {now()}", "", "| sheet | pass | crossings | through objects | over dims | text/line | text/text | outside | columns |", "|---|---|---|---|---|---|---|---|---|"]
        for stem, rep in sorted(((s.stem, json.loads((qa_dir / (s.stem + '.json')).read_text())) for s in project.glob("drawings/*.html") if (qa_dir / (s.stem + ".json")).exists()), key=lambda t: t[0]):
            g = lambda k: rep.get(k, "—")
            lines.append(f"| {stem} | {'PASS' if rep.get('pass') else 'FAIL'} | {g('leader_crossings')} | {g('leader_through_geometry')} | {g('leader_over_dimension')} | {g('text_over_line')} | {g('text_over_text')} | {g('outside_border')} | {g('label_columns')} |")
        (qa_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        fails = [s for s, rep in changed if not rep.get("pass")]
        status.append(f"- sheet QA: {len(changed)} checked, {len(fails)} failing" + (f" ({', '.join(fails[:8])})" if fails else ""))
        return True
    return False


# ----------------------------------------------------------------------------- 3 project book
def build_book(project: Path, status: list[str]) -> None:
    out = SITE_ROOT / project.name
    gen = LIBRARY_ROOT / "templates" / "gen_book.py"
    if gen.exists():
        r = subprocess.run([sys.executable, str(gen), "--project", str(project), "--out", str(out)], text=True, capture_output=True)
        if r.returncode:
            status.append(f"- book: gen_book.py failed — {r.stderr.strip()[-300:]}")
            return
    else:
        builtin_book(project, out)
    if shutil.which("pagefind"):
        subprocess.run(["pagefind", "--site", str(out)], text=True, capture_output=True)
    status.append(f"- book rebuilt → {BASE_URL}/{project.name}/" if BASE_URL else f"- book rebuilt → {out}")


def builtin_book(project: Path, out: Path) -> None:
    """Minimal book until the library's gen_book.py exists: copies the HTML deliverables and writes the index,
    llms.txt and index.json — one URL per sheet, calc, decision and review round."""
    out.mkdir(parents=True, exist_ok=True)
    entries = {"drawings": [], "calcs": [], "reviews": [], "reports": [], "bq": [], "decisions": []}
    for sub in ("drawings", "calcs", "reports", "bq"):
        src = project / sub
        if not src.exists():
            continue
        dst = out / sub
        dst.mkdir(exist_ok=True)
        for f in sorted(src.glob("*")):
            if f.is_file() and f.suffix.lower() in (".html", ".csv", ".json", ".md", ".pdf"):
                shutil.copy2(f, dst / f.name)
                entries[sub].append(f.name)
        qa = src / "qa"
        if qa.exists():
            (dst / "qa").mkdir(exist_ok=True)
            for f in qa.glob("*"):
                shutil.copy2(f, dst / "qa" / f.name)
    dec = project / "decisions.md"
    if dec.exists():
        shutil.copy2(dec, out / "decisions.md")
        entries["decisions"].append("decisions.md")
    for rd in sorted(project.glob("reviews/*/round-*")):
        fb = rd / "feedback.json"
        if fb.exists():
            tdir = out / "reviews" / rd.parent.name
            tdir.mkdir(parents=True, exist_ok=True)
            data = json.loads(fb.read_text(encoding="utf-8"))
            page = tdir / (rd.name + ".html")
            rows = "".join(f"<tr><td>{f.get('issue_id','')}</td><td>{f.get('severity','')}</td><td>{esc(f.get('title',''))}</td><td>{esc(f.get('location',''))}</td><td>{esc(f.get('acceptance',''))}</td></tr>" for f in data.get("findings", []))
            checks = "".join(f"<tr><td>{k}</td><td>{'PASS' if v.get('passed') else 'FAIL'}</td><td>{esc(str(v.get('evidence','')))}</td></tr>" for k, v in data.get("checks", {}).items())
            cov = data.get("coverage", {})
            page.write_text(f"<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><title>{rd.parent.name} {rd.name}</title></head><body data-pagefind-body>"
                            f"<h1>{rd.parent.name} — {rd.name}: {data.get('verdict')}</h1><p>{esc(data.get('summary',''))}</p>"
                            f"<p>{esc(str(data.get('verdict_basis', '')))}</p>"
                            f"<p>commit {data.get('commit')} · packet {data.get('version_hash')} · blind answer {data.get('blind_answer_sha256')} · "
                            f"model {esc(str(data.get('models_used') or data.get('model')))} · {data.get('reviewed')} · "
                            f"sheets read in full {len(cov.get('sheets_read_in_full', []))}/{len(cov.get('sheets_in_scope', []))}</p>"
                            f"<h2>Checks</h2><table border=1>{checks}</table><h2>Findings</h2><table border=1><tr><th>id</th><th>severity</th><th>title</th><th>location</th><th>acceptance</th></tr>{rows}</table>"
                            f"<pre>{esc(json.dumps(data, indent=1, ensure_ascii=False))}</pre></body></html>", encoding="utf-8")
            entries["reviews"].append(f"{rd.parent.name}/{rd.name}.html")
    status_md = project / "STATUS.md"
    status_html = esc(status_md.read_text(encoding="utf-8")) if status_md.exists() else ""
    def section(title, sub, items):
        if not items:
            return ""
        return f"<h2>{title}</h2><ul>" + "".join(f"<li><a href=\"{sub}/{i}\">{i}</a></li>" for i in items) + "</ul>"
    body = (f"<h1>{esc(project.name)} — project book</h1><p>rebuilt {now()}</p>"
            + section("Drawings", "drawings", entries["drawings"]) + section("Calculations", "calcs", entries["calcs"])
            + section("Reviews", "reviews", entries["reviews"]) + section("Reports", "reports", entries["reports"])
            + section("BQ", "bq", entries["bq"]) + section("Decisions", ".", entries["decisions"])
            + f"<h2>Server status</h2><pre>{status_html}</pre>")
    (out / "index.html").write_text(f"<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><title>{esc(project.name)}</title></head><body data-pagefind-body>{body}</body></html>", encoding="utf-8")
    (out / "index.json").write_text(json.dumps({"project": project.name, "rebuilt": now(), **entries}, indent=1, ensure_ascii=False), encoding="utf-8")
    llms = [f"# {project.name}", "", f"> Well Smart project book. One URL per sheet, calc, decision and review round. Base: {BASE_URL}/{project.name}/", ""]
    for sub in ("drawings", "calcs", "reviews", "reports", "bq", "decisions"):
        for i in entries[sub]:
            llms.append(f"- [{i}]({BASE_URL}/{project.name}/{sub + '/' if sub != 'decisions' else ''}{i})")
    (out / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ----------------------------------------------------------------------------- main loop
def tick(st: dict) -> None:
    for project in projects():
        pst = st["projects"].setdefault(project.name, {})
        status: list[str] = []
        try:
            did_review = handle_requests(project, status)
            did_qa = check_sheets(project, pst, status)
            sig = tree_signature(project)
            if did_review or did_qa or pst.get("sig") != sig:
                if project.name in PRIVATE:
                    status.append("- book: skipped (PRIVATE_PROJECTS)")
                else:
                    build_book(project, status)
                pst["sig"] = sig
        except Exception as e:
            status.append(f"- runner error: {e}")
            log(f"[{project.name}] error: {e}")
        if status:
            prev = (project / "STATUS.md").read_text(encoding="utf-8").splitlines() if (project / "STATUS.md").exists() else []
            keep = [l for l in prev if l.startswith("- ")][:40]
            (project / "STATUS.md").write_text(f"# Server status — {project.name}\n\nlast run {now()}\n\n" + "\n".join(status + keep) + "\n", encoding="utf-8")
    save_state(st)


def main() -> None:
    log(f"runner start: projects={PROJECTS_ROOT} site={SITE_ROOT} poll={POLL}s provider={os.environ.get('WS_REVIEWER_PROVIDER', 'openai')}")
    st = load_state()
    once = "--once" in sys.argv
    while True:
        try:
            tick(st)
        except Exception as e:
            log("tick error:", e)
        if once:
            break
        time.sleep(POLL)


if __name__ == "__main__":
    main()
