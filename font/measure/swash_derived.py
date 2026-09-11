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
# How long the stroke may run STRAIGHT out of the leg before it starts to turn, and where
# it is back on the artwork's path, as fractions of the trail.  Off by default: running it
# straight for a cut-length and easing back over the two after reads as a longer, fuller
# stroke in outline, but it is bought by bending the hook, and the hook will not take it --
# the inner edge stops being fittable (2.32 mark units against 0.25) and derive_trail's own
# mask guard rejects the result.
HOLD = tuple(float(v) for v in os.environ.get('ORPHAN_SWASH_HOLD', '0,0').split(','))
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


def _fit_edge(pts, walk, head_tangent=None, n=WALK_N):
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
        `release`.

        Blended by POSITION, not by direction.  Rotating each tangent and re-integrating
        holds the direction correctly but every later point inherits the correction, so the
        tail walks off the hoop -- 13 to 45 mark units of it, depending how long the hold
        is.  Blending toward a straight ray and back again keeps the change local: past
        `release` the path is the artwork's, to the unit.
        """
        if release <= hold:
            return mid
        u = _arcfrac(mid)
        d = np.r_[0.0, np.cumsum(np.abs(np.diff(mid)))]
        w = np.clip((release - u) / (release - hold), 0.0, 1.0)
        w = 0.5 * (1 - np.cos(np.pi * w))
        return mid + w * (mid[0] + axis * d - mid)

    e1, e2 = aV[3] - aV[2], aV[4] - aV[5]
    axis = e1 / abs(e1) + e2 / abs(e2)
    axis = axis / abs(axis)

    def place(edge, h, head, tail):
        u = _arcfrac(edge)
        g = GAIN + (k_head - GAIN) * 0.5 * (1 + np.cos(np.pi * np.minimum(1.0, u / reach)))
        mid = straighten(edge + h, HOLD[0], HOLD[1])
        p = mid - g * h + d_head * (1 - u) + d_tail * u
        a = 0.5 * (1 + np.cos(np.pi * np.minimum(1.0, u / END_BLEND)))
        b = 0.5 * (1 + np.cos(np.pi * np.minimum(1.0, (1 - u) / END_BLEND)))
        return p + (head - p[0]) * a + (tail - p[-1]) * b, abs(head - p[0]), abs(tail - p[-1])

    outer, r0, r1 = place(outer, h_out, nV3, nf1)
    inner, r2, r3 = place(inner, h_in, nV4, nf0)
    residual = max(r0, r1, r2, r3)

    # Leaving the foot, the two edges disagree about what they are doing: the outer runs
    # ALONG the stroke, 77.6 deg, and the inner runs ACROSS it, 16.9 deg, so the swash opens
    # out of the cut as a mouth rather than carrying on as a stroke.  On the artwork that is
    # a small wedge; against the A's 60% wider foot it is a long spike of leg with the hook
    # hung off the side of it.
    #
    # So over the head the inner edge is the OUTER edge offset by the cut, which is the one
    # thing that makes the pair parallel, and it blends back to its own shape by PATH_REACH.
    # The midline is already right -- the artwork leaves the foot within 0.2 deg of the
    # leg's axis -- so the stroke now runs out of the leg parallel-sided and then turns,
    # rather than turning the moment it leaves.
    # Over the same one cut-length as the flare and the straight run.  ONE length governs
    # the whole head: the foot is one cut-length wide, so for one cut-length of travel the
    # stroke is still leaving the foot -- it runs straight, it stays parallel-sided, and it
    # carries the foot's extra width -- and then it turns, easing onto the artwork's own
    # path over the two cut-lengths after that.  Holding the edges parallel much further
    # closes the hook's mouth on itself; by a third of the trail the outline self-intersects.
    ui = _arcfrac(inner)
    w = 0.5 * (1 + np.cos(np.pi * np.minimum(1.0, ui / (PATH_REACH or reach))))
    inner = inner + w * (_at(outer, ui) + (nV4 - nV3) - inner)

    # The OUTER edge leaves the foot cut running along the leg edge it meets, so the leg
    # runs on into the hook rather than the hook being stuck onto it.  The artwork is 1.04
    # deg off parallel there, near enough that it already reads as a continuation, and the
    # 1 deg is given up so the rule is exact and follows the leg: R2c's flare turns that
    # edge 2.3 deg and the swash turns with it.
    #
    # The INNER edge is left to follow the rebuilt geometry.  It has no anchor in the leg
    # to inherit: V[4] is the MOUTH of the hook, where the ribbon opens away from the leg
    # rather than running on down it.  Forcing it parallel to the leg's other edge makes
    # its first piece leave steeply downhill and double back to a knot that is up and to
    # the right -- a hairpin inside one short segment, curvature peaking at 78 against the
    # artwork's 0.77.  Imposing the ARTWORK's own angle there is not much better: the
    # wider foot has swung that piece's chord 20 deg, so the old angle no longer suits it
    # and the fit answers by collapsing both handles to about an eighth of the chord,
    # which is a straight line with a corner at each end.
    #
    # It goes in as a tangent CONSTRAINT on the fit.  Fitting first and rotating the handle
    # afterwards puts the angle right and the curve wrong: the piece has to reach the same
    # far knot from a direction it was not fitted for, and it arrives stalled -- sample steps
    # of 0.010 against a median of 0.111, curvature peaking at 104 where the artwork peaks at
    # 0.77.  That is a cusp a hundredth of a unit across sitting in the first knot of the
    # hook, which is exactly the kind of bulge this is meant to remove.
    t_out = aV[3] - aV[2]
    (so, eo), (si, ei) = (_fit_edge(outer, EDGE_OUTER, t_out / abs(t_out)),
                          _fit_edge(inner, EDGE_INNER))
    _write_chain(items, EDGE_OUTER, outer[0], so)
    _write_chain(items, EDGE_INNER, inner[0], si)
    _warp_cap(items, HEAD_CAP, oV3, oV4, nV3, nV4)
    _warp_cap(items, TAIL_CAP, of0, of1, nf0, nf1)
    rotated = _departure_error(items, a_verts)

    gaps = [(i, abs(_C(items[i][-1]) - _C(items[(i + 1) % len(items)][1])))
            for i in range(len(items))
            if abs(_C(items[i][-1]) - _C(items[(i + 1) % len(items)][1])) > 1e-9]
    r = _width_ratio(before, items)
    report = dict(head_cut=(abs(oV4 - oV3), abs(nV4 - nV3)),
                  tail_face=(abs(of1 - of0), abs(nf1 - nf0)),
                  gain=GAIN, k_head=k_head, reach=reach, residual=residual, fit_err=(eo, ei), ratio=r,
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
    print('  refit worst %.4f (outer) / %.4f (inner) mark units' % r['fit_err'])
    print('  edges leave the foot off parallel with the leg by %s deg'
          % ', '.join('%.2f' % v for v in r['departures_rotated_deg']))
    print('  %d items, %d continuity gaps' % (len(it), len(r['gaps'])))
