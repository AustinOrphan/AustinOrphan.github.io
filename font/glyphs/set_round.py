"""
set_round: the letters whose skeleton is a round -- C G Q S U J.

Every round is R1: an outer curve, and a counter that is the outer curve
brought in by RING_W (33.19) and then displaced by RING_OFF (19.8 units
toward 45 deg, fixed to the page), so each of these letters carries the O's
own weight and the O's own direction -- 53.0 at the lower left, 13.4 at the
upper right (R7).  C, G, Q, U and J are circles and use rules.round_arc /
rules.round_ring unchanged.  Only the S is elliptical, and its arcs are built
here from pen primitives because lib has no elliptical round; the construction
is R1's, term for term (outer ellipse, counter the same ellipse with both
semi-axes inset by RING_W and the centre displaced by RING_OFF).

Straight strokes are rules.stem / rules.horizontal, terminals are R5 cuts
through the lib constructors, and pieces that overlap are unioned at compile
(R6).

Two joins in this group are solved rather than drawn, and both come down to
the same thing: where two curves have to become one outline, put them where
they TOUCH.

  The S's waist.  The two bowls are STACKED -- centres 30 units apart in x
  and 349 in y -- because that is the only arrangement that reads as an S,
  and a stacked waist is the one place R1 will not close by itself: the two
  bowls' outward normals there are opposite, so their bands are RING_W minus
  and plus the SAME component of RING_OFF and differ by 22 units, and that
  difference vanishes only if the stroke crosses the waist rising at 45 deg,
  which is a coil.  So the whole difference is spent on ONE edge.  The lower
  edge is a true tangency, solved for: the upper bowl's semi-height is the
  value at which its outer edge touches the lower bowl's counter.  The upper
  edge is the straight line tangent to BOTH the upper counter and the lower
  bowl's outer edge -- a line tangent to two curves meets each of them
  without turning, so that edge has no corner either, and the 22 units come
  out as the straight's length.  Measured on the finished outline all three
  waist hand-offs turn 0.00 deg and the letter has no reflex vertex.

  The U's and J's stems against their rounds.  R1's displacement means a stem
  cannot be tangent to the outer circle and to the counter at once, so each
  junction takes the tangency its side allows: the stem is placed so that edge
  is tangent to its circle (not merely sitting on the circle's extreme, which
  is a different thing once R3's taper tilts the edge), and the arc is ended on
  the ray through that point, so the arc's own end IS where the stem meets it.
  On the light side the tangency is taken 0.25 units inside the round's circle
  (GRAZE) so that the two cross at 2.5 deg rather than grazing at 0, which no
  boolean can resolve, and the stem's foot stops there rather than being
  carried past it, where it would poke out of the round.  The round's own disc,
  cut by the stem's own edge, fills the rest (_fill_out on the heavy side,
  _fill_in on the light one).  Measured on the built outline the hand-offs
  close to 0.000 units; what is left is the crossing of the stem's other edge
  with the round, a change of tangent of 17-25 deg, the kink every sans-serif
  bowl has where its stem enters.

Departures from SPEC section 5, all argued in the glyphs' notes: the C's ink
falls 5.8 units short of the wide body because its aperture removes the right
extreme, and the S's waist carries one straight edge (above) plus elliptical
rather than circular bowls, which R1 allows as long as its construction is
applied to both axes, as it is.  No departure on width: every body here is
R8's own -- C G Q wide, U medium, S J narrow.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from pen import (Contour, add, sub, mul, norm, unit, perp, from_ang, ang, line, line_2pt,
                 line_circle, line_x_at_y, arc_segments, from_poly, ccw)
from metrics import CAP, OVER_ROUND, SB_STRAIGHT, SB_ROUND
from rules import (glyph, stem, diagonal, horizontal, round_arc, round_ring, w_stem, w_horizontal,
                   w_backslash, RING_W, RING_OFF, ROUND_THICK, ROUND_THIN, CUT_DEG, HORIZ_MID)

# ---- proportions (R8) and the metric lines -------------------------------------------
BODY_WIDE   = 720                 # the O's diameter: C G Q
BODY_MEDIUM = 558                 # the A's foot spread: U
BODY_NARROW = 420                 # three quarters of medium: S J
TOP, BOT    = CAP + OVER_ROUND, -OVER_ROUND      # 710 / -10, the round overshoots
G_BAR_Y     = CAP / 2 - HORIZ_MID / 4            # 338.125: the mid line reflected in the half-cap

def _band_w(th):
    """R1 band width along the radius at page angle th (deg): RING_W minus the displacement's
    component, so 53.0 at 225 deg and 13.4 at 45 deg whatever the round's size."""
    return RING_W - norm(RING_OFF) * math.cos(math.radians(th) - math.atan2(RING_OFF[1], RING_OFF[0]))

def _circ_x(c, r, y, side=1):
    """x on the circle (c, r) at height y; side +1 the right half, -1 the left."""
    return c[0] + side * math.sqrt(max(0.0, r*r - (y - c[1])**2))

def _flush_arc(bar, c, r, n=12):
    """Replace a bar's flat right end with an arc of the round's OUTER circle through the two
    corners, so the bar's end and the round's edge are one curve instead of a chord that pokes
    out at one corner and falls short at the other.  Tooling: it moves the end by at most the
    circle's sagitta over the bar's own thickness (2 units at the G)."""
    pts = bar.flatten(); xmax = max(p[0] for p in pts)
    idx = sorted(i for i, p in enumerate(pts) if abs(p[0] - xmax) < 1e-6)
    assert len(idx) == 2 and idx[1] == idx[0] + 1, idx
    ya, yb = pts[idx[0]][1], pts[idx[1]][1]          # keep the contour's own direction round the end
    arc = [(_circ_x(c, r, ya + (yb-ya)*k/n), ya + (yb-ya)*k/n) for k in range(n+1)]
    return from_poly(ccw(pts[:idx[0]] + arc + pts[idx[1]+1:]))

def _lens(l, c, r, side):
    """The piece of the disc (c, r) lying on one side of the line l: side +1 to the left of l's
    direction, -1 to the right.  Used to fill a stem's junction with a round out to the round's own
    circle, so the outline hands off between stem and round without a step (R6: overlap and union).
    Built as chord + true cubic arc: an arc_poly polygon here leaves a chain of short chords in the
    finished silhouette, which the compiler's rounding turns into a visible ripple."""
    p, v = l
    f = sub(p, c); b = 2*(f[0]*v[0] + f[1]*v[1]); cc = f[0]*f[0] + f[1]*f[1] - r*r
    disc = b*b - 4*cc
    if disc <= 0: raise ValueError('line misses the circle')
    t0, t1 = (-b - math.sqrt(disc))/2, (-b + math.sqrt(disc))/2
    P0, P1 = add(p, mul(v, t0)), add(p, mul(v, t1))
    a0, a1 = ang(sub(P0, c)), ang(sub(P1, c))
    for end in (a0 if a0 > a1 else a0 + 360.0, a0 if a0 < a1 else a0 - 360.0):
        mid = add(c, mul(from_ang((a1 + end) / 2), r))          # which way round is the piece wanted
        if (perp(v)[0]*(mid[0]-p[0]) + perp(v)[1]*(mid[1]-p[1])) * side > 0:
            k = Contour(P0); k.line_to(P1)                      # the chord, then the circle itself
            for sg in arc_segments(c, r, a1, end)[1]: k.curve_to(sg[1], sg[2], sg[3])
            return k.ccw()
    raise ValueError('no side')

# ---- the elliptical band (S only), R1 term for term ----------------------------------
def _ell_segs(C, A, B, t0, t1):
    """Cubic segments of the ellipse (centre C, semi-axes A, B) between parameters t0 -> t1
    (degrees).  An affine image of a circular arc is exact for cubics, so this is the unit
    circle's own arc_segments mapped by (x, y) -> (Cx + A x, Cy + B y)."""
    start, segs = arc_segments((0.0, 0.0), 1.0, t0, t1)
    m = lambda p: (C[0] + A*p[0], C[1] + B*p[1])
    return m(start), [('c', m(s[1]), m(s[2]), m(s[3])) for s in segs]

def _ell_pt(C, A, B, t):
    return (C[0] + A*math.cos(math.radians(t)), C[1] + B*math.sin(math.radians(t)))

def _ell_tan(C, A, B, t):
    """Direction of travel along the ellipse at parameter t, for increasing t (degrees)."""
    return ang((-A * math.sin(math.radians(t)), B * math.cos(math.radians(t))))

def _ell_arc(k, C, A, B, t0, t1):
    """Append the ellipse arc t0 -> t1 to the contour k, or start one if k is None.  The
    join to whatever k ended on is a straight line_to, so a piece that starts where the
    last one ended adds a zero-length segment and one that starts elsewhere adds a face."""
    s, segs = _ell_segs(C, A, B, t0, t1)
    k = Contour(s) if k is None else k.line_to(s)
    for sg in segs: k.curve_to(sg[1], sg[2], sg[3])
    return k

def _ell_pierce(e1, e2, w1, n=60, it=30):
    """How far the curve e1 reaches inside the ellipse e2 over the parameter window w1, measured in
    e2's own normalised radius: the minimum of ((x-C2x)/A2)^2 + ((y-C2y)/B2)^2 - 1 along e1, found
    by sampling and then Newton.  Negative exactly when e1 has crossed inside e2, so it decides the
    side of a near-tangency cleanly, which a distance (which is 0 on BOTH sides of a crossing)
    cannot.  Returns (that minimum, the parameter on e1 where it falls)."""
    (C1, A1, B1), (C2, A2, B2) = e1, e2
    def f(r):
        x, y = C1[0] + A1*math.cos(r), C1[1] + B1*math.sin(r)
        return ((x - C2[0]) / A2)**2 + ((y - C2[1]) / B2)**2 - 1.0
    lo, hi = math.radians(w1[0]), math.radians(w1[1])
    t = min(((f(lo + (hi-lo) * i / (n-1.0)), lo + (hi-lo) * i / (n-1.0)) for i in range(n)))[1]
    for _ in range(it):
        x, y = C1[0] + A1*math.cos(t), C1[1] + B1*math.sin(t)
        dx, dy = -A1*math.sin(t), B1*math.cos(t)
        ex, ey = -A1*math.cos(t), -B1*math.sin(t)
        u, v = (x - C2[0]) / A2**2, (y - C2[1]) / B2**2
        d1 = 2*(u*dx + v*dy)
        d2 = 2*(dx*dx/A2**2 + dy*dy/B2**2 + u*ex + v*ey)
        s = -d1 / d2 if d2 > 1e-15 else -d1
        t = max(lo, min(hi, t + max(-0.2, min(0.2, s))))
        if abs(s) < 1e-14: break
    return f(t), math.degrees(t)

# ---- C and G -------------------------------------------------------------------------
C_R = BODY_WIDE / 2                       # 360: the O's own radius, so C and G are the O's round
C_C = (C_R, CAP / 2)                      # centre; the outer circle spans -10 .. 710 like the O
STRESS = ang(RING_OFF)                    # 45.07 deg: the direction the O's counter is displaced
C_TILT = CUT_DEG / 2                      # the aperture's own rotation: half a cut angle, dropped so the
                                          # UPPER end lands nearer the round's right extreme -- see build_C
C_TOP, C_BOT = CUT_DEG - C_TILT, -CUT_DEG - C_TILT   # +10.3 / -30.9: the aperture still spans 2*CUT_DEG,
                                          # the A's apex angle, but sits below the horizontal, which buys
                                          # 17 units of ink and 1.8 units of terminal weight for 4 units
                                          # of aperture height

def _c_arc(a0=None, a1=None):
    """The C's arc: a round of the O's size opened on the right, both ends radial (R1).  It runs
    counter-clockwise from the top end, over the top, down the left and round the bottom to the
    bottom end, so the aperture is the wedge between a0 and a1 on the right."""
    a0 = C_TOP if a0 is None else a0
    a1 = C_BOT if a1 is None else a1
    return round_arc(C_C, C_R, a0, a1 + 360.0)

def build_C():
    arc = _c_arc()
    x_max = C_C[0] + C_R * math.cos(math.radians(C_TOP))
    return glyph(ord('C'), [arc], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"One R1 arc (rules.round_arc) of the O's own round: outer circle r={C_R:g} centred at "
                     f"{C_C}, spanning {BOT} to {TOP} like the O, counter brought in by RING_W and displaced by "
                     f"RING_OFF, opened on the right between the radial ends at {C_TOP:+.2f} and {C_BOT:+.2f} deg.",
        aperture=f"The aperture spans {2*CUT_DEG:.1f} deg -- twice CUT_DEG, R5's own cut angle, which is the "
                 f"A's apex angle and the face's one angular constant -- and it is rotated {C_TILT:.2f} deg "
                 f"(half a cut angle) BELOW the horizontal, so the ends stand at {C_TOP:+.2f} and "
                 f"{C_BOT:+.2f} rather than at +-{CUT_DEG:g}.  The rotation is what a C wants anyway: the "
                 f"upper terminal reaches further round than the lower one, as it does in most C's.  It also "
                 f"buys on every count the symmetric pair was weak on -- ink {C_R*(1+math.cos(math.radians(CUT_DEG))):.1f} "
                 f"-> {x_max:.1f}, upper terminal {_band_w(CUT_DEG):.1f} -> {_band_w(C_TOP):.1f} -- for "
                 f"{360*(math.sin(math.radians(CUT_DEG))-math.sin(math.radians(-CUT_DEG))) - 360*(math.sin(math.radians(C_TOP))-math.sin(math.radians(C_BOT))):.0f} "
                 f"units of aperture height, which stays at "
                 f"{360*(math.sin(math.radians(C_TOP))-math.sin(math.radians(C_BOT))):.0f}.  Drawn and set "
                 f"aside: the pair on the mark's stress axis ({STRESS:+.2f}/{-STRESS:+.2f}, the direction "
                 f"RING_OFF displaces the counter), which puts the upper end at exactly the O's thin stroke "
                 f"({_band_w(STRESS):.1f}) and cuts the ink to "
                 f"{C_R*(1+math.cos(math.radians(STRESS))):.0f}, 85% of the O -- beside the O in COCOA that C "
                 f"read visibly narrower than its own width class; the symmetric +-{CUT_DEG:g} pair (ink "
                 f"{C_R*(1+math.cos(math.radians(CUT_DEG))):.0f}); and a full CUT_DEG of tilt, which lands the "
                 f"upper end on the right extreme (ink {2*C_R:.0f} exactly) but drops the whole aperture below "
                 f"the middle and reads as a nicked O.",
        terminals=f"Both ends are R1 radial cuts (R5: partial rounds end in radial cuts), so their length is "
                  f"whatever the band is at that angle: {_band_w(C_TOP):.1f} at the upper end, "
                  f"{_band_w(C_BOT):.1f} at the lower (R7, heavy toward the lower left).  The upper terminal "
                  f"is DECIDED, not left over.  It is the aperture's tilt that decides it, and the tilt was "
                  f"read off the four values of C_TILT that the face's own angle offers -- 0, CUT_DEG/4, "
                  f"CUT_DEG/2 and CUT_DEG give upper terminals of {_band_w(CUT_DEG):.1f}, "
                  f"{_band_w(CUT_DEG*0.75):.1f}, {_band_w(C_TOP):.1f}, {_band_w(0.0):.1f} against apertures "
                  f"of 253, 252, {360*(math.sin(math.radians(C_TOP))-math.sin(math.radians(C_BOT))):.0f} and "
                  f"237 units of height.  CUT_DEG/2 is the last one whose aperture still straddles the "
                  f"middle of the letter; a full CUT_DEG drops the whole aperture below it.  At "
                  f"{_band_w(C_TOP):.1f} the upper "
                  f"terminal is still the lightest face in the letter and vanishes below about 30 px -- so "
                  f"does the O's own upper right, which is {ROUND_THIN:.1f}, and that is the face.",
        width=f"R8 gives C the wide body, the O's {BODY_WIDE}, measured outer extreme to outer extreme.  A C "
              f"that keeps the O's own circle cannot reach it exactly -- whatever the aperture, the right "
              f"extreme is cut away -- so the ink comes out {x_max:.1f}, {BODY_WIDE - x_max:.1f} units "
              f"({(BODY_WIDE - x_max)/BODY_WIDE*100:.1f}%) short of the O's diameter, and the advance follows "
              f"the ink (R9).  That shortfall is now smaller than the C's own overshoot and smaller than a "
              f"stroke's rounding: a C this close to the O is the usual optical relationship.",
        spacing=f"{SB_ROUND}/{SB_ROUND}: a round on the left, the arc's ends on the right.",
        deviations=f"R8 (minor, disclosed): the ink is {x_max:.1f}, {BODY_WIDE - x_max:.1f} short of the wide "
                   f"body's {BODY_WIDE}, because the aperture removes the right extreme; see 'width'.  "
                   f"Nothing else.",
        geometry=dict(centre=C_C, r_out=C_R, r_in=C_R - RING_W, arc_deg=(C_TOP, C_BOT), ink_width=x_max,
                      terminal_w=(_band_w(C_TOP), _band_w(C_BOT)))))

G_TIP_X = 560.0                           # left tip of the G's bar

def _g_parts(tip_x=None):
    """The G: the C's round carried on round to the bar's height, closed by an R4 bar."""
    tip_x = G_TIP_X if tip_x is None else tip_x
    a1 = 360.0 + math.degrees(math.asin((G_BAR_Y - C_C[1]) / C_R))     # where the arc reaches the bar
    x_right = _circ_x(C_C, C_R, G_BAR_Y)
    arc = round_arc(C_C, C_R, C_TOP, a1)
    bar = _flush_arc(horizontal(tip_x, x_right, G_BAR_Y, left='up'), C_C, C_R)
    return arc, bar, a1, x_right

def build_G():
    arc, bar, a1, x_right = _g_parts()
    L = x_right - G_TIP_X
    counter_x = C_C[0] + RING_OFF[0] + math.sqrt((C_R - RING_W)**2 - (G_BAR_Y - C_C[1] - RING_OFF[1])**2)
    w_end = w_horizontal(L, 1)
    flush = max(abs(x_right - _circ_x(C_C, C_R, G_BAR_Y + w_end * (k/40.0 - 0.5))) for k in range(41))
    ink = max(p[0] for c in (arc, bar) for p in c.flatten()) - min(p[0] for c in (arc, bar) for p in c.flatten())
    return glyph(ord('G'), [arc, bar], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"The C's round (same centre, same r={C_R:g}, same top end at {C_TOP:+.2f} deg) carried on "
                     f"counter-clockwise past the right extreme to {a1 - 360:+.2f} deg, where the outer circle "
                     f"is at the bar's centre-line, plus one R4 bar (rules.horizontal) from a free R5 tip at "
                     f"x={G_TIP_X:g} to the outer circle at x={x_right:.1f}.  No stem under the bar: the round "
                     f"itself already runs down the right side to the baseline, so a stem would only double it.",
        bar=f"centre-line y={G_BAR_Y:.3f} = CAP/2 - HORIZ_MID/4, the face's mid line (E's middle arm, H's bar) "
            f"reflected in the half-cap, so the G's bar sits as far below centre as that line sits above it and "
            f"the bowl stays the larger opening.  R4 widths over its own length {L:.1f}: "
            f"{w_horizontal(L, 0):.1f} at the tip to {w_horizontal(L, 1):.1f} at the round (R7).  It crosses the "
            f"counter at x={counter_x:.1f}, so {counter_x - G_TIP_X:.0f} units of it read inside the bowl.",
        tip=f"R5 cut, body 'up': the bar's centre-line is below the letter's centre, so the corner farther from "
            f"the centre is the lower one and the tip sits there, the cut rising to the right (R5, R7).",
        joins=f"The arc's radial end at {a1 - 360:+.2f} deg lies inside the bar (the bar is "
              f"{w_horizontal(L, 1):.1f} thick there against the band's {_band_w(a1):.1f}), so it is never seen. "
              f"The bar's right end is reshaped to the outer circle itself (_flush_arc), which moves it by at "
              f"most {flush:.3f} units -- the largest |bar end x - circle x| over the whole "
              f"{w_end:.1f}-unit end, not a signed value at one height: at the bar's height the circle is all "
              f"but vertical, so the silhouette runs from the round into the bar's end and out along its top "
              f"edge without a step.",
        width=f"The bar carries the G out to the round's own right extreme, so the G is the full R8 wide body: "
              f"ink {ink:.1f} against the O's {BODY_WIDE}.",
        spacing=f"{SB_ROUND}/{SB_ROUND}: round on the left, round on the right.",
        deviations="none from R1-R9.",
        geometry=dict(centre=C_C, r_out=C_R, arc_deg=(C_TOP, a1 - 360), bar_y=G_BAR_Y, bar_x=(G_TIP_X, x_right))))


# ---- Q -------------------------------------------------------------------------------
Q_TAIL_DEG = -STRESS                      # the tail's direction: the mark's stress axis, mirrored
Q_TAIL_END_Y = 0.0                        # the tail's tip lands on the baseline

def _q_tail(deg=None, end_y=None):
    """The Q's tail: an R2 '\\' diagonal leaving the ring at the lower right.  Its buried upper end
    is the chord tangent to the counter circle, so the tail springs from the ring's inner edge and
    nothing of it is ever seen inside the counter; its lower end is a free R5 cut."""
    deg = Q_TAIL_DEG if deg is None else deg
    end_y = Q_TAIL_END_Y if end_y is None else end_y
    u = from_ang(deg)
    ci, ri = add(C_C, RING_OFF), C_R - RING_W
    p1 = add(ci, mul(u, ri))                                  # tangent point on the counter
    # R2's p0 is the CENTRE-LINE end; the R5 tip is half a width off it, on the lower-left side, so the
    # centre-line end is solved (fixed point, the width follows its own height) to put the tip on end_y.
    n = perp(u)
    y0 = end_y
    for _ in range(20):
        y0 = end_y + n[1] * w_backslash(y0) / 2
    p0 = add(p1, mul(u, (y0 - p1[1]) / u[1]))
    tail = diagonal(p0, p1, bottom='right', top=None)
    assert abs(min(q[1] for q in tail.flatten()) - end_y) < 1e-6, tail.bbox()
    return tail, p0, p1, u



# ---- S -------------------------------------------------------------------------------
# The S is two R1 rounds STACKED, not offset along the stress axis, because that is the only
# arrangement that reads as an S.  What R1 will not give it is a waist whose two edges are both
# tangent: at a smooth waist the two bowls' outward normals are opposite, so their bands are
# RING_W -+ the same displacement component and differ by 2*|RING_OFF|*|cos(waist tilt + 45)|,
# which vanishes only when the stroke crosses the waist rising at 45 deg -- and a stroke rising
# at 45 deg through the middle of an S turns the letter into two hooks (the previous drawing of
# this glyph did exactly that and read "S" as a coil).  So the waist takes the step, and it is
# spent on ONE edge and hidden as a straight: the lower edge is a true tangency between the
# upper bowl's outer edge and the lower bowl's counter, and the upper edge is the straight line
# tangent to BOTH the upper counter and the lower bowl's outer edge.  Neither hand-off turns a
# corner; the whole difference between the two bands shows up as the length of that straight,
# which is the S's spine and reads as one.
S_BODY   = BODY_NARROW            # 420, R8's own narrow width for S -- no departure
S_A      = 195.0                  # each bowl's outer semi-width: the bowls span 390 of the 420 body,
                                  # so their centres sit 30 apart in x (the upper bowl holds the left
                                  # extreme, the lower the right) and the waist runs nearly level
S_BL     = 210.0                  # the lower bowl's outer semi-height; the upper bowl's is solved
S_TOP_T, S_BOT_T = 30.0, 210.0    # the two terminals, as parameters on their own bowls
S_WAIST  = (200.0, 340.0)         # where round the upper bowl the waist is looked for

def _s_bowls(a, b_u, b_l):
    """The S's four ellipses: each bowl's outer ellipse and, per R1, its counter -- the same ellipse
    with BOTH semi-axes brought in by RING_W and the centre displaced by RING_OFF.  The upper bowl
    touches the cap overshoot and the left extreme, the lower the baseline overshoot and the right."""
    Cu, Cl = (a, TOP - b_u), (S_BODY - a, BOT + b_l)
    return dict(Uo=(Cu, a, b_u), Ui=(add(Cu, RING_OFF), a - RING_W, b_u - RING_W),
                Lo=(Cl, a, b_l), Li=(add(Cl, RING_OFF), a - RING_W, b_l - RING_W))

def _ell_param(e, P):
    """The parameter (degrees) of a point that lies on the ellipse e."""
    (C, A, B) = e
    return math.degrees(math.atan2((P[1] - C[1]) / B, (P[0] - C[0]) / A)) % 360.0

def _s_solve_b_u(a, b_l, lo=60.0, hi=420.0, it=60):
    """The upper bowl's semi-height, solved so that its OUTER edge is tangent to the lower bowl's
    counter.  That pair is the waist's lower edge, and tangency is what lets the outline hand off
    from one bowl to the other there without a step or a corner.  Bisection on the pierce depth,
    which is signed (negative once the upper bowl has crossed inside the lower counter) and so
    decides the side of a tangency, where a distance would read 0 on both."""
    for _ in range(it):
        m = (lo + hi) / 2
        if _ell_pierce(_s_bowls(a, m, b_l)['Uo'], _s_bowls(a, m, b_l)['Li'], S_WAIST)[0] > 0: lo = m
        else: hi = m
    return (lo + hi) / 2

def _s_sep_tangent(e1, e2, n=1440):
    """The straight that bridges the waist's UPPER edge: the line tangent to both the upper counter
    e1, which stays above it, and the lower bowl's outer edge e2, which stays below it.  Solved on
    the support function -- for a unit normal nu the tangent to (C, A, B) on the far side is at
    C.nu -+ hypot(A nu_x, B nu_y) -- by scanning nu's direction for a sign change and bisecting.
    Returns (nu's angle, contact on e1, contact on e2) for the tangent that descends to the right,
    i.e. the one whose contacts are in the order the outline needs them."""
    (C1, A1, B1), (C2, A2, B2) = e1, e2
    def gap(deg):
        nu = from_ang(deg)
        return ((C1[0]*nu[0] + C1[1]*nu[1] - math.hypot(A1*nu[0], B1*nu[1]))
                - (C2[0]*nu[0] + C2[1]*nu[1] + math.hypot(A2*nu[0], B2*nu[1])))
    def contacts(deg):
        nu = from_ang(deg)
        h1, h2 = math.hypot(A1*nu[0], B1*nu[1]), math.hypot(A2*nu[0], B2*nu[1])
        return ((C1[0] - A1*A1*nu[0]/h1, C1[1] - B1*B1*nu[1]/h1),
                (C2[0] + A2*A2*nu[0]/h2, C2[1] + B2*B2*nu[1]/h2))
    out, prev = [], gap(0.0)
    for i in range(1, n + 1):
        d = 180.0 * i / n; v = gap(d)
        if prev * v < 0:
            a, b = 180.0 * (i - 1) / n, d
            for _ in range(80):
                m = (a + b) / 2
                if gap(m) * prev > 0: a = m
                else: b = m
            out.append(((a + b) / 2,) + contacts((a + b) / 2))
        prev = v
    good = [t for t in out if t[1][0] < t[2][0]]          # e1's contact left of e2's: the descending one
    if not good: raise ValueError('the upper counter and the lower bowl are not separated')
    return good[0]

_S_SOLVED = []
def _s_solve():
    """Everything the S's outline needs, solved once: the four ellipses, the tangency that closes the
    waist's lower edge, and the straight that closes its upper edge."""
    if _S_SOLVED: return _S_SOLVED[0]
    b_u = _s_solve_b_u(S_A, S_BL)
    e = _s_bowls(S_A, b_u, S_BL)
    d, t_xu = _ell_pierce(e['Uo'], e['Li'], S_WAIST)          # the waist's lower edge: Uo touches Li
    PX = _ell_pt(*e['Uo'], t_xu); t_xl = _ell_param(e['Li'], PX)
    a_nu, T1, T2 = _s_sep_tangent(e['Ui'], e['Lo'])           # the waist's upper edge: the straight
    g = dict(e=e, b_u=b_u, pierce=d, t_xu=t_xu, t_xl=t_xl, PX=PX,
             nu=a_nu, T1=T1, T2=T2, g_u=_ell_param(e['Ui'], T1), g_l=_ell_param(e['Lo'], T2))
    assert S_WAIST[0] + 2 < t_xu < S_WAIST[1] - 2, t_xu       # the tangency is at the waist, not at
    assert abs(d) < 1e-6, d                                   # a window's edge, and it really closes
    _S_SOLVED.append(g)
    return g

def _up(t, base):   return t + 360.0 * math.ceil((base - t) / 360.0 - 1e-12)     # smallest >= base
def _down(t, base): return t - 360.0 * math.ceil((t - base) / 360.0 - 1e-12)     # largest <= base

def _s_contour(g):
    """The S as ONE closed contour, four arcs and three straights.  Round from the top terminal down
    the upper bowl's outer edge to the waist; across the waist's lower edge, which is a tangency, so
    that straight has zero length; down the lower bowl's counter to the bottom terminal; across the
    bottom terminal's radial face; back up the lower bowl's outer edge to the tangent point; along
    the straight that bridges the waist's upper edge; up the upper bowl's counter to the top
    terminal; across its radial face."""
    e = g['e']
    k = _ell_arc(None, *e['Uo'], S_TOP_T, _up(g['t_xu'], S_TOP_T))
    k = _ell_arc(k, *e['Li'], g['t_xl'], _down(S_BOT_T, g['t_xl']))
    k = _ell_arc(k, *e['Lo'], _down(S_BOT_T, g['t_xl']), _up(g['g_l'], _down(S_BOT_T, g['t_xl'])))
    k = _ell_arc(k, *e['Ui'], _up(g['g_u'], S_TOP_T), S_TOP_T)
    return k.ccw()

def _turn(a, b):
    """The outline's change of direction at a corner, from direction a to direction b (degrees)."""
    return (b - a + 180.0) % 360.0 - 180.0

def _s_corners(g, sgn):
    """Every corner of the S's outline, as (name, turn in degrees) with the sign the finished
    (counter-clockwise) contour has: positive convex, negative reflex.  Directions are read off the
    curves themselves -- an ellipse's tangent at the parameter, reversed where the outline runs the
    parameter backwards, and the chord's own direction for each straight."""
    e = g['e']
    fwd  = lambda k, t: _ell_tan(*e[k], t)
    back = lambda k, t: _ell_tan(*e[k], t) + 180.0
    top_face = ang(sub(_ell_pt(*e['Uo'], S_TOP_T), _ell_pt(*e['Ui'], S_TOP_T)))
    bot_face = ang(sub(_ell_pt(*e['Lo'], S_BOT_T), _ell_pt(*e['Li'], S_BOT_T)))
    bridge   = ang(sub(g['T1'], g['T2']))
    return [('waist, lower edge (upper bowl outer -> lower counter)',
             sgn * _turn(fwd('Uo', g['t_xu']), back('Li', g['t_xl']))),
            ('bottom terminal, counter corner', sgn * _turn(back('Li', S_BOT_T), bot_face)),
            ('bottom terminal, outer corner',   sgn * _turn(bot_face, fwd('Lo', S_BOT_T))),
            ('waist, upper edge: lower bowl outer -> the straight',
             sgn * _turn(fwd('Lo', g['g_l']), bridge)),
            ('waist, upper edge: the straight -> upper counter',
             sgn * _turn(bridge, back('Ui', g['g_u']))),
            ('top terminal, counter corner', sgn * _turn(back('Ui', S_TOP_T), top_face)),
            ('top terminal, outer corner',   sgn * _turn(top_face, fwd('Uo', S_TOP_T)))]

def build_S():
    g = _s_solve(); e = g['e']
    (Cu, au, bu), (Cl, al, bl) = e['Uo'], e['Lo']
    raw = _s_contour(g); k = raw.ccw()
    corners = _s_corners(g, 1.0 if raw.area() > 0 else -1.0)
    reflex = [f"{n} {t:+.2f}" for n, t in corners if t < -0.001]
    w_up = norm(sub(_ell_pt(*e['Uo'], g['t_xu']), _ell_pt(*e['Ui'], g['t_xu'])))
    w_lo = norm(sub(_ell_pt(*e['Lo'], g['t_xl']), _ell_pt(*e['Li'], g['t_xl'])))
    w_top = norm(sub(_ell_pt(*e['Uo'], S_TOP_T), _ell_pt(*e['Ui'], S_TOP_T)))
    w_bot = norm(sub(_ell_pt(*e['Lo'], S_BOT_T), _ell_pt(*e['Li'], S_BOT_T)))
    bridge = norm(sub(g['T1'], g['T2'])); b_ang = ang(sub(g['T2'], g['T1']))
    u = perp(unit(sub(g['T2'], g['T1'])))
    waist = abs(u[0]*(g['PX'][0]-g['T1'][0]) + u[1]*(g['PX'][1]-g['T1'][1]))
    return glyph(ord('S'), [k], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"Two R1 rounds STACKED and traced as ONE closed contour.  Upper bowl: outer ellipse "
                     f"semi-axes ({au:.1f}, {bu:.1f}) centred {tuple(round(v,1) for v in Cu)}, touching the cap "
                     f"overshoot {TOP:g} and the left extreme.  Lower bowl: ({al:.1f}, {bl:.1f}) centred "
                     f"{tuple(round(v,1) for v in Cl)}, touching the baseline overshoot {BOT:g} and the right "
                     f"extreme.  Both are ellipses with R1 applied term for term -- outer ellipse; counter the "
                     f"same ellipse with BOTH semi-axes brought in by RING_W={RING_W:.2f} and the centre "
                     f"displaced by RING_OFF -- so the stroke still runs {ROUND_THICK:.1f} at the lower left to "
                     f"{ROUND_THIN:.1f} at the upper right as in the O.  The centres are {Cl[0]-Cu[0]:.0f} apart "
                     f"in x and {Cu[1]-Cl[1]:.0f} in y: a stack, not a diagonal, so each bowl carries about "
                     f"{2*au/S_BODY*100:.0f}% of the body's width and the arcs are "
                     f"{_up(g['t_xu'], S_TOP_T)-S_TOP_T:.0f} deg (upper) and "
                     f"{_up(g['g_l'], _down(S_BOT_T, g['t_xl']))-_down(S_BOT_T, g['t_xl']):.0f} deg (lower), "
                     f"each opening sideways -- the upper to the right, the lower to the left.",
        waist=f"R1 cannot make both edges of a stacked waist tangent.  At a smooth waist the two bowls' "
              f"outward normals are opposite, so their bands are RING_W minus and plus the SAME component of "
              f"RING_OFF and differ by 2*|RING_OFF|*|cos(waist tilt + 45 deg)| -- zero only when the stroke "
              f"crosses the waist rising at 45 deg, which is a coil, not an S.  Here the upper band is "
              f"{w_up:.1f} at the hand-off and the lower {w_lo:.1f}, a difference of {w_up-w_lo:.1f}, and the "
              f"whole of it is spent on ONE edge: the LOWER edge is a true tangency (the upper bowl's outer "
              f"edge touching the lower bowl's counter, closed by the solve to {abs(g['pierce']):.1e} in the "
              f"lower counter's own normalised radius, {abs(g['pierce'])*al/2:.4f} units), and the UPPER edge "
              f"is the straight line tangent to BOTH the upper counter and the lower bowl's outer edge.  A "
              f"line tangent to both meets each without turning, so neither hand-off is a corner "
              f"(measured: {corners[0][1]:+.2f}, {corners[3][1]:+.2f}, {corners[4][1]:+.2f} deg); the "
              f"difference between the bands comes out as the straight's LENGTH, {bridge:.0f} units at "
              f"{b_ang:.1f} deg, from {tuple(round(v) for v in g['T2'])} to "
              f"{tuple(round(v) for v in g['T1'])}.  That straight is the S's spine and reads as one.  The "
              f"ink across the waist -- the tangency point to the straight -- is {waist:.1f}.",
        corners=f"Every corner of the finished contour, measured on the outline itself as the change of "
                f"direction from the incoming edge to the outgoing one (positive convex, negative reflex): "
                + "; ".join(f"{n} {t:+.2f} deg" for n, t in corners) + ".  "
                + (f"REFLEX VERTICES: {'; '.join(reflex)}." if reflex else
                   "No reflex vertex anywhere; the four right-angled corners are the two free terminals' "
                   "radial faces, which R1 asks for, and the three waist hand-offs are tangent to within "
                   "the solver's own residual."),
        terminals=f"Ends at parameters {S_TOP_T:g} on the upper bowl (upper right) and {S_BOT_T:g} on the "
                  f"lower (lower left), each cut on the chord between outer edge and counter at that "
                  f"parameter -- R1's radial cut, which under the affine map that makes the ellipse is a "
                  f"chord at constant parameter.  R1's widths put {w_top:.1f} at the top terminal and "
                  f"{w_bot:.1f} at the bottom one (R7: light upper right, heavy lower left).  The pair leaves "
                  f"the upper bowl open over {360 - (_up(g['t_xu'], S_TOP_T) - S_TOP_T):.0f} deg to the right "
                  f"and the lower open over "
                  f"{360 - (_up(g['g_l'], _down(S_BOT_T, g['t_xl'])) - _down(S_BOT_T, g['t_xl'])):.0f} deg to "
                  f"the left, the two apertures facing opposite ways as an S's must.  THE ONE READING THE "
                  f"RULES LEAVE OPEN in this letter: the pair itself.  20/200, 30/195, 40/220, 45/225 and "
                  f"15/185 were all drawn and read; every one of them is legible, and 30/210 is kept because "
                  f"it is the pair that leaves both terminals pointing squarely out of the letter -- 20/200 "
                  f"curls the upper one down into its own counter and 45/225 opens the upper aperture past "
                  f"the C's.",
        proportion=f"Body {S_BODY:g}, R8's own narrow width -- the previous drawing of this letter took the "
                   f"medium {BODY_MEDIUM:g} because its bowls, solved for a doubly tangent waist, came out "
                   f"barely half the body wide and needed the room; stacked bowls do not.  The two free "
                   f"numbers are the bowls' semi-width ({S_A:g}, the same for both, so the centres sit "
                   f"{S_BODY - 2*S_A:g} apart in x) and the lower bowl's semi-height ({S_BL:g}); the upper "
                   f"bowl's semi-height ({bu:.2f}) is solved, not chosen, by the waist's lower tangency.  "
                   f"The lower bowl is the taller of the two ({bl/bu:.2f}x), so the waist sits above the "
                   f"middle at y={g['PX'][1]:.0f} and the lower counter is the larger, as R7 asks.",
        spacing=f"{SB_ROUND}/{SB_ROUND}: round on both sides.",
        deviations=f"None on width: the body is R8's narrow {S_BODY:g}.  Two, both inside R1 and both "
                   f"argued above.  First, the bowls are ellipses rather than circles, which R1 allows as "
                   f"long as its construction is applied to both axes, as it is; lib has no elliptical band, "
                   f"so the arcs are built here from pen's arc_segments under an affine map (exact for "
                   f"cubics).  Second, the waist's upper edge is a straight tangent to both curves rather "
                   f"than a curve-to-curve hand-off, because R1's absolute displacement leaves the two bands "
                   f"{w_up-w_lo:.1f} units apart there and no stacked arrangement can close that; the "
                   f"straight is the cheapest thing that closes it without a corner.",
        geometry=dict(upper=dict(centre=Cu, a=au, b=bu), lower=dict(centre=Cl, a=al, b=bl),
                      waist=dict(tangency=g['PX'], t_upper=g['t_xu'], t_lower=g['t_xl'],
                                 bands=(w_up, w_lo), ink=waist,
                                 straight=dict(fr=g['T2'], to=g['T1'], length=bridge, deg=b_ang)),
                      corners=corners)))

def build_Q():
    tail, p0, p1, u = _q_tail()
    ring = round_ring(C_C, C_R)
    w0, w1 = w_backslash(p0[1]), w_backslash(p1[1])
    exit_p = line_circle(line(p1, u), C_C, C_R, pick='max')
    return glyph(ord('Q'), ring + [tail], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"The O's ring, verbatim (rules.round_ring, r={C_R:g} centred {C_C}: same circle, same "
                     f"counter, same displacement), plus one R2 tail crossing the band at the lower right.",
        tail=f"An R2 '\\\\' diagonal (rules.diagonal, so its width is R2's field at its own heights: "
             f"{w1:.1f} where it leaves the counter, {w0:.1f} at the tip) running at {Q_TAIL_DEG:.2f} deg.  That "
             f"is the mark's own stress axis -- the 45.07 deg direction the O's counter is displaced along -- "
             f"mirrored in the horizontal, the only slope the mark offers besides the A's legs, and the legs "
             f"(68.7 deg from the horizontal) are far too steep to read as a tail rather than a second leg.",
        tail_ends=f"The buried upper end is the chord tangent to the COUNTER circle at "
                  f"{tuple(round(v, 1) for v in p1)} (a chord {w1:.1f} long stands {w1**2/(8*(C_R-RING_W)):.2f} "
                  f"units off the arc, so nothing of the tail is ever seen inside the counter and none of the "
                  f"counter is bitten into); it crosses the outer circle at "
                  f"{tuple(round(v, 1) for v in exit_p)} and {norm(sub(p0, exit_p)):.0f} units of tail are "
                  f"visible outside the ring.  R2's p0 is a centre-line end, so it is solved to put the R5 TIP exactly "
                  f"on the baseline (checked): the Q keeps the face's "
                  f"cap-to-baseline span and needs no descender.",
        tail_cut=f"R5, {CUT_DEG:g} deg off the horizontal.  The tail is all but radial to the ring, so R5's "
                 f"'corner farther from the letter's centre' does not decide the side (the two corners are "
                 f"{norm(sub(add(p0, mul(perp(u), w0/2)), C_C)):.0f} and "
                 f"{norm(sub(sub(p0, mul(perp(u), w0/2)), C_C)):.0f} units out); R7 does, as it does for the I "
                 f"in set_straight: the tip is kept at the lower-left corner and the upper-right corner is cut "
                 f"away.",
        spacing=f"{SB_ROUND}/{SB_ROUND}: the ring on the left, the tail's R5 tip on the right.  The tail carries "
                f"the right extreme {max(q[0] for q in tail.flatten()) - (C_C[0] + C_R):.0f} units past the ring, "
                f"so the Q's advance is that much wider than the O's.",
        deviations="none from R1-R9.",
        geometry=dict(centre=C_C, r_out=C_R, tail=dict(deg=Q_TAIL_DEG, buried_end=p1, tip=p0, w=(w1, w0)))))


# ---- U and J -------------------------------------------------------------------------
U_R  = BODY_MEDIUM / 2                     # 279: the half round's outer radius
U_C  = (U_R, BOT + U_R)                    # centre; the round sits on the baseline overshoot
J_R  = BODY_NARROW / 2                     # 210
J_C  = (J_R, BOT + J_R)
J_END = 165.0                              # the hook's free radial end, a little above the left extreme
BURY = 20.0                                # how far a stem's flat end runs on past the junction, buried
OVERLAP = 1.0                              # how far a fill reaches into the stem it abuts, so the union
                                           # never has to resolve two contours that only touch along a line

def _stem_edge(x_c, side, y0=0.0, y1=CAP):
    """The line of an R3 stem's left (-1) or right (+1) edge.  Stems taper, so it is not vertical."""
    return line_2pt((x_c + side * w_stem(y0) / 2, y0), (x_c + side * w_stem(y1) / 2, y1))

def _stem_tangent_x(c, r, edge, at_left):
    """The stem centre x at which the stem's `edge` (-1 its left edge, +1 its right) runs TANGENT to
    the circle (c, r), the circle's centre lying to the left of that edge (at_left +1) or to its
    right (-1).  R3's stems taper, so a stem edge is not vertical and tangency is not the same thing
    as putting the edge on the circle's extreme: setting the edge on the extreme leaves the two
    curves a fraction of a unit apart everywhere else, which is a small step in the finished outline
    (0.6 units on the U's counter, 1.1 on the J's silhouette).  Solving for the tangency instead
    makes the hand-off exact -- no step and no change of tangent at the point they touch."""
    p, v = _stem_edge(0.0, edge)
    n = perp(v)                                     # points to the left of the edge's direction (up)
    d0 = n[0] * (c[0] - p[0]) + n[1] * (c[1] - p[1])
    return (d0 - at_left * r) / n[0]

def _stem_x_on_extreme(c, r, side, inner=False):
    """The placement this module used before _stem_tangent_x: a stem's edge set ON the circle's own
    extreme rather than tangent to the circle.  Kept only so the notes can say what the difference
    between the two is worth in units."""
    if inner: return c[0] + RING_OFF[0] + side * (r - RING_W + w_stem(c[1]) / 2)
    return c[0] + side * (r - w_stem(c[1]) / 2)

GRAZE = 0.25    # how far INSIDE its circle a stem's edge is set tangent at a junction.  Tangent to
                # the circle itself is the exact answer geometrically, but a tangent line lies
                # outside its circle everywhere but the one touch point, so stem and round would
                # meet at a zero-angle contact and overlap in nothing -- which a boolean union
                # cannot resolve (fontforge's overlap remover fails outright: "winding number did
                # not return to 0" on the J, and a zero-area spike on the U's counter).  Set tangent
                # 0.25 units inside instead and the stem's edge CROSSES its circle at a real angle,
                # sqrt(2*GRAZE/r) = 2.4 to 2.8 deg here, with area to spare on both sides of it.
                # The hand-off stays stepless, because the arc is ended exactly at that crossing;
                # what the 0.25 costs is that much bite into the counter on the heavy side, over
                # about 11 units of the stem's run -- 0.06 px at the 240 px proof.

def _light_junction(c, r, side):
    """The junction where the round's band is NARROWER than the stem (the light, upper-right side).
    Returns the stem's centre x, the ray the round's arc must end on, and the height the stem's
    buried foot stops at.  The stem's outer edge is set tangent to the circle GRAZE units inside the
    round's own, so it crosses the round's circle at a shallow but real angle; the arc is ended on
    the ray through that crossing, so the silhouette hands off with no step; and the foot stops at
    the inner circle's tangency, which is inside the round's circle, so no ink pokes out of the
    silhouette (the old foot, carried 20 units past the junction, poked out by about a unit)."""
    x = _stem_tangent_x(c, r - GRAZE, side, side)
    q = line_circle(_stem_edge(x, side), c, r, pick='max')     # the upper of the two crossings
    return x, ang(sub(q, c)), _touch_y(_touch_deg(x, side, c, r - GRAZE, c), c, r - GRAZE)

def _heavy_junction(c, r, side):
    """The junction where the round's band is WIDER than the stem (the heavy, lower-left side).
    Returns the stem's centre x and the ray the round's arc must end on.  The mirror of
    _light_junction: the stem's inner edge is set tangent to the circle GRAZE units inside the
    COUNTER's, so it crosses the counter at a real angle (2.6 deg) instead of grazing it -- an
    exact tangency there leaves the union a zero-area spike at the touch point -- and the arc is
    ended on the ray through that crossing, so the counter hands off with no step.  The stem bites
    GRAZE units into the counter over about 11 units of its run, which is below any raster."""
    ci, ri = add(c, RING_OFF), r - RING_W
    x = _stem_tangent_x(ci, ri - GRAZE, -side, side)
    q = line_circle(_stem_edge(x, -side), ci, ri, pick='min')   # the lower of the two crossings
    return x, ang(sub(q, c))

def _touch_deg(x_c, edge, c, r, at):
    """The polar angle, measured at the point `at`, of the place where a stem's `edge` touches the
    circle (c, r): the foot of the perpendicular from c to that edge line.  Ending a round's arc on
    THIS ray, rather than at the circle's own extreme, puts the arc's end exactly where the stem's
    edge meets it, so the two hand off with neither a step nor a change of tangent.  (arc_band
    measures its end rays at the outer centre even for the counter, hence `at`.)"""
    p, v = _stem_edge(x_c, edge)
    n = perp(v)
    d = n[0] * (c[0] - p[0]) + n[1] * (c[1] - p[1])
    return ang(sub(sub(c, mul(n, d)), at))

def _touch_y(deg, c, r):
    """The height of the point on the circle (c, r) at polar angle deg -- where a stem's edge is
    tangent to it, so where that stem's buried foot has to stop: a tangent line lies OUTSIDE its
    circle everywhere but the one point, so a stem carried past the tangency pokes out of the
    round's silhouette (0.9 units at the U's old foot, 1.1 at the J's) and the outline steps back
    at the foot.  Stopping OVERLAP short of it leaves the ink OVERLAP^2 / 2r = 0.002 units proud,
    while still overlapping the round in area, which the union needs."""
    return c[1] + r * math.sin(math.radians(deg))

def _handoff_out(x_c, c, r):
    """Height at which a LEFT stem's outer edge crosses the round's outer circle: above it the stem
    carries the silhouette, below it the round does."""
    return line_circle(_stem_edge(x_c, -1), c, r, pick='max')[1]

def _handoff_in(x_c, c, r):
    """Height at which a RIGHT stem's inner edge crosses the counter: above it the stem carries the
    counter's edge, below it the counter's own curve does."""
    return line_circle(_stem_edge(x_c, -1), add(c, RING_OFF), r - RING_W, pick='min')[1]

def _fill_in(x_c, c, r):
    """For a stem on the letter's RIGHT.  The round's disc inside the stem's inner edge: it carries the stem's inner edge on
    down into the round until the counter's own curve crosses it, so the counter turns a corner instead
    of stepping.  Bounded by the stem's edge and the round's outer circle, so it adds nothing outside
    either."""
    return _lens(_stem_edge(x_c, -1), c, r, -1)

def _fill_out(x_c, c, r):
    """For a stem on the letter's LEFT.  The round's disc outside the stem's outer edge: it carries the round's own circle up to
    where the stem's outer edge crosses it, so the silhouette hands off without a step.  The edge is
    moved OVERLAP into the stem so the two contours overlap in area rather than touching along a line."""
    l = _stem_edge(x_c, -1)
    return _lens((add(l[0], (OVERLAP, 0.0)), l[1]), c, r, +1)

def _kink(x_c, edge, c, r, pick):
    """The change of tangent where a stem's `edge` crosses a round's circle (c, r), in degrees: the
    angle between the circle's own tangent there and the stem's edge."""
    l = _stem_edge(x_c, edge)
    q = line_circle(l, c, r, pick=pick)
    a = abs((ang(l[1]) - ang(perp(sub(q, c))) + 180.0) % 360.0 - 180.0)
    return min(a, 180.0 - a)

_JOIN_NOTE = (
    "R1 against R3 is the one join these letters cannot dodge: the band is {left:.1f} wide at the round's "
    "left extreme and {right:.1f} at its right, against a stem of {stem:.1f} at that height, and the "
    "counter's displacement means a stem cannot be tangent to the outer circle and to the counter at once.  "
    "So each side takes the tangency it can, and the round's own disc fills the rest (R6: overlap and "
    "union).  Two things are solved rather than assumed.  First, the stem is placed by tangency to its "
    "circle -- the outer circle on the light side, the counter on the heavy one -- not by sitting its edge "
    "on that circle's extreme, which is a different thing once R3's taper tilts the edge ({tang_err:.2f} "
    "units apart on the heavy side here) and which used to show in the finished outline.  Second, the arc "
    "is ended on the ray through that point, so the arc's own end IS where the stem meets it: measured on "
    "the built outline both hand-offs close to {step:.3f} units, no step in the silhouette and none in the "
    "counter.  The tangency is taken {graze:g} units inside each circle (GRAZE) rather than on it, so that "
    "stem and round cross at {graze_l:.1f} deg on the heavy side and {graze_r:.1f} deg on the light one "
    "instead of grazing at 0 -- a zero-angle contact is not something a boolean union can resolve -- and "
    "the light-side stem's foot stops at its tangency instead of being carried on down, where it would "
    "poke about a unit out of the round and the silhouette would step back at the foot.  What is left at "
    "each junction is the crossing of the stem's OTHER edge with the round, a change of tangent of "
    "{kink_l:.1f} deg on the heavy side and {kink_r:.1f} deg on the light one: the kink every sans-serif "
    "bowl has where its stem enters, and the only thing R1 against R3 leaves behind.")

def build_U():
    xl, a0 = _heavy_junction(U_C, U_R, -1)                           # counter crossing, left
    xr, a1, y0r = _light_junction(U_C, U_R, +1)                      # silhouette crossing, right
    a1 += 360.0
    y0 = U_C[1] - BURY
    left  = stem(xl, y0,  CAP, bottom=None, top='right')
    right = stem(xr, y0r, CAP, bottom=None, top='left')
    arc   = round_arc(U_C, U_R, a0, a1)
    fills = [_fill_out(xl, U_C, U_R), _fill_in(xr, U_C, U_R)]
    hand_l, hand_r = _handoff_out(xl, U_C, U_R), _handoff_in(xr, U_C, U_R)
    end_l = line_circle(line(U_C, from_ang(a0)), add(U_C, RING_OFF), U_R - RING_W, pick='max')
    end_r = add(U_C, mul(from_ang(a1), U_R))                   # the arc's own two ends at the stems
    step_l = abs(end_l[0] - line_x_at_y(_stem_edge(xl, +1), end_l[1]))
    step_r = abs(end_r[0] - line_x_at_y(_stem_edge(xr, +1), end_r[1]))
    return glyph(ord('U'), [arc, left, right] + fills, sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"Medium body {BODY_MEDIUM}: two R3 stems (rules.stem) from the cap down into a lower half "
                     f"round (rules.round_arc, r={U_R:g} centred {U_C}, {a0:.2f} to {a1 - 360:.2f} deg) that "
                     f"sits on the baseline overshoot and whose outer circle spans the body.  The stems' tops "
                     f"are free R5 cuts with the body toward each other, so the tips are the two upper corners "
                     f"and the cuts fall inward.",
        joins=_JOIN_NOTE.format(left=_band_w(180), right=_band_w(0), stem=w_stem(U_C[1]),
                                tang_err=abs(xl - _stem_x_on_extreme(U_C, U_R, -1, inner=True)),
                                step=max(step_l, step_r), graze=GRAZE,
                                graze_l=_kink(xl, +1, add(U_C, RING_OFF), U_R - RING_W, 'min'),
                                graze_r=_kink(xr, +1, U_C, U_R, 'max'),
                                kink_l=_kink(xl, -1, U_C, U_R, 'max'),
                                kink_r=_kink(xr, -1, add(U_C, RING_OFF), U_R - RING_W, 'min')) +
              f"  Here the arc ends on the rays at {a0:.2f} deg (the counter's crossing with the left stem's "
              f"inner edge) and {a1 - 360:.2f} deg (the circle's crossing with the right stem's outer edge), "
              f"and the two crossings are at y={hand_l:.0f} on the left and y={hand_r:.0f} on the right; the "
              f"left stem's outer edge stands {xl - w_stem(U_C[1])/2:.1f} units inside the round's left "
              f"extreme, which is why the round shows on the left a little higher than on the right -- R1's "
              f"displacement, made visible.",
        stem_feet=f"the left stem's foot is flat and buried {BURY:g} units past the junction at y={y0:.0f}, "
                  f"inside the round's own band: its outer edge stands at x={xl - w_stem(y0)/2:.1f} there "
                  f"against the circle's own {_circ_x(U_C, U_R, y0, -1):.1f}, well inside the silhouette.  The "
                  f"right stem's foot stops at y={y0r:.1f}, the tangency with the circle {GRAZE:g} units "
                  f"inside the round's, which is the last height at which the whole foot is still inside the "
                  f"silhouette; carried down to the round's centre as it was, its outer corner stood 0.9 "
                  f"units outside the round and the silhouette stepped back there.",
        spacing=f"{SB_ROUND}/{SB_ROUND}: BOTH extremes are the round's own circle, so both sides take a "
                f"round's bearing.  On the left the outer circle reaches x=0 at y={U_C[1]:.0f} while the left "
                f"stem's outer edge stands {xl - w_stem(U_C[1])/2:.1f} units inside it; on the right the stem's "
                f"outer edge meets the circle within a quarter of a unit of its extreme, so there stem and "
                f"round hold the extreme together.  The letter's two sides are the same shape -- a stem "
                f"running down into the round -- and 40/60 (R9 read literally off which of the two owns the "
                f"extreme) put the ink {abs(SB_STRAIGHT - SB_ROUND)/2:.0f} units left of centre in the advance, "
                f"which showed against the symmetric V, X and Y.  40 on both sides is the same reading applied "
                f"to the same shape twice.",
        deviations="none from R1-R9; the two fills are junction tooling (R6), each bounded by the round's own "
                   "circle and a stem's own edge, so no new curve or weight is introduced.",
        geometry=dict(centre=U_C, r_out=U_R, stems=(xl, xr), stem_bottom=y0, arc_deg=(a0, a1 - 360),
                      handoff=(hand_l, hand_r), handoff_step=(step_l, step_r))))

def build_J():
    x_s, a1, y0 = _light_junction(J_C, J_R, +1)                      # silhouette crossing at the stem
    a1 += 360.0
    st  = stem(x_s, y0, CAP, bottom=None, top='left')
    arc = round_arc(J_C, J_R, J_END, a1)
    fill = _fill_in(x_s, J_C, J_R)
    tip = add(J_C, mul(from_ang(J_END), J_R))
    return glyph(ord('J'), [arc, st, fill], sb=(SB_ROUND, SB_STRAIGHT), notes=dict(
        construction=f"Narrow body {BODY_NARROW}: one R3 stem (rules.stem) down the right and a hook that is an "
                     f"R1 arc (rules.round_arc, r={J_R:g} centred {J_C}) from {J_END:g} deg round the bottom to "
                     f"the stem, sitting on the baseline overshoot.",
        hook=f"The free end is R1's radial cut at {J_END:g} deg, a little past the left extreme, so the hook "
             f"lifts instead of stopping dead on the horizontal; the face is {_band_w(J_END):.1f} long there, "
             f"the heavy side of the round (R7).  Its outer tip is at {tuple(round(v, 1) for v in tip)}.",
        stem_top=f"free R5 cut with the body to the left: the tip is the upper-right corner, the corner farther "
                 f"from the letter's centre (R5), the same cut the H's and the U's right stems take.",
        joins=f"The stem meets the round on its light side, the U's right junction exactly (_light_junction): "
              f"its outer edge is solved tangent to the circle {GRAZE:g} units inside the round's own -- not "
              f"set on the round's extreme, which is {abs(x_s - _stem_x_on_extreme(J_C, J_R, +1)):.2f} units "
              f"away once R3's taper tilts the edge, and which used to leave the stem's foot a unit outside "
              f"the round -- so it crosses the round's circle at {_kink(x_s, +1, J_C, J_R, 'max'):.1f} deg, a "
              f"shallow but real crossing the union can resolve.  The arc is ended on the ray at "
              f"{a1 - 360:.2f} deg through that crossing, so the arc's own end is exactly where the stem's "
              f"edge meets it: measured on the built outline the hand-off closes to "
              f"{abs(add(J_C, mul(from_ang(a1), J_R))[0] - line_x_at_y(_stem_edge(x_s, +1), add(J_C, mul(from_ang(a1), J_R))[1])):.3f} "
              f"units, and the stem's foot stops at y={y0:.1f}, still inside the silhouette.  The stem is then "
              f"carried on down inside the round to y={_handoff_in(x_s, J_C, J_R):.0f}, where the counter "
              f"crosses its inner edge (_fill_in) and the outline turns "
              f"{_kink(x_s, -1, add(J_C, RING_OFF), J_R - RING_W, 'min'):.1f} deg -- a change of tangent, not "
              f"a step.  The band is only "
              f"{_band_w(0):.1f} against the stem's {w_stem(J_C[1]):.1f} there, which is R1 against R3.",
        spacing=f"{SB_ROUND} beside the hook, {SB_STRAIGHT} beside the stem.",
        deviations="none from R1-R9.",
        geometry=dict(centre=J_C, r_out=J_R, stem_x=x_s, stem_bottom=y0, arc_deg=(J_END, a1 - 360.0))))

GLYPHS = {'C': build_C, 'G': build_G, 'Q': build_Q, 'S': build_S, 'U': build_U, 'J': build_J}
