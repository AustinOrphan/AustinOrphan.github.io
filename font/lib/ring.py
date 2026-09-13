"""R4b: an interior horizontal is a chord of the mark's ring.

SPEC section 5 gives R4 two weights for a horizontal -- one for a stroke that runs into a round,
one for a stroke in the open -- and leaves them level. R4b adds the gesture: a horizontal that
lies on NO METRIC LINE is not level at all, it is a chord of the ring the A carries, rising to
the right and arched on the ring's own radius.

    tilt(L) = min(RING_TILT, atan(RISE / L))

What every chord in the face shares is the RISE, not the angle. One angle is not one gesture:
an H bar spans 1.6x an E arm, so the same tilt would lift them differently. One rise is. A
chord shorter than the A's own span takes the ring's angle verbatim; a longer one relaxes until
its rise matches. The crossover between the two halves is the A's span, which is true by
construction -- both numbers are measured off its bar -- and not a discovered coincidence.

A horizontal ON the cap line or the baseline stays exactly level. The ring passes BEHIND the
letter, so it is not the ring's business to break the letter's silhouette against the line of
type; only the interior strokes are its to move.

The chord pivots about the horizontal's own centre line, so a glyph's colour and its counters
stay where the level rule put them, and only the gesture is new.

The band is CONSTANT and the rise is CAPPED, and both are one OPEN decision rather than a
settled one -- see SPEC R4b, "how literally to take the ring". What is here is reading A. Four
others were measured and drawn: B takes the ring's own constant 19.87 deg instead of capping the
rise, C adds the ring's width profile on top, and D and E draw the chord as an actual piece of
the annulus with both edges off the two ellipses, at the face's weight and at the mark's own.
measure/ring_readings.py rebuilds all four; measure/evidence/ring-*.png are the sheets.

The A cannot settle it. Its span, 251.11, is exactly where constant-rise and constant-angle
cross -- the crossover IS RISE/tan(RING_TILT) and both are measured off that same bar -- so every
reading reproduces the A and they diverge only on wider letters.
"""
import math

from pen import (Contour, add, sub, mul, unit, perp, norm, ang, from_ang, fit_cubics, fit_ranges,
                 clip_half, cut_for)
from metrics import CAP
from rules import w_horizontal, w_stem, HORIZ_FREE, HORIZ_JOIN, HORIZ_TAPER, CUT_DEG
from glyphs.core import MID_LINE, RISE, RING_TILT, ARC_R, RING

# How far past each end the band is drawn before it is clipped, and how finely the arch is
# sampled before it is fitted back to cubics.
EXT, NSAMP, FIT_TOL = 90.0, 90, 0.03
CHORD_SEGS = 5      # fixed pieces per chord edge; the most the adaptive fit ever asked for


def tilt_for(length):
    """The tilt a chord of this length takes: the ring's angle, or as much of it as keeps the
    rise to the ring's own."""
    return min(RING_TILT, math.degrees(math.atan(RISE / length)))


def chord_ends(x0, x1, y_mid=MID_LINE, sign=1.0):
    """The two centre-line ends of a chord spanning x0..x1 about y_mid.

    sign=-1 is the ring REFLECTED in y_mid. Only a glyph with a reason may take it -- the G,
    whose bar would otherwise close its aperture rather than open it.
    """
    L = x1 - x0
    dy = sign * L * math.tan(math.radians(tilt_for(L))) / 2
    return (x0, y_mid - dy), (x1, y_mid + dy), L


def _mirror(y_mid):
    return lambda p: (p[0], 2 * y_mid - p[1])


def ring_chord(x0, x1, y_mid=MID_LINE, mid=HORIZ_JOIN, end0=None, end1=None, sign=1.0):
    """An interior horizontal, built as a chord of the ring.

    Rises to the right by tilt_for(L) about y_mid, arched on ARC_R, carrying R4's widths and
    R4's taper measured on the CHORD's own normal rather than on the vertical -- the band is
    the same band, just no longer level.

    end0/end1 are (pointA, pointB) lines to cut the ends on: the outer edge of a stroke the
    chord passes behind, or an R5 face. None leaves the end square, for a caller that will
    bury it.
    """
    # Built upright and mirrored afterwards, so the arch reflects with everything else.
    p0, p1, L = chord_ends(x0, x1, y_mid, 1.0)
    u = unit(sub(p1, p0)); n = perp(u); Lc = norm(sub(p1, p0))
    h = math.sqrt(max(0.0, ARC_R * ARC_R - (Lc / 2) ** 2))
    c = sub(mul(add(p0, p1), 0.5), mul(n, h))          # centre below: the chord arches UP
    a0, a1 = ang(sub(p0, c)), ang(sub(p1, c))
    if a1 > a0:
        a1 -= 360.0
    da = math.degrees(EXT / ARC_R)
    t0, t1 = -da / (a0 - a1), 1.0 + da / (a0 - a1)     # extended, so the clip has material

    def sample(t):
        a = a0 + (a1 - a0) * t
        r = from_ang(a)
        q = add(c, mul(r, ARC_R))
        w = w_horizontal(L, t, mid)
        return add(q, mul(r, w / 2)), sub(q, mul(r, w / 2))

    # SOLVED, not clipped.  This used to be built long -- extended past both ends "so the
    # clip has material" -- and then cut back with pen.clip_half.  A clip keeps whichever
    # pieces fall inside, so how many segments come back depends on which segment the cut
    # lands in, and that moves with WEIGHT and PUSH; varLib then drops the glyph, which is
    # what froze the arms out of the axis.  Solving for the parameter where each EDGE meets
    # each end line and sampling only between them gives the same shape with a segment count
    # that cannot move: CHORD_SEGS a side, two cut faces, always.
    #
    # Each edge is solved separately because they meet an oblique end at different parameters;
    # the face between those two points is the cut, and lies on the line by construction.
    ends = [end0, end1]
    if sign < 0:                                   # the ends are given in final space
        m = _mirror(y_mid)
        ends = [None if e is None else (m(e[0]), m(e[1])) for e in ends]

    def edge(i):
        return lambda t: sample(t)[i]

    def meet(fn, e, lo, hi):
        """Where this edge crosses that end line, by bisection; None keeps the plain end."""
        if e is None:
            return None
        nn = perp(unit(sub(e[1], e[0])))
        f = lambda t: (fn(t)[0] - e[0][0]) * nn[0] + (fn(t)[1] - e[0][1]) * nn[1]
        flo, fhi = f(lo), f(hi)
        if (flo > 0) == (fhi > 0):
            return None
        for _ in range(60):
            md = (lo + hi) / 2
            if (f(lo) > 0) != (f(md) > 0): hi = md
            else: lo = md
        return (lo + hi) / 2

    spans = []
    for i in (0, 1):
        fn = edge(i)
        lo = meet(fn, ends[0], t0, 0.5)
        hi = meet(fn, ends[1], 0.5, t1)
        spans.append((0.0 if lo is None else lo, 1.0 if hi is None else hi))

    def run(i):
        lo, hi = spans[i]
        return [sample(lo + (hi - lo) * j / NSAMP)[i] for j in range(NSAMP + 1)]

    top, bot = run(0), run(1)

    def tangents(P):
        return [unit(sub(P[min(i + 1, len(P) - 1)], P[max(i - 1, 0)])) for i in range(len(P))]

    # A FIXED number of pieces, so a chord has the same points in every master (pen.fit_cubics).
    # Adaptively these ran 2 to 5 across the grid, and a glyph whose point count moves with the
    # knobs is dropped from the variable font's gvar.
    #
    # And a fixed number is only half of it.  The fit also chooses WHERE to cut, by splitting
    # whichever piece currently fits worst, and that is a discrete choice over a quantity that
    # moves with the knobs: two masters keep the same five pieces and still cut the arc in
    # different places, so varLib pairs control point i with a point describing somewhere else
    # on the letter and the straight line it draws between them misses.  That is what put the S
    # 42 units out between its masters and the 8 47.
    #
    # Here the knots are EVENLY SPACED rather than chosen, which is stable by construction:
    # index j is j/NSAMP along this edge's own clipped span in every master, and an even split
    # of a fixed sample count reads neither knob.  pen.fit_cubics warns off even division in
    # general and is right to -- it straddles corners, and on the 8 that cost a factor of 40 --
    # but a chord has no corner in it.  It is an arc of ARC_R carrying R4's gentle taper, and
    # measured over the sixteen chords the face draws, at eight points of the design space, an
    # even split fits them to 0.022 units at worst against 0.017 for choosing -- a forty-fifth
    # of the compiler's rounding either way.
    rg = [(i * NSAMP // CHORD_SEGS, (i + 1) * NSAMP // CHORD_SEGS) for i in range(CHORD_SEGS)]
    st, et = fit_cubics(top, tangents(top), ranges=rg)
    sb, eb = fit_cubics(bot[::-1], tangents(bot[::-1]), ranges=rg)
    k = Contour(top[0])
    for seg in st:
        k.curve_to(*seg)
    k.line_to(bot[-1])
    for seg in sb:
        k.curve_to(*seg)
    k = k.ccw()

    if sign < 0:
        k = k.map(_mirror(y_mid)).ccw()
        p0, p1, L = chord_ends(x0, x1, y_mid, sign)

    return k, dict(x=(x0, x1), y=(p0[1], p1[1]), length=L, tilt=sign * tilt_for(L),
                   rise=p1[1] - p0[1], w=(w_horizontal(L, 0, mid), w_horizontal(L, 1, mid)),
                   sagitta=Lc * Lc / (8 * ARC_R), fit_err=max(et, eb))


def chord_edge_point(x0, x1, y_c, edge, at_x, mid=HORIZ_JOIN, sign=1.0):
    """The point on a chord's top (+1) or bottom (-1) edge at x = at_x, and the edge's unit
    tangent there. edge=0 gives the centre line.

    A round that joins a chord cannot be solved against a straight line, because the chord is
    arched: what stands in for the edge is its TANGENT where the join actually happens. Which
    point that is depends on the bowl, so the caller iterates.
    """
    p0, p1, L = chord_ends(x0, x1, y_c, 1.0)
    u = unit(sub(p1, p0)); n = perp(u); Lc = norm(sub(p1, p0))
    h = math.sqrt(max(0.0, ARC_R * ARC_R - (Lc / 2) ** 2))
    c = sub(mul(add(p0, p1), 0.5), mul(n, h))
    a0, a1 = ang(sub(p0, c)), ang(sub(p1, c))
    if a1 > a0:
        a1 -= 360.0
    M = _mirror(y_c)

    # The edge is the arc at radius R(t), where R carries R4's taper on the arc's own normal.
    # Both R(t) and the angle are linear in t, so the tangent is exact in closed form -- and it
    # has to be. A finite difference here puts a ~2e-9 floor under the tangent, the bowl solves
    # against that tangent, and _bar_bowl's 1e-10 fixed point can then never close: at
    # WEIGHT 1.45 / PUSH 0.30 the P's bowl spun out its 500 passes and raised.
    dadt = math.radians(a1 - a0)
    dRdt = edge * sign * (-HORIZ_TAPER * L) / 2

    def _R(t):
        return ARC_R + edge * sign * w_horizontal(L, t, mid) / 2

    def pt(t):
        r = from_ang(a0 + (a1 - a0) * t)
        q = add(c, mul(r, _R(t)))
        return M(q) if sign < 0 else q

    def tangent(t):
        a = math.radians(a0 + (a1 - a0) * t)
        r, rp = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
        d = add(mul(r, dRdt), mul(rp, _R(t) * dadt))
        return unit((d[0], -d[1]) if sign < 0 else d)

    lo, hi = -1.0, 2.0
    for _ in range(80):
        m = (lo + hi) / 2
        if pt(m)[0] < at_x:
            lo = m
        else:
            hi = m
    t = (lo + hi) / 2
    return pt(t), tangent(t)


def r5_line(x0, x1, y_mid, which, body, mid=HORIZ_JOIN, sign=1.0):
    """The R5 cut at a FREE end of a chord: CUT_DEG off the vertical with the tip at the corner
    away from `body` -- but measured on the chord's own normal, as the A's feet are measured on
    its legs rather than on the page."""
    p0, p1, L = chord_ends(x0, x1, y_mid, sign)
    u = unit(sub(p1, p0)); n = perp(u)
    p = p1 if which == 'right' else p0
    w = w_horizontal(L, 1.0 if which == 'right' else 0.0, mid)
    away = 1.0 if body == 'down' else -1.0
    tip = add(p, mul(n, away * w / 2))
    _, angle, _ = cut_for((0.0, 0.0), (1.0 if which == 'left' else -1.0, 0.0), which, body, CUT_DEG)
    d = from_ang(angle)
    return (tip, add(tip, d))


def stem_edge_line(x_centre, side, inset=0.15):
    """The outer edge of an R3 stem as a line -- what a chord that passes BEHIND that stem is
    cut on, exactly as the A's bar is cut on its legs' outer edges. Pulled `inset` into the stem
    so the union never has two coincident edges to anti-alias against each other."""
    s = -1.0 if side == 'left' else 1.0
    return ((x_centre + s * (w_stem(0) / 2 - inset), 0.0),
            (x_centre + s * (w_stem(CAP) / 2 - inset), CAP))


def stem_outer_x(x_centre, side, y):
    return x_centre + (-1.0 if side == 'left' else 1.0) * w_stem(y) / 2


def solve_span(x_stem, side, x_far, y_mid=MID_LINE):
    """Where a chord meets a crossed stem's outer edge.

    That edge slopes, so the end's x depends on its y, which depends on the chord's length,
    which depends on the x. Four passes settle it to well under a unit.
    """
    x = stem_outer_x(x_stem, side, y_mid)
    for _ in range(4):
        if side == 'left':
            p0, _, _ = chord_ends(x, x_far, y_mid)
            x = stem_outer_x(x_stem, side, p0[1])
        else:
            _, p1, _ = chord_ends(x_far, x, y_mid)
            x = stem_outer_x(x_stem, side, p1[1])
    return x
