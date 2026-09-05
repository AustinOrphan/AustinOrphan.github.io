"""
set_bowl: B D P R -- an R3 stem, R1 half rounds, R4 horizontals to carry them
to the stem; R adds an R2 leg.

Every stroke is a lib constructor and every weight, taper, cut angle and
displacement comes from lib/rules.py:

  stem     rules.stem(STEM_X, 0, CAP, bottom='right', top='right').  The foot
           tip is the letter's lower-left corner (0, 0); the cut rises into the
           letter, free on P and R, buried under the baseline arm on B and D.
           The top cut is buried under the cap-line arm on all four.

  bowl     rules.round_arc(c, r, a0, a1): a half round, R1 exactly -- counter =
           outer inset by RING_W then displaced by RING_OFF toward 45 deg on
           the page, radial ends.  Heavy (53.0) at the lower left, light (13.4)
           at the upper right, whatever the bowl's size (R1, R7).

  arms     rules.arm(x0, x1, 'top'|'bottom', ...) on the cap line and baseline:
           outer edge exactly level on 700 / 0, R4's widths measured from it,
           the whole 1.8%-of-length taper on the inner edge, an R5 cut at the
           stem corner (set_straight's junction: the stem alone supplies the
           left edge, the arm alone the top or bottom edge, and the two share
           one outline point).  P's and R's bowl bottom and B's waist are
           rules.horizontal: level centre-line, symmetric taper.

  leg      (R) rules.diagonal, a "\\" parallel to the A's right leg, foot cut
           with the body to the left so the tip lands exactly on the baseline
           at the body width; top flat and buried in the bowl's bottom stroke.

Joining a round to a horizontal.  A round's band is 47.23 thick at its bottom
(RING_W + RING_OFF.y) and 19.15 at its top, against R4's 47.5 at mid-length:
the two constructions nearly agree at the bottom of a round and not at all at
the top, so the two joins are made differently and each is made the same way in
all four letters:

  bottom of a round on a horizontal (D and B's baseline arms, P/R's bar, B's
  waist under the upper bowl) -- the round is solved so its COUNTER is tangent
  to the horizontal's inner edge.  The counter and the inner edge then form one
  smooth line: the horizontal's inner edge runs level to the tangent point and
  the counter curves away from it, no ledge, no notch.  The round's outer
  circle, being 47.23 - w thicker than the bar at that point, dips a unit or
  two below the horizontal's outer edge, so the arc's radial end a0 is taken
  where the outer circle crosses that edge on the right; left of it the
  horizontal's own edge is the letter's outline, right of it the arc, and the
  two meet in a corner of a few degrees.  What is left of R1-vs-R4 is a step of
  RING_W/r of the thickness difference where the arc's radial end meets the
  counter, under half a unit in every glyph here (recorded per glyph).

  top of a round under a horizontal (B's lower bowl under the waist) -- the
  same, upside down: the counter is tangent to the horizontal's inner edge and
  the arc ends on the ray through that tangent point.  The band is only 19.15
  thick there, so the outer end of that radial cut is buried inside the bar and
  nothing of the join shows at all.

  cap-line arms -- the arm is DRAWN ON TO THE WEDGE FOR ITS INNER EDGE ONLY AND
  ITS OUTER EDGE IS CUT BACK TO THE ROUND'S CAP TANGENT POINT.  R4's 47.5
  against the band's 19.15 at the top of a round means a level underside is the
  only join there without a ledge, so the underside has to run level past the
  round's top until it meets the counter circle in a corner (the 'wedge'):
  x = 345.46 on D, 471.58 on P and R, 447.00 on B.  But the round's outer
  circle has fallen well away from the cap line by then -- to 671.62 on D,
  673.06 on P/R, 672.98 on B -- so an arm drawn level all the way to the wedge
  would end in a flat shelf standing 27-28 units proud of the arc and dropping
  off it in a cliff.  The outer edge is therefore trimmed back to the point
  where arm and circle ARE tangent, the round's top: x = 207.25 on D, 376.41 on
  P and R, 355.14 on B, cutting a 92-138 unit overhang.  That trim is what
  shapes the top of all four letters: the visible top edge is level on 700 from
  the stem to the tangent point and the arc from there on, and the chord the
  trim leaves behind runs from the tangent point back inside the band (its
  clearance from the counter circle, 8.6-9.2 units here, is measured and
  asserted in _cap_arm_note), so it is the deleted overhang, not the chord,
  that shows.  The top stroke thins from the arm's width to the band's along
  the way (R7).

Tooling (not rules; invisible in the outline).  This covers the BASELINE ARMS'
and the BARS' (P/R's bowl bottom, B's waist) buried right ends only: each is
reshaped so it lies strictly inside the band -- from the inner corner straight
to a point half a unit inside the outer circle, then a chord back to the point
where the two outlines meet -- and nothing of that reshaping reaches the
outline, because at the bottom of a round the band (47.23) is thicker than the
bar and the end is swallowed whole.  The same routine (_bury) is used on the
cap-line arms, but there it is NOT tooling: it deletes a visible overhang, as
set out above.  Apart from those two things every edge is the lib constructor's
own geometry.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from pen import (add, sub, mul, dot, perp, from_ang, ang, line, line_2pt, line_circle, circle_circle,
                 from_poly, ccw)
from metrics import CAP, SB_STRAIGHT, SB_ROUND
from rules import (glyph, stem, diagonal, horizontal, arm, round_arc, RING_W, RING_OFF, CUT_DEG, HORIZ_MID,
                   HORIZ_TAPER, w_stem, w_horizontal, w_backslash, BACK_BASE, BACK_CAP)
from glyphs import core

# ---- proportions read from the exemplars and the face --------------------------------
_A = core.build_A()['notes']
BODY      = round(_A['vertices']['tipR'][0] - _A['vertices']['tipL'][0])   # 558: the A's foot spread, R8 medium
LEG_ANGLE = _A['leg_angles'][1]                                            # 111.29 deg: the A's right leg, a "\" stroke

MID_LINE = CAP / 2 + HORIZ_MID / 4   # 361.875: the face's mid line (set_straight.MID_Y); cross-checked at import
def _check_mid_line():
    import importlib
    try: ss = importlib.import_module('glyphs.set_straight')
    except ModuleNotFoundError as e:
        if e.name != 'glyphs.set_straight': raise
        return 'set_straight not present; cross-check skipped'
    if abs(ss.MID_Y - MID_LINE) > 1e-9:
        raise RuntimeError(f'set_bowl.MID_LINE ({MID_LINE}) != set_straight.MID_Y ({ss.MID_Y})')
    return 'equals set_straight.MID_Y (checked at import)'
_MID_CHECK = _check_mid_line()

STEM_X  = w_stem(0) / 2                      # 19.75: stem centre; foot tip at x = 0
FOOT    = (STEM_X - w_stem(0) / 2, 0.0)      # (0, 0)   the stem's lower-left corner
TOP     = (STEM_X - w_stem(CAP) / 2, CAP)    # (6.2, 700) the stem's upper-left corner
P_BAR_Y = MID_LINE                           # P/R bowl-bottom centre-line
B_WAIST_Y = MID_LINE + HORIZ_MID / 2         # 385.625: B waist centre-line; its underside on the mid line
B_UPPER_INSET = RING_W                       # upper bowl's right extreme one round stroke inside the lower's
BAND_BOT = RING_W + RING_OFF[1]              # 47.23: an R1 band at the bottom of a round (R7's heavy side)
BAND_TOP = RING_W - RING_OFF[1]              # 19.15: and at the top
RUN = RING_W                                 # how far a bottom join's buried end runs past the meeting point
BURY_IN = 0.5                                # a buried end's chord sits this far inside the outer circle


# ---- helpers -------------------------------------------------------------------------
def _stem():
    return stem(STEM_X, 0.0, CAP, bottom='right', top='right')

def _sdist(l, p):
    """Signed distance of p from line l, positive to the left of its direction (above, for a +x line)."""
    return dot(sub(p, l[0]), perp(l[1]))

def _hline(x0, x1, y_c, edge):
    """The top (+1) or bottom (-1) edge line of rules.horizontal(x0, x1, y_c)."""
    L = x1 - x0
    return line_2pt((x0, y_c + edge * w_horizontal(L, 0) / 2), (x1, y_c + edge * w_horizontal(L, 1) / 2))

def _armline(x0, x1, outer, edge):
    """The outer (+1) or inner (-1) edge line of rules.arm(x0, x1, outer): the outer edge is level on
    the metric line, the inner edge carries R4's whole taper."""
    y_out, sgn = (CAP, -1) if outer == 'top' else (0.0, 1)
    if edge > 0: return line((x0, y_out), (1.0, 0.0))
    L = x1 - x0
    return line_2pt((x0, y_out + sgn * w_horizontal(L, 0)), (x1, y_out + sgn * w_horizontal(L, 1)))

def _touch(l, ci, ri, s):
    """Where a counter circle (ci, ri) tangent to line l touches it; s = +1 if the counter is above l."""
    return sub(ci, mul(perp(l[1]), s * ri))

def _solve_bowl(right, conds):
    """Radius and centre height of a round whose right extreme is `right`, from two linear
    conditions.  Each is ('cap',) -- outer circle tangent to the cap line -- or (s, line) with
    s = +1 for a counter tangent to `line` from above (a horizontal under the round) and -1 from
    below (a horizontal over it).  R1 fixes the counter, so each tangency is linear in (r, cy):
    with c = (right - r, cy), ci = c + RING_OFF and ri = r - RING_W, sdist(l, ci) = s (r - RING_W).
    Returns (r, cy)."""
    rows = []
    for cond in conds:
        if cond[0] == 'cap':
            rows.append((1.0, 1.0, float(CAP)))                       # r + cy = CAP
        else:
            s, l = cond; n = perp(l[1])
            C = dot(sub((right + RING_OFF[0], RING_OFF[1]), l[0]), n)  # sdist(l, ci) = C - r n.x + cy n.y
            rows.append((-n[0] - s, n[1], -C - s * RING_W))
    (a1, b1, k1), (a2, b2, k2) = rows
    det = a1*b2 - a2*b1
    if abs(det) < 1e-12: raise ValueError('degenerate bowl conditions')
    return (k1*b2 - k2*b1) / det, (a1*k2 - a2*k1) / det

def _bury(bar, outer, c, r, T, x1):
    """Reshape the flat right end of a rules.arm / rules.horizontal contour so it is buried in
    the band of the round (c, r): inner corner -> (x1, BURY_IN inside the outer circle) -> chord
    back to T, the point where the two outlines meet.  outer: 'top' if the bar's outer edge is
    its top.  Two different jobs, so read the caller: on a BASELINE ARM or a BAR (outer='bottom')
    x1 is past the meeting point, the end is extended into a band thicker than itself and nothing
    of this shows -- tooling.  On a CAP-LINE ARM (outer='top') x1 is the wedge and T the round's
    cap tangent point, well to the left of it, so this CUTS THE OUTER EDGE BACK and deletes a
    visible overhang; it is that trim, not tooling, that shapes the top of the letter."""
    pts = bar.flatten()
    xmax = max(p[0] for p in pts)
    right = [p for p in pts if abs(p[0] - xmax) < 1e-6]
    OR = max(right, key=lambda p: p[1]) if outer == 'top' else min(right, key=lambda p: p[1])
    side = 1 if outer == 'top' else -1
    yc = c[1] + side * math.sqrt(max(0.0, r*r - (x1 - c[0])**2))
    E = (x1, yc - side * BURY_IN)
    i = pts.index(OR); n = len(pts)
    before = pts[(i - 1) % n]
    rep = [E, T] if abs(before[0] - xmax) < 1e-6 else [T, E]
    return from_poly(ccw(pts[:i] + rep + pts[i+1:]))


# ---- the two round-to-horizontal joins ------------------------------------------------
def _bowl(right, below, cap=True, above=None):
    """One half round, R1, solved from its right extreme and the horizontals it joins.
    `below` / `above` are (outer edge, inner edge) line pairs of the horizontals under and over
    it; the counter is tangent to each inner edge.  cap=True replaces `above` with tangency to
    the cap line.  The arc runs from a0, where the outer circle crosses the lower horizontal's
    OUTER edge on the right, to a1: 90 (the cap) or the ray through the upper tangent point."""
    conds = [(+1, below[1]), ('cap',) if cap else (-1, above[1])]
    r, cy = _solve_bowl(right, conds)
    c = (right - r, cy); ci = add(c, RING_OFF); ri = r - RING_W
    Po = line_circle(below[0], c, r, pick='max')          # where the outline hands off to the arc
    a0 = ang(sub(Po, c))
    Pi = line_circle(line(c, from_ang(a0)), ci, ri, pick='max')
    hi = (c[0], float(CAP)) if cap else _touch(above[1], ci, ri, -1)
    a1 = 90.0 if cap else ang(sub(hi, c))
    return dict(c=c, r=r, ci=ci, ri=ri, a0=a0, a1=a1, Po=Po, Pi=Pi, hi=hi,
                lo=_touch(below[1], ci, ri, +1), step=_sdist(below[1], Pi))

def _bar_bowl(right, y_c, x0=STEM_X, cap=True, above=None):
    """A round standing on a rules.horizontal centred on y_c and running from x0.  The
    horizontal's length is solved with the round: it ends exactly where the round's outer circle
    crosses its underside, which is where the letter's outline hands off from one to the other."""
    x1 = right - 140.0
    for _ in range(500):
        below = (_hline(x0, x1, y_c, -1), _hline(x0, x1, y_c, +1))
        b = _bowl(right, below, cap=cap, above=above)
        if abs(b['Po'][0] - x1) < 1e-10: break
        x1 = (x1 + b['Po'][0]) / 2
    else: raise RuntimeError('bar/bowl solve did not converge')
    b.update(x0=x0, x1=x1, y_c=y_c, below=below)
    return b

def _arm_bowl(right, x0=FOOT[0], cap=True, above=None):
    """The same on a baseline rules.arm (outer edge exactly on 0, R4's taper on the inner edge)."""
    x1 = right - 200.0
    for _ in range(500):
        below = (_armline(x0, x1, 'bottom', +1), _armline(x0, x1, 'bottom', -1))
        b = _bowl(right, below, cap=cap, above=above)
        if abs(b['Po'][0] - x1) < 1e-10: break
        x1 = (x1 + b['Po'][0]) / 2
    else: raise RuntimeError('arm/bowl solve did not converge')
    b.update(x0=x0, x1=x1, below=below)
    return b

def _bar(b):
    """The rules.horizontal of a _bar_bowl, its buried end reshaped to lie inside the band."""
    return _bury(horizontal(b['x0'], b['x1'], b['y_c']), 'bottom', b['c'], b['r'], b['Po'], b['x1'] + RUN)

def _bottom_arm(b):
    """The baseline rules.arm of an _arm_bowl: outer edge exactly on 0, R5 cut at the foot corner,
    buried end reshaped to lie inside the band."""
    a = arm(b['x0'], b['x1'], 'bottom', left='cut', right='flat')
    return _bury(a, 'bottom', b['c'], b['r'], b['Po'], b['x1'] + RUN)

def _wedge_x(x0, y_out, ci, ri, sgn):
    """x where a cap-line arm's inner edge meets the counter circle (ci, ri), solved with the arm's
    own length (R4's taper depends on it).  sgn -1: top arm."""
    x1 = ci[0] + ri
    for _ in range(50):
        L = x1 - x0
        inner = line_2pt((x0, y_out + sgn * w_horizontal(L, 0)), (x1, y_out + sgn * w_horizontal(L, 1)))
        p = line_circle(inner, ci, ri, pick='max')
        if abs(p[0] - x1) < 1e-9: return x1
        x1 = p[0]
    return x1

def _top_arm(b):
    """Cap-line arm from the stem's top corner into the round, meeting its counter in the wedge."""
    x1 = _wedge_x(TOP[0], CAP, b['ci'], b['ri'], -1)
    a = arm(TOP[0], x1, 'top', left='cut', right='flat')
    return _bury(a, 'top', b['c'], b['r'], (b['c'][0], float(CAP)), x1), x1


def _check(b):
    """The join is what it claims: the hand-off point is on both the outer circle and the
    horizontal's outer edge, the counter is tangent to the horizontal's inner edge, and what is
    left of the R1-vs-R4 thickness difference is under a unit."""
    assert abs(math.dist(b['Po'], b['c']) - b['r']) < 1e-6, 'hand-off not on the outer circle'
    assert abs(_sdist(b['below'][0], b['Po'])) < 1e-6, 'hand-off not on the outer edge'
    assert abs(_sdist(b['below'][1], b['ci']) - b['ri']) < 1e-6, 'counter not tangent to the inner edge'
    assert 0 <= b['step'] < 1.0, f"step {b['step']}"
    return b

def _leg(tip, y_top):
    """R2 "\\" diagonal parallel to the A's right leg; R5 foot with the body to the left puts the
    tip exactly at `tip` on the baseline; top flat and buried at y_top.  rules.diagonal takes
    CENTRE-LINE ends and the R2 field is read there, so the centre-line end p0 is placed half a
    width off the tip along the stroke's normal and w0 solved to be consistent with it."""
    u = from_ang(LEG_ANGLE); n = perp(u)
    k = (BACK_CAP - BACK_BASE) / CAP
    w0 = w_backslash(tip[1]) / (1 - k * n[1] / 2)
    p0 = add(tip, mul(n, w0 / 2))
    p1 = add(p0, mul(u, (y_top - p0[1]) / u[1]))
    leg = diagonal(p0, p1, bottom='left', top=None)
    xs = [p[0] for p in leg.flatten()]; ys = [p[1] for p in leg.flatten()]
    assert abs(max(xs) - tip[0]) < 1e-6 and abs(min(ys) - tip[1]) < 1e-6, (max(xs), min(ys))
    return leg, p0, p1

def _round_note(b):
    return dict(centre=b['c'], r_out=b['r'], r_in=b['ri'], counter_centre=b['ci'], arc_deg=(b['a0'], b['a1']),
                right=b['c'][0] + b['r'], hand_off=b['Po'], counter_tangent=b['lo'], top=b['c'][1] + b['r'],
                bottom=b['c'][1] - b['r'])

def _kink(b): return abs(-90.0 - b['a0'])

def _join_note(b, what):
    return (f"{what}: R1's counter is tangent to the horizontal's inner edge at ({b['lo'][0]:.1f}, {b['lo'][1]:.1f}), "
            f"so the inner edge runs level into the counter as one smooth line -- no ledge and no notch inside "
            f"the letter.  The band is {BAND_BOT:.2f} thick at the bottom of a round against the horizontal's "
            f"R4 {abs(_sdist(b['below'][0], b['lo'])):.2f} there, so the outer circle dips "
            f"{BAND_BOT - abs(_sdist(b['below'][0], b['lo'])):.2f} below the horizontal's outer edge and the "
            f"outline hands off to the arc where it crosses it, at ({b['Po'][0]:.1f}, "
            f"{b['Po'][1]:.1f}), the two meeting at {_kink(b):.1f} deg (arc a0 = {b['a0']:.2f} deg, a radial R1 "
            f"end).  All that is left of R1 vs R4 is a {b['step']:.2f}-unit step where that radial end meets the "
            f"counter ({b['step']*100/CAP:.2f}% of the cap).")

def _cap_arm_note(b, x1):
    """The cap-line arm's numbers: drawn to the wedge, outer edge trimmed to the round's top."""
    tang = b['c'][0]
    y_at_wedge = b['c'][1] + math.sqrt(max(0.0, b['r']**2 - (x1 - tang)**2))
    T, E = (tang, float(CAP)), (x1, y_at_wedge - BURY_IN)     # the chord _bury leaves in place of the corner
    d = sub(E, T); t = max(0.0, min(1.0, dot(sub(b['ci'], T), d) / dot(d, d)))
    clear = math.dist(add(T, mul(d, t)), b['ci']) - b['ri']   # >0: the chord stays outside the counter
    assert clear > 0, f'the trim chord cuts into the counter by {-clear:.2f}'
    return dict(drawn_to_wedge_x=x1, outer_edge_ends_x=tang, overhang_trimmed=x1 - tang,
                cliff_avoided=CAP - y_at_wedge, circle_y_at_wedge=y_at_wedge,
                r4_length=x1 - TOP[0], visible_outer_length=tang - TOP[0],
                w_at_stem=w_horizontal(x1 - TOP[0], 0), w_at_wedge=w_horizontal(x1 - TOP[0], 1),
                chord_clear_of_counter=clear)

def _top_join(b, x1):
    n = _cap_arm_note(b, x1)
    return (f"Cap-line arm: rules.arm, outer edge level on {CAP}.  Its underside has to run level past the round's "
            f"top and meet the counter circle in a corner (the wedge, x={x1:.2f}), the arm's R4 width being "
            f"{HORIZ_MID:g} at mid-length against the band's {BAND_TOP:.2f} at the top of a round -- a level "
            f"underside is the only join there without a ledge.  Its OUTER EDGE IS CUT BACK to the round's cap "
            f"tangent point at x={n['outer_edge_ends_x']:.2f}, where arm and outer circle are tangent, trimming "
            f"{n['overhang_trimmed']:.2f} units of overhang: drawn level all the way to the wedge the arm would "
            f"stand {n['cliff_avoided']:.2f} units proud of the arc there (the circle is down to "
            f"{n['circle_y_at_wedge']:.2f} by x={x1:.2f}) and drop off it in a cliff.  That trim is what shapes "
            f"this letter's top: level on {CAP} from the stem to x={n['outer_edge_ends_x']:.2f}, then the arc.  "
            f"The chord the trim leaves runs back inside the band -- it clears the counter circle by "
            f"{n['chord_clear_of_counter']:.2f} units, asserted at build time -- so it does not show, and the "
            f"deleted overhang is the whole of what the trim does.  The top stroke thins from the arm's width to the band's along the "
            f"way (R7).")

_TOOLING = ("Tooling, invisible in the union: the baseline arm's and the bar's buried right ends are reshaped to "
            "lie inside the band (_bury) -- at the bottom of a round the band is thicker than the horizontal, so "
            "the end is swallowed whole.  (_bury also cuts the cap-line arm, but that is a visible trim, described "
            "above, not tooling.)  Stem and arm share exactly one outline point at each metric-line corner "
            "(set_straight's junction).")


# ---- glyphs --------------------------------------------------------------------------
def build_D():
    b = _check(_arm_bowl(BODY))
    arc = round_arc(b['c'], b['r'], b['a0'], b['a1'])
    top, x_top = _top_arm(b)
    bot = _bottom_arm(b)
    L_top, L_bot = x_top - TOP[0], b['x1'] - FOOT[0]
    return glyph(ord('D'), [_stem(), top, arc, bot], sb=(SB_STRAIGHT, SB_ROUND), notes=dict(
        construction=f"R3 rules.stem, both R5 cuts buried under the arms; rules.round_arc(({b['c'][0]:.1f}, "
                     f"{b['c'][1]:.1f}), r={b['r']:.1f}, {b['a0']:.2f}..90) -- the R1 half round, counter inset "
                     f"RING_W ({RING_W:.2f}) and displaced RING_OFF toward 45 deg, right extreme {BODY} (R8 "
                     f"medium), tangent to the cap line at x={b['c'][0]:.1f}; rules.arm on the cap line from the "
                     f"stem's top corner, drawn to the wedge at x={x_top:.1f} for its inner edge with its outer "
                     f"edge trimmed back to the bowl's cap tangent point at x={b['c'][0]:.1f} (see joins); "
                     f"rules.arm on the baseline from the foot corner "
                     f"to x={b['x1']:.1f}, where the outline hands off to the arc.",
        joins=f"{_top_join(b, x_top)}  {_join_note(b, 'Baseline arm')}  {_TOOLING}",
        weight=f"R1 puts {RING_W + RING_OFF[1]:.1f} of band at the bowl's bottom left and {RING_W - RING_OFF[1]:.1f} "
               f"at its top right, the O's own distribution at the O's own absolute weight (R1, R7); the bowl is "
               f"{b['r']*2/(2*(CAP/2)):.2f} of the O's radius and carries the O's stroke, not a scaled one.",
        proportions=f"Body {BODY} (R8 medium, the A's foot spread). Arms {L_top:.1f} (cap line) and {L_bot:.1f} "
                    f"(baseline) long, so R4 makes them {w_horizontal(L_top, 0):.1f} and {w_horizontal(L_bot, 0):.1f} "
                    f"at the stem.  Those are the DRAWN lengths, which is what R4's {HORIZ_TAPER*100:g}%-of-length "
                    f"taper is taken over, because the inner edge carries the whole taper and runs the whole way: "
                    f"the baseline arm's drawn length is also its visible one ({L_bot:.1f}, ending where the "
                    f"outline hands off to the arc), but the cap-line arm is drawn {L_top:.1f} to the wedge while "
                    f"its outer edge, trimmed back to the round's top, shows only "
                    f"{_cap_arm_note(b, x_top)['visible_outer_length']:.1f} -- "
                    f"{100*L_top/_cap_arm_note(b, x_top)['visible_outer_length'] - 100:.0f}% longer than what shows.",
        deviations=f"The bowl's outer circle passes {BAND_BOT - abs(_sdist(b['below'][0], b['lo'])):.2f} below "
                   f"the baseline (R1's band at the bottom of a round against R4's width there), but the arc "
                   f"begins where that circle crosses the baseline, so nothing of the letter goes below 0: the "
                   f"top and bottom extremes are the level arms and sit exactly on 0 and {CAP} like the H's and "
                   f"I's (R4), with no round overshoot -- an overshooting bowl would step off the flat arms. "
                   f"Residual R1-vs-R4 step {b['step']:.2f} units, recorded in joins.  The cap-line arm's outer edge "
                   f"is trimmed back to the bowl's top (joins): a construction the rules leave open, not a "
                   f"departure -- what shows of that edge is level on {CAP} exactly (R4).  No free R5 ends.",
        bowl=_round_note(b), arms=dict(top_end_x=x_top, bottom_end_x=b['x1'], top_len=L_top, bottom_len=L_bot,
                                       top_w_at_stem=w_horizontal(L_top, 0), bottom_w_at_stem=w_horizontal(L_bot, 0),
                                       cap_arm=_cap_arm_note(b, x_top)),
        stem=dict(x=STEM_X, w_foot=w_stem(0), w_cap=w_stem(CAP)), body_width=BODY))

def _p_parts():
    b = _check(_bar_bowl(BODY, P_BAR_Y))
    arc = round_arc(b['c'], b['r'], b['a0'], b['a1'])
    top, x_top = _top_arm(b)
    return b, arc, top, x_top, _bar(b)

def _p_notes(b, x_top, extra=""):
    L, Lt = b['x1'] - STEM_X, x_top - TOP[0]
    return dict(
        construction=f"R3 rules.stem with a free R5 foot (tip at (0, 0), the cut rising into the letter) and a top "
                     f"cut buried under the arm; rules.round_arc(({b['c'][0]:.1f}, {b['c'][1]:.1f}), r={b['r']:.1f}, "
                     f"{b['a0']:.2f}..90) -- the R1 half round, counter inset RING_W ({RING_W:.2f}) and displaced "
                     f"RING_OFF toward 45 deg, right extreme {BODY} (R8 medium), tangent to the cap line at "
                     f"x={b['c'][0]:.1f}; rules.arm on the cap line, drawn to the wedge at x={x_top:.1f} for its inner "
                     f"edge with its outer edge trimmed back to the bowl's cap tangent point at "
                     f"x={b['c'][0]:.1f} (see joins); "
                     f"rules.horizontal(STEM_X, {b['x1']:.1f}, y={b['y_c']:.3f}) closing the bowl below, its "
                     f"centre-line the face's mid line CAP/2 + HORIZ_MID/4 ({_MID_CHECK}), so H, E, P and R carry "
                     f"one horizontal through a word.  Bowl {CAP - b['lo'][1]:.0f} tall "
                     f"({100*(CAP - b['lo'][1])/CAP:.0f}% of the cap). {extra}",
        joins=f"{_top_join(b, x_top)}  {_join_note(b, 'Bowl bottom')}  {_TOOLING}",
        weight=f"R1: {BAND_BOT:.1f} of band at the bowl's lower left, {BAND_TOP:.1f} at its upper right, the O's "
               f"distribution at the O's absolute weight whatever the bowl's size (R1, R7).",
        proportions=f"Body {BODY} (R8 medium). Cap-line arm {Lt:.1f} long ({w_horizontal(Lt, 0):.1f} at the stem), "
                    f"bowl-bottom horizontal {L:.1f} ({w_horizontal(L, 0):.1f} at the stem, {w_horizontal(L, 1):.1f} "
                    f"at the hand-off).  Both are DRAWN lengths, and R4's {HORIZ_TAPER*100:g}%-of-length taper is "
                    f"taken over the drawn length because the inner edge, which carries the whole taper, runs the "
                    f"whole way.  For the bowl-bottom horizontal that is also its visible length, ending where the "
                    f"outline hands off to the arc; the cap-line arm is drawn {Lt:.1f} to the wedge but its outer "
                    f"edge is trimmed back to the round's top and shows only "
                    f"{_cap_arm_note(b, x_top)['visible_outer_length']:.1f}, so its R4 length is "
                    f"{100*Lt/_cap_arm_note(b, x_top)['visible_outer_length'] - 100:.0f}% longer than what shows.",
        deviations=f"Bowl height is fixed by the mid line, not by a ratio.  The bowl's outer circle passes "
                   f"{BAND_BOT - abs(_sdist(b['below'][0], b['lo'])):.2f} below the horizontal's underside "
                   f"(R1's band at the bottom of a round against R4's width there), but the arc "
                   f"begins where it crosses that underside, so nothing hangs below the bar.  Residual R1-vs-R4 "
                   f"step {b['step']:.2f} units, recorded in joins.  The cap-line arm's outer edge is trimmed "
                   f"back to the bowl's top (joins): a construction the rules leave open, not a departure -- "
                   f"what shows of that edge is level on {CAP} exactly (R4).  No others.",
        bowl=_round_note(b), bar=dict(y=b['y_c'], x1=b['x1'], length=L, w_stem=w_horizontal(L, 0), w_end=w_horizontal(L, 1)),
        cap_arm=_cap_arm_note(b, x_top),
        mid_line=dict(y=MID_LINE, source='CAP/2 + HORIZ_MID/4', cross_check=_MID_CHECK),
        stem=dict(x=STEM_X, w_foot=w_stem(0), w_cap=w_stem(CAP), foot_cut_deg=CUT_DEG), body_width=BODY)

def build_P():
    b, arc, top, x_top, bar = _p_parts()
    return glyph(ord('P'), [_stem(), top, arc, bar], sb=(SB_STRAIGHT, SB_ROUND), notes=_p_notes(b, x_top))

def build_R():
    b, arc, top, x_top, bar = _p_parts()
    leg, p0, p1 = _leg((float(BODY), 0.0), P_BAR_Y)
    notes = _p_notes(b, x_top, extra=(
        f"Leg: rules.diagonal, a \"\\\" at {LEG_ANGLE:.2f} deg (the A's right leg, half the apex angle off the "
        f"stem), centre-line from ({p1[0]:.1f}, {p1[1]:.1f}) on the bowl-bottom's centre-line down to "
        f"({p0[0]:.2f}, {p0[1]:.2f}); the R5 foot with the body to the left puts the tip exactly at ({BODY}, 0) "
        f"(asserted); top flat and buried in the bowl's bottom stroke.  R2 widths: {w_backslash(p0[1]):.2f} at p0, "
        f"{w_backslash(p1[1]):.2f} at the top."))
    notes['leg'] = dict(angle_deg=LEG_ANGLE, top=p1, bottom=p0, tip=(BODY, 0.0),
                        w_top=w_backslash(p1[1]), w_foot=w_backslash(p0[1]))
    notes['spacing'] = f"{SB_STRAIGHT} beside the stem, {SB_ROUND} on the right: the leg's foot tip is a point."
    return glyph(ord('R'), [_stem(), top, arc, bar, leg], sb=(SB_STRAIGHT, SB_ROUND), notes=notes)


def _b_parts(inset=B_UPPER_INSET):
    """B's two bowls and its waist.  The waist is one R4 rules.horizontal; the upper bowl's counter
    is tangent to its top edge and the lower bowl's counter to its underside, so both counters run
    out of the one bar as smooth lines and the waist reads as a single junction.  The upper bowl is
    solved with the waist (its length ends where the outline hands off, as everywhere here); the
    lower bowl is then solved between that waist and its own baseline arm."""
    up = _check(_bar_bowl(BODY - inset, B_WAIST_Y))
    above = (up['below'][1], up['below'][0])          # the waist seen from below: its inner edge is its underside
    lo = _check(_arm_bowl(BODY, cap=False, above=above))
    assert lo['hi'][0] < up['x1'], 'the lower bowl touches the waist past the end of the bar'
    assert lo['c'][1] + lo['r'] < up['Pi'][1], 'the lower bowl is not buried inside the waist'
    crotch = circle_circle(up['c'], up['r'], lo['c'], lo['r'], pick='max')
    return up, lo, _bar(up), crotch

def build_B():
    up, lo, waist, crotch = _b_parts()
    top, x_top = _top_arm(up)
    bot = _bottom_arm(lo)
    arc_u = round_arc(up['c'], up['r'], up['a0'], up['a1'])
    arc_l = round_arc(lo['c'], lo['r'], lo['a0'], lo['a1'])
    def tangent_right(b):
        t = perp(sub(crotch, b['c'])); return t if t[0] > 0 else mul(t, -1)
    tu, tl = tangent_right(up), tangent_right(lo)
    notch = math.degrees(math.atan2(abs(tu[0]*tl[1] - tu[1]*tl[0]), dot(tu, tl)))
    under, Lw, Lb = lo['hi'][1], up['x1'] - STEM_X, lo['x1'] - FOOT[0]
    return glyph(ord('B'), [_stem(), top, arc_u, waist, arc_l, bot], sb=(SB_STRAIGHT, SB_ROUND), notes=dict(
        construction=f"R3 rules.stem, both R5 cuts buried; cap-line rules.arm drawn to the wedge at x={x_top:.1f} for "
                     f"its inner edge, its outer edge trimmed back to the upper bowl's cap tangent point at "
                     f"x={up['c'][0]:.1f} (see joins); upper "
                     f"rules.round_arc(({up['c'][0]:.1f}, {up['c'][1]:.1f}), r={up['r']:.1f}, {up['a0']:.2f}..90) "
                     f"tangent to the cap line, standing on the waist; waist rules.horizontal(STEM_X, "
                     f"{up['x1']:.1f}, y={B_WAIST_Y:.3f}); lower rules.round_arc(({lo['c'][0]:.1f}, "
                     f"{lo['c'][1]:.1f}), r={lo['r']:.1f}, {lo['a0']:.2f}..{lo['a1']:.2f}) hanging from the waist "
                     f"and standing on the baseline arm, which is rules.arm to x={lo['x1']:.1f}.  Right extremes "
                     f"{BODY - B_UPPER_INSET:.1f} (upper) and {BODY} (lower).",
        waist=f"One junction: the upper bowl's counter is tangent to the waist's top edge at ({up['lo'][0]:.1f}, "
              f"{up['lo'][1]:.1f}) and the lower bowl's counter to its underside at ({lo['hi'][0]:.1f}, "
              f"{lo['hi'][1]:.1f}), so both counters leave the one bar as smooth lines.  The lower bowl's band is "
              f"only {BAND_TOP:.2f} thick at its top, so its whole radial end is buried inside the waist "
              f"(outer top {lo['c'][1] + lo['r']:.1f} against the waist's top edge at {up['Pi'][1]:.1f}) and "
              f"nothing of that join shows; the upper bowl's band is {BAND_BOT:.2f} at its bottom, so it hands "
              f"off to the waist's underside at ({up['Po'][0]:.1f}, {up['Po'][1]:.1f}) at {_kink(up):.1f} deg, "
              f"buried in turn inside the lower bowl, which reaches {lo['c'][1] + lo['r'] - up['Po'][1]:.1f} "
              f"above it there.  On the outline only the crotch at ({crotch[0]:.1f}, {crotch[1]:.1f}) shows, "
              f"where the two outer arcs cross at {notch:.1f} deg.",
        joins=f"{_top_join(up, x_top)}  {_join_note(up, 'Upper bowl on the waist')}  "
              f"{_join_note(lo, 'Lower bowl on the baseline arm')}  {_TOOLING}",
        weight=f"Both bowls are R1 exactly: counter inset RING_W ({RING_W:.2f}) then displaced RING_OFF "
               f"({RING_OFF[0]:.1f}, {RING_OFF[1]:.1f}) toward 45 deg on the page, so each carries "
               f"{BAND_BOT:.1f} at its lower left and {BAND_TOP:.1f} at its upper right whatever its size "
               f"(R1, R7) -- the same absolute distribution as the O, and the same in both bowls, the lighter "
               f"side of each falling at the top right.",
        proportion=f"Waist centre-line MID_LINE + HORIZ_MID/2 = {B_WAIST_Y:.3f}: its underside at the bowls is "
                   f"{under:.1f}, {under - MID_LINE:.1f} above the face's mid line, so the lower bowl shows "
                   f"{under:.0f} of the cap against the upper's {CAP - under:.0f} ({under/(CAP - under):.3f}) "
                   f"and the weight sits low (R7).  The upper bowl's right extreme stands RING_W "
                   f"({B_UPPER_INSET:.2f}) inside the lower's and its radius is {lo['r'] - up['r']:.1f} smaller, "
                   f"so the right side steps in at the waist.  Arms: the cap-line arm is drawn "
                   f"{x_top - TOP[0]:.1f} to the wedge and that is the length R4's taper is taken over (the inner "
                   f"edge carries the taper and runs the whole way), while its outer edge, trimmed back to the "
                   f"upper bowl's top, shows only {_cap_arm_note(up, x_top)['visible_outer_length']:.1f}; the "
                   f"baseline arm's drawn {Lb:.1f} is also its visible length, ending at the hand-off, and the "
                   f"waist's {Lw:.1f} likewise.",
        deviations=f"Waist height, the upper bowl's inset and the cap-line arm's trim back to the bowl's top "
                   f"(joins) are constructions the rules leave open, recorded above; what shows of the trimmed "
                   f"edge is level on {CAP} exactly (R4). "
                   "Residual R1-vs-R4 steps as recorded in joins. No free R5 ends; no round overshoot, the top "
                   "and bottom extremes being the level arms (R4).",
        upper=_round_note(up), lower=_round_note(lo),
        waist_geometry=dict(y=B_WAIST_Y, x1=up['x1'], length=Lw, w_stem=w_horizontal(Lw, 0),
                            w_end=w_horizontal(Lw, 1), crotch=crotch, notch_deg=notch),
        arms=dict(top_end_x=x_top, bottom_end_x=lo['x1'], top_len=x_top - TOP[0], bottom_len=Lb,
                  cap_arm=_cap_arm_note(up, x_top)),
        stem=dict(x=STEM_X, w_foot=w_stem(0), w_cap=w_stem(CAP)), body_width=BODY))

GLYPHS = {'B': build_B, 'D': build_D, 'P': build_P, 'R': build_R}
