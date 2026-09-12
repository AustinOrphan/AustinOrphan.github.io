"""The swash, re-derived for the mark the typeface draws.

The swash is construction rather than ink: it is the gesture the write-on pen follows, and
design/logo-animation/derive_trail.py reads its two long edges to get a centre-line and a
width profile.  It is not a free curve -- the artwork authors it to span exactly cut to
cut, and both of those cuts moved:

    head   items 4+5 run from the A's V[3] to its V[4], along the right foot's cut, which
           R2c widened from 6.2436 to 9.9763 mark units
    tail   item 11 runs along the hoop's hook face, bar item 7, which R1b's thicker band
           grew from 3.3477 to 4.1037

Leaving the swash alone does not keep the artwork's gesture, it breaks the one thing the
artwork pinned: the pen started on the foot it starts from and ended on the face it hands
off to.  Against the re-derived mark it started 268 path units away from that foot and 37%
narrower than it.

    THE SWASH IS A STROKE, AND IS WIDENED AS ONE.

That is the whole of this file.  The obvious approach -- treat the swash as an outline and
scale each edge about a centre-line paired by ARC FRACTION -- is wrong, because the outer
edge of a loop is far longer than the inner one, so the two samples are nowhere near across
from each other.  The "centre" is skewed, the "half-width" points the wrong way, and the
ribbon comes out swelling and pinching: measured perpendicular width 1.05 to 1.35 times the
artwork's where a flat 1.226 was asked for.

So the pairing is done properly -- marching, monotone, local, described at _pair -- and
then each edge is moved along ITS OWN half-width vector, which is the identity at gain 1
and leaves both edges with their own sampling and their own shape.  Only the ends need
more: the gain ramps out where the pairing bridges the cuts rather than crossing the
ribbon, and a blend carries the edges onto the cuts themselves.

There is no width profile decision left to make.  The head cut grew 1.5978, but that is the
length of an OBLIQUE cut, not a stroke width: the perpendicular width just past it is 3.48,
not 6.24.  A wider cut at the same perpendicular width simply means a more oblique cut,
which is what R2c did to the A's foot, so the gain is RING_GAIN the whole way and the
obliqueness absorbs the rest.  An earlier cut of this carried the foot's 1.5978 into the
body and scaled the loop -- already the widest thing in the mark -- from 1303 to 1947 path
units, which filled the counter in and read as a slab.

One thing no offset construction gets for free is the angle the swash leaves the foot at.
The artwork grows it straight out of the leg: its outer edge leaves V[3] collinear with the
leg edge arriving there, 1.04 deg off.  Rebuilding leaves that at about 20 deg, a kink
exactly where the eye is drawn, so both departure handles are set back to the artwork's own
angles, measured AGAINST the A's edges rather than absolutely.  That is what makes the
swash follow the foot: R2c's flare turns the leg edge 2.3 deg and the swash turns with it.
Only the handles move; every anchor stays where the rebuild put it.
"""
import cmath, json, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'measure'))

import rules
from pen import fit_cubics

SRC_PATH = os.path.join(HERE, 'source', 'ai_objects.json')

HEAD_CAP = (4, 5)                 # the A's right foot cut, V[3] -> V[4]
TAIL_CAP = (11,)                  # the hoop's hook face, bar item 7
# each long edge walked HEAD -> TAIL, as (item index, walked backwards?)
EDGE_INNER = [(6, False), (7, False), (8, False), (9, False), (10, False)]
EDGE_OUTER = [(3, True), (2, True), (1, True), (0, True), (14, True), (13, True), (12, True)]
# (item, index of the anchor in it, index of its handle, the A's edge to measure against)
DEPARTURES = ((3, 4, 3, (2, 3)), (6, 1, 2, (4, 5)))

NS = 1500                                                     # samples along the spine
END_BLEND = float(os.environ.get('ORPHAN_SWASH_END', 0.06))   # residual anchoring span
HEAD_REACH = float(os.environ.get('ORPHAN_SWASH_REACH', 0.0))   # 0 = one cut-length of travel
PATH_REACH = float(os.environ.get('ORPHAN_SWASH_PATH', 0.0))    # 0 = one cut-length, as above
# How long the stroke runs STRAIGHT out of the leg before it turns, and where it is back on
# the artwork's path, as fractions of arc length.  Set where the counter-turn the run forces
# stays at a tenth of the curvature the stroke itself carries: at 4% of the trail it is
# 8.5%, at 5% it is 10.1%, at 6% 15.3%, and at one cut-length 86% -- by which point the S is
# plainly visible and the inner edge has stopped being fittable.  See `straighten`.
HOLD = tuple(float(v) for v in os.environ.get('ORPHAN_SWASH_HOLD', '0.025,0.08').split(','))
# How much of the hook's curvature to keep, and how far the hook runs.  Below 1 the turn
# takes a bigger radius, so the bottom of the hook sits lower and rounder and its counter
# opens.  The stroke thickened inside an envelope that did not grow, which closes a counter
# the way it does in any bold weight; the artwork keeps a gap of 0.49 times the stroke
# width between the two arms of the curl.
# OFF.  Scaling the hook's curvature does reopen its counter, but it is the wrong
# mechanism and it was the single largest source of fault in this outline.  Opening by 14%
# throws the far end 37.2 mark units off the hoop -- a quarter of the trail's own length --
# and the correction needed to drag it back IS the deformation: it left the outer edge with
# a knuckle of radius 0.069 mark units on a 7.3-unit band, straight flanks either side of
# it, and the swash reaching x=103.0 where the artwork reaches 94.5, outside the mark.  At
# 1.0 the transform round-trips to 0.065 units, so the machinery is sound and the setting
# is not; the counter is opened by DEEPEN instead, which is local and needs no such
# correction.  Kept, off, because the measurement is worth not repeating.
OPEN = float(os.environ.get('ORPHAN_SWASH_OPEN', 1.0))
OPEN_TO = float(os.environ.get('ORPHAN_SWASH_OPEN_TO', 0.30))
# How much deeper the bottom of the hook sits, in mark units, and over how much of the
# trail either side of it that is spread.  Opening the curvature deepens too, but it
# deepens by inflating the whole curl -- to reach 1.8 units it throws the swash out to
# x=117 against the artwork's 94.5, well outside the mark -- so the depth is put in
# locally instead, as a bump on the midline centred on the hook's lowest point.
DEEPEN = float(os.environ.get('ORPHAN_SWASH_DEEPEN', 4.0))
DEEPEN_SPAN = float(os.environ.get('ORPHAN_SWASH_DEEPEN_SPAN', 0.58))
# How much of the deepening goes into WIDTH rather than into moving the midline.  Dropping
# the midline drops both edges, and the inner one is on the concave side, so it tightens:
# the upper edge of the hook comes to a radius of about 1.2 mark units against the
# artwork's 6.1.  Putting two thirds of it into width instead holds the inner edge still
# and drops only the outer, which is what the depth is actually for.
DEEPEN_SPLIT = float(os.environ.get('ORPHAN_SWASH_SPLIT', 0.20))
# Over how much of the trail the inner edge's head is bent onto the leg's right edge, so
# the swash leaves the foot parallel on BOTH sides.  0 leaves it wherever the ribbon puts
# it, which is 70 degrees off -- worse than the artwork's own 57.
PARALLEL = float(os.environ.get('ORPHAN_SWASH_PARALLEL', 0.04))
# A light smoothing of each finished edge before it is refitted.  The transforms leave
# shallow dents -- stretches where the outer edge is locally CONCAVE, radius about 1.2 mark
# units on a band 7.5 wide -- which are high-frequency against a curve whose own radius is
# nearer 8, so a small window takes them out without moving the curve.
POLISH = float(os.environ.get('ORPHAN_SWASH_POLISH', 0.05))
GAIN = float(os.environ.get('ORPHAN_SWASH_GAIN', 0.0)) or rules.RING_GAIN


def _C(p):
    return complex(p[0], p[1])


def _seg_pts(it, n=160):
    P = [_C(q) for q in it[1:]]
    ts = [i / (n - 1.) for i in range(n)]
    if it[0] == 'l':
        return [P[0] * (1 - t) + P[1] * t for t in ts]
    return [(1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t * t * P[2]
            + t ** 3 * P[3] for t in ts]


WALK_N = 160


def _walk(items, walk, n=WALK_N):
    """The edge as one polyline, head -> tail."""
    pts = []
    for k, rev in walk:
        p = _seg_pts(items[k], n)
        if rev:
            p = p[::-1]
        pts += p[1:] if pts else p
    return np.array(pts)


def _pair(outer, inner, window=0.06):
    """Which inner sample sits ACROSS the ribbon from each outer one.

    A plain nearest-point search does not work on this shape.  The swash curls into a loop,
    so the outer edge of one part of the ribbon runs close to the INNER edge of another
    part, and the nearest inner sample to a point on the loop's outside is often most of
    the way round the gesture.  So the search marches: it starts paired head to head and
    may only ever move forward, within a window of where it already is, which is both local
    and monotone, the two things a ribbon's correspondence has to be.
    """
    w = max(2, int(window * len(inner)))
    out, j = np.empty(len(outer), dtype=int), 0
    for i, o in enumerate(outer):
        hi = min(len(inner), j + w + 1)
        j = j + int(np.abs(inner[j:hi] - o).argmin())
        out[i] = j
    return out


def _smooth(z, frac):
    """A light box filter, reflected at the ends so they do not drift."""
    w = max(3, int(frac * len(z)) | 1)
    return np.convolve(np.pad(z, w // 2, mode='reflect'), np.ones(w) / w, 'valid')


def _polish_edge(p, u, amount):
    """Smooth an edge's body, handing its two ends back untouched.

    A reflected box filter moves its own endpoints.  Letting it do that costs 0.84 mark
    units of anchor forcing where everything else here needs 0.001, and the end blend then
    takes that out inside 6% of the trail -- a fresh deformation on the foot it is trying
    to land cleanly on.  So the correction is tapered out over the same span the blend uses.
    """
    if amount <= 0:
        return p
    q = _smooth(p.real, amount) + 1j * _smooth(p.imag, amount)
    keep = np.maximum(_ease(1.0 - np.minimum(1.0, u / END_BLEND)),
                      _ease(1.0 - np.minimum(1.0, (1 - u) / END_BLEND)))
    return p * keep + q * (1 - keep)


def _ease(x):
    """A C2 ease: zero first AND second derivative at both ends.

    Every blend in this file moves POSITION, and a position blend that is only C1 puts a
    step in the curvature at each of its boundaries -- which is a crease in the outline,
    however smooth the tangents look.  Both the obvious easings are C1 only: the raised
    cosine has second derivative pi^2/2 at its ends, and smoothstep 3x^2-2x^3 has 6.  They
    are why the hook grew a knuckle of radius 0.159 mark units where the band is 7.27 wide,
    and why the flanks either side of it went straight.  The quintic is the cheapest curve
    that lands flat to second order at both ends.
    """
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (10.0 + x * (6.0 * x - 15.0))


def _arcfrac(P):
    d = np.r_[0.0, np.cumsum(np.abs(np.diff(P)))]
    return d / d[-1]


def _at(P, s):
    """The curve P sampled at arc fractions s."""
    f = _arcfrac(P)
    return np.interp(s, f, P.real) + 1j * np.interp(s, f, P.imag)


def _half(a_edge, b_edge, glide=0.02):
    """The half-width vector at every sample of `a_edge`, pointing at `b_edge`.

    The pairing is monotone but it STALLS: long runs of samples on one edge share a single
    sample on the other wherever the ribbon turns, so `b_edge[pair]` repeats points and
    then jumps.  What gets smoothed is therefore the CORRESPONDENCE, not the geometry: the
    pairing is really a monotone map between the two edges' arc fractions, smoothing that
    scalar map makes it glide instead of stalling, and the other edge is then read off at
    the smoothed parameter rather than being averaged, so neither edge is distorted.
    """
    t = _smooth(_arcfrac(b_edge)[_pair(a_edge, b_edge)], glide)
    t = np.maximum.accumulate(t)
    # Span [0, 1] exactly.  Smoothing a monotone rising map lifts its first value off zero,
    # which would leave the half-width vector at the head pointing somewhere just short of
    # the far side of the cut -- and the head's whole anchoring rests on that vector BEING
    # the half-cut, so the ends would then need almost two mark units of forcing to reach
    # the cut they are supposed to land on by construction.
    t = np.clip((t - t[0]) / (t[-1] - t[0]), 0.0, 1.0)
    h = (_at(b_edge, t) - a_edge) / 2

    # The half-width vector is a slowly varying quantity ALONG the ribbon, but it is read
    # off a discrete pairing, so it carries ripple at the sample scale.  At gain 1 that
    # never shows -- h is not used -- but the widening adds (gain - 1) * h to each edge,
    # and a second derivative of sample-scale ripple is enormous: the rebuilt edges came
    # out with 53 changes of curvature sign and curvature peaking at 25 against the
    # artwork's 0.77.  Smoothing h is safe in a way that smoothing the spine is not: it is
    # a width, not a path, so a window wide enough to clear the ripple costs nothing.  The
    # two ends are put back exactly, because the head's anchoring rests on h being the
    # half-cut there.
    e0, e1 = h[0], h[-1]
    h = _smooth(h.real, 0.015) + 1j * _smooth(h.imag, 0.015)
    h[0], h[-1] = e0, e1
    return h


def _fit_edge(pts, walk, head_tangent=None, per_item=True, n=WALK_N):
    """One cubic per SOURCE item, over that item's own stretch of the edge.

    Refitting the edge as a whole and letting the fitter place its own knots by worst error
    puts them where the curve strays most, which is the middle of the loop, and leaves the
    head sharing a piece with a long run behind it.  Averaged over that piece the head
    comes out straight -- spine curvature 0.001 where the artwork has 0.088 -- so the
    stroke runs out of the leg dead flat and then snaps into the curl a mark unit later,
    which is the break you see at the junction rather than a flow into the hook.

    The artwork's own knots do not have that problem: a designer put them where the gesture
    changes, and item 3 is the head's own piece.  So they are kept, and each item is fitted
    over the stretch it already covered.  It keeps the source's 15-item topology honestly
    too, rather than reusing the count while moving every boundary.
    """
    # Tangents come from the WHOLE edge and are then sliced, never taken per piece.  Per
    # piece, every knot gets a one-sided derivative and the two items sharing it disagree,
    # so the fit is handed a tangent the samples do not actually have: item 6 came back
    # with handles of 0.37 and 0.54 on a chord of 4.32, which is a cubic that is a straight
    # line with a hard turn at each end, and curvature peaked at 76 against the artwork's
    # 0.77.  Sliced from the whole, adjacent pieces share a knot tangent exactly and the
    # chain is G1 by construction.
    tan = np.gradient(pts)
    tan = tan / np.abs(tan)
    if head_tangent is not None:
        tan[0] = head_tangent               # a CONSTRAINT on the fit, not a twist after it
    if not per_item:
        # The source's knots only suit the source's shape.  Once the path is reshaped the
        # head needs its knots somewhere else, and holding them where the artwork put them
        # costs the inner edge 3 to 15 mark units of fit.  derive_trail reads items 6-10 as
        # a RUN, so where the knots fall inside it is ours to choose.
        return fit_cubics([(z.real, z.imag) for z in pts],
                          [(z.real, z.imag) for z in tan], nseg=len(walk))
    segs, err = [], 0.0
    for k in range(len(walk)):
        a = k * (n - 1)
        P, t = pts[a:a + n], tan[a:a + n]
        one, e = fit_cubics([(z.real, z.imag) for z in P],
                            [(z.real, z.imag) for z in t], nseg=1)
        segs += one
        err = max(err, e)
    return segs, err


def _write_chain(items, walk, start, segs):
    """Lay a fitted head -> tail chain back into the source's items and directions."""
    cur = (start.real, start.imag)
    for (k, rev), (c1, c2, p3) in zip(walk, segs):
        items[k] = ['c', list(p3), list(c2), list(c1), list(cur)] if rev else \
                   ['c', list(cur), list(c1), list(c2), list(p3)]
        cur = p3


def _similarity(a, b, A, B):
    k = (B - A) / (b - a)
    return lambda z: A + k * (z - a)


def _warp_cap(items, idxs, old_a, old_b, new_a, new_b):
    f = _similarity(old_a, old_b, new_a, new_b)
    for k in idxs:
        items[k] = [items[k][0]] + [[f(_C(p)).real, f(_C(p)).imag] for p in items[k][1:]]



def _departure_error(items, verts):
    """How far off parallel with the leg each edge leaves the foot cut, in degrees."""
    V = [_C(v) for v in verts]
    want = (V[3] - V[2], V[4] - V[5])
    return [math.degrees(cmath.phase((_C(items[i][h]) - _C(items[i][a])) / w))
            for (i, a, h, _), w in zip(DEPARTURES, want)]


def _curvature(items, walk, n=400):
    """Tightest radius on an edge, and the worst curvature jump across a knot.

    Tangent continuity is not enough and checking only it is how a knuckle got into the
    hook unnoticed: the joins were G1 to 0.000 deg while the curvature stepped 2049:1
    across one of them, which is a crease a pen could not make.  Radii are in mark units,
    so they are read against the local band width -- an outer edge whose radius is a
    fraction of the stroke's own width is a corner however smooth its tangents are.
    """
    tight, jump, ends = 1e18, 1.0, []
    for k, rev in walk:
        P = [_C(q) for q in items[k][1:]]
        t = np.linspace(0, 1, n)
        d1 = 3 * ((1-t)**2 * (P[1]-P[0]) + 2*(1-t)*t * (P[2]-P[1]) + t*t * (P[3]-P[2]))
        d2 = 6 * ((1-t) * (P[2]-2*P[1]+P[0]) + t * (P[3]-2*P[2]+P[1]))
        kap = np.abs(d1.real*d2.imag - d1.imag*d2.real) / np.maximum(np.abs(d1)**3, 1e-12)
        r = 1.0 / np.maximum(kap, 1e-12)
        tight = min(tight, float(r.min()))
        ends.append((float(r[-1]), float(r[0])) if not rev else (float(r[0]), float(r[-1])))
    for (_, a), (b, _) in zip(ends, ends[1:]):
        jump = max(jump, max(a, b) / max(min(a, b), 1e-12))
    return tight, jump


def _width_ratio(before, after):
    """How much wider the ribbon actually got, along the body, as (p10, p50, p90).

    Measured perpendicular width, at matched arc length along the outer edge, with the
    end regions left out: there the cap governs the width and a cut is not a width.  The
    interesting number is the SPREAD -- a gain that is not uniform is what makes a ribbon
    swell and pinch instead of reading as one stroke.
    """
    w = []
    for it in (before, after):
        o, i = _walk(it, EDGE_OUTER), _walk(it, EDGE_INNER)
        w.append((_arcfrac(o), np.abs(o - _at(i, np.clip(np.maximum.accumulate(
            _smooth(_arcfrac(i)[_pair(o, i)], 0.02)), 0, 1)))))
    g = np.linspace(END_BLEND, 1 - END_BLEND, 400)
    r = np.interp(g, *w[1]) / np.interp(g, *w[0])
    return tuple(float(v) for v in np.percentile(r, (10, 50, 90)))


def derived_swash_items(a_verts=None, hoop_items=None):
    """The artwork's swash rebuilt as a stroke on the re-derived mark's two cuts.

    Returns (items, report).  Pass the re-derived A vertices and hoop items to avoid
    recomputing them; both default to deriving them here.
    """
    if a_verts is None:
        from mark_derived import parts
        a_poly = parts()[0]
        a_verts = [list(a_poly.start)] + [list(s[-1]) for s in a_poly.segs]
        if len(a_verts) == 7 and a_verts[0] == a_verts[-1]:
            a_verts = a_verts[:6]
    if hoop_items is None:
        from hoop_derived import derived_hoop_items
        hoop_items = derived_hoop_items()[0]

    page = json.load(open(SRC_PATH))['AO'][0]
    src = {o['role']: o for o in page['objects']}
    items = [list(it) for it in src['white']['items']]
    before = [list(it) for it in items]
    # Both edges leave the foot cut running along the leg edge they meet, so the leg runs
    # on into the hook and the cut between them is never seen as an edge.  The artwork's own
    # angles are 1.04 deg off parallel on the outer edge -- near enough that it reads as a
    # continuation -- but 57 deg off on the inner one, which is a corner, and against the A's
    # 60% wider foot that corner is what makes the leg look sliced off rather than turned.

    # the four points the swash is pinned to.  The BEFORE anchors come from the swash's own
    # copies of them: the source rounds each object independently, so the A's vertices and
    # bar item 7 agree with the swash's copies only to about 5e-4.
    nV3, nV4 = _C(a_verts[3]), _C(a_verts[4])
    nf0, nf1 = _C(hoop_items[7][1]), _C(hoop_items[7][-1])
    oV3, oV4 = _C(items[HEAD_CAP[0]][1]), _C(items[HEAD_CAP[-1]][-1])
    of0, of1 = _C(items[TAIL_CAP[0]][1]), _C(items[TAIL_CAP[-1]][-1])

    # Each edge is moved along its OWN half-width vector, so at GAIN 1 nothing happens at
    # all and each edge keeps its own sampling and its own shape.  Rebuilding both edges
    # off a shared resampled spine is the tempting alternative and it loses exactly that:
    # the inner edge comes back as something a 5-cubic refit misses by 0.4 mark units,
    # against 0.11 for the artwork's own.
    outer, inner = _walk(items, EDGE_OUTER), _walk(items, EDGE_INNER)
    h_out, h_in = _half(outer, inner), _half(inner, outer)

    # At the cut the gain is the CUT'S OWN growth, not the body's.  The pairing bridges an
    # oblique cut at each end rather than crossing the ribbon, so what it reports there is
    # the half-cut -- and multiplying the half-cut by how much the cut grew lands the edges
    # on the new cut exactly, with nothing left for a blend to force.  Ramping the gain out
    # to 1.0 at the ends instead, which is what an earlier cut of this did, leaves the pen
    # at the ARTWORK's width where the A's foot is now 60% wider: the leg arrives 7.76 mark
    # units across and the hook leaves at 3.48, a step of 0.45 where the artwork steps 0.72,
    # and the stroke visibly drops rather than flowing on into the hook.
    #
    # At the tail the two already agree -- the hook face grew by RING_GAIN, which is the
    # body's gain -- so only the head has a flare to spend.  It is spent over ONE
    # CUT-LENGTH of travel, which is a measurement rather than a taste: the foot's
    # influence on the stroke leaving it reaches as far along as the foot is wide, so a
    # wider foot spends its flare over a proportionally longer run and the rule holds at
    # any weight.  Here that is 9.9763 units of a 135.2580-unit edge, 7.4% of the trail.
    k_head = abs(nV4 - nV3) / abs(oV4 - oV3)
    reach = HEAD_REACH or abs(nV4 - nV3) / float(np.sum(np.abs(np.diff(outer))))

    # The ribbon moves as ONE: the displacement is the CUTS' midpoints, common to both
    # edges.  Anchoring each edge to its own two endpoints instead pulls them apart by the
    # cut's whole growth, 3.73 mark units, right through the middle of the gesture -- the
    # ribbon then widens by 1.7 units at mid-length whatever the gain is set to.
    d_head = (nV3 + nV4) / 2 - (oV3 + oV4) / 2
    d_tail = (nf0 + nf1) / 2 - (of0 + of1) / 2

    aV = [_C(v) for v in a_verts]

    def straighten(mid, hold, release):
        """Run the midline straight out along the leg for `hold`, back on its own path by
        `release`.  Blended by POSITION, so past `release` the path IS the artwork's and the
        tail still arrives at the hoop exactly.

        This buys the straight run with an INFLECTION: the stroke bends off the artwork's
        curve, runs straight, and has to bend the other way to rejoin before resuming the
        curl.  That is not an artefact of this particular blend, it is the geometry.  Fix
        the arc length and ask for a straight run at the head and a single-signed turn after
        it, and the far end misses the hook face by 13 to 34 mark units depending how long
        the run is; let a solver close that by choosing the length, and it does -- at 2.27
        times the length, winding the same 266 degrees round a completely different gesture.
        There is no straight run at this arc length that lands on the hoop without one.

        So `hold` is a dial on a real trade, and it is set where the counter-turn stays
        under a tenth of the curvature the stroke itself carries -- visible in the numbers,
        not in the mark.  Turn it up with ORPHAN_SWASH_HOLD and the stroke leaves the leg
        straighter for longer and the S becomes something you can see.
        """
        if release <= hold:
            return mid
        u = _arcfrac(mid)
        d = np.r_[0.0, np.cumsum(np.abs(np.diff(mid)))]
        w = _ease(np.clip((release - u) / (release - hold), 0.0, 1.0))
        return mid + w * (mid[0] + axis * d - mid)

    e1, e2 = aV[3] - aV[2], aV[4] - aV[5]
    axis = e1 / abs(e1) + e2 / abs(e2)
    axis = axis / abs(axis)

    # Reshaped ONCE, on the outer edge's copy of the midline, and both edges then read the
    # same displacement off it by arc fraction.  Reshaping each edge's own copy separately
    # is the trap: they are the same curve but parameterised differently, so they come back
    # as two different curves and the pair stops bounding a ribbon at all -- the measured
    # width collapses to a quarter of the artwork's.
    def open_hook(mid, c, upto):
        """Scale the hook's curvature by `c`, giving the turn a bigger radius."""
        if c == 1.0:
            return mid
        n = 2000
        d = np.r_[0.0, np.cumsum(np.abs(np.diff(mid)))]
        t = np.linspace(0.0, 1.0, n)
        m = np.interp(t, d / d[-1], mid.real) + 1j * np.interp(t, d / d[-1], mid.imag)
        tg = np.gradient(_smooth(m.real, 0.01) + 1j * _smooth(m.imag, 0.01))
        k = _smooth(np.gradient(np.unwrap(np.angle(tg)), t), 0.01)
        w = np.clip((t - upto) / (0.5 * upto), 0.0, 1.0)       # c through the hook, 1 after
        g = c + (1.0 - c) * 0.5 * (1 - np.cos(np.pi * w))
        an = np.unwrap(np.angle(tg))[0] + np.r_[
            0.0, np.cumsum((k[1:] * g[1:] + k[:-1] * g[:-1]) / 2 * np.diff(t))]
        st = np.exp(1j * an)
        P = m[0] + d[-1] * np.r_[0.0, np.cumsum((st[1:] + st[:-1]) / 2 * np.diff(t))]

        # Re-integrating a changed curvature moves everything after it, so the tail ends up
        # 21 mark units off the hook's face.  That closing error is taken out smoothly over
        # everything past the hook rather than left for the end blend, which would otherwise
        # have to cram 21 units into the last 6% of the trail.
        P = P - (P[-1] - m[-1]) * _ease((t - upto) / (1.0 - upto))
        return np.interp(d / d[-1], t, P.real) + 1j * np.interp(d / d[-1], t, P.imag)

    def outward(mid):
        """Unit normal pointing AWAY from the hook's interior.

        The deepening used to displace straight down, which deepens the bottom of the curl
        but cannot push its flanks out -- and the drawn correction asks for both: it runs
        1.9 units below the bottom and then 2.6 units outside the right flank as it climbs.
        Down is only the outward direction at the very bottom; a normal is the outward
        direction everywhere.
        """
        t = np.gradient(_smooth(mid.real, 0.01) + 1j * _smooth(mid.imag, 0.01))
        n = 1j * t / np.abs(t)
        lo = int(np.argmin(mid.imag))
        return n if n[lo].imag < 0 else -n

    def deepen_bump(mid, span):
        """A raised-cosine hump over the bottom of the hook, zero at both ends of the trail."""
        u = _arcfrac(mid)
        u0 = u[int(np.argmin(mid.imag))]                  # the hook's lowest point
        # The bump has to reach zero at BOTH ends of the trail, and the hook's lowest point
        # sits at about 15% of it, closer to the head than `span`.  A symmetric window
        # therefore still has height left at u=0 and drags the head off the foot cut -- 1.53
        # mark units of it, which the end blend then has to force back.  So the left side
        # tapers over however much room there actually is.
        left = np.clip(1.0 - (u0 - u) / max(u0, 1e-6), 0.0, 1.0)
        right = np.clip(1.0 - (u - u0) / span, 0.0, 1.0)
        return _ease(np.where(u < u0, left, right))

    # The midline is smoothed before anything differentiates it.  It is built from the
    # pairing, and the pairing stalls -- consecutive midpoints repeat where the ribbon
    # turns -- so the raw midline carries sample-scale noise.  Measured on the ARTWORK's
    # own midline that noise reads as a radius of 0.000 mark units; open_hook takes two
    # derivatives of it to get curvature, so the noise comes back as real creases in both
    # edges.  The half-width vector is smoothed for the same reason a few lines up.
    mid_raw = _smooth((outer + h_out).real, 0.01) + 1j * _smooth((outer + h_out).imag, 0.01)
    opened = open_hook(mid_raw, OPEN, OPEN_TO)
    bump = deepen_bump(opened, DEEPEN_SPAN) if DEEPEN else np.zeros(len(opened))
    mid_ref = opened + DEEPEN * (1.0 - DEEPEN_SPLIT) * bump * outward(opened)
    disp_ref = straighten(mid_ref, HOLD[0], HOLD[1]) - mid_raw
    u_ref = _arcfrac(mid_ref)

    def place(edge, h, head, tail):
        u = _arcfrac(edge)
        g = GAIN + (k_head - GAIN) * _ease(1.0 - np.minimum(1.0, u / reach))
        # The displacement is looked up by POSITION along the shared midline, not by arc
        # fraction.  The two edges are parameterised quite differently near the head -- the
        # inner one is much the shorter -- so the same fraction is a different place on the
        # curve, and the bump lands offset on one edge against the other.  That put a hard
        # V in the inner edge just past the foot cut, radius 0.05 mark units where the
        # artwork has 6.09.
        mid = edge + h
        # Indexed against the UNDISPLACED midline.  mid_ref has already been moved -- by up
        # to 4 mark units at the bottom of the hook -- so asking which of its points is
        # nearest to an edge's own, still-undisplaced midline lands systematically off, and
        # by a different amount on each of the two edges.  The ribbon then spreads: a
        # displacement that only moves the midline, and must therefore leave the width
        # alone, was widening the stroke from x1.22 to x1.42.
        at = _pair(mid, mid_raw)
        if DEEPEN and DEEPEN_SPLIT:
            grow = DEEPEN * DEEPEN_SPLIT * bump[at] / 2.0
            h = h * (1.0 + grow / np.maximum(np.abs(h), 1e-9))
        mid = mid + disp_ref[at]
        p = mid - g * h + d_head * (1 - u) + d_tail * u
        p = _polish_edge(p, u, POLISH)
        a = _ease(1.0 - np.minimum(1.0, u / END_BLEND))
        b = _ease(1.0 - np.minimum(1.0, (1 - u) / END_BLEND))
        return p + (head - p[0]) * a + (tail - p[-1]) * b, abs(head - p[0]), abs(tail - p[-1])

    outer, r0, r1 = place(outer, h_out, nV3, nf1)
    inner, r2, r3 = place(inner, h_in, nV4, nf0)

    # Bend the inner edge's head onto the leg's right edge, as a rotation about the anchor
    # that decays away.  This moves the POLYLINE, so the refit follows it naturally -- the
    # thing that does not work is constraining the fit's departure tangent while leaving the
    # polyline at 70 degrees off, which collapses the first piece's handle to a cusp.
    if PARALLEL > 0:
        # A true BEND: each tangent is rotated and the edge re-integrated, then the position
        # error that leaves is taken back out over the same span.  Rotating the points about
        # the anchor instead is a shear, not a bend -- it concentrates the whole turn near
        # the anchor and leaves a bump, curvature peaking at 0.754 over the head where the
        # artwork peaks at 0.243, and no span helps because the concentration is the
        # mechanism rather than the amount.
        want = (aV[4] - aV[5]) / abs(aV[4] - aV[5])
        ui = _arcfrac(inner)
        t = np.gradient(_smooth(inner.real, 0.01) + 1j * _smooth(inner.imag, 0.01))
        rot = cmath.phase(want / (t[0] / abs(t[0])))
        w = _ease(1.0 - np.minimum(1.0, ui / PARALLEL))
        ds = np.r_[0.0, np.abs(np.diff(inner))]
        step = (t / np.abs(t)) * np.exp(1j * rot * w)
        bent = inner[0] + np.cumsum(step * ds)
        v = _ease(np.minimum(1.0, ui / PARALLEL))
        bent = bent - (bent[-1] - inner[-1]) * 0.0        # the tail is pinned below anyway
        inner = inner * v + bent * (1 - v)
        inner = _polish_edge(inner, ui, POLISH)
        inner = inner + (nV4 - inner[0]) * _ease(1.0 - np.minimum(1.0, ui / END_BLEND)) \
                      + (nf0 - inner[-1]) * _ease(1.0 - np.minimum(1.0, (1 - ui) / END_BLEND))
    residual = max(r0, r1, r2, r3)

    # Leaving the foot, the two edges disagree about what they are doing: the outer runs
    # ALONG the stroke, 77.6 deg, and the inner runs ACROSS it, 16.9 deg, so the swash opens
    # out of the cut as a mouth rather than carrying on as a stroke.
    #
    # That is fixed by constraining the inner edge's departure TANGENT, never its position.
    # Placing it -- running it parallel to the outer edge, offset by the cut, over the head
    # -- does make the pair parallel, and it overrides the width while it does so: the cut
    # is 9.98 units long where the ribbon just past it is meant to be 4.6, so the stroke is
    # held open at the cut's width and then has to collapse back, leaving a waist of 4.17
    # where the profile asks for 5.12.  The artwork swells smoothly from 3.47 to 5.93 and
    # never reverses; that waist is the one thing in the whole head that does.
    t_out, t_in = aV[3] - aV[2], aV[4] - aV[5]
    keep = False                       # the artwork's knots only suit the artwork's path
    (so, eo), (si, ei) = (_fit_edge(outer, EDGE_OUTER, t_out / abs(t_out), keep),
                          _fit_edge(inner, EDGE_INNER, None, keep))
    _write_chain(items, EDGE_OUTER, outer[0], so)
    _write_chain(items, EDGE_INNER, inner[0], si)
    _warp_cap(items, HEAD_CAP, oV3, oV4, nV3, nV4)
    _warp_cap(items, TAIL_CAP, of0, of1, nf0, nf1)
    rotated = _departure_error(items, a_verts)

    gaps = [(i, abs(_C(items[i][-1]) - _C(items[(i + 1) % len(items)][1])))
            for i in range(len(items))
            if abs(_C(items[i][-1]) - _C(items[(i + 1) % len(items)][1])) > 1e-9]
    r = _width_ratio(before, items)
    curv = (_curvature(items, EDGE_OUTER), _curvature(items, EDGE_INNER))
    report = dict(head_cut=(abs(oV4 - oV3), abs(nV4 - nV3)),
                  tail_face=(abs(of1 - of0), abs(nf1 - nf0)),
                  gain=GAIN, k_head=k_head, reach=reach, residual=residual, curv=curv, fit_err=(eo, ei), ratio=r,
                  departures_rotated_deg=rotated, gaps=gaps)
    return items, report


if __name__ == '__main__':
    it, r = derived_swash_items()
    print('  head cut  %.4f -> %.4f mark units  (x%.4f, absorbed by the cut going oblique)'
          % (r['head_cut'][0], r['head_cut'][1], r['head_cut'][1] / r['head_cut'][0]))
    print('  tail face %.4f -> %.4f  (x%.4f)'
          % (r['tail_face'][0], r['tail_face'][1], r['tail_face'][1] / r['tail_face'][0]))
    print('  width x%.4f asked for; body delivered %.3f / %.3f / %.3f  (p10/p50/p90)'
          % ((r['gain'],) + r['ratio']))
    print("  head gain x%.4f (the cut's own growth) spent by %d%% of the trail;"
          ' the anchors need %.4f units of forcing' % (r['k_head'], round(r['reach'] * 100),
                                                       r['residual']))
    print('  straight out of the leg for %g%% of the trail, back on its path by %g%%'
          % (HOLD[0] * 100, HOLD[1] * 100))
    print('  refit worst %.4f (outer) / %.4f (inner) mark units' % r['fit_err'])
    print('  edges leave the foot off parallel with the leg by %s deg'
          % ', '.join('%.2f' % v for v in r['departures_rotated_deg']))
    (ro, jo), (ri, ji) = r['curv']
    print('  tightest radius %.3f (outer) / %.3f (inner) mark units; worst curvature jump'
          ' across a knot %.0f:1 / %.0f:1' % (ro, ri, jo, ji))
    print('  %d items, %d continuity gaps' % (len(it), len(r['gaps'])))
