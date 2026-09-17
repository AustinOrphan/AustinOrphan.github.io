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
from pen import (add, ang, cut_for, from_ang, line_circle, mul, norm, perp, stroke, sub,
                 Contour, from_poly, ccw)
from metrics import ASC_LC, DESC_LC, OVER_ROUND, SB_ROUND, SB_STRAIGHT, XH
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


GLYPHS = {'o': build_o, 'a': build_a}
