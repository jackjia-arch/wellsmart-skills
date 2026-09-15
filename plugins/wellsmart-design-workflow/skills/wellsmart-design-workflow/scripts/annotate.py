#!/usr/bin/env python3
"""
annotate.py — deterministic annotation layout and checker for Well Smart HTML/SVG sheets.

Why this exists: a language model placing leader coordinates by hand produces crossing leaders,
leaders through other objects, labels at random heights and labels on top of lines. So the model
never places annotations. It DECLARES them (what to say, what it points at, which side), and this
module lays them out: labels in an aligned column, sorted in the same order as their targets so
leaders cannot cross, leaders anchored on the target's outline, routed around everything else,
dimensions in their own bands on the sides that carry no labels. Then the checker verifies the
finished SVG and reports every violation with coordinates, so a failed sheet is fixed, not argued about.

All units are PAPER millimetres (the sheet's viewBox).

Library use (from gen.py or any generator):
    from annotate import Layout
    L = Layout(view=(12, 12, 250, 200), text_mm=2.5)
    L.obstacle_rect(20, 30, 100, 90, tag="PIT", solid=False)   # a container outline: leaders may cross it
    c = L.obstacle_circle(60, 80, 8, tag="C1")                  # a solid object: leaders may not pass through it
    L.label("MAIN IN / TIE / OUT  5C 240 AL SWA", target=c, side="auto")
    L.dim(20, 120, ref=95, band=1, side="bottom")               # horizontal dimension 20→120, measured edge at y=95
    svg, report = L.render()                                    # svg: <g class="annotations">…</g>; report: dict

Command line:
    python3 annotate.py check <sheet.html> [border_mm]   # run the checker on a finished sheet, print JSON
    python3 annotate.py demo  <out.html>                 # the cable-pit example: before (hand-placed) / after (engine)

SVG classes the checker understands (the generator writes them):
    leader  dim  ext  label  dimtext   annotation roles
    outline                            container linework (walls, pit outlines) — leaders may cross it
    grid  halftone  qa  bg  border  furniture  arrow  bubble   ignored as obstacles
Everything else is SOLID geometry: a leader may touch exactly one such element — its target — at its end.
"""
from __future__ import annotations

import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

TOL = 0.35          # mm — touching within this is not a crossing
CJK = re.compile(r"[　-鿿＀-￯]")
IGNORED = {"grid", "halftone", "qa", "bg", "border", "furniture", "arrow", "bubble"}


# ----------------------------------------------------------------------------- geometry
def text_width(s: str, h: float) -> float:
    """Width estimate used everywhere in the company spec: Latin 0.55·h per char, CJK 1.0·h."""
    return sum((1.0 if CJK.match(ch) else 0.55) * h for ch in s)


def seg_seg(p1, p2, p3, p4) -> bool:
    """Proper intersection of two segments (shared endpoints within TOL do not count)."""
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    for a in (p1, p2):
        for b in (p3, p4):
            if math.dist(a, b) < TOL:
                return False
    d1, d2 = orient(p3, p4, p1), orient(p3, p4, p2)
    d3, d4 = orient(p1, p2, p3), orient(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and 0 not in (d1, d2, d3, d4)


def dist_point_seg(p, a, b) -> float:
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def seg_disc(p1, p2, c, r) -> bool:
    """Segment passes through the disc interior; touching the circumference at an endpoint is fine."""
    if dist_point_seg(c, p1, p2) >= r - TOL:
        return False
    return True


def seg_circle_outline(p1, p2, c, r) -> bool:
    """Segment crosses the circumference (used for hollow circles)."""
    d1, d2 = math.dist(p1, c) - r, math.dist(p2, c) - r
    if abs(d1) < TOL or abs(d2) < TOL:
        return False
    if (d1 > 0) != (d2 > 0):
        return True
    return d1 > 0 and dist_point_seg(c, p1, p2) < r - TOL


def seg_rect(p1, p2, rect) -> bool:
    """Segment passes through the rectangle interior (Liang–Barsky); edge touching is fine."""
    x, y, w, h = rect
    x0, y0, x1, y1 = x + TOL, y + TOL, x + w - TOL, y + h - TOL
    if x1 <= x0 or y1 <= y0:
        return False
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, p1[0] - x0), (dx, x1 - p1[0]), (-dy, p1[1] - y0), (dy, y1 - p1[1])):
        if p == 0:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    return t1 - t0 > 1e-6 and math.hypot(dx, dy) * (t1 - t0) > TOL


def rect_edges(rect):
    x, y, w, h = rect
    return [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)), ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]


def rect_rect(a, b, pad=0.0) -> bool:
    return not (a[0] + a[2] + pad <= b[0] or b[0] + b[2] + pad <= a[0] or
                a[1] + a[3] + pad <= b[1] or b[1] + b[3] + pad <= a[1])


# ----------------------------------------------------------------------------- primitives
@dataclass
class Prim:
    kind: str                      # circle | rect | seg | text
    data: tuple
    tag: str = ""
    role: str = "geom"             # geom | outline | leader | dim | ext | label | dimtext | text | ignored
    solid: bool = True             # solid: leaders may not pass through; outline: crossing allowed

    def bbox(self):
        if self.kind == "circle":
            cx, cy, r = self.data
            return (cx - r, cy - r, 2 * r, 2 * r)
        if self.kind in ("rect", "text"):
            return self.data
        x1, y1, x2, y2 = self.data
        return (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

    def hit_seg(self, p1, p2) -> bool:
        """Does the segment pass through / across this primitive (beyond mere touching)?"""
        if self.kind == "circle":
            c, r = (self.data[0], self.data[1]), self.data[2]
            return seg_disc(p1, p2, c, r) if self.solid else seg_circle_outline(p1, p2, c, r)
        if self.kind in ("rect", "text"):
            if self.solid or self.kind == "text":
                return seg_rect(p1, p2, self.data)
            return any(seg_seg(p1, p2, a, b) for a, b in rect_edges(self.data))
        x1, y1, x2, y2 = self.data
        return seg_seg(p1, p2, (x1, y1), (x2, y2))

    def hit_box(self, box, pad=0.0) -> bool:
        """Does a text box collide with this primitive?"""
        if self.kind == "circle":
            cx, cy, r = self.data
            bx, by, bw, bh = box
            nx, ny = min(max(cx, bx - pad), bx + bw + pad), min(max(cy, by - pad), by + bh + pad)
            d = math.dist((cx, cy), (nx, ny))
            return d < r if self.solid else (d < r and any(math.dist((cx, cy), q) > r for q in
                                                          ((bx, by), (bx + bw, by), (bx, by + bh), (bx + bw, by + bh)))) or d < r
        if self.kind in ("rect", "text"):
            if self.solid or self.kind == "text":
                return rect_rect(self.data, box, pad)
            padded = (box[0] - pad, box[1] - pad, box[2] + 2 * pad, box[3] + 2 * pad)
            return any(seg_rect(a, b, padded) for a, b in rect_edges(self.data))
        x1, y1, x2, y2 = self.data
        padded = (box[0] - pad, box[1] - pad, box[2] + 2 * pad, box[3] + 2 * pad)
        return seg_rect((x1, y1), (x2, y2), padded)

    def touches_point(self, p, tol=0.6) -> bool:
        if self.kind == "circle":
            cx, cy, r = self.data
            return abs(math.dist(p, (cx, cy)) - r) <= tol
        if self.kind in ("rect", "text"):
            return any(dist_point_seg(p, a, b) <= tol for a, b in rect_edges(self.data))
        x1, y1, x2, y2 = self.data
        return dist_point_seg(p, (x1, y1), (x2, y2)) <= tol

    def anchor_towards(self, p):
        """Point on the outline nearest to p — where a leader ends."""
        if self.kind == "circle":
            cx, cy, r = self.data
            ang = math.atan2(p[1] - cy, p[0] - cx)
            return (cx + r * math.cos(ang), cy + r * math.sin(ang))
        if self.kind in ("rect", "text"):
            x, y, w, h = self.data
            px, py = min(max(p[0], x), x + w), min(max(p[1], y), y + h)
            if x < px < x + w and y < py < y + h:
                d = min((px - x, "l"), (x + w - px, "r"), (py - y, "t"), (y + h - py, "b"))
                return {"l": (x, py), "r": (x + w, py), "t": (px, y), "b": (px, y + h)}[d[1]]
            return (px, py)
        x1, y1, x2, y2 = self.data
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            return (x1, y1)
        t = max(0.0, min(1.0, ((p[0] - x1) * dx + (p[1] - y1) * dy) / (dx * dx + dy * dy)))
        return (x1 + t * dx, y1 + t * dy)


# ----------------------------------------------------------------------------- layout
@dataclass
class LabelIntent:
    text: str
    target: Prim
    side: str = "auto"          # auto | left | right
    members: list = field(default_factory=list)   # identical targets: one label, leader to the reachable member

    @property
    def count(self):
        return len(self.members) if self.members else 1


class Layout:
    """Collect obstacles, label intents and dimensions; render aligned, non-crossing annotations."""

    def __init__(self, view, text_mm=2.5, column_gap=10.0, shoulder=3.0, max_leader=45.0, scale=1.0):
        self.view = view
        self.scale = scale                     # drawing scale denominator: dimension text = paper mm × scale
        self.h = text_mm
        self.gap = column_gap
        self.shoulder = shoulder
        self.max_leader = max_leader
        self.obstacles: list[Prim] = []
        self.labels: list[LabelIntent] = []
        self.dims: list[dict] = []
        self.keyed: list[tuple[int, str]] = []

    # --- declare geometry (everything drawn in the view)
    def obstacle_circle(self, cx, cy, r, tag="", solid=True):
        p = Prim("circle", (cx, cy, r), tag, "geom" if solid else "outline", solid); self.obstacles.append(p); return p

    def obstacle_rect(self, x, y, w, h, tag="", solid=True):
        p = Prim("rect", (x, y, w, h), tag, "geom" if solid else "outline", solid); self.obstacles.append(p); return p

    def obstacle_seg(self, x1, y1, x2, y2, tag=""):
        p = Prim("seg", (x1, y1, x2, y2), tag); self.obstacles.append(p); return p

    def obstacle_text(self, x, y, w, h, tag=""):
        p = Prim("text", (x, y, w, h), tag, "text"); self.obstacles.append(p); return p

    # --- declare annotations
    def label(self, text, target, side="auto", members=None):
        if isinstance(target, tuple):
            target = Prim(target[0], tuple(target[1:]))
        li = LabelIntent(text, target, side, list(members or []))
        self.labels.append(li)
        return li

    def dim(self, a, b, ref, band=1, side="bottom", text=None):
        """Linear dimension between paper coordinates a and b. ref = y (bottom/top) or x (left/right) of the
        measured edge; band 1 is nearest the geometry, band 2 outside it (7 mm apart). The text is the real
        size (paper × scale) unless given."""
        self.dims.append({"a": a, "b": b, "ref": ref, "band": band, "side": side, "text": text})

    # --- internals
    def envelope(self):
        bs = [o.bbox() for o in self.obstacles] or [self.view]
        return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[0] + b[2] for b in bs), max(b[1] + b[3] for b in bs))

    def _dim_geometry(self, env):
        x0, y0, x1, y1 = env
        out = []
        for d in self.dims:
            off = 8 + 7 * (d["band"] - 1)
            text = d["text"] if d["text"] is not None else f"{round(abs(d['b'] - d['a']) * self.scale):d}"
            if d["side"] in ("bottom", "top"):
                yb = y1 + off if d["side"] == "bottom" else y0 - off
                gap, over = (1.5, 2) if d["side"] == "bottom" else (-1.5, -2)
                out.append({"side": d["side"], "line": (d["a"], yb, d["b"], yb), "text": text, "vertical": False,
                            "exts": [(d["a"], d["ref"] + gap, d["a"], yb + over), (d["b"], d["ref"] + gap, d["b"], yb + over)],
                            "tx": (d["a"] + d["b"]) / 2, "ty": yb - 1.0, "extent": yb + over})
            else:
                xb = x0 - off if d["side"] == "left" else x1 + off
                gap, over = (-1.5, -2) if d["side"] == "left" else (1.5, 2)
                out.append({"side": d["side"], "line": (xb, d["a"], xb, d["b"]), "text": text, "vertical": True,
                            "exts": [(d["ref"] + gap, d["a"], xb + over, d["a"]), (d["ref"] + gap, d["b"], xb + over, d["b"])],
                            "tx": xb - 1.0 if d["side"] == "left" else xb + 1.0 + self.h, "ty": (d["a"] + d["b"]) / 2, "extent": xb + over})
        return out

    def render(self):
        env = self.envelope()
        x0, y0, x1, y1 = env
        vx, vy, vw, vh = self.view
        dims = self._dim_geometry(env)
        dim_prims: list[Prim] = []
        for d in dims:
            dim_prims.append(Prim("seg", d["line"], role="dim"))
            for e in d["exts"]:
                dim_prims.append(Prim("seg", e, role="ext"))
            tw = text_width(d["text"], self.h)
            box = (d["tx"] - self.h, d["ty"] - tw / 2, self.h, tw) if d["vertical"] else (d["tx"] - tw / 2, d["ty"] - self.h, tw, self.h)
            dim_prims.append(Prim("text", box, d["text"], "dimtext"))
        dim_sides = {d["side"] for d in dims}
        right_x = max([x1] + [d["extent"] for d in dims if d["side"] == "right"]) + self.gap
        left_x = min([x0] + [d["extent"] for d in dims if d["side"] == "left"]) - self.gap
        allow = {"right": "right" not in dim_sides, "left": "left" not in dim_sides}
        if not (allow["right"] or allow["left"]):
            allow["right"] = True
        cols = {"right": [], "left": []}
        for li in self.labels:
            side = li.side
            if side == "auto":
                tb = li.target.bbox()
                side = "right" if (tb[0] + tb[2] / 2) >= (x0 + x1) / 2 else "left"
            if not allow[side]:
                side = "right" if allow["right"] else "left"
            cols[side].append(li)
        pitch_of = lambda li: (li.text.count("\n") + 1) * 1.5 * self.h + 1.5
        placed = []
        keyed_counter = [0]
        for side, items in cols.items():
            if not items:
                continue
            xcol = right_x if side == "right" else left_x
            sx = -1 if side == "right" else 1     # same row: nearest target to the column gets the slot nearest the row
            items.sort(key=lambda li: (round(li.target.bbox()[1] + li.target.bbox()[3] / 2, 1),
                                       sx * (li.target.bbox()[0] + li.target.bbox()[2] / 2)))   # order = target order → no crossings
            ys = [li.target.bbox()[1] + li.target.bbox()[3] / 2 for li in items]
            for i in range(1, len(items)):
                ys[i] = max(ys[i], ys[i - 1] + pitch_of(items[i - 1]))
            bottom = vy + vh - 3
            if ys and ys[-1] + pitch_of(items[-1]) > bottom:
                shift = ys[-1] + pitch_of(items[-1]) - bottom
                ys = [y - shift for y in ys]
            for li, y in zip(items, ys):
                placed.append(self._route(li, side, xcol, y, dim_prims, placed, keyed_counter))
        self._number_keyed(placed)
        parts = ['<g class="annotations">']
        for d in dims:
            l = d["line"]
            parts.append(f'<line class="dim" x1="{l[0]:.2f}" y1="{l[1]:.2f}" x2="{l[2]:.2f}" y2="{l[3]:.2f}"/>')
            for e in d["exts"]:
                parts.append(f'<line class="ext" x1="{e[0]:.2f}" y1="{e[1]:.2f}" x2="{e[2]:.2f}" y2="{e[3]:.2f}"/>')
            parts += self._arrow((l[0], l[1]), (l[2], l[3]), both=True)
            rot = f' transform="rotate(-90 {d["tx"]:.2f} {d["ty"]:.2f})"' if d["vertical"] else ""
            parts.append(f'<text class="dimtext" x="{d["tx"]:.2f}" y="{d["ty"]:.2f}" font-size="{self.h}" text-anchor="middle"{rot}>{d["text"]}</text>')
        for p in placed:
            parts += p["svg"]
        parts.append("</g>")
        report = self.check_placed(placed, dim_prims)
        report["keyed_notes"] = list(self.keyed)
        return "\n".join(parts), report

    def _arrow(self, a, b, both=False):
        out = []
        def head(tip, frm):
            ang = math.atan2(tip[1] - frm[1], tip[0] - frm[0])
            l, w = 2.5, 0.8
            p1 = (tip[0] - l * math.cos(ang) + w * math.sin(ang), tip[1] - l * math.sin(ang) - w * math.cos(ang))
            p2 = (tip[0] - l * math.cos(ang) - w * math.sin(ang), tip[1] - l * math.sin(ang) + w * math.cos(ang))
            return f'<polygon class="arrow" points="{tip[0]:.2f},{tip[1]:.2f} {p1[0]:.2f},{p1[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}"/>'
        out.append(head(b, a))
        if both:
            out.append(head(a, b))
        return out

    def _route(self, li, side, xcol, y, dim_prims, placed, keyed_counter):
        """Shoulder + straight leader from the column to the target outline. Try every member of a group
        (nearest to the column first); if none is reachable without crossing anything, use a keyed note."""
        sgn = -1 if side == "right" else 1
        shoulder_in = (xcol + sgn * self.shoulder, y)
        text = li.text + (f"  ×{li.count}" if li.count > 1 and "×" not in li.text else "")
        lines = text.split("\n")
        tw = max(text_width(s, self.h) for s in lines)
        th = len(lines) * 1.5 * self.h
        if side == "right":
            tx, anchor_attr, tbox = xcol + 1.5, "start", (xcol + 1.5, y - self.h, tw, th + 0.5)
        else:
            tx, anchor_attr, tbox = xcol - 1.5, "end", (xcol - 1.5 - tw, y - self.h, tw, th + 0.5)
        candidates = [li.target] + [m for m in li.members if m is not li.target]
        candidates.sort(key=lambda t: math.dist(shoulder_in, (t.bbox()[0] + t.bbox()[2] / 2, t.bbox()[1] + t.bbox()[3] / 2)))
        for target in candidates:
            anchor = target.anchor_towards(shoulder_in)
            segs = [((xcol, y), shoulder_in), (shoulder_in, anchor)]
            if math.dist(shoulder_in, anchor) <= self.max_leader and self._clear(segs, target, dim_prims, placed, tbox):
                svg = [f'<path class="leader" data-label="{self._esc(text)}" d="M {xcol:.2f} {y:.2f} L {shoulder_in[0]:.2f} '
                       f'{shoulder_in[1]:.2f} L {anchor[0]:.2f} {anchor[1]:.2f}"/>'] + self._arrow(shoulder_in, anchor)
                svg.append(self._text(tx, y, lines, anchor_attr, "label", text))
                return {"text": text, "segs": segs, "tbox": tbox, "target": target, "svg": svg, "side": side, "keyed": False}
        # keyed note: numbered bubble beside the target with a ≤ 5 mm leader; the text goes to the notes list
        keyed_counter[0] += 1
        n = keyed_counter[0]
        target = li.target
        cx_, cy_, r_ = self._centre_radius(target)
        best = None
        for ang in (315, 45, 225, 135, 0, 90, 180, 270):
            a = math.radians(ang)
            px, py = cx_ + (r_ + 4.5) * math.cos(a), cy_ + (r_ + 4.5) * math.sin(a)
            bubble_box = (px - 2, py - 2, 4, 4)
            anchor = target.anchor_towards((px, py))
            if not any(o.hit_box(bubble_box, pad=0.5) for o in self.obstacles if o is not target) and \
               not any(rect_rect(bubble_box, p["tbox"], pad=0.5) for p in placed) and \
               self._clear([((px, py), anchor)], target, dim_prims, placed, bubble_box):
                best = (px, py, anchor)
                break
        if best is None:
            px, py = cx_ + r_ + 4.5, cy_ - r_ - 4.5
            best = (px, py, target.anchor_towards((px, py)))
        px, py, anchor = best
        return {"text": text, "segs": [((px, py), anchor)], "tbox": (px - 2, py - 2, 4, 4), "target": target, "svg": [],
                "side": side, "keyed": True, "bubble": (px, py, anchor)}

    def _number_keyed(self, placed):
        """Keyed notes are numbered left→right, top→bottom by target, whatever order they were placed in."""
        keyed = [p for p in placed if p["keyed"]]
        keyed.sort(key=lambda p: (round(p["target"].bbox()[1], 0), p["target"].bbox()[0]))
        self.keyed = []
        for n, p in enumerate(keyed, 1):
            px, py, anchor = p["bubble"]
            self.keyed.append((n, p["text"]))
            p["svg"] = [f'<path class="leader keyed" data-label="{n}" d="M {px:.2f} {py:.2f} L {anchor[0]:.2f} {anchor[1]:.2f}"/>',
                        f'<circle class="bubble" cx="{px:.2f}" cy="{py:.2f}" r="2"/>',
                        f'<text class="label" data-label="{n}" x="{px:.2f}" y="{py + 0.9:.2f}" font-size="{self.h}" text-anchor="middle">{n}</text>']

    @staticmethod
    def _centre_radius(p):
        b = p.bbox()
        return b[0] + b[2] / 2, b[1] + b[3] / 2, max(b[2], b[3]) / 2

    def _clear(self, segs, target, dim_prims, placed, tbox):
        for s in segs:
            for o in self.obstacles:
                if o is target or not o.solid and o.kind != "text":
                    continue           # containers may be crossed; solids may not
                if o.hit_seg(*s):
                    return False
            for d in dim_prims:
                if d.hit_seg(*s):
                    return False
            for p in placed:
                if any(seg_seg(s[0], s[1], s2[0], s2[1]) for s2 in p["segs"]) or seg_rect(s[0], s[1], p["tbox"]):
                    return False
        if any(rect_rect(tbox, p["tbox"], pad=1.0) for p in placed):
            return False
        if any(o.hit_box(tbox, pad=1.0) for o in self.obstacles):
            return False
        if any(d.hit_box(tbox, pad=1.0) for d in dim_prims):
            return False
        return True

    def _text(self, x, y, lines, anchor, cls, label):
        y0 = y + self.h * 0.35
        if len(lines) == 1:
            return f'<text class="{cls}" data-label="{self._esc(label)}" x="{x:.2f}" y="{y0:.2f}" font-size="{self.h}" text-anchor="{anchor}">{self._esc(lines[0])}</text>'
        out = [f'<text class="{cls}" data-label="{self._esc(label)}" x="{x:.2f}" y="{y0:.2f}" font-size="{self.h}" text-anchor="{anchor}">']
        for i, s in enumerate(lines):
            out.append(f'<tspan x="{x:.2f}" dy="{0 if i == 0 else 1.5 * self.h:.2f}">{self._esc(s)}</tspan>')
        return "".join(out) + "</text>"

    @staticmethod
    def _esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("\n", " / ")

    def check_placed(self, placed, dim_prims):
        rep = {"leader_crossings": 0, "leader_through_geometry": 0, "leader_over_dimension": 0, "text_over_line": 0,
               "text_over_text": 0, "unaligned_labels": 0, "order_mismatch": 0, "leader_too_long": 0,
               "keyed": sum(1 for p in placed if p["keyed"]), "details": []}
        for i, p in enumerate(placed):
            for s in p["segs"]:
                if math.dist(*s) > self.max_leader:
                    rep["leader_too_long"] += 1
                for o in self.obstacles:
                    if o is not p["target"] and o.solid and o.hit_seg(*s):
                        rep["leader_through_geometry"] += 1; rep["details"].append(f"leader '{p['text']}' through {o.kind} {o.tag}")
                for d in dim_prims:
                    if d.hit_seg(*s):
                        rep["leader_over_dimension"] += 1; rep["details"].append(f"leader '{p['text']}' crosses a dimension")
                for q in placed[i + 1:]:
                    if any(seg_seg(s[0], s[1], s2[0], s2[1]) for s2 in q["segs"]):
                        rep["leader_crossings"] += 1; rep["details"].append(f"leaders cross: '{p['text']}' × '{q['text']}'")
            for q in placed[i + 1:]:
                if rect_rect(p["tbox"], q["tbox"], pad=0.3):
                    rep["text_over_text"] += 1
            if any(o.hit_box(p["tbox"]) for o in self.obstacles) or any(d.hit_box(p["tbox"]) for d in dim_prims):
                rep["text_over_line"] += 1; rep["details"].append(f"text '{p['text']}' on linework")
        for side in ("right", "left"):
            col = [p for p in placed if p["side"] == side and not p["keyed"]]
            xs = {round(p["tbox"][0] if side == "right" else p["tbox"][0] + p["tbox"][2], 1) for p in col}
            if len(xs) > 1:
                rep["unaligned_labels"] += len(xs) - 1
            ys_lab = [p["tbox"][1] for p in col]
            ys_tgt = [p["target"].bbox()[1] + p["target"].bbox()[3] / 2 for p in col]
            if ys_lab != sorted(ys_lab) or ys_tgt != sorted(ys_tgt):
                rep["order_mismatch"] += 1
        rep["pass"] = all(rep[k] == 0 for k in ("leader_crossings", "leader_through_geometry", "leader_over_dimension",
                                                 "text_over_line", "text_over_text", "unaligned_labels", "order_mismatch",
                                                 "leader_too_long"))
        return rep


# ----------------------------------------------------------------------------- checker for finished SVG files
def _num(v, default=0.0):
    try:
        return float(re.sub(r"[a-z%]+$", "", v.strip()))
    except Exception:
        return default


ROLE_WORDS = ("leader", "dim", "ext", "label", "dimtext", "outline") + tuple(IGNORED)


def parse_svg(svg_text: str) -> list[Prim]:
    """Extract primitives with roles from an SVG string (only translate() transforms are honoured)."""
    svg_text = re.sub(r'\sxmlns(:\w+)?="[^"]+"', "", svg_text)
    root = ET.fromstring(svg_text)
    prims: list[Prim] = []

    def walk(el, ox=0.0, oy=0.0, inherited=""):
        tag = el.tag.split("}")[-1]
        if tag in ("style", "script", "defs", "title", "desc") or el.get("id") == "qa":
            return
        cls = (el.get("class", "") + " " + inherited).strip()
        m = re.search(r"translate\(\s*([-\d.]+)[ ,]+([-\d.]+)", el.get("transform", ""))
        if m:
            ox, oy = ox + float(m.group(1)), oy + float(m.group(2))
        role = "geom"
        for r in ROLE_WORDS:
            if re.search(rf"(^|\s){r}(\s|$)", cls):
                role = "ignored" if r in IGNORED else r
                break
        solid = role != "outline"
        name = el.get("data-label", "") or el.get("id", "")
        if role != "ignored":
            if tag == "circle":
                prims.append(Prim("circle", (_num(el.get("cx", "0")) + ox, _num(el.get("cy", "0")) + oy, _num(el.get("r", "0"))), name, role, solid))
            elif tag == "rect":
                prims.append(Prim("rect", (_num(el.get("x", "0")) + ox, _num(el.get("y", "0")) + oy, _num(el.get("width", "0")), _num(el.get("height", "0"))), name, role, solid))
            elif tag == "line":
                prims.append(Prim("seg", (_num(el.get("x1", "0")) + ox, _num(el.get("y1", "0")) + oy, _num(el.get("x2", "0")) + ox, _num(el.get("y2", "0")) + oy), name, role, solid))
            elif tag in ("polyline", "polygon"):
                pts = re.findall(r"[-\d.]+", el.get("points", ""))
                xy = [(float(pts[i]) + ox, float(pts[i + 1]) + oy) for i in range(0, len(pts) - 1, 2)]
                if tag == "polygon" and xy:
                    xy.append(xy[0])
                for a, b in zip(xy, xy[1:]):
                    prims.append(Prim("seg", (a[0], a[1], b[0], b[1]), name, role, solid))
            elif tag == "path":
                cur = start = None
                for cmd, args in re.findall(r"([MLHVZmlhvz])\s*([^MLHVZmlhvz]*)", el.get("d", "")):
                    nums = [float(n) for n in re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", args)]
                    if cmd in "Mm":
                        for i in range(0, len(nums) - 1, 2):
                            p = (nums[i] + ox, nums[i + 1] + oy) if cmd == "M" or cur is None else (cur[0] + nums[i], cur[1] + nums[i + 1])
                            if i == 0:
                                cur = start = p
                            else:
                                prims.append(Prim("seg", (*cur, *p), name, role, solid)); cur = p
                    elif cmd in "Ll":
                        for i in range(0, len(nums) - 1, 2):
                            p = (nums[i] + ox, nums[i + 1] + oy) if cmd == "L" else (cur[0] + nums[i], cur[1] + nums[i + 1])
                            prims.append(Prim("seg", (*cur, *p), name, role, solid)); cur = p
                    elif cmd in "Hh":
                        for n in nums:
                            p = (n + ox, cur[1]) if cmd == "H" else (cur[0] + n, cur[1])
                            prims.append(Prim("seg", (*cur, *p), name, role, solid)); cur = p
                    elif cmd in "Vv":
                        for n in nums:
                            p = (cur[0], n + oy) if cmd == "V" else (cur[0], cur[1] + n)
                            prims.append(Prim("seg", (*cur, *p), name, role, solid)); cur = p
                    elif cmd in "Zz" and cur and start:
                        prims.append(Prim("seg", (*cur, *start), name, role, solid)); cur = start
            elif tag == "text":
                size = _num(el.get("font-size", "2.5"), 2.5)
                spans = [s for s in el if s.tag.split("}")[-1] == "tspan"]
                lines = [("".join(s.itertext())).strip() for s in spans] if spans else ["".join(el.itertext()).strip()]
                txt = " / ".join(lines)
                w = max((text_width(s, size) for s in lines), default=0)
                h = len(lines) * 1.5 * size - 0.5 * size
                x, y = _num(el.get("x", "0")) + ox, _num(el.get("y", "0")) + oy
                anchor = el.get("text-anchor", "start")
                x0 = x - w if anchor == "end" else x - w / 2 if anchor == "middle" else x
                if re.search(r"rotate\(\s*-?90", el.get("transform", "")):
                    prims.append(Prim("text", (x - size, y - w / 2, size, w), name or txt, role if role != "geom" else "text"))
                else:
                    prims.append(Prim("text", (x0, y - size * 0.8, w, h), name or txt, role if role != "geom" else "text"))
        for ch in el:
            walk(ch, ox, oy, cls if tag == "g" else "")

    walk(root)
    return prims


def check_svg(svg_text: str, size_mm=(420, 297), border=10.0) -> dict:
    prims = parse_svg(svg_text)
    leaders = [p for p in prims if p.role == "leader"]
    dims = [p for p in prims if p.role in ("dim", "ext")]
    geom = [p for p in prims if p.role in ("geom", "outline")]
    texts = [p for p in prims if p.kind == "text"]
    labels = [p for p in prims if p.role == "label" and p.kind == "text"]
    rep = {"leader_crossings": 0, "leader_through_geometry": 0, "leader_over_dimension": 0, "leader_over_outline": 0,
           "text_over_line": 0, "text_over_text": 0, "leader_too_long": 0, "outside_border": 0, "details": []}
    W, H = size_mm
    by_label: dict[str, list[Prim]] = {}
    for l in leaders:
        by_label.setdefault(l.tag or f"leader@{l.data[0]:.1f},{l.data[1]:.1f}", []).append(l)
    groups = list(by_label.items())
    for gi, (name, segs) in enumerate(groups):
        ends = [(segs[-1].data[2], segs[-1].data[3]), (segs[0].data[0], segs[0].data[1])]
        target = next((g for e in ends for g in geom if g.touches_point(e)), None)
        if sum(math.dist((s.data[0], s.data[1]), (s.data[2], s.data[3])) for s in segs) > 60:
            rep["leader_too_long"] += 1; rep["details"].append(f"leader {name!r} longer than 60 mm")
        for s in segs:
            a, b = (s.data[0], s.data[1]), (s.data[2], s.data[3])
            for g in geom:
                if g is target or not g.hit_seg(a, b):
                    continue
                if g.solid:
                    rep["leader_through_geometry"] += 1; rep["details"].append(f"leader {name!r} through {g.kind} {g.tag!r} at {tuple(round(v, 1) for v in g.bbox())}")
                else:
                    rep["leader_over_outline"] += 1
            for d in dims:
                if d.hit_seg(a, b):
                    rep["leader_over_dimension"] += 1; rep["details"].append(f"leader {name!r} crosses dimension line {tuple(round(v, 1) for v in d.data)}")
            for name2, segs2 in groups[gi + 1:]:
                if any(seg_seg(a, b, (s2.data[0], s2.data[1]), (s2.data[2], s2.data[3])) for s2 in segs2):
                    rep["leader_crossings"] += 1; rep["details"].append(f"leaders cross: {name!r} × {name2!r}")
            for t in texts:
                if t.tag != name and seg_rect(a, b, t.data):
                    rep["text_over_line"] += 1; rep["details"].append(f"leader {name!r} through text {t.tag!r}")
    for i, t in enumerate(texts):
        for u in texts[i + 1:]:
            if rect_rect(t.data, u.data, pad=-0.3):
                rep["text_over_text"] += 1; rep["details"].append(f"text overlap: {t.tag!r} × {u.tag!r}")
        for g in geom + dims:
            if g.kind == "text":
                continue
            if g.hit_box(t.data):
                rep["text_over_line"] += 1; rep["details"].append(f"linework through text {t.tag!r} at {tuple(round(v, 1) for v in t.data)}")
        x, y, w, h = t.data
        if x < border or y < border or x + w > W - border or y + h > H - border:
            rep["outside_border"] += 1; rep["details"].append(f"text {t.tag!r} outside the border")
    lefts = sorted(round(p.data[0], 1) for p in labels)
    clusters = 1 if lefts else 0
    for a, b in zip(lefts, lefts[1:]):
        if b - a > 0.5:
            clusters += 1
    rep["label_columns"] = clusters
    rep["annotated_items"] = len(texts) + len(groups) + sum(1 for d in dims if d.role == "dim")
    rep["pass"] = all(rep[k] == 0 for k in ("leader_crossings", "leader_through_geometry", "leader_over_dimension",
                                             "text_over_line", "text_over_text", "leader_too_long", "outside_border"))
    return rep


def check_file(path: str, border=10.0) -> dict:
    html = open(path, encoding="utf-8").read()
    m = re.search(r"<svg[^>]*viewBox=\"([^\"]+)\"[^>]*>.*?</svg>", html, re.S)
    if not m:
        return {"error": "no svg with a viewBox"}
    vb = [float(v) for v in m.group(1).split()]
    return check_svg(m.group(0), size_mm=(vb[2], vb[3]), border=border)


# ----------------------------------------------------------------------------- demo (the cable-pit example)
def demo(out_path: str) -> str:
    """The cable pit that came back with crossed leaders — three 240 mm² feeders, four 25 mm² consumer
    cables, pit 400 wide — drawn at 1:10 twice: BEFORE as hand-placed, AFTER laid out by the engine."""
    S = 10.0
    R = lambda v: v / S
    style = ('<style>text{font-family:Arial,Helvetica,sans-serif;paint-order:stroke fill;stroke:#fff;stroke-width:0.7;'
             'stroke-linejoin:round;fill:#000}.outline{fill:none;stroke:#000;stroke-width:0.5}.cab{fill:#7030A0;fill-opacity:0.15;'
             'stroke:#7030A0;stroke-width:0.5}.leader,.dim,.ext{fill:none;stroke:#000;stroke-width:0.25}.arrow{fill:#000;stroke:none}'
             '.bubble{fill:#fff;stroke:#000;stroke-width:0.25}.bad{stroke:#E00000!important}.title{font-size:3.5px;font-weight:bold}'
             '.cap{font-size:2.5px;fill:#555}.furniture{fill:none;stroke:#bbb;stroke-width:0.25;stroke-dasharray:1 1}</style>')
    PIT_Y, W, D = 14, 400, 250

    def geometry(px):
        g = [f'<rect class="outline" x="{px:.2f}" y="{PIT_Y:.2f}" width="{R(W):.2f}" height="{R(D):.2f}"/>']
        big = [(px + R(80 + i * 120), PIT_Y + R(170), R(22.5)) for i in range(3)]
        small = [(px + R(60 + i * 90), PIT_Y + R(70), R(8)) for i in range(4)]
        for cx, cy, r in big + small:
            g.append(f'<circle class="cab" cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}"/>')
        return g, big, small

    parts = ['<svg viewBox="0 0 210 60" width="210mm" height="60mm">', style,
             '<rect class="bg" x="0" y="0" width="210" height="60" fill="#fff"/>']
    # ---- BEFORE: labels at arbitrary heights; the upper label points at the lower object and vice versa → X
    px = 44
    g, big, small = geometry(px)
    parts += g
    parts.append('<text class="title" x="8" y="9">BEFORE — HAND-PLACED BY THE MODEL</text>')
    parts.append(f'<path class="leader bad" data-label="MAINS" d="M 40 27 L {big[0][0] - big[0][2] * 0.7:.2f} {big[0][1] - big[0][2] * 0.7:.2f}"/>')
    parts.append('<text class="label" data-label="MAINS" x="40" y="26" font-size="2.5" text-anchor="end"><tspan x="40" dy="0">MAINS IN / TIE / OUT</tspan><tspan x="40" dy="3.75">5C 240 AL SWA</tspan></text>')
    parts.append(f'<path class="leader bad" data-label="CONSUMER" d="M 40 40 L {small[0][0] - small[0][2]:.2f} {small[0][1]:.2f}"/>')
    parts.append('<text class="label" data-label="CONSUMER" x="40" y="41" font-size="2.5" text-anchor="end">CONSUMER ×4 5C 25 CU</text>')
    yb = PIT_Y + R(D) + 8
    parts.append(f'<line class="dim" x1="{px:.2f}" y1="{yb:.2f}" x2="{px + R(W):.2f}" y2="{yb:.2f}"/>')
    parts.append(f'<line class="ext bad" x1="{px + R(W):.2f}" y1="{PIT_Y + 1.5:.2f}" x2="{px + R(W):.2f}" y2="{yb + 2:.2f}"/>')
    parts.append(f'<line class="ext" x1="{px:.2f}" y1="{PIT_Y + R(D) + 1.5:.2f}" x2="{px:.2f}" y2="{yb + 2:.2f}"/>')
    parts.append(f'<text class="dimtext" x="{px + R(W) / 2:.2f}" y="{yb - 1:.2f}" font-size="2.5" text-anchor="middle">400</text>')
    # a depth dimension put on the same side as the labels — its line and extension lines cut both leaders
    xd = px - 6
    parts.append(f'<line class="dim bad" x1="{xd:.2f}" y1="{PIT_Y:.2f}" x2="{xd:.2f}" y2="{PIT_Y + R(D):.2f}"/>')
    parts.append(f'<line class="ext" x1="{px - 1.5:.2f}" y1="{PIT_Y:.2f}" x2="{xd - 2:.2f}" y2="{PIT_Y:.2f}"/>')
    parts.append(f'<line class="ext" x1="{px - 1.5:.2f}" y1="{PIT_Y + R(D):.2f}" x2="{xd - 2:.2f}" y2="{PIT_Y + R(D):.2f}"/>')
    parts.append(f'<text class="dimtext" x="{xd - 1:.2f}" y="{PIT_Y + R(D) / 2:.2f}" font-size="2.5" text-anchor="middle" transform="rotate(-90 {xd - 1:.2f} {PIT_Y + R(D) / 2:.2f})">250</text>')
    # ---- AFTER: declared annotations, engine layout
    ox = 118
    g, big, small = geometry(ox)
    parts += g
    parts.append(f'<text class="title" x="{ox - 6}" y="9">AFTER — DECLARED, LAID OUT BY annotate.py</text>')
    L = Layout(view=(ox - 8, 12, 100, 62), text_mm=2.5, column_gap=8, max_leader=45, scale=S)
    L.obstacle_rect(ox, PIT_Y, R(W), R(D), tag="PIT", solid=False)
    bigs = [L.obstacle_circle(cx, cy, r, tag=f"BIG{i}") for i, (cx, cy, r) in enumerate(big)]
    smalls = [L.obstacle_circle(cx, cy, r, tag=f"SMALL{i}") for i, (cx, cy, r) in enumerate(small)]
    L.label("MAINS IN / TIE / OUT\n5C 240 AL SWA", target=bigs[2], members=bigs, side="right")
    L.label("CONSUMER 5C 25 CU SWA", target=smalls[3], members=smalls, side="right")
    L.dim(ox, ox + R(W), ref=PIT_Y + R(D), band=1, side="bottom")
    svg, rep = L.render()
    parts.append(svg)
    parts.append(f'<text class="cap" x="{ox - 6}" y="57">ENGINE CHECK {"PASS" if rep["pass"] else "FAIL"}: crossings {rep["leader_crossings"]} · through objects {rep["leader_through_geometry"]} · over dims {rep["leader_over_dimension"]}</text>')
    parts.append("</svg>")
    svg_all = "\n".join(parts)
    file_rep = check_svg(svg_all, size_mm=(210, 60), border=0)
    html = ('<!DOCTYPE html><html lang="en-AU"><head><meta charset="UTF-8"><title>annotate.py demo</title></head><body>'
            + svg_all + f'<pre>{json.dumps(file_rep, indent=1, ensure_ascii=False)}</pre></body></html>')
    open(out_path, "w", encoding="utf-8").write(html)
    print(json.dumps({"engine_report_after": rep, "file_check_both_halves": file_rep}, indent=1, ensure_ascii=False))
    return svg_all


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "check":
        print(json.dumps(check_file(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 10.0), indent=1, ensure_ascii=False))
    elif len(sys.argv) >= 3 and sys.argv[1] == "demo":
        demo(sys.argv[2])
    else:
        print(__doc__)
