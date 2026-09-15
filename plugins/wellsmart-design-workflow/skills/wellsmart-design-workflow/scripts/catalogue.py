#!/usr/bin/env python3
"""
catalogue.py — the Well Smart project knowledge base as one JSON file.

Pilot substitute for the ProjectBook catalogue API (references/project-knowledge-base.md,
references/hosting.md). It keeps `catalogue.json` at the project repository root and the
immutable originals under `kb/`, with the semantics the portal will apply, so every id
created here is imported unchanged when the portal is live. Standard library only.

Semantics
  ADD      new stable document_id (DOC-<DISCIPLINE>-<NNNN>) with its first revision R01
  REVISE   same document_id, new immutable revision (R02, R03 …) with parent revision,
           reason, impact list and SHA-256; older revisions untouched; no pointer moves
  ATTACH   evidence (endorsement, photo, approval, test, other) bound to one exact
           revision, optionally also to an asset_id; the main file is unchanged
  PUBLISH  the publish-effective transaction: current_by_use[<use>][<scope>][<document_id>]
           switches to one revision in ONE atomic write; the previous current for that
           use / scope is recorded as superseded with the timestamp; a publish event and
           a history row are appended; every other use and scope is untouched
  RELEASE  frozen project_release_id → the full list of document_id / revision_id / SHA-256
           current for a use (and scope), or named explicitly, written to
           kb/releases/<id>.json; files are referenced, never re-issued or copied

Rules enforced here
  - a revision key kb/originals/<document_id>/<revision_id>/<sha256>/<filename> is never
    overwritten and a revision_id is never reused; this script deletes nothing, ever
  - identical bytes for the same document_id → "already exists", no new revision
    (a new attachment relation on the existing revision is still allowed)
  - "current" is held per use (design / construction / operations) and per scope and is
    set only by `publish`, never by upload time; add / revise / attach move no pointer
  - a draft is published for operations only when --basis names an acceptance
  - an endorsement marks exactly the revision it was attached to; a later revision never
    inherits it; digital_signature_verified stays false unless --digital-verified is given;
    a package manifest that does not match the catalogue leaves the record "to be confirmed"
  - document states are separate facts: draft · AI-reviewed · consultant-endorsed ·
    construction-issued · accepted as-built. `states` lists every fact reached, `state`
    is the highest for tables. None of them is a technical PASS.
  - every mutating command writes the whole catalogue atomically (temp file + os.replace);
    --request-id makes a replayed command recognised and applied once

Commands
  add <file> --title T --discipline D [--doc-type TYPE] [--level L] [--system S] [--asset A]
      [--task T] [--reason R] [--impact "a,b"] [--identity KEY] [--note N] [--confirm-new]
  revise <document_id> <file> --reason R [--impact "a,b"] [--parent Rnn] [--task T] [--note N]
  attach <document_id> <revision_id> <file> --kind endorsement|photo|approval|test|other
      [--scope S] [--asset A] [--note N]
      for --kind endorsement: --signer X --firm F --discipline D --date YYYY-MM-DD
      [--conditions C] [--covering-letter REF] [--manifest manifest.json]
      [--received YYYY-MM-DD] [--digital-verified]
  publish <document_id> <revision_id> --use design|construction|operations [--scope S]
      --basis "<gate report / closed round / issue closure / construction issue / acceptance>"
      [--release-id ID] [--state AI-reviewed]
  release --id <project_release_id> [--use U] [--scope S] [--include DOC-X-0001:R02 …] [--note N]
  list [--use U] [--scope S] [--history] [--drafts]
  history <document_id>
  check
  export-index
  selftest

Every command takes --root (default .), --by (default env WS_USER, then the OS user) and,
for mutating commands, --request-id. Every command prints a one-line result first.

Layout under --root
  catalogue.json
  kb/originals/<document_id>/<revision_id>/<sha256>/<filename>      immutable originals
  kb/attachments/<document_id>/<revision_id>/<sha256>/<filename>    evidence originals
  kb/endorsements/<endorsement_id>.json                             endorsement records
  kb/releases/<project_release_id>.json                             frozen manifests
  kb/index.json, kb/llms.txt                                        derived (export-index)

Script success is a data-consistency result, never an engineering PASS.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import getpass
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

SCHEMA = "wsg.catalogue/1"
CATALOGUE = "catalogue.json"
USES = ("design", "construction", "operations")
KINDS = ("endorsement", "photo", "approval", "test", "other")
STATES = ("draft", "AI-reviewed", "consultant-endorsed", "construction-issued", "accepted as-built")
DEFAULT_SCOPE = "project"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DOC_ID = re.compile(r"^DOC-([A-Z0-9]+)-(\d{4,})$")
REV_ID = re.compile(r"^R(\d{2,})$")
AREA = {
    "drawing": "Drawings / Models", "sheet": "Drawings / Models", "ifc": "Drawings / Models",
    "model": "Drawings / Models", "calc": "Calculations", "calc-book": "Calculations",
    "dbr": "Calculations", "compliance-matrix": "Calculations", "brief": "Overview",
    "report": "Overview", "gate-report": "Overview", "spec": "Procurement / Construction",
    "bq": "Procurement / Construction", "rfq": "Procurement / Construction",
    "release-sheet": "Procurement / Construction", "construction-record": "Procurement / Construction",
    "as-built": "Assets / O&M", "om-manual": "Assets / O&M", "asset-register": "Assets / O&M",
    "commissioning": "Assets / O&M", "endorsement": "Endorsements / Approvals",
    "approval": "Endorsements / Approvals", "decision": "Issues / Decisions",
    "issue": "Issues / Decisions", "review-round": "Issues / Decisions",
}


class Refused(Exception):
    """A command that changed nothing because a rule or a check failed."""


# ----------------------------------------------------------------------------- helpers
def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def today() -> str:
    return dt.date.today().isoformat()


def sha256_of(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def norm_key(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def disc_code(d: str | None) -> str:
    code = re.sub(r"[^A-Z0-9]", "", (d or "").upper())
    if not code:
        raise Refused("--discipline must contain letters or digits (MECH, ELEC, HYD, FIRE, STR, ARCH, ID, VT, CIVIL, ESD, PM …)")
    return code


def split_list(values) -> list[str]:
    out: list[str] = []
    for v in values or []:
        for part in str(v).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def valid_date(s: str | None, flag: str) -> str:
    try:
        return dt.date.fromisoformat(s or "").isoformat()
    except ValueError:
        raise Refused(f"{flag} must be a date YYYY-MM-DD, got {s!r}") from None


def who(a) -> str:
    if getattr(a, "by", None):
        return a.by
    if os.environ.get("WS_USER"):
        return os.environ["WS_USER"]
    try:
        return getpass.getuser()
    except Exception:  # pragma: no cover - odd environments
        return "unknown"


def source_file(p: str) -> Path:
    src = Path(p)
    if not src.is_file():
        raise Refused(f"{p} is not a file")
    return src


def rev_seq(rev_id: str) -> int:
    m = REV_ID.match(rev_id or "")
    if not m:
        raise Refused(f"bad revision_id {rev_id!r} (expected R01, R02 …)")
    return int(m.group(1))


def state_rank(s: str) -> int:
    return STATES.index(s) if s in STATES else -1


def add_state(rev: dict, state: str) -> None:
    """Record a document-state fact on a revision; facts are never removed."""
    if state not in rev["states"]:
        rev["states"].append(state)
        rev["states"].sort(key=state_rank)
    rev["state"] = max(rev["states"], key=state_rank)


# ----------------------------------------------------------------------------- catalogue I/O
def cat_path(root: Path) -> Path:
    return root / CATALOGUE


def new_catalogue(project_id: str) -> dict:
    return {
        "schema": SCHEMA, "project_id": project_id, "created_at": now_iso(), "updated_at": None,
        "catalog_version": 0, "default_use": "design", "sequences": {},
        "documents": {}, "attachments": {}, "endorsements": {},
        "current_by_use": {u: {} for u in USES}, "releases": {}, "history": [], "events": [],
    }


def load(root: Path, create: bool = False, project: str | None = None) -> dict:
    p = cat_path(root)
    if p.exists():
        with p.open(encoding="utf-8") as f:
            cat = json.load(f)
        if cat.get("schema") != SCHEMA:
            raise Refused(f"{p} is not a {SCHEMA} catalogue")
        return cat
    if not create:
        raise Refused(f"no {CATALOGUE} at {root.resolve()} (a first `add` creates it)")
    return new_catalogue(project or root.resolve().name)


def save(root: Path, cat: dict) -> None:
    """Write the whole catalogue atomically: temp file in the same directory, fsync, os.replace."""
    cat["catalog_version"] = int(cat.get("catalog_version", 0)) + 1
    cat["updated_at"] = now_iso()
    root.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".catalogue-", suffix=".tmp", dir=root)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cat, f, indent=2, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, cat_path(root))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def store(root: Path, src: Path, rel_dir: str, sha: str) -> str:
    """Copy src under <root>/<rel_dir>/<src.name>. The key is created only if absent;
    identical bytes already at the key are reused; different bytes are refused."""
    rel = f"{rel_dir}/{src.name}"
    dest = root / rel_dir / src.name

    def same_bytes() -> bool:
        have, _ = sha256_of(dest)
        return have == sha

    if dest.exists():
        if same_bytes():
            return rel
        raise Refused(f"key {rel} already holds different bytes; an existing revision key is never overwritten")
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".incoming-", dir=dest.parent)
    os.close(fd)
    try:
        shutil.copyfile(src, tmp)
        got, _ = sha256_of(Path(tmp))
        if got != sha:
            raise Refused(f"{src.name} changed while it was being copied; nothing stored")
        try:
            os.link(tmp, dest)  # creates the key only when it does not exist yet
        except FileExistsError:
            if not same_bytes():
                raise Refused(f"key {rel} appeared with different bytes during the copy; refusing to overwrite") from None
        except OSError:  # hard links unsupported: exclusive create instead
            try:
                with open(dest, "xb") as out, open(tmp, "rb") as inp:
                    shutil.copyfileobj(inp, out)
            except FileExistsError:
                if not same_bytes():
                    raise Refused(f"key {rel} appeared with different bytes during the copy; refusing to overwrite") from None
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
    return rel


def write_new_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8") as f:
            f.write(text)
    except FileExistsError:
        raise Refused(f"{path} already exists; frozen files are never rewritten") from None


def next_seq(cat: dict, key: str) -> int:
    n = int(cat["sequences"].get(key, 0)) + 1
    cat["sequences"][key] = n
    return n


def replayed(cat: dict, request_id: str | None) -> dict | None:
    if not request_id:
        return None
    for e in cat["events"]:
        if e.get("request_id") == request_id:
            return e
    return None


def record_event(cat: dict, command: str, by: str, request_id: str | None, **details) -> str:
    eid = f"EVT-{next_seq(cat, 'EVT'):06d}"
    cat["events"].append({"event_id": eid, "at": now_iso(), "by": by, "command": command,
                          "request_id": request_id, **details})
    return eid


def get_doc(cat: dict, doc_id: str) -> dict:
    d = cat["documents"].get(doc_id)
    if not d:
        raise Refused(f"unknown document_id {doc_id}")
    return d


def get_rev(cat: dict, doc_id: str, rev_id: str) -> tuple[dict, dict]:
    d = get_doc(cat, doc_id)
    r = d["revisions"].get(rev_id)
    if not r:
        raise Refused(f"{doc_id} has no revision {rev_id} (has {', '.join(sorted(d['revisions'], key=rev_seq))})")
    return d, r


def latest_rev_id(doc: dict) -> str:
    return max(doc["revisions"], key=rev_seq)


def find_hash(cat: dict, sha: str) -> list[tuple[str, str]]:
    return [(d, r) for d, doc in cat["documents"].items() for r, rev in doc["revisions"].items() if rev["sha256"] == sha]


def find_identity(cat: dict, key: str) -> str | None:
    for d, doc in cat["documents"].items():
        if doc.get("identity_key") == key:
            return d
    return None


def pointers_for(cat: dict, doc_id: str) -> list[tuple[str, str, dict]]:
    return [(u, s, p) for u in USES for s, m in cat["current_by_use"].get(u, {}).items()
            for d, p in m.items() if d == doc_id]


def already_applied(cat: dict, a) -> bool:
    e = replayed(cat, getattr(a, "request_id", None))
    if e:
        print(f"already applied: request {a.request_id} was {e['event_id']} ({e['command']} at {e['at']}); nothing changed")
        return True
    return False


def verify_original(root: Path, rev: dict, label: str) -> None:
    p = root / rev["path"]
    if not p.exists():
        raise Refused(f"{label} original missing at {rev['path']}; nothing changed")
    got, n = sha256_of(p)
    if got != rev["sha256"] or n != rev["bytes"]:
        raise Refused(f"{label} original at {rev['path']} does not match its recorded SHA-256 / byte count; nothing changed")


# ----------------------------------------------------------------------------- commands
def cmd_add(a) -> int:
    root = Path(a.root)
    by = who(a)
    cat = load(root, create=True, project=a.project)
    if already_applied(cat, a):
        return 0
    src = source_file(a.file)
    sha, size = sha256_of(src)
    disc = disc_code(a.discipline)
    doc_type = norm_key(a.doc_type) or "other"
    identity = a.identity or "|".join([disc, doc_type, norm_key(a.title), norm_key(a.level), norm_key(a.system), norm_key(a.asset)])
    dup = find_identity(cat, identity)
    if dup and not a.confirm_new:
        raise Refused(f"identity key already registered as {dup}: use `revise {dup} {src.name} --reason …`, "
                      f"or --confirm-new to register a separate logical document")
    same = find_hash(cat, sha)
    if same and not a.confirm_new:
        where = ", ".join(f"{d} {r}" for d, r in same)
        print(f"already exists: identical bytes are registered as {where}; no new document created "
              f"(attach relations may still be added to that revision; --confirm-new registers a separate logical document)")
        return 0
    doc_id = f"DOC-{disc}-{next_seq(cat, 'DOC-' + disc):04d}"
    rev_id = "R01"
    path = store(root, src, f"kb/originals/{doc_id}/{rev_id}/{sha}", sha)
    at = now_iso()
    rev = {"revision_id": rev_id, "document_id": doc_id, "parent_revision_id": None,
           "sha256": sha, "bytes": size, "filename": src.name, "path": path,
           "state": "draft", "states": ["draft"], "reason": a.reason or "ADD: first registration",
           "impact": split_list(a.impact), "task": a.task, "note": a.note,
           "submitted_by": by, "submitted_at": at, "endorsement_ids": [], "pending_endorsement_ids": [],
           "attachment_ids": [], "publish_events": [], "superseded_by": []}
    cat["documents"][doc_id] = {
        "document_id": doc_id, "title": a.title, "discipline": disc, "doc_type": doc_type,
        "area": AREA.get(doc_type, "Overview"), "level": a.level, "system": a.system, "asset": a.asset,
        "identity_key": identity, "task": a.task, "created_at": at, "created_by": by,
        "revision_seq": 1, "revisions": {rev_id: rev}}
    eid = record_event(cat, "add", by, a.request_id, document_id=doc_id, revision_id=rev_id, sha256=sha, path=path)
    save(root, cat)
    print(f"ADD {doc_id} {rev_id} · {src.name} · {size} B · sha256 {sha[:16]}… · state draft · {path} · by {by} · {eid}")
    return 0


def cmd_revise(a) -> int:
    root = Path(a.root)
    by = who(a)
    cat = load(root)
    if already_applied(cat, a):
        return 0
    doc = get_doc(cat, a.document_id)
    src = source_file(a.file)
    sha, size = sha256_of(src)
    for rid, r in doc["revisions"].items():
        if r["sha256"] == sha:
            print(f"already exists: {a.document_id} {rid} holds identical bytes; no new revision created; current pointers unchanged")
            return 0
    parent = a.parent or latest_rev_id(doc)
    if parent not in doc["revisions"]:
        raise Refused(f"{a.document_id} has no revision {parent} to use as parent")
    seq = int(doc["revision_seq"]) + 1
    rev_id = f"R{seq:02d}"
    if rev_id in doc["revisions"]:
        raise Refused(f"{a.document_id} {rev_id} already exists; a revision_id is never reused (sequence corrupt — run check)")
    path = store(root, src, f"kb/originals/{a.document_id}/{rev_id}/{sha}", sha)
    at = now_iso()
    doc["revision_seq"] = seq
    doc["revisions"][rev_id] = {
        "revision_id": rev_id, "document_id": a.document_id, "parent_revision_id": parent,
        "sha256": sha, "bytes": size, "filename": src.name, "path": path,
        "state": "draft", "states": ["draft"], "reason": a.reason, "impact": split_list(a.impact),
        "task": a.task, "note": a.note, "submitted_by": by, "submitted_at": at,
        "endorsement_ids": [], "pending_endorsement_ids": [], "attachment_ids": [],
        "publish_events": [], "superseded_by": []}
    elsewhere = [f"{d} {r}" for d, r in find_hash(cat, sha) if d != a.document_id]
    eid = record_event(cat, "revise", by, a.request_id, document_id=a.document_id, revision_id=rev_id,
                       parent_revision_id=parent, sha256=sha, path=path, reason=a.reason)
    save(root, cat)
    note = f" · same bytes also registered as {', '.join(elsewhere)}" if elsewhere else ""
    print(f"REVISE {a.document_id} {rev_id} (parent {parent}) · {src.name} · {size} B · sha256 {sha[:16]}… · state draft · "
          f"current pointers unchanged · impact {len(split_list(a.impact))} · by {by} · {eid}{note}")
    return 0


def load_manifest(cat: dict, path: str | None) -> tuple[list[dict], list[str]]:
    """Read a package manifest [{document_id, revision_id, sha256}] and verify every line."""
    if not path:
        return [], []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise Refused(f"--manifest {path}: {e}") from None
    entries = data.get("package_manifest", data) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise Refused("--manifest must be a JSON list of {document_id, revision_id, sha256}")
    out, mismatches = [], []
    for e in entries:
        d, r, s = e.get("document_id"), e.get("revision_id"), e.get("sha256")
        rev = cat["documents"].get(d, {}).get("revisions", {}).get(r)
        if not rev:
            mismatches.append(f"{d} {r}: not in the catalogue")
            verified = False
        elif rev["sha256"] != s:
            mismatches.append(f"{d} {r}: manifest sha256 differs from the catalogue revision")
            verified = False
        else:
            verified = True
        out.append({"document_id": d, "revision_id": r, "sha256": s, "verified": verified})
    return out, mismatches


def cmd_attach(a) -> int:
    root = Path(a.root)
    by = who(a)
    cat = load(root)
    if already_applied(cat, a):
        return 0
    doc, rev = get_rev(cat, a.document_id, a.revision_id)
    if a.kind not in KINDS:
        raise Refused(f"--kind must be one of {', '.join(KINDS)}")
    src = source_file(a.file)
    sha, size = sha256_of(src)
    scope = a.scope or DEFAULT_SCOPE
    at = now_iso()
    att_id = f"ATT-{next_seq(cat, 'ATT'):04d}"
    path = store(root, src, f"kb/attachments/{a.document_id}/{a.revision_id}/{sha}", sha)
    att = {"attachment_id": att_id, "kind": a.kind, "document_id": a.document_id, "revision_id": a.revision_id,
           "asset_id": a.asset, "sha256": sha, "bytes": size, "filename": src.name, "path": path,
           "scope": scope, "note": a.note, "submitted_by": by, "submitted_at": at, "endorsement_id": None}
    tail = ""
    if a.kind == "endorsement":
        for flag in ("signer", "firm", "discipline", "date"):
            if not getattr(a, flag):
                raise Refused(f"--kind endorsement needs --signer --firm --discipline --date (missing --{flag})")
        date = valid_date(a.date, "--date")
        received = valid_date(a.received, "--received") if a.received else today()
        manifest, mismatches = load_manifest(cat, a.manifest)
        status = "consultant-endorsed" if not mismatches else "to be confirmed"
        end_id = f"END-{next_seq(cat, 'END'):04d}"
        end = {
            "endorsement_id": end_id, "document_id": a.document_id, "revision_id": a.revision_id,
            "revision_sha256": rev["sha256"], "sha256": sha, "attachment_id": att_id,
            "signer": a.signer, "firm": a.firm, "discipline": a.discipline, "date": date,
            "conditions": a.conditions or "", "scope": scope, "covering_letter_ref": a.covering_letter or "",
            "package_manifest": manifest, "digital_signature_verified": bool(a.digital_verified),
            "received_date": received, "registered_by": by, "registered_date": today(), "status": status,
            "note": "Covers this revision_id only; a later revision never inherits it. "
                    "A scanned signature is not a verified digital signature.",
        }
        if mismatches:
            end["manifest_mismatches"] = mismatches
        cat["endorsements"][end_id] = end
        att["endorsement_id"] = end_id
        if status == "consultant-endorsed":
            rev["endorsement_ids"].append(end_id)
            add_state(rev, "consultant-endorsed")
        else:
            rev.setdefault("pending_endorsement_ids", []).append(end_id)
        write_new_file(root / "kb" / "endorsements" / f"{end_id}.json", json.dumps(end, indent=2, ensure_ascii=False) + "\n")
        tail = (f" · endorsement {end_id} {status} ({a.signer}, {a.firm}, {a.discipline}, {date}; "
                f"digital_signature_verified {str(bool(a.digital_verified)).lower()})"
                + (f" · manifest mismatches: {'; '.join(mismatches)}" if mismatches else ""))
    rev["attachment_ids"].append(att_id)
    cat["attachments"][att_id] = att
    eid = record_event(cat, "attach", by, a.request_id, attachment_id=att_id, kind=a.kind, document_id=a.document_id,
                       revision_id=a.revision_id, asset_id=a.asset, sha256=sha, endorsement_id=att["endorsement_id"])
    save(root, cat)
    asset = f" · asset {a.asset}" if a.asset else ""
    print(f"ATTACH {att_id} {a.kind} → {a.document_id} {a.revision_id}{asset} · {src.name} · {size} B · sha256 {sha[:16]}… · "
          f"scope {scope} · main file unchanged · state {rev['state']}{tail} · by {by} · {eid}")
    return 0


def cmd_publish(a) -> int:
    root = Path(a.root)
    by = who(a)
    cat = load(root)
    if already_applied(cat, a):
        return 0
    use = a.use
    if use not in USES:
        raise Refused(f"--use must be one of {', '.join(USES)}")
    scope = a.scope or DEFAULT_SCOPE
    basis = (a.basis or "").strip()
    if not basis:
        raise Refused("--basis is required: the gate report, closed review round, issue closure, "
                      "construction-issue authority or acceptance record this publish rests on")
    doc, rev = get_rev(cat, a.document_id, a.revision_id)
    # validation: the revision and its required derivatives (pilot: the original is present and matches)
    verify_original(root, rev, f"{a.document_id} {a.revision_id}")
    if a.release_id:
        rel = cat["releases"].get(a.release_id)
        if not rel:
            raise Refused(f"unknown release {a.release_id}")
        if not any(e["document_id"] == a.document_id and e["revision_id"] == a.revision_id and e["sha256"] == rev["sha256"]
                   for e in rel["entries"]):
            raise Refused(f"release {a.release_id} does not include {a.document_id} {a.revision_id} with this hash")
    ptrs = cat["current_by_use"].setdefault(use, {}).setdefault(scope, {})
    cur = ptrs.get(a.document_id)
    if cur and cur["revision_id"] == a.revision_id:
        print(f"no change: {a.document_id} {a.revision_id} is already current_{use}[{scope}] (since {cur['published_at']})")
        return 0
    unendorsed = state_rank(rev["state"]) < state_rank("consultant-endorsed")
    if use == "operations" and unendorsed and "accept" not in basis.lower():
        raise Refused(f"{a.revision_id} is {rev['state']}: a draft is published for operations only with an acceptance "
                      f"basis (--basis must name the acceptance record); nothing changed")
    if a.state and a.state != "AI-reviewed":
        raise Refused("--state can only set AI-reviewed; consultant-endorsed comes from `attach --kind endorsement`, "
                      "construction-issued from `publish --use construction`, accepted as-built from `publish --use operations`")
    # ---- everything below is one in-memory change, then ONE atomic write
    at = now_iso()
    prev_id = cur["revision_id"] if cur else None
    eid = record_event(cat, "publish", by, a.request_id, use=use, scope=scope, document_id=a.document_id,
                       revision_id=a.revision_id, previous_revision_id=prev_id, basis=basis, release_id=a.release_id)
    if a.state:
        add_state(rev, "AI-reviewed")
    if use == "construction":
        add_state(rev, "construction-issued")
    elif use == "operations":
        add_state(rev, "accepted as-built")
    if cur:
        doc["revisions"][prev_id]["superseded_by"].append(
            {"use": use, "scope": scope, "revision_id": a.revision_id, "at": at, "event_id": eid})
    ptrs[a.document_id] = {"document_id": a.document_id, "revision_id": a.revision_id, "published_at": at,
                           "published_by": by, "basis": basis, "release_id": a.release_id, "event_id": eid}
    rev["publish_events"].append({"event_id": eid, "use": use, "scope": scope, "at": at, "by": by,
                                  "basis": basis, "release_id": a.release_id, "previous_revision_id": prev_id})
    cat["history"].append({"at": at, "event_id": eid, "use": use, "scope": scope, "document_id": a.document_id,
                           "revision_id": a.revision_id, "previous_revision_id": prev_id, "basis": basis,
                           "release_id": a.release_id, "by": by, "state_after": rev["state"]})
    save(root, cat)
    others = ", ".join(f"{u}[{s}]={p['revision_id']}" for u, s, p in pointers_for(cat, a.document_id)
                       if not (u == use and s == scope)) or "none"
    print(f"PUBLISH current_{use}[{scope}] {a.document_id}: {prev_id or '—'} → {a.revision_id} · state {rev['state']} · "
          f"basis: {basis} · superseded {prev_id or 'nothing'} at {at} · other pointers of this document: {others} · {eid}")
    return 0


def cmd_release(a) -> int:
    root = Path(a.root)
    by = who(a)
    cat = load(root)
    if already_applied(cat, a):
        return 0
    rid = a.id
    if not SAFE_ID.match(rid or ""):
        raise Refused("--id must be letters, digits, dot, underscore or hyphen (e.g. REL-S7-r017, S9-package-1)")
    if rid in cat["releases"]:
        raise Refused(f"release {rid} is already frozen; a release is never rewritten — choose a new id")
    if not a.use and not a.include:
        raise Refused("give --use (freeze the current documents of that use) and/or --include DOC-X-0001:R02 (explicit revisions)")
    if a.use and a.use not in USES:
        raise Refused(f"--use must be one of {', '.join(USES)}")
    entries: dict[tuple[str, str], dict] = {}
    if a.use:
        by_scope = cat["current_by_use"].get(a.use, {})
        scopes = [a.scope] if a.scope else sorted(by_scope)
        for scope in scopes:
            for doc_id, ptr in sorted(by_scope.get(scope, {}).items()):
                rev = cat["documents"][doc_id]["revisions"][ptr["revision_id"]]
                entries[(doc_id, ptr["revision_id"])] = {
                    "document_id": doc_id, "revision_id": ptr["revision_id"], "sha256": rev["sha256"],
                    "bytes": rev["bytes"], "filename": rev["filename"], "path": rev["path"], "state": rev["state"],
                    "scope": scope, "source": f"current_{a.use}", "published_at": ptr["published_at"]}
    for inc in a.include or []:
        m = re.match(r"^(DOC-[A-Z0-9]+-\d{4,}):(R\d{2,})$", inc.strip())
        if not m:
            raise Refused(f"--include {inc}: expected DOC-<DISC>-<NNNN>:R<nn>")
        doc_id, rev_id = m.group(1), m.group(2)
        _, rev = get_rev(cat, doc_id, rev_id)
        entries.setdefault((doc_id, rev_id), {
            "document_id": doc_id, "revision_id": rev_id, "sha256": rev["sha256"], "bytes": rev["bytes"],
            "filename": rev["filename"], "path": rev["path"], "state": rev["state"],
            "scope": a.scope or DEFAULT_SCOPE, "source": "explicit", "published_at": None})
    if not entries:
        raise Refused(f"nothing to release: no current documents for {a.use}[{a.scope or 'all scopes'}] and no --include")
    for (doc_id, rev_id), e in entries.items():
        verify_original(root, cat["documents"][doc_id]["revisions"][rev_id], f"{doc_id} {rev_id}")
    ordered = [entries[k] for k in sorted(entries)]
    manifest = {"schema": "wsg.release/1", "project_release_id": rid, "project_id": cat["project_id"],
                "created_at": now_iso(), "created_by": by, "use": a.use, "scope": a.scope,
                "note": a.note, "base_catalog_version": cat["catalog_version"], "count": len(ordered),
                "entries": ordered}
    body = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    rel_path = f"kb/releases/{rid}.json"
    write_new_file(root / rel_path, body)
    cat["releases"][rid] = {**manifest, "path": rel_path, "manifest_sha256": sha256_text(body)}
    eid = record_event(cat, "release", by, a.request_id, project_release_id=rid, use=a.use, scope=a.scope,
                       count=len(ordered), path=rel_path, manifest_sha256=cat["releases"][rid]["manifest_sha256"])
    save(root, cat)
    print(f"RELEASE {rid} frozen · {len(ordered)} revisions · use {a.use or '—'} · scope {a.scope or 'all'} · {rel_path} · "
          f"manifest sha256 {cat['releases'][rid]['manifest_sha256'][:16]}… · files referenced, not re-issued · "
          f"no current pointer moved · {eid}")
    return 0


def _cut(s, n: int) -> str:
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def cmd_list(a) -> int:
    root = Path(a.root)
    cat = load(root)
    if a.history:
        rows = [h for h in cat["history"] if (not a.use or h["use"] == a.use) and (not a.scope or h["scope"] == a.scope)]
        print(f"publish history · project {cat['project_id']} · catalog_version {cat['catalog_version']} · {len(rows)} events"
              f"{' · use ' + a.use if a.use else ''}{' · scope ' + a.scope if a.scope else ''}")
        print(f"{'at':<25} {'use':<12} {'scope':<14} {'document_id':<18} {'from':<5} {'to':<5} {'state_after':<20} {'by':<12} basis")
        for h in rows:
            print(f"{h['at']:<25} {h['use']:<12} {_cut(h['scope'], 14):<14} {h['document_id']:<18} {h['previous_revision_id'] or '—':<5} "
                  f"{h['revision_id']:<5} {_cut(h['state_after'], 20):<20} {_cut(h['by'], 12):<12} {h['basis']}")
        return 0
    use = a.use or cat.get("default_use", "design")
    if use not in USES:
        raise Refused(f"--use must be one of {', '.join(USES)}")
    by_scope = cat["current_by_use"].get(use, {})
    scopes = [a.scope] if a.scope else sorted(by_scope)
    rows = []
    for scope in scopes:
        for doc_id, ptr in sorted(by_scope.get(scope, {}).items()):
            doc = cat["documents"][doc_id]
            rev = doc["revisions"][ptr["revision_id"]]
            rows.append((scope, doc_id, ptr["revision_id"], rev["state"], doc["discipline"], doc["doc_type"],
                         doc["title"], ptr["published_at"], ptr["basis"]))
    print(f"current_{use} · project {cat['project_id']} · catalog_version {cat['catalog_version']} · {len(rows)} documents"
          f"{' · scope ' + a.scope if a.scope else ''} · current is set by publish events, never by upload time")
    print(f"{'scope':<14} {'document_id':<18} {'rev':<5} {'state':<20} {'disc':<6} {'type':<12} {'title':<40} {'published_at':<25} basis")
    for r in rows:
        print(f"{_cut(r[0], 14):<14} {r[1]:<18} {r[2]:<5} {_cut(r[3], 20):<20} {_cut(r[4], 6):<6} {_cut(r[5], 12):<12} "
              f"{_cut(r[6], 40):<40} {r[7]:<25} {r[8]}")
    if a.drafts:
        waiting = {"design": "awaiting gate release", "construction": "awaiting construction issue",
                   "operations": "awaiting acceptance"}[use]
        current_revs = {(d, p["revision_id"]) for m in by_scope.values() for d, p in m.items()}
        n = 0
        for doc_id, doc in sorted(cat["documents"].items()):
            latest = latest_rev_id(doc)
            if (doc_id, latest) not in current_revs:
                n += 1
                rev = doc["revisions"][latest]
                print(f"  {waiting}: {doc_id} {latest} · state {rev['state']} · {_cut(doc['title'], 40)} · "
                      f"submitted {rev['submitted_at']} by {rev['submitted_by']}")
        print(f"  {n} documents whose latest revision is not current_{use}")
    return 0


def cmd_history(a) -> int:
    root = Path(a.root)
    cat = load(root)
    doc = get_doc(cat, a.document_id)
    revs = sorted(doc["revisions"], key=rev_seq)
    print(f"{a.document_id} · {doc['title']} · {doc['discipline']} {doc['doc_type']} · level {doc.get('level') or '—'} · "
          f"system {doc.get('system') or '—'} · asset {doc.get('asset') or '—'} · identity {doc['identity_key']} · "
          f"{len(revs)} revisions · created {doc['created_at']} by {doc['created_by']}")
    for rid in revs:
        r = doc["revisions"][rid]
        cur = [f"current_{u}[{s}]" for u, s, p in pointers_for(cat, a.document_id) if p["revision_id"] == rid]
        print(f"  {rid} parent {r['parent_revision_id'] or '—'} · state {r['state']} ({', '.join(r['states'])}) · {r['bytes']} B · "
              f"sha256 {r['sha256']} · {r['submitted_at']} by {r['submitted_by']} · {r['path']}")
        print(f"       reason: {r['reason'] or '—'}" + (f" · impact: {', '.join(r['impact'])}" if r["impact"] else "")
              + (f" · task {r['task']}" if r.get("task") else "") + (f" · note: {r['note']}" if r.get("note") else ""))
        for eid in r["endorsement_ids"]:
            e = cat["endorsements"][eid]
            print(f"       endorsement {eid}: {e['signer']} ({e['firm']}, {e['discipline']}) dated {e['date']} · scope {e['scope']} · "
                  f"status {e['status']} · conditions: {e['conditions'] or '—'} · digital_signature_verified "
                  f"{str(e['digital_signature_verified']).lower()} · covers this revision only")
        for eid in r.get("pending_endorsement_ids", []):
            e = cat["endorsements"][eid]
            print(f"       endorsement {eid}: {e['signer']} ({e['firm']}) · status {e['status']} · not marked endorsed: "
                  f"{'; '.join(e.get('manifest_mismatches', []))}")
        for aid in r["attachment_ids"]:
            t = cat["attachments"][aid]
            print(f"       attachment {aid}: {t['kind']} · {t['filename']} · scope {t['scope']}"
                  + (f" · asset {t['asset_id']}" if t.get("asset_id") else "") + f" · {t['submitted_at']}")
        for pe in r["publish_events"]:
            print(f"       published current_{pe['use']}[{pe['scope']}] at {pe['at']} by {pe['by']} · basis: {pe['basis']}"
                  + (f" · release {pe['release_id']}" if pe.get("release_id") else ""))
        for s in r["superseded_by"]:
            print(f"       superseded for {s['use']}[{s['scope']}] by {s['revision_id']} at {s['at']}")
        print(f"       now: {', '.join(cur) if cur else 'not current for any use'}")
    return 0


def cmd_check(a) -> int:
    root = Path(a.root)
    cat = load(root)
    fails: list[str] = []
    counts = {"documents": 0, "revisions": 0, "attachments": 0, "endorsements": 0, "pointers": 0,
              "releases": 0, "history": len(cat["history"]), "events": len(cat["events"])}
    bad = fails.append
    seen_paths: dict[str, str] = {}
    identity: dict[str, str] = {}
    doc_max: dict[str, int] = {}

    def check_file(rel: str, sha: str, size: int, label: str) -> None:
        if rel in seen_paths:
            bad(f"{label}: key {rel} is also used by {seen_paths[rel]}")
        seen_paths[rel] = label
        p = root / rel
        if not p.exists():
            bad(f"{label}: file missing at {rel}")
            return
        got, n = sha256_of(p)
        if got != sha:
            bad(f"{label}: SHA-256 mismatch at {rel} (recorded {sha[:16]}…, found {got[:16]}…)")
        if n != size:
            bad(f"{label}: byte count {n} differs from recorded {size}")

    for doc_id, doc in cat["documents"].items():
        counts["documents"] += 1
        m = DOC_ID.match(doc_id)
        if not m or doc.get("document_id") != doc_id:
            bad(f"{doc_id}: malformed document_id or record")
        else:
            doc_max[m.group(1)] = max(doc_max.get(m.group(1), 0), int(m.group(2)))
        key = doc.get("identity_key")
        if key in identity:
            bad(f"{doc_id} and {identity[key]} share the identity key {key!r}")
        identity[key] = doc_id
        maxseq = 0
        for rid, r in doc["revisions"].items():
            counts["revisions"] += 1
            label = f"{doc_id} {rid}"
            if not REV_ID.match(rid) or r.get("revision_id") != rid or r.get("document_id") != doc_id:
                bad(f"{label}: revision key and record disagree")
                continue
            maxseq = max(maxseq, rev_seq(rid))
            if not r["path"].startswith(f"kb/originals/{doc_id}/{rid}/{r['sha256']}/"):
                bad(f"{label}: path {r['path']} is not its revision key")
            check_file(r["path"], r["sha256"], r["bytes"], label)
            par = r.get("parent_revision_id")
            if par is None and rid != "R01":
                bad(f"{label}: has no parent revision")
            if par is not None and (par not in doc["revisions"] or rev_seq(par) >= rev_seq(rid)):
                bad(f"{label}: parent {par} missing or not older")
            if r.get("state") not in STATES or any(s not in STATES for s in r.get("states", [])) \
                    or r.get("state") != max(r.get("states") or ["draft"], key=state_rank):
                bad(f"{label}: state {r.get('state')!r} / states {r.get('states')!r} inconsistent")
            if bool(r["endorsement_ids"]) != ("consultant-endorsed" in r["states"]):
                bad(f"{label}: consultant-endorsed fact and endorsement list disagree")
            if any(pe["use"] == "construction" for pe in r["publish_events"]) != ("construction-issued" in r["states"]):
                bad(f"{label}: construction-issued fact and publish events disagree")
            if any(pe["use"] == "operations" for pe in r["publish_events"]) != ("accepted as-built" in r["states"]):
                bad(f"{label}: accepted as-built fact and publish events disagree")
            for eid in r["endorsement_ids"] + r.get("pending_endorsement_ids", []):
                e = cat["endorsements"].get(eid)
                if not e:
                    bad(f"{label}: endorsement {eid} not in the catalogue")
                elif (e["document_id"], e["revision_id"]) != (doc_id, rid):
                    bad(f"{label}: lists endorsement {eid} that is bound to {e['document_id']} {e['revision_id']} — an endorsement never moves")
            for aid in r["attachment_ids"]:
                t = cat["attachments"].get(aid)
                if not t:
                    bad(f"{label}: attachment {aid} not in the catalogue")
                elif (t["document_id"], t["revision_id"]) != (doc_id, rid):
                    bad(f"{label}: lists attachment {aid} bound to {t['document_id']} {t['revision_id']}")
        if int(doc.get("revision_seq", 0)) < maxseq:
            bad(f"{doc_id}: revision_seq {doc.get('revision_seq')} below the highest revision R{maxseq:02d}")
    for aid, t in cat["attachments"].items():
        counts["attachments"] += 1
        rev = cat["documents"].get(t["document_id"], {}).get("revisions", {}).get(t["revision_id"])
        if not rev:
            bad(f"{aid}: bound to unknown revision {t['document_id']} {t['revision_id']}")
        elif aid not in rev["attachment_ids"]:
            bad(f"{aid}: not listed on {t['document_id']} {t['revision_id']}")
        check_file(t["path"], t["sha256"], t["bytes"], aid)
    for eid, e in cat["endorsements"].items():
        counts["endorsements"] += 1
        rev = cat["documents"].get(e["document_id"], {}).get("revisions", {}).get(e["revision_id"])
        if not rev:
            bad(f"{eid}: bound to unknown revision {e['document_id']} {e['revision_id']}")
            continue
        if e["revision_sha256"] != rev["sha256"]:
            bad(f"{eid}: revision_sha256 differs from {e['document_id']} {e['revision_id']}")
        if e["status"] == "consultant-endorsed" and eid not in rev["endorsement_ids"]:
            bad(f"{eid}: consultant-endorsed but not listed on its revision")
        if e["status"] != "consultant-endorsed" and eid in rev["endorsement_ids"]:
            bad(f"{eid}: status {e['status']} yet listed as an endorsement of the revision")
        if e["attachment_id"] not in cat["attachments"]:
            bad(f"{eid}: attachment {e['attachment_id']} missing")
        for other_doc, other_rev in ((d, r) for d, doc in cat["documents"].items() for r in doc["revisions"]
                                     if (d, r) != (e["document_id"], e["revision_id"])):
            if eid in cat["documents"][other_doc]["revisions"][other_rev]["endorsement_ids"]:
                bad(f"{eid}: also listed on {other_doc} {other_rev} — an endorsement is never inherited")
        if e["status"] == "consultant-endorsed":
            for line in e.get("package_manifest", []):
                r2 = cat["documents"].get(line["document_id"], {}).get("revisions", {}).get(line["revision_id"])
                if not r2 or r2["sha256"] != line["sha256"]:
                    bad(f"{eid}: package manifest line {line['document_id']} {line['revision_id']} no longer matches the catalogue")
        fp = root / "kb" / "endorsements" / f"{eid}.json"
        if not fp.exists():
            bad(f"{eid}: record file kb/endorsements/{eid}.json missing")
        else:
            try:
                with fp.open(encoding="utf-8") as f:
                    if json.load(f).get("endorsement_id") != eid:
                        bad(f"{eid}: record file names a different endorsement")
            except (OSError, json.JSONDecodeError) as ex:
                bad(f"{eid}: record file unreadable ({ex})")
    last: dict[tuple[str, str, str], dict] = {}
    for h in cat["history"]:
        key = (h["use"], h["scope"], h["document_id"])
        last[key] = h
        doc = cat["documents"].get(h["document_id"])
        if not doc or h["revision_id"] not in doc["revisions"]:
            bad(f"history {h['event_id']}: revision {h['document_id']} {h['revision_id']} does not exist")
            continue
        if h["previous_revision_id"]:
            prev = doc["revisions"].get(h["previous_revision_id"])
            if not prev or not any(s["use"] == h["use"] and s["scope"] == h["scope"] and s["revision_id"] == h["revision_id"]
                                   and s["event_id"] == h["event_id"] for s in prev["superseded_by"]):
                bad(f"history {h['event_id']}: {h['document_id']} {h['previous_revision_id']} carries no matching superseded_by record")
    for use in USES:
        for scope, m in cat["current_by_use"].get(use, {}).items():
            for doc_id, ptr in m.items():
                counts["pointers"] += 1
                doc = cat["documents"].get(doc_id)
                if not doc or ptr["revision_id"] not in doc["revisions"] or ptr.get("document_id") != doc_id:
                    bad(f"current_{use}[{scope}] {doc_id}: pointer does not resolve to a revision of that document")
                    continue
                h = last.get((use, scope, doc_id))
                if not h or h["revision_id"] != ptr["revision_id"] or h["event_id"] != ptr["event_id"]:
                    bad(f"current_{use}[{scope}] {doc_id}: pointer {ptr['revision_id']} disagrees with the last publish event")
                rev = doc["revisions"][ptr["revision_id"]]
                for s in rev["superseded_by"]:
                    if s["use"] == use and s["scope"] == scope and s["at"] > ptr["published_at"]:
                        bad(f"current_{use}[{scope}] {doc_id}: {ptr['revision_id']} was superseded by {s['revision_id']} after it was published")
    for (use, scope, doc_id), h in last.items():
        ptr = cat["current_by_use"].get(use, {}).get(scope, {}).get(doc_id)
        if not ptr or ptr["revision_id"] != h["revision_id"]:
            bad(f"history says current_{use}[{scope}] {doc_id} = {h['revision_id']} but the pointer is {ptr['revision_id'] if ptr else 'missing'}")
    for doc_id, doc in cat["documents"].items():
        for rid, r in doc["revisions"].items():
            for s in r["superseded_by"]:
                if s["revision_id"] not in doc["revisions"]:
                    bad(f"{doc_id} {rid}: superseded_by names unknown revision {s['revision_id']}")
                if not any(h["event_id"] == s["event_id"] and h["previous_revision_id"] == rid and h["revision_id"] == s["revision_id"]
                           and h["use"] == s["use"] and h["scope"] == s["scope"] for h in cat["history"]):
                    bad(f"{doc_id} {rid}: superseded_by {s['revision_id']} ({s['use']}[{s['scope']}]) has no publish event")
    for rid, rel in cat["releases"].items():
        counts["releases"] += 1
        fp = root / rel["path"]
        if not fp.exists():
            bad(f"release {rid}: manifest file {rel['path']} missing")
        else:
            text = fp.read_text(encoding="utf-8")
            if sha256_text(text) != rel["manifest_sha256"]:
                bad(f"release {rid}: manifest file {rel['path']} does not match its recorded SHA-256")
            else:
                filed = json.loads(text)
                if {(e["document_id"], e["revision_id"], e["sha256"]) for e in filed["entries"]} != \
                        {(e["document_id"], e["revision_id"], e["sha256"]) for e in rel["entries"]}:
                    bad(f"release {rid}: manifest file and catalogue entries differ")
        for e in rel["entries"]:
            r = cat["documents"].get(e["document_id"], {}).get("revisions", {}).get(e["revision_id"])
            if not r:
                bad(f"release {rid}: {e['document_id']} {e['revision_id']} does not exist")
            elif r["sha256"] != e["sha256"]:
                bad(f"release {rid}: {e['document_id']} {e['revision_id']} hash differs from the catalogue")
    for disc, mx in doc_max.items():
        if int(cat["sequences"].get("DOC-" + disc, 0)) < mx:
            bad(f"sequence DOC-{disc} below the highest document number {mx}")
    for prefix, items in (("ATT", cat["attachments"]), ("END", cat["endorsements"])):
        mx = max((int(i.split("-")[1]) for i in items), default=0)
        if int(cat["sequences"].get(prefix, 0)) < mx:
            bad(f"sequence {prefix} below the highest id {mx}")
    ev_ids = [e["event_id"] for e in cat["events"]]
    if len(ev_ids) != len(set(ev_ids)):
        bad("duplicate event ids")
    req = [e["request_id"] for e in cat["events"] if e.get("request_id")]
    if len(req) != len(set(req)):
        bad("duplicate request ids in the event log")
    unregistered = 0
    for sub in ("originals", "attachments"):
        base = root / "kb" / sub
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file() and not p.name.startswith(".incoming-") and p.relative_to(root).as_posix() not in seen_paths:
                    unregistered += 1
    verdict = "OK" if not fails else f"FAILED ({len(fails)})"
    print(f"CHECK {verdict} · project {cat['project_id']} · catalog_version {cat['catalog_version']} · " +
          " · ".join(f"{k} {v}" for k, v in counts.items()) +
          f" · unregistered files under kb {unregistered} · data-consistency result, not an engineering PASS")
    for f in fails:
        print(f"  FAIL {f}")
    return 1 if fails else 0


def cmd_export_index(a) -> int:
    root = Path(a.root)
    cat = load(root)
    at = now_iso()
    current: dict[str, dict[str, list[dict]]] = {}
    n = 0
    for use in USES:
        current[use] = {}
        for scope, m in sorted(cat["current_by_use"].get(use, {}).items()):
            rows = []
            for doc_id, ptr in sorted(m.items()):
                doc = cat["documents"][doc_id]
                rev = doc["revisions"][ptr["revision_id"]]
                rows.append({"document_id": doc_id, "revision_id": ptr["revision_id"], "title": doc["title"],
                             "discipline": doc["discipline"], "doc_type": doc["doc_type"], "area": doc["area"],
                             "level": doc.get("level"), "system": doc.get("system"), "asset": doc.get("asset"),
                             "state": rev["state"], "states": rev["states"], "sha256": rev["sha256"], "bytes": rev["bytes"],
                             "path": rev["path"], "published_at": ptr["published_at"], "basis": ptr["basis"],
                             "release_id": ptr.get("release_id"), "endorsements": rev["endorsement_ids"]})
                n += 1
            current[use][scope] = rows
    releases = [{"project_release_id": r, "use": rel["use"], "scope": rel["scope"], "count": rel["count"],
                 "created_at": rel["created_at"], "path": rel["path"]} for r, rel in sorted(cat["releases"].items())]
    index = {"schema": "wsg.index/1", "project_id": cat["project_id"], "generated_at": at,
             "catalog_version": cat["catalog_version"], "documents": len(cat["documents"]),
             "current": current, "releases": releases}
    kb = root / "kb"
    kb.mkdir(parents=True, exist_ok=True)
    (kb / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [f"# {cat['project_id']} — project knowledge base", "",
             f"> Current effective documents per use and scope from catalogue.json (catalog_version {cat['catalog_version']}, "
             f"generated {at}). \"Current\" is set by publish events, never by upload time. Drafts are not listed. "
             f"Full history: python3 scripts/catalogue.py history <document_id>.", ""]
    for use in USES:
        lines.append(f"## current_{use}")
        if not any(current[use].values()):
            lines.append("- (none published)")
        for scope, rows in current[use].items():
            lines.append(f"### scope {scope}")
            for r in rows:
                lines.append(f"- {r['document_id']} {r['revision_id']} · {r['title']} · {r['discipline']} {r['doc_type']} · "
                             f"state {r['state']} · {r['path']} · published {r['published_at']} · basis: {r['basis']}")
        lines.append("")
    lines.append("## releases")
    lines.extend([f"- {r['project_release_id']} · use {r['use'] or '—'} · scope {r['scope'] or 'all'} · {r['count']} revisions · {r['path']}"
                  for r in releases] or ["- (none)"])
    (kb / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"EXPORT-INDEX kb/index.json and kb/llms.txt · {n} current entries across {len(USES)} uses · "
          f"{len(releases)} releases · catalog_version {cat['catalog_version']}")
    return 0


# ----------------------------------------------------------------------------- selftest
def cmd_selftest(a) -> int:
    results: list[tuple[bool, str]] = []

    def t(name: str, cond: bool, detail: str = "") -> None:
        results.append((bool(cond), name + (f" — {detail}" if detail and not cond else "")))
        print(("PASS " if cond else "FAIL ") + results[-1][1])

    def q(*argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = run(list(argv))
            except SystemExit as e:  # argparse errors
                code = int(e.code or 0)
        return code, out.getvalue().strip(), err.getvalue().strip()

    with tempfile.TemporaryDirectory(prefix="catalogue-selftest-") as tmp:
        root = Path(tmp)
        R = ["--root", tmp, "--by", "selftest"]

        def cat() -> dict:
            return json.loads(cat_path(root).read_text(encoding="utf-8"))

        def cat_bytes() -> bytes:
            return cat_path(root).read_bytes()

        a1 = root / "M-604.svg"; a1.write_text("<svg>L22 CHW schematic v1</svg>")
        a2 = root / "M-604_v2.svg"; a2.write_text("<svg>L22 CHW schematic v2 — duct resized</svg>")
        b1 = root / "A-100.svg"; b1.write_text("<svg>Ground floor GA</svg>")
        b2 = root / "A-100_v2.svg"; b2.write_text("<svg>Ground floor GA v2</svg>")
        letter = root / "endorsement-letter.pdf"; letter.write_bytes(b"%PDF-1.4 signed letter\n")
        letter2 = root / "package-letter.pdf"; letter2.write_bytes(b"%PDF-1.4 package letter\n")
        photo = root / "site-photo.jpg"; photo.write_bytes(b"\xff\xd8photo")

        code, out, err = q("add", str(a1), "--title", "L22 CHW schematic", "--discipline", "MECH", "--doc-type", "drawing",
                           "--level", "L22", "--system", "CHW", "--task", "S6", "--project", "DEMO", *R)
        t("add A creates DOC-MECH-0001 R01", code == 0 and "ADD DOC-MECH-0001 R01" in out, out + err)
        c = cat()
        sha_a1, _ = sha256_of(a1)
        ra1 = c["documents"]["DOC-MECH-0001"]["revisions"]["R01"]
        t("A R01 stored at its revision key with matching SHA-256",
          ra1["path"] == f"kb/originals/DOC-MECH-0001/R01/{sha_a1}/M-604.svg" and (root / ra1["path"]).exists()
          and sha256_of(root / ra1["path"])[0] == sha_a1 and ra1["state"] == "draft" and ra1["parent_revision_id"] is None)
        code, out, err = q("add", str(b1), "--title", "Ground floor GA", "--discipline", "ARCH", "--doc-type", "drawing", "--level", "L00", *R)
        t("add B creates DOC-ARCH-0001 R01", code == 0 and "ADD DOC-ARCH-0001 R01" in out, out + err)
        code, out, err = q("add", str(a2), "--title", "L22 CHW schematic", "--discipline", "MECH", "--doc-type", "drawing",
                           "--level", "L22", "--system", "CHW", *R)
        t("add with an existing identity key is refused and points to revise", code == 2 and "revise DOC-MECH-0001" in err, out + err)
        code, out, err = q("add", str(a1), "--title", "Copy of the schematic", "--discipline", "MECH", *R)
        t("add of identical bytes reports already exists and creates nothing",
          code == 0 and "already exists" in out and len(cat()["documents"]) == 2, out + err)
        b_before = copy.deepcopy(cat()["documents"]["DOC-ARCH-0001"])
        a_r01_before = copy.deepcopy(cat()["documents"]["DOC-MECH-0001"]["revisions"]["R01"])

        code, out, err = q("revise", "DOC-MECH-0001", str(a2), "--reason", "duct resized after clash I-0017",
                           "--impact", "M-012,M-604", "--impact", "BQ-M-22", *R)
        c = cat()
        ra2 = c["documents"]["DOC-MECH-0001"]["revisions"].get("R02", {})
        t("revise A creates R02 with parent R01 and the impact list",
          code == 0 and "REVISE DOC-MECH-0001 R02 (parent R01)" in out and ra2.get("parent_revision_id") == "R01"
          and ra2.get("impact") == ["M-012", "M-604", "BQ-M-22"] and ra2.get("state") == "draft", out + err)
        t("revise leaves R01 untouched and moves no pointer",
          c["documents"]["DOC-MECH-0001"]["revisions"]["R01"] == a_r01_before
          and all(not m for m in c["current_by_use"].values()))
        code, out, err = q("revise", "DOC-MECH-0001", str(a2), "--reason", "again", *R)
        t("revise with identical bytes reports already exists and adds no revision",
          code == 0 and "already exists" in out and len(cat()["documents"]["DOC-MECH-0001"]["revisions"]) == 2, out + err)

        code, out, err = q("publish", "DOC-MECH-0001", "R01", "--use", "design", "--basis", "G4 gate report 2026-09-10", *R)
        c = cat()
        t("publish A R01 for design sets current_design[project]",
          code == 0 and c["current_by_use"]["design"]["project"]["DOC-MECH-0001"]["revision_id"] == "R01"
          and len(c["history"]) == 1, out + err)
        t("B is untouched by A's publish and has no pointer",
          c["documents"]["DOC-ARCH-0001"] == b_before and "DOC-ARCH-0001" not in c["current_by_use"]["design"].get("project", {}))
        code, out, err = q("publish", "DOC-MECH-0001", "R01", "--use", "construction", "--basis", "construction issue CI-001 signed by PD", *R)
        c = cat()
        t("publish A R01 for construction sets current_construction and the construction-issued fact",
          code == 0 and c["current_by_use"]["construction"]["project"]["DOC-MECH-0001"]["revision_id"] == "R01"
          and "construction-issued" in c["documents"]["DOC-MECH-0001"]["revisions"]["R01"]["states"], out + err)
        code, out, err = q("publish", "DOC-MECH-0001", "R02", "--use", "design", "--basis", "G5 gate report; issue I-0017 closed", *R)
        c = cat()
        r01 = c["documents"]["DOC-MECH-0001"]["revisions"]["R01"]
        t("publish A R02 for design moves design to R02 while construction stays on R01",
          code == 0 and c["current_by_use"]["design"]["project"]["DOC-MECH-0001"]["revision_id"] == "R02"
          and c["current_by_use"]["construction"]["project"]["DOC-MECH-0001"]["revision_id"] == "R01", out + err)
        t("R01 records superseded_by R02 for design only, with a timestamp",
          [(s["use"], s["scope"], s["revision_id"]) for s in r01["superseded_by"]] == [("design", "project", "R02")]
          and bool(r01["superseded_by"][0]["at"]))
        t("R02 stays draft after a design publish", c["documents"]["DOC-MECH-0001"]["revisions"]["R02"]["state"] == "draft")
        before = cat_bytes()
        code, out, err = q("publish", "DOC-MECH-0001", "R02", "--use", "operations", "--basis", "handover meeting", *R)
        t("publishing a draft for operations without an acceptance basis is refused and changes nothing",
          code == 2 and "accept" in err and cat_bytes() == before, out + err)
        code, out, err = q("publish", "DOC-MECH-0001", "R02", "--use", "design", "--basis", "G5 again", *R)
        t("re-publishing the current revision reports no change", code == 0 and "no change" in out and len(cat()["history"]) == 3, out + err)

        code, out, err = q("attach", "DOC-MECH-0001", "R01", str(letter), "--kind", "endorsement", "--signer", "J. Smith",
                           "--firm", "XYZ Consulting", "--discipline", "MECH", "--date", "2026-09-12",
                           "--conditions", "subject to CHW pump curve confirmation", "--scope", "L22 CHW",
                           "--covering-letter", "endorsement-letter.pdf", *R)
        c = cat()
        r01 = c["documents"]["DOC-MECH-0001"]["revisions"]["R01"]
        r02 = c["documents"]["DOC-MECH-0001"]["revisions"]["R02"]
        e1 = c["endorsements"].get("END-0001", {})
        t("attach endorsement to A R01 creates END-0001 bound to R01 and marks R01 consultant-endorsed",
          code == 0 and e1.get("revision_id") == "R01" and "END-0001" in r01["endorsement_ids"]
          and "consultant-endorsed" in r01["states"] and e1.get("status") == "consultant-endorsed", out + err)
        t("endorsement record has the template fields and digital_signature_verified false",
          all(k in e1 for k in ("endorsement_id", "document_id", "revision_id", "sha256", "signer", "firm", "discipline", "date",
                                "conditions", "scope", "covering_letter_ref", "package_manifest", "digital_signature_verified",
                                "received_date", "registered_by", "registered_date", "status"))
          and e1.get("digital_signature_verified") is False and (root / "kb/endorsements/END-0001.json").exists())
        t("R01 original bytes unchanged by the endorsement", sha256_of(root / r01["path"])[0] == sha_a1)
        t("R02 (later revision) does not inherit the endorsement",
          r02["endorsement_ids"] == [] and "consultant-endorsed" not in r02["states"] and r02["state"] == "draft")
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps([{"document_id": "DOC-MECH-0001", "revision_id": "R02", "sha256": "0" * 64}]))
        code, out, err = q("attach", "DOC-MECH-0001", "R02", str(letter2), "--kind", "endorsement", "--signer", "J. Smith",
                           "--firm", "XYZ Consulting", "--discipline", "MECH", "--date", "2026-09-13", "--manifest", str(manifest),
                           "--digital-verified", *R)
        c = cat()
        r02 = c["documents"]["DOC-MECH-0001"]["revisions"]["R02"]
        e2 = c["endorsements"].get("END-0002", {})
        t("endorsement with a mismatching package manifest stays 'to be confirmed' and marks nothing",
          code == 0 and e2.get("status") == "to be confirmed" and r02["endorsement_ids"] == [] and r02["state"] == "draft"
          and e2.get("digital_signature_verified") is True, out + err)
        code, out, err = q("attach", "DOC-ARCH-0001", "R01", str(photo), "--kind", "photo", "--asset", "AHU-01", *R)
        t("attach photo binds to the revision and the asset", code == 0 and cat()["attachments"]["ATT-0003"]["asset_id"] == "AHU-01", out + err)

        code, out, err = q("release", "--id", "REL-G5-001", "--use", "design", *R)
        c = cat()
        rel = c["releases"].get("REL-G5-001", {})
        t("release freezes current_design: A R02 only, with SHA-256, file written, no pointer moved",
          code == 0 and [(e["document_id"], e["revision_id"], e["sha256"]) for e in rel.get("entries", [])]
          == [("DOC-MECH-0001", "R02", sha256_of(a2)[0])] and (root / "kb/releases/REL-G5-001.json").exists()
          and c["current_by_use"]["construction"]["project"]["DOC-MECH-0001"]["revision_id"] == "R01", out + err)
        code, out, err = q("release", "--id", "REL-G5-001", "--use", "design", *R)
        t("a frozen release id is refused a second time", code == 2 and "never rewritten" in err, out + err)
        code, out, err = q("release", "--id", "REL-S4-viewer", "--include", "DOC-ARCH-0001:R01", *R)
        t("explicit release of a draft revision (viewer release) works", code == 0 and cat()["releases"]["REL-S4-viewer"]["count"] == 1, out + err)
        code, out, err = q("publish", "DOC-ARCH-0001", "R01", "--use", "design", "--basis", "G3", "--release-id", "REL-G5-001", *R)
        t("publish citing a release that lacks the revision is refused", code == 2 and "does not include" in err, out + err)
        code, out, err = q("publish", "DOC-ARCH-0001", "R01", "--use", "design", "--basis", "G3 gate report", "--release-id", "REL-S4-viewer", *R)
        t("publish citing a release that holds the revision succeeds", code == 0, out + err)

        code, out, err = q("check", *R)
        t("check passes on the consistent catalogue", code == 0 and out.startswith("CHECK OK"), out + err)
        p = root / ra1["path"]
        original = p.read_bytes()
        p.write_bytes(original + b"x")
        code, out, err = q("check", *R)
        t("check fails when an original's bytes change", code == 1 and "SHA-256 mismatch" in out, out + err)
        p.write_bytes(original)
        code, out, err = q("check", *R)
        t("check passes again once the bytes are restored", code == 0, out + err)

        code, out, err = q("revise", "DOC-ARCH-0001", str(b2), "--reason", "north stair door swing", "--request-id", "req-77", *R)
        code2, out2, err2 = q("revise", "DOC-ARCH-0001", str(a1), "--reason", "replayed", "--request-id", "req-77", *R)
        t("a replayed request id is recognised and applied once",
          code == 0 and code2 == 0 and "already applied" in out2 and len(cat()["documents"]["DOC-ARCH-0001"]["revisions"]) == 2, out2 + err2)

        code, out, err = q("list", "--use", "construction", *R)
        t("list --use construction shows A at R01", code == 0 and "DOC-MECH-0001" in out and " R01 " in out, out + err)
        code, out, err = q("list", "--use", "design", "--drafts", *R)
        t("list --use design shows A at R02 and the pending ARCH R02 draft", code == 0 and " R02 " in out and "awaiting gate release: DOC-ARCH-0001 R02" in out, out + err)
        code, out, err = q("list", "--history", *R)
        t("list --history prints every publish event", code == 0 and "4 events" in out, out + err)
        code, out, err = q("history", "DOC-MECH-0001", *R)
        t("history shows the revision chain, the endorsement and the supersession",
          code == 0 and "R02 parent R01" in out and "endorsement END-0001" in out and "superseded for design[project] by R02" in out, out + err)
        code, out, err = q("export-index", *R)
        idx = json.loads((root / "kb/index.json").read_text(encoding="utf-8")) if (root / "kb/index.json").exists() else {}
        t("export-index writes kb/index.json and kb/llms.txt with the current documents",
          code == 0 and [r["document_id"] + " " + r["revision_id"] for r in idx.get("current", {}).get("design", {}).get("project", [])]
          == ["DOC-ARCH-0001 R01", "DOC-MECH-0001 R02"] and "DOC-MECH-0001 R02" in (root / "kb/llms.txt").read_text(encoding="utf-8"), out + err)
        n_files_before = sum(1 for _ in (root / "kb").rglob("*") if _.is_file())
        code, out, err = q("check", *R)
        t("final check passes and no file was deleted", code == 0 and sum(1 for _ in (root / "kb").rglob("*") if _.is_file()) == n_files_before, out + err)

    passed = sum(1 for ok, _ in results if ok)
    failed = len(results) - passed
    print(f"selftest: {passed} passed, {failed} failed")
    return 1 if failed else 0


# ----------------------------------------------------------------------------- CLI
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="catalogue.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="project repository root holding catalogue.json and kb/ (default .)")
    common.add_argument("--by", help="submitter; default env WS_USER, then the OS user name")
    mut = argparse.ArgumentParser(add_help=False, parents=[common])
    mut.add_argument("--request-id", help="idempotency key: a replayed command with the same id is recognised and applied once")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")

    p = sub.add_parser("add", parents=[mut], help="register a new document: new document_id, revision R01, file stored at its key")
    p.add_argument("file")
    p.add_argument("--title", required=True)
    p.add_argument("--discipline", required=True, help="MECH ELEC HYD FIRE STR ARCH ID VT CIVIL ESD PM … (becomes the DOC-<DISC>- prefix)")
    p.add_argument("--doc-type", default="other",
                   help="drawing calc calc-book dbr compliance-matrix gate-report brief report spec bq rfq release-sheet ifc "
                        "decision review-round as-built om-manual asset-register commissioning construction-record other")
    p.add_argument("--level"); p.add_argument("--system"); p.add_argument("--asset"); p.add_argument("--task")
    p.add_argument("--reason", help="reason recorded on R01 (default: ADD: first registration)")
    p.add_argument("--impact", action="append", help="comma-separated impact list; may repeat")
    p.add_argument("--identity", help="identity key such as a sheet number, calc ID or model id + release; "
                                      "default discipline|doc_type|title|level|system|asset")
    p.add_argument("--note")
    p.add_argument("--project", help="project_id written when catalogue.json is created (default: the root folder name)")
    p.add_argument("--confirm-new", action="store_true", help="register a separate logical document although the identity key or the bytes already exist")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("revise", parents=[mut], help="new immutable revision of an existing document; pointers do not move")
    p.add_argument("document_id"); p.add_argument("file")
    p.add_argument("--reason", required=True)
    p.add_argument("--impact", action="append", help="comma-separated calcs / sheets / models / BQ lines / signed scopes affected; may repeat")
    p.add_argument("--parent", help="parent revision (default: the latest revision)")
    p.add_argument("--task"); p.add_argument("--note")
    p.set_defaults(func=cmd_revise)

    p = sub.add_parser("attach", parents=[mut], help="bind evidence to one exact revision (and optionally an asset); main file unchanged")
    p.add_argument("document_id"); p.add_argument("revision_id"); p.add_argument("file")
    p.add_argument("--kind", required=True, choices=KINDS)
    p.add_argument("--scope", help="what the evidence covers (default project)")
    p.add_argument("--asset", help="asset_id the evidence also covers")
    p.add_argument("--note")
    p.add_argument("--signer"); p.add_argument("--firm"); p.add_argument("--discipline")
    p.add_argument("--date", help="date on the signature or covering letter, YYYY-MM-DD")
    p.add_argument("--conditions", help="conditions attached to the endorsement")
    p.add_argument("--covering-letter", help="reference to the covering letter or confirmation email")
    p.add_argument("--manifest", help="JSON list of {document_id, revision_id, sha256} for a package signature")
    p.add_argument("--received", help="date received, YYYY-MM-DD (default today)")
    p.add_argument("--digital-verified", action="store_true", help="a digital signature was verified (never for a scanned signature)")
    p.set_defaults(func=cmd_attach)

    p = sub.add_parser("publish", parents=[mut], help="publish-effective: switch current_by_use[use][scope] to this revision in one atomic write")
    p.add_argument("document_id"); p.add_argument("revision_id")
    p.add_argument("--use", required=True, choices=USES)
    p.add_argument("--scope", help="whole project (default), a level id, system id, discipline, procurement package or named package")
    p.add_argument("--basis", required=True, help="gate report / closed round / issue closure / construction-issue authority / acceptance record")
    p.add_argument("--release-id", help="frozen release this publish rests on; must include the revision")
    p.add_argument("--state", choices=["AI-reviewed"], help="also record the AI-reviewed fact (which layers / round in --basis)")
    p.set_defaults(func=cmd_publish)

    p = sub.add_parser("release", parents=[mut], help="freeze project_release_id → document_id / revision_id / SHA-256 manifest")
    p.add_argument("--id", required=True, help="project_release_id, e.g. REL-S7-r017 or S9-package-1")
    p.add_argument("--use", choices=USES, help="freeze every current document of this use")
    p.add_argument("--scope", help="limit to one scope")
    p.add_argument("--include", action="append", help="explicit DOC-X-0001:R02 to include (drafts allowed, e.g. a viewer release); may repeat")
    p.add_argument("--note")
    p.set_defaults(func=cmd_release)

    p = sub.add_parser("list", parents=[common], help="current effective revisions for a use (default design), or the publish history")
    p.add_argument("--use", choices=USES); p.add_argument("--scope")
    p.add_argument("--history", action="store_true", help="print the publish history instead")
    p.add_argument("--drafts", action="store_true", help="also list documents whose latest revision is not current for the use")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("history", parents=[common], help="every revision of a document with parent, reason, states, endorsements, publish events")
    p.add_argument("document_id")
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("check", parents=[common], help="integrity: files and hashes, pointers, keys, endorsements, supersession chains, releases")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("export-index", parents=[common], help="write kb/index.json and kb/llms.txt (current per use) for the static book")
    p.set_defaults(func=cmd_export_index)

    p = sub.add_parser("selftest", help="run the whole flow in a temporary directory and print PASS / FAIL per assertion")
    p.set_defaults(func=cmd_selftest)
    return ap


def run(argv: list[str]) -> int:
    a = build_parser().parse_args(argv)
    try:
        return int(a.func(a) or 0)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2


def main() -> None:
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
