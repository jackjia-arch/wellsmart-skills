/* Well Smart sheet QA overlay — embed as the ONLY <script> in every HTML/SVG sheet.
   Runs on load, draws red dashed boxes into <g id="qa"> for every failure, prints a badge at (12, 292)
   and writes the counts to window.WS_QA (and into #manifest JSON if present). Screen only: add
   @media print { #qa { display:none } } to the sheet CSS. Units: viewBox mm.
   Checks: 1 text outside the 10 mm border · 2 text over text (>0.3 mm) · 3 element outside the sheet ·
   4 colour outside the palette · 5 leader crossing leader / dimension line · 6 leader through a solid
   object other than its target · 7 linework through text · 8 density (annotated items vs threshold) ·
   9 label columns (labels on one side share one x). Classes: leader dim ext label dimtext outline
   grid halftone qa bg border furniture arrow bubble — as in scripts/annotate.py. */
(function () {
  var PALETTE = ["#000000","#808080","#B3B3B3","#E00000","#0055D4","#D400AA","#009933","#F07800","#007A7A",
                 "#8B0000","#0099CC","#E8407A","#8B4513","#6B8E23","#B8860B","#7030A0","#4A6A8A","#E6E6E6"];
  var DENSITY = { A3: 60, A1: 150 };
  var svg = document.querySelector("svg"); if (!svg) return;
  var vb = svg.viewBox.baseVal, W = vb.width, H = vb.height, BORDER = 10, TOL = 0.35;
  var size = W > 600 ? "A1" : "A3";
  var qa = document.getElementById("qa"); if (!qa) { qa = document.createElementNS(svg.namespaceURI, "g"); qa.id = "qa"; svg.appendChild(qa); }
  var fails = [], counts = { outside_border: 0, text_overlap: 0, outside_sheet: 0, palette: 0, leader_crossings: 0,
                             leader_through_geometry: 0, text_over_lines: 0, density: 0, unaligned_labels: 0 };
  function hasCls(el, c) { return (" " + (el.getAttribute("class") || "") + " ").indexOf(" " + c + " ") >= 0; }
  function roleOf(el) { var e = el; while (e && e !== svg) { var cls = e.getAttribute("class") || "";
      var m = cls.match(/\b(leader|dim|ext|label|dimtext|outline|grid|halftone|qa|bg|border|furniture|arrow|bubble)\b/); if (m) return m[1]; e = e.parentNode; } return "geom"; }
  var IGN = { grid:1, halftone:1, qa:1, bg:1, border:1, furniture:1, arrow:1, bubble:1 };
  var ctm = svg.getScreenCTM(); var inv = ctm.inverse();
  function mm(r) { var a = svg.createSVGPoint(); a.x = r.left; a.y = r.top; var b = svg.createSVGPoint(); b.x = r.right; b.y = r.bottom;
      a = a.matrixTransform(inv); b = b.matrixTransform(inv); return { x: a.x, y: a.y, w: b.x - a.x, h: b.y - a.y }; }
  function mark(box, why) { var r = document.createElementNS(svg.namespaceURI, "rect");
      r.setAttribute("x", box.x - 0.5); r.setAttribute("y", box.y - 0.5); r.setAttribute("width", Math.max(box.w, 0.1) + 1); r.setAttribute("height", Math.max(box.h, 0.1) + 1);
      r.setAttribute("fill", "none"); r.setAttribute("stroke", "#FF0000"); r.setAttribute("stroke-width", "0.3"); r.setAttribute("stroke-dasharray", "2 1"); qa.appendChild(r); fails.push(why); console.warn("QA:", why); }
  // --- collect segments (leaders, dims, geometry) from lines / polylines / paths (M L H V Z) / rect edges / circles
  function segsOf(el) { var out = [], t = el.tagName.toLowerCase(), n = function (a) { return parseFloat(el.getAttribute(a)) || 0; };
      var off = { x: 0, y: 0 }, e = el; while (e && e !== svg) { var tr = (e.getAttribute("transform") || "").match(/translate\(\s*([-\d.]+)[ ,]+([-\d.]+)/); if (tr) { off.x += +tr[1]; off.y += +tr[2]; } e = e.parentNode; }
      if (t === "line") out.push([[n("x1") + off.x, n("y1") + off.y], [n("x2") + off.x, n("y2") + off.y]]);
      else if (t === "polyline" || t === "polygon") { var p = (el.getAttribute("points") || "").match(/[-\d.]+/g) || [], pts = []; for (var i = 0; i + 1 < p.length; i += 2) pts.push([+p[i] + off.x, +p[i + 1] + off.y]); if (t === "polygon" && pts.length) pts.push(pts[0]); for (i = 1; i < pts.length; i++) out.push([pts[i - 1], pts[i]]); }
      else if (t === "path") { var d = el.getAttribute("d") || "", cur = null, start = null, re = /([MLHVZmlhvz])\s*([^MLHVZmlhvz]*)/g, m;
        while ((m = re.exec(d))) { var c = m[1], nums = (m[2].match(/-?\d*\.?\d+(?:e-?\d+)?/g) || []).map(Number);
          if (c === "M" || c === "m") { for (var k = 0; k + 1 < nums.length; k += 2) { var pt = (c === "M" || !cur) ? [nums[k] + off.x, nums[k + 1] + off.y] : [cur[0] + nums[k], cur[1] + nums[k + 1]]; if (k === 0) { cur = start = pt; } else { out.push([cur, pt]); cur = pt; } } }
          else if (c === "L" || c === "l") { for (k = 0; k + 1 < nums.length; k += 2) { pt = c === "L" ? [nums[k] + off.x, nums[k + 1] + off.y] : [cur[0] + nums[k], cur[1] + nums[k + 1]]; out.push([cur, pt]); cur = pt; } }
          else if (c === "H" || c === "h") { nums.forEach(function (v) { pt = c === "H" ? [v + off.x, cur[1]] : [cur[0] + v, cur[1]]; out.push([cur, pt]); cur = pt; }); }
          else if (c === "V" || c === "v") { nums.forEach(function (v) { pt = c === "V" ? [cur[0], v + off.y] : [cur[0], cur[1] + v]; out.push([cur, pt]); cur = pt; }); }
          else if ((c === "Z" || c === "z") && cur && start) { out.push([cur, start]); cur = start; } } }
      else if (t === "rect") { var x = n("x") + off.x, y = n("y") + off.y, w = n("width"), h = n("height"); out.push([[x, y], [x + w, y]], [[x + w, y], [x + w, y + h]], [[x + w, y + h], [x, y + h]], [[x, y + h], [x, y]]); }
      return out; }
  function circleOf(el) { var n = function (a) { return parseFloat(el.getAttribute(a)) || 0; }; return { cx: n("cx"), cy: n("cy"), r: n("r") }; }
  function orient(a, b, c) { return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]); }
  function dist(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1]); }
  function segSeg(p1, p2, p3, p4) { if (dist(p1, p3) < TOL || dist(p1, p4) < TOL || dist(p2, p3) < TOL || dist(p2, p4) < TOL) return false;
      var d1 = orient(p3, p4, p1), d2 = orient(p3, p4, p2), d3 = orient(p1, p2, p3), d4 = orient(p1, p2, p4); return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0)) && d1 && d2 && d3 && d4; }
  function distPS(p, a, b) { var dx = b[0] - a[0], dy = b[1] - a[1]; if (!dx && !dy) return dist(p, a); var t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy))); return dist(p, [a[0] + t * dx, a[1] + t * dy]); }
  function segRect(p1, p2, b) { var x0 = b.x + TOL, y0 = b.y + TOL, x1 = b.x + b.w - TOL, y1 = b.y + b.h - TOL; if (x1 <= x0 || y1 <= y0) return false;
      var dx = p2[0] - p1[0], dy = p2[1] - p1[1], t0 = 0, t1 = 1, P = [-dx, dx, -dy, dy], Q = [p1[0] - x0, x1 - p1[0], p1[1] - y0, y1 - p1[1]];
      for (var i = 0; i < 4; i++) { if (P[i] === 0) { if (Q[i] < 0) return false; } else { var t = Q[i] / P[i]; if (P[i] < 0) t0 = Math.max(t0, t); else t1 = Math.min(t1, t); } }
      return t1 - t0 > 1e-6 && Math.hypot(dx, dy) * (t1 - t0) > TOL; }
  function boxOverlap(a, b, pad) { pad = pad || 0; return !(a.x + a.w + pad <= b.x || b.x + b.w + pad <= a.x || a.y + a.h + pad <= b.y || b.y + b.h + pad <= a.y); }
  // --- gather
  var texts = [], leaders = [], dims = [], solids = [];
  Array.prototype.forEach.call(svg.querySelectorAll("text"), function (t) { if (t.closest("#qa")) return; var b = mm(t.getBoundingClientRect()); texts.push({ el: t, box: b, role: roleOf(t), name: t.getAttribute("data-label") || t.textContent.trim() }); });
  Array.prototype.forEach.call(svg.querySelectorAll("line,polyline,polygon,path,rect,circle"), function (el) { if (el.closest("#qa")) return; var role = roleOf(el); if (IGN[role]) return;
      var tag = el.tagName.toLowerCase();
      if (role === "leader") { var nm = el.getAttribute("data-label") || ("leader@" + leaders.length); var g = leaders.filter(function (l) { return l.name === nm; })[0]; if (!g) { g = { name: nm, segs: [], el: el }; leaders.push(g); } g.segs = g.segs.concat(segsOf(el)); }
      else if (role === "dim" || role === "ext") dims.push({ segs: segsOf(el), el: el });
      else if (role === "label" || role === "dimtext") return;
      else if (tag === "circle") solids.push({ kind: "circle", c: circleOf(el), solid: role !== "outline", el: el });
      else if (tag === "rect" && role !== "outline") solids.push({ kind: "rect", box: mm(el.getBoundingClientRect()), solid: true, el: el, segs: segsOf(el) });
      else solids.push({ kind: "segs", segs: segsOf(el), solid: role !== "outline", el: el }); });
  function hitsSolid(o, p1, p2) { if (o.kind === "circle") return distPS([o.c.cx, o.c.cy], p1, p2) < o.c.r - TOL;
      if (o.kind === "rect") return segRect(p1, p2, o.box); return o.segs.some(function (s) { return segSeg(p1, p2, s[0], s[1]); }); }
  function touches(o, p) { if (o.kind === "circle") return Math.abs(dist(p, [o.c.cx, o.c.cy]) - o.c.r) <= 0.6; var ss = o.segs || []; return ss.some(function (s) { return distPS(p, s[0], s[1]) <= 0.6; }); }
  // --- 1, 2, 3, 7 text checks
  texts.forEach(function (t, i) { var b = t.box;
      if (b.x < BORDER || b.y < BORDER || b.x + b.w > W - BORDER || b.y + b.h > H - BORDER) { counts.outside_border++; mark(b, "text outside border: " + t.name); }
      texts.slice(i + 1).forEach(function (u) { if (boxOverlap(b, u.box, -0.3)) { counts.text_overlap++; mark(b, "text overlap: " + t.name + " × " + u.name); } });
      var mid = [[b.x, b.y + b.h / 2], [b.x + b.w, b.y + b.h / 2]];
      var hit = solids.some(function (o) { if (o.kind === "circle") { var nx = Math.min(Math.max(o.c.cx, b.x), b.x + b.w), ny = Math.min(Math.max(o.c.cy, b.y), b.y + b.h); return dist([nx, ny], [o.c.cx, o.c.cy]) < o.c.r; }
          if (o.kind === "rect") return boxOverlap(b, o.box); return o.segs.some(function (s) { return segRect(s[0], s[1], b); }); }) ||
          dims.some(function (d) { return d.segs.some(function (s) { return segRect(s[0], s[1], b); }); }) ||
          leaders.some(function (l) { return l.name !== t.name && l.segs.some(function (s) { return segRect(s[0], s[1], b); }); });
      if (hit) { counts.text_over_lines++; mark(b, "linework through text: " + t.name); } });
  Array.prototype.forEach.call(svg.children, function (el) { if (el.id === "qa" || el.tagName.toLowerCase() === "style" || el.tagName.toLowerCase() === "script") return; try { var b = mm(el.getBoundingClientRect()); if (b.w > 0 && (b.x < -TOL || b.y < -TOL || b.x + b.w > W + TOL || b.y + b.h > H + TOL)) { counts.outside_sheet++; mark({ x: Math.max(b.x, 0), y: Math.max(b.y, 0), w: Math.min(b.w, W), h: Math.min(b.h, H) }, "element outside sheet: " + (el.id || el.tagName)); } } catch (e) {} });
  // --- 4 palette
  function hex(c) { var m = (c || "").match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/); if (!m) return c ? c.toUpperCase() : ""; return "#" + [m[1], m[2], m[3]].map(function (v) { return ("0" + (+v).toString(16)).slice(-2); }).join("").toUpperCase(); }
  Array.prototype.forEach.call(svg.querySelectorAll("*"), function (el) { if (el.closest("#qa") || /^(style|script|defs|title|desc|clipPath)$/i.test(el.tagName)) return; var cs = getComputedStyle(el);
      [cs.stroke, cs.fill].forEach(function (c) { var h = hex(c); if (!h || h === "NONE" || h === "#FFFFFF" || c === "none" || c === "transparent" || c.indexOf("rgba(0, 0, 0, 0)") === 0) return; if (PALETTE.indexOf(h) < 0) { counts.palette++; try { mark(mm(el.getBoundingClientRect()), "colour off palette " + h + " on " + el.tagName); } catch (e) {} } }); });
  // --- 5, 6 leaders
  leaders.forEach(function (l, i) { var ends = []; if (l.segs.length) { var f = l.segs[0], z = l.segs[l.segs.length - 1]; ends = [z[1], f[0]]; }
      var target = null; ends.forEach(function (e) { if (!target) solids.forEach(function (o) { if (!target && touches(o, e)) target = o; }); });
      l.segs.forEach(function (s) {
        leaders.slice(i + 1).forEach(function (m) { m.segs.forEach(function (s2) { if (segSeg(s[0], s[1], s2[0], s2[1])) { counts.leader_crossings++; mark({ x: Math.min(s[0][0], s[1][0]), y: Math.min(s[0][1], s[1][1]), w: Math.abs(s[1][0] - s[0][0]), h: Math.abs(s[1][1] - s[0][1]) }, "leaders cross: " + l.name + " × " + m.name); } }); });
        dims.forEach(function (d) { d.segs.forEach(function (s2) { if (segSeg(s[0], s[1], s2[0], s2[1])) { counts.leader_crossings++; mark({ x: Math.min(s[0][0], s[1][0]), y: Math.min(s[0][1], s[1][1]), w: Math.abs(s[1][0] - s[0][0]), h: Math.abs(s[1][1] - s[0][1]) }, "leader crosses dimension: " + l.name); } }); });
        solids.forEach(function (o) { if (o === target || !o.solid) return; if (hitsSolid(o, s[0], s[1])) { counts.leader_through_geometry++; mark({ x: Math.min(s[0][0], s[1][0]), y: Math.min(s[0][1], s[1][1]), w: Math.abs(s[1][0] - s[0][0]), h: Math.abs(s[1][1] - s[0][1]) }, "leader through object: " + l.name); } }); }); });
  // --- 8 density, 9 columns
  var items = texts.length + leaders.length + dims.filter(function (d) { return roleOf(d.el) === "dim"; }).length;
  if (items > DENSITY[size]) { counts.density = 1; fails.push("density " + items + " > " + DENSITY[size] + " — split the view"); }
  var labels = texts.filter(function (t) { return t.role === "label" && !t.el.closest(".bubble") && (t.el.getAttribute("text-anchor") || "start") !== "middle"; });
  var xs = labels.map(function (t) { return Math.round(t.box.x * 2) / 2; }).sort(function (a, b) { return a - b; }), cols = xs.length ? 1 : 0;
  for (var j = 1; j < xs.length; j++) if (xs[j] - xs[j - 1] > 0.5) cols++;
  if (cols > 2) { counts.unaligned_labels = cols - 2; fails.push("labels in " + cols + " columns — align to one column per side"); }
  // --- badge
  var total = 0; for (var k in counts) total += counts[k];
  var badge = document.createElementNS(svg.namespaceURI, "text"); badge.setAttribute("x", 12); badge.setAttribute("y", H - 5); badge.setAttribute("font-size", "2.5"); badge.setAttribute("font-family", "Arial, Helvetica, sans-serif");
  badge.setAttribute("fill", total ? "#FF0000" : "#007700"); badge.textContent = total ? ("QA: " + total + " ISSUES — " + Object.keys(counts).filter(function (k) { return counts[k]; }).map(function (k) { return k + " " + counts[k]; }).join(", ")) : "QA: PASS";
  qa.appendChild(badge);
  window.WS_QA = { counts: counts, fails: fails, items: items, size: size };
  var man = document.getElementById("manifest"); if (man) { try { var m = JSON.parse(man.textContent); m.qa = counts; m.item_count = items; man.textContent = JSON.stringify(m); } catch (e) {} }
})();
