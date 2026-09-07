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
"""
import math

from pen import (Contour, add, sub, mul, unit, perp, norm, ang, from_ang, fit_cubics,
                 clip_half, cut_for)
from metrics import CAP
from rules import w_horizontal, w_stem, HORIZ_FREE, HORIZ_JOIN, CUT_DEG
from glyphs.core import MID_LINE, RISE, RING_TILT, ARC_R, RING

# How far past each end the band is drawn before it is clipped, and how finely the arch is
# sampled before it is fitted back to cubics.
EXT, NSAMP, FIT_TOL = 90.0, 90, 0.03


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

    ts = [t0 + (t1 - t0) * i / NSAMP for i in range(NSAMP + 1)]
    top = [sample(t)[0] for t in ts]
    bot = [sample(t)[1] for t in ts]

    def tangents(P):
        return [unit(sub(P[min(i + 1, len(P) - 1)], P[max(i - 1, 0)])) for i in range(len(P))]

    st, et = fit_cubics(top, tangents(top), tol=FIT_TOL)
    sb, eb = fit_cubics(bot[::-1], tangents(bot[::-1]), tol=FIT_TOL)
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

    inside = mul(add(p0, p1), 0.5)
    for e in (end0, end1):
        if e is not None:
            k = clip_half(k, e[0], e[1], inside)
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

    def pt(t):
        a = a0 + (a1 - a0) * t
        r = from_ang(a)
        q = add(add(c, mul(r, ARC_R)), mul(r, edge * sign * w_horizontal(L, t, mid) / 2))
        return M(q) if sign < 0 else q

    lo, hi = -1.0, 2.0
    for _ in range(80):
        m = (lo + hi) / 2
        if pt(m)[0] < at_x:
            lo = m
        else:
            hi = m
    t = (lo + hi) / 2
    return pt(t), unit(sub(pt(t + 1e-4), pt(t - 1e-4)))


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
