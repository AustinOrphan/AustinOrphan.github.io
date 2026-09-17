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
from pen import add, ang, from_ang, line_circle, mul, norm, perp, sub, Contour, from_poly, ccw
from metrics import ASC_LC, DESC_LC, OVER_ROUND, SB_ROUND, SB_STRAIGHT, XH
from rules import RING_OFF, RING_W, CUT_DEG, round_ring, w_stem
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
