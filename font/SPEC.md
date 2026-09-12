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

**What is derived rather than transcribed.** Three parts of the mark were
carried into the font as literal outlines and so ignored the WEIGHT and PUSH
knobs entirely: the O's counter, the A's crossbar, and the A's counter. All
three are solved now.

- **The O's counter** — `r_in = r_out - RING_W`, displaced by `RING_OFF`, which
  reproduces the traced ring to the last bit at the mark's own numbers.
- **The A's crossbar** — the ring is an annulus between two concentric coaxial
  ellipses, so the outer stays traced (it is the silhouette) and the inner is
  inset from it by R4's join weight, `RING_W + RING_OFF[1]`. That is the law
  every chord in the face already scales by, so the A's bar and the letters
  that borrow its ring now move together: 42.7 / 47.8 / 63.1 across the weight
  axis against `HORIZ_JOIN`'s 42.3 / 47.2 / 62.2. It follows PUSH too, because
  the band depends on the displacement. Where the ellipse fit and the drawn
  outline disagree the drawing wins, so the inset carries one calibration
  solved on the mean band over the visible span; the derived bar is then never
  more than 0.84 units from the drawn one, inside the fit residual above.
- **The A's counter** — the two outer edges inset by R2's widths. Both inner
  edges come out straight, since R2's width is linear in y and the offset
  direction is fixed along a straight leg, so the counter apex is simply where
  they meet and each cut point is where an inner edge meets that foot's own
  cut. Lands within **0.54 units** of the traced points.

Only `A.open`, the unencoded alternate, keeps the traced bar with its hooks: it
is a transcription of the mark rather than a stroke of a letter, so it is not
the knobs' to move.

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
leaning like "/" is **65.00** units wide at the baseline and **20.89** at the
cap line, one leaning like "\\" is **62.64** and **19.36**, linear in between.
Shorter diagonals take the widths at whatever heights they span. Applies to V,
W, M, N, K, X, Y, Z, 4, 7.

Neither end of that field is the mark's. The mark's own legs are **39.90** and
**37.54** at the baseline and **25.99** and **24.46** at the cap. R2b adds 20
units at the base and R2c tilts a further 5.10 out of the cap and into it —
three rules that are one decision, and `ORPHAN_FOOT=0` turns off all of them.

Those four numbers were **39.5 / 27.1** and **37.2 / 25.5** until the A's
counter was derived and the discrepancy surfaced. §2.2 measured the legs at the
**foot cut** and the **counter apex** — y 20.1 and y 643.5 — and the rule stored
them as if they were the baseline and the cap line. The values above are the
same two measurements extrapolated from where they were actually taken. The
correction is systematic: about 1% light at the foot, 4% heavy at the cap, and a
taper flatter than the A's own. It also corrects §2.2's "the legs lose about
1.6% of their length in width" — the 12.39-unit drop was divided by the whole
768.4-unit leg but measured over only 669.1 of it. **The rate is 1.85%.**

**R1b. The rounds follow R2b.** R2b widens the straights at the baseline, and
a round has no foot to widen: its weight is the band and the counter's
displacement, both fixed to the page rather than to height. Left alone the
face's straights averaged **42.9** units against its rounds' **33.2**, a 29%
split the mark does not have, and an O beside an H looked starved.

So the round takes that gain, as a ratio: the band **and** the displacement are
both multiplied by `1 + FOLLOW × (FOOT_WIDEN/2) / RING_W`, where the fraction
before FOLLOW is how much R2b lifts the straights' mean. The round's contrast
is untouched whatever FOLLOW is — thick over thin stays the mark's **3.97** —
so PUSH means what it meant, and at `ORPHAN_FOOT=0` it reduces to the mark
exactly.

`FOLLOW` is **0.75**, not 1. At 1 the straights and the rounds are exactly
level and R3's check holds at its own original 0.75%; the round is deliberately
let fall a quarter of the way behind instead, because that is half of what pays
for R2c. RING_W goes 33.19 → **40.69** and the displacement 19.83 → **24.31**,
which leaves the straights **5.5%** over the rounds. See R2c for the trade, and
for why 5.5% is the affordable end of it.

This looked unaffordable when it was first measured. The WEIGHT ceiling at
PUSH 1.00 appeared to fall from 2.302 to 1.638 with the band alone and to
1.110 with the displacement as well, against an axis that needs 2.00. All
three numbers were an artefact of one line of code: the B's upper bowl meets
its waist at a **tangency** — its counter tangent to the waist's top edge puts
the bowl's lowest point at `MID_LINE + HORIZ_MID - RING_OFF[1] - RING_W`,
which is `MID_LINE` exactly, and the waist's underside is on `MID_LINE` — and
`set_bowl._bowl` was asking that tangency for two roots. It got them by
rounding at the mark's numbers and stopped getting them under a heavier band.
Read as the tangency it is, the ceilings are **3.014, 2.370 and 2.311**. The
axis had more room than anyone thought at the mark's numbers too.

**R2b. The widened base.** One number in this face is a design decision rather
than a reading: the base of R2's field is **20 units wider than the mark's**,
and the cap is the mark's exactly. On its own it puts a stroke at 59.90 at the
baseline and still 25.99 at the cap line, so the taper is steeper and the whole
lower half of the face is planted rather than merely tipped. It scales with
WEIGHT like the rest of R2. (R2c then tilts a further 5.10 out of the cap and
into the base; the field's published numbers under R2 are both rules together.)

Three alternatives were measured and drawn before this one was taken — the
mark's own taper, a wider foot with a **curved** taper, and a **true flare**
confined to the bottom 200 units. `measure/evidence/foot-matrix.png` and
`foot-full-letter.png` are the comparison, at three strengths each. The flare
is the only one that leaves the letter's colour above the foot untouched
(32.9 at mid-cap at every strength); this one does not, and that is the point.
It is also the only one the existing machinery draws exactly, because the
field stays **linear** and `stroke()` interpolates between two endpoint
widths; a flare or a curve would need `stroke()`, `diagonal()` and
`_derive_counter` taught to follow a field along the stroke.

What it costs is R3's corroboration, below, and a colour difference between
the face's straights and its rounds that the mark does not have. The rounds
have no foot to widen: a round's weight is modulated by stress, not by height.

**R2c. The foot meets the round.** R2b widened the base and R1b brought the
rounds up with it, which left the foot at **59.90** against a round that
reaches **69.0** where it is thickest — 87% of the heaviest stroke in the face.
`measure/evidence/stem-vs-round-profile.png` is where that was read off: a
stem's width plotted against height, beside the band of the round standing next
to it. R2c closes the last 13% and states the result as the rule:

> **A stroke at the baseline is as wide as a round at its thickest.**

It is paid for from two places at once, because neither alone is affordable.
**TAPER** moves the base up and the cap *down* by the same amount, so the
field's mean does not move and nothing keyed to the mean moves either; alone it
needs 9.1 units and takes the cap to 16.90, under ROUND_THIN, and to 12 units
at the Thin master, which drops out below about 16px. **FOLLOW** (R1b) lets the
round fall behind instead; alone it needs the round held to 0.43 of R2b's gain
and runs the straights 14.6% over them, which is where an O starts to look
starved — the very thing R1b was written to fix.

Solving `base = ROUND_THICK` leaves a one-parameter family and FOLLOW picks the
point on it. Every row reads foot/thickest = 100.0% in a real build, and every
row builds all 18 masters:

| FOLLOW | TAPER | foot | cap | colour | taper ratio |
|---|---|---|---|---|---|
| 1.00 | +9.09 | 68.99 | 16.90 | −0.6% | 4.08:1 |
| **0.75** | **+5.10** | **65.00** | **20.89** | **+5.5%** | **3.11:1** |
| 0.50 | +1.11 | 61.01 | 24.88 | +12.5% | 2.45:1 |
| 0.43 | 0.00 | 59.90 | 25.99 | +14.6% | 2.30:1 |

**0.75** is where both costs are small: 5.1 units of cap, which leaves it at
20.89 and still above the round's thinnest stroke, and 5.5% of colour, a fifth
of the split R1b was written to close. `measure/evidence/foot-blend.png` is the
family as letters.

TAPER is **derived**, not set, so the rule goes on holding if FOOT_WIDEN or
FOLLOW is moved. Two things about where it holds, both consequences of the axes
rather than slips. It is solved at the **default cut** and scaled with WEIGHT
like the rest of R2, so foot over thickest reads 100.0% at (1, 1) and drifts
either side: **86% at Thin, 123% at Black, 136% at PUSH 0.30**. A round's
thickest point is `RING_W × WEIGHT + 19.83 × PUSH` — the band scales with
weight and the displacement does not — while a straight scales with weight
alone. Chasing the invariant along the axes would mean the contrast axis
redrawing the skeleton, which is the one thing PUSH must not do. The rule is a
statement about the face, read at the face's own weight.

And it switches off with the widening: R2c is not a separate idea from R2b but
the rest of the same one, so `ORPHAN_FOOT=0` turns off R2b, R1b's gain and this
together and the face reproduces the mark exactly — which is what
`proof.py --overlay` is built with.

The rule is stated on the stem field. The backslash field keeps its own
measured offset from it, 2.36 units lighter, exactly as it does everywhere else
in R2.

**R3. Verticals.** No exemplar exists, so a stem takes the left leg's profile:
**65.00 at the baseline tapering to 20.89 at the cap line** — R2b and R2c reach
every upright in the face through this rule, which is the whole of its scope.

The check on borrowing the leg was the O: a stem beside an O should carry the
O's average weight, and before R2b the profile's width at mid-height
(**32.94**) sat within **0.73%** of the O's mean stroke (33.19). Under R2's
pre-correction numbers it was 33.30, within 0.34%. **R2b breaks that check**:
mid-cap is now **42.94** against a round band of **40.69**, 5.5% over. The
check was always a corroboration rather than a derivation, and what it
corroborated — where the stem's profile came from — has not changed. But it no
longer lands exactly, and that is the strongest argument against R2b.

It broke by 29% before R1b, and R1b could close it completely by setting FOLLOW
to 1. The 5.5% that is left is bought, not conceded: it is the price of R2c's
wider foot, and the alternative was to take the whole of that price out of the
cap width instead.

R2b does not fit through the axes for free either. The U's left stem is set
tangent to the counter on its bowl's heavy side, which fixes the inner edge
and lets the outer edge fall where it may; once the stem is wider than the
band there, the outer edge falls out of the bowl entirely and the join has no
solution. Measured across the master grid, the largest widening the old rule
tolerated ran from 22.13 units at Thin/PUSH 1.00 down to **2.97 at Black/PUSH
0.30**, so +20 broke 13 of the 18 masters. The stem now takes **whichever
tangency keeps it inside the bowl** — the counter while it fits, the outer
circle once it does not, the two coinciding at the crossover. Past that point
the silhouette is the smooth one and the counter takes the corner, which is
what the light side already does on the other stem.

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

**OPEN: how literally to take the ring.** What is built and shipped is reading
**A** below. Readings B–E were measured and drawn but not landed, and the choice
between them is deferred rather than settled. `measure/ring_readings.py` rebuilds
all four; the sheets are in `measure/evidence/ring-*.png`.

The rules above cap the chord's rise at the A's own 90.77, so a long chord
flattens (an H's bar to 9.34°). That is one reading of "the horizontal is a chord
of the ring", and the A cannot confirm it: its span, 251.1, is exactly where
constant-rise and constant-angle cross, since the crossover *is* `RISE /
tan(RING_TILT)` and both are measured off that same bar. The mark is silent here.
Only the page decides.

- **A — capped rise** (shipped). Tilt falls with span: 19.87° under 251 units,
  9.34° at an H's 551. Band constant, R4's linear taper. The cost: at long spans
  the bar leaves the ring — an H's bar ends sit ~54 units off the underlay.
- **B — the ring's own angle.** Centre a chord on the ring and its tilt is
  constant at **19.87°**, the rise scaling with span. This is what a real ring
  behind the page does: a wider letter is a bigger window on the same object.
  One rule, no cap, and the bar stays on the ring at every width. An H's bar
  rises 199.4 units instead of 90.8.
- **C — B, plus the ring's width profile.** Same ends as R4, but the middle
  swells: ×1.016 on a G's bar, ×1.043 on the A's own, ×1.083 on an E's arm,
  ×1.265 (+8.8 units) on an H's. Still R4's circular arch underneath.
- **D — the annulus, weight normalised.** Both edges taken straight off the two
  ellipses (§2.2) through `build_A`'s transform, so the arch is elliptical, its
  curvature varies along the bar, and the edges are struck separately. Scaled
  about its centre line so midspan meets R4's nominal: 27.1 / 33.2 / 25.4 across
  an H's bar. **Note this overrides R7 for interior horizontals** — the ring's
  band is near-symmetric about midspan, not weighted to the left, so the
  directional taper R7 asks for is gone. That is a decision to take on purpose,
  not to inherit.
- **E — the annulus verbatim.** The mark's own weight, untouched: 40.8 / 50.0 /
  38.3. Literally what the logo does — SPEC §2.2 records the bar as the mark's
  heaviest stroke, 6.0–6.4 pt against the O's 4.2 — and a much darker face, with
  every interior horizontal near 50 units against stems of 33.

Two measurements that bear on the choice. The A's bar's edges really are
separately struck, the upper on a radius of 2118.2 units and the lower on 2742.8
(whole-edge circle fits to the drawn outline, max residual 0.074 and 0.100). And
an H's bar at 551.6 units spans 69.9 pt of the ring, against the ring's own
visible bar of about 70 pt — so an H shows very nearly the whole thing, where the
A shows its middle 45%. The ring can supply chords up to 695 units and the widest
interior horizontal in the face is the 4's crossbar at 558, so none of B–E
degenerates anywhere.

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

## 5b. How far the axes run

The WEIGHT and PUSH knobs are bounded by the **bowl letters** — B, D, P and R,
each a round solved against a horizontal on one or both faces. They, not the
diagonals, decide the range. `measure/bowl_region.py` draws the map.

The whole 63-glyph set builds over **WEIGHT 0.60–2.00 × PUSH 0.30–1.00**, and
the variable font is cut at **0.70–2.00** (wght 280–800), which holds at every
push in that range. It was 0.85–1.45 (wght 340–580) until both of the things
holding it there turned out to be the solver rather than the letters:

- **The B's cap-line trim left a straight chord across a round band.** A
  straight line across a round band is the one path that heads for the counter,
  because the band's own curve falls away from it. The edge follows the band
  now, so its clearance is the band's thin side rather than a chord's worst
  case — **13.30 units at the mark against 8.54** — and it holds until
  `ROUND_THIN` itself runs out.
- **`_wedge_x` searched undamped.** From the counter's right extreme its first
  step jumped clean past the solution, and at that x the arm's inner edge missed
  the counter altogether. The B failed at low push not because there was no
  wedge but because the search stepped over it. It is damped now, like
  `_bar_bowl` and `_arm_bowl` already were.

What bounds it now is geometry, not tooling:

- **Below about push 0.12** the counter has moved so far from the cap line that
  a cap-line arm's inner edge never reaches it, and there is no wedge to solve
  for. Checked directly: over every x where the edge meets the counter at all,
  the solution always lies to the left of the trial, so no fixed point exists.
- **At the push ceiling**, `ROUND_THIN` goes to zero — the round is closing into
  a C. That is the knobs' own ceiling anyway (`PUSH = 1.674 × WEIGHT`).
- **Past weight 2.00** the bowl's outer circle and its horizontal's outer edge
  stop meeting.

## 5c. The figures

The ten figures were settled together rather than one at a time, because the
thing that decides them is how they sit in a row.

**The rounds now agree.** Every lower round is **464** deep: the 5's bowl, the 6
and 9's shared bowl, and the 3 and 8's lower rounds. Before, they ran 390–430
with the 5 the shallowest, and the 5 read light beside its neighbours.

**The 5.** Bowl 558 × 464, terminal at 165°, and the bowl carried on to 84°
before the bar swallows it. Its bar stays **level**, and that is a derived
result rather than an exception: the bar meets the bowl at its TOP, where the R1
band is 19.4 units, and the bar carries 47.2. A 47-unit stroke cannot hand off
to a 19-unit band without a ledge, so its underside has to run level to a wedge
— which is exactly what §5's `set_bowl` note says about the cap-line arms of B,
D, P and R. The rule generalises: **a horizontal meeting a round at its thin side
must run level; one meeting it at the thick side can hand off, and can therefore
take R4b's tilt.** A tilted bar was drawn and measured: its underside falls
inside the bowl's counter from x≈120 onward, so the figure has no solution, not
merely an awkward one.

**The 6 and 9.** The shared bowl follows the 5 to 464; the 6's terminal swings up
from 45° to 55°. The spine's height had been written as a literal `515`, which is
only correct while the bowl is 205 deep — it is derived now, `TOP − (BOT + B69)`,
so the 6 keeps reaching the top of the figure when the bowl moves.

**The 3 and 8.** These are two-storey, so their two rounds share a 720-unit
budget and a deeper lower round has to be taken out of the upper. Two things
follow:

- The upper round is **370 wide** against the lower's 558. At the old 88% the two
  bowls were nearly the same round twice, which is what made the 8 read as two
  circles stacked rather than as one letter.
- The upper round's **height is solved, not chosen**. The ink between the two
  counters at the waist is `2·RING_W − overlap`; the overlap is pure geometry
  while `RING_W` scales with the weight, so a fixed height gives a waist that is
  half a stroke at Thin and one and a half at Black. Setting `overlap = RING_W`
  puts exactly **one stroke** between the counters at every point on both axes.
  At the mark's own weight that lands on 289.2, which is where the constant had
  been set by eye.

**The 8's silhouette is one contour.** Unioned from two closed rounds it corners
at each waist — 42° at these proportions — and that corner is what the eye reads
as two separate objects. It is traced as a single outline now, upper round over
the top and lower under the bottom, with each corner bridged by an arc of
**`ROUND_THIN`** (13.4). That is the O's own thin side, the narrowest stroke the
face draws anywhere, so no new number enters and the join follows both knobs;
at the top of the push axis it goes to zero and the join relaxes back to the
plain corner, which is the same place the round itself closes into a C. Larger
radii were drawn and rejected: by r 50 the arc stops softening the corner and
starts packing the notch, taking the silhouette across the waist from 200 units
to 276.

The counters are **not** derived from that silhouette. An 8's ink is two rings,
so its two counters are the two ring-holes; eroding the outer contour gives one
connected region, not two.

## 6. What is deliberately not in the face

- the white swash and the two eyes (need the ring or the animation);
- the A's lean and the A/O size ratio (composition);
- hooked, tilted or arched horizontals anywhere but the A (R4);
- a lowercase (D7);
- a second weight, though every stroke is parametric and the pen would take
  one.
