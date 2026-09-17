"""The bowled lowercase: o c e a b d p q g.

Every letter here is R1's ring at the lowercase size plus, where it needs one, a single R3
stem placed by the same tangency the capitals use.  Nothing in this file invents a shape;
what it adds is one junction rule the capitals never needed, because no capital stops a stem
at the height of a round's own crown.

  THE CROWN-WEDGE JOINT
  ---------------------
  Section 4's tangency puts a stem's inner edge OUTSIDE the ring above y = 322.2, so a stem
  that runs on past the bowl -- b, d, and the ascenders generally -- leaves an aperture there,
  which is a normal feature of those letters and wants no correction.

  A stem that STOPS at the x-height is a different case.  Its top and the bowl's crown then
  sit at the same height with a wedge of white between them, and that reads as a nick in the
  letter rather than as an aperture.  a, p, q and g are all in this case.

  The joint solves it with two derived numbers and no new shape:

    * the stem stops at CROWN_Y, the height at which the bowl's outline actually meets its
      inner edge, so nothing of the stem stands proud of the bowl; and
    * its buried top is cut on the BOWL'S OWN TANGENT there, so the bowl's curve runs into
      the cut with no corner at all.

  R5 does not govern that cut.  R5 is the rule for FREE ends, and this one is buried in a
  junction; cutting it at R5's 20.6 degrees leaves a 28.75 degree corner where the curve
  enters the wedge, which is visible as a shoulder at display size.  On the tangent the
  corner is 0.00 degrees.  The crown wedge itself is unaffected -- it is the open space above
  the cut, and it stays.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from pen import (add, ang, cut_for, fit_cubics, fit_ranges, from_ang, isect, line_2pt,
                 line_ang, line_circle, mul, norm, perp, stroke, sub, unit,
                 Contour, from_poly, ccw)
from metrics import ASC_LC, DESC_LC, OVER_ROUND, SB_ROUND, SB_STRAIGHT, XH
import rules
from rules import RING_OFF, RING_W, CUT_DEG, glyph, round_ring, w_stem
from glyphs import set_round as SR

# The bowl: R1's ring, sized so the x-height is its flat height and it overshoots as a round
# does.  This is the o, and every other bowl in this file is the same circle, not a variant.
BOWL_R = (XH + 2 * OVER_ROUND) / 2.0            # 202.5
BOWL_C = (BOWL_R, XH / 2.0)                     # (202.5, 192.5)
GRAZE = SR.GRAZE


def bowl():
    """R1's ring at lowercase size: the o's own contours, counter displaced toward 45 deg."""
    return round_ring(BOWL_C, BOWL_R)


def stem_x(side):
    """Section 4's tangency, taken the way _light_junction and _heavy_junction take it: the
    stem's outer edge tangent to the circle GRAZE units inside the bowl's own, so the two
    cross at a real angle instead of grazing and the boolean has area to work with."""
    return SR._stem_tangent_x(BOWL_C, BOWL_R - GRAZE, side, side)


def crown_joint(side):
    """Where a stem that stops at the x-height must stop instead, and how its top is cut.

    Returns (y, deg): the height at which the bowl's outline meets the stem's inner edge, and
    the angle of the bowl's tangent there, measured in degrees below the horizontal.  The stem
    is cut on that tangent, hinged on the meeting point."""
    x = stem_x(side)
    inner = SR._stem_edge(x, -side, y0=0.0, y1=XH)
    p = line_circle(inner, BOWL_C, BOWL_R, pick='max')
    d = sub(p, BOWL_C)
    # the outline's tangent at p is perpendicular to the radius; its slope below the
    # horizontal is the same on both sides of the bowl, so take it off |dx|.
    return p[1], math.degrees(math.atan2(abs(d[0]), d[1]))


CROWN_Y, CROWN_DEG = crown_joint(+1)            # 324.6 and 49.35 at the axis origin


def joint_stem(side, y0, foot):
    """A stem that STOPS inside the bowl, cut on the crown-wedge joint.

    The joint is expressible in pen.stroke's own vocabulary: its ('cut', angle, side) end spec
    takes an ABSOLUTE angle and puts the tip on the named edge.  The tip is the stem's inner
    corner, which sits exactly on the bowl's outline at CROWN_Y, and the angle is the bowl's
    tangent there -- negative on the right of the bowl, where the tangent falls to the right,
    positive on the left, where it falls to the left.

    `foot` is the direction of the letter's body at the free end ('left' / 'right'), or None
    for an end that is itself buried and wants no cut."""
    x = stem_x(side)
    inner = 'L' if side > 0 else 'R'
    e0 = cut_for((x, y0), (x, CROWN_Y), 'bottom', foot, CUT_DEG) if foot else ('flat',)
    return stroke((x, y0), (x, CROWN_Y), w_stem(y0), w_stem(CROWN_Y),
                  e0, ('cut', -side * CROWN_DEG, inner))


def build_o():
    """R1's ring at lowercase size.  Nothing else: the o is the bowl, and every other bowled
    letter in this file is this same circle with something joined to it."""
    return glyph(ord('o'), bowl(), sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"rules.round_ring(({BOWL_C[0]:g}, {BOWL_C[1]:g}), r={BOWL_R:g}) -- R1 term for "
                     f"term at the lowercase size: band RING_W ({RING_W:.2f}), counter displaced "
                     f"RING_OFF toward 45 deg, both ABSOLUTE and so identical to the capital O's.",
        weight=f"The band is {RING_W/(2*BOWL_R)*100:.2f}% of this letter's diameter against "
               f"{RING_W/720*100:.2f}% of the cap O's, because R1 is absolute and the x-height is "
               f"55% of the cap.  That is the ordinary relationship between a lowercase and its "
               f"capitals, not a defect (see metrics.XH).",
        spacing=f"{SB_ROUND}/{SB_ROUND}: a round on both extremes (R9).",
        deviations="none from R1-R9."))


def build_a():
    """The bowl plus one R3 stem stopped on the crown-wedge joint.

    Single-storey per D7's successor: the a is R1's ring and an R3 stem, both rules the face
    already has.  A double-storey a would need an arch and a bowl-to-stem junction the mark
    supplies nothing for."""
    return glyph(ord('a'), bowl() + [joint_stem(+1, 0.0, 'left')],
                 sb=(SB_ROUND, SB_STRAIGHT), notes=dict(
        construction=f"The o's ring verbatim, plus a stem centred x={stem_x(+1):.2f} (section 4 "
                     f"tangency) running from the baseline to the joint at y={CROWN_Y:.2f}.",
        joint=f"The stem stops where the bowl's outline meets its inner edge ({CROWN_Y:.2f}) and its "
              f"buried top is cut on the bowl's tangent there ({CROWN_DEG:.2f} deg below the "
              f"horizontal), so the curve runs into the cut with a 0.00 deg corner.  R5's "
              f"{CUT_DEG:g} deg would leave 28.75 deg of corner, visible as a shoulder; R5 governs "
              f"FREE ends and this one is buried.",
        foot=f"R5, {CUT_DEG:g} deg, tip at the outer corner: a free end, so R5 does govern it.",
        spacing=f"{SB_ROUND}/{SB_STRAIGHT}: the bowl on the left, the stem on the right (R9).",
        deviations="none from R1-R9; the joint is a construction the rules leave open, not a "
                   "departure from them."))


def _descender_letter(cp, side, name):
    """p and q: the bowl and one stem, mirrored.  The stem runs to the descender line and
    stops there EXACTLY -- OVER_ROUND is the overshoot a round takes through a metric line,
    and an R5 cut is not a round, so a flat foot sits on -185 the way a straight sits on 0."""
    foot = 'right' if side < 0 else 'left'
    sb = (SB_STRAIGHT, SB_ROUND) if side < 0 else (SB_ROUND, SB_STRAIGHT)
    return glyph(cp, bowl() + [joint_stem(side, DESC_LC, foot)], sb=sb, notes=dict(
        construction=f"The o's ring verbatim, plus a stem centred x={stem_x(side):.2f} (section 4 "
                     f"tangency, {'left' if side < 0 else 'right'} of the bowl) running from the "
                     f"descender line to the joint at y={CROWN_Y:.2f}.",
        joint=f"The crown-wedge joint: the stem stops where the bowl's outline meets its inner "
              f"edge and its buried top is cut on the bowl's tangent there ({CROWN_DEG:.2f} deg), "
              f"so the curve enters the cut with no corner.  Same construction as the a and the g.",
        foot=f"R5, {CUT_DEG:g} deg, on {DESC_LC} exactly.  A round overshoots a metric line by "
             f"OVER_ROUND ({OVER_ROUND}); an R5 cut does not, so this foot sits on the descender "
             f"line the way the I's sits on the baseline.",
        spacing=f"{sb[0]}/{sb[1]}: the stem is the outer extreme on its own side and the bowl on "
                f"the other (R9).  The stem is {abs(stem_x(side) - (0 if side < 0 else 2*BOWL_R)):.2f} "
                f"from the bowl's extreme, and at the descender it is the wider of the two.",
        deviations="none from R1-R9."))


def build_p(): return _descender_letter(ord('p'), -1, 'p')
def build_q(): return _descender_letter(ord('q'), +1, 'q')


def _ascender_letter(cp, side):
    """b and d: the bowl and one stem that RUNS PAST it to the ascender.

    These are the joint's other case and want none of it.  A stem that stops at the x-height
    leaves its top and the bowl's crown at the same height with a wedge between them, which
    reads as a nick; a stem that carries on leaves an ordinary APERTURE between bowl and
    ascender, which is a feature every b and d has ever had.  So the stem is a plain R3 stem
    with two free R5 ends, and the only thing shared with a p or q is the bowl and the section
    4 tangency that places it.

    They are NOT mirrored geometry.  Both take stem_x for their own side, and R1's counter
    displacement makes those two positions different letters: the d's stem meets a 16.45-unit
    band and the b's a 42.50-unit one, so the b joins its bowl over a longer run and reads
    slightly heavier at the join.  That is R1 showing, not an error to correct out."""
    x = stem_x(side)
    body = 'right' if side < 0 else 'left'
    sb = (SB_STRAIGHT, SB_ROUND) if side < 0 else (SB_ROUND, SB_STRAIGHT)
    st = rules.stem(x, 0.0, ASC_LC, bottom=body, top=body)
    return glyph(cp, bowl() + [st], sb=sb, notes=dict(
        construction=f"The o's ring verbatim, plus a plain R3 stem centred x={x:.2f} (section 4 "
                     f"tangency, {'left' if side < 0 else 'right'} of the bowl) from the baseline "
                     f"to the ascender at {ASC_LC:g}, level with the cap line.",
        joint="None, and deliberately.  The crown-wedge joint exists for a stem that STOPS at the "
              "x-height beside a bowl; this one runs past, so the gap above the bowl is the "
              "ordinary aperture between bowl and ascender and wants no correction.",
        ends=f"Two free R5 cuts at {CUT_DEG:g} deg, the body side of each taken from the bowl.",
        taper=f"R3 read literally runs this stem from {w_stem(0.0):.2f} at the baseline to "
              f"{w_stem(ASC_LC):.2f} at the ascender -- half the bowl's own band ({RING_W:.2f}). "
              f"The capitals' stems do exactly the same over the same span; it shows more here "
              f"because the bowl beside it is half the size.  Flagged, not corrected.",
        spacing=f"{sb[0]}/{sb[1]}: the stem on its own side, the bowl on the other (R9).",
        deviations="none from R1-R9."))


def build_b(): return _ascender_letter(ord('b'), -1)
def build_d(): return _ascender_letter(ord('d'), +1)


# ---- g ---------------------------------------------------------------------------------
# The g is the a's stem with its foot turned into a tail.  What makes it a g rather than a q
# is that turn, and what makes the turn the face's own is where it leaves: at G_KICK_Y the
# stem bends onto the MARK'S STRESS AXIS -- the 45.07 deg direction R1 displaces the counter
# along, which is also the Q's tail -- runs G_KICK_LEN along it, and only then turns.
#
# The angle is fixed, not axis-dependent: RING_OFF's two components both scale with PUSH, so
# PUSH changes the displacement's length and never its direction.  Measured at all twelve
# cells of the shipped grid it is 45.067 degrees in every one.  What does move is the band the
# kick departs through: 28.50 at Thin, 40.74 at Regular, 81.43 at Black.
G_KICK_Y   = 90.0                      # where the stem stops running vertical
G_KICK_LEN = 110.0                     # how far it runs on the stress axis before the turn
G_KNEE_X   = 212.0
G_TIP      = (74.0, -104.0)
G_TIP_T    = (-0.72, 0.70)
G_TIP_W    = 34.0                      # the terminal band, never under ROUND_THIN
G_NSEG     = 34                        # cubics per edge, frozen at the axis origin
G_N        = 130                       # spine samples per span
G_DEPTH    = DESC_LC - OVER_ROUND      # the tail turns THROUGH the descender line, so it
                                       # overshoots as a round does; the q's flat foot does not


def _w1(y):
    """R3's width at the AXIS ORIGIN.  The field is linear in WEIGHT, so dividing it out is
    exact, and the g's knots have to be chosen on the origin's shape to stay compatible."""
    return w_stem(y) / rules.WEIGHT


def _tangent_x(wf, side):
    """set_round._stem_tangent_x with the width field injectable, so the origin's placement can
    be rebuilt from inside any master."""
    r = BOWL_R - GRAZE
    e0 = (side * wf(0.0) / 2, 0.0); e1 = (side * wf(XH) / 2, XH)
    v = unit(sub((e1[0], XH), (e0[0], 0.0))); n = perp(v)
    d0 = n[0] * (BOWL_C[0] - e0[0]) + n[1] * (BOWL_C[1] - e0[1])
    return (d0 - side * r) / n[0]


def _crown(wf, side):
    """CROWN_Y and CROWN_DEG for a given width field."""
    x = _tangent_x(wf, side)
    edge = line_2pt((x - side * wf(0.0) / 2, 0.0), (x - side * wf(XH) / 2, XH))
    p = line_circle(edge, BOWL_C, BOWL_R, pick='max')
    d = sub(p, BOWL_C)
    return p[1], math.degrees(math.atan2(abs(d[0]), d[1]))


def _g_spine(ky, wf):
    """The tail's centre line: down the stem, out along the stress axis, round the knee, to the
    tip.  A C1 chain of cubics, sampled evenly."""
    x = _tangent_x(wf, +1)
    crown_y, _deg = _crown(wf, +1)
    u = from_ang(-ang(RING_OFF))                       # the mark's stress axis, mirrored
    n2 = (x, G_KICK_Y)
    nodes = [((x, crown_y), (0.0, -1.0), None, 70.0),
             (n2,           (0.0, -1.0), 70.0, 60.0),
             (add(n2, mul(u, G_KICK_LEN)), u, 60.0, 92.0),
             ((G_KNEE_X, ky), unit((-1.0, 0.03)), 120.0, 64.0),
             (G_TIP, unit(G_TIP_T), 82.0, None)]
    pts = []
    for i in range(len(nodes) - 1):
        (P0, t0, _i0, h0), (P1, t1, h1, _o1) = nodes[i], nodes[i + 1]
        A = add(P0, mul(t0, h0)); B = sub(P1, mul(t1, h1))
        for k in range(G_N + 1):
            if i and k == 0: continue
            t = k / G_N; m = 1 - t
            pts.append((m**3*P0[0] + 3*m*m*t*A[0] + 3*m*t*t*B[0] + t**3*P1[0],
                        m**3*P0[1] + 3*m*m*t*A[1] + 3*m*t*t*B[1] + t**3*P1[1]))
    return pts, crown_y


def _g_tan(P):
    return [unit(sub(P[min(i+1, len(P)-1)], P[max(i-1, 0)])) for i in range(len(P))]


def _g_edges(ky, wf):
    """Both offset edges.  The width runs from the stem's own at the joint down to the terminal
    band as one smoothstep, and takes R3's widening below the baseline on top of that, so the
    tail is neither a constant-width ribbon nor thinner than the field says."""
    pts, crown_y = _g_spine(ky, wf)
    n = len(pts); w_top = wf(crown_y)
    L, Rt = [], []
    for i, (q, t) in enumerate(zip(pts, _g_tan(pts))):
        f = i / (n - 1); e = f * f * (3 - 2 * f)
        w = (w_top + (G_TIP_W - w_top) * e) * (wf(q[1]) / w_top)
        nv = perp(t)
        L.append(add(q, mul(nv, w / 2))); Rt.append(sub(q, mul(nv, w / 2)))
    return L, Rt, crown_y


def _g_solve(wf):
    """Move the knee until the ink bottoms on G_DEPTH.  Damped: once the turn is tight the knee
    moves the lowest point non-linearly."""
    ky = -170.0
    for i in range(40):
        L, Rt, _c = _g_edges(ky, wf)
        low = min(z[1] for z in L + Rt)
        if abs(low - G_DEPTH) < 0.01: break
        ky += (G_DEPTH - low) * (1.0 if i < 6 else 0.5)
    return ky


def _g_profile(wf):
    """Both edges, with BOTH ends already cut: R5 on the free tip, the crown-wedge joint on the
    buried top.  The cuts have to happen before the knots are chosen, not after -- the joint
    moves the outer corner about 50 units down the edge, and a knot fitted to the uncut shape
    then sits nowhere near the curve it is meant to describe."""
    ky = _g_solve(wf)
    L, Rt, crown_y = _g_edges(ky, wf)
    _cy, crown_deg = _crown(wf, +1)
    t = unit(sub(L[-1], L[-2])); wt = norm(sub(L[-1], Rt[-1]))
    k5 = math.tan(math.radians(CUT_DEG))
    L = L[:-1] + [add(L[-1], mul(t, wt/2*k5))]
    Rt = Rt[:-1] + [add(Rt[-1], mul(t, -wt/2*k5))]
    # the tip of the joint cut is the INNER corner, which for a spine travelling downwards is
    # Rt[0]; the cut runs from it on the bowl's tangent there to meet the outer edge
    L = [isect(line_2pt(L[0], L[1]), line_ang(Rt[0], -crown_deg))] + L[1:]
    return L, Rt, crown_y, wt, ky


def _g_ranges():
    """Where the g's cubics start and end, as sample indices: chosen ONCE on the axis origin's
    shape and held.  A fixed segment COUNT does not fix the knots -- fit_cubics splits on an
    argmax over residuals, which lands on a different sample as the axes move, and masters whose
    knots disagree cannot interpolate.  This is the fault that broke the S and the 8."""
    L, Rt, _c, _w, _k = _g_profile(_w1)
    return (fit_ranges(L, _g_tan(L), G_NSEG),
            fit_ranges(Rt[::-1], [mul(t, -1) for t in _g_tan(Rt)[::-1]], G_NSEG))


_G_RANGES = _g_ranges()


def build_g():
    """The a's stem with its foot turned into a tail, on the mark's own stress axis."""
    L, Rt, crown_y, wt, ky = _g_profile(w_stem)
    rg_out, rg_in = _G_RANGES
    so, eo = fit_cubics(L, _g_tan(L), tol=9e9, ranges=[tuple(r) for r in rg_out])
    si, ei = fit_cubics(Rt[::-1], [mul(x, -1) for x in _g_tan(Rt)[::-1]], tol=9e9,
                        ranges=[tuple(r) for r in rg_in])
    k = Contour(L[0])
    for sg in so: k.curve_to(*sg)
    k.line_to(Rt[-1])
    for sg in si: k.curve_to(*sg)
    return glyph(ord('g'), bowl() + [k.ccw()], sb=(SB_ROUND, SB_ROUND), adv=485, notes=dict(
        construction=f"The o's ring verbatim, plus one fitted stroke: the a's stem from the joint "
                     f"at y={crown_y:.2f} down to y={G_KICK_Y:g}, then {G_KICK_LEN:g} units along "
                     f"the mark's stress axis ({-ang(RING_OFF):.3f} deg), then the turn and the tail.",
        stress_axis="The kick's direction is R1's own counter displacement mirrored in the "
                    "horizontal -- the Q's tail axis.  It is FIXED across the design space: "
                    "RING_OFF's two components both scale with PUSH, so PUSH moves the "
                    "displacement's length and never its angle.  The band it departs through does "
                    "move, 28.50 at Thin to 81.43 at Black.",
        joint=f"The crown-wedge joint, as on a, p and q: the stroke starts where the bowl's "
              f"outline meets its inner edge and its buried top is cut on the bowl's tangent "
              f"({CROWN_DEG:.2f} deg).",
        depth=f"Solved per master: the knee moves until the ink bottoms on {G_DEPTH:g}, the "
              f"descender plus OVER_ROUND, because the tail turns THROUGH the line as a round "
              f"does.  The q's flat R5 foot does not overshoot and sits on {DESC_LC:g}.",
        knots=f"{G_NSEG} cubics per edge, taken once on the axis origin's shape and held.",
        tip=f"R5, {CUT_DEG:g} deg, band {wt:.1f} -- a free end.",
        spacing=f"{SB_ROUND}/{SB_ROUND} and the advance PINNED to the o's 485: the tail reaches "
                f"past it and projects into the next letter's bearing rather than being paid for "
                f"in width, the way a swash does.  Setting the advance from the tail instead "
                f"opens a hole beside every g at x-height level, because the tail's extreme is "
                f"below the baseline where nothing else is.",
        deviations="none from R1-R9.",
        fit=dict(worst_error=max(eo, ei), segs=(len(so), len(si)), knee_y=ky)))


GLYPHS = {'o': build_o, 'a': build_a, 'b': build_b, 'd': build_d,
          'p': build_p, 'q': build_q, 'g': build_g}
