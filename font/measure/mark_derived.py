"""The mark, re-derived from the font, as ONE outline.

Logo.astro's hero variant strokes the mark with stroke-width 300 and
paint-order="stroke fill", so the red outline is drawn around the path itself.  Three stacked
shapes -- ring, hoop, A -- would each get their own outline, including along the seams where they
cross, so the mark has to reach the site as a single unioned contour set.  That is the whole reason
this file exists rather than emitting the three parts separately.

    ring   the font's O, mapped back into mark coordinates
    hoop   measure/hoop_derived, the artwork's hoop at the face's band
    A      the font's A polygon, mapped back the same way

The union is taken on dense polygons and then fitted BACK to cubics, because the union's corners are
real corners -- where the A crosses the ring there is a genuine tangent break -- and a cubic chain
fitted straight through one puts a bulge in it.  So the boundary is split at every turn sharper than
CORNER_DEG and each smooth run is fitted on its own.

Writes build/mark.json: the contours in mark coordinates and, if geometry.json is available, the
same thing in site path units ready for logo-mark.ts.
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'measure'))
from pen import Contour, add, sub, mul, unit, norm, fit_cubics
import glyphs.core as core
from hoop_derived import derived_hoop

from shapely.geometry import Polygon
from shapely.ops import unary_union

PER = 0.02          # flattening step, in mark units (the mark is 100 wide)
CORNER_DEG = 12.0   # a turn sharper than this is a corner and gets its own fit boundary
FIT_TOL = 0.004     # mark units; 0.004 is a thousandth of the A's stroke


def _inv_A():
    A = core.build_A(); n = A['notes']
    from pen import rot
    def f(p):
        q = ((p[0] - n['x_shift']) / n['scale'] + n['apex_source'][0], p[1] / n['scale'] + n['y_feet_source'])
        return add(rot(sub(q, n['apex_source']), -n['rotated_by_deg']), n['apex_source'])
    return A, f


def _inv_O():
    O = core.build_O(); n = O['notes']
    def f(p):
        return add(mul(sub(p, n['centre']), 1.0 / n['scale']), (n['source_outer'][0], n['source_outer'][1]))
    return O, f


def parts():
    """The three shapes in mark coordinates: (A polygon, ring outer, ring counter, hoop)."""
    A, invA = _inv_A()
    O, invO = _inv_O()
    a_poly = A['contours'][0].map(invA)          # contour 0 only: 1 is the bar, 2 and 3 the ring tails
    o_out, o_in = (c.map(invO) for c in O['contours'][:2])
    hoop, _ = derived_hoop()
    return a_poly, o_out, o_in, hoop


def artwork_polygon():
    """The same union taken on the ARTWORK, so the two can be compared as like for like."""
    import json as _j
    src = _j.load(open(os.path.join(HERE, 'source', 'ai_objects.json')))['AO'][0]
    obj = {o['role']: o for o in src['objects']}
    from pen import source_contours, from_poly
    ring_cs = source_contours(obj['ring']['items'])
    o_out, o_in = ring_cs[0], ring_cs[1]
    if Polygon(o_out.flatten(per=PER)).area < Polygon(o_in.flatten(per=PER)).area:
        o_out, o_in = o_in, o_out
    ring = Polygon(o_out.flatten(per=PER), [o_in.flatten(per=PER)])
    bar = unary_union([Polygon(c.flatten(per=PER)).buffer(0) for c in source_contours(obj['bar']['items'])])
    a = Polygon([tuple(v) for v in obj['A']['vertices']]).buffer(0)
    u = unary_union([ring.buffer(0), bar, a])
    if u.geom_type == 'MultiPolygon':
        u = max(u.geoms, key=lambda g: g.area)
    return u


def union_polygon():
    a_poly, o_out, o_in, hoop = parts()
    ring = Polygon(o_out.flatten(per=PER), [o_in.flatten(per=PER)])
    shapes = [Polygon(a_poly.flatten(per=PER)).buffer(0),
              ring.buffer(0),
              Polygon(hoop.flatten(per=PER)).buffer(0)]
    u = unary_union(shapes)
    if u.geom_type == 'MultiPolygon':
        u = max(u.geoms, key=lambda g: g.area)
    return u


def _corners(pts):
    """Indices where the boundary turns sharper than CORNER_DEG."""
    n = len(pts)
    out = []
    for i in range(n):
        a, b, c = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        u1, u2 = sub(b, a), sub(c, b)
        if norm(u1) < 1e-9 or norm(u2) < 1e-9: continue
        u1, u2 = unit(u1), unit(u2)
        d = math.degrees(math.acos(max(-1.0, min(1.0, u1[0]*u2[0] + u1[1]*u2[1]))))
        if d > CORNER_DEG: out.append(i)
    return out


def to_contour(ring_pts):
    """One closed ring of the union, fitted back to cubics with its corners preserved."""
    pts = list(ring_pts)
    if pts[0] == pts[-1]: pts.pop()
    cs = _corners(pts)
    if not cs:                                   # a smooth closed curve: fit as one loop
        cs = [0]
    runs = []
    for i, s in enumerate(cs):
        e = cs[(i + 1) % len(cs)]
        seq = pts[s:e + 1] if e > s else pts[s:] + pts[:e + 1]
        if len(seq) >= 2: runs.append(seq)
    k = Contour(tuple(pts[cs[0]]))
    worst = 0.0
    for seq in runs:
        tg = [unit(sub(seq[min(i+1, len(seq)-1)], seq[max(i-1, 0)])) for i in range(len(seq))]
        segs, err = fit_cubics(seq, tg, tol=FIT_TOL)
        worst = max(worst, err)
        for sg in segs: k.curve_to(*sg)
    return k, worst, len(runs)


def fit_union(u):
    """A shapely polygon back to cubic contours, corners preserved."""
    rings = [list(u.exterior.coords)] + [list(h.coords) for h in u.interiors]
    out, worst, runs = [], 0.0, 0
    for r in rings:
        c, e, n = to_contour(r)
        out.append(c); worst = max(worst, e); runs += n
    return out, dict(worst_fit=worst, runs=runs, contours=len(out),
                     area=u.area, holes=len(u.interiors))


def derive():
    return fit_union(union_polygon())


def to_site(cs, geometry_json):
    """Mark coordinates into the site's path units, using the transform geometry.json already fits
    between the Illustrator source and the shipped path.  Going through that transform rather than
    fitting a new one is what keeps the mark in the same place: every mask, viewBox and anchor in
    the animation is expressed in these units and none of them has to move.

    The check that it is the right transform: push the ARTWORK through it and the result lands on
    the shipped path's own bounding box, 10623 x 10053 against 10622 x 10053."""
    import math as _m
    T = json.load(open(geometry_json))['transform']
    s_, th = T['scale'], _m.radians(T['rotation_deg'])
    tx, ty = T['translate']['x'], T['translate']['y']
    co, si = _m.cos(th), _m.sin(th)
    def f(p):
        x, y = p
        return (s_ * (x * co - y * si) + tx, s_ * (x * si + y * co) + ty)
    return [c.map(f) for c in cs]


def path_d(cs, ndigits=0):
    """SVG path data, coordinates rounded.  The shipped path is written in whole path units -- a
    tenth of a viewBox unit, 0.008% of the mark -- and matching that keeps the file small."""
    r = (lambda v: int(round(v))) if ndigits == 0 else (lambda v: round(v, ndigits))
    out = []
    for c in cs:
        d = ['M%s %s' % (r(c.start[0]), r(c.start[1]))]
        for sg in c.segs:
            if sg[0] == 'l':
                d.append('L%s %s' % (r(sg[1][0]), r(sg[1][1])))
            else:
                d.append('C%s %s %s %s %s %s' % (r(sg[1][0]), r(sg[1][1]), r(sg[2][0]), r(sg[2][1]),
                                                 r(sg[3][0]), r(sg[3][1])))
        d.append('Z')
        out.append(' '.join(d))
    return ' '.join(out)


if __name__ == '__main__':
    cs, info = derive()
    print('  union: %d contours (%d holes), %d smooth runs, worst fit %.5f mark units'
          % (info['contours'], info['holes'], info['runs'], info['worst_fit']))
    geo = os.path.join(os.path.dirname(HERE), 'design', 'logo-animation', 'geometry.json')
    payload = dict(info=info, contours=[c.to_json() for c in cs])
    if os.path.exists(geo):
        site = to_site(cs, geo)
        from pen import bbox as _bb
        x0, y0, x1, y1 = _bb([c.flatten() for c in site])
        d = path_d(site)
        payload['site_path'] = d
        payload['site_bbox'] = [x0, y0, x1, y1]
        print('  site units: %.0f x %.0f path units, path %d chars' % (x1 - x0, y1 - y0, len(d)))
        # the same transform applied to the ARTWORK, as the check that it is the right one
        acs, _ = fit_union(artwork_polygon())
        ax0, ay0, ax1, ay1 = _bb([c.flatten() for c in to_site(acs, geo)])
        print('  check: the artwork through the same transform is %.0f x %.0f'
              ' (the shipped path is 10622 x 10053)' % (ax1 - ax0, ay1 - ay0))
    json.dump(payload, open(os.path.join(HERE, 'build', 'mark.json'), 'w'))
    print('  wrote build/mark.json')
