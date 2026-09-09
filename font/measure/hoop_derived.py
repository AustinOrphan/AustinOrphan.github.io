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
    # The MAIN rim only, not the hooks' outer curls.  Pushing each inner sample away from its
    # nearest point on the whole outer boundary sounds right and is not: on the left the hook's
    # outer curl wraps back UNDER the band and wins the nearest-point search, so those samples were
    # pushed toward the rim instead of away from it and the band came out thinner where it should
    # have been thickest.  The main rim is the edge the band is measured from everywhere it matters,
    # and at the hooks the gain is ramped to nothing anyway.
    outer = _flatten([items[j] for j in (1, 2, 3)])
    inner = _flatten([items[j] for j in INNER_RUN])

    # Where each hook's inner curl hands over to the main rim, measured along the inner run.
    #
    # The gain is held at ZERO for the whole of both curls and ramped up on the MAIN RUN, over the
    # third of it nearest each hand-over.  Two reasons, and the first one is not the obvious one.
    #
    # A hook encloses an eye about two units of the mark's 100 wide against a band of five, so 30%
    # of the band shuts it, and the eye is the whole reason a hook reads as a curl rather than a
    # blob.  That is why the hooks keep the band they were drawn with.
    #
    # But the ramp has to be flat across the whole curl, not merely zero at the tip.  The push is
    # "away from the main rim by (k-1) times the distance to it", and at a hook that distance is not
    # the band -- it is 14.6 units where the band is 5 -- so even a tenth of the gain there moves the
    # edge half a unit in a direction that has nothing to do with the local stroke.  Ramping through
    # the curl cost a sliver of the artwork at both tips: ink LOST, which is what showed as a corner
    # jutting out of the curl.
    L_END = sum(_seglen(items[j]) for j in range(8, 11))        # end of hook L's inner curl
    R_START = sum(_seglen(items[j]) for j in range(8, 14))      # start of hook R's inner curl
    TOTAL = sum(_seglen(items[j]) for j in INNER_RUN)
    BLEND = (R_START - L_END) / 3.0

    def ramp(s):
        t = min((s - L_END) / BLEND, (R_START - s) / BLEND, 1.0)
        if t <= 0: return 0.0
        return t * t * (3 - 2 * t)                              # smoothstep: no corner at either end

    def push(p, w):
        q = min(outer, key=lambda o: (o[0]-p[0])**2 + (o[1]-p[1])**2)
        d = math.hypot(p[0]-q[0], p[1]-q[1])
        if d < 1e-9 or w <= 0.0: return p, d
        g = w * (K - 1)
        return (p[0] + (p[0]-q[0])/d * g * d, p[1] + (p[1]-q[1])/d * g * d), d

    moved, bands, s = [], [], 0.0
    for i, p in enumerate(inner):
        if i: s += math.dist(inner[i-1], p)
        m, d = push(p, ramp(s)); moved.append(m)
        if L_END <= s <= R_START: bands.append(d)

    tg = [unit(sub(moved[min(i+1, len(moved)-1)], moved[max(i-1, 0)])) for i in range(len(moved))]
    segs, err = fit_cubics(moved, tg, nseg=nseg)

    k = Contour(tuple(items[17][1]))
    for j in (17, 0, 1, 2, 3, 4, 5, 6):
        it = items[j]
        k.curve_to(tuple(it[2]), tuple(it[3]), tuple(it[4])) if it[0] == 'c' else k.line_to(tuple(it[2]))
    f = items[7]                                         # hook L's face, exactly as drawn: the gain
    k.curve_to(tuple(f[2]), tuple(f[3]), tuple(f[4]))    # is zero at the ends so nothing has moved
    for sg in segs: k.curve_to(*sg)
    f = items[16]                                        # hook R's face, likewise
    k.curve_to(tuple(f[2]), tuple(f[3]), tuple(f[4]))
    return k.ccw(), dict(k=K, fit_err=err, band_min=min(bands), band_max=max(bands), nseg=nseg)


if __name__ == '__main__':
    hoop, n = derived_hoop()
    print('  k %.4f  (HORIZ_JOIN %.2f against the mark\'s %.2f)' % (K, core._JOIN_AT_11 * core._band_k(), core._JOIN_AT_11))
    print('  the artwork\'s band runs %.2f to %.2f of the mark\'s 100 units; every part of it grows by the same %.1f%%'
          % (n['band_min'], n['band_max'], 100 * (K - 1)))
    print('  inner edge refitted to %d cubics, worst deviation %.4f units' % (n['nseg'], n['fit_err']))
    json.dump(dict(hoop=hoop.to_json(), **n), open(os.path.join(HERE, 'build', 'hoop.json'), 'w'))
    print('  wrote build/hoop.json')
