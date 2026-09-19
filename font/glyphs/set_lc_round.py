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
from pen import (add, ang, arc_segments, cut_for, fit_cubics, fit_ranges, from_ang, isect,
                 line_2pt, BAND_SEGS,
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





# ---- n and h ---------------------------------------------------------------------------
# An n is not two posts with an arch dropped between them.  It is ONE stroke that runs up the
# left leg, turns over, and comes down the right leg, and the shoulder is simply where that
# stroke is curving.  Built that way the shoulder is seamless by construction: there is no
# junction in the letter to solve.  Built as three pieces unioned together -- which was tried
# -- the arch's radial end cuts show as notches against the legs and the letter reads as an
# arcade.
#
# The h is the same stroke with the left leg carried on to the ascender as a plain R3 stem.
# Its shoulder starts BURIED at H_BURY rather than at the baseline: the leg already makes that
# foot, and two opposite R5 cuts unioned together square it off flat.
N_SPRING = 180.0                # where the leg stops running straight
# The handles into the apex.  120, not the 150 this file carried: the four-panel sheet the arch
# was chosen from was drawn by a scratch prototype whose spine() bound h_in as a DEFAULT ARGUMENT
# and whose build() passed only the spring positionally, so the handle knob never moved and all
# four panels were drawn at 120 while their labels read 120 / 150 / 185 / 215.  What was chosen
# there was the SPRING; the shape approved was 180/120.  At 120 this module reproduces that image
# to 0.15% of its area, at 150 it is 21.59% off it.
N_HANDLE = 120.0
H_BURY   = 165.0                # where the h's shoulder starts, inside the leg
HN_NSEG  = 38                   # cubics per edge, frozen at the axis origin.  30 holds the n
                                # (0.165 worst) but not the h, whose buried start moves further
                                # across the axis: 0.909 at Black against MAX_ERR 0.6.
HN_SAMP  = 150                  # spine samples per span


def _band_at(th, ring_w=None, ring_off=None):
    """R1's band for a point whose outward normal points at page angle `th`.  Defaults to this
    instance's ring; _hn_ranges passes the axis origin's, to rebuild the shape the knots were
    chosen on."""
    ring_w = RING_W if ring_w is None else ring_w
    ring_off = RING_OFF if ring_off is None else ring_off
    return ring_w - norm(ring_off) * math.cos(math.radians(th) - math.radians(ang(ring_off)))


def _hn_spine(y0, wf, ring_w, ring_off, y1=0.0):
    """(left leg x, y0) up, over the apex, down to (right leg x, y1)."""
    xl, xr = _tangent_x(wf, -1), _tangent_x(wf, +1)
    apex_y = BOWL_C[1] + BOWL_R - _band_at(90.0, ring_w, ring_off) / 2.0
    nodes = [((xl, y0),          (0.0, 1.0),  None,     60.0),
             ((xl, N_SPRING),    (0.0, 1.0),  60.0,     N_HANDLE),
             ((BOWL_C[0], apex_y),(1.0, 0.0), N_HANDLE, N_HANDLE),
             ((xr, N_SPRING),    (0.0,-1.0),  N_HANDLE, 60.0),
             ((xr, y1),          (0.0,-1.0),  60.0,     None)]
    pts = []
    for i in range(len(nodes) - 1):
        (P0, t0, _i, h0), (P1, t1, h1, _o) = nodes[i], nodes[i + 1]
        A = add(P0, mul(t0, h0)); B = sub(P1, mul(t1, h1))
        for k in range(HN_SAMP + 1):
            if i and k == 0: continue
            t = k / HN_SAMP; m = 1 - t
            pts.append((m**3*P0[0] + 3*m*m*t*A[0] + 3*m*t*t*B[0] + t**3*P1[0],
                        m**3*P0[1] + 3*m*m*t*A[1] + 3*m*t*t*B[1] + t**3*P1[1]))
    return pts, (xl, xr)


def _crown_at(wf):
    """The a's crown joint rebuilt from an injected width field: where the stem's inner edge meets
    the bowl's outer circle, and the bowl's own angle there."""
    x = _tangent_x(wf, +1)
    e0 = (x - wf(0.0) / 2.0, 0.0); e1 = (x - wf(XH) / 2.0, XH)
    p = line_circle(line_2pt(e0, e1), BOWL_C, BOWL_R, pick='max')
    d = sub(p, BOWL_C)
    return p, math.degrees(math.atan2(abs(d[0]), d[1]))


def _a_edge_out(wf, y, cj):
    """How far the a's own outer edge stands out from its stem's centre-line at height y.

    Three pieces, which is what the a's silhouette is: the stem's edge while the stem is outside
    the bowl, the bowl's outer circle once it is outside the stem, and between them the cut that
    bridges the two.  Leaving the bridge out lets the stem's line run on to the apex."""
    p, cdeg = cj
    x = _tangent_x(wf, +1)
    bowl = BOWL_C[0] + math.sqrt(max(BOWL_R ** 2 - (y - BOWL_C[1]) ** 2, 0.0))
    stem = x + wf(y) / 2.0
    cut = p[0] - (y - p[1]) / math.tan(math.radians(cdeg))
    return max(bowl, min(stem, cut)) - x


CROWN_SUB = 4                   # knots per interval between the crown's piece transitions


def _crown_piece(wf, y, cj):
    """Which of the a's three pieces is the outer edge at height y: the stem, the cut that bridges
    it to the bowl, or the bowl."""
    p, cdeg = cj
    x = _tangent_x(wf, +1)
    bowl = BOWL_C[0] + math.sqrt(max(BOWL_R ** 2 - (y - BOWL_C[1]) ** 2, 0.0))
    stem = x + wf(y) / 2.0
    cut = p[0] - (y - p[1]) / math.tan(math.radians(cdeg))
    inner = 'stem' if stem <= cut else 'cut'
    return 'bowl' if bowl >= min(stem, cut) else inner


def _crown_knots(y0, wf, ring_w, ring_off, y1=0.0):
    """Every sample where the crowned edge turns a corner: each switch between the a's three
    pieces, and the sample where the crown gives way to the arch again.

    One knot at the end was not enough.  The edge follows max(bowl, min(stem, cut)) and the live
    piece changes twice more on the way up, each change a curvature break; a cubic spanning one
    of them fitted no better than 1.210 whatever else was done to the knots."""
    L0, _r0, _x0 = _hn_edges(y0, wf, ring_w, ring_off, y1, False)
    L1, _r1, _x1 = _hn_edges(y0, wf, ring_w, ring_off, y1, True)
    moved = [i for i in range(len(L0)) if abs(L0[i][0] - L1[i][0]) > 1e-9]
    if not moved: return []
    cj = _crown_at(wf)
    out, prev = [], _crown_piece(wf, L1[moved[0]][1], cj)
    for i in moved:
        now = _crown_piece(wf, L1[i][1], cj)
        if now != prev: out.append(i); prev = now
    out.append(moved[-1])
    out = sorted(set(out))
    # One knot per transition still left a cubic spanning 20 samples of hard curve at WEIGHT 1.45
    # (0.705).  A midpoint between each consecutive pair fixes that and keeps the count fixed --
    # always 2n-1 knots for n transitions, whatever the masters do.
    # Transitions alone still left a cubic spanning 20 samples of hard curve at WEIGHT 1.45
    # (0.705), because the piece next to a transition was being cut by an ORIGIN knot that does
    # not move with it.  So every knot inside the crown is derived from the transitions: each
    # interval between them is divided into CROWN_SUB equal parts.  The count is then fixed by
    # the number of transitions alone, which is 4 in every master.
    full = []
    for i, k in enumerate(out):
        if i:
            a = out[i-1]
            full += [a + int(round((k - a) * j / float(CROWN_SUB))) for j in range(1, CROWN_SUB)]
        full.append(k)
    return sorted(set(full))


def _crown_end(y0, wf, ring_w, ring_off, y1=0.0):
    """The sample the crown stops at -- the corner -- read off the edge itself by building it both
    ways and taking the last sample that moved.  Asking the question a second time in its own
    words got a different answer: the crown is applied against the SPINE's tangents, and the
    edge's own tangent at the cut foot already fails that test, which returned 0."""
    L0, _r0, _x0 = _hn_edges(y0, wf, ring_w, ring_off, y1, False)
    L1, _r1, _x1 = _hn_edges(y0, wf, ring_w, ring_off, y1, True)
    moved = [i for i in range(len(L0)) if abs(L0[i][0] - L1[i][0]) > 1e-9]
    return moved[-1] if moved else 0


def _hn_edges(y0, wf, ring_w, ring_off, y1=0.0, crown=False):
    """Both offset edges.  The legs carry R3's field and the apex carries R1's own top band,
    blended by the SPINE'S OWN TANGENT -- vertical while the stroke is a leg, horizontal at the
    apex.  (The radial direction reads the opposite way round and inverts the blend.)"""
    pts, (xl, xr) = _hn_spine(y0, wf, ring_w, ring_off, y1)
    apex_w = _band_at(90.0, ring_w, ring_off)
    ts = [unit(sub(pts[min(i+1, len(pts)-1)], pts[max(i-1, 0)])) for i in range(len(pts))]
    L, Rt = [], []
    for p, t in zip(pts, ts):
        turn = abs(t[0]); k = turn * turn * (3 - 2 * turn)
        w = wf(p[1]) * (1 - k) + apex_w * k
        nv = perp(t)
        L.append(add(p, mul(nv, w/2))); Rt.append(sub(p, mul(nv, w/2)))
    if crown:
        # The a's crown joint, on the springing leg.  Same joint, not an imitation: this leg sits
        # at exactly the x the a's stem sits at, the same tangency on the same circle at the same
        # GRAZE.  The a's edge converges back onto the arch's by itself, so the band ends on its
        # own -- y=183 to about 340 at the origin, pushing out by at most 13.2 units.  Points are
        # moved on the edge rather than a stem being unioned on, so this stays one contour.
        cj = _crown_at(wf)
        for i in range(min(2 * HN_SAMP + 1, len(L))):
            if ts[i][1] <= abs(ts[i][0]): break     # L is the TOP edge past the turn, not the left
            tgt = _a_edge_out(wf, L[i][1], cj)
            if tgt > xl - L[i][0]: L[i] = (xl - tgt, L[i][1])
    return L, Rt, (xl, xr)


def _r5_foot(L, Rt, mid, at_start):
    """R5 on a foot of the fitted stroke.  R5 puts the tip on the corner AWAY from the body and
    cuts the corner toward the body back, so on a symmetric letter the two feet MIRROR.  Taking
    "away from the body" as "further from the letter's own centre" gets that for free; cutting
    the same corner at both ends does not, and leaves an n whose feet lean the same way."""
    i = 0 if at_start else -1
    j = 1 if at_start else -2
    w = norm(sub(L[i], Rt[i]))
    k5 = math.tan(math.radians(CUT_DEG))
    if abs(L[i][0] - mid) > abs(Rt[i][0] - mid):        # L is the tip: cut Rt back
        Rt = list(Rt); Rt[i] = sub(Rt[i], mul(unit(sub(Rt[i], Rt[j])), w * k5))
    else:                                                # Rt is the tip: cut L back
        L = list(L); L[i] = sub(L[i], mul(unit(sub(L[i], L[j])), w * k5))
    return L, Rt


def _hn_profile(y0, wf, ring_w, ring_off, cut_start, y1=0.0, crown=False):
    L, Rt, (xl, xr) = _hn_edges(y0, wf, ring_w, ring_off, y1, crown)
    mid = (xl + xr) / 2.0
    if cut_start: L, Rt = _r5_foot(L, Rt, mid, True)
    L, Rt = _r5_foot(L, Rt, mid, False)
    return L, Rt, (xl, xr)


def _expand_ranges(spec, ks, npts):
    """A frozen spec plus this master's crown knots -> the index ranges to fit with."""
    if spec[0] == 'plain': return spec[1]
    rg0, slots = spec[1], spec[2]
    cuts = [rg0[0][0]] + [b for _a, b in rg0]
    for slot, k in zip(slots, ks):
        if slot < len(cuts): cuts[slot] = k
    for i in range(1, len(cuts)): cuts[i] = max(cuts[i], cuts[i-1] + 1)
    cuts[-1] = npts - 1
    for i in range(len(cuts) - 2, 0, -1): cuts[i] = min(cuts[i], cuts[i+1] - 1)
    return [(cuts[i], cuts[i+1]) for i in range(len(cuts) - 1)]


def _crown_spec(L, rg, ks):
    """The origin's knots with this crown's knots merged in, and where each landed."""
    ks = [k for k in ks if 0 < k < len(L) - 1]
    if not ks: return ('plain', rg)
    cuts = sorted(set([rg[0][0]] + [b for _a, b in rg] + ks))
    return ('split', [(cuts[i], cuts[i+1]) for i in range(len(cuts)-1)],
            [cuts.index(k) for k in ks])


def _hn_ranges(y0, cut_start, y1=0.0, crown=False):
    """Knots chosen once on the axis origin's shape and held, as for the g."""
    L, Rt, (xl, _xr) = _hn_profile(y0, _w1, rules.RING_W_1, rules.RING_OFF_1, cut_start, y1, crown)
    rg_in = fit_ranges(Rt[::-1], [mul(t, -1) for t in _g_tan(Rt)[::-1]], HN_NSEG)
    rg = fit_ranges(L, _g_tan(L), HN_NSEG)
    if crown:
        # The crown is piecewise and which piece is live moves with weight, so the edge is not
        # affine in the knobs the way the S's construction is: plain frozen indices describe a
        # different place in each master and the fit stalls at 1.210 however many there are (38
        # cubics and 72 both give exactly that).  The a does not suffer this because its crown is
        # an explicit VERTEX.  So keep the origin's knots and insert ONE at the corner; per master
        # only that knot slides.
        return _crown_spec(L, rg, _crown_knots(y0, _w1, rules.RING_W_1, rules.RING_OFF_1, y1)), rg_in
    return ('plain', rg), rg_in


_N_RANGES = _hn_ranges(0.0, True, crown=True)
_H_RANGES = _hn_ranges(H_BURY, False)

# Where the m's middle leg stops.  The m is a two-counter letter like the capital M, whose vee
# sits at 0.40 of the cap and whose notes argue that a middle carried to the baseline reads as a
# third counter rather than a stem.  This is the lowercase of the same decision, one step lower:
# at 0.40 (y=154) the two counters are open but the middle barely exists, and above that -- 0.49
# and up -- the two counters merge into one 651-unit space and the letter stops reading as an m.
M_MID_Y   = 115.0
_M_RANGES = _hn_ranges(0.0, True, M_MID_Y, crown=True)


def _hn_stroke(y0, cut_start, ranges, y1=0.0, crown=False):
    L, Rt, (xl, xr) = _hn_profile(y0, w_stem, RING_W, RING_OFF, cut_start, y1, crown)
    spec, rg_in = ranges
    ks = _crown_knots(y0, w_stem, RING_W, RING_OFF, y1) if crown else []
    rg_out = _expand_ranges(spec, ks, len(L))
    so, eo = fit_cubics(L, _g_tan(L), tol=9e9, ranges=[tuple(r) for r in rg_out])
    si, ei = fit_cubics(Rt[::-1], [mul(x, -1) for x in _g_tan(Rt)[::-1]], tol=9e9,
                        ranges=[tuple(r) for r in rg_in])
    k = Contour(L[0])
    for sg in so: k.curve_to(*sg)
    k.line_to(Rt[-1])
    for sg in si: k.curve_to(*sg)
    return k.ccw(), max(eo, ei), (xl, xr)


def _u_spine(y0, wf, ring_w, ring_off):
    """The n's stroke inverted: down the left leg, under the nadir, up the right leg.

    Not a mirrored n.  R1's band is 23.48 at the top of the ring and 57.90 at the bottom, so the
    u's turn is more than twice the weight of the n's shoulder -- and that is correct, because
    the o is heavier at the bottom too.  It also means the u's turn and its legs are close in
    weight (57.90 against 65.00 at the baseline) where the n's are far apart."""
    xl, xr = _tangent_x(wf, -1), _tangent_x(wf, +1)
    nadir = BOWL_C[1] - BOWL_R + _band_at(270.0, ring_w, ring_off) / 2.0
    nodes = [((xl, y0),               (0.0,-1.0), None,     60.0),
             ((xl, XH - N_SPRING),    (0.0,-1.0), 60.0,     N_HANDLE),
             ((BOWL_C[0], nadir),     (1.0, 0.0), N_HANDLE, N_HANDLE),
             ((xr, XH - N_SPRING),    (0.0, 1.0), N_HANDLE, 60.0),
             ((xr, XH),               (0.0, 1.0), 60.0,     None)]
    pts = []
    for i in range(len(nodes) - 1):
        (P0, t0, _i, h0), (P1, t1, h1, _o) = nodes[i], nodes[i + 1]
        A = add(P0, mul(t0, h0)); B = sub(P1, mul(t1, h1))
        for k in range(HN_SAMP + 1):
            if i and k == 0: continue
            t = k / HN_SAMP; m = 1 - t
            pts.append((m**3*P0[0] + 3*m*m*t*A[0] + 3*m*t*t*B[0] + t**3*P1[0],
                        m**3*P0[1] + 3*m*m*t*A[1] + 3*m*t*t*B[1] + t**3*P1[1]))
    return pts, (xl, xr)


def _turn_edges(spine_fn, y0, wf, ring_w, ring_off, apex_deg):
    """Offset both edges of a turning stroke: R3's field on the legs, R1's own band at the turn,
    blended by the spine's own tangent."""
    pts, (xl, xr) = spine_fn(y0, wf, ring_w, ring_off)
    apex_w = _band_at(apex_deg, ring_w, ring_off)
    ts = [unit(sub(pts[min(i+1, len(pts)-1)], pts[max(i-1, 0)])) for i in range(len(pts))]
    L, Rt = [], []
    for p, t in zip(pts, ts):
        turn = abs(t[0]); k = turn * turn * (3 - 2 * turn)
        w = wf(p[1]) * (1 - k) + apex_w * k
        nv = perp(t)
        L.append(add(p, mul(nv, w/2))); Rt.append(sub(p, mul(nv, w/2)))
    return L, Rt, (xl, xr)


def _u_profile(y0, wf, ring_w, ring_off, cut_start):
    L, Rt, (xl, xr) = _turn_edges(_u_spine, y0, wf, ring_w, ring_off, 270.0)
    mid = (xl + xr) / 2.0
    if cut_start: L, Rt = _r5_foot(L, Rt, mid, True)
    L, Rt = _r5_foot(L, Rt, mid, False)
    return L, Rt, (xl, xr)


# The u's turn is the heaviest curvature change in the arch family, so it does not fit on the
# n's 38 cubics: at 38 the worst residual over the axis grid is 0.878, past MAX_ERR's 0.6.  The
# residual falls to 0.063 at 46 and converges at 0.009 by 54, which is where this sits -- the
# knee of the curve, not the first count that merely passes.
U_NSEG = 54

_U_RANGES = (lambda L, Rt: (fit_ranges(L, _g_tan(L), U_NSEG),
                            fit_ranges(Rt[::-1], [mul(t, -1) for t in _g_tan(Rt)[::-1]], U_NSEG))
             )(*_u_profile(XH, _w1, rules.RING_W_1, rules.RING_OFF_1, True)[:2])


def build_u():
    """The n's stroke turned upside down."""
    L, Rt, (xl, xr) = _u_profile(XH, w_stem, RING_W, RING_OFF, True)
    rg_out, rg_in = _U_RANGES
    so, eo = fit_cubics(L, _g_tan(L), tol=9e9, ranges=[tuple(r) for r in rg_out])
    si, ei = fit_cubics(Rt[::-1], [mul(x, -1) for x in _g_tan(Rt)[::-1]], tol=9e9,
                        ranges=[tuple(r) for r in rg_in])
    k = Contour(L[0])
    for sg in so: k.curve_to(*sg)
    k.line_to(Rt[-1])
    for sg in si: k.curve_to(*sg)
    n = _arch_note(xl, xr, max(eo, ei), U_NSEG)
    n['construction'] = ("One stroke, the n's inverted: down the left leg at x=%.2f, under the "
                         "nadir, up the right leg at x=%.2f." % (xl, xr))
    n['weight'] = (f"The turn carries R1's band at the BOTTOM of the ring, {_band_at(270.0):.2f}, "
                   f"against the n's {_band_at(90.0):.2f} at the top -- more than twice it, "
                   f"because R1 displaces the counter toward 45 deg and the o is heavier at the "
                   f"bottom too.  So the u's turn and its legs are close in weight ({_band_at(270.0):.2f} "
                   f"against {w_stem(0.0):.2f}) where the n's are far apart.")
    return glyph(ord('u'), [k.ccw()], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=n)


def _arch_note(xl, xr, err, nseg=HN_NSEG):
    return dict(
        construction=f"One stroke: up the left leg at x={xl:.2f}, over the apex, down the right "
                     f"leg at x={xr:.2f}.  Both legs take section 4's tangency.  The shoulder is "
                     f"where that stroke is curving, not a join -- built as separate pieces the "
                     f"arch's radial end cuts show as notches and the letter reads as an arcade.",
        arch=f"The leg stops running straight at y={N_SPRING:g} and the handles into the apex are "
             f"{N_HANDLE:g}.  The spring was chosen against 250 (a flat bridge), 120 (a generic "
             f"inverted U) and 60 (a peaked counter and a picket rhythm), all four drawn at this "
             f"same handle.",
        weight=f"The legs carry R3's field and the apex carries R1's own top band "
               f"({_band_at(90.0):.2f}), blended by the spine's own tangent -- vertical on a leg, "
               f"horizontal at the apex.  The radial direction reads the opposite way round and "
               f"inverts the blend.",
        feet=f"R5, {CUT_DEG:g} deg, and MIRRORED: the tip is the corner away from the body, so an "
             f"n's two feet lean opposite ways, as the H's do.",
        knots=f"{nseg} cubics per edge, taken once on the axis origin's shape and held.  "
              f"Worst fit {err:.3f}.",
        deviations="none from R1-R9.")


def build_n():
    """One stroke, up and over and down."""
    k, err, (xl, xr) = _hn_stroke(0.0, True, _N_RANGES, crown=True)
    return glyph(ord('n'), [k], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=_arch_note(xl, xr, err))


def build_h():
    """The n's stroke with the left leg carried on to the ascender.

    The shoulder starts buried at H_BURY rather than at the baseline: the leg already makes that
    foot, and two opposite R5 cuts unioned together square it off flat."""
    k, err, (xl, xr) = _hn_stroke(H_BURY, False, _H_RANGES)
    leg = rules.stem(xl, 0.0, ASC_LC, bottom='right', top='right')
    n = _arch_note(xl, xr, err)
    n['construction'] = ("The n's stroke exactly, with the left leg carried on to the ascender as "
                         "a plain R3 stem -- the same field a capital stem takes, so the ascender "
                         "is the established thin stroke and not a lowercase weight of its own.  "
                         + n['construction'])
    n['feet'] = (f"R5, {CUT_DEG:g} deg, mirrored.  The shoulder starts buried at y={H_BURY:g} so "
                 f"the leg alone makes the left foot; reaching the baseline unions two opposite "
                 f"cuts and squares it flat.")
    return glyph(ord('h'), [leg, k], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=n)





# ---- c and e ---------------------------------------------------------------------------
# The c is the capital C's construction at lowercase size, not a segment erased from the o.
# The C solves its aperture and the solution is a rule, so the c inherits it: the opening spans
# 2 * CUT_DEG -- twice R5's cut angle, which is the A's apex angle and the face's one angular
# constant -- and it is rotated CUT_DEG/2 BELOW the horizontal, so the upper terminal reaches
# further round than the lower one, as a c wants. Both ends are radial cuts, so a terminal's
# length is whatever R1's band is at that angle rather than anything chosen.
#
# The e is that same arc carried further round, closed by an R4 bar. Its aperture cannot be the
# c's: a c opens at the middle of its right side and an e opens BELOW its bar, so the opening
# has to sit lower or the bar lands inside it.
C_TILT_LC = CUT_DEG / 2.0
C_TOP_LC, C_BOT_LC = CUT_DEG - C_TILT_LC, -CUT_DEG - C_TILT_LC      # +10.3 / -30.9

E_BAR_Y = XH / 2.0 + rules.HORIZ_MID / 4.0      # the E's own rule, read at lowercase height
# The e's aperture spans 2 * CUT_DEG, the same opening the c takes and the same one the capital
# C solves for.  Its UPPER end is not free -- it is pinned where the arc meets the bar -- so the
# lower end follows from it rather than being chosen.  Left at a chosen value the two letters
# disagree: the arc ends up wrapping 31.8 deg of opening against the c's 41.2.


def build_c():
    """The C's aperture rule at lowercase size."""
    # ccw FROM the upper terminal all the way round TO the lower one, so the gap is the
    # 2*CUT_DEG between them.  The other way round spans 401 deg and closes the letter.
    arc = rules.round_arc(BOWL_C, BOWL_R, C_TOP_LC, C_BOT_LC + 360.0)
    return glyph(ord('c'), [arc], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"One R1 arc of the o's own ring (centre {BOWL_C}, r={BOWL_R:g}, counter "
                     f"inset RING_W and displaced RING_OFF), opened on the right between the "
                     f"radial ends at {C_BOT_LC:+.2f} and {C_TOP_LC:+.2f} deg.  This is the "
                     f"capital C's construction read at the lowercase size, not a segment erased "
                     f"from the o.",
        aperture=f"The opening spans {2*CUT_DEG:.1f} deg -- twice CUT_DEG, R5's cut angle and the "
                 f"face's one angular constant -- rotated {C_TILT_LC:.2f} deg below the "
                 f"horizontal, so the upper terminal reaches further round than the lower one.  "
                 f"The C's own solution; see set_round.build_C for the alternatives it was "
                 f"chosen over.",
        terminals=f"Both ends are radial cuts (R5: partial rounds end in radial cuts), so each "
                  f"terminal is as long as R1's band at its own angle -- {_band_at(C_TOP_LC):.2f} "
                  f"at the upper end and {_band_at(C_BOT_LC):.2f} at the lower, heavy toward the "
                  f"lower left per R7.",
        spacing=f"{SB_ROUND}/{SB_ROUND}: a round on both extremes (R9).",
        deviations="none from R1-R9."))


def _e_bar_edges_OLD():
    """Where the bar's two ends sit, and where the arc must stop so it is buried under it.

    The arc's radial terminal at the bar's height is a nearly HORIZONTAL face pointing right,
    and the bar arrives side-on, so the two cannot both be the terminal there: butted together
    they leave a step.  The BAR is the terminal -- it is the free end R5 governs -- and the arc
    runs on underneath it and stops out of sight.

    Each end of the bar is taken to the ring's OUTER circle at the bar's own extreme height, not
    at its centre line, so a flat end cannot poke out of the round where the circle bulges past
    it."""
    half = rules.w_horizontal(2 * BOWL_R, 0) / 2.0
    ys = (E_BAR_Y - half, E_BAR_Y + half)
    def circ_dx(y): return math.sqrt(max(BOWL_R**2 - (y - BOWL_C[1])**2, 0.0))
    dx = min(circ_dx(y) for y in ys)            # the tighter of the two, so both corners are inside
    return BOWL_C[0] - dx, BOWL_C[0] + dx, ys


def _e_bar_edges():
    """Where the bar's two ends sit.

    The right end takes the ring's outer circle at the bar's BOTTOM edge, and its R5 cut puts
    the tip there -- so the tip lands exactly on the arc's own outer end and the two share that
    point, while the cut carries the top corner well back inside the round.  Taking the top edge
    instead pulls the end short and leaves the arc touching it at a pinch; taking a radial cut
    gives a nearly horizontal face at this angle, which reads as a blunt chop."""
    half = rules.w_horizontal(2 * BOWL_R, 0) / 2.0
    ys = (E_BAR_Y - half, E_BAR_Y + half)
    def dx(y): return math.sqrt(max(BOWL_R**2 - (y - BOWL_C[1])**2, 0.0))
    # The two ends want OPPOSITE crossings.  The left end must clear the circle at BOTH its
    # corners to stay buried, so it takes the tighter one; the right end's tip has to land on
    # the arc's outer end, so it takes the wider.  Using one for both leaves the left poking out
    # of the bowl or the right falling short of the arc.
    return BOWL_C[0] - min(dx(ys[0]), dx(ys[1])), BOWL_C[0] + max(dx(ys[0]), dx(ys[1])), ys


def _e_bar_angle():
    """The angle at which the arc stops.

    _e_bar_edges takes the bar's right end to the ring's outer circle at the bar's TOP edge --
    the tighter of its two corners.  So the arc must end at exactly that angle: its outer corner
    and the bar's top-right corner are then the SAME point, the two outlines meet there with
    nothing left over, and the bar's R5 cut is the letter's terminal.

    Burying the arc further round instead does not work, and was tried: below that angle the
    ring is further right than the bar's end, so the arc's radial cut pokes out under the bar
    as a spur."""
    _x0, _x1, ys = _e_bar_edges()
    return math.degrees(math.asin(max(-1.0, min(1.0, (ys[0] - BOWL_C[1]) / BOWL_R))))


def _e_bar_note():
    a = _e_bar_angle()
    return a


def _arc_flat_end(a1, y_cut):
    """R1's band from a HORIZONTAL cut at y_cut, counter-clockwise to a radial end at a1.

    rules.round_arc cuts both ends along rays from the centre.  At the e's terminal that ray is
    nearly horizontal but not quite, so the bowl's end does not lie flush with the bar's
    underside and the two leave a sliver.  Cutting that one end on the horizontal puts them on
    the same line."""
    c, r_out, r_in, off = BOWL_C, BOWL_R, BOWL_R - RING_W, RING_OFF
    ci = add(c, off)
    o0 = (c[0] + math.sqrt(max(r_out**2 - (y_cut - c[1])**2, 0.0)), y_cut)
    i0 = (ci[0] + math.sqrt(max(r_in**2 - (y_cut - ci[1])**2, 0.0)), y_cut)
    a0 = ang(sub(o0, c))
    start, outer = arc_segments(c, r_out, a0, a1, BAND_SEGS)
    i1 = line_circle(line_ang(c, a1), ci, r_in, pick='max')
    def _near(b, a): return a + ((b - a + 180) % 360) - 180
    _, inner = arc_segments(ci, r_in, _near(ang(sub(i1, ci)), a1),
                            _near(ang(sub(i0, ci)), a0), BAND_SEGS)
    k = Contour(start)
    for sg in outer: k.curve_to(sg[1], sg[2], sg[3])
    k.line_to(i1)
    for sg in inner: k.curve_to(sg[1], sg[2], sg[3])
    return k.ccw()


def _bar_underside(bar, x):
    """The bar's own bottom edge at x.  R4 horizontals TAPER along their length, so a bar has no
    single bottom; reading one off a nominal half-width put the bowl's cut 3.3 units below where
    the underside actually is, and the bowl showed beneath the bar."""
    below = [q for q in bar.flatten(per=1.0) if q[1] < E_BAR_Y]
    return min(below, key=lambda q: abs(q[0] - x))[1]


def _e_open():
    """Where the e's arc stops at the bottom: the SAME angle the c stops at.

    The two letters sit beside each other constantly, and what shows is where each arc ends --
    so the bottom terminals are shared and only the top differs, the c's being free and the e's
    pinned under its bar.  Giving the e its own 2 * CUT_DEG of opening instead put its lower
    terminal at -43.38 against the c's -30.90, and the pair read as two unrelated letters."""
    return C_BOT_LC


# The crossbar's shape is a WORKING DEFAULT, not a settled decision.  Five candidates were
# drawn and measured; this is the one chosen to carry on with.  The others, with their numbers,
# are recorded in the note below.
#
#   A    R4's horizontal, R5-cut, flush on the bowl.  mean 40.98, ink 11.68%.  The ONLY
#        candidate inside the face's established horizontal band -- E 40.01, F 40.68, H 41.16.
#   H2   a flipped wedge whose point starts at x 120.  mean 19.57, ink 10.14%.  Lightest, but
#        it reads as a spike and its weight is nearer the bowl's thin band (16.38) than any
#        horizontal in the face.
#   J35  tapers to 35% at the band.  mean 29.05, ink 11.10%.  Costs most of A's departure from
#        R4 without changing the letter much.
#   M2   this construction cut at x 100.  mean 30.50, ink 10.80%.
#   M3   this construction cut at x 140.  mean 29.66, ink 10.46%.  <- current default
#
# M is the only family that sheds mass by LENGTH rather than by thinness, so the bar keeps real
# weight along everything that shows; the saving comes from stopping short.  That is also its
# risk: cut this far back the bar no longer closes the counter on the left, and the e moves
# toward a c with a cross-stroke.
E_BAR_STOP  = 140.0       # where the bar's free end is cut, short of the left band
E_BAR_TAPER = 0.70        # its width there, as a fraction of the width at the bowl


def _e_bar():
    """The crossbar: full width and R5-cut flush on the bowl at the right, tapering gently
    leftward, then cut on the mark's stress axis short of the left band.

    The right end is unchanged from A -- its R5 tip sits on the ring's outer circle at the bar's
    bottom edge, which is exactly where the arc's own outer end lands, so the two meet at a
    point they both already own.  The free left end is cut at 45.07 deg, the angle R1 displaces
    the counter along and the one the Q's leg runs at."""
    x0, x1, _ys = _e_bar_edges()
    hr = rules.w_horizontal(x1 - x0, 1.0) / 2.0
    hl = hr * E_BAR_TAPER
    t5 = math.tan(math.radians(CUT_DEG))
    run = 2 * hl / math.tan(math.radians(abs(ang(RING_OFF))))
    k = Contour((E_BAR_STOP, E_BAR_Y - hl))
    k.line_to((x1, E_BAR_Y - hr))
    k.line_to((x1 - 2 * hr * t5, E_BAR_Y + hr))
    k.line_to((E_BAR_STOP + run, E_BAR_Y + hl))
    return k.ccw()


def build_e():
    """The c's arc carried round to an R4 bar."""
    bar = _e_bar()
    arc = _arc_flat_end(_e_open() + 360.0, _bar_underside(bar, _e_bar_edges()[1]))
    return glyph(ord('e'), [arc, bar], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"The c's arc carried further round -- from {_e_open():+.2f} deg, below the "
                     f"bar, all the way over the top and down to where the bar meets it at "
                     f"{_e_bar_angle():+.2f} -- and closed by an R4 horizontal at y={E_BAR_Y:.2f}.",
        bar=f"On the E's own rule (CAP/2 + HORIZ_MID/4) read at the x-height rather than the cap: "
            f"y={E_BAR_Y:.2f}.  Full width and R5-cut flush on the bowl at the right; tapering to "
            f"{E_BAR_TAPER:.0%} leftward and cut on the mark's stress axis at x={E_BAR_STOP:g}, "
            f"short of the left band.  A WORKING DEFAULT -- see the note above _e_bar for the four "
            f"alternatives and their measurements.",
        aperture=f"The lower terminal is the c's own, {C_BOT_LC:+.2f} deg, so the two letters end "
                 f"their arcs in the same place; only the top differs, the c's being free and the "
                 f"e's pinned under the bar at {_e_bar_angle():+.2f}.  That makes the e's opening "
                 f"{_e_bar_angle()-C_BOT_LC:.1f} deg against the c's {2*CUT_DEG:.1f} -- narrower, "
                 f"because the bar closes its top, which is what an e wants.",
        spacing=f"{SB_ROUND}/{SB_ROUND} (R9).",
        deviations="none from R1-R9."))


def _shift(k, dx):
    """a contour moved right by dx"""
    return k.map(lambda p: (p[0] + dx, p[1]))


def build_m():
    """The n's stroke, plus a SECOND shoulder off the middle leg.

    An m is not three posts and two arches.  It is the n's stroke -- left leg, shoulder, middle
    leg -- with a second shoulder springing from that middle leg exactly as the h's springs from
    its ascender, buried at H_BURY so the leg alone makes the foot.  Both shoulders are the same
    stroke, so the two arches are identical rather than merely similar."""
    first, e1, (xl, xr) = _hn_stroke(0.0, True, _M_RANGES, M_MID_Y, crown=True)
    second, e2, _x = _hn_stroke(H_BURY, False, _H_RANGES)
    span = xr - xl
    n = _arch_note(xl, xr + span, max(e1, e2))
    n['construction'] = (f"The n's stroke, then the h's shoulder shifted right by {span:.2f} -- the "
                         f"distance between the n's own legs -- so the m's two arches are the SAME "
                         f"stroke, not two drawings of one idea.  Three legs at x={xl:.2f}, "
                         f"{xr:.2f} and {xr+span:.2f}.")
    n['middle'] = (f"The middle leg stops at y={M_MID_Y:g}, {100*M_MID_Y/XH:.0f}% of the x-height, and "
                   f"ends in R5's own foot -- one face at {CUT_DEG:g} deg with the tip on the RIGHT, "
                   f"which is not a choice: the middle IS the first stroke's right leg, and R5 puts "
                   f"that leg's tip on the corner away from its own stroke's centre, which is the "
                   f"right.  Carrying it to the baseline gives three legs and three counters; "
                   f"stopping it higher than about 0.49 of the x-height merges the two counters into "
                   f"one 651-unit space and the letter stops reading as an m.  The capital M makes "
                   f"the same decision at 0.40 of the cap and argues it the same way.")
    n['feet'] = (f"R5, {CUT_DEG:g} deg.  The two outer feet mirror as the n's do.  The middle needs no "
                 f"foot rule of its own: the second stroke is buried at y={H_BURY:g}, above where the "
                 f"first stroke's right leg now ends, so nothing of it reaches down to union with "
                 f"that cut.")
    return glyph(ord('m'), [first, _shift(second, span)],
                 sb=(SB_STRAIGHT, SB_STRAIGHT), notes=n)


# How far along the stroke the r ends, as a fraction of the spine.  0.619 is where the arm reaches
# exactly as far as it did when the r was built as a separate stem plus an arm; the number differs
# from that build's 0.62 only because the spine now starts at the baseline rather than at H_BURY.
R_STOP = 0.619


def _r_profile(wf, ring_w, ring_off):
    """The n's WHOLE stroke -- foot, leg, shoulder -- truncated at R_STOP and given a free R5
    terminal.

    One stroke, as the n and the h are.  It was previously a rules.stem leg with the h's shoulder
    unioned on top of it, and that is wrong for the reason a union always is here: the two pieces
    draw the same left edge from different code, they disagree by fractions of a unit all the way
    up, and the leg's own R5 top cut is then left standing proud of the arm.  Measured, the leg
    contour minus the arm contour came to 258 separate slivers and the step showed at the top left.

    The truncation index comes off HN_SAMP, a constant, so the same sample ends the stroke in every
    master and the knots below stay comparable."""
    L, Rt, (xl, xr) = _hn_edges(0.0, wf, ring_w, ring_off, crown=True)
    mid = (xl + xr) / 2.0
    L, Rt = _r5_foot(L, Rt, mid, True)            # the foot, cut as the n's left foot is
    keep = int(len(L) * R_STOP)
    L, Rt = L[:keep], Rt[:keep]
    L, Rt = _r5_foot(L, Rt, mid, False)           # the arm's terminal, the one thing the r decides
    return L, Rt, (xl, xr)


def _r_ranges():
    """As _hn_ranges, for the r's truncated copy of the same crowned edge."""
    L, Rt, _x = _r_profile(_w1, rules.RING_W_1, rules.RING_OFF_1)
    rg_in = fit_ranges(Rt[::-1], [mul(t, -1) for t in _g_tan(Rt)[::-1]], HN_NSEG)
    rg = fit_ranges(L, _g_tan(L), HN_NSEG)
    return _crown_spec(L, rg, _crown_knots(0.0, _w1, rules.RING_W_1, rules.RING_OFF_1)), rg_in


_R_RANGES = _r_ranges()


def build_r():
    """The n's left leg and the start of its shoulder, stopped in a free R5 terminal.

    The r is the arch interrupted: the same leg and the same shoulder as the n, ended partway
    round instead of coming down into a second leg.  Where it ends is the letter's one decision;
    the rest is the n's."""
    L, Rt, (xl, xr) = _r_profile(w_stem, RING_W, RING_OFF)
    spec, rg_in = _R_RANGES
    rg_out = _expand_ranges(spec, _crown_knots(0.0, w_stem, RING_W, RING_OFF), len(L))
    so, eo = fit_cubics(L, _g_tan(L), tol=9e9, ranges=[tuple(r) for r in rg_out])
    si, ei = fit_cubics(Rt[::-1], [mul(x, -1) for x in _g_tan(Rt)[::-1]], tol=9e9,
                        ranges=[tuple(r) for r in rg_in])
    k = Contour(L[0])
    for sg in so: k.curve_to(*sg)
    k.line_to(Rt[-1])
    for sg in si: k.curve_to(*sg)
    n = _arch_note(xl, xr, max(eo, ei))
    n['construction'] = (f"ONE stroke, the n's own: up from the foot at x={xl:.2f}, through the "
                         f"spring, and stopped at {R_STOP:.1%} of its run instead of carrying over "
                         f"the apex and down into a second leg.  Not a stem with an arm unioned on "
                         f"-- see the note in _r_profile.")
    n['terminal'] = (f"A free R5 cut, {CUT_DEG:g} deg -- the one thing the r decides that the n "
                     f"does not.  The foot is the n's own left foot, cut by the same rule.")
    return glyph(ord('r'), [k.ccw()], sb=(SB_STRAIGHT, SB_ROUND), notes=n)


# ---- s -------------------------------------------------------------------------------
# The one lowercase letter that reuses none of the joints above -- and it does not need a new
# construction either.  The capital S is already parametric: one stroke, a quarter of an upper
# ellipse, a cubic connector carrying the inflection, a quarter of a lower ellipse, offset by
# R1's band for the direction each point faces.  The lowercase s is that spine SCALED and the
# band left ALONE.
#
# Scaled by what: the lowercase round is the capital round at
# (XH + 2*OVER_ROUND) / (CAP + 2*OVER_ROUND) = 405/720 = 0.5625 -- that is how the o relates to
# the O (r 202.5 against 360), so it is how the s relates to the S.  The band does not take that
# factor, because R1's band and counter displacement are ABSOLUTE and not proportional (SPEC 5,
# R1).  The o already carries the O's full 40.69, and so does this.
#
# The terminals stay at the same ELLIPSE PARAMETERS, 20 and -160 degrees, not at the same
# absolute heights: a parameter is what survives the scale, and it is what puts the lowercase
# aperture in the same place on the letter as the capital's.
S_K      = (XH + 2 * OVER_ROUND) / (CAP_ROUND := (700 + 2 * OVER_ROUND))
S_BODY   = SR.S_BODY * S_K          # 315.00
S_B      = SR.S_B * S_K             # 112.50, each bowl's semi-height
# The connector's handle -- how straight it runs between the two bowls.  The capital's number
# UNSCALED, alone among the spine quantities, and for the same reason the band is unscaled: what
# the connector has to do does not shrink with the letter.  At 84.38, the scaled value, the waist
# runs 11 degrees off horizontal at its flattest and the letter leans; at 150 it runs 2 degrees
# and stands up.  Swept against it afterwards, the body stays at 315 and the bowls at 112.5 --
# with a handle this long a DEEPER bowl steepens the waist again (9 degrees at 130, 15 at 145),
# which is the opposite of what it does at the short handle.
S_WAIST  = SR.S_WAIST               # 150
S_TOP    = SR.S_TOP                 # 20 deg, a parameter on the upper ellipse
S_BOT    = SR.S_BOT                 # -160 deg
S_N      = SR.S_N                   # samples per section
S_NSEG   = 39                       # cubics per edge; where they are frozen is argued below
# Where the knots are taken.  Every other glyph in this file takes them at the AXIS ORIGIN, as
# the capital S does, because that is where the mark's own measurements sit and it leaves an
# already-shipped outline untouched.  Neither reason applies to a new glyph, and the criterion
# the capital actually used -- the lowest worst-case fit over the masters -- points somewhere
# else here: the offset edges are furthest from their ellipse when the band is widest, so knots
# chosen at the TOP of the weight axis are adequate everywhere lighter while knots chosen at the
# origin strain at the top.  Measured over the 4x3 grid, worst fit by freeze point at 39 cubics:
# origin 0.500, w1.45 0.378, w2.00 0.113.  At the origin it takes 51 cubics to reach 0.210, so
# the heavy end buys a better fit with 12 fewer pieces per edge.  PUSH sits at the middle of its
# range rather than an end, where it makes almost no difference (0.103 at 0.30, 0.113 at 1.00).
S_FREEZE = (rules.WEIGHT_TOP, 0.65)
S_TOPY, S_BOTY = XH + OVER_ROUND, -OVER_ROUND


def _s_spine(ring_w=None, ring_off=None):
    """(point, unit tangent, width) from the top terminal to the bottom one.  The capital's
    construction at S_K, with R1's band unscaled."""
    A = S_BODY / 2.0
    band = lambda th: _band_at(th, ring_w, ring_off)
    wt, wl, wb, wr = band(90.0), band(180.0), band(270.0), band(0.0)
    Cu = (wl/2 + A, S_TOPY - wt/2 - S_B)                # the top a half-band below the overshoot
    Cl = (S_BODY - wr/2 - A, S_BOTY + wb/2 + S_B)       # the bottom mirrored
    out = []
    for i in range(S_N + 1):                            # upper quarter, increasing parameter
        t = S_TOP + (180.0 - S_TOP) * i / S_N; r = math.radians(t)
        out.append(((Cu[0] + A*math.cos(r), Cu[1] + S_B*math.sin(r)),
                    unit((-A*math.sin(r), S_B*math.cos(r))), band(SR._ell_nrm(A, S_B, t))))
    low = []
    for i in range(S_N + 1):                            # lower quarter, DECREASING parameter
        t = S_BOT * i / S_N; r = math.radians(t)
        low.append(((Cl[0] + A*math.cos(r), Cl[1] + S_B*math.sin(r)),
                    unit((A*math.sin(r), -S_B*math.cos(r))), band(SR._ell_nrm(A, S_B, t))))
    P0, P3 = out[-1][0], low[0][0]                      # straight down at both ends, so the
    P1, P2 = (P0[0], P0[1] - S_WAIST), (P3[0], P3[1] + S_WAIST)   # connector is tangent-continuous
    w0, w3 = out[-1][2], low[0][2]                      # with both quarters by construction
    for i in range(1, S_N):
        u = i / float(S_N); m = 1 - u
        out.append(((m**3*P0[0] + 3*m*m*u*P1[0] + 3*m*u*u*P2[0] + u**3*P3[0],
                     m**3*P0[1] + 3*m*m*u*P1[1] + 3*m*u*u*P2[1] + u**3*P3[1]),
                    unit((3*m*m*(P1[0]-P0[0]) + 6*m*u*(P2[0]-P1[0]) + 3*u*u*(P3[0]-P2[0]),
                          3*m*m*(P1[1]-P0[1]) + 6*m*u*(P2[1]-P1[1]) + 3*u*u*(P3[1]-P2[1]))),
                    w0 + (w3 - w0) * (3*u*u - 2*u**3)))
    return out + low


def _s_edges(pts):
    L = [add(p, mul(perp(d), w/2)) for p, d, w in pts]
    Rt = [sub(p, mul(perp(d), w/2)) for p, d, w in pts]
    return L, Rt


_S_RANGES = (lambda L, Rt: (fit_ranges(L, _g_tan(L), S_NSEG),
                            fit_ranges(Rt[::-1], [mul(t, -1) for t in _g_tan(Rt)[::-1]], S_NSEG))
             )(*_s_edges(_s_spine(rules.RING_W_1 * S_FREEZE[0],
                                  mul(rules.RING_OFF_1, S_FREEZE[1]))))


def build_s():
    """The capital's one stroke at 56.25%, carrying the capital's band."""
    pts = _s_spine()
    L, Rt = _s_edges(pts)
    rg_out, rg_in = _S_RANGES
    so, eo = fit_cubics(L, _g_tan(L), tol=9e9, ranges=[tuple(r) for r in rg_out])
    si, ei = fit_cubics(Rt[::-1], [mul(x, -1) for x in _g_tan(Rt)[::-1]], tol=9e9,
                        ranges=[tuple(r) for r in rg_in])
    k = Contour(L[0])
    for sg in so: k.curve_to(*sg)
    k.line_to(Rt[-1])                                   # the terminal, square to the spine
    for sg in si: k.curve_to(*sg)
    ws = [w for _, _, w in pts]
    return glyph(ord('s'), [k.ccw()], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"The capital S's spine verbatim at {S_K:.4f} -- body {S_BODY:.2f}, bowl "
                     f"semi-height {S_B:.2f}, connector handles {S_WAIST:.2f} -- which is the same "
                     f"factor the o takes from the O, (XH + 2*OVER_ROUND)/(CAP + 2*OVER_ROUND). "
                     f"Upper quarter from {S_TOP:g} deg over the top to the left extreme, cubic "
                     f"connector straight down at both ends, lower quarter round the bottom to "
                     f"{S_BOT:g} deg.",
        weight=f"R1's band for the direction each point faces, and NOT scaled: R1's band and "
               f"counter displacement are absolute, not proportional, so this carries the O's own "
               f"{_band_at(90.0):.2f} at the top, {_band_at(180.0):.2f} at the left extreme, "
               f"{_band_at(0.0):.2f} at the right, {_band_at(270.0):.2f} at the bottom, "
               f"{min(ws):.2f} at its thinnest.  Across the connector the outward side swaps, so "
               f"the width blends left-extreme to right-extreme and the thick-to-thin transition "
               f"falls on the waist -- on a cubic Hermite carrying the quarters' own end slopes, "
               f"not the capital's smoothstep, whose zero end slopes step against them and leave "
               f"a {5.9:.1f}-unit corner on the outer edge at this scale.",
        terminals=f"At ellipse PARAMETERS {S_TOP:g} and {S_BOT:g} deg, not at fixed heights: the "
                  f"parameter is what survives the scale, so the lowercase aperture sits in the "
                  f"same place on the letter as the capital's.",
        knots=f"{S_NSEG} cubics per edge, taken once at WEIGHT {S_FREEZE[0]:g} / PUSH "
              f"{S_FREEZE[1]:g} and held -- not at the axis origin; see the note by S_FREEZE.  "
              f"Worst fit {max(eo, ei):.3f}.",
        deviations="none from R1-R9."))


GLYPHS = {'o': build_o, 'a': build_a, 'b': build_b, 'c': build_c, 'd': build_d,
          'e': build_e, 'g': build_g, 'h': build_h, 'm': build_m, 'n': build_n,
          'p': build_p, 'q': build_q, 'r': build_r, 's': build_s, 'u': build_u}
