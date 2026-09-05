# AO mark write-on: choreography

Reference: `comp.mp4` (1920x1080, 29.97 fps, 80 frames, white mark on black).
Frame numbers are 0-based and times are `frame / 29.97`. Extracted frame
FILES are 1-based (ffmpeg's numbering): frame n is `f{n+1:03d}.png`, so
`f001.png` is frame 0 and the first inked frame, 8, is `f009.png`.
`contact-sheet.png` shows the active frames at 2x with frame number and time;
`timeline.json` is an older per-frame ink table (misregistered masks, timing
only).

The clip's mark is not the site's mark. Its A is narrower (the right leg is
9 deg off vertical against the site's 16 deg) and its bar is wider relative
to the A, so a single affine cannot register one onto the other; everything
below was measured relative to features (legs, bar, hook tips), not by
overlay.

## Verifying

`compare.png` is produced by `scripts/anim-frames.mjs`: each video frame next
to the component seeked to the same time, f4..f36. Rerun with a preview and a
headless Chrome running (astro preview binds `[::1]`, so `localhost`, not
`127.0.0.1`):

```bash
npm run build && npm run preview -- --port 4620 &
BASE_URL=http://localhost:4620 CDP_PORT=9222 FRAMES_DIR=path/to/frames node scripts/anim-frames.mjs
```

The harness aborts unless the first video tile with ink is frame 8, which
catches an off-by-one in the frame files.

`trail-modes.png` is produced by `scripts/anim-trail-modes.mjs` against the
same preview: the two trail treatments at 0.60, 0.72 and 0.85 s.

```bash
BASE_URL=http://localhost:4620 node scripts/anim-trail-modes.mjs
```

`trail-check.png` and `geometry.json`'s `trail_from_video` are the record of a
superseded pass; nothing produces them any more. See The pen trail below.

## What the clip does

| time (s)    | frames  | event |
|-------------|---------|-------|
| 0.00 - 0.24 | f0-f7   | black |
| 0.24 - 0.37 | f8-f11  | **left leg** drawn in one stroke from the **foot up to the apex** at constant speed: 21 % at f8, 46 % f9, 72 % f10, 97 % f11. |
| 0.35 - 0.50 | f11-f15 | **right leg** drawn from the **apex down to the foot**, same pace: 12 % at f11, 27 % f12, 52 % f13, 78 % f14, complete f15. The pen runs on into the trail. |
| 0.48 - 0.80 | f15-f24 | **pen trail**, a narrow stroke (about 0.55-0.6 of the bar's run weight; 40 px against the bar's 68-74 px in the clip). It leaves the right foot, dips, and curls up the OUTSIDE of the right leg (loop bottom f16, rightmost f17, climbing f18), crosses the right leg at 0.42 of the leg's height (f19), then runs LEFT under the bar, below it and roughly level while the bar rises to the right (f20-f22), crosses the left leg (f22) and ends on the left hook tip (f24). Head position along the trail: 7 % f15, 16 % f16, 26 % f17, 36 % f18, 46 % f19, 57 % f20, 67 % f21, 77 % f22, 86 % f23, 100 % f24: constant speed, the whole trail in 0.32 s. |
| 0.53 - 1.10 | f16-f33 | **thin circle** grows about the ring's outer centre from r = 0 as a hairline (5-6 px in the clip, 60 site units), at a steady rate until f24 then easing into its final radius (r = 88, 120, 151, 182, 213, 242, 268, 299, 329, 351, 371, 387, 400, 409, 412 viewBox units at f19..f33). |
| 0.73 - 1.08 | f22-f33 | the circle **thickens** linearly from the hairline to the ring's mean weight: 10, 14, 17, 20, 25, 29, 32, 36, 38, 40, 41 px at f23..f33 (41 px = 390 site units). |
| 0.80 - 1.03 | f24-f31 | **bar inks in** left to right along its centre-line, hooks included: hook tip and bend at f25 (9 %), to just short of the left leg at f26 (34 %), past it f27 (47 %), at the right leg f28 (63 %), 80 % f29, into the right hook f30 (93 %), complete f31. |
| 0.80 - 0.90 | f24-f27 | the trail's **tail retracts** from the right foot: the loop is gone by f27, when the tail sits at the right-leg crossing (0.386 of the trail): 5 % f24, 16 % f25, 27 % f26, 39 % f27. |
| 0.90 - 1.01 | f27-f30 | the **remnant under the bar** is erased right to left, slightly ahead of the bar head: gone (merged into the left hook) at f30. |
| 1.02 - 1.10 | f31-f33 | the ring gains its displaced counter and the mark settles; f33 is the final frame. |
| 1.10 - 2.67 | f33-f79 | complete; hold. Plays once. |

## The component's timeline (`src/components/LogoAnimated.astro`)

Every start and duration lives in the `--la-t-*` / `--la-d-*` custom
properties on `.site-logo-anim`; the animations only reference those.

| start | dur   | property        | element           | what |
|-------|-------|-----------------|-------------------|------|
| 0.24  | 0.13  | `--la-t-leg-l`  | `.la-leg-l`       | mask stroke `M1623 1201 L5916 10247` (foot -> apex), width 860, dash reveal, linear |
| 0.36  | 0.135 | `--la-t-leg-r`  | `.la-leg-r`       | mask stroke `M5916 10247 L8436 334` (apex -> foot), width 790, dash reveal, linear |
| 0.48  | 0.32  | `--la-t-trail`  | `.la-trail-m` or `.la-trail-line` | head: `stroke-dasharray` 0 -> 1, easing `--la-ease-head`, built per instance from the trail's landmarks (below); the layer switches on at the same instant |
| 0.535 | 0.565 | `--la-t-circle` | `.la-circle`      | `r` 0 -> 4038 with a `linear()` curve fitted to the measured radii |
| 0.73  | 0.35  | `--la-t-thicken`| `.la-circle`      | `stroke-width` 60 -> 390, linear |
| 0.80  | 0.23  | `--la-t-bar`    | `.la-bar-m`       | mask stroke on the bar centre-line, width 970, dash reveal with `linear(0, 0.09 14.8%, 0.34 29.6%, 0.47 43.9%, 0.63 58.3%, 0.8 73%, 0.93 87.4%, 1)` |
| 0.80  | 0.21  | `--la-t-tail`   | `.la-trail-m` or `.la-trail-line` | tail: visible span [tail, 1], tail 0 -> 1 with `--la-ease-tail`: the loop goes by 0.90 (tail on the crossing that closes it), the remnant by 1.01; the layer fades out over 20 ms at 1.01 |
| 1.02  | 0.08  | `--la-t-final`  | `.la-final`       | Logo.astro layer fades in over the pieces (brings the ring's counter and, for `hero`, the outline and shadow) |
| 1.10  | step  | `--la-t-done`   | `.la-pieces`      | legs, bar and circle switch off; the script then drops `la-play` |

The trail's head and tail run on whichever element the treatment renders: the
mask stroke that sweeps the swash, or the uniform line (see The pen trail).

**The two easings are the one thing not written in the stylesheet.** Both are
authored in fractions of the TRAIL, from `logo-trail.ts`'s `TRAIL_MARKS`, and
the component's frontmatter maps them to dash positions before emitting them
as `--la-ease-head-l` / `--la-ease-tail-l` on the mark. The stops in the built
HTML are therefore NOT the landmark numbers, and re-deriving them from the
marks by hand will get them wrong:

- `swash`: the mask sweeps a longer path than the trail (its lead-in and
  lead-out, below), so fraction `f` of the trail is at `0.0422 + 0.9463 f` of
  the dash. Head `linear(0.042, 0.524 48.1%, 0.902 89.7%, 1)`.
- `stroke`: the line's round cap puts ink half a pen width (190 units, 0.015)
  past the dash, so the dash runs that far behind. Head
  `linear(0, 0.494 48.1%, 0.894 89.7%, 0.985)`.

The percentages are the clip's: it closes the loop over the right leg at f19 =
0.634 s and reaches the left leg at f23 = 0.767 s, which are 48.1 % and 89.7 %
of the 0.48 -> 0.80 s window. Measured back off the built page by probing the
rendered pixels along the centre-line, the visible head sits at 0.510 of the
trail at 0.634 s and 0.907 at 0.767 s in both treatments, and there is no ink
at all at 0.480 s in `swash` (0.015, the pen tip, in `stroke`).

`linear()` easings sit behind `@supports`; browsers without it get
cubic-bezier approximations. `prefers-reduced-motion: reduce` disables every
animation, leaving the resting state (the final layer only), which is also
what renders with no CSS at all.

## Verifying the resting state

The final layer is Logo.astro's markup element for element (both draw the
path from `src/components/logo-mark.ts`), so once `la-play` is dropped the
component paints exactly what Logo paints. Checked by cloning a settled
`LogoAnimated`, building a plain Logo from its `.la-final` children, and
comparing the two inside one screenshot: 0 differing pixels at 28 and 44 px.
At 120 px and above a few hundred edge pixels differ, but two copies of the
static Logo placed at different offsets on the same page differ by the same
count, so that residue is Chrome's position-dependent rasterisation, not the
component. Compare at equal offsets or at the same position, never across it.

## Geometry

All in site path units (tenths, y-up, inside Logo.astro's
`translate(0,1084) scale(0.1,-0.1)` group). Full data and derivation:
`geometry.json`, `derive_geometry.py`, `derive_trail.py`,
`geometry-overlay.png`.

- Source -> site transform: `site = 106.2323 * R(0.0103 deg) * src + (110.284, -315.076)`; residual against the traced site path: mean 4.5, p95 12.2, max 20.6 units (0.05 / 0.12 / 0.2 pt).
- A: apex (5916, 10247), counter apex (5832, 9274), left foot tip (1274, 1100) / cut mid (1623, 1201), right foot cut mid (8436, 334) / tip (8737, 194). Each leg is the A polygon split at apex-counter, so a leg's mask reveals only its own leg. Leg mask width 860 for the left piece, 790 for the right (round caps); each
  covers its own piece's corners. The left piece runs 60 units past the
  apex-counter split, clipped back to the A's right outer edge, so the two
  fills interpenetrate instead of abutting — abutting fills are antialiased
  independently and leave a hairline of background down the apex for the whole
  animated span. Same trick, same 60 units, as the swash's two joins. Leg centre-lines are stored in the pen's direction: left foot -> apex, apex -> right foot.
- Bar centre-line: 10 cubics, length 13039, left hook tip (1669, 3683) -> right hook tip (9744, 5715). Marks by arc length: hook bend 0.091, bar left end 0.181, left leg 0.373, right leg 0.626, bar right end 0.831, right hook bend 0.915. Widths: run 605-650, left hook curl 891, right hook 516; mask width 970.
- Trail: see The pen trail below.
- Ring: outer centre (5523.1, 5424.9) r 4233.5; inner centre (5687.8, 5590.0) r 3843.2; counter offset 233 toward 45 deg; weight 623 / 157 / mean 390. The animated circle is centred on the outer centre and ends at r 4038, w 390, whose outer edge and average inner edge match the true ring; the final layer's fade-in supplies the counter.

## The pen trail

The trail is authored in the Illustrator file. `AO.ai` page 1 carries a fourth
filled object beside the ring, the bar and the A: a white swash lying under
them, invisible on the white artboard. Its centre-line starts 0.04 path units
from the A's right-foot cut midpoint, where the right leg's centre-line ends,
and finishes 0.24 from the start of the bar's centre-line, so the mark is
authored as ONE pen gesture: right leg -> trail -> bar.

`derive_trail.py` derives it into `geometry.json`'s `trail_from_swash`, in the
same site path units as everything else:

- `outline_joined_d` / `centre_joined_d` — **what the component uses.** The
  swash outline and its centre-line, with the join fix below applied.
- `mask` — the reveal sweep's path and the fractions that place the trail on
  it (edit 4 below).
- `outline_d` / `centre_d` — the authored shape before the fix, for reference.
- Arc length 12337. Width 663 at the foot, 1303 at its widest through the
  loop, 356 where it meets the hook.
- Marks: crosses the right leg at 0.033 (leaving the foot) and 0.509 (the
  crossing that closes the loop), the left leg at 0.909.

`derive_trail.py` owns the trail outright: `derive_geometry.py` derives the A,
the bar and the ring, and carries the two trail blocks forward untouched when
it rewrites `geometry.json`. It used to fit a second, coarser centre-line of
its own to the same swash, which disagreed (band width 632 against the real
1303, marks 0.537/0.891 against 0.509/0.909); that block is gone rather than
kept as a second answer to the same question. Each block in the file now
carries a `note` saying whether it is authoritative or superseded.

Four deliberate edits to the authored shape, all in `derive_trail.py` and all
switchable off there:

1. **The tail's exit angle.** The swash's tail end face IS the left hook's
   return end face — the two objects share that edge exactly — but the pen
   turns 13.5 deg across it, which reads as a notch. The last 20 pt is
   re-aimed from 17 to 12 deg with the tip held at the face width; narrowing
   the tip instead opens a step. `join-variants.png` shows 17, 12, 8 and
   3.5 deg; `join-before-after.png` the chosen one. `BLEND = 0` restores the
   authored shape.
2. **Pinned end faces.** The outline is rebuilt by offsetting the centre-line,
   so its end cross-sections come out perpendicular to the pen. Neither
   authored face is: the tail's is off by the re-aim (38 units) and the head's
   is the A's foot cut, which the pen crosses at 68 deg (360 units). Both
   pairs of corners are pinned back onto the real edges over the first and
   last 12 pt — the head's onto the A's `rcut`/`rtip`, the tail's onto the
   hook's face — which closes the wedge of background that otherwise opens at
   each join.
3. **60 units of overlap** past each face, into the A's foot along the leg's
   own edges and into the hook along its return direction, so the abutting
   fills do not show an antialiasing hairline. The script aborts if either
   overlap is not fully inside the shape it hides in.
4. **A lead-in and a lead-out on the sweep path** (`mask`). The reveal is a
   dash sweeping a stroke along the centre-line. With ROUND caps the ink runs
   half a stroke width — 680 units, 5.5 % of the trail — ahead of the dash at
   the head and the same behind it at the tail: every landmark fires early and
   5.8 % of the trail pops in on the frame the layer switches on. BUTT caps put
   the boundary exactly at the dash, but then the boundary at each END of the
   path is a perpendicular cut too, and neither end face is perpendicular. So
   the sweep runs along the centre-line extended 550 units before its start and
   150 past its end (both derived from how far the faces and their overlaps
   reach, x1.5, and checked against sweeping over some later part of the
   swash), with butt caps. The trail then occupies [0.0422, 0.9885] of the
   sweep, which is the mapping the easings use.

### The two treatments

`LogoAnimated` takes a `trail` prop. Only the chosen treatment is rendered —
the other one's geometry never reaches the HTML, which is worth 5 KB per mark
— and the root carries `site-logo-anim-trail-<mode>` to style against.

| `trail` | what is drawn | reveal |
|---------|---------------|--------|
| `swash` (default) | `outline_joined_d` as a filled path, so the trail carries its authored taper: widest through the loop, narrowing into the bar | a mask stroke sweeping the extended centre-line at width 1360 with BUTT caps (the outline reaches 653 units from the centre-line), the technique the legs and bar use |
| `stroke` | `centre_joined_d` stroked at `--la-trail-weight` (380 units, 0.6 of the bar's run) with round caps | the dash reveal runs on that stroke itself; no mask |

**The clip matches `stroke`**: its trail is a uniform narrow line, about
0.55-0.6 of the bar's run weight. `swash` is the mark's own drawing and is the
default; `trail-modes.png` shows them side by side, and the two heads sit at
the same fraction of the trail in every column. The visible difference is
weight, not timing: through the loop the swash is 1303 units against the
line's 380, so at small sizes it reads as a brush flourish rather than a pen
line and crowds the A's counter around 0.70-0.85 s. If the mark is only ever
shown at 28-44 px, `stroke` is the more legible of the two, and it is also
what the clip does.

### The superseded video trail

An earlier pass traced the trail from the clip's own frames and warped it onto
the site's geometry; `geometry.json` keeps it as `trail_from_video` and
`trail-check.png` shows the fit. It is not used, and nothing derives it any
more. It was wrong at the source: the clip was rendered from a different
drawing of the mark. Registering the Illustrator mark onto the clip's final
frame by maximising overlap reaches only IoU 0.55, and the whole residual is
in the A, whose legs in the clip are narrower and more upright (the ring and
the bar match well), so the traced line had to be snapped to the site's legs
and hook at four landmarks to land anywhere near them. The swash needs no
snapping: it joins the source's own A and bar to 0.00 pt.
