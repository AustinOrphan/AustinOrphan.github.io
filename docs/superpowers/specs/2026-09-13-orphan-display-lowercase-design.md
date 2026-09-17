# Orphan Display: a lowercase

**Status:** design agreed, not yet implemented
**Supersedes:** SPEC.md D7, which recorded the face as unicase

## Why this reopens D7

D7 says: *"The source has no lowercase, so there is no lowercase DNA to extrapolate
from; inventing 26 forms would be exactly the guesswork this project refuses. This is
the largest scope decision in the face and the easiest to revisit."*

It is being revisited because its premise is narrower than it reads. Only two of the
face's 63 glyphs are traced: the A and the O. The other 61 — the S, the K, the W, the
ampersand, the figures — are composed from R1 through R9, and the S is recorded as a
deliberate departure from R8's width classes. The face already builds letters the mark
never contained. A lowercase differs in degree, not in kind.

What stays true from D7 is that some lowercase letters reach further from the mark than
others. So each letter carries a stated provenance: derived where the rules reach it,
designed where they do not, and the difference recorded rather than smoothed over.

## The governing principle

**Apply the existing rule literally. Where it surprises, record the surprise rather
than add a special case.**

Three decisions below follow from this and would each have gone the other way under a
different principle: R3 is read unchanged at lowercase heights even though it gives
stems a third heavier than the bowls they join; R2 is read below the baseline even
though it was never measured there; and the x-height sits at a proportion that pulls
against the construction rather than agreeing with it.

## 1. Vertical metrics

| | units | share of cap |
|---|---|---|
| cap height (existing) | 700 | — |
| x-height | 385 | 55% |
| ascender | 700 | level with the cap line |
| descender | −185 | |
| overshoot, lowercase rounds | 10 | unchanged from `OVER_ROUND` |
| declared ascent / descent (existing) | 800 / 200 | unchanged |

These are D6-class typographic constants — the mark cannot supply them — and belong in
`lib/metrics.py` beside `CAP`, `SB_ROUND` and `SPACE_ADV`.

### The x-height is a deliberate collision

55% is small for a geometric sans; faces of this kind usually sit between 65% and 73%.
It was chosen knowing that, because the tension between an old-style proportion and a
ring-and-band construction is the point rather than an oversight.

It was not chosen to fix colour, and the record should be clear about that. R1's band
and counter displacement are absolute, not proportional, so a smaller x-height makes
the lowercase o's band a larger share of its own diameter: 10.05% at x-height 385
against the cap O's 5.65%. That is the normal typographic relationship — a lowercase
carrying the same absolute stroke as the capitals is why all-caps setting looks lighter
— and it needs no correction. Scaling the band to match the capitals' ratio is in any
case impossible: it would put the band at 22.88 against a displacement of 24.31, and
the counter would escape the outer contour and open the o into a C.

### Ascender and descender

Ascenders sit level with the cap line rather than above it. An old-style proportion
would normally put them above, which would reinforce the character, but `b` standing
taller than `B` reads as an error in a face whose capitals are this geometric.

−185 keeps the lowercase inside the declared descent of 200, with the same clearance
the comma now has after its tail depth was pinned. The 700-above to 185-below ratio is
3.8:1, inside the ordinary range.

Overshoot stays at 10 units, absolute. It corrects for the eye rather than scaling with
the form, and holding it constant is both conventional and what R1's absoluteness
predicts.

## 2. Character

**Single-storey `a` and `g`.** The `a` is R1's ring plus an R3 stem; the `g` is that
ring plus a descender. Both fall out of rules the face already has, so both stay on the
derived side. A double-storey `a` would need an arch and a bowl-to-stem junction that
nothing in the mark supplies, and a double-storey `g` two bowls and a link with no
relative among the existing 63 glyphs.

The cost is accepted: single-storey forms are less legible in running text and read as
more mannered. With a 55% x-height and long ascenders the result is a distinctly
classical-geometric character.

### The descender terminals are not a free choice

A single-storey `g` is a ring with a descender. So is a `q`. Drawn with the same
terminal they are **the same glyph** — this was confirmed by drawing all five
descending letters against seven terminals and finding `q` and `g` indistinguishable in
every row. The terminal is therefore what makes a `g` a `g`, and it cannot be uniform
across the set.

| letter | terminal |
|---|---|
| `p` `q` | plain, R5 cut |
| `g` | the stem bends onto the mark's stress axis and turns into a tail — see below |
| `j` | the J's hook, an R1 arc of radius 92 |
| `y` | no terminal; the right arm runs to the foot and takes an R5 cut |

`p` and `q` stay plain precisely so that `g`'s tail can do its work. Every free end in
the face is cut per R5, so a flat descender foot would be the only uncut terminal in
the typeface.

### The `g` and the `q` are one construction

Both letters are the `o`'s ring plus **one R3 stem**, placed by §4's tangency. The `q`
leaves that stem straight and cuts both free ends per R5. The `g` bends the same stem
onto the mark's own stress axis at y 90, runs 110 units along it, and then turns into
the tail, whose tip is R5-cut at 34 units. Nothing else differs, which is what makes
them read as one family rather than two unrelated letters.

The kick's direction is the mark's stress axis, **−45.067°**, and it is fixed: `RING_OFF`'s
two components both scale with PUSH, so PUSH changes the displacement's length and never
its angle. Measured at all twelve cells of the shipped axis grid, the angle is 45.067° in
every one. What does move is the band the kick departs through — 28.50 at Thin, 40.74 at
Regular, 81.43 at Black.

The tail's depth is **solved per master**, not chosen: the knee is moved until the ink
bottoms on −195, the descender plus `OVER_ROUND`. That holds to −195.0 in all twelve
cells. The overshoot is correct for the `g`, whose tail turns through the descender line
as a round does. It is **not** correct for the `q`, whose foot is a flat R5 cut and should
sit on the declared −185 exactly, the way a straight sits on the baseline; the drawings
currently put it at −195 and need correcting. Worst cubic fit over the grid is 0.262 against `MAX_ERR` 0.6, with the knots taken
once at the axis origin and held.

**An alternate is kept.** The same stem with no kick turns straight into its tail; it
reaches only 409.6 and so stays inside the advance, needing no kerning anywhere. It is
the safer letter and the less characterful one, and it should stay drawn until the rest
of the descending set exists.

**A stemless `g` was drawn and rejected.** It was the `o` plus the `Q`'s own leg — a
straight R2 diagonal springing from the counter on the stress axis, turned into a tail.
Alone it was the better letter: its spine was the best-conditioned of anything drawn
(compatible at 32 knots and insensitive to the count, where the stemmed versions needed
26 to 40 and one failed a corner), its departure dent was 27.0 against the shipped `Q`'s
71.4 at the same junction, and having no stem it could not collide with `q`. It was
rejected because of what it did to the `q`: with both letters built that way, the `q`'s
bowl is unsupported above y 95 and reads as an `o` with a leg. The construction that made
the `g` good made the `q` weak.

### The `y`

Two R2 arms, the right one carrying on past the junction to the foot: a v with a tail,
not a capital Y with a descender bolted on.

The junction sits at **114.5**. That is the capital Y's own rule — `MID_Y = CAP/2 +
HORIZ_MID/4`, the optical middle it shares with E H K X — applied to the lowercase
stroke **measured whole**. The capital's stroke runs from the baseline to the cap line;
the lowercase's runs 185 units further down, so the same rule puts its junction lower
relative to the x-height: 0.297 of it rather than 0.521.

## 3. Stems

**R3 unchanged.** A lowercase stem takes `w_slash(y)` exactly as a capital does.

R3's claim is that a stem at mid-height matches the O's mean band, and at cap height it
holds to 6% — 42.94 against 40.69. At lowercase heights it does not: 52.87 at mid
x-height (+30%) and 65.00 at the baseline (+60%).

Two alternatives were drawn and rejected. Holding the stem flat at the band's 40.69
gives the evenest colour and seamless shoulders, but makes the lowercase monolinear
while the capitals keep R2's baseline widening. Re-anchoring R3's field over 0..385 so
mid-x-height lands on the band keeps R3's sentence true at both scales.

The objection to re-anchoring is stronger than "it adds a rule", and the earlier draft
undersold it. **Re-anchoring is not a coherent rule at all.** Read over 0..385, the field
gives −15.2 units at the ascender line; scaled by 385/700 it gives −8.4. Ascenders run to
700, so both readings have run out of field before `b d h k l` reach their tops, and the
stem has no width there. Anchoring each letter on its own extent instead would give `l`
and `n` different stem widths at the same height, which is plainly wrong. R3 read
literally is the only one of the three that is well defined.

**The cost is real and belongs in the record.** Lowercase stems are **2.24×** the
capitals' relative weight — 13.73% of the x-height against 6.13% of the cap height — and
the rounds 1.78×. Set together, `DOG gogo` reads close to two different fonts on one
line. That is a consequence of R1's band being absolute rather than anything R3 could
fix: §1 already records that scaling the band puts it at 22.88 against a displacement of
24.31 and opens the `o` into a `C`. The lever, if this ever needs one, is the x-height,
not R3.

**The step this implies is solved, not accepted.** The capitals have the identical
mismatch — a capital B's stem is 65 at the baseline against a bowl band of 40.7 — and
the face solves it per junction with `_heavy_junction`, `_light_junction`, buried feet
and fill lenses. The lowercase junctions get the same treatment. A butt joint between a
65-unit stem and a 40.7-unit band is a drawing error, not a consequence of R3.

**Below the baseline, R2 extrapolates — and the face already does this.** R2 was
measured on the A's legs, which span the baseline to the cap line, so a descender foot
at y = −185 reads 76.66 units by extrapolation.

That looked like the weakest claim in this document until the face was asked what it
already does down there. Exactly one stroke in the existing 63 glyphs descends below
the baseline: the comma's tail, which reaches −169. R2 gives it **75.65** units at its
tip, 16.4% wider than at the baseline, and that is what ships today. A lowercase
descender at −185 reads 76.66, within **one unit** of shipped precedent.

So the extrapolation is not invented. It is the rule the face's only descending stroke
already follows, and the lowercase lands a unit away from it.

## 4. Bowls

**A bowled letter's stem is placed so its outer edge runs TANGENT to the bowl's outer
circle**, solved with `set_round._stem_tangent_x`.

Not on the circle's extreme. R3's stems taper, so a stem edge is not vertical, and an
edge set on the extreme meets the circle at exactly one height and parts from it
everywhere else. Measured on the lowercase bowls, the circle then pokes **6.17 units**
past the stem at the bowl's widest point, on both sides, putting an S-curve in a flank
that should run straight. Tangency gives 0.00: the two touch and never cross.

This is not a new rule. `_stem_tangent_x`'s own docstring records the same mistake and
the same fix at capital scale — *"setting the edge on the extreme leaves the two curves
a fraction of a unit apart everywhere else, which is a small step in the finished
outline (0.6 units on the U's counter, 1.1 on the J's silhouette)."* The lowercase
version of that step is ten times larger, because the bowl is smaller relative to the
taper.

Two alternatives were drawn and rejected. Centring the stem on the band fails because
**the ring is not symmetric**: R1 displaces the counter toward 45°, so the band is 57.86
units on the left and 23.52 on the right, and a mirrored placement rule sitting over an
unmirrored ring leaves `d` and `q` with a stem protruding 12 units past their bowls.
Setting the outer edge on the extreme is the 6.17-unit case above.

### The crown notch belongs to `p q g`, not to `b d`

Tangency has a consequence §4's first draft did not state. A stem's inner edge leaves the
ring's outline at **y = 322.2**, so above that the stem stands clear of the bowl and there
is a gap beside it. Measured as a dip in the top profile, every bowled letter shows one:
`b` and `d` 70.4, `p` and `q` 60.3, `g` 60.4.

**Those are not the same thing, and an earlier draft of this section wrongly said they
were.** What the dip means depends on where the stem stops.

- On `b` and `d` the stem runs on to the ascender, so the profile rises past the bowl and
  the gap is the **aperture** between bowl and ascender — a normal feature of the letter,
  present in every `b` and `d` ever drawn. Nothing to fix.
- On `p`, `q` and `g` the stem stops level with the bowl's crown. Two ink extremes sit at
  the same height with a V between them, and that reads as a **nick**. This is the defect.

So it is three letters, not five, and the fix has to put ink in the wedge rather than take
it away: ending the bowl's arc on the stem's crossing, the way `build_D` does, leaves the
dip unchanged at 70.43 and 60.3 because the D closes that wedge with its cap-line **arm**,
which a lowercase bowl does not have.

The notch's depth is exactly `stem top − 324.6`, so dropping the stem to 324.6 closes it —
at the cost of a stem that no longer reaches the x-height. A bespoke fix was also drawn and
rejected: an arc bridging the `g`'s stem-top to the bowl, tangent at 70° and passing through
the stem's R5 corner. It closed the notch and read as an added part rather than a junction.

### `d` and `q` are the light-side case

No capital in the face puts a stem to the right of a bowl. B, D, P and R all have the
stem on the left, against the heavy 57.86 band. Only the U has ever met the light side,
and only with a partial round. A 65-unit stem is 12% wider than the band it meets on
`b`, and 176% wider on `d`. These two letters should be expected to need the care the
U's right junction needed, and they are the ones most likely to fight during stage one.

## 5. Spacing

R9 unchanged: 60 beside a stem, 40 beside a round, by the shape of the extreme.

**The `g` is the first glyph whose advance is not set by its own ink.** Its tail reaches
499.4, but the advance is 485 — the `o`'s own, measured from the bowl — and the tail
projects 54 units past it. Setting the advance from the tail instead gives 579 and opens
a hole beside every `g` at x-height level, because the tail's extreme is below the
baseline where nothing else is.

The projection is safe as measured and tight as measured: the closest approach to a
following `g`, `q` or `o` is **61 units**, against the **80** two `o`s clear. The face
already pays for this idiom in the capitals the other way round — the `Q`'s advance is
844 against the `O`'s 800 — but a `Q` appears once a paragraph and a `g` appears
constantly, which is why the `g` projects rather than widens.

**This clearance is provisional.** It is measured against `g`, `q` and `o` only. `j`, `y`
and `p` do not exist yet and could sit closer; the number must be re-taken once the
descending set is drawn.

## 6. Scope and staging

**Stage one** — every letter needing no new construction machinery, only R1 arcs, R3
stems, R4 bars and R5 cuts:

```
a b c d e f g h i j l m n o p q r t u
```

Nineteen letters. Provenance: all derived, with two needing an argument recorded in
their glyph notes. The `e` takes its aperture and bar from the C and R4, but its
proportion is a choice. The `j` has no relative except the existing J.

Stage one exists to prove the metrics on running text before the remaining letters
depend on them. The 55% x-height is the unusual decision here and it should be read in
a paragraph, not a table.

**Stage two** — `k s v w x y z`. The diagonals need R2's field read at lowercase
heights; the `s` needs `set_round`'s elliptical construction scaled down.

Each stage gets its own spec, plan and pull request.

## 7. Code

Following the existing grain, which organises glyphs by construction family rather
than alphabetically:

| file | holds |
|---|---|
| `glyphs/set_lc_round.py` | `o c e b d p q a g` |
| `glyphs/set_lc_straight.py` | `n m h u i l r t f j` |
| `lib/metrics.py` | `XH`, `ASC_LC`, `DESC_LC` as D6 constants |

`lib/rules.py` is unchanged. That is the point of reading R3 and R2 literally, and it
is the strongest single argument for the choices in §3.

`compile_font.py` currently maps each lowercase codepoint onto its capital (line 39)
and declares `os2_xheight = cap` (line 22). Both change: the lowercase glyphs take
their own codepoints, and the declared x-height becomes 385.

## 8. Verification

- `measure/vertical_metrics.py` sweeps both axes and covers the new glyphs unchanged.
  It will catch a descender that breaks the declared metric, which is a live risk given
  R2 extrapolates below the baseline.
- `measure/vf_roundtrip.py` and the whole-font interpolation audit apply unchanged.
- **New:** a junction sweep that fails when a stem-to-bowl join leaves a step in the
  silhouette. §3 makes this the thing most likely to go wrong silently, and nothing
  currently checks it. The threshold is not invented: measure the capitals' own worst
  junction across the design space first, and set it there. The capitals already solve
  the identical problem, so whatever step they tolerate is the standard the lowercase
  should be held to.

## 9. What this document does not settle

- The ampersand. It is the worst-drawn glyph in the face and it cannot be judged until
  there is a lowercase rhythm to sit it on.
- Whether R3's taper survives contact with a paragraph. §3 now records the measured
  consequence — lowercase stems at 2.24× the capitals' relative weight — and shows that
  neither alternative reading is coherent. What is still open is whether that ratio is
  acceptable, and the lever is the x-height rather than R3.
- Whether the `g` ships with the kick or the no-kick alternate, and whether the kicked
  `g`'s 61-unit clearance survives `j`, `y` and `p`.
- The `q`'s flat foot is drawn at −195 and should be −185: overshoot belongs to rounds,
  not to R5 cuts. Same question for `p`, and for every flat lowercase foot.
- How `p q g` close their crown wedge. Three letters, one answer wanted.
- Whether R3's taper is bearable on an **ascender**. `b` and `d` were drawn for the first
  time here: their stems run 65.00 at the baseline to 20.89 at 700, so the ascender ends at
  half the bowl's own band (40.69) and reads as a spike. The capitals' stems do exactly the
  same thing over the same span, but against a bowl twice the size, so it shows far less.
- Kerning of any kind.
