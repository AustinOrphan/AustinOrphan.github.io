"""The lowercase diagonals: k v w x y z.

Built on the capitals' own constructors rather than on rules.diagonal.  That matters: rules.
diagonal puts a stroke's CENTRE-LINE end on the point it is given and lets the R5 cut fall where
it may, so tips miss the line they should sit on and two strokes meeting in a point leave a notch
between their square ends.  set_diagonal._placed_stroke puts the stroke's CUT CORNER exactly on
the point, _point_cuts mitres two strokes meeting in a point, and _bisect buries an end in a
sloping edge.  All three are point-parameterised, so the capitals' solutions work at any height.

R2 gives every one of these its width from its own lean, and R6 gives a point its overshoot, so
what is left to decide is only where the ends are -- and the capitals decided that too.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from metrics import ASC_LC, CAP, DESC_LC, OVER_ROUND, SB_ROUND, SB_STRAIGHT, XH
from pen import (add, ang, ccw, from_poly, isect, line, line_ang, line_2pt, cut_for,
                 mul, perp, stroke, sub, unit)
import rules
from rules import glyph, w_stem, w_horizontal, w_at, wh_at, CUT_DEG
from pen import bbox
from glyphs import set_diagonal as SD
from glyphs import set_round as SR
from glyphs import set_lc_round as LR

HALF_APEX = SD.HALF_APEX                       # 21.29: the A's leg lean, the face's only diagonal
POINT_Y   = SD.POINT_Y                         # -16: R6's overshoot for a point, absolute
TIP_Y     = XH + SD.OVER_POINT                 # 401: where a point's tip sits at the top
MID       = XH / 2.0 + SD.HORIZ_MID / 4.0      # 206.97: the optical middle, as the capitals' is
HALF      = SD._spread(XH - POINT_Y, HALF_APEX)   # 156.27: the A's lean over the x-height
BODY      = 2 * HALF                           # 312.54 -- derived, not the capitals' body scaled
Y_NUDGE   = 10.0                               # how far the y's arm reaches into its leg
W_PEAK    = XH - LR.M_MID_Y                    # 270: mirrors the m's middle, as the W mirrors the M's vee


def _stressed(hi=None, lo=None, body=None):
    """Run a build inside this letter's R2s frame (rules.stress_for).  The w is two v's wide and
    the k reaches the ascender; everything else takes the lowercase's own body and box."""
    def deco(fn):
        def wrapper(*a, **k):
            with rules.stress_for(body if body is not None else BODY,
                                  lo=-OVER_ROUND if lo is None else lo,
                                  hi=hi):
                return fn(*a, **k)
        wrapper.__name__, wrapper.__doc__ = fn.__name__, fn.__doc__
        return wrapper
    return deco


def _arm_at(x0, x1, y_out, sgn, left='cut', right='cut'):
    """rules.arm, but with its outer line given instead of taken as CAP or the baseline."""
    body = 'down' if sgn < 0 else 'up'
    L = x1 - x0
    outer_l = line((x0, y_out), (1, 0))
    inner_l = line_2pt((x0, y_out + sgn * wh_at(L, 0, None, (x0, y_out))),
                       (x1, y_out + sgn * wh_at(L, 1, None, (x1, y_out))))
    def end(spec, x_end, face):
        if spec == 'flat': return line((x_end, y_out), (0, 1))
        other = x1 if face == 'left' else x0
        _, angle, _ = cut_for((x_end, y_out), (other, y_out), face, body, CUT_DEG)
        return line_ang((x_end, y_out), angle)
    l_end, r_end = end(left, x0, 'left'), end(right, x1, 'right')
    return from_poly(ccw([isect(outer_l, l_end), isect(inner_l, l_end),
                          isect(inner_l, r_end), isect(outer_l, r_end)])), inner_l


def _note(what, **kw):
    n = dict(construction=what,
             widths="R2's field by each stroke's own lean; nothing is chosen.",
             points=f"R6: a point's tip overshoots by {SD.OVER_POINT:g}, so the bottom points sit "
                    f"at {POINT_Y:g} and any top point at {TIP_Y:g}.",
             deviations="none from R1-R9.")
    n.update(kw); return n


V_T, V_TL, V_TR = (HALF, POINT_Y), (0.0, XH), (BODY, XH)


def _v_strokes():
    """The v's two arms, in nominal coordinates, for the v and for the y to extend."""
    cL, cR = SD._point_cuts(ang(sub(V_TL, V_T)), ang(sub(V_TR, V_T)))
    return (SD._placed_stroke(V_T, +1, V_TL, +1, end0=cL, end1='right'),
            SD._placed_stroke(V_T, -1, V_TR, -1, end0=cR, end1='left'))


@_stressed()
def build_v():
    """The capital V at the x-height -- and its width is derived there too, not scaled."""
    T, TL, TR = V_T, V_TL, V_TR
    left, right = _v_strokes()
    return glyph(ord('v'), [left, right], sb=(SB_ROUND, SB_ROUND), notes=_note(
        f"The A's legs inverted at the x-height: two R2 diagonals leaning {HALF_APEX:.2f} deg off "
        f"the vertical, meeting in a mitred point at ({HALF:.2f}, {POINT_Y:g}).",
        proportion=f"body {BODY:.2f}, which is the A's own lean run over the x-height "
                   f"(2 * {XH:g}-{POINT_Y:g} * tan {HALF_APEX:.2f}) -- derived here, not the "
                   f"capitals' 558 scaled down.  The two agree to 1.3 units, which is the check.",
        point="mitred with _point_cuts: each stroke's buried cut runs two thirds of the way from "
              "its own outer edge to the other's, so the two nest instead of leaving a notch."))


@_stressed(body=2 * BODY)
def build_w():
    """Two v's sharing a middle peak, as the capital W is two V's."""
    # The peak's x is the leg's OWN run at the A's lean over its own height, as the capital's is
    # (_w_parts).  Putting it at 2*HALF instead -- the run over the full x-height -- leaned the
    # legs 28.7 deg rather than 21.29, and the mitre computed for that could not close them: at
    # y=320, fifty units above the peak, there was still leg left.
    run = (W_PEAK - POINT_Y) * math.tan(math.radians(HALF_APEX))
    P_BL = (HALF, POINT_Y)
    T = (P_BL[0] + run, W_PEAK)
    P_BR = (T[0] + run, POINT_Y)
    F_L, F_R = (0.0, XH), (P_BR[0] + HALF, XH)
    cLs, cLl = SD._point_cuts(ang(sub(F_L, P_BL)), ang(sub(T, P_BL)))
    cRs, cRl = SD._point_cuts(ang(sub(F_R, P_BR)), ang(sub(T, P_BR)))
    cTl, cTr = SD._point_cuts(ang(sub(P_BL, T)), ang(sub(P_BR, T)))
    return glyph(ord('w'), [SD._placed_stroke(F_L, +1, P_BL, +1, end0='right', end1=cLs),
                            SD._placed_stroke(T, +1, P_BL, -1, end0=cTl, end1=cLl),
                            SD._placed_stroke(T, -1, P_BR, +1, end0=cTr, end1=cRl),
                            SD._placed_stroke(F_R, -1, P_BR, -1, end0='left', end1=cRs)],
                 sb=(SB_ROUND, SB_ROUND), notes=_note(
        f"Two v's meeting at a peak, the capital W's arrangement.  All four strokes lean the A's "
        f"{HALF_APEX:.2f} deg; the capital splays its sides to reach the M's advance, and the "
        f"lowercase has no such target to reach.",
        peak=f"{W_PEAK:g}, which is the x-height less the m's middle ({LR.M_MID_Y:g}) -- the same "
             f"mirror the capital W takes from the M's vee at 0.40 of the cap.",
        points="all three mitred with _point_cuts."))


@_stressed()
def build_x():
    """The capital X's solver: the tops are solved so the centre-lines cross on the axis."""
    xc = BODY / 2.0
    def top_x(E0, s0, s1, lo, hi):
        for _ in range(60):
            t = (lo + hi) / 2
            c0, c1 = SD._centres(E0, s0, (t, XH), s1)
            x_mid = c0[0] + (c1[0] - c0[0]) * (MID - c0[1]) / (c1[1] - c0[1])
            if x_mid < xc: lo = t
            else: hi = t
        return (lo + hi) / 2
    tR = top_x((0.0, 0.0), +1, -1, xc, BODY)
    tL = top_x((BODY, 0.0), -1, +1, 0.0, xc)
    return glyph(ord('x'), [SD._diag((0.0, 0.0), +1, (tR, XH), -1, bottom='right', top='left'),
                            SD._diag((BODY, 0.0), -1, (tL, XH), +1, bottom='left', top='right')],
                 sb=(SB_ROUND, SB_ROUND), notes=_note(
        f"Two R2 diagonals whose TIPS sit on the corners -- feet exactly on the baseline, tops "
        f"exactly on the x-height -- with the top x solved ({tR:.2f} and {tL:.2f}) so the two "
        f"centre-lines cross on the letter's axis at the optical middle, {MID:.2f}.",
        proportion=f"body {BODY:.2f}, the v's."))


@_stressed(lo=DESC_LC)
def build_y():
    """The v, with its right leg longer.  Nothing else differs.

    Both arms are the v's own, mitred at the v's own point by _point_cuts; only the right one is
    carried on past that point, down to the descender.  The left arm's mitre then sits inside the
    leg that continues, which is what keeps the junction clean -- cutting it parallel to the leg
    instead left it ending in a long wedge that hung out past the leg's left edge."""
    T, TL, TR = V_T, V_TL, V_TR
    c0, c1 = SD._centres(T, -1, TR, -1)                  # the v's right leg, centre-line ends
    d = unit(sub(c0, c1))                                # on down the same line
    # R2 takes a stroke's width from its own lean, so the two arms of a vee read DIFFERENT
    # fields: the leg rises to the right (w_slash), the arm to the left (w_backslash).  This is
    # the choice _placed_stroke makes for itself from the sign of the run, and it is the whole
    # of the residual that kept the y off the v -- one field for both put the arm's left edge a
    # constant 1.1 units outside the v's, all the way up.
    wf, wf_arm = rules.w_slash, rules.w_backslash
    # Widths on the v's OWN ramp, extrapolated -- not wf() re-evaluated at the new end.  pen.
    # stroke interpolates linearly between its two ends, so an end in a different place gives a
    # different ramp: taken fresh, the leg sat a constant 0.87 units right of the v's arm all the
    # way up, which is the whole reason the two letters would not lie on each other.
    span_v = math.dist(c0, c1)
    w_c0, w_c1 = w_at(wf, c0), w_at(wf, c1)
    def leg(depth):
        bot = add(c1, mul(d, depth))
        w_bot = w_c1 + (depth / span_v) * (w_c0 - w_c1) if span_v else w_c1
        return bot, stroke(bot, c1, w_bot, w_c1,
                           cut_for(bot, c1, 'bottom', 'right', CUT_DEG),
                           SD._end('left', -1, 1, c1, bot))
    lo, hi = 0.0, 2.0 * (c1[1] - DESC_LC)                # solved so the R5 TIP lands on -185
    for _ in range(40):
        mid = (lo + hi) / 2
        if min(p[1] for p in leg(mid)[1].flatten()) > DESC_LC: lo = mid
        else: hi = mid
    bot, right = leg((lo + hi) / 2)
    # The left arm is the v's OWN.  _centres solves a centre-line from the points it is given, so
    # the arm has to be placed on the v's point and the v's corner or it leans differently --
    # measured, placing it on the crossing of the outer edges instead put the y's left edge at
    # 28.68 deg against the v's 21.29 and drifted them 38.6 units apart by mid-arm.
    a0, a1 = SD._centres(T, +1, TL, +1)                  # the v's left arm, centre-line ends
    u = unit(sub(a0, a1))
    # Its end is cut ALONG the leg, and slid down its own centre-line until that cut sits on the
    # leg's FAR edge.  Sliding along the centre-line cannot change the lean.  Cut on the leg's
    # near edge or through its centre the arm still reached past the far edge: a 108-unit spur
    # below the junction, and a +0.23 reversal in an edge that otherwise falls 2.34 a step.
    lw = w_at(wf, T) / 2.0
    far = line_2pt(add(bot, mul(perp(d), lw)), add(c1, mul(perp(d), lw)))
    p0 = isect(line_2pt(a0, a1), far)
    leg_ang = ang(sub(c1, bot))
    # The width at that new end is the v's own ramp extrapolated, not wf(p0) freshly evaluated:
    # pen.stroke interpolates linearly between its two ends, so an end in a different place makes
    # a different ramp and the arm stops being the v's.  Taken fresh it drifted 0.87 units from
    # the v at mid-arm; on the v's ramp it is exact.
    span = math.dist(a0, a1)
    sp = math.dist(p0, a1) / span if span else 0.0
    w_a0, w_a1 = wf_arm(a0[1]), wf_arm(a1[1])
    left = stroke(p0, a1, w_a1 + sp * (w_a0 - w_a1), w_a1, ('cut', leg_ang, 'R'),
                  SD._end('right', +1, 1, a1, a0))
    # The y is SPACED like the v, not by its own leftmost ink.  rules.glyph puts the left extreme
    # on the sidebearing, and the y's left extreme is the tail's tip below the baseline -- so
    # placed that way the whole letter shifted right and the arm no longer sat where the v's arm
    # sits: measured, up to 38.6 units adrift at mid-arm.  The arm is registered instead and the
    # tail hangs into the bearing, exactly as the g's tail projects past its advance.
    v_l, v_r = _v_strokes()
    v_glyph = glyph(ord('v'), [v_l, v_r], sb=(SB_ROUND, SB_ROUND))
    ink = bbox([c.flatten() for c in [left, right]])
    arm_x0 = bbox([left.flatten()])[0]
    return glyph(ord('y'), [left, right], adv=v_glyph['adv'],
                 sb=(SB_ROUND - (arm_x0 - ink[0]), SB_ROUND), notes=_note(
        f"The v with its right leg longer: the same two strokes, mitred at the same point "
        f"({T[0]:.2f}, {T[1]:g}), with the right one carried on to ({bot[0]:.2f}, {DESC_LC:g}).",
        junction=f"The arm is the v's, placed exactly as the v places it; only its end differs, "
                 f"cut along the leg and slid down its own centre-line until that cut lands on "
                 f"the leg's far edge, so nothing of it reaches past.  The v's own mitre cannot "
                 f"serve, since it assumes both arms stop at the point.",
        angle=f"The leg is the v's stroke extended along its own centre-line, so the two letters "
              f"share the line and not merely a nominal lean: measured, the y's right edge is the "
              f"v's to 0.00 units at every height from 120 to 360.",
        tail=f"solved so the R5 tip lands on {DESC_LC:g}; putting the centre-line there left the "
             f"tip fifteen units short.",
        spacing=f"the v's advance and the v's left bearing measured on the ARM, so the two letters "
                f"register above the junction.  The tail hangs into the left bearing as the g's "
                f"hangs past its advance."))


@_stressed()
def build_z():
    """The capital Z at the x-height: two arms with the diagonal buried in both."""
    top, top_inner = _arm_at(0.0, BODY, XH, -1, left='cut', right='flat')
    bot, bot_inner = _arm_at(0.0, BODY, 0.0, +1, left='flat', right='cut')
    tw0, tw1 = wh_at(BODY, 0, None, (0.0, 0.0)), wh_at(BODY, 1, None, (BODY, 0.0))
    bi = ((0.0, tw0), (BODY, tw1)); ti = ((0.0, XH - tw0), (BODY, XH - tw1))
    c0 = SD._bisect(270.0, ang(sub(bi[1], bi[0])))
    c1 = SD._bisect(90.0, ang(sub(ti[0], ti[1])))
    diag = SD._placed_stroke(bi[0], +1, ti[1], -1, end0=c0, end1=c1)
    return glyph(ord('z'), [top, diag, bot], sb=(SB_ROUND, SB_ROUND), notes=_note(
        f"The capital Z at the x-height: an R4 arm with its top edge on {XH:g}, another with its "
        f"bottom edge on the baseline, and an R2 diagonal between their far corners.",
        buried=f"The diagonal's two ends are buried in the arms and cut on the BISECTOR of each "
               f"arm's end face and its inner edge.  R4 takes its whole taper on the inner edge, "
               f"so neither inner edge is level -- both slope -- and bisecting a level edge "
               f"instead leaves the diagonal standing proud of the arm.",
        proportion=f"body {BODY:.2f}, the v's."))


@_stressed(hi=ASC_LC)
def build_k():
    """The l's stem with the capital K's arm and leg."""
    xL = w_stem(0.0) / 2.0
    J = (xL, MID)
    st = rules.stem(xL, 0.0, ASC_LC, bottom='right', top='right')
    arm = SD._diag(J, 0, (BODY, XH), +1, top=('right', 'down'))
    leg = SD._diag((BODY, 0.0), +1, J, 0, bottom=('right', 'up'))
    return glyph(ord('k'), [st, arm, leg], sb=(SB_STRAIGHT, SB_ROUND), notes=_note(
        f"The capital K at the x-height: an R3 stem to the ascender with the arm and the leg "
        f"meeting on its centre-line at ({J[0]:.2f}, {MID:.2f}), buried there.",
        height=f"the stem reaches {ASC_LC:g}, the ascender, as the b, d, h and l do.",
        free_ends="Both present the letter's RIGHT face and lie nearer a horizontal than a "
                  "vertical, so R5's SECOND case applies -- the same cut turned 90 degrees, taken "
                  "off the vertical -- exactly as the capital K's note says.  Their tips sit on "
                  "the x-height and the baseline at the letter's right extreme.",
        proportion=f"body {BODY:.2f}, the v's."))


GLYPHS = {'k': build_k, 'v': build_v, 'w': build_w, 'x': build_x, 'y': build_y, 'z': build_z}
