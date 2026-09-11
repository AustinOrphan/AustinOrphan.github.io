"""The swash, re-derived for the mark the typeface draws.

The swash is construction, not ink: it is the gesture the write-on pen follows, and
design/logo-animation/derive_trail.py reads its two long edges to get a centre-line and a
width profile.  It is NOT a free curve -- the artwork authors it to span exactly cut to
cut, and both of those cuts have moved:

    head   items 4+5 run from the A's V[3] to its V[4], i.e. along the right foot's cut.
           R2c widened that cut from 6.2441 to 9.9763 mark units.
    tail   item 11 runs along the hoop's hook face, item 7 of the bar.  R1b thickened the
           band, so the face grew from 3.3483 to 4.1037.

Leaving the swash alone therefore does not "keep the artwork's gesture", it breaks the one
thing the artwork actually pinned: the pen started as wide as the foot it starts on, and
ended as wide as the face it hands off to.  Against the re-derived mark the old swash is
37% too narrow at the foot and its head sits 268 path units off the foot it claims to
leave from.

The re-derivation is fixed by those two cuts and has no free parameter:

    caps        the similarity that carries the old cut onto the new one, so the cap lands
                on the new cut exactly and keeps whatever bow the artwork drew into it
    long edges  a uniform scale by k(u) about the artwork's own centre-line, then a shift
                by d(u), with u each point's arc fraction from head to tail

Each cap's similarity IS a scale about its own midpoint plus a shift, so taking k and d
to the cap values at u=0 and u=1 makes the long edges agree with the caps exactly.  k is
carried as the complex ratio, not its magnitude: the cuts very nearly hold their angle
(-25.0 deg at the foot, 114.3 at the hook face) but not exactly, and dropping the 0.012
deg they do turn leaves the edges 0.001 units off the caps at all four junctions.  With
it the junctions close and the topology, 15 items in the source's order, which
derive_trail indexes by position, is untouched.

k is scaled about the CENTRE-LINE rather than each edge being displaced on its own.
Displacing the edges is exact at both ends too, but it adds a near-constant vector to a
width vector that rotates through the loop, so wherever the loop has turned away from the
cut the two partly cancel: it took the widest part of the trail from 1303 to 1150 path
units while every other part of the mark grew.  Scaling cannot do that -- the width is
multiplied by k(u) whatever direction it points.

The widening is not chosen anywhere: k(0) and k(1) are the two cuts' own growth, 1.5978
and 1.2258.  What IS a decision is how far the head's share of that reaches, and taking
it linearly to the tail is wrong: the foot cut grew by 1.5978 because R2c flares the
stroke AT THE BASELINE and tapers it away over the letter's height, so it is a local
fact about the foot, not a weight the whole gesture shares.  Carried the full length it
scales the loop -- already the widest thing in the mark at 1303 path units, wider than
the A's own stem -- to 1947, and the sweep reads as a blob rather than a swash.

So the head's share is released over the first 5% of the trail and the body sits at
k_tail, the ring's gain, which is what the rest of the mark gained.  5% is derive_trail's
own number: it is how far it holds the trail on the swash's authored edges before
building its own head, so past it the cut has stopped being what the trail follows.

The release has to be that short because of where the loop is.  The pen leaves the foot
and curls immediately, so the loop occupies roughly u 0.1 to 0.35 -- releasing over
derive_trail's full hold-to-release window, (0.05, 0.32), swallows the whole loop and
lands within 15 path units of the linear profile.  Against the artwork the loop is the
tell: it is a tapered ribbon around an open counter, and at 1.5 it fills in to a slab
with the counter all but closed.  At the ring's gain the counter stays open.  That is
also where derive_trail's own guard sits -- past about 1.3 the loop is wide enough that
the mask's lead-in sweeps over outline points belonging elsewhere on the trail and the
derivation refuses to write.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'measure'))

SRC_PATH = os.path.join(HERE, 'source', 'ai_objects.json')

HEAD_CAP = (4, 5)       # the A's right foot cut, V[3] -> V[4]
TAIL_CAP = (11,)        # the hoop's hook face, bar item 7
# each long edge walked HEAD -> TAIL, as (item index, walked backwards?)
EDGE_INNER = [(6, False), (7, False), (8, False), (9, False), (10, False)]
EDGE_OUTER = [(3, True), (2, True), (1, True), (0, True), (14, True), (13, True), (12, True)]

# how much of the trail the foot cut's extra width is spent over: full at the cut, gone by
# 5%, which is as far as derive_trail holds the trail on the swash's own authored edges
HEAD_REACH = tuple(float(v) for v in os.environ.get('ORPHAN_SWASH_REACH', '0.0,0.05').split(','))
PROFILE = os.environ.get('ORPHAN_SWASH_PROFILE', 'ramp')      # 'ramp' | 'linear'


def _head_share(u):
    """How much of the head's correction still applies at arc fraction u."""
    if PROFILE == 'linear':
        return 1.0 - u
    a, b = HEAD_REACH
    if u <= a:
        return 1.0
    if u >= b:
        return 0.0
    return 0.5 * (1.0 + math.cos(math.pi * (u - a) / (b - a)))


def _C(p):
    return complex(p[0], p[1])


def _seg_pts(it, n=96):
    P = [_C(q) for q in it[1:]]
    if it[0] == 'l':
        return [P[0] * (1 - t) + P[1] * t for t in (i / (n - 1.) for i in range(n))]
    return [(1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t * t * P[2]
            + t ** 3 * P[3] for t in (i / (n - 1.) for i in range(n))]


def _arclen(it):
    p = _seg_pts(it)
    return sum(abs(p[i + 1] - p[i]) for i in range(len(p) - 1))


def _similarity(a, b, A, B):
    """The similarity carrying the segment a->b onto A->B."""
    k = (B - A) / (b - a)
    return lambda z: A + k * (z - a)


def _warp_cap(items, idxs, old_a, old_b, new_a, new_b):
    f = _similarity(old_a, old_b, new_a, new_b)
    for k in idxs:
        items[k] = [items[k][0]] + [[f(_C(p)).real, f(_C(p)).imag] for p in items[k][1:]]


def _edge_u(items, walk):
    """Each item's (u at forward control point 0, u at forward control point 3)."""
    lens = [_arclen(items[k]) for k, _ in walk]
    total, acc, out = sum(lens), 0.0, {}
    for (k, rev), L in zip(walk, lens):
        u0, u1 = acc / total, (acc + L) / total
        acc += L
        out[k] = (u1, u0) if rev else (u0, u1)
    return out


def _edge_samples(items, walk, n=1200):
    """The edge resampled head -> tail at n points evenly spaced in arc length."""
    pts = []
    for k, rev in walk:
        p = _seg_pts(items[k])
        pts += (p[::-1] if rev else p)[(1 if pts else 0):]
    d = [0.0]
    for i in range(len(pts) - 1):
        d.append(d[-1] + abs(pts[i + 1] - pts[i]))
    total, out, j = d[-1], [], 0
    for i in range(n):
        target = total * i / (n - 1.)
        while j < len(d) - 2 and d[j + 1] < target:
            j += 1
        span = d[j + 1] - d[j]
        f = 0.0 if span <= 0 else (target - d[j]) / span
        out.append(pts[j] * (1 - f) + pts[j + 1] * f)
    return out


def _warp_edges(items, edges, centre, k_head, k_tail, d_head, d_tail):
    """Scale by k(u) about the artwork's centre-line, then shift by d(u)."""
    n = len(centre)
    for walk in edges:
        for k, (ua, ub) in _edge_u(items, walk).items():
            m = len(items[k]) - 1
            pts = []
            for i, p in enumerate(items[k][1:]):
                u = ua + (ub - ua) * (i / (m - 1.))
                c = centre[min(n - 1, max(0, int(round(u * (n - 1)))))]
                h = _head_share(u)
                kk = k_head * h + k_tail * (1 - h)
                z = c + kk * (_C(p) - c) + d_head * h + d_tail * (1 - h)
                pts.append([z.real, z.imag])
            items[k] = [items[k][0]] + pts


def derived_swash_items(a_verts=None, hoop_items=None):
    """The artwork's swash carried onto the re-derived mark's two cuts.

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

    # The four points the swash is pinned to, before and after.  The BEFORE anchors are
    # taken from the swash's own copies of them, not from the A's vertices and the bar's
    # item 7: the source rounds each object's coordinates independently, so those agree
    # only to about 5e-4, and anchoring the caps to one copy while the long edges carry
    # the other reopens that difference as a gap at all four junctions.
    nV3, nV4 = _C(a_verts[3]), _C(a_verts[4])
    nf0, nf1 = _C(hoop_items[7][1]), _C(hoop_items[7][-1])
    oV3, oV4 = _C(items[HEAD_CAP[0]][1]), _C(items[HEAD_CAP[-1]][-1])
    of0, of1 = _C(items[TAIL_CAP[0]][1]), _C(items[TAIL_CAP[-1]][-1])

    k_head, k_tail = (nV4 - nV3) / (oV4 - oV3), (nf1 - nf0) / (of1 - of0)
    d_head, d_tail = (nV3 + nV4) / 2 - (oV3 + oV4) / 2, (nf0 + nf1) / 2 - (of0 + of1) / 2

    # the artwork's own centre-line, the axis the width is scaled about.  Both edges are
    # resampled head -> tail in arc fraction, which is the same pairing derive_trail uses
    # to read a width profile back off the result.
    inner = _edge_samples(items, EDGE_INNER)
    outer = _edge_samples(items, EDGE_OUTER)
    centre = [(a + b) / 2 for a, b in zip(inner, outer)]

    _warp_edges(items, (EDGE_INNER, EDGE_OUTER), centre, k_head, k_tail, d_head, d_tail)
    _warp_cap(items, HEAD_CAP, oV3, oV4, nV3, nV4)
    _warp_cap(items, TAIL_CAP, of0, of1, nf0, nf1)

    gaps = []
    for i in range(len(items)):
        a = _C(items[i][-1]); b = _C(items[(i + 1) % len(items)][1])
        if abs(a - b) > 1e-9:
            gaps.append((i, abs(a - b)))
    report = dict(
        head_cut=(abs(oV4 - oV3), abs(nV4 - nV3)),
        tail_face=(abs(of1 - of0), abs(nf1 - nf0)),
        k=(abs(k_head), abs(k_tail)), gaps=gaps)
    return items, report


if __name__ == '__main__':
    it, r = derived_swash_items()
    print('  head cut  %.4f -> %.4f mark units  (x%.4f)'
          % (r['head_cut'][0], r['head_cut'][1], r['head_cut'][1] / r['head_cut'][0]))
    print('  tail face %.4f -> %.4f mark units  (x%.4f)'
          % (r['tail_face'][0], r['tail_face'][1], r['tail_face'][1] / r['tail_face'][0]))
    print('  %d items, %d continuity gaps' % (len(it), len(r['gaps'])))
    for i, g in r['gaps']:
        print('    gap after item %d: %.6f' % (i, g))
