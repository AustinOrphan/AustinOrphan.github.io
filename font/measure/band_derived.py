"""The cut band, derived from the shipped mark.

The `cut` treatment draws the mark's outline with the letterform punched out of it, so the
glyph is a hole and the ground shows through. On a page that is a mask: stroke the mark, then
subtract the mark. In a file handed to a design tool it should be a real filled path, for the
same reason hero's outline is flattened on export -- a mask is a promise the renderer may not
keep, and this repo has been bitten by exactly that with `paint-order`.

The band is
                    buffer(mark, BAND / 2) - mark

which is the outward half of a centred stroke of width BAND. Shapely's round joins are the
same construction as `stroke-linejoin: round`, and buffering a polygon WITH holes grows the
outer boundary while shrinking each counter, which is what the rendered band does too: it
hugs the counters from the inside exactly as it hugs the silhouette from the outside.

Input is LOGO_MARK_D from src/components/logo-mark.ts, NOT the font. The band depends only on
the mark, so re-deriving it must not require the font sources; that is why this is its own
generator rather than another branch of mark_derived.py. Extract by EXPORT NAME -- there is
more than one long path in that file.

BAND is 300 path units, the same number --logo-band defaults to, chosen against two measured
bounds:

  floor    the mark's own thinnest stroke is 191 path units, and the band's visible weight is
           half the stroke, so below 382 the band is lighter than the lightest part of the
           mark it traces
  ceiling  the mark has 8 counters, the tightest with a gap of 402 path units. The band
           advances half its width from each side, so that counter seals when the stroke
           reaches ~400 -- confirmed by rasterising: 8 counters open at 380, 7 at 400

300 sits 23 % below the ceiling. 382 would make the band exactly the mark's thinnest stroke,
which is prettier and 2 % from failure; mark_derived.py can re-derive the mark, and a small
shift in one counter would close it.

Writes build/band.json. Paste site_path into logo-mark.ts as LOGO_BAND_D, and keep `band` in
step with the --logo-band default in global.css -- scripts/check-derived.mjs asserts both.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'lib'))
sys.path.insert(0, os.path.join(HERE, 'measure'))
from pen import fit_cubics, norm, sub, unit            # noqa: E402
from shapely.geometry import Polygon                   # noqa: E402
from shapely.ops import unary_union                    # noqa: E402

REPO = os.path.dirname(HERE)
MARK_TS = os.path.join(REPO, 'src', 'components', 'logo-mark.ts')

BAND = 300.0        # path units of stroke; the visible band is half of it
PER = 6.0           # flattening step in path units (the mark is ~12460 wide)
QUAD_SEGS = 64      # segments per quarter turn in the buffer, before the cubic fit
CORNER_DEG = 12.0   # mark_derived's value: a sharper turn is a real corner, fitted separately
FIT_TOL = 0.5       # path units; mark_derived's 0.004 mark units is about this once scaled


def read_mark(name='LOGO_MARK_D'):
    """The shipped path, by export name."""
    src = open(MARK_TS).read()
    m = re.search(r"export const %s\s*=\s*\n?\s*'([^']+)'" % name, src)
    if not m:
        raise SystemExit('%s not found in %s' % (name, MARK_TS))
    return m.group(1)


def flatten(d, per=PER):
    """SVG path data to a list of closed polygons. Only M/L/C/Z appear in the mark."""
    toks = re.findall(r'[MLCZ]|-?\d+(?:\.\d+)?', d)
    rings, cur, pos, start = [], [], (0.0, 0.0), (0.0, 0.0)
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == 'M':
            if len(cur) > 2:
                rings.append(cur)
            pos = start = (float(toks[i + 1]), float(toks[i + 2]))
            cur = [pos]
            i += 3
        elif t == 'L':
            pos = (float(toks[i + 1]), float(toks[i + 2]))
            cur.append(pos)
            i += 3
        elif t == 'C':
            p1 = (float(toks[i + 1]), float(toks[i + 2]))
            p2 = (float(toks[i + 3]), float(toks[i + 4]))
            p3 = (float(toks[i + 5]), float(toks[i + 6]))
            n = max(2, int(norm(sub(p3, pos)) / per) + 2)
            for k in range(1, n + 1):
                u = k / n
                v = 1 - u
                cur.append((v * v * v * pos[0] + 3 * v * v * u * p1[0] + 3 * v * u * u * p2[0] + u * u * u * p3[0],
                            v * v * v * pos[1] + 3 * v * v * u * p1[1] + 3 * v * u * u * p2[1] + u * u * u * p3[1]))
            pos = p3
            i += 7
        else:                       # Z
            pos = start
            i += 1
    if len(cur) > 2:
        rings.append(cur)
    return rings


def mark_polygon(d):
    """The mark as one polygon with its counters as holes.

    Nonzero fill on nested rings: a ring inside an odd number of others is a hole. The mark's
    counters are all one level deep, so containment counts are enough.
    """
    polys = [Polygon(r).buffer(0) for r in flatten(d)]
    polys = [p for p in polys if not p.is_empty]
    depth = [sum(1 for q in polys if q is not p and q.contains(p)) for p in polys]
    shells = [p for p, k in zip(polys, depth) if k % 2 == 0]
    holes = [p for p, k in zip(polys, depth) if k % 2 == 1]
    out = unary_union(shells)
    for h in holes:
        out = out.difference(h)
    return out


def to_contour(ring):
    """A dense ring back to a cubic chain, split at every real corner."""
    P = [tuple(p) for p in ring]
    if P[0] == P[-1]:
        P = P[:-1]
    n = len(P)
    T, corners = [], []
    for i in range(n):
        a = unit(sub(P[i], P[i - 1]))
        b = unit(sub(P[(i + 1) % n], P[i]))
        T.append(unit((a[0] + b[0], a[1] + b[1])))
        dot = max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1]))
        import math
        if math.degrees(math.acos(dot)) > CORNER_DEG:
            corners.append(i)
            T[i] = b
    if not corners:
        corners = [0]
    segs, worst, runs = [], 0.0, 0
    for k, s in enumerate(corners):
        e = corners[(k + 1) % len(corners)]
        idx = list(range(s, e + 1)) if e > s else list(range(s, n)) + list(range(0, e + 1))
        if len(idx) < 2:
            continue
        pts = [P[j] for j in idx]
        # A tangent per POINT, not just the two ends: fit_cubics slices P and T together as it
        # subdivides, so they have to be the same length. Same construction mark_derived uses.
        tans = [unit(sub(pts[min(i + 1, len(pts) - 1)], pts[max(i - 1, 0)])) for i in range(len(pts))]
        cs, err = fit_cubics(pts, tans, tol=FIT_TOL)
        segs.append((pts[0], cs))
        worst = max(worst, err)
        runs += len(cs)
    return segs, worst, runs


def path_d(contours):
    def r(v):
        return ('%.0f' % v) if abs(v - round(v)) < 5e-4 else ('%.1f' % v)
    out = []
    for segs in contours:
        d = []
        for j, (start, cs) in enumerate(segs):
            if j == 0:
                d.append('M%s %s' % (r(start[0]), r(start[1])))
            for c in cs:
                d.append('C%s %s %s %s %s %s' % (r(c[0][0]), r(c[0][1]), r(c[1][0]), r(c[1][1]),
                                                 r(c[2][0]), r(c[2][1])))
        d.append('Z')
        out.append(' '.join(d))
    return ' '.join(out)


def derive(band=BAND):
    mark = mark_polygon(read_mark())
    grown = mark.buffer(band / 2.0, quad_segs=QUAD_SEGS, join_style='round')
    ring = grown.difference(mark)
    geoms = list(ring.geoms) if ring.geom_type == 'MultiPolygon' else [ring]
    contours, worst, runs = [], 0.0, 0
    for g in geoms:
        for r in [g.exterior] + list(g.interiors):
            segs, e, n = to_contour(list(r.coords))
            contours.append(segs)
            worst = max(worst, e)
            runs += n
    return contours, dict(band=band, parts=len(geoms), contours=len(contours), runs=runs,
                          worst_fit=worst, area=ring.area, mark_area=mark.area,
                          mark_counters=len(mark.interiors))


if __name__ == '__main__':
    cs, info = derive()
    d = path_d(cs)
    print('  mark: %d counters' % info['mark_counters'])
    print('  band: %.0f path units of stroke, %.0f visible' % (info['band'], info['band'] / 2))
    print('  %d part(s), %d contours, %d smooth runs, worst fit %.4f path units'
          % (info['parts'], info['contours'], info['runs'], info['worst_fit']))
    print('  band area is %.1f%% of the mark' % (100.0 * info['area'] / info['mark_area']))
    print('  path %d chars' % len(d))
    out = os.path.join(HERE, 'build')
    os.makedirs(out, exist_ok=True)
    json.dump(dict(info=info, site_path=d), open(os.path.join(out, 'band.json'), 'w'))
    print('  wrote build/band.json')
