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
  enclose two small eyes.

Taken together these are the signature of a **planetary ring**: an elliptical
annulus seen in perspective, whose front half is the bar. Fitting that model
(major axis from hook tip to hook tip, height from the bar's edges) gives an
outer ellipse of 51.5 × 11.3 pt tilted 14.1°, an inner ellipse of 45.4 × 5.0 pt
sharing its centre and axis, centred at (50.0, 51.5), which is 2.6 pt from the
O's centre. The bar's top and bottom edges lie on the two ellipses to 0.10 and
0.13 pt mean residual, the hooks' outer curls to 0.23 pt, and the band between
the ellipses is 6.0 pt at the ends and 6.4 pt in the middle, the bar's own
width. So the hooks are the ring's ends, the eyes are the gap between the
ring's two edges where they turn, and each return stroke is the start of the
ring's **back half**, which in the mark disappears behind the O; the returns
thin to about half the bar's width before they vanish. The fit lives in
`source/ai_objects.json` under the bar object's `ring`.

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

**D5. The ring's back half continues to the legs.** In the mark the bar is
the front half of a ring (§2.2) and the returns are the start of its back half,
hidden behind the O. Carried verbatim without the O, the returns end in space.
The user's direction was that the hooks should follow their trajectory back
to the legs and that the bar is a ring like a planet's. So each return is
continued from its end face along the ring's centre ellipse (the mean of the
fitted outer and inner ellipses) toward the ring's middle until it passes
behind the nearer leg, thinning from the face width to the face's thinnest
stroke, the O's thin side (13.4 units), where it meets the leg's outer edge,
the way the mark's own returns thin toward the planet; the last stretch to the
leg's centre-line is buried so the union is seamless. The face midpoints sit
0.26 and 0.41 pt off the centre ellipse and are blended onto it over the first
8 pt. The back arcs reach the legs after 9.0 pt (71 units) on the left and
23.4 pt (185 units) on the right. The bar and hooks themselves are verbatim
and the A's advance stays 847.

Built and set aside on the way (`measure/evidence/hook-options*.png`): a
straight continuation of each return (a 201-unit hairline on the right, no
curvature), a circular bend of 20° (an arbitrary amount), and sliding the
hooks inward until the returns land on the legs (moves the hooks and narrows
the bar). The bar without tails is kept as the unencoded alternate `A.open`.

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
| A bar | source Béziers, verbatim; box 40 … 807 × 179 … 499 |
| A tails | ring back arcs, 71 and 185 units to the legs, 26.4 / 18.9 → 13.4 wide |
| A advance | 847 (A.open, no tails: 847) |
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
of its length from left to right**, and level. A horizontal whose outer edge
lies on the cap line or the baseline (the arms of E, F, L, T, Z, the tops and
bottoms of digits) keeps that edge exactly on the metric line and takes the
whole taper on its inner edge, so flat tops and bottoms sit where the H's and
I's do; a horizontal away from the metric lines (H's bar, E's middle arm, A's
would-be bar) tapers symmetrically about a level centre-line. `rules.arm()`
and `rules.horizontal()` build the two cases. The bar's tilt, arch and hooks
are one gesture, the A's flourish; the hooks cannot recur on an E without
colliding with the arm below, and the tilt and arch belong to the same
stroke, so none of the three transfers. Horizontals end in R5 cuts.

**R4b. The ring the rest of the face borrows.** R4 leaves horizontals level.
That holds on the metric lines and nowhere else. The A's crossbar **is** the
mark's ring (§2.2), so the ring's gesture can be read straight off it: the two
cut faces `clip_legs` leaves are its ends, and the line between their midpoints
is the chord the ring draws through that letter. Under R4b every **interior**
horizontal — one lying on no metric line — is a chord of that same ring.

What the chords share is the **rise**, not the angle:

> `tilt(L) = min(RING_TILT, atan(RISE / L))`, with **RISE 90.77** and
> **RING_TILT 19.87°** measured off the A's bar.

One angle is not one gesture. An H bar spans 1.6× an E arm, and the same tilt
would lift them by different amounts, reading as two ring fragments rather than
one ring. One rise is. A chord shorter than the A's own span takes the ring's
angle verbatim; a longer one relaxes until its rise matches. The crossover
between the two halves is **251.11**, the A's own span — true *by
construction*, since it is `RISE/tan(RING_TILT)` and both are measured off the
same bar. It looks like a discovered fact and is not one.

The chord is **arched** on the A's bar's own radius, **ARC_R 2429.5** (308 pt,
§2.2), and pivots about its own centre-line, so a glyph's colour and its
counters stay where the level rule put them and only the gesture is new. It
carries R4's widths and R4's taper, measured on the chord's own normal rather
than on the vertical.

A horizontal **on** the cap line or the baseline stays exactly level. The ring
passes *behind* the letter, so it is not the ring's business to break the
letter's silhouette against the line of type; only the interior strokes are its
to move.

Taken by E, F, H, P, R, B, G and the 4. The G takes the ring **reflected** in
its bar's height, because `G_BAR_Y` is the mid line reflected in the half-cap;
taking it upright there would tilt the bar *into* the aperture and close the
letter, which is the one thing the G's bar exists to keep open. The 4's crossbar
is the H's bar doing the H's job, and nothing about a figure exempts it: its R5
tips are cut on the chord's normal and the diagonal's foot follows the bar,
rather than the bar being held level to keep that foot where it was.

Two exceptions beyond the metric lines, both because the stroke's *meaning*
depends on being level rather than its silhouette:

- **The mathematical marks.** `+` and `=` are level by definition — an equals
  sign is two level bars, and a tilted one is not an equals sign. `_` must tile
  with the next underscore into one unbroken line, which a tilt would break.
  These keep R4's level horizontal.
- **The 5** — *not yet decided, and currently level.* Its bar is not merely
  near its bowl, it is tangent to it **along** its length: the whole figure is
  solved so the bar's top edge passes through the bowl's top point. Tilting the
  bar moves that tangency 84 units left (to where the ellipse's own slope
  matches the chord's) and drops the stem's foot 84 units with it, and
  `_bury_end`, which reshapes the bar's buried end on the assumption of a level
  bar meeting the bowl at its top, produces a spur instead of a join. The solve
  converges; the figure it converges to is a different 5. That is a redesign to
  be judged on its own, not a wiring job, so the 5 is left level and listed here
  rather than quietly skipped.

The A itself does not move. Dropping its bar onto the mid line was considered —
it would put the mark on the line E, F, H, K, X and Y are built on — but the A
is the mark, and the rest of the face borrows from it rather than the other way
round. `ORPHAN_RING_DROP=1` builds that reading (RISE 100.09, tilt 19.93°).

**The band stays constant, deliberately.** The mark's bar is not an offset
band: its two edges are separately struck, the upper on a radius of **2118.2**
units and the lower on **2742.8** (whole-edge circle fits to the drawn outline,
max residual 0.074 and 0.100). So the mark's own bar swells toward midspan.
It swells by **0.85 units** — over the 251-unit span the A gives it. Carrying
the two radii onto a longer chord instead of the swell would put **4.13 units**
into the middle of an H's 551-unit bar, +12% on a 33-unit stroke: an artefact of
length, not something the mark does. That is the same trap the tilt rule was
written to avoid, one step further on, so it takes the same answer — transplant
the amount, not the geometry. And the amount is 0.85 units, which at any size
this face is set at is below the resolution of the thing it would correct. So
the band is built constant, from one radius, and the 0.85 is left on the table
knowingly rather than by omission.

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
