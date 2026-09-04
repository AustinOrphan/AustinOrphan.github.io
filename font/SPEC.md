# Orphan Display: specification

A typeface grown from the two letters in the AO mark. This document records
what the mark is, measured from its Illustrator source, and every decision
taken in turning those two letters into a font. Numbers in **points** are the
source's own units (a 100 pt artboard). Numbers in **units** are font units
(1000 per em, cap height 700).

Nothing in the A or O is drawn by eye. `glyphs/core.py` reads the source
geometry and applies only the transforms listed in §3.

## 1. Source

`source/AO.ai` (Illustrator 30.2), page 1, holds the mark as four separate
filled objects, in stacking order:

| object | segments | what it is |
|---|---|---|
| white | 15 cubics | a swash lying under the black objects, invisible on the white artboard; it matches the sweep the bar makes in the animation video and is treated as an animation asset, not part of the static mark |
| ring | 24 cubics, two subpaths | the O |
| bar | 18 cubics, one closed outline | the crossbar with both hooks |
| A | 6 straight segments | the A's legs, a single polygon |

Page 2 is the united export the site's `Logo.astro` path came from (it is a
uniform scaling of page 1; the apex tips coincide to one part in ten
thousand). `source/favicon.ai` has the same three black objects in the
favicon colour. `measure/extract_ai.py` reads all of this into
`source/ai_objects.json`.

Before the `.ai` files were available the same geometry was recovered from the
site's SVG path by fitting (`measure/extract.py` and friends, evidence in
`measure/evidence/`). Those fits agree with the source to within tracing
tolerance: ring radii within 0.1%, counter offset 5.50% vs 5.51%, cut angles
within 0.2°. They are kept as an independent check.

## 2. What the mark is

### 2.1 The O (ring object)

Two true circles. Fitted to the source path with residuals of 0.006 pt and
0.004 pt over roughly a thousand samples each:

| | centre (pt) | radius (pt) |
|---|---|---|
| outer | (50.963, 54.023) | 39.852 |
| inner | (52.513, 55.577) | 36.178 |

The inner circle is displaced **2.195 pt toward 45.07°**, which is 5.51% of
the outer radius. The ring is therefore not monoline: 5.87 pt at the lower
left (225°), 1.48 pt at the upper right (45°), 3.67 pt on average, which is
4.6% of the diameter. The source path carries extra nodes where the A and bar
cross the ring (boolean scars); the circles themselves are exact.

### 2.2 The A (A polygon + bar object)

The polygon's vertices, in order, in points:

| vertex | position |
|---|---|
| left foot tip | (10.958, 13.321) |
| left foot cut | (17.523, 15.224) |
| counter apex | (53.876, 90.260) |
| right foot cut | (75.548, 7.417) |
| right foot tip | (81.207, 4.778) |
| apex | (54.669, 99.415) |

From these:

- **Outer legs** at 63.10° and 105.68° from the horizontal. Their bisector is
  at 84.37°, so the A **leans 5.63°** with the apex to the right. **Apex
  angle 42.58°.**
- **Legs taper.** Perpendicular width of the left leg 5.01 pt at the foot,
  3.44 pt at the counter apex; right leg 4.72 pt and 3.24 pt. Both lose about
  1.6% of their length in width from bottom to top, and the left leg is 6%
  heavier than the right.
- **Feet are cut obliquely**, tip at the outer corner: the left cut runs at
  +16.2° absolute, the right at −25.0°. In the A's own frame that is +21.8°
  and −19.4°, i.e. each foot is cut at roughly half the apex angle from the
  horizontal, which is the same as saying each cut is perpendicular to the
  *opposite* leg (within 1°).
- **The apex is a clean point:** the outer edges meet at the tip.

The bar object is one closed outline of 18 cubics, so its hooks are open
curls, not loops. Read off its Béziers (and the fits in
`measure/measurements.json`):

- It is a **shallow arch**, not a straight bar: the bottom edge is a circular
  arc of radius ≈ 308 pt with a sagitta of ≈ 1.9 pt over the visible chord.
- It **rises 11.5°** absolute, **17.2° in the A's frame**.
- It is the **heaviest stroke**: ≈ 6.0 pt at mid-length, tapering from ≈ 6.2 pt
  at the left to ≈ 5.0 pt at the right.
- Both ends **hook downward**. In the united mark the hooks touch the ring and
  enclose two small eyes; the eyes exist only because of the ring.

### 2.3 Composition, not letterform

These belong to how the two letters are arranged in the mark, not to either
letter, and are not carried into the font:

- the A's 5.63° lean inside the ring;
- the A being 19% taller than the ring (apex 5.9 pt above it, feet up to 9.5 pt
  below);
- the bar spanning the ring's full diameter;
- the two eyes between hooks and ring;
- the white swash.

## 3. From isolated letters to glyphs: decisions

Each of these is a change a typeface forces. Anything not listed here is the
source, verbatim.

**D1. The A stands upright.** Rotated by +5.63° about its apex, so the
bisector of its outer legs is vertical. Evidence that the lean is placement
rather than letterform: once upright, the two feet land within 1.6 pt of level
(1.8% of a leg length) and the legs are equal in length within 2%. Keeping the
lean would instead have required an 8% asymmetry in leg length to reach a
baseline, a larger distortion of the letter than the rotation.
*Alternative kept open:* an oblique face at 5.63°, which is one parameter in
`build_A`.

**D2. Feet levelled.** Upright, the feet differ by 12.7 units. Each foot's cut
is slid along its own leg by half of that (6.4 units), keeping the cut angle,
so both tips sit on the baseline. This is the only geometric edit to the A.

**D3. Separate scales for A and O.** The O is scaled so its outer circle
spans the cap height plus round overshoot (9.034 units/pt). The A is scaled so
its feet sit on the baseline and its apex tip on cap + point overshoot (7.888
units/pt). The mark's A-to-O size ratio is composition (§2.3); a typeface's
capitals share a cap height. Consequence: relative to the O, the A's strokes
come out 13% lighter than in the mark, landing the diagonals at 92–96% of the
round weight, which is the conventional optical relationship.

**D4. The O is built from its fitted circles**, not from the node-split source
path. Identical within 0.01 pt, without the boolean scars.

**D5. The bar is carried verbatim**, all 18 cubics, hooks included, through
the same rotation and scale as the polygon. The isolated A is exactly
polygon ∪ bar. Consequence: the hooks overhang the feet by 104 units on the
left and 105 on the right, giving the A an advance of 847 units, wide for a
capital. That width *is* the letter as drawn; a compact alternate is possible
later but is not this A.

**D6. Typographic constants** (`lib/metrics.py`), which the mark cannot
supply: em 1000; cap 700; round overshoot 10; point overshoot 16; side bearing
60 beside a straight stem, 40 beside a round or a pointed extreme; word space
260; ascent 800 / descent 200.

**D7. Unicase.** The source has no lowercase, so there is no lowercase DNA to
extrapolate from; inventing 26 forms would be exactly the guesswork this
project refuses. Lowercase code points map to the capitals. This is the
largest scope decision in the face and the easiest to revisit.

## 4. The A and O in font units

| | value |
|---|---|
| O outer radius | 360 (spans −10 … 710) |
| O inner radius | 326.81 |
| O counter offset | 19.83 units toward 45.07° |
| O stroke, thick / mean / thin | 53.0 / 33.2 / 13.4 |
| A apex | (423.4, 716) |
| A feet tips | (143.8, 0) and (701.9, 0) |
| A leg angles | 68.71° and 111.29° |
| A left leg width, foot → apex | 39.5 → 27.1 |
| A right leg width, foot → apex | 37.2 → 25.5 |
| A foot cuts | +21.8° and −19.4° from horizontal |
| A bar | verbatim; box 40 … 807 × 179 … 499 |
| A advance | 847 |
| O advance | 800 |

## 5. Rules for every other glyph

The rest of the face is extrapolated, and the value of the extrapolation rests
on every rule tracing back to §2. These are the rules. They are what the glyph
workflow builds to and what its verifiers check.

**R1. Rounds.** A round form is an outer contour and a counter that is the
outer contour brought in by **33.2 units** (the O's mean stroke) and then
displaced **19.8 units toward 45.07° on the page**. For the O itself this
reproduces the source exactly (inner radius 326.8). Stroke and displacement
are absolute, not proportional to the round's size, so a bowl half the O's
size carries the O's weight rather than half of it. The displacement direction
is fixed to the page, not to the glyph, so every round in the face is heavy
(53.0) at the lower left and light (13.4) at the upper right, like the O.
Partial rounds (C, G, S, U, the bowls of B, D, P, R, the digits) are arcs of
that construction with radial cuts.

**R2. Diagonals.** The A's legs, as a weight field over height: a stroke
leaning like "/" is 39.5 units wide at the baseline and 27.1 at the cap line,
one leaning like "\\" is 37.2 and 25.5, linear in between. Shorter diagonals
take the widths at whatever heights they span. Applies to V, W, M, N, K, X, Y,
Z, 4, 7.

**R3. Verticals.** No exemplar exists, so a stem takes the left leg's profile:
**39.5 at the baseline tapering to 27.1 at the cap line.** The check on that
choice is the O: the O's mean stroke width (33.2) equals this profile's width
at mid-height (33.3), so a stem beside an O carries the O's average weight.

**R4. Horizontals.** From the bar: **47.5 units at mid-length, thinning 1.8%
of its length from left to right**, and level. The bar's tilt, arch and hooks
are one gesture, the A's flourish; the hooks cannot recur on an E without
colliding with the arm below, and the tilt and arch belong to the same
stroke, so none of the three transfers. Horizontals end in R5 cuts.

**R5. Terminals.** Every free end of a stem or diagonal is cut like the A's
feet: **20.6° off the horizontal** (half the apex angle; measured 21.8° and
19.4°), tip at the corner farther from the letter's centre, so the cut rises
toward the interior at the bottom of a stem and falls toward it at the top.
Arms take the same cut turned 90°: 20.6° off the vertical, tip at the outer
corner. The mark's other terminal, the hook, stays with the A (R4).

**R6. Junctions and points.** Strokes simply overlap and are unioned; the A
polygon and the bar are joined the same way. Where two strokes meet in a
point (A, V, W, M, N), the outer edges meet at the tip and the tip overshoots
the cap line or baseline by 16 units.

**R7. Weight direction.** Every rule above puts weight at the lower left and
lightness at the upper right: rounds by displacement, straights by taper,
horizontals by tapering rightward. A glyph that breaks this direction is
wrong.

**R8. Proportions.** Body widths (outer extreme to outer extreme) come
from the two exemplars. The O's diameter, **720**, is the wide width: C, G, Q.
The A's foot spread, **558**, is the medium width: H, N, U, V, X, Y, K, T, Z,
D, B, P, R and the digits' bodies. Narrow letters take three quarters of
medium, **420**: E, F, L, S, J. Every pointed construction (V, W, M, N, K, X,
Y) uses the A's apex angle, 42.6°, with R2 widths; where that alone would push
a letter's advance past 0.95 em (W), the vees are steepened only as far as
needed and the deviation recorded in the glyph's notes. No advance exceeds the
em. A glyph may depart from these widths only for a reason written in its
notes.

**R9. Spacing.** D6's side bearings by the shape of the extreme (stem: 60,
round or point: 40). Kerning is out of scope until the set is complete.

## 6. What is deliberately not in the face

- the white swash and the two eyes (need the ring or the animation);
- the A's lean and the A/O size ratio (composition);
- hooked, tilted or arched horizontals anywhere but the A (R4);
- a lowercase (D7);
- a second weight, though every stroke is parametric and the pen would take
  one.
