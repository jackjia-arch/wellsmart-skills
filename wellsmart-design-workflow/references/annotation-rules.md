# Annotation rules — how leaders, labels and dimensions are placed, and how the AI is made to comply

Annotation is where AI drawings fail most: leaders that cross each other, leaders that run through other objects, labels at random heights, labels touching lines, dimension lines cut by leaders, the wrong label on the wrong object. The cause is structural — a model writing SVG coordinates by hand cannot see the picture it is producing — so the fix is structural too: **the model declares annotations; a script places them; a checker proves them.** Rules first, then the mechanism.

## The defect catalogue (from real sheets, 2026-09-14)

| # | Defect seen | Why it happens | Rule that removes it |
|---|---|---|---|
| D1 | Two leaders cross in an X: the upper label points at the lower object and vice versa | Labels placed in a different vertical order from their targets | R3 (label order = target order) |
| D2 | A leader runs through other cables / objects on its way to its target | Straight line from wherever the label landed, no obstacle test | R5 (through nothing but its target), R8 (keyed notes) |
| D3 | A leader crosses a dimension line or an extension line | Dimensions and labels put on the same side of the view | R6 (labels and dimensions never share a side) |
| D4 | A label sits on a dashed line or on linework; "PE" text touching the bus line | No clearance test; label anchored at the object instead of in a column | R2 (column), R7 (1 mm clearance) |
| D5 | Labels scattered at unrelated x positions and heights | Each label placed "near its object" | R2 (one aligned column per side) |
| D6 | Wrong label on the wrong object (240 mm² text on the 25 mm² cable) | Label text and target chosen separately | R1 (declare text + target together, tag-checked) |
| D7 | Four leaders to four identical items, or one leader lost among them | No grouping | R4 (one label, ×N, leader to the reachable member) |
| D8 | Leader starts on the wrong side of a symbol or inside it | Endpoint typed by hand | R5 (anchor computed on the outline) |
| D9 | Very long leaders across the whole view | Label column far away or on the wrong side | R9 (≤ 45 mm A3 / 60 mm A1), side = auto |
| D10 | Dimension text on the line, extension lines starting on the object | No band geometry | R10 (bands: 8 mm, +7 mm; 1.5 mm gap, 2 mm overshoot) |
| D11 | Chinese label text and English text mixed on one line, leaders from the middle of a word | Free-form text | R11 (English uppercase; one label = one text block; leader starts at the shoulder) |
| D12 | Everything crammed, then labels shrunk to fit | No density rule | R12 (split, never shrink) |

## The twelve rules

R1 **Declare, don't draw.** An annotation is `label(text, target, side)`: the text, the element it points at (by tag from the DB) and a side preference. The model never types leader or label coordinates on a generated sheet.

R2 **One aligned column per side.** Labels on the right of a view share one x (text left-aligned, leader shoulder at the column); labels on the left share one x (text right-aligned). Two columns per view at most. Labels are never scattered around the geometry.

R3 **Label order = target order.** Within a column, labels are stacked in the same vertical order as their targets (same row: the target nearest the column takes the slot nearest the row). With this, leaders from one column cannot cross each other. Slots are pulled towards their target's height and pushed apart by the pitch (1.5 × text height per line + 1.5 mm).

R4 **Identical items get one label.** `members=[…]`: one label with "×N", one leader to the member that can be reached without crossing anything. Never N leaders.

R5 **A leader passes through nothing but its target.** It may cross a container outline (a wall, a pit, an enclosure — class `outline`) but never another object, another leader, a dimension, a text box or a grid bubble. It ends on the target's outline (computed anchor), with a filled arrowhead on a line or edge and a dot on a surface. Straight, or straight with a horizontal shoulder at the column; never curved, never more than one bend.

R6 **Labels and dimensions never share a side.** Dimensions go in bands on the sides that carry no labels (default: dimensions bottom and left, labels right; or dimensions bottom, labels right and left). A leader therefore never has to cross a dimension line.

R7 **Clearance.** Text keeps ≥ 1 mm from every line and ≥ 1 mm from other text; the halo is a rendering aid, not a permission to overlap.

R8 **When a target is unreachable, use a keyed note.** A 4 mm numbered bubble beside the target with a ≤ 5 mm leader, and the text in the notes list ("1 — INCOMING 5C 240 AL SWA"). This is what a row of cables inside an enclosure, or items deep inside a plant room, always get. Over 8 leader labels in one view → keyed notes for the whole view.

R9 **Leader length ≤ 45 mm on A3, ≤ 60 mm on A1.** Longer means the column is on the wrong side or the view needs splitting or keyed notes.

R10 **Dimension geometry is fixed.** First band 8 mm outside the geometry envelope, subsequent bands +7 mm; extension lines start 1.5 mm off the object and overshoot the dimension line by 2 mm; text 1 mm above the line, centred, real size (paper × scale), no unit; closed filled arrowheads ≈ 2.5 mm; chained dimensions must sum to the overall.

R11 **Text discipline.** English uppercase; one label = one text block (tspans for multiple lines, first line the name, second the spec); Chinese only as the second line of a sheet or view title; no rotated labels (rotated text only on vertical dimension values); tags and run labels may take their service colour, everything else black.

R12 **Density before drawing.** Estimated annotated items (labels + leaders + dimensions + tags) above ≈ 60 on an A3 view or ≈ 150 on an A1 view → split the view first (by system, then by grid zone, then by scale). Never shrink text, never stack labels, never drop items.

## The mechanism — how the AI is forced to comply

1. **Generated sheets (gen.py path).** The generator collects the geometry it drew as obstacles (`solid=True` for objects, `solid=False` for container outlines), declares labels and dimensions, and calls `Layout.render()` from `scripts/annotate.py`. The engine sorts, stacks, anchors, routes, falls back to keyed notes, and returns the SVG group plus a report. A report with any non-zero count stops the generator (the sheet is not written) with the offending labels named.

2. **Chat-drawn sheets (the model writes the SVG itself, as in the project drafting spec).** The model must still not place annotations by feel. Procedure, written into the sheet's LAYOUT PLAN comment before the SVG:
   - list every target with its outline geometry (tag, kind, coordinates);
   - list every label as text → target → side;
   - compute the column x per side (envelope + 10 mm beyond any dimension band on that side);
   - sort labels by target y, assign slot y values with the pitch rule, write the shoulder and anchor points;
   - for every leader write the segment-intersection check against every other leader, every dimension line and every solid object (a one-line "OK" per pair is enough, but it must be written);
   - only then write the SVG, using the classes `leader / label / dim / ext / outline` so the overlay and the checker can see the roles.
   Any label whose check fails becomes a keyed note in the same step.

3. **The checker after every sheet.** `python3 scripts/annotate.py check <sheet.html>` parses the SVG and reports leader crossings, leaders through objects, leaders over dimensions, text over lines, text over text, leaders too long, text outside the border, label columns, and the annotated-item count. In Claude Code the loop is: draw → check → fix every listed item → check again → only a clean report is issued. The in-browser overlay (`templates/qa-overlay.js`, embedded in every sheet) runs the same checks on open, draws red boxes and prints the badge, so a person sees the state without running anything.

4. **The reviewer counts for itself.** In the review round the second model is told to count crossings from the SVG, not to trust the badge (review-hub rules). A sheet with a non-zero count is a `major` finding.

## Worked example

The cable pit that came back with an X: three 240 mm² feeders, four 25 mm² consumer cables, pit 400 wide. Declared as two labels (`MAINS IN / TIE / OUT 5C 240 AL SWA` with the three big cables as members; `CONSUMER 5C 25 CU SWA` with the four small ones) and one dimension (400, bottom). The engine puts both labels in a right column, consumer above mains (target order), leaders straight to the nearest member of each group, dimension in the bottom band; report: crossings 0, through objects 0, over dimensions 0. `python3 scripts/annotate.py demo out.html` draws the before / after pair with both checks.

A pillar with six cables in a row: labels on the left are moved to the right because the left carries a dimension band; the outer cables are labelled with straight leaders; the inner cables cannot be reached without crossing their neighbours, so they become keyed notes 1–3 with 4 mm bubbles and short leaders. That is the correct professional result, produced without a person deciding it.

## Sheet classes (so scripts can see roles)

`leader` (path/line/polyline, `data-label` = the label text or keyed number), `label` (text), `dim` (dimension line), `ext` (extension line), `dimtext`, `outline` (container linework a leader may cross), `bubble`, `arrow`; ignored as obstacles: `grid`, `halftone`, `qa`, `bg`, `border`, `furniture`. Everything without a class is solid geometry.
