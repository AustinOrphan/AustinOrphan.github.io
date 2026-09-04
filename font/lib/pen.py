"""
Font-space geometry for the Orphan face.  Pure Python, y-up, font units.

Glyphs are built from a few primitives:

  stroke()   a straight stroke with independent widths at each end (the mark's
             strokes taper), ended flat, or cut obliquely with one corner as
             the tip (the mark's feet), or extended for a junction overlap
  ring()     two circles with the inner one offset -- the mark's O exactly
  arc_band() a partial ring, for C G S U and the bowls of B D P R
  the low-level line/circle helpers, for glyphs assembled edge by edge (the A)

Every polygon is returned as a list of (x, y) tuples wound counter-clockwise;
holes are wound clockwise.  The compiler unions overlapping polygons, so a
glyph is simply a list of overlapping pieces.
"""
import math

# ------------------------------------------------------------------ vectors
def add(a, b):   return (a[0]+b[0], a[1]+b[1])
def sub(a, b):   return (a[0]-b[0], a[1]-b[1])
def mul(a, k):   return (a[0]*k, a[1]*k)
def dot(a, b):   return a[0]*b[0] + a[1]*b[1]
def norm(a):     return math.hypot(a[0], a[1])
def unit(a):
    m = norm(a); return (a[0]/m, a[1]/m)
def perp(a):     return (-a[1], a[0])            # +90 degrees
def rot(a, deg):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    return (a[0]*c - a[1]*s, a[0]*s + a[1]*c)
def ang(a):      return math.degrees(math.atan2(a[1], a[0]))
def from_ang(deg): return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))

# ------------------------------------------------------------------ lines & circles
# a line is (point, unit direction); a circle is (centre, radius)
def line(p, v):        return (tuple(p), unit(v))
def line_ang(p, deg):  return (tuple(p), from_ang(deg))
def line_2pt(p, q):    return (tuple(p), unit(sub(q, p)))
def offset_line(l, d): return (add(l[0], mul(perp(l[1]), d)), l[1])   # parallel line, d to the left
def point_on(l, t):    return add(l[0], mul(l[1], t))

def isect(l1, l2):
    (p, u), (q, v) = l1, l2
    den = u[0]*v[1] - u[1]*v[0]
    if abs(den) < 1e-12: raise ValueError("parallel lines")
    w = sub(q, p); t = (w[0]*v[1] - w[1]*v[0]) / den
    return point_on(l1, t)

def line_x_at_y(l, y):
    (p, v) = l
    if abs(v[1]) < 1e-12: raise ValueError("horizontal line")
    return p[0] + v[0] * (y - p[1]) / v[1]

def line_circle(l, c, r, pick='max'):
    """Intersections of a line with a circle. pick: 'min'/'max' by line parameter, or a point to be nearest."""
    p, v = l; f = sub(p, c)
    b = 2*dot(f, v); cc = dot(f, f) - r*r; disc = b*b - 4*cc
    if disc < 0: raise ValueError("line misses circle")
    ts = [(-b - math.sqrt(disc))/2, (-b + math.sqrt(disc))/2]
    if pick == 'min':   t = ts[0]
    elif pick == 'max': t = ts[1]
    else:               t = min(ts, key=lambda t: norm(sub(point_on(l, t), pick)))
    return point_on(l, t)

def circle_circle(c1, r1, c2, r2, pick='max'):
    """Intersections of two circles. pick: 'min'/'max' by x, or a point to be nearest."""
    d = norm(sub(c2, c1))
    a = (r1*r1 - r2*r2 + d*d) / (2*d); h = math.sqrt(max(0.0, r1*r1 - a*a))
    m = add(c1, mul(unit(sub(c2, c1)), a)); n = perp(unit(sub(c2, c1)))
    cands = [add(m, mul(n, h)), sub(m, mul(n, h))]
    if pick == 'min':   return min(cands, key=lambda q: q[0])
    elif pick == 'max': return max(cands, key=lambda q: q[0])
    return min(cands, key=lambda q: norm(sub(q, pick)))

def circle_poly(c, r, n=160, ccw=True):
    pts = [(c[0] + r*math.cos(2*math.pi*i/n), c[1] + r*math.sin(2*math.pi*i/n)) for i in range(n)]
    return pts if ccw else pts[::-1]

def arc_poly(c, r, p_from, p_to, ccw=True, n=None):
    """Arc of the circle (c, r) from p_from to p_to, going counter-clockwise or clockwise."""
    a0 = math.atan2(p_from[1]-c[1], p_from[0]-c[0]); a1 = math.atan2(p_to[1]-c[1], p_to[0]-c[0])
    if ccw and a1 < a0: a1 += 2*math.pi
    if not ccw and a1 > a0: a1 -= 2*math.pi
    if n is None: n = max(4, int(abs(a1-a0) * r / 6))          # ~6 units per segment
    return [(c[0] + r*math.cos(a0 + (a1-a0)*i/n), c[1] + r*math.sin(a0 + (a1-a0)*i/n)) for i in range(n+1)]

def arc_poly_deg(c, r, a0, a1, n=None):
    return arc_poly(c, r, add(c, mul(from_ang(a0), r)), add(c, mul(from_ang(a1), r)), ccw=(a1 > a0), n=n)

# ------------------------------------------------------------------ polygons
def signed_area(poly):
    return 0.5 * sum(poly[i][0]*poly[(i+1) % len(poly)][1] - poly[(i+1) % len(poly)][0]*poly[i][1] for i in range(len(poly)))
def ccw(poly):  return poly if signed_area(poly) > 0 else poly[::-1]
def cw(poly):   return poly if signed_area(poly) < 0 else poly[::-1]
def bbox(polys):
    xs = [p[0] for poly in polys for p in poly]; ys = [p[1] for poly in polys for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))
def transform(poly, scale=1.0, rot_deg=0.0, origin=(0.0, 0.0), translate=(0.0, 0.0)):
    """Rotate about `origin`, scale about `origin`, then translate."""
    out = []
    for p in poly:
        q = rot(sub(p, origin), rot_deg); q = mul(q, scale); out.append(add(add(q, origin), translate))
    return out

# ------------------------------------------------------------------ strokes
def stroke(p0, p1, w0, w1, end0=('flat',), end1=('flat',)):
    """A straight stroke from p0 to p1, `w0` wide at p0 and `w1` wide at p1.

    End specs:
      ('flat',)                 square to the centre-line
      ('extend', d)             square, but d units further out (to overlap a junction)
      ('cut', angle, side)      oblique: the corner on `side` ('L' or 'R', looking
                                from p0 toward p1) is the tip, sitting exactly at
                                the end point; the cut line runs from it at the
                                absolute `angle` to meet the other edge
    """
    v = unit(sub(p1, p0)); n = perp(v)
    L0, R0 = add(p0, mul(n, w0/2)), sub(p0, mul(n, w0/2))
    L1, R1 = add(p1, mul(n, w1/2)), sub(p1, mul(n, w1/2))
    left, right = line_2pt(L0, L1), line_2pt(R0, R1)
    def end(spec, pt, Lpt, Rpt, outward):
        kind = spec[0]
        if kind == 'flat':
            return Lpt, Rpt
        if kind == 'extend':
            e = line(add(pt, mul(outward, spec[1])), n)
            return isect(left, e), isect(right, e)
        if kind == 'cut':
            _, angle, side = spec
            cut = line_ang(Lpt if side == 'L' else Rpt, angle)
            return (Lpt, isect(right, cut)) if side == 'L' else (isect(left, cut), Rpt)
        raise ValueError(spec)
    a, b = end(end0, p0, L0, R0, mul(v, -1))
    c, d = end(end1, p1, L1, R1, v)
    return from_poly(ccw([b, d, c, a]))

def ring(c, r_out, r_in, off=(0.0, 0.0)):
    """The mark's O: an outer circle and an inner circle whose centre is displaced by `off`.
    Returns [outer (ccw), inner (cw)] as cubic contours."""
    return [circle_contour(c, r_out, ccw=True), circle_contour(add(c, off), r_in, ccw=False)]

def arc_band(c, r_out, r_in, off, a0, a1):
    """The part of ring() between polar angles a0 -> a1 (degrees, measured at the OUTER
    centre, counter-clockwise), both ends cut along the rays from that centre.
    Used for C, G, S, U and the bowls of B, D, P, R.  Returns one ccw Contour."""
    ci = add(c, off)
    start, outer = arc_segments(c, r_out, a0, a1)
    i1 = line_circle(line_ang(c, a1), ci, r_in, pick='max')     # inner end on the a1 ray
    i0 = line_circle(line_ang(c, a0), ci, r_in, pick='max')
    b1, b0 = ang(sub(i1, ci)), ang(sub(i0, ci))
    if b0 > b1: b0 -= 360                                        # go back the way we came
    _, inner = arc_segments(ci, r_in, b1, b0)
    k = Contour(start)
    for sg in outer: k.curve_to(sg[1], sg[2], sg[3])
    k.line_to(i1)
    for sg in inner: k.curve_to(sg[1], sg[2], sg[3])
    return k.ccw()

# ------------------------------------------------------------------ cubic contours
# Glyph outlines are carried as contours of straight and cubic segments so the
# source's own Beziers (the bar and its hooks) pass through untouched, and so
# circles stay circles instead of 160-gons.
KAPPA = 0.5522847498

class Contour:
    __slots__ = ('start', 'segs')
    def __init__(self, start):
        self.start = (float(start[0]), float(start[1])); self.segs = []
    def line_to(self, p):
        self.segs.append(('l', (float(p[0]), float(p[1])))); return self
    def curve_to(self, c1, c2, p):
        self.segs.append(('c', (float(c1[0]), float(c1[1])), (float(c2[0]), float(c2[1])), (float(p[0]), float(p[1])))); return self
    def end(self):
        return self.segs[-1][-1] if self.segs else self.start
    def map(self, fn):
        c = Contour(fn(self.start))
        for s in self.segs:
            c.segs.append((s[0],) + tuple(fn(p) for p in s[1:]))
        return c
    def flatten(self, per=3.0):
        pts, last = [self.start], self.start
        for s in self.segs:
            if s[0] == 'l':
                pts.append(s[1]); last = s[1]
            else:
                c1, c2, p = s[1], s[2], s[3]
                n = max(3, int((norm(sub(c1, last)) + norm(sub(c2, c1)) + norm(sub(p, c2))) / per))
                for k in range(1, n+1):
                    t = k/n; m = 1-t
                    pts.append((m**3*last[0] + 3*m*m*t*c1[0] + 3*m*t*t*c2[0] + t**3*p[0],
                                m**3*last[1] + 3*m*m*t*c1[1] + 3*m*t*t*c2[1] + t**3*p[1]))
                last = p
        if norm(sub(pts[-1], pts[0])) < 1e-9: pts.pop()
        return pts
    def area(self):   return signed_area(self.flatten())
    def reversed(self):
        # walk back from the end, swapping each cubic's handles
        pts = [self.start] + [s[-1] for s in self.segs]
        c = Contour(pts[-1])
        for i in range(len(self.segs)-1, -1, -1):
            s = self.segs[i]; prev = pts[i]
            if s[0] == 'l': c.line_to(prev)
            else:           c.curve_to(s[2], s[1], prev)
        return c
    def ccw(self):    return self if self.area() > 0 else self.reversed()
    def cw(self):     return self if self.area() < 0 else self.reversed()
    def bbox(self):   return bbox([self.flatten()])
    def to_svg(self):
        d = [f"M{self.start[0]:.3f},{self.start[1]:.3f}"]
        for s in self.segs:
            if s[0] == 'l': d.append(f"L{s[1][0]:.3f},{s[1][1]:.3f}")
            else: d.append(f"C{s[1][0]:.3f},{s[1][1]:.3f} {s[2][0]:.3f},{s[2][1]:.3f} {s[3][0]:.3f},{s[3][1]:.3f}")
        return " ".join(d) + " Z"
    def to_json(self):
        return {'start': list(self.start), 'segs': [[s[0]] + [list(p) for p in s[1:]] for s in self.segs]}
    @staticmethod
    def from_json(j):
        c = Contour(j['start'])
        for s in j['segs']: c.segs.append((s[0],) + tuple(tuple(p) for p in s[1:]))
        return c

def from_poly(pts):
    c = Contour(pts[0])
    for p in pts[1:]: c.line_to(p)
    return c

def circle_contour(c, r, ccw=True):
    k = KAPPA * r; x, y = c
    out = Contour((x + r, y))
    out.curve_to((x + r, y + k), (x + k, y + r), (x, y + r))
    out.curve_to((x - k, y + r), (x - r, y + k), (x - r, y))
    out.curve_to((x - r, y - k), (x - k, y - r), (x, y - r))
    out.curve_to((x + k, y - r), (x + r, y - k), (x + r, y))
    return out if ccw else out.reversed()

def arc_segments(c, r, a0, a1):
    """Cubic segments approximating the arc a0 -> a1 (degrees), split into <= 90-degree pieces.
    Returns (start_point, [('c', c1, c2, p), ...])."""
    n = max(1, int(math.ceil(abs(a1 - a0) / 90.0 - 1e-9)))
    segs = []; start = add(c, mul(from_ang(a0), r))
    for i in range(n):
        b0 = math.radians(a0 + (a1-a0)*i/n); b1 = math.radians(a0 + (a1-a0)*(i+1)/n)
        t = math.tan((b1 - b0)/4) * 4/3
        p0 = (c[0] + r*math.cos(b0), c[1] + r*math.sin(b0)); p3 = (c[0] + r*math.cos(b1), c[1] + r*math.sin(b1))
        c1 = (p0[0] - t*r*math.sin(b0), p0[1] + t*r*math.cos(b0)); c2 = (p3[0] + t*r*math.sin(b1), p3[1] - t*r*math.cos(b1))
        segs.append(('c', c1, c2, p3))
    return start, segs

def source_contours(items):
    """Contours from an Illustrator object's segment list ([['c', p0, c1, c2, p1], ['l', p0, p1], ...]).
    A new contour starts wherever a segment does not begin where the previous one ended."""
    out, cur, last = [], None, None
    for it in items:
        p0 = tuple(it[1])
        if cur is None or last is None or norm(sub(p0, last)) > 1e-6:
            cur = Contour(p0); out.append(cur)
        if it[0] == 'l': cur.line_to(it[2])
        else:            cur.curve_to(it[2], it[3], it[4])
        last = tuple(it[-1])
    return out

def cut_for(p_end, p_other, face, body, off_deg):
    """The ('cut', angle, side) end spec for stroke(), implementing the mark's oblique
    terminal (SPEC R5).  `face` is the side of the glyph the end is on ('bottom', 'top',
    'left', 'right'); `body` is the direction along that face toward the rest of the
    letter ('left', 'right', 'up', 'down').  The tip is the corner away from the body; the
    cut runs from it toward the body, `off_deg` off the face's axis and back into the
    stroke, exactly as the A's feet are cut."""
    v = unit(sub(p_end, p_other)); n = perp(v)
    b = {'right': (1, 0), 'left': (-1, 0), 'up': (0, 1), 'down': (0, -1)}[body]
    side = 'L' if dot(n, b) < 0 else 'R'
    if face == 'bottom':  angle = off_deg if b[0] > 0 else 180 - off_deg
    elif face == 'top':   angle = -off_deg if b[0] > 0 else 180 + off_deg
    elif face == 'right': angle = 270 - off_deg if b[1] < 0 else 90 + off_deg
    elif face == 'left':  angle = 270 + off_deg if b[1] < 0 else 90 - off_deg
    else: raise ValueError(face)
    return ('cut', angle, side)
