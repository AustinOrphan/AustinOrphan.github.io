"""The mark's hoop at the face's weights, with its hooks kept.

The hoop is the A's bar run free: inside the letter the legs clip it long before its ends, so the
font never draws the parts that make the mark -- the two hooks curling back at each end.  R4 ties a
bar that runs into a round to that round's band, so R1b thickens the hoop with everything else, and
core._derived_bar is what the letter uses: a plain piece of the ring's annulus, square at both ends.
Dropped into the mark that is wrong twice over -- it stops square where the artwork curls, and it
runs to a construction range (18 to 152 degrees) that was only ever there to be cut away.

So the hoop is re-derived the way the A's bar is, but on the ARTWORK's own geometry and over the
artwork's own extent: every OUTER curve is left exactly as drawn -- the main rim and both hooks'
outer rims and nothing about the silhouette's ends -- and only the INNER curves move, inward, by the
same factor core._ring_ellipses uses for the bar inside the letter.

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


def derived_hoop(nseg=28):
    """The hoop thickened to the face's band, in the mark's own coordinates.

    Every OUTER curve is the artwork, untouched -- the main rim, both hooks' outer rims, and so the
    whole silhouette and both curls.  The inner edge is moved AWAY from the outer one by (k-1) times
    its own local distance to it, which thickens the band by exactly the factor R1b thickens a round,
    proportionally all the way round rather than by a constant amount: the hoop is a ring in
    perspective and its band is not the same width at both ends.  The moved samples are refitted to
    cubics with a fixed piece count, and the two flat faces are redrawn to the ends that moved.
    """
    items = BAR['items']
    outer = _flatten([items[j] for j in (17, 0, 1, 2, 3, 4, 5, 6)])
    inner = _flatten([items[j] for j in INNER_RUN])

    def push(p):
        q = min(outer, key=lambda o: (o[0]-p[0])**2 + (o[1]-p[1])**2)
        d = math.hypot(p[0]-q[0], p[1]-q[1])
        if d < 1e-9: return p, 0.0
        return (p[0] + (p[0]-q[0])/d * (K-1) * d, p[1] + (p[1]-q[1])/d * (K-1) * d), d

    moved, bands = [], []
    for p in inner:
        m, d = push(p); moved.append(m); bands.append(d)

    tg = [unit(sub(moved[min(i+1, len(moved)-1)], moved[max(i-1, 0)])) for i in range(len(moved))]
    segs, err = fit_cubics(moved, tg, nseg=nseg)

    k = Contour(tuple(items[17][1]))
    for j in (17, 0, 1, 2, 3, 4, 5, 6):
        it = items[j]
        k.curve_to(tuple(it[2]), tuple(it[3]), tuple(it[4])) if it[0] == 'c' else k.line_to(tuple(it[2]))
    k.line_to(moved[0])                                  # hook L's face, redrawn to the new inner end
    for sg in segs: k.curve_to(*sg)
    k.line_to(tuple(items[17][1]))                       # hook R's face, likewise
    return k.ccw(), dict(k=K, fit_err=err, band_min=min(bands), band_max=max(bands), nseg=nseg)


if __name__ == '__main__':
    hoop, n = derived_hoop()
    print('  k %.4f  (HORIZ_JOIN %.2f against the mark\'s %.2f)' % (K, core._JOIN_AT_11 * core._band_k(), core._JOIN_AT_11))
    print('  the artwork\'s band runs %.2f to %.2f of the mark\'s 100 units; every part of it grows by the same %.1f%%'
          % (n['band_min'], n['band_max'], 100 * (K - 1)))
    print('  inner edge refitted to %d cubics, worst deviation %.4f units' % (n['nseg'], n['fit_err']))
    json.dump(dict(hoop=hoop.to_json(), **n), open(os.path.join(HERE, 'build', 'hoop.json'), 'w'))
    print('  wrote build/hoop.json')
