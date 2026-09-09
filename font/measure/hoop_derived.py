"""The mark's hoop at the face's weights, with its hooks kept.

The hoop is the A's bar run free: inside the letter the legs clip it long before its ends, so the
font never draws the parts that make the mark -- the two hooks curling back at each end.  R4 ties a
bar that runs into a round to that round's band, so R1b thickens the hoop with everything else, and
core._derived_bar is what the letter uses: a plain piece of the ring's annulus, square at both ends.
Dropped into the mark that is wrong twice over -- it stops square where the artwork curls, and it
runs to a construction range (18 to 152 degrees) that was only ever there to be cut away.

So the hoop is re-derived on the ARTWORK's own geometry and over the artwork's own extent, by the
same factor R4 gives a bar that runs into a round.

    band' = band * k,    k = HORIZ_JOIN / HORIZ_JOIN_at_the_mark

The inner edge is one unbroken run of eight segments in the traced path, so it can be thickened as a
single curve and nothing has to be stitched: each of its samples is pushed away from its nearest
point on the outer edge by (k-1) times that distance, which grows every part of the band by the same
proportion rather than by a constant amount -- the hoop is a ring in perspective and its band runs
from 2.24 to 6.14 units of the mark's 100.

Writes build/hoop.json and measure/evidence/hoop-derived.svg.
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
from pen import Contour, source_contours, bbox, fit_cubics, unit, sub
import glyphs.core as core

SRC = json.load(open(os.path.join(HERE, 'source', 'ai_objects.json')))['AO'][0]
BAR = next(o for o in SRC['objects'] if o['role'] == 'bar')
RG, HK = BAR['ring'], BAR['hooks']

# The factor is R4's join weight against the mark's own: HORIZ_JOIN / 47.2255.  NOT core's
# _BAR_CAL as well -- that constant calibrates the A's bar against the ring's ANNULUS, a different
# construction, and applying it here would shrink the hoop by 2.7% at the mark's own numbers.  The
# reference for the hoop is the artwork, so at ORPHAN_FOOT=0 this must be exactly 1 and the hoop
# must come back byte for byte.  It does.
K = core._band_k()

# The traced hoop runs: hook R outer (17, 0), the main rim (1..3), hook L outer (4..6), hook L's
# flat face (7), then EIGHT segments of inner edge in one unbroken run (8..15) -- hook L's inner
# curl, the main inner rim, hook R's inner curl -- and hook R's face (16).  That the inner edge is
# contiguous is what makes this simple: thicken it as ONE curve and nothing has to be stitched.
FACE = {h['face_seg'] for h in HK.values()}          # 7 and 16
INNER_RUN = list(range(8, 16))


def _seglen(it, n=24):
    """Arc length of one traced segment, for placing the ramp at the hooks' own hand-overs."""
    if it[0] == 'l': return math.dist(tuple(it[1]), tuple(it[2]))
    p0, c1, c2, p1 = (tuple(it[1]), tuple(it[2]), tuple(it[3]), tuple(it[4]))
    L, prev = 0.0, p0
    for t in range(1, n + 1):
        u = t / n; m = 1 - u
        q = (m**3*p0[0] + 3*m*m*u*c1[0] + 3*m*u*u*c2[0] + u**3*p1[0],
             m**3*p0[1] + 3*m*m*u*c1[1] + 3*m*u*u*c2[1] + u**3*p1[1])
        L += math.dist(prev, q); prev = q
    return L


def _flatten(items, per=0.25):
    """The inner run as a dense polyline, and the outer boundary as another."""
    out = []
    for it in items:
        p0 = tuple(it[1])
        if it[0] == 'l':
            p1 = tuple(it[2]); n = max(2, int(math.dist(p0, p1) / per))
            out += [(p0[0] + (p1[0]-p0[0])*t/n, p0[1] + (p1[1]-p0[1])*t/n) for t in range(n)]
        else:
            c1, c2, p1 = (tuple(it[2]), tuple(it[3]), tuple(it[4]))
            L = math.dist(p0, c1) + math.dist(c1, c2) + math.dist(c2, p1)
            n = max(3, int(L / per))
            for t in range(n):
                u = t / n; m = 1 - u
                out.append((m**3*p0[0] + 3*m*m*u*c1[0] + 3*m*u*u*c2[0] + u**3*p1[0],
                            m**3*p0[1] + 3*m*m*u*c1[1] + 3*m*u*u*c2[1] + u**3*p1[1]))
    out.append(tuple(items[-1][-1]))
    return out


def derived_hoop(nseg=34):
    """The hoop thickened to the face's band, in the mark's own coordinates.

    The INNER edge is the artwork, untouched, and the OUTER edge moves outward.  That is the wrong
    way round at first glance -- the letter's bar thickens inward -- and it is the only way that
    works here, because of the eyes.

    Each hook curls back and encloses an eye about two units of the mark's 100 across.  The eye is
    bounded on one side by the hook's inner curl and on the other by the main band's inner edge, so
    ANY inward thickening walks straight into it: the gain is 1.85 units against an eye of 2.  The
    first attempt shut both eyes.  Ramping the gain to nothing across each hook kept them open but
    left the hoop 30% heavier in the middle and its drawn weight at the ends -- a bulge, which is
    not a weight change, it is a lump.

    Moving the outer edge instead thickens the band by the same 30% EVERYWHERE, uniformly, with no
    ramp and nothing to blend: the eyes are not on that side of the stroke.  What it costs is the
    outer silhouette, which grows by the gain -- the hoop's rim and both curls stand a little
    further out.  That is what a thicker ribbon does, and it is the side of the mark with room.

    Each outer sample is pushed away from its own region's inner edge -- the main rim against the
    main inner edge, each hook's outer curl against its own inner curl -- by (k-1) times the distance
    to it, so the band grows by the same proportion everywhere rather than by a constant amount.  The
    hoop is a ring in perspective and its band runs 4.7 to 6.1 units of the mark's 100.
    """
    items = BAR['items']
    OUT_RUN = [17, 0, 1, 2, 3, 4, 5, 6]
    REF = {17: (14, 15), 0: (14, 15),                      # hook R's outer against hook R's inner
           1: (11, 13), 2: (11, 13), 3: (11, 13),          # the main rim against the main inner edge
           4: (8, 10), 5: (8, 10), 6: (8, 10)}             # hook L's outer against hook L's inner
    ref_pts = {}
    for lo, hi in set(REF.values()):
        ref_pts[(lo, hi)] = _flatten([items[j] for j in range(lo, hi + 1)])

    moved, bands = [], []
    for j in OUT_RUN:
        pts = _flatten([items[j]])
        R = ref_pts[REF[j]]
        for p in pts:
            q = min(R, key=lambda o: (o[0]-p[0])**2 + (o[1]-p[1])**2)
            d = math.hypot(p[0]-q[0], p[1]-q[1])
            bands.append(d)
            moved.append(p if d < 1e-9 else
                         (p[0] + (p[0]-q[0])/d * (K-1) * d, p[1] + (p[1]-q[1])/d * (K-1) * d))

    tg = [unit(sub(moved[min(i+1, len(moved)-1)], moved[max(i-1, 0)])) for i in range(len(moved))]
    segs, err = fit_cubics(moved, tg, nseg=nseg)

    k = Contour(moved[0])
    for sg in segs: k.curve_to(*sg)
    k.line_to(tuple(items[8][1]))                          # hook L's face, to the inner edge as drawn
    for j in INNER_RUN:
        it = items[j]
        k.curve_to(tuple(it[2]), tuple(it[3]), tuple(it[4])) if it[0] == 'c' else k.line_to(tuple(it[2]))
    k.line_to(moved[0])                                    # hook R's face, likewise
    return k.ccw(), dict(k=K, fit_err=err, band_min=min(bands), band_max=max(bands), nseg=nseg)


if __name__ == '__main__':
    hoop, n = derived_hoop()
    print('  k %.4f  (HORIZ_JOIN %.2f against the mark\'s %.2f)' % (K, core._JOIN_AT_11 * core._band_k(), core._JOIN_AT_11))
    print('  the artwork\'s band runs %.2f to %.2f of the mark\'s 100 units; every part of it grows by the same %.1f%%'
          % (n['band_min'], n['band_max'], 100 * (K - 1)))
    print('  inner edge refitted to %d cubics, worst deviation %.4f units' % (n['nseg'], n['fit_err']))
    json.dump(dict(hoop=hoop.to_json(), **n), open(os.path.join(HERE, 'build', 'hoop.json'), 'w'))
    print('  wrote build/hoop.json')
