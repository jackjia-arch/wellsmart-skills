#!/usr/bin/env python3
"""
coord_check.py — deterministic 2D services-coordination checker (S3 zoning plans, S6 layouts).

Why it exists
-------------
Big ducts and big pipes must never meet for the first time in the S7 clash run. Before any 3D
model exists, every run on a level is a polyline in plan with a size and a vertical band (top /
bottom RL). That is enough to compute, deterministically, every crossing, every parallel
approach, every envelope breach and whether the ceiling zone is deep enough for two runs to
stack. This script does that from two DB files and writes a CSV report plus an optional SVG plan.
It runs at S3 (services-zoning plans, `--stage S3`, missing RLs tolerated on small runs) and at
S6 (discipline layouts, `--stage S6`, missing RLs on large runs are errors). Its result is a
data-consistency result, never an engineering PASS (SKILL.md rule 10).

Input files (one per level; metres; project coordinate system; RLs in metres to 3 decimals)
------------------------------------------------------------------------------------------
db/services-routes.json
  {"level": "L22", "units": "m",
   "zones": [ {"id": "CZ-CORR-A", "polygon": [[x,y], ...], "structure_soffit_rl": 77.20,
               "ceiling_rl": 76.00, "hanger_allowance": 0.05, "ceiling_allowance": 0.03,
               "band_order": ["FIRE","DUCT","PIPE","TRAY"], "min_vertical_clearance": 0.05,
               "min_side_clearance": 0.10, "access_side_clearance": 0.30} ],
   "runs":  [ {"id": "SA-22-01", "system": "SA", "family": "DUCT", "path": [[x,y],[x,y],...],
               "width": 1.0, "depth": 0.5, "insulation": 0.025, "top_rl": 77.120,
               "bottom_rl": 76.620, "sheet": "M-131", "needs_access": ["top"], "priority": 2},
              {"id": "CHWS-22-01", "system": "CHW", "family": "PIPE", "path": [...], "dn": 150,
               "od": 0.1683, "insulation": 0.032, "top_rl": 76.508, "bottom_rl": 76.340},
              {"id": "CT-22-01", "system": "ELEC", "family": "TRAY", "path": [...], "width": 0.6,
               "depth": 0.1, "top_rl": 76.230, "bottom_rl": 76.130},
              {"id": "DR-22-01", "system": "SAN", "family": "DRAIN", "path": [...], "dn": 100,
               "od": 0.110, "fall": "1:60", "invert_start_rl": 76.550, "invert_end_rl": 76.495} ]}

  zone fields    polygon (closed implicitly), structure_soffit_rl, ceiling_rl; optional
                 hanger_allowance (0.05), ceiling_allowance (0.03), min_vertical_clearance (0.05),
                 min_side_clearance (0.10), access_side_clearance (0.30), band_order (list, from the
                 soffit downwards; keys are families, plus "FIRE" for any run of the FIRE system).
  run fields     id (unique), system (system_id; runs of the SAME system are never checked
                 against each other), family DUCT | PIPE | TRAY | DRAIN | BUSWAY | CONDUIT | BRACE
                 (BRACE = the plan envelope of a seismic brace strut, width x depth, never LARGE;
                 declared with the SAME system as the run it braces, where it crosses a lane,
                 so it is checked against every other system but not against its own run),
                 path (>= 2 vertices, metres), size, insulation (m; number or {"thickness": m}),
                 RLs, optional sheet, needs_access (sides: top, bottom, left, right, side),
                 priority (1 = most fixed; a clash message names the other run as the one to move),
                 rl_basis "bare" (default) | "outside", band (overrides the band-order key),
                 element_ids (carried through, not checked).
  size           DUCT / TRAY / BUSWAY: width, depth (bare metal, m).
                 PIPE / DRAIN / CONDUIT: od (m); if only dn is given the nominal steel-pipe OD for
                 that DN is used (DN100 = 0.1143, DN150 = 0.1683 ...; otherwise dn / 1000).
                 Effective outside size = bare size + 2 x insulation on every side.
  RLs            top_rl / bottom_rl are the BARE element (bottom of duct, top of pipe); the checker
                 adds the insulation. Set "rl_basis": "outside" when the RLs already include it.
                 The RL span must agree with the size (10 mm tolerance) or the run gets a P2.
                 A run that changes level (a drop under a duct) is two runs with different ids.
  DRAIN          gravity drain: fall (gradient as 0.0167 or "1:60") and invert_start_rl /
                 invert_end_rl (linear between them along the path), or inverts (one per vertex).
                 Top of pipe = invert + od. Without inverts the drain is UNPLACED.
  unplaced       a run without RLs is UNPLACED: INFO at S3 for a small run, P2 at S6, P1 for a
                 LARGE run at either stage (large runs must have RLs even at S3).
  LARGE          duct width >= 0.6 m or depth >= 0.4 m; pipe / drain / conduit DN >= 100 or
                 od >= 0.1 m; tray width >= 0.45 m; every busway. Change with --large-* flags;
                 the thresholds in force are written into the report (CONFIG row).

db/crossings.json — the crossings register (planned crossings, the S6 sections behind them)
  [ {"id": "X-22-001", "runs": ["SA-22-01", "CHWS-22-01"], "at": [14.0, 1.6],
     "resolution": "pipe under duct", "over_run": "SA-22-01", "under_run": "CHWS-22-01",
     "over_bottom_rl": 76.620, "under_top_rl": 76.508, "clearance": 0.055,
     "section_sheet": "C-322", "status": "RESOLVED"} ]
  over_bottom_rl / under_top_rl are the bare RLs of the two runs at the crossing (a drain's
  invert + od for its top, its invert for its bottom); section_ref is accepted for section_sheet.
  An entry matches a computed crossing when it names the same two run ids within 0.5 m.

Checks and report rows (reports/crossings-<level>.csv)
------------------------------------------------------
columns: id, type, run_a, run_b, x, y, zone, vertical_check, required_depth, available_depth,
         register_status, section_sheet, severity, message
1. ENVELOPE  every placed run, in every zone its vertices / segment midpoints fall in:
             top + hanger_allowance <= structure_soffit_rl and bottom - ceiling_allowance >=
             ceiling_rl (effective sizes). Breach = P1. A sample point outside every zone uses
             --default-zone or is NO ZONE (P2). RL SPAN (P2) when the RLs disagree with the size.
             BAND ORDER (P2, warning) at a crossing where a run of an earlier band (e.g. FIRE)
             sits below a run of a later band of the zone's band_order.
2. CROSS     every pair of runs of different systems whose centreline segments intersect or
             touch, or whose outside envelopes overlap where the segments are not parallel.
             gap = upper run effective bottom - lower run effective top: OK if gap >=
             min_vertical_clearance (INFO), TIGHT if 0 <= gap < clearance (P1), CLASH if they
             overlap (P0), UNRESOLVED if either run has no RLs (INFO; the UNPLACED row carries
             the severity). Depth budget at every crossing, placed or not: required_depth = the
             two effective depths + clearance + hanger_allowance + ceiling_allowance vs
             available_depth = structure_soffit_rl - ceiling_rl; required > available = P0.
             A LARGE x LARGE crossing needs a register entry with a section_sheet and status
             RESOLVED, otherwise NEEDS SECTION (P1) even when the gap is OK; a register entry
             whose over / under RLs differ from the run RLs at that point by more than 5 mm is
             REGISTER MISMATCH (P1); a register entry that matches no computed crossing is
             STALE (P2). Crossing above a gravity drain is a normal crossing; crossing below it
             is checked against the drain invert at that chainage.
3. PARALLEL  two runs of different systems whose segments are within 10 degrees of parallel and
             overlap in extent by >= 1.0 m, with the horizontal gap between their outside
             envelopes below min_side_clearance (or access_side_clearance on a side named in
             needs_access): TOO CLOSE (P1) when they overlap vertically or the vertical gap is
             below min_vertical_clearance; otherwise a stacked parallel run, INFO with the gap.
4. DRAIN     the invert of a DRAIN falls continuously along the path at >= fall: FALL OK (INFO)
             or FALL FAIL (P1); a drain without a fall value is checked for monotonic fall only
             and gets a P2.
5. UNPLACED  runs without RLs, severity per the stage rule above.
Severities: P0 = CLASH or depth-budget FAIL; P1 = NEEDS SECTION, REGISTER MISMATCH, TOO CLOSE,
TIGHT, envelope breach, FALL FAIL, large run unplaced; P2 = STALE, BAND ORDER, NO ZONE, RL SPAN,
small run unplaced at S6; INFO otherwise. Exit code 1 if any P0 / P1 row exists.

Commands
--------
  check   --routes db/services-routes.json [--crossings db/crossings.json] [--stage S3|S6]
          [--out reports/crossings-<level>.csv] [--svg reports/crossings-<level>.svg]
          [--default-zone soffit=77.2,ceiling=76.0[,hanger=0.05,ceiling_allowance=0.03,
           vclear=0.05,side=0.10,access=0.30]] [--large-duct-width 0.6] [--large-duct-depth 0.4]
          [--large-pipe-dn 100] [--large-pipe-od 0.1] [--large-tray-width 0.45]
  summary <report.csv>        counts per severity, per type and per verdict
  demo    <dir>               write a sample level (db/ + crossings register) into <dir>, run
                              check --stage S6 on it and print the report
  selftest                    run the demo in a temp dir and assert the expected findings and
                              the geometry helpers
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import math
import os
import sys
import tempfile
from collections import Counter

SCRIPT_VERSION = "coord_check 1.0"
EPS = 0.0005            # m — RLs are to 3 decimals; a half-millimetre is "equal"
GEOM_EPS = 1e-6         # m — geometric coincidence
PARALLEL_DEG = 10.0     # segments closer than this to parallel are checked as PARALLEL, not CROSS
PARALLEL_MIN_OVERLAP = 1.0   # m
REGISTER_MATCH_RADIUS = 0.5  # m
REGISTER_RL_TOL = 0.005      # m
RL_SPAN_TOL = 0.010          # m

FAMILIES = ("DUCT", "PIPE", "TRAY", "DRAIN", "BUSWAY", "CONDUIT", "BRACE")
RECT_FAMILIES = ("DUCT", "TRAY", "BUSWAY", "BRACE")
ROUND_FAMILIES = ("PIPE", "DRAIN", "CONDUIT")
FIRE_SYSTEMS = ("FIRE", "FS", "FH", "SPR", "SPK", "FHR", "SPRINKLER", "HYDRANT")
SEVERITIES = ("P0", "P1", "P2", "INFO")
STAGES = ("S3", "S6")
COLUMNS = ["id", "type", "run_a", "run_b", "x", "y", "zone", "vertical_check", "required_depth",
           "available_depth", "register_status", "section_sheet", "severity", "message"]
TYPE_PREFIX = {"CONFIG": "CFG", "ENVELOPE": "ENV", "CROSS": "CRS", "PARALLEL": "PAR", "DRAIN": "DRN",
               "UNPLACED": "UNP"}
TYPE_ORDER = ["CONFIG", "ENVELOPE", "CROSS", "PARALLEL", "DRAIN", "UNPLACED"]

ZONE_DEFAULTS = {"hanger_allowance": 0.05, "ceiling_allowance": 0.03, "min_vertical_clearance": 0.05,
                 "min_side_clearance": 0.10, "access_side_clearance": 0.30}

# Nominal steel-pipe outside diameters (m) used only when a round run gives dn without od.
STEEL_OD = {15: 0.0213, 20: 0.0269, 25: 0.0337, 32: 0.0424, 40: 0.0483, 50: 0.0603, 65: 0.0761,
            80: 0.0889, 100: 0.1143, 125: 0.1397, 150: 0.1683, 200: 0.2191, 250: 0.2731, 300: 0.3239,
            350: 0.3556, 400: 0.4064, 450: 0.4572, 500: 0.508, 600: 0.6096}

FAMILY_COLOUR = {"DUCT": "#2b6cb0", "PIPE": "#2f855a", "TRAY": "#dd6b20", "DRAIN": "#8b5a2b",
                 "BUSWAY": "#6b46c1", "CONDUIT": "#4a5568", "BRACE": "#805ad5", "FIRE": "#c53030"}
SEVERITY_COLOUR = {"P0": "#c53030", "P1": "#dd6b20", "P2": "#718096", "INFO": "#718096", "OK": "#2f855a"}


# ----------------------------------------------------------------------------- small helpers

def fmt(v) -> str:
    """Format a length / RL to 3 decimals for the report; blank for None."""
    if v is None or v == "":
        return ""
    return f"{float(v):.3f}"


def worst(*sevs: str) -> str:
    """The most severe of the given severities (P0 < P1 < P2 < INFO)."""
    order = {s: i for i, s in enumerate(SEVERITIES)}
    return min((s for s in sevs if s), key=lambda s: order[s])


def parse_fall(v) -> float | None:
    """Accept a gradient as a number (0.0167) or a ratio string ("1:60", "1/60")."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("/", ":")
    if ":" in s:
        num, den = s.split(":", 1)
        return float(num) / float(den)
    return float(s)


def gradient_text(g: float) -> str:
    """0.01833 -> '1:54.5 (0.0183)'."""
    if g <= 0:
        return f"{g:.4f} (no fall)"
    return f"1:{1.0 / g:.1f} ({g:.4f})"


# ----------------------------------------------------------------------------- geometry (plan, metres)

def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def seg_length(a, b) -> float:
    return dist(a, b)


def polyline_length(path) -> float:
    return sum(dist(path[i], path[i + 1]) for i in range(len(path) - 1))


def closest_point_on_segment(p, a, b):
    """The point of segment a-b closest to p, and its parameter t in [0, 1]."""
    d = sub(b, a)
    L2 = dot(d, d)
    if L2 < GEOM_EPS ** 2:
        return a, 0.0
    t = max(0.0, min(1.0, dot(sub(p, a), d) / L2))
    return (a[0] + t * d[0], a[1] + t * d[1]), t


def segment_intersection(p1, p2, p3, p4):
    """
    Intersection of segments p1-p2 and p3-p4.
    Returns (kind, point): kind is "cross" (proper crossing), "touch" (an endpoint lies on the
    other segment, T-junctions included), "collinear" (overlapping on one line; point = the middle
    of the overlap) or "none" (point None). Collinear runs are a PARALLEL matter, not a crossing.
    """
    r = sub(p2, p1)
    s = sub(p4, p3)
    denom = cross(r, s)
    qp = sub(p3, p1)
    if abs(denom) < GEOM_EPS:
        if abs(cross(qp, r)) > GEOM_EPS:
            return "none", None                       # parallel, distinct lines
        rr = dot(r, r)
        if rr < GEOM_EPS ** 2:
            return "none", None
        t0 = dot(qp, r) / rr
        t1 = t0 + dot(s, r) / rr
        lo, hi = max(0.0, min(t0, t1)), min(1.0, max(t0, t1))
        if lo > hi + GEOM_EPS:
            return "none", None                       # collinear but disjoint
        tm = (lo + hi) / 2
        return "collinear", (p1[0] + tm * r[0], p1[1] + tm * r[1])
    t = cross(qp, s) / denom
    u = cross(qp, r) / denom
    tol = 1e-9
    if -tol <= t <= 1 + tol and -tol <= u <= 1 + tol:
        pt = (p1[0] + t * r[0], p1[1] + t * r[1])
        touching = min(t, 1 - t) < 1e-7 or min(u, 1 - u) < 1e-7
        return ("touch" if touching else "cross"), pt
    return "none", None


def closest_points_segments(p1, p2, p3, p4):
    """Closest pair of points between two segments and their distance (endpoint-based, exact for
    non-intersecting segments because the minimum is attained at an endpoint of one of them)."""
    best = None
    for p, a, b in ((p1, p3, p4), (p2, p3, p4)):
        q, _ = closest_point_on_segment(p, a, b)
        d = dist(p, q)
        if best is None or d < best[0]:
            best = (d, p, q)
    for p, a, b in ((p3, p1, p2), (p4, p1, p2)):
        q, _ = closest_point_on_segment(p, a, b)
        d = dist(p, q)
        if best is None or d < best[0]:
            best = (d, q, p)
    return best  # (distance, point on seg 1, point on seg 2)


def angle_between_segments_deg(p1, p2, p3, p4) -> float:
    """Angle 0..90 degrees between two segment directions (direction-agnostic)."""
    a, b = sub(p2, p1), sub(p4, p3)
    la, lb = math.hypot(*a), math.hypot(*b)
    if la < GEOM_EPS or lb < GEOM_EPS:
        return 90.0
    c = abs(dot(a, b) / (la * lb))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def point_on_segment(p, a, b, tol=GEOM_EPS) -> bool:
    q, _ = closest_point_on_segment(p, a, b)
    return dist(p, q) <= tol


def point_in_polygon(p, poly, tol=GEOM_EPS) -> bool:
    """Ray casting; a point on the boundary counts as inside (runs hug zone edges). Works for
    concave polygons; the polygon is closed implicitly."""
    n = len(poly)
    if n < 3:
        return False
    for i in range(n):
        if point_on_segment(p, poly[i], poly[(i + 1) % n], tol):
            return True
    inside = False
    x, y = p
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def polygon_centroid(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def chainage_of_point(path, p) -> float:
    """Distance along the polyline to the point of it closest to p."""
    best = (None, 0.0)
    run = 0.0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        q, t = closest_point_on_segment(p, a, b)
        d = dist(p, q)
        if best[0] is None or d < best[0]:
            best = (d, run + t * seg_length(a, b))
        run += seg_length(a, b)
    return best[1]


def left_of(a_start, a_end, p) -> bool:
    """True when p lies to the left of the directed segment a_start -> a_end (y up, plan view)."""
    return cross(sub(a_end, a_start), sub(p, a_start)) > 0


# ----------------------------------------------------------------------------- data model

class Thresholds:
    """The LARGE-run thresholds (see module docstring); overridable from the command line."""

    def __init__(self, duct_width=0.6, duct_depth=0.4, pipe_dn=100, pipe_od=0.1, tray_width=0.45):
        self.duct_width = float(duct_width)
        self.duct_depth = float(duct_depth)
        self.pipe_dn = float(pipe_dn)
        self.pipe_od = float(pipe_od)
        self.tray_width = float(tray_width)

    def text(self) -> str:
        return (f"LARGE = duct width >= {self.duct_width:.3f} or depth >= {self.duct_depth:.3f}; "
                f"pipe/drain/conduit DN >= {self.pipe_dn:.0f} or od >= {self.pipe_od:.3f}; "
                f"tray width >= {self.tray_width:.3f}; every busway")


class Zone:
    """A ceiling-zone polygon with its vertical envelope and clearance rules."""

    def __init__(self, d: dict, synthetic=False):
        self.id = str(d.get("id") or "DEFAULT")
        self.polygon = [(float(p[0]), float(p[1])) for p in d.get("polygon", [])]
        if not synthetic and len(self.polygon) < 3:
            raise SystemExit(f"zone {self.id}: polygon needs at least 3 vertices")
        try:
            self.soffit = float(d["structure_soffit_rl"])
            self.ceiling = float(d["ceiling_rl"])
        except (KeyError, TypeError, ValueError):
            raise SystemExit(f"zone {self.id}: structure_soffit_rl and ceiling_rl are required numbers")
        if self.soffit <= self.ceiling:
            raise SystemExit(f"zone {self.id}: structure_soffit_rl must be above ceiling_rl")
        for k, v in ZONE_DEFAULTS.items():
            setattr(self, k, float(d.get(k, v)))
        self.band_order = [str(b).upper() for b in (d.get("band_order") or [])]
        self.synthetic = synthetic

    @property
    def available(self) -> float:
        return self.soffit - self.ceiling

    def contains(self, p) -> bool:
        return (not self.synthetic) and point_in_polygon(p, self.polygon)


class Run:
    """One services run: a plan polyline with an effective outside envelope and a vertical band."""

    def __init__(self, d: dict):
        self.raw = d
        self.id = str(d.get("id") or "").strip()
        if not self.id:
            raise SystemExit("every run needs an id")
        self.system = str(d.get("system") or "").strip().upper()
        if not self.system:
            raise SystemExit(f"run {self.id}: system is required")
        self.family = str(d.get("family") or "").strip().upper()
        if self.family not in FAMILIES:
            raise SystemExit(f"run {self.id}: family must be one of {', '.join(FAMILIES)}")
        path = d.get("path") or []
        if len(path) < 2:
            raise SystemExit(f"run {self.id}: path needs at least 2 vertices")
        self.path = [(float(p[0]), float(p[1])) for p in path]
        self.sheet = str(d.get("sheet") or "")
        self.priority = d.get("priority")
        self.needs_access = [str(s).lower() for s in (d.get("needs_access") or [])]
        self.rl_basis = str(d.get("rl_basis") or "bare").lower()
        self.band = str(d.get("band") or "").upper() or None
        self.element_ids = list(d.get("element_ids") or [])
        ins = d.get("insulation", 0) or 0
        if isinstance(ins, dict):
            ins = ins.get("thickness", (ins.get("thickness_mm") or 0) / 1000.0)
        self.insulation = float(ins)
        self.dn = d.get("dn")
        self.od = d.get("od")
        # bare sizes
        if self.family in RECT_FAMILIES:
            try:
                self.width = float(d["width"])
                self.depth = float(d["depth"])
            except (KeyError, TypeError, ValueError):
                raise SystemExit(f"run {self.id} ({self.family}): width and depth are required")
            self.od_source = ""
        else:
            if self.od is not None:
                self.od = float(self.od)
                self.od_source = "od"
            elif self.dn is not None:
                dn = int(round(float(self.dn)))
                self.od = STEEL_OD.get(dn, dn / 1000.0)
                self.od_source = f"od from DN{dn} ({'steel table' if dn in STEEL_OD else 'dn/1000'})"
            else:
                raise SystemExit(f"run {self.id} ({self.family}): od or dn is required")
            self.width = self.depth = self.od
        self.eff_w = self.width + 2 * self.insulation   # horizontal outside size
        self.eff_d = self.depth + 2 * self.insulation   # vertical outside size
        self.half_w = self.eff_w / 2
        # vertical placement
        self.top_rl = d.get("top_rl")
        self.bottom_rl = d.get("bottom_rl")
        self.fall = parse_fall(d.get("fall"))
        self.inverts = None
        if self.family == "DRAIN":
            invs = d.get("inverts")
            if invs:
                if len(invs) != len(self.path):
                    raise SystemExit(f"run {self.id}: inverts must have one value per path vertex")
                self.inverts = [float(v) for v in invs]
            elif d.get("invert_start_rl") is not None and d.get("invert_end_rl") is not None:
                s, e = float(d["invert_start_rl"]), float(d["invert_end_rl"])
                self.inverts = self._linear_profile(s, e)
            elif d.get("invert_start_rl") is not None and self.fall is not None:
                s = float(d["invert_start_rl"])
                self.inverts = self._linear_profile(s, s - self.fall * polyline_length(self.path))
            self.top_rl = self.bottom_rl = None
        else:
            if self.top_rl is not None and self.bottom_rl is not None:
                self.top_rl, self.bottom_rl = float(self.top_rl), float(self.bottom_rl)
                if self.top_rl < self.bottom_rl:
                    raise SystemExit(f"run {self.id}: top_rl is below bottom_rl")
            else:
                self.top_rl = self.bottom_rl = None

    # -- profile helpers
    def _linear_profile(self, start_rl: float, end_rl: float) -> list[float]:
        total = polyline_length(self.path)
        out, run = [], 0.0
        for i, _ in enumerate(self.path):
            if i:
                run += dist(self.path[i - 1], self.path[i])
            out.append(start_rl - (start_rl - end_rl) * (run / total if total else 0))
        return out

    def invert_at(self, p) -> float:
        """Drain invert at the chainage of the point of the path closest to p."""
        s = chainage_of_point(self.path, p)
        run = 0.0
        for i in range(len(self.path) - 1):
            L = dist(self.path[i], self.path[i + 1])
            if s <= run + L + GEOM_EPS or i == len(self.path) - 2:
                t = 0.0 if L < GEOM_EPS else max(0.0, min(1.0, (s - run) / L))
                return self.inverts[i] + (self.inverts[i + 1] - self.inverts[i]) * t
            run += L
        return self.inverts[-1]

    # -- placement
    @property
    def placed(self) -> bool:
        if self.family == "DRAIN":
            return self.inverts is not None
        return self.top_rl is not None

    def eff_top_at(self, p) -> float:
        """Effective (outside of insulation) top RL at plan point p."""
        if self.family == "DRAIN":
            return self.invert_at(p) + self.od + self.insulation
        return self.top_rl if self.rl_basis == "outside" else self.top_rl + self.insulation

    def eff_bottom_at(self, p) -> float:
        if self.family == "DRAIN":
            return self.invert_at(p) - self.insulation
        return self.bottom_rl if self.rl_basis == "outside" else self.bottom_rl - self.insulation

    def bare_top_at(self, p) -> float:
        if self.family == "DRAIN":
            return self.invert_at(p) + self.od
        return self.top_rl - self.insulation if self.rl_basis == "outside" else self.top_rl

    def bare_bottom_at(self, p) -> float:
        if self.family == "DRAIN":
            return self.invert_at(p)
        return self.bottom_rl + self.insulation if self.rl_basis == "outside" else self.bottom_rl

    def rl_span_expected(self) -> float:
        return self.eff_d if self.rl_basis == "outside" else self.depth

    # -- classification
    def is_fire(self) -> bool:
        return self.system in FIRE_SYSTEMS or self.system.startswith("FIRE")

    def band_key(self) -> str:
        return self.band or ("FIRE" if self.is_fire() else self.family)

    def is_large(self, thr: Thresholds) -> bool:
        if self.family == "BRACE":
            return False
        if self.family == "DUCT":
            return self.width >= thr.duct_width - EPS or self.depth >= thr.duct_depth - EPS
        if self.family == "BUSWAY":
            return True
        if self.family == "TRAY":
            return self.width >= thr.tray_width - EPS
        dn_large = self.dn is not None and float(self.dn) >= thr.pipe_dn
        return dn_large or self.od >= thr.pipe_od - EPS

    def size_text(self) -> str:
        if self.family in RECT_FAMILIES:
            s = f"{self.width * 1000:.0f}x{self.depth * 1000:.0f}"
        else:
            s = f"DN{int(round(float(self.dn)))}" if self.dn is not None else f"od {self.od:.4f}"
        if self.insulation:
            s += f" +{self.insulation * 1000:.0f} ins"
        return s

    def segments(self):
        return [(self.path[i], self.path[i + 1]) for i in range(len(self.path) - 1)]

    def sample_points(self):
        """Vertices and segment midpoints — the points used to find a run's zones."""
        pts = list(self.path)
        for a, b in self.segments():
            pts.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
        return pts

    def colour(self) -> str:
        return FAMILY_COLOUR["FIRE"] if self.is_fire() else FAMILY_COLOUR[self.family]


class RegisterEntry:
    """One planned crossing from db/crossings.json."""

    def __init__(self, d: dict):
        self.raw = d
        self.id = str(d.get("id") or "")
        runs = d.get("runs") or []
        if len(runs) != 2:
            raise SystemExit(f"crossing {self.id or '?'}: runs must list exactly two run ids")
        self.runs = frozenset(str(r) for r in runs)
        at = d.get("at") or []
        if len(at) != 2:
            raise SystemExit(f"crossing {self.id}: at must be [x, y]")
        self.at = (float(at[0]), float(at[1]))
        self.resolution = str(d.get("resolution") or "")
        self.over_run = str(d.get("over_run") or "")
        self.under_run = str(d.get("under_run") or "")
        self.over_bottom_rl = d.get("over_bottom_rl")
        self.under_top_rl = d.get("under_top_rl")
        self.clearance = d.get("clearance")
        self.section_sheet = str(d.get("section_sheet") or d.get("section_ref") or "")
        self.status = str(d.get("status") or "").strip().upper()
        self.matched = False


# ----------------------------------------------------------------------------- loading

def load_routes(path: str):
    """Read services-routes.json -> (level, zones, runs). Units must be metres."""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    units = str(d.get("units") or "m").lower()
    if units != "m":
        raise SystemExit(f"{path}: units must be 'm' (metres), got '{units}'")
    level = str(d.get("level") or "L00")
    zones = [Zone(z) for z in d.get("zones") or []]
    runs = [Run(r) for r in d.get("runs") or []]
    ids = Counter(r.id for r in runs)
    dupes = sorted(k for k, c in ids.items() if c > 1)
    if dupes:
        raise SystemExit(f"{path}: duplicate run ids {dupes}")
    zids = Counter(z.id for z in zones)
    dupes = sorted(k for k, c in zids.items() if c > 1)
    if dupes:
        raise SystemExit(f"{path}: duplicate zone ids {dupes}")
    return level, zones, runs


def load_crossings(path: str | None) -> list[RegisterEntry]:
    if not path:
        return []
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, dict):
        d = d.get("crossings") or []
    return [RegisterEntry(e) for e in d]


def parse_default_zone(spec: str | None) -> Zone | None:
    """--default-zone soffit=77.2,ceiling=76.0[,hanger=..,ceiling_allowance=..,vclear=..,side=..,access=..]"""
    if not spec:
        return None
    keys = {"soffit": "structure_soffit_rl", "ceiling": "ceiling_rl", "hanger": "hanger_allowance",
            "ceiling_allowance": "ceiling_allowance", "vclear": "min_vertical_clearance",
            "side": "min_side_clearance", "access": "access_side_clearance"}
    d = {"id": "DEFAULT"}
    for part in spec.split(","):
        if not part.strip():
            continue
        if "=" not in part:
            raise SystemExit(f"--default-zone: expected key=value, got '{part}'")
        k, v = part.split("=", 1)
        k = k.strip().lower()
        if k not in keys:
            raise SystemExit(f"--default-zone: unknown key '{k}' (use {', '.join(keys)})")
        d[keys[k]] = float(v)
    if "structure_soffit_rl" not in d or "ceiling_rl" not in d:
        raise SystemExit("--default-zone needs at least soffit=.. and ceiling=..")
    return Zone(d, synthetic=True)


def zone_at(p, zones: list[Zone], default: Zone | None) -> Zone | None:
    """The first zone whose polygon contains p, else the default zone (may be None)."""
    for z in zones:
        if z.contains(p):
            return z
    return default


# ----------------------------------------------------------------------------- findings

def finding(type_, severity, run_a="", run_b="", x=None, y=None, zone="", vertical_check="",
            required_depth=None, available_depth=None, register_status="", section_sheet="", message=""):
    """One report row (ids are assigned after all checks, in report order)."""
    return {"id": "", "type": type_, "run_a": run_a, "run_b": run_b, "x": fmt(x), "y": fmt(y),
            "zone": zone, "vertical_check": vertical_check, "required_depth": fmt(required_depth),
            "available_depth": fmt(available_depth), "register_status": register_status,
            "section_sheet": section_sheet, "severity": severity, "message": message}


def assign_ids(rows: list[dict]) -> list[dict]:
    """Order rows by check type and number them ENV-001, CRS-001 ... within each type."""
    order = {t: i for i, t in enumerate(TYPE_ORDER)}

    def num(s):
        return float(s) if s else 0.0

    rows.sort(key=lambda r: (order.get(r["type"], 99), r["run_a"], r["run_b"], num(r["x"]), num(r["y"])))
    counters: Counter = Counter()
    for r in rows:
        counters[r["type"]] += 1
        r["id"] = f"{TYPE_PREFIX.get(r['type'], r['type'][:3])}-{counters[r['type']]:03d}"
    return rows


class Context:
    """Everything a check needs: runs, zones, register, stage and thresholds."""

    def __init__(self, level, zones, runs, register, stage, thr, default_zone):
        self.level = level
        self.zones = zones
        self.runs = runs
        self.register = register
        self.stage = stage
        self.thr = thr
        self.default_zone = default_zone
        self.parallel_pairs_checked = 0
        self.crossings_checked = 0

    def zone_at(self, p):
        return zone_at(p, self.zones, self.default_zone)


# ----------------------------------------------------------------------------- 1. ENVELOPE

def check_envelope(ctx: Context) -> list[dict]:
    """Every placed run must sit inside the vertical envelope of every zone it passes through."""
    rows = []
    for run in ctx.runs:
        if not run.placed:
            continue
        if run.family != "DRAIN":
            span = run.top_rl - run.bottom_rl
            expected = run.rl_span_expected()
            if abs(span - expected) > RL_SPAN_TOL:
                p = run.path[0]
                z = ctx.zone_at(p)
                rows.append(finding("ENVELOPE", "P2", run.id, "", p[0], p[1], z.id if z else "",
                                    "RL SPAN",
                                    message=f"top_rl - bottom_rl = {span:.3f} but the {run.rl_basis} size is "
                                            f"{expected:.3f} ({run.size_text()}); fix the RLs or set rl_basis"))
        by_zone: dict[str, list] = {}
        zone_objs: dict[str, Zone] = {}
        outside = []
        for p in run.sample_points():
            z = ctx.zone_at(p)
            if z is None:
                outside.append(p)
                continue
            by_zone.setdefault(z.id, []).append(p)
            zone_objs[z.id] = z
        if outside:
            p = outside[0]
            rows.append(finding("ENVELOPE", "P2", run.id, "", p[0], p[1], "", "NO ZONE",
                                message=f"{len(outside)} of {len(run.sample_points())} sample points lie outside "
                                        f"every zone (first at {p[0]:.3f}, {p[1]:.3f}); add the zone or pass "
                                        f"--default-zone"))
        for zid, pts in by_zone.items():
            z = zone_objs[zid]
            top = max(run.eff_top_at(p) for p in pts)
            bot = min(run.eff_bottom_at(p) for p in pts)
            top_margin = z.soffit - (top + z.hanger_allowance)
            bot_margin = (bot - z.ceiling_allowance) - z.ceiling
            breach = top_margin < -EPS or bot_margin < -EPS
            required = (top - bot) + z.hanger_allowance + z.ceiling_allowance
            parts = [f"top {top:.3f} + hanger {z.hanger_allowance:.3f} vs soffit {z.soffit:.3f} "
                     f"(margin {top_margin:+.3f})",
                     f"bottom {bot:.3f} - ceiling allowance {z.ceiling_allowance:.3f} vs ceiling {z.ceiling:.3f} "
                     f"(margin {bot_margin:+.3f})"]
            msg = ("ENVELOPE BREACH: " if breach else "inside envelope: ") + "; ".join(parts)
            if z.synthetic:
                msg += " [default zone]"
            p = pts[0]
            rows.append(finding("ENVELOPE", "P1" if breach else "INFO", run.id, "", p[0], p[1], z.id,
                                "BREACH" if breach else "OK", required, z.available, message=msg))
    return rows


# ----------------------------------------------------------------------------- 2. CROSS

def find_crossings(a: Run, b: Run) -> list[tuple]:
    """All distinct crossing points of two runs: centreline intersections / touches, plus places
    where the outside envelopes overlap although the centrelines miss (non-parallel segments).
    Returns [(kind, point)] with nearby candidates merged (one crossing per location)."""
    cands = []
    merge_r = max(REGISTER_MATCH_RADIUS, a.half_w + b.half_w)
    for sa in a.segments():
        for sb in b.segments():
            kind, pt = segment_intersection(sa[0], sa[1], sb[0], sb[1])
            if kind in ("cross", "touch"):
                cands.append((kind, pt))
                continue
            if kind == "collinear":
                continue
            if angle_between_segments_deg(sa[0], sa[1], sb[0], sb[1]) < PARALLEL_DEG:
                continue
            d, p, q = closest_points_segments(sa[0], sa[1], sb[0], sb[1])
            if d < a.half_w + b.half_w - GEOM_EPS:
                cands.append(("envelope", ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)))
    rank = {"cross": 0, "touch": 1, "envelope": 2}
    cands.sort(key=lambda c: rank[c[0]])
    merged: list[tuple] = []
    for kind, pt in cands:
        if any(dist(pt, m[1]) <= merge_r for m in merged):
            continue
        merged.append((kind, pt))
    merged.sort(key=lambda c: (c[1][0], c[1][1]))
    return merged


def match_register(ctx: Context, a: Run, b: Run, pt) -> RegisterEntry | None:
    """The register entry naming these two runs within REGISTER_MATCH_RADIUS of pt (nearest)."""
    key = frozenset((a.id, b.id))
    best = None
    for e in ctx.register:
        if e.runs != key:
            continue
        d = dist(e.at, pt)
        if d <= REGISTER_MATCH_RADIUS and (best is None or d < best[0]):
            best = (d, e)
    return best[1] if best else None


def register_check(ctx: Context, a: Run, b: Run, pt, e: RegisterEntry | None, both_large: bool,
                   upper: Run | None, lower: Run | None):
    """Register status for one crossing -> (status, section_sheet, severity, note)."""
    if e is None:
        if both_large:
            return ("NEEDS SECTION", "", "P1",
                    "LARGE x LARGE crossing has no register entry: add one with a C-3xx section and status RESOLVED")
        return "NOT REQUIRED", "", "INFO", ""
    e.matched = True
    if e.status != "RESOLVED" or not e.section_sheet:
        why = []
        if e.status != "RESOLVED":
            why.append(f"status {e.status or 'blank'}")
        if not e.section_sheet:
            why.append("no section_sheet")
        if both_large:
            return "NEEDS SECTION", e.section_sheet, "P1", f"register {e.id}: {', '.join(why)}"
        return e.status or "OPEN", e.section_sheet, "INFO", f"register {e.id}: {', '.join(why)}"
    problems = []
    if a.placed and b.placed:
        if e.over_run and e.under_run and {e.over_run, e.under_run} == {a.id, b.id}:
            if upper is not None and e.over_run != upper.id:
                problems.append(f"register says {e.over_run} over {e.under_run} but the RLs put {upper.id} over {lower.id}")
        elif e.over_run or e.under_run:
            problems.append("over_run / under_run do not name these two runs")
        runs_by_id = {a.id: a, b.id: b}
        over = runs_by_id.get(e.over_run)
        under = runs_by_id.get(e.under_run)
        if over is not None and e.over_bottom_rl is not None:
            actual = over.bare_bottom_at(pt)
            if abs(float(e.over_bottom_rl) - actual) > REGISTER_RL_TOL + 1e-9:
                problems.append(f"over_bottom_rl {float(e.over_bottom_rl):.3f} vs run {over.id} bottom {actual:.3f} "
                                f"(delta {float(e.over_bottom_rl) - actual:+.3f})")
        if under is not None and e.under_top_rl is not None:
            actual = under.bare_top_at(pt)
            if abs(float(e.under_top_rl) - actual) > REGISTER_RL_TOL + 1e-9:
                problems.append(f"under_top_rl {float(e.under_top_rl):.3f} vs run {under.id} top {actual:.3f} "
                                f"(delta {float(e.under_top_rl) - actual:+.3f})")
    if problems:
        return "REGISTER MISMATCH", e.section_sheet, "P1", f"register {e.id} ({e.section_sheet}): " + "; ".join(problems)
    return "RESOLVED", e.section_sheet, "INFO", f"register {e.id} RESOLVED ({e.section_sheet})"


def priority_hint(a: Run, b: Run) -> str:
    """Which run should move at a clash: the one with the larger priority number (1 = most fixed)."""
    pa = a.priority if a.priority is not None else 99
    pb = b.priority if b.priority is not None else 99
    if pa == pb:
        return ""
    mover = a if pa > pb else b
    return f"; move {mover.id} (priority {mover.priority if mover.priority is not None else 'none'})"


def check_crossings(ctx: Context) -> list[dict]:
    """Every crossing of two runs of different systems: vertical gap, depth budget, register,
    band order. Also the STALE register entries afterwards."""
    rows = []
    runs = ctx.runs
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            a, b = runs[i], runs[j]
            if a.system == b.system:
                continue
            for kind, pt in find_crossings(a, b):
                ctx.crossings_checked += 1
                rows.extend(crossing_rows(ctx, a, b, pt, kind))
    for e in ctx.register:
        if not e.matched:
            ra, rb = sorted(e.runs)
            rows.append(finding("CROSS", "P2", ra, rb, e.at[0], e.at[1], "", "-", register_status="STALE",
                                section_sheet=e.section_sheet,
                                message=f"register {e.id} ({ra} x {rb} at {e.at[0]:.3f}, {e.at[1]:.3f}) matches no "
                                        f"computed crossing within {REGISTER_MATCH_RADIUS} m: routes changed or "
                                        f"entry mislocated; retire or relocate it"))
    return rows


def crossing_rows(ctx: Context, a: Run, b: Run, pt, kind: str) -> list[dict]:
    """The CROSS row (and a possible BAND ORDER row) for one crossing point."""
    z = ctx.zone_at(pt)
    clearance = z.min_vertical_clearance if z else ZONE_DEFAULTS["min_vertical_clearance"]
    hanger = z.hanger_allowance if z else ZONE_DEFAULTS["hanger_allowance"]
    ceil_allow = z.ceiling_allowance if z else ZONE_DEFAULTS["ceiling_allowance"]
    both_large = a.is_large(ctx.thr) and b.is_large(ctx.thr)
    parts = []
    sev = "INFO"
    upper = lower = None
    # vertical
    if a.placed and b.placed:
        ta, ba = a.eff_top_at(pt), a.eff_bottom_at(pt)
        tb, bb = b.eff_top_at(pt), b.eff_bottom_at(pt)
        if ba >= tb - EPS:
            upper, lower, gap = a, b, ba - tb
        elif bb >= ta - EPS:
            upper, lower, gap = b, a, bb - ta
        else:
            gap = -(min(ta, tb) - max(ba, bb))
        if upper is None:
            verdict, vsev = "CLASH", "P0"
            parts.append(f"CLASH: {a.id} ({ba:.3f}..{ta:.3f}) and {b.id} ({bb:.3f}..{tb:.3f}) overlap by "
                         f"{-gap:.3f}{priority_hint(a, b)}")
        elif gap < clearance - EPS:
            verdict, vsev = "TIGHT", "P1"
            parts.append(f"TIGHT: {upper.id} over {lower.id}, gap {gap:.3f} < clearance {clearance:.3f}")
        else:
            verdict, vsev = "OK", "INFO"
            parts.append(f"{upper.id} over {lower.id}, gap {gap:.3f} >= {clearance:.3f}")
        for r in (a, b):
            if r.family == "DRAIN":
                parts.append(f"{r.id} invert {r.invert_at(pt):.3f} at chainage {chainage_of_point(r.path, pt):.2f} m")
    else:
        verdict, vsev = "UNRESOLVED", "INFO"
        missing = [r.id for r in (a, b) if not r.placed]
        parts.append(f"UNRESOLVED: no RLs on {', '.join(missing)}")
    sev = worst(sev, vsev)
    # depth budget
    required = a.eff_d + b.eff_d + clearance + hanger + ceil_allow
    available = z.available if z else None
    if z is None:
        parts.append(f"no zone at this point: depth budget {required:.3f} not checked (NO ZONE)")
        dsev = "P2"
    elif required > available + EPS:
        parts.append(f"DEPTH BUDGET FAIL: {a.eff_d:.3f} + {b.eff_d:.3f} + clearance {clearance:.3f} + hanger "
                     f"{hanger:.3f} + ceiling {ceil_allow:.3f} = {required:.3f} > available {available:.3f} in {z.id}")
        dsev = "P0"
    else:
        parts.append(f"depth budget {required:.3f} <= {available:.3f}")
        dsev = "INFO"
    sev = worst(sev, dsev)
    # register
    e = match_register(ctx, a, b, pt)
    rstatus, section, rsev, rnote = register_check(ctx, a, b, pt, e, both_large, upper, lower)
    if rnote:
        parts.append(rnote)
    sev = worst(sev, rsev)
    if kind == "envelope":
        parts.append("centrelines do not meet; outside envelopes overlap")
    if both_large:
        parts.append("LARGE x LARGE")
    rows = [finding("CROSS", sev, a.id, b.id, pt[0], pt[1], z.id if z else "", verdict, required, available,
                    rstatus, section, "; ".join(parts))]
    # band order (warning)
    if z and z.band_order and upper is not None:
        ku, kl = upper.band_key(), lower.band_key()
        if ku in z.band_order and kl in z.band_order and z.band_order.index(ku) > z.band_order.index(kl):
            rows.append(finding("ENVELOPE", "P2", a.id, b.id, pt[0], pt[1], z.id, "BAND ORDER",
                                message=f"{lower.id} ({kl}) is below {upper.id} ({ku}) but the zone band order is "
                                        f"{' > '.join(z.band_order)} (soffit downwards)"))
    return rows


# ----------------------------------------------------------------------------- 3. PARALLEL

def side_name(run: Run, seg, p) -> str:
    """'left' or 'right' of run's directed segment for the neighbour point p."""
    return "left" if left_of(seg[0], seg[1], p) else "right"


def needs_side_access(run: Run, side: str) -> bool:
    return any(s in (side, "side", "sides", "both") for s in run.needs_access)


def parallel_candidates(a: Run, b: Run):
    """Segment pairs of a and b that are near-parallel with >= 1 m of overlapping extent.
    Yields (overlap_len, centreline_separation, midpoint, seg_a, seg_b)."""
    for sa in a.segments():
        for sb in b.segments():
            if angle_between_segments_deg(sa[0], sa[1], sb[0], sb[1]) >= PARALLEL_DEG:
                continue
            d = sub(sa[1], sa[0])
            L = math.hypot(*d)
            if L < GEOM_EPS:
                continue
            u = (d[0] / L, d[1] / L)
            t0 = dot(sub(sb[0], sa[0]), u)
            t1 = dot(sub(sb[1], sa[0]), u)
            lo, hi = max(0.0, min(t0, t1)), min(L, max(t0, t1))
            overlap = hi - lo
            if overlap < PARALLEL_MIN_OVERLAP:
                continue
            tm = (lo + hi) / 2
            mid_a = (sa[0][0] + u[0] * tm, sa[0][1] + u[1] * tm)
            q, _ = closest_point_on_segment(mid_a, sb[0], sb[1])
            sep = dist(mid_a, q)
            mid = ((mid_a[0] + q[0]) / 2, (mid_a[1] + q[1]) / 2)
            yield overlap, sep, mid, sa, sb


def check_parallel(ctx: Context) -> list[dict]:
    """Parallel runs of different systems closer than the side clearance: TOO CLOSE, or a stacked
    parallel run (INFO). One row per run pair (the worst segment pair)."""
    rows = []
    runs = ctx.runs
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            a, b = runs[i], runs[j]
            if a.system == b.system:
                continue
            worst_row = None
            worst_rank = None
            for overlap, sep, mid, sa, sb in parallel_candidates(a, b):
                ctx.parallel_pairs_checked += 1
                z = ctx.zone_at(mid)
                min_side = z.min_side_clearance if z else ZONE_DEFAULTS["min_side_clearance"]
                access = z.access_side_clearance if z else ZONE_DEFAULTS["access_side_clearance"]
                vclear = z.min_vertical_clearance if z else ZONE_DEFAULTS["min_vertical_clearance"]
                gap = sep - (a.half_w + b.half_w)
                side_a = side_name(a, sa, mid if sep > GEOM_EPS else sb[0])   # side of a that faces b
                side_b = side_name(b, sb, mid if sep > GEOM_EPS else sa[0])
                req = min_side
                why = f"min_side_clearance {min_side:.3f}"
                if needs_side_access(a, side_a) or needs_side_access(b, side_b):
                    req = max(min_side, access)
                    who = a.id if needs_side_access(a, side_a) else b.id
                    why = f"access_side_clearance {access:.3f} ({who} needs access on that side)"
                if gap >= req - EPS:
                    continue
                horiz = f"side gap {gap:.3f} < {why}; overlap {overlap:.2f} m; separation {sep:.3f}"
                if a.placed and b.placed:
                    ta, ba = a.eff_top_at(mid), a.eff_bottom_at(mid)
                    tb, bb = b.eff_top_at(mid), b.eff_bottom_at(mid)
                    if ba >= tb - EPS or bb >= ta - EPS:
                        upper, lower = (a, b) if ba >= tb - EPS else (b, a)
                        vgap = upper.eff_bottom_at(mid) - lower.eff_top_at(mid)
                        vreq = vclear
                        vwhy = f"min_vertical_clearance {vclear:.3f}"
                        if "top" in lower.needs_access or "bottom" in upper.needs_access:
                            vreq = max(vclear, access)
                            vwhy = f"access_side_clearance {access:.3f} (stacked on an access side)"
                        if vgap < vreq - EPS:
                            verdict, sev = "TOO CLOSE", "P1"
                            msg = f"TOO CLOSE (stacked): {upper.id} over {lower.id}, vertical gap {vgap:.3f} < {vwhy}; {horiz}"
                        else:
                            verdict, sev = "STACKED", "INFO"
                            msg = f"stacked parallel run: {upper.id} over {lower.id}, vertical gap {vgap:.3f} >= {vwhy}; {horiz}"
                    else:
                        overlap_v = min(ta, tb) - max(ba, bb)
                        verdict, sev = "TOO CLOSE", "P1"
                        msg = (f"TOO CLOSE: {a.id} ({ba:.3f}..{ta:.3f}) beside {b.id} ({bb:.3f}..{tb:.3f}), "
                               f"vertical overlap {overlap_v:.3f}; {horiz}")
                else:
                    missing = [r.id for r in (a, b) if not r.placed]
                    verdict, sev = "UNRESOLVED", "INFO"
                    msg = f"UNRESOLVED: no RLs on {', '.join(missing)}; {horiz}"
                rank = ({"P0": 0, "P1": 1, "P2": 2, "INFO": 3}[sev], gap)
                if worst_rank is None or rank < worst_rank:
                    worst_rank = rank
                    worst_row = finding("PARALLEL", sev, a.id, b.id, mid[0], mid[1], z.id if z else "", verdict,
                                        message=msg)
            if worst_row:
                rows.append(worst_row)
    return rows


# ----------------------------------------------------------------------------- 4. DRAIN

def check_drains(ctx: Context) -> list[dict]:
    """A gravity drain's invert must fall continuously along its path at >= its fall."""
    rows = []
    for run in ctx.runs:
        if run.family != "DRAIN" or not run.placed:
            continue
        p = run.path[0]
        z = ctx.zone_at(p)
        segs = []
        for i, (a, b) in enumerate(run.segments()):
            L = dist(a, b)
            drop = run.inverts[i] - run.inverts[i + 1]
            segs.append((i, L, drop / L if L > GEOM_EPS else 0.0))
        total = polyline_length(run.path)
        overall = (run.inverts[0] - run.inverts[-1]) / total if total > GEOM_EPS else 0.0
        head = f"invert {run.inverts[0]:.3f} -> {run.inverts[-1]:.3f} over {total:.3f} m = {gradient_text(overall)}"
        if run.fall is None:
            flat = [s for s in segs if s[2] <= 0]
            if flat:
                i, L, g = flat[0]
                rows.append(finding("DRAIN", "P1", run.id, "", p[0], p[1], z.id if z else "", "FALL FAIL",
                                    message=f"FALL FAIL: segment {i + 1} ({L:.2f} m) has {gradient_text(g)}; {head}; no fall value given"))
            else:
                rows.append(finding("DRAIN", "P2", run.id, "", p[0], p[1], z.id if z else "", "FALL NOT GIVEN",
                                    message=f"no fall value on the run: monotonic fall only checked; {head}"))
            continue
        bad = [s for s in segs if s[2] < run.fall - 1e-9]
        if bad:
            i, L, g = min(bad, key=lambda s: s[2])
            rows.append(finding("DRAIN", "P1", run.id, "", p[0], p[1], z.id if z else "", "FALL FAIL",
                                message=f"FALL FAIL: segment {i + 1} ({L:.2f} m) falls at {gradient_text(g)} < required "
                                        f"{gradient_text(run.fall)}; {head}"))
        else:
            rows.append(finding("DRAIN", "INFO", run.id, "", p[0], p[1], z.id if z else "", "FALL OK",
                                message=f"{head} >= required {gradient_text(run.fall)} on every segment"))
    return rows


# ----------------------------------------------------------------------------- 5. UNPLACED

def check_unplaced(ctx: Context) -> list[dict]:
    """Runs without RLs: INFO (small, S3), P2 (small, S6), P1 (LARGE at either stage)."""
    rows = []
    for run in ctx.runs:
        if run.placed:
            continue
        large = run.is_large(ctx.thr)
        p = run.path[0]
        z = ctx.zone_at(p)
        what = "no invert RLs (invert_start_rl / invert_end_rl or inverts)" if run.family == "DRAIN" else "no top_rl / bottom_rl"
        if large:
            sev = "P1"
            msg = f"UNPLACED LARGE run ({run.size_text()}): {what}; large runs must have RLs even at S3"
        elif ctx.stage == "S6":
            sev = "P2"
            msg = f"UNPLACED small run ({run.size_text()}): {what}; every run needs RLs at S6"
        else:
            sev = "INFO"
            msg = f"UNPLACED small run ({run.size_text()}): {what}; allowed at S3, crossings reported UNRESOLVED"
        rows.append(finding("UNPLACED", sev, run.id, "", p[0], p[1], z.id if z else "", "UNPLACED", message=msg))
    return rows


# ----------------------------------------------------------------------------- run everything

def run_checks(ctx: Context, routes_path="", crossings_path="") -> list[dict]:
    """All checks -> numbered report rows (CONFIG row first)."""
    cfg = finding("CONFIG", "INFO", message=(
        f"{SCRIPT_VERSION}; level {ctx.level}; stage {ctx.stage}; {ctx.thr.text()}; zone defaults "
        + ", ".join(f"{k} {v:.3f}" for k, v in ZONE_DEFAULTS.items())
        + f"; register match radius {REGISTER_MATCH_RADIUS} m, register RL tolerance {REGISTER_RL_TOL} m; "
        f"parallel < {PARALLEL_DEG:.0f} deg over >= {PARALLEL_MIN_OVERLAP} m; routes {routes_path or '-'}; "
        f"crossings {crossings_path or '-'}; {len(ctx.runs)} runs, {len(ctx.zones)} zones, {len(ctx.register)} register entries"))
    rows = [cfg]
    rows += check_envelope(ctx)
    rows += check_crossings(ctx)
    rows += check_parallel(ctx)
    rows += check_drains(ctx)
    rows += check_unplaced(ctx)
    return assign_ids(rows)


# ----------------------------------------------------------------------------- report output

def write_csv(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})
    os.replace(tmp, path)


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    missing = [c for c in COLUMNS if rows and c not in rows[0]]
    if missing:
        raise SystemExit(f"{path}: missing columns {missing}")
    return rows


def summary_lines(rows: list[dict]) -> list[str]:
    """Counts per severity, per type and per verdict (register statuses included)."""
    by_sev = Counter(r["severity"] for r in rows)
    by_type = Counter(r["type"] for r in rows)
    lines = ["severity: " + ", ".join(f"{s} {by_sev.get(s, 0)}" for s in SEVERITIES),
             "type:     " + ", ".join(f"{t} {by_type[t]}" for t in TYPE_ORDER if by_type.get(t))]
    matrix = Counter((r["type"], r["severity"]) for r in rows if r["type"] != "CONFIG")
    for t in TYPE_ORDER:
        cells = [f"{s} {matrix[(t, s)]}" for s in SEVERITIES if matrix.get((t, s))]
        if cells:
            lines.append(f"  {t:<9} " + ", ".join(cells))
    verdicts = Counter(r["vertical_check"] for r in rows if r["vertical_check"] and r["vertical_check"] != "-")
    lines.append("verdicts: " + ", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())))
    reg = Counter(r["register_status"] for r in rows if r["register_status"] and r["register_status"] != "NOT REQUIRED")
    if reg:
        lines.append("register: " + ", ".join(f"{k} {v}" for k, v in sorted(reg.items())))
    return lines


def print_report(rows: list[dict], full: bool) -> None:
    """Console table: every P0 / P1 / P2 row (all rows when full=True), then the summary."""
    shown = [r for r in rows if full or r["severity"] != "INFO"]
    if not shown:
        print("no P0 / P1 / P2 findings")
    for r in shown:
        loc = f"({r['x']}, {r['y']})" if r["x"] else ""
        pair = r["run_a"] + (f" x {r['run_b']}" if r["run_b"] else "")
        reg = f" [{r['register_status']}{' ' + r['section_sheet'] if r['section_sheet'] else ''}]" if r["register_status"] else ""
        print(f"{r['id']:<8} {r['severity']:<4} {r['type']:<8} {r['vertical_check']:<12} {pair:<26} {loc:<18} {r['zone']:<10}{reg}")
        print(f"         {r['message']}")
    print("-" * 78)
    for line in summary_lines(rows):
        print(line)


def has_blockers(rows: list[dict]) -> bool:
    return any(r["severity"] in ("P0", "P1") for r in rows)


# ----------------------------------------------------------------------------- SVG plan

def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def render_svg(ctx: Context, rows: list[dict], title: str) -> str:
    """A simple plan: zones, runs as filled bands of their effective width (colour by family,
    dashed when unplaced), crossing / parallel markers by severity, run labels and a legend."""
    pts = [p for z in ctx.zones for p in z.polygon] + [p for r in ctx.runs for p in r.path]
    if not pts:
        pts = [(0, 0), (10, 10)]
    minx, maxx = min(p[0] for p in pts) - 1.5, max(p[0] for p in pts) + 1.5
    miny, maxy = min(p[1] for p in pts) - 1.5, max(p[1] for p in pts) + 1.5
    w_m, h_m = max(maxx - minx, 1.0), max(maxy - miny, 1.0)
    scale = max(10.0, min(60.0, 1500.0 / w_m, 900.0 / h_m))
    margin = 40
    legend_h = 150
    W = int(w_m * scale + 2 * margin)
    H = int(h_m * scale + 2 * margin + legend_h)

    def X(x):
        return margin + (x - minx) * scale

    def Y(y):
        return margin + (maxy - y) * scale

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="Arial, Helvetica, sans-serif" font-size="11">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<text x="{margin}" y="{margin - 16}" font-size="15" font-weight="bold">{_esc(title)}</text>']
    # grid every metre, labels every 5 m
    x0, x1 = math.floor(minx), math.ceil(maxx)
    y0, y1 = math.floor(miny), math.ceil(maxy)
    out.append('<g stroke="#e2e8f0" stroke-width="0.5">')
    for gx in range(x0, x1 + 1):
        out.append(f'<line x1="{X(gx):.1f}" y1="{Y(miny):.1f}" x2="{X(gx):.1f}" y2="{Y(maxy):.1f}"/>')
    for gy in range(y0, y1 + 1):
        out.append(f'<line x1="{X(minx):.1f}" y1="{Y(gy):.1f}" x2="{X(maxx):.1f}" y2="{Y(gy):.1f}"/>')
    out.append('</g><g fill="#718096" font-size="9">')
    for gx in range(x0, x1 + 1):
        if gx % 5 == 0:
            out.append(f'<text x="{X(gx):.1f}" y="{Y(miny) + 12:.1f}" text-anchor="middle">{gx}</text>')
    for gy in range(y0, y1 + 1):
        if gy % 5 == 0:
            out.append(f'<text x="{X(minx) - 4:.1f}" y="{Y(gy) + 3:.1f}" text-anchor="end">{gy}</text>')
    out.append('</g>')
    # zones
    for z in ctx.zones:
        pts_s = " ".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in z.polygon)
        c = polygon_centroid(z.polygon)
        out.append(f'<polygon points="{pts_s}" fill="#f7fafc" stroke="#a0aec0" stroke-width="1" stroke-dasharray="6,3"/>')
        out.append(f'<text x="{X(c[0]):.1f}" y="{Y(c[1]) - 4:.1f}" text-anchor="middle" fill="#4a5568" font-size="10">'
                   f'{_esc(z.id)}  soffit {z.soffit:.3f} / ceiling {z.ceiling:.3f} / zone {z.available:.3f}</text>')
    # runs
    for r in ctx.runs:
        pts_s = " ".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in r.path)
        col = r.colour()
        dash = ' stroke-dasharray="8,5"' if not r.placed else ""
        op = "0.30" if not r.placed else "0.55"
        out.append(f'<polyline points="{pts_s}" fill="none" stroke="{col}" stroke-opacity="{op}" '
                   f'stroke-width="{max(2.0, r.eff_w * scale):.1f}" stroke-linecap="butt" stroke-linejoin="miter"{dash}/>')
        out.append(f'<polyline points="{pts_s}" fill="none" stroke="{col}" stroke-width="1"/>')
        p = r.path[0]
        q = r.path[1]
        ang = math.degrees(math.atan2(-(Y(q[1]) - Y(p[1])), X(q[0]) - X(p[0])))
        if ang > 90 or ang < -90:
            ang += 180
        rl = ""
        if r.placed:
            rl = (f" inv {r.inverts[0]:.3f}->{r.inverts[-1]:.3f}" if r.family == "DRAIN"
                  else f" RL {r.bottom_rl:.3f}-{r.top_rl:.3f}")
        else:
            rl = " UNPLACED"
        mx, my = (X(p[0]) + X(q[0])) / 2, (Y(p[1]) + Y(q[1])) / 2
        out.append(f'<text transform="translate({mx:.1f},{my:.1f}) rotate({-ang:.1f})" text-anchor="middle" '
                   f'font-size="10" fill="#1a202c" paint-order="stroke" stroke="#ffffff" stroke-width="3">'
                   f'{_esc(r.id)} {_esc(r.size_text())}{_esc(rl)}</text>')
    # markers
    for row in rows:
        if row["type"] not in ("CROSS", "PARALLEL") or not row["x"]:
            continue
        x, y = X(float(row["x"])), Y(float(row["y"]))
        sev = row["severity"]
        stale = row["register_status"] == "STALE"
        if stale:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="none" stroke="#718096" stroke-width="1.5" stroke-dasharray="3,2"/>')
        elif sev == "P0":
            out.append(f'<g stroke="{SEVERITY_COLOUR["P0"]}" stroke-width="2.5">'
                       f'<line x1="{x - 7:.1f}" y1="{y - 7:.1f}" x2="{x + 7:.1f}" y2="{y + 7:.1f}"/>'
                       f'<line x1="{x - 7:.1f}" y1="{y + 7:.1f}" x2="{x + 7:.1f}" y2="{y - 7:.1f}"/>'
                       f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="none" stroke-width="1.2"/></g>')
        elif sev in ("P1", "P2"):
            col = SEVERITY_COLOUR[sev]
            out.append(f'<polygon points="{x:.1f},{y - 9:.1f} {x - 8:.1f},{y + 6:.1f} {x + 8:.1f},{y + 6:.1f}" '
                       f'fill="{col}" fill-opacity="0.85" stroke="#1a202c" stroke-width="0.8"/>')
        elif row["vertical_check"] == "OK":
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{SEVERITY_COLOUR["OK"]}" stroke="#1a202c" stroke-width="0.8"/>')
        else:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{SEVERITY_COLOUR["INFO"]}" stroke="#1a202c" stroke-width="0.8"/>')
        out.append(f'<text x="{x + 11:.1f}" y="{y + 4:.1f}" font-size="9" fill="#1a202c" paint-order="stroke" '
                   f'stroke="#ffffff" stroke-width="2.5">{_esc(row["id"])}</text>')
    # legend
    ly = H - legend_h + 20
    out.append(f'<text x="{margin}" y="{ly}" font-weight="bold">Legend</text>')
    lx = margin
    for name in ("DUCT", "PIPE", "TRAY", "DRAIN", "BUSWAY", "CONDUIT", "BRACE", "FIRE"):
        out.append(f'<rect x="{lx}" y="{ly + 8}" width="18" height="10" fill="{FAMILY_COLOUR[name]}" fill-opacity="0.6"/>'
                   f'<text x="{lx + 22}" y="{ly + 17}">{name}{" system" if name == "FIRE" else ""}</text>')
        lx += 95
    my_ = ly + 36
    out.append(f'<circle cx="{margin + 8}" cy="{my_}" r="6" fill="{SEVERITY_COLOUR["OK"]}"/><text x="{margin + 20}" y="{my_ + 4}">crossing OK</text>')
    out.append(f'<g stroke="{SEVERITY_COLOUR["P0"]}" stroke-width="2.5"><line x1="{margin + 130}" y1="{my_ - 6}" x2="{margin + 142}" y2="{my_ + 6}"/>'
               f'<line x1="{margin + 130}" y1="{my_ + 6}" x2="{margin + 142}" y2="{my_ - 6}"/></g><text x="{margin + 150}" y="{my_ + 4}">P0 clash / depth budget</text>')
    out.append(f'<polygon points="{margin + 300},{my_ - 8} {margin + 292},{my_ + 6} {margin + 308},{my_ + 6}" fill="{SEVERITY_COLOUR["P1"]}"/>'
               f'<text x="{margin + 315}" y="{my_ + 4}">P1 (orange) / P2 (grey) triangle</text>')
    out.append(f'<circle cx="{margin + 520}" cy="{my_}" r="6" fill="{SEVERITY_COLOUR["INFO"]}"/><text x="{margin + 532}" y="{my_ + 4}">INFO / unresolved</text>')
    out.append(f'<circle cx="{margin + 660}" cy="{my_}" r="7" fill="none" stroke="#718096" stroke-dasharray="3,2"/><text x="{margin + 672}" y="{my_ + 4}">stale register entry</text>')
    out.append(f'<text x="{margin}" y="{my_ + 24}" fill="#4a5568">dashed band = UNPLACED (no RLs); band width = effective outside width incl. insulation</text>')
    out.append(f'<text x="{margin}" y="{my_ + 42}" fill="#4a5568">{_esc(ctx.thr.text())}</text>')
    sev = Counter(r["severity"] for r in rows)
    out.append(f'<text x="{margin}" y="{my_ + 60}" fill="#4a5568">stage {ctx.stage}; P0 {sev.get("P0", 0)}, P1 {sev.get("P1", 0)}, '
               f'P2 {sev.get("P2", 0)}, INFO {sev.get("INFO", 0)}; {SCRIPT_VERSION}; a script result is a data-consistency check, not an engineering PASS</text>')
    out.append('</svg>')
    return "\n".join(out)


# ----------------------------------------------------------------------------- commands

def thresholds_from_args(a: argparse.Namespace) -> Thresholds:
    return Thresholds(getattr(a, "large_duct_width", 0.6), getattr(a, "large_duct_depth", 0.4),
                      getattr(a, "large_pipe_dn", 100), getattr(a, "large_pipe_od", 0.1),
                      getattr(a, "large_tray_width", 0.45))


def cmd_check(a: argparse.Namespace) -> int:
    stage = (a.stage or "S6").upper()
    if stage not in STAGES:
        raise SystemExit(f"--stage must be one of {', '.join(STAGES)}")
    level, zones, runs = load_routes(a.routes)
    register = load_crossings(a.crossings)
    ctx = Context(level, zones, runs, register, stage, thresholds_from_args(a), parse_default_zone(a.default_zone))
    rows = run_checks(ctx, a.routes, a.crossings or "")
    out = a.out or f"reports/crossings-{level}.csv"
    write_csv(out, rows)
    title = f"Services coordination check  {level}  stage {stage}  {_dt.date.today().isoformat()}"
    if a.svg:
        os.makedirs(os.path.dirname(os.path.abspath(a.svg)), exist_ok=True)
        with open(a.svg, "w", encoding="utf-8") as f:
            f.write(render_svg(ctx, rows, title))
    print(title)
    print(f"{ctx.thr.text()}; {ctx.crossings_checked} crossings and {ctx.parallel_pairs_checked} parallel segment pairs checked")
    print_report(rows, full=getattr(a, "full", False))
    print(f"wrote {out}" + (f" and {a.svg}" if a.svg else ""))
    blockers = has_blockers(rows)
    print("result: " + ("P0 / P1 present -> exit 1" if blockers else "no P0 / P1 -> exit 0") +
          " (data-consistency result, not an engineering PASS)")
    return 1 if blockers else 0


def cmd_summary(a: argparse.Namespace) -> int:
    rows = read_csv(a.file)
    print(f"{a.file}: {len(rows)} rows")
    for line in summary_lines(rows):
        print(line)
    return 0


# ----------------------------------------------------------------------------- demo data

def demo_routes() -> dict:
    """A 30 m corridor on L22: zone A (x 0-20, 1.20 m ceiling zone) and zone B (x 20-30, 0.75 m,
    higher lift-lobby ceiling). Sizes and RLs are chosen so that the checker finds exactly: one
    CLASH (drain raised above its registered invert under the SA duct), one depth-budget FAIL
    (unplaced HHWS pipe cannot stack with the SA duct in zone B), one NEEDS SECTION (CHWR x SA
    not in the register), one TOO CLOSE (EA duct 50 mm beside the SA duct), one UNPLACED pipe."""
    return {
        "level": "L22", "units": "m",
        "zones": [
            {"id": "CZ-CORR-A", "polygon": [[0, 0], [20, 0], [20, 3], [0, 3]],
             "structure_soffit_rl": 77.200, "ceiling_rl": 76.000, "hanger_allowance": 0.05,
             "ceiling_allowance": 0.03, "band_order": ["FIRE", "DUCT", "PIPE", "TRAY"],
             "min_vertical_clearance": 0.05, "min_side_clearance": 0.10, "access_side_clearance": 0.30},
            {"id": "CZ-CORR-B", "polygon": [[20, 0], [30, 0], [30, 3], [20, 3]],
             "structure_soffit_rl": 77.200, "ceiling_rl": 76.450, "hanger_allowance": 0.05,
             "ceiling_allowance": 0.03, "band_order": ["FIRE", "DUCT", "PIPE", "TRAY"],
             "min_vertical_clearance": 0.05, "min_side_clearance": 0.10, "access_side_clearance": 0.30},
        ],
        "runs": [
            {"id": "SA-22-01", "system": "SA", "family": "DUCT", "path": [[0, 1.6], [30, 1.6]],
             "width": 1.0, "depth": 0.5, "insulation": 0.025, "top_rl": 77.120, "bottom_rl": 76.620,
             "sheet": "M-131", "priority": 1, "element_ids": ["DUCT-SA-L22-001"]},
            {"id": "EA-22-01", "system": "EA", "family": "DUCT", "path": [[8, 0.7], [20, 0.7]],
             "width": 0.6, "depth": 0.4, "insulation": 0.025, "top_rl": 77.120, "bottom_rl": 76.720,
             "sheet": "M-132", "priority": 2, "element_ids": ["DUCT-EA-L22-004"]},
            {"id": "CHWS-22-01", "system": "CHW", "family": "PIPE", "path": [[14, 3.0], [14, 0.4]],
             "dn": 150, "od": 0.1683, "insulation": 0.032, "top_rl": 76.508, "bottom_rl": 76.340,
             "sheet": "M-141", "priority": 3},
            {"id": "CHWR-22-01", "system": "CHW", "family": "PIPE", "path": [[14.5, 3.0], [14.5, 0.4]],
             "dn": 150, "od": 0.1683, "insulation": 0.032, "top_rl": 76.508, "bottom_rl": 76.340,
             "sheet": "M-141", "priority": 3},
            {"id": "FS-22-01", "system": "FIRE", "family": "PIPE", "path": [[0, 0.15], [30, 0.15]],
             "dn": 100, "od": 0.1143, "insulation": 0, "top_rl": 77.145, "bottom_rl": 77.031,
             "sheet": "F-121", "priority": 2},
            {"id": "CT-22-01", "system": "ELEC", "family": "TRAY", "path": [[0, 2.55], [20, 2.55]],
             "width": 0.6, "depth": 0.1, "top_rl": 76.230, "bottom_rl": 76.130, "sheet": "E-151",
             "needs_access": ["top"], "priority": 3},
            {"id": "DR-22-01", "system": "SAN", "family": "DRAIN", "path": [[5, 3.0], [5, 0.0]],
             "dn": 100, "od": 0.110, "fall": "1:60", "invert_start_rl": 76.550, "invert_end_rl": 76.495,
             "sheet": "H-161", "priority": 1},
            {"id": "HHWS-22-01", "system": "HHW", "family": "PIPE", "path": [[25, 3.0], [25, 0.0]],
             "dn": 65, "od": 0.0761, "insulation": 0.025, "sheet": "M-142"},
        ],
    }


def demo_crossings() -> list:
    """The register for the demo level: every LARGE x LARGE crossing except CHWR x SA; X-22-006
    records the intended drain invert under the SA duct, which the route no longer honours."""
    def entry(i, over, under, at, over_bottom, under_top, clearance, sheet, resolution):
        return {"id": f"X-22-{i:03d}", "runs": [over, under], "at": at, "resolution": resolution,
                "over_run": over, "under_run": under, "over_bottom_rl": over_bottom, "under_top_rl": under_top,
                "clearance": clearance, "section_sheet": sheet, "status": "RESOLVED"}
    return [
        entry(1, "SA-22-01", "CHWS-22-01", [14.0, 1.6], 76.620, 76.508, 0.055, "C-322", "pipe under duct"),
        entry(2, "EA-22-01", "CHWS-22-01", [14.0, 0.7], 76.720, 76.508, 0.155, "C-322", "pipe under duct"),
        entry(3, "EA-22-01", "CHWR-22-01", [14.5, 0.7], 76.720, 76.508, 0.155, "C-322", "pipe under duct"),
        entry(4, "CHWS-22-01", "CT-22-01", [14.0, 2.55], 76.340, 76.230, 0.078, "C-322", "pipe over tray"),
        entry(5, "CHWR-22-01", "CT-22-01", [14.5, 2.55], 76.340, 76.230, 0.078, "C-322", "pipe over tray"),
        entry(6, "SA-22-01", "DR-22-01", [5.0, 1.6], 76.620, 76.535, 0.060, "C-323", "drain under duct, invert 76.425"),
        entry(7, "DR-22-01", "CT-22-01", [5.0, 2.55], 76.542, 76.230, 0.312, "C-323", "drain over tray"),
        entry(8, "FS-22-01", "DR-22-01", [5.0, 0.15], 77.031, 76.608, 0.423, "C-323", "drain under fire main"),
    ]


def write_demo(d: str) -> tuple[str, str]:
    os.makedirs(os.path.join(d, "db"), exist_ok=True)
    routes = os.path.join(d, "db", "services-routes.json")
    crossings = os.path.join(d, "db", "crossings.json")
    with open(routes, "w", encoding="utf-8") as f:
        json.dump(demo_routes(), f, indent=2)
        f.write("\n")
    with open(crossings, "w", encoding="utf-8") as f:
        json.dump(demo_crossings(), f, indent=2)
        f.write("\n")
    return routes, crossings


def cmd_demo(a: argparse.Namespace) -> int:
    routes, crossings = write_demo(a.dir)
    print(f"wrote {routes} and {crossings}")
    ns = argparse.Namespace(routes=routes, crossings=crossings, stage="S6",
                            out=os.path.join(a.dir, "reports", "crossings-L22.csv"),
                            svg=os.path.join(a.dir, "reports", "crossings-L22.svg"), default_zone=None, full=True)
    code = cmd_check(ns)
    print(f"check exit code {code}" + (" (expected: the sample contains a clash)" if code else ""))
    return 0


# ----------------------------------------------------------------------------- selftest

def _ctx(zones, runs, register=(), stage="S6", default_zone=None) -> Context:
    return Context("T", [Zone(z) for z in zones], [Run(r) for r in runs], [RegisterEntry(e) for e in register],
                   stage, Thresholds(), default_zone)


def cmd_selftest(a: argparse.Namespace) -> int:
    results = []

    def ok(name, cond):
        results.append((name, bool(cond)))
        print(("PASS " if cond else "FAIL ") + name)

    def near(p, q, tol=1e-6):
        return p is not None and q is not None and dist(p, q) < tol

    # --- geometry
    k, p = segment_intersection((0, 0), (1, 1), (0, 1), (1, 0))
    ok("proper crossing", k == "cross" and near(p, (0.5, 0.5)))
    k, p = segment_intersection((0, 0), (2, 0), (1, 0), (1, 1))
    ok("T-junction touch", k == "touch" and near(p, (1, 0)))
    k, p = segment_intersection((0, 0), (1, 0), (1, 0), (2, 1))
    ok("endpoint-to-endpoint touch", k == "touch" and near(p, (1, 0)))
    k, p = segment_intersection((0, 0), (2, 0), (1, 0), (3, 0))
    ok("collinear overlap", k == "collinear" and near(p, (1.5, 0)))
    ok("collinear disjoint", segment_intersection((0, 0), (1, 0), (2, 0), (3, 0))[0] == "none")
    ok("parallel distinct lines", segment_intersection((0, 0), (1, 0), (0, 1), (1, 1))[0] == "none")
    ok("skew non-touching", segment_intersection((0, 0), (1, 0), (2, 1), (2, 2))[0] == "none")
    d, p, q = closest_points_segments((0, 0), (1, 0), (2, 1), (2, 2))
    ok("closest points", abs(d - math.sqrt(2)) < 1e-9 and near(p, (1, 0)) and near(q, (2, 1)))
    sq = [(0, 0), (2, 0), (2, 2), (0, 2)]
    ok("pip square inside / outside", point_in_polygon((1, 1), sq) and not point_in_polygon((3, 1), sq))
    ok("pip on edge and vertex count as inside", point_in_polygon((2, 1), sq) and point_in_polygon((0, 0), sq))
    L = [(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)]
    ok("pip concave L", point_in_polygon((0.5, 2), L) and point_in_polygon((2, 0.5), L) and not point_in_polygon((2, 2), L))
    U = [(0, 0), (3, 0), (3, 3), (2, 3), (2, 1), (1, 1), (1, 3), (0, 3)]
    ok("pip concave U", point_in_polygon((1.5, 0.5), U) and point_in_polygon((0.5, 2.5), U) and not point_in_polygon((1.5, 2), U))
    ok("angle between segments", abs(angle_between_segments_deg((0, 0), (1, 0), (0, 0), (0, 1)) - 90) < 1e-9
       and angle_between_segments_deg((0, 0), (1, 0), (5, 5), (0, 5)) < 1e-9)
    A = Run({"id": "A", "system": "X", "family": "DUCT", "path": [[0, 0], [5, 0], [5, 5]], "width": 0.4, "depth": 0.3})
    B = Run({"id": "B", "system": "Y", "family": "PIPE", "path": [[3, -1], [7, 3]], "od": 0.1})
    ok("two distinct crossings of an L-shaped run", len(find_crossings(A, B)) == 2)
    C = Run({"id": "C", "system": "Y", "family": "PIPE", "path": [[4, -1], [6, 1]], "od": 0.1})
    ok("crossing through a corner merges to one", len(find_crossings(A, C)) == 1)
    D = Run({"id": "D", "system": "Y", "family": "PIPE", "path": [[2, 0.22], [2, 4]], "od": 0.1})
    xs = find_crossings(A, D)
    ok("envelope-only overlap is a crossing", len(xs) == 1 and xs[0][0] == "envelope")
    DR = Run({"id": "DR", "system": "SAN", "family": "DRAIN", "path": [[0, 0], [3, 0], [3, 4]], "od": 0.11,
              "fall": "1:50", "invert_start_rl": 10.0, "invert_end_rl": 9.86})
    ok("drain invert interpolation", abs(DR.invert_at((3, 2)) - 9.90) < 1e-9 and abs(chainage_of_point(DR.path, (3, 2)) - 5) < 1e-9)
    ok("fall parsing", abs(parse_fall("1:60") - 1 / 60) < 1e-12 and parse_fall(0.02) == 0.02 and parse_fall(None) is None)

    # --- demo level, S6
    with tempfile.TemporaryDirectory() as d:
        routes, crossings = write_demo(d)
        out = os.path.join(d, "reports", "crossings-L22.csv")
        svg = os.path.join(d, "reports", "crossings-L22.svg")
        code = cmd_check(argparse.Namespace(routes=routes, crossings=crossings, stage="S6", out=out, svg=svg,
                                            default_zone=None, full=False))
        ok("demo S6 exits 1", code == 1)
        rows = read_csv(out)
        ok("csv and svg written", os.path.exists(out) and os.path.exists(svg) and rows[0]["type"] == "CONFIG")
        clash = [r for r in rows if r["vertical_check"] == "CLASH"]
        ok("exactly one CLASH (drain x SA duct), P0", len(clash) == 1 and clash[0]["severity"] == "P0"
           and {clash[0]["run_a"], clash[0]["run_b"]} == {"SA-22-01", "DR-22-01"})
        ok("the clash row carries REGISTER MISMATCH", clash and clash[0]["register_status"] == "REGISTER MISMATCH")
        needs = [r for r in rows if r["register_status"] == "NEEDS SECTION"]
        ok("exactly one NEEDS SECTION (CHWR x SA), P1", len(needs) == 1 and needs[0]["severity"] == "P1"
           and {needs[0]["run_a"], needs[0]["run_b"]} == {"SA-22-01", "CHWR-22-01"} and needs[0]["vertical_check"] == "OK")
        close = [r for r in rows if r["vertical_check"] == "TOO CLOSE"]
        ok("exactly one TOO CLOSE (EA beside SA), P1", len(close) == 1 and close[0]["severity"] == "P1"
           and {close[0]["run_a"], close[0]["run_b"]} == {"SA-22-01", "EA-22-01"})
        unp = [r for r in rows if r["type"] == "UNPLACED"]
        ok("exactly one UNPLACED (HHWS), P2 at S6", len(unp) == 1 and unp[0]["run_a"] == "HHWS-22-01" and unp[0]["severity"] == "P2")
        resolved_ok = [r for r in rows if r["vertical_check"] == "OK" and r["register_status"] == "RESOLVED"]
        ok("OK crossings with register RESOLVED and a section sheet", len(resolved_ok) == 7 and all(r["section_sheet"] for r in resolved_ok))
        budget = [r for r in rows if r["type"] == "CROSS" and r["required_depth"] and r["available_depth"]
                  and float(r["required_depth"]) > float(r["available_depth"])]
        ok("exactly one depth-budget FAIL (HHWS x SA in zone B), P0", len(budget) == 1 and budget[0]["severity"] == "P0"
           and budget[0]["zone"] == "CZ-CORR-B" and budget[0]["vertical_check"] == "UNRESOLVED")
        ok("every crossing row has a depth budget", all(r["required_depth"] and r["available_depth"] for r in rows
                                                        if r["type"] == "CROSS" and r["register_status"] != "STALE"))
        ok("no STALE, no BAND ORDER, no envelope breach in the demo",
           not [r for r in rows if r["register_status"] == "STALE" or r["vertical_check"] in ("BAND ORDER", "BREACH", "NO ZONE", "RL SPAN")])
        ok("drain fall OK", [r["vertical_check"] for r in rows if r["type"] == "DRAIN"] == ["FALL OK"])
        non_info = sorted((r["type"], r["vertical_check"], r["severity"]) for r in rows if r["severity"] != "INFO")
        ok("exactly five non-INFO findings", non_info == [("CROSS", "CLASH", "P0"), ("CROSS", "OK", "P1"),
                                                          ("CROSS", "UNRESOLVED", "P0"), ("PARALLEL", "TOO CLOSE", "P1"),
                                                          ("UNPLACED", "UNPLACED", "P2")])
        ok("11 crossings computed", sum(1 for r in rows if r["type"] == "CROSS") == 11)
        # S3 on the same data: the small unplaced pipe is only INFO
        code3 = cmd_check(argparse.Namespace(routes=routes, crossings=crossings, stage="S3", out=out, svg=None,
                                             default_zone=None, full=False))
        rows3 = read_csv(out)
        unp3 = [r for r in rows3 if r["type"] == "UNPLACED"]
        ok("S3: small unplaced run is INFO", len(unp3) == 1 and unp3[0]["severity"] == "INFO" and code3 == 1)
        # summary reads the file
        ok("summary lines", any(line.startswith("severity:") for line in summary_lines(rows)))

    # --- synthetic rule tests
    zone = {"id": "Z", "polygon": [[0, 0], [10, 0], [10, 4], [0, 4]], "structure_soffit_rl": 10.0, "ceiling_rl": 9.0,
            "band_order": ["FIRE", "DUCT", "PIPE", "TRAY"]}
    duct = {"id": "D1", "system": "SA", "family": "DUCT", "path": [[0, 2], [10, 2]], "width": 0.8, "depth": 0.4,
            "insulation": 0.025, "top_rl": 9.90, "bottom_rl": 9.50}
    fire = {"id": "F1", "system": "FIRE", "family": "PIPE", "path": [[5, 0], [5, 4]], "dn": 100, "od": 0.1143,
            "top_rl": 9.40, "bottom_rl": 9.286}
    rows = run_checks(_ctx([zone], [duct, fire]))
    ok("band order warning: FIRE below DUCT is P2", any(r["vertical_check"] == "BAND ORDER" and r["severity"] == "P2" for r in rows))
    ok("large x large without register is NEEDS SECTION", any(r["register_status"] == "NEEDS SECTION" for r in rows))
    big_fire = dict(fire, top_rl=9.45, bottom_rl=9.336)      # eff top 9.45 vs duct eff bottom 9.475: gap 0.025
    rows = run_checks(_ctx([zone], [duct, big_fire]))
    ok("gap below clearance is TIGHT P1", any(r["vertical_check"] == "TIGHT" and r["severity"] == "P1" for r in rows))
    reg = [{"id": "X1", "runs": ["D1", "F1"], "at": [5, 2], "over_run": "D1", "under_run": "F1", "over_bottom_rl": 9.50,
            "under_top_rl": 9.40, "clearance": 0.05, "section_sheet": "C-301", "status": "RESOLVED"},
           {"id": "X9", "runs": ["D1", "F1"], "at": [1, 2], "section_sheet": "C-301", "status": "RESOLVED"}]
    rows = run_checks(_ctx([zone], [duct, fire], reg))
    ok("matching register entry is RESOLVED, unmatched one is STALE P2",
       any(r["register_status"] == "RESOLVED" for r in rows) and any(r["register_status"] == "STALE" and r["severity"] == "P2" for r in rows))
    reg_open = [dict(reg[0], status="OPEN")]
    rows = run_checks(_ctx([zone], [duct, fire], reg_open))
    ok("register entry not RESOLVED is NEEDS SECTION", any(r["register_status"] == "NEEDS SECTION" for r in rows))
    reg_bad = [dict(reg[0], under_top_rl=9.35)]
    rows = run_checks(_ctx([zone], [duct, fire], reg_bad))
    ok("register RL off by > 5 mm is REGISTER MISMATCH P1", any(r["register_status"] == "REGISTER MISMATCH" and r["severity"] == "P1" for r in rows))
    high = dict(duct, top_rl=9.96, bottom_rl=9.56)
    rows = run_checks(_ctx([zone], [high]))
    ok("envelope breach at the soffit is P1", any(r["vertical_check"] == "BREACH" and r["severity"] == "P1" for r in rows))
    off = dict(duct, path=[[0, 6], [10, 6]])
    rows = run_checks(_ctx([zone], [off]))
    ok("run outside every zone is NO ZONE P2", any(r["vertical_check"] == "NO ZONE" and r["severity"] == "P2" for r in rows))
    rows = run_checks(_ctx([zone], [off], default_zone=parse_default_zone("soffit=10,ceiling=9")))
    ok("--default-zone covers it", not any(r["vertical_check"] == "NO ZONE" for r in rows) and any(r["zone"] == "DEFAULT" for r in rows))
    span = dict(duct, bottom_rl=9.60)
    rows = run_checks(_ctx([zone], [span]))
    ok("RL span disagreeing with the size is P2", any(r["vertical_check"] == "RL SPAN" and r["severity"] == "P2" for r in rows))
    outside = dict(duct, rl_basis="outside", top_rl=9.925, bottom_rl=9.475)
    r_out = Run(outside)
    ok("rl_basis outside: no insulation added", abs(r_out.eff_top_at((1, 2)) - 9.925) < 1e-9 and abs(r_out.bare_top_at((1, 2)) - 9.90) < 1e-9
       and not any(r["vertical_check"] == "RL SPAN" for r in run_checks(_ctx([zone], [outside]))))
    unplaced_large = {k: v for k, v in duct.items() if k not in ("top_rl", "bottom_rl")}
    for stage in ("S3", "S6"):
        rows = run_checks(_ctx([zone], [unplaced_large], stage=stage))
        ok(f"large unplaced run is P1 at {stage}", any(r["type"] == "UNPLACED" and r["severity"] == "P1" for r in rows))
    small = {"id": "P2", "system": "HHW", "family": "PIPE", "path": [[0, 1], [10, 1]], "dn": 50}
    sev = {stage: [r["severity"] for r in run_checks(_ctx([zone], [small], stage=stage)) if r["type"] == "UNPLACED"][0]
           for stage in ("S3", "S6")}
    ok("small unplaced run: INFO at S3, P2 at S6", sev == {"S3": "INFO", "S6": "P2"})
    tray = {"id": "T1", "system": "ELEC", "family": "TRAY", "path": [[0, 2.9], [10, 2.9]], "width": 0.6, "depth": 0.1,
            "top_rl": 9.30, "bottom_rl": 9.20}                    # side gap 0.175 to the duct envelope
    rows = run_checks(_ctx([zone], [duct, tray]))
    ok("parallel with adequate side gap produces no PARALLEL row", not any(r["type"] == "PARALLEL" for r in rows))
    tray_close = dict(tray, path=[[0, 2.75], [10, 2.75]])   # side gap 0.025 < 0.10, stacked 0.175 below the duct
    rows = run_checks(_ctx([zone], [duct, tray_close]))
    par = [r for r in rows if r["type"] == "PARALLEL"]
    ok("stacked parallel run is INFO with the gap", len(par) == 1 and par[0]["vertical_check"] == "STACKED" and par[0]["severity"] == "INFO"
       and "0.175" in par[0]["message"])
    tray_access = dict(tray_close, needs_access=["top"])
    rows = run_checks(_ctx([zone], [duct, tray_access]))
    par = [r for r in rows if r["type"] == "PARALLEL"]
    ok("stacked on an access side needs access_side_clearance -> TOO CLOSE", len(par) == 1 and par[0]["vertical_check"] == "TOO CLOSE")
    tray_same = dict(tray_close, top_rl=9.60, bottom_rl=9.50)
    rows = run_checks(_ctx([zone], [duct, tray_same]))
    ok("parallel, too close and overlapping vertically -> TOO CLOSE P1",
       any(r["type"] == "PARALLEL" and r["vertical_check"] == "TOO CLOSE" and r["severity"] == "P1" for r in rows))
    side_access = dict(duct, needs_access=["right"])       # tray at y 2.9 is to the LEFT of the eastbound duct
    rows = run_checks(_ctx([zone], [side_access, tray]))
    ok("needs_access on the far side changes nothing", not any(r["type"] == "PARALLEL" for r in rows))
    side_access = dict(duct, needs_access=["left"])
    rows = run_checks(_ctx([zone], [side_access, tray]))
    ok("needs_access on the facing side applies access_side_clearance", any(r["type"] == "PARALLEL" for r in rows))
    drain_bad = {"id": "DR2", "system": "SAN", "family": "DRAIN", "path": [[1, 0], [1, 2], [1, 4]], "dn": 100, "od": 0.11,
                 "fall": "1:60", "inverts": [9.50, 9.49, 9.40]}
    rows = run_checks(_ctx([zone], [drain_bad]))
    ok("drain segment below its fall is FALL FAIL P1", any(r["vertical_check"] == "FALL FAIL" and r["severity"] == "P1" for r in rows))
    drain_nofall = {k: v for k, v in drain_bad.items() if k != "fall"}
    rows = run_checks(_ctx([zone], [drain_nofall]))
    ok("drain without a fall value is P2", any(r["vertical_check"] == "FALL NOT GIVEN" and r["severity"] == "P2" for r in rows))
    drain_under = {"id": "DR3", "system": "SAN", "family": "DRAIN", "path": [[5, 0], [5, 4]], "dn": 100, "od": 0.11,
                   "fall": "1:60", "invert_start_rl": 9.45, "invert_end_rl": 9.38}
    rows = run_checks(_ctx([zone], [duct, drain_under]))
    cr = [r for r in rows if r["type"] == "CROSS"]
    ok("crossing below a drain checks the drain invert at that chainage", len(cr) == 1 and cr[0]["vertical_check"] == "CLASH"
       and "invert 9.415" in cr[0]["message"])
    same = dict(fire, id="F2", system="SA")
    rows = run_checks(_ctx([zone], [duct, same]))
    ok("same-system runs are never checked against each other", not any(r["type"] == "CROSS" for r in rows))
    ok("large thresholds", Run(duct).is_large(Thresholds()) and not Run(small).is_large(Thresholds())
       and Run(dict(fire, dn=80, od=0.0889)).is_large(Thresholds()) is False and Run(tray).is_large(Thresholds())
       and not Run(duct).is_large(Thresholds(duct_width=0.9, duct_depth=0.5)))
    ok("dn without od uses the steel table", abs(Run(small).od - 0.0603) < 1e-9)

    n_fail = sum(1 for _, c in results if not c)
    print(f"{len(results) - n_fail} passed, {n_fail} failed")
    return 1 if n_fail else 0


# ----------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("check", help="run the coordination checks on one level; exit 1 on any P0 / P1",
                       description="Run the ENVELOPE / CROSS / PARALLEL / DRAIN / UNPLACED checks on one level's "
                                   "services-routes.json (and its crossings register) and write the CSV report.")
    s.add_argument("--routes", required=True, help="db/services-routes.json for the level")
    s.add_argument("--crossings", help="db/crossings.json (the crossings register)")
    s.add_argument("--stage", default="S6", help="S3 (zoning plans: small unplaced runs are INFO) or S6 (default)")
    s.add_argument("--out", help="report CSV (default reports/crossings-<level>.csv)")
    s.add_argument("--svg", help="also draw the plan to this SVG file")
    s.add_argument("--default-zone", help="soffit=..,ceiling=..[,hanger=..,ceiling_allowance=..,vclear=..,side=..,access=..] "
                                          "for points outside every zone polygon")
    s.add_argument("--large-duct-width", type=float, default=0.6, help="LARGE duct width threshold, m (0.6)")
    s.add_argument("--large-duct-depth", type=float, default=0.4, help="LARGE duct depth threshold, m (0.4)")
    s.add_argument("--large-pipe-dn", type=float, default=100, help="LARGE pipe DN threshold (100)")
    s.add_argument("--large-pipe-od", type=float, default=0.1, help="LARGE pipe od threshold, m (0.1)")
    s.add_argument("--large-tray-width", type=float, default=0.45, help="LARGE tray width threshold, m (0.45)")
    s.add_argument("--full", action="store_true", help="print INFO rows too")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("summary", help="counts per severity, type and verdict of a report CSV")
    s.add_argument("file")
    s.set_defaults(fn=cmd_summary)

    s = sub.add_parser("demo", help="write the sample level into <dir>, run check --stage S6 and print the report")
    s.add_argument("dir")
    s.set_defaults(fn=cmd_demo)

    s = sub.add_parser("selftest", help="assert the demo findings and the geometry helpers")
    s.set_defaults(fn=cmd_selftest)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
