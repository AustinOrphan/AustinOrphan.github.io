"""
SPEC section 5 as code.  Every glyph outside core.py is built with these, so a
number never has to be re-read from the spec, and a verifier can check a glyph
against the same functions that built it.
"""
import json, math, os
from pen import *
from metrics import CAP, OVER_POINT, OVER_ROUND, SB_STRAIGHT, SB_ROUND

_SRC = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'source', 'ai_objects.json')))['AO'][0]
_ring = next(o for o in _SRC['objects'] if o['role'] == 'ring')
_sO = (CAP + 2*OVER_ROUND) / (2*_ring['outer'][2])

# ---- The two knobs -------------------------------------------------------------------
#
# The mark gives one weight and one amount of stress. These scale the two independently, so
# the face can be cut at other weights without redrawing it. Both are 1.0 for the mark itself,
# and at (1.0, 1.0, ORPHAN_FOOT=0) every glyph is byte for byte what the mark produces -- that is
# the test. It now needs the third setting: FOOT_WIDEN below is a design decision taken on top of
# the derivation, so the SHIPPED cut deliberately does not reproduce the mark, and the sheet that
# checks the derivation (proof.py --overlay) is built with the widening off.
#
#   WEIGHT  scales the STROKE. RING_W is the O's mean band and, by R3, the stem at mid-cap, so
#           the straights scale with it or the rounds and the straights come apart.
#   PUSH    scales the O counter's DISPLACEMENT, which is where all of the face's stress comes
#           from. It moves thin and thick apart around a fixed mean, so it changes CONTRAST at
#           near-constant colour -- it is not a second weight.
#
# They are not fully independent at the ends: the thin side of a round is RING_W*WEIGHT minus
# the displacement, so PUSH has a ceiling of 1.674*WEIGHT before that goes to zero, which is
# also where the O would split into a C. Nothing here enforces it; ROUND_THIN simply goes
# negative and the build fails loudly.
WEIGHT = float(os.environ.get('ORPHAN_WEIGHT', 1.0))
PUSH   = float(os.environ.get('ORPHAN_PUSH', 1.0))

# ---- R1 rounds: the O's construction in absolute units, so every round in the face
#      carries the O's stroke and the O's displacement whatever its size.
# R1b. The rounds follow R2b.
#
# R2b widens the straights at the baseline and a round has no foot to widen -- its weight is the
# band and the counter's displacement, both fixed to the page rather than to height.  Left alone,
# the face's straights averaged 42.9 units against its rounds' 33.2, a 29% split the mark does not
# have, and an O beside an H looked starved.
#
# So the BAND takes the same gain R2b gives the straights' MEAN: RING_W is multiplied by
# 1 + (FOOT_WIDEN/2) / RING_W_mark.  R3's check -- a stem and an O carry the same weight -- goes on
# holding at its own original 0.75%, because both sides moved by the same fraction, and at
# FOOT_WIDEN 0 this reduces to the mark exactly.
#
# The DISPLACEMENT takes the same gain, so the round's CONTRAST is untouched: thick over thin stays
# the mark's 53.02/13.36 = 3.97 rather than flattening to 2.70, PUSH means what it meant, and its
# ceiling sits where it sat.  Scaling the band alone is the other reading and ORPHAN_OFF_MUL builds
# it; it is a more monoline O than the mark's.
#
# This looked unaffordable at first.  Measured across the grid the WEIGHT ceiling at PUSH 1.00 fell
# from 2.302 to 1.638 with the band alone and to 1.110 with the displacement as well, against an
# axis that needs 2.00.  All three numbers were an artefact: the B's upper bowl meets its waist at
# a TANGENCY, and set_bowl._bowl was asking that tangency for two roots.  It got them by rounding
# at the mark's numbers and stopped getting them under a heavier band.  Read as the tangency it is,
# the ceilings are 3.014, 2.370 and 2.311 -- the axis fits with room, and it had more room than
# anyone thought at the mark's numbers too.
_RING_ADD = float(os.environ.get('ORPHAN_RING_ADD', 0.0))    # TEST KNOB: extra band on every round
_OFF_MUL  = float(os.environ.get('ORPHAN_OFF_MUL', 1.0))     # TEST KNOB: counter displacement multiplier
_RING_MARK = (_ring['outer'][2] - _ring['inner'][2]) * _sO                        # 33.19, the mark's band
_FOOT1   = float(os.environ.get('ORPHAN_FOOT', 20.0))                             # R2b at WEIGHT 1
RING_GAIN = 1.0 + (_FOOT1 / 2) / _RING_MARK                                       # 1.3013 at FOOT 20
RING_W   = (_RING_MARK * RING_GAIN + _RING_ADD) * WEIGHT                          # 43.19 at WEIGHT 1
_OFF0    = ((_ring['inner'][0]-_ring['outer'][0]) * _sO, (_ring['inner'][1]-_ring['outer'][1]) * _sO)   # (14.0, 14.0)
RING_OFF = (_OFF0[0] * PUSH * _OFF_MUL * RING_GAIN, _OFF0[1] * PUSH * _OFF_MUL * RING_GAIN)
ROUND_THICK, ROUND_THIN = RING_W + norm(RING_OFF), RING_W - norm(RING_OFF)         # 53.0 and 13.4 at (1, 1)

def round_ring(c, r_out):
    """A complete round: outer radius r_out, counter per R1. -> [outer, inner] contours."""
    return ring(c, r_out, r_out - RING_W, RING_OFF)

def round_arc(c, r_out, a0, a1):
    """A partial round between polar angles a0 -> a1 (ccw, degrees), radial ends. -> Contour"""
    return arc_band(c, r_out, r_out - RING_W, RING_OFF, a0, a1)

# ---- R2 / R3 straight-stroke weights as a field over height (units)
# Measured off the mark, then scaled with WEIGHT: R3 ties the stem at mid-cap to the O's mean
# band, so if these did not move with RING_W a heavier cut would have heavy rounds on light
# straights. The TAPER is a proportion of the width, so it survives the scaling unchanged.
# R2's widths, at the heights the rule actually evaluates them at.
#
# SPEC 2.2 measured the A's legs at two places: the FOOT CUT and the COUNTER APEX. Those were
# then stored as if they were the baseline and the cap line, which they are not -- the foot cut
# sits at y 20.1 and the counter apex at y 643.5, not at 0 and 700. Read as base/cap the numbers
# were 39.5/27.1 and 37.2/25.5; extrapolated from where they were actually taken they are the
# ones below. The correction is small and systematic: about 1% light at the foot, 4% heavy at
# the cap, and a taper flatter than the A's own.
#
# It also fixes SPEC 2.2's "the legs lose about 1.6% of their length in width": the 12.39-unit
# drop was divided by the whole 768.4-unit leg, but measured over only 669.1 of it. It is 1.85%.
#
# The check this weakens is R3's, which corroborates borrowing the leg's profile for a stem by
# noting the profile's mid-height matches the O's mean band. It still holds -- 32.94 against
# 33.19, 0.75% -- where the old numbers gave 33.30, 0.34%. Both sit well inside any tolerance
# that check can carry, and a wrong derivation is not worth keeping to make it land prettier.
# FOOT_WIDEN is the one number in R2 that is NOT measured off the mark.  The mark's own A tapers
# 39.90 -> 25.99 straight, and the face was cut that way; this widens the BASE of that taper by
# 20 units and leaves the cap where it is, so a stroke is 59.90 at the baseline and still 25.99 at
# the cap line.  Three things about it are worth stating, because it is a departure:
#
#   * It is a DESIGN decision, not a reading.  The alternatives were measured and drawn first --
#     a wider foot with a curved taper, and a true flare confined to the bottom 200 units -- and
#     measure/evidence/foot-matrix.png and foot-full-letter.png are the comparison.  A flare holds
#     the letter's colour above the foot exactly; this does not, and that is the point: it makes
#     the whole lower half of the face heavier, planted rather than merely tipped.
#   * The field STAYS LINEAR, which is why it costs nothing.  stroke() samples a width at each end
#     and interpolates, so a straight taper from a wider base is the one treatment the existing
#     machinery draws exactly; a flare or a curve would need stroke(), diagonal() and
#     _derive_counter taught to follow a field along the stroke.
#   * It SCALES WITH WEIGHT, like the rest of R2, so the Black carries proportionally the same foot
#     as the Thin rather than a progressively smaller one.
#
# It costs R3 its corroboration, and that is the strongest thing against it.  R3 borrows the leg's
# profile for a stem and checks the choice against the O: the profile's width at mid-cap used to be
# 32.94 against the O's mean band of 33.19, within 0.75%.  It is now 42.94, 29% heavier, and the
# whole lower half of the face's straights are heavier than its rounds -- the rounds have no foot to
# widen, because a round's weight is modulated by stress and not by height.  The check was always a
# corroboration rather than a derivation, and what it corroborated is where the stem's profile CAME
# from, which has not changed.  But the face now has a colour difference between straight and round
# that it did not have, by choice.
#
# R3 borrows the left leg's profile for the stem, so this reaches every upright in the face too.
# That is the whole of the change: no vertex moves, only the base of one linear field.  It does not
# fit through the axes for free -- see set_round._heavy_junction, where the U's stem is now placed
# by whichever tangency keeps it inside its bowl.
FOOT_WIDEN = float(os.environ.get('ORPHAN_FOOT', 20.0)) * WEIGHT

_CAP_NARROW = float(os.environ.get('ORPHAN_CAP_NARROW', 0.0)) * WEIGHT   # TEST KNOB
SLASH_BASE, SLASH_CAP = 39.899 * WEIGHT + FOOT_WIDEN, 25.987 * WEIGHT - _CAP_NARROW   # "/" and stems
BACK_BASE,  BACK_CAP  = 37.544 * WEIGHT + FOOT_WIDEN, 24.464 * WEIGHT - _CAP_NARROW   # "\\"

def w_slash(y):     return SLASH_BASE + (SLASH_CAP - SLASH_BASE) * (y / CAP)
def w_backslash(y): return BACK_BASE  + (BACK_CAP  - BACK_BASE)  * (y / CAP)
w_stem = w_slash

# ---- R4 horizontals
# R4 has two weights, because a horizontal has two jobs.
#
# A horizontal that RUNS INTO A ROUND has to arrive at that round's own band, or the outline
# steps where they meet: HORIZ_JOIN is the band at the bottom of a round (R7's heavy side),
# and the bowl letters' bars and arms are solved against it.
#
# A horizontal IN THE OPEN has no such constraint, and giving it the join weight made every
# free arm as heavy as the heaviest part of the O.  Measured colour ran from Y at -41% to
# B at +47% of the alphabet's median, horizontal-dense letters at the top of that list and
# diagonal-dense ones at the bottom.  HORIZ_FREE is RING_W instead -- the round's NOMINAL
# band, which is also the stem at mid-cap -- so a free arm, a stem and an unmodulated round
# all weigh the same.
#
# The two cannot be reconciled by one number.  Lowering the single R4 to 33 opened a 7.6-unit
# ledge at every bowl, and tapering a bar from free to join weight sent its underside tangent
# to the bowl's bottom, where the two curves no longer cross and the join has no solution.
HORIZ_JOIN  = RING_W + RING_OFF[1]       # 47.23, an R1 band at the bottom of a round
HORIZ_FREE  = RING_W                     # 33.19, a horizontal that runs into nothing
HORIZ_TAPER = 0.018                      # loss per unit length, left to right, either way
HORIZ_MID   = HORIZ_JOIN                 # the metric-line nominal: the mid line is shared with
                                         # the bowl letters, so it stays tied to the join weight
def w_horizontal(length, t, mid=None):
    """Width of a horizontal of `length` at fraction t along it (0 = left end, 1 = right end).

    `mid` is the nominal: HORIZ_FREE by default, HORIZ_JOIN for a horizontal solved against a
    round.  R4's length taper applies either way."""
    return (HORIZ_FREE if mid is None else mid) + HORIZ_TAPER * length * (0.5 - t)

# ---- R5 terminals
CUT_DEG = 20.6

# ---- convenience constructors -------------------------------------------------
def stem(x, y0=0.0, y1=CAP, bottom=None, top=None, kind='slash'):
    """A vertical stem centred on x from y0 to y1.  bottom/top: None for flat, or the
    direction of the letter's body along that end ('left'/'right') for an R5 cut."""
    wf = w_slash if kind == 'slash' else w_backslash
    e0 = cut_for((x, y0), (x, y1), 'bottom', bottom, CUT_DEG) if bottom else ('flat',)
    e1 = cut_for((x, y1), (x, y0), 'top', top, CUT_DEG) if top else ('flat',)
    return stroke((x, y0), (x, y1), wf(y0), wf(y1), e0, e1)

def diagonal(p0, p1, bottom=None, top=None):
    """A diagonal from its LOWER point p0 to its UPPER point p1; width from the R2 field
    by the lean of the stroke.  bottom/top as in stem()."""
    if p0[1] > p1[1]: p0, p1 = p1, p0
    wf = w_slash if p1[0] >= p0[0] else w_backslash
    e0 = cut_for(p0, p1, 'bottom', bottom, CUT_DEG) if bottom else ('flat',)
    e1 = cut_for(p1, p0, 'top', top, CUT_DEG) if top else ('flat',)
    return stroke(p0, p1, wf(p0[1]), wf(p1[1]), e0, e1)

def horizontal(x0, x1, y, left=None, right=None, mid=None):
    """A level horizontal from x0 to x1 centred on y, R4 widths.  left/right: None for
    flat, or the direction of the letter's body along that end ('up'/'down') for an R5 cut."""
    L = abs(x1 - x0)
    e0 = cut_for((x0, y), (x1, y), 'left', left, CUT_DEG) if left else ('flat',)
    e1 = cut_for((x1, y), (x0, y), 'right', right, CUT_DEG) if right else ('flat',)
    return stroke((x0, y), (x1, y), w_horizontal(L, 0, mid), w_horizontal(L, 1, mid), e0, e1)

def glyph(cp, contours, adv=None, sb=(SB_STRAIGHT, SB_STRAIGHT), notes=None):
    """Package a glyph: shifts the contours so the left extreme sits at sb[0] and sets the
    advance from the right extreme plus sb[1], unless adv is given."""
    x0, y0, x1, y1 = bbox([c.flatten() for c in contours])
    dx = sb[0] - x0
    contours = [c.map(lambda p: (p[0] + dx, p[1])) for c in contours]
    return dict(cp=cp, adv=adv if adv is not None else round(x1 - x0 + sb[0] + sb[1]), contours=contours, notes=notes or {})

def arm(x0, x1, outer, left='cut', right='cut', mid=None):
    """An R4 horizontal whose OUTER edge lies level on a metric line: outer='top' puts the
    top edge on CAP with the body below, 'bottom' the bottom edge on 0 with the body above.
    Widths are R4's (w_horizontal at each end) measured from the outer edge, so the whole
    1.8%-of-length change is taken on the inner edge and the flat side stays exactly on the
    metric line (SPEC R4).  Each end is 'cut' (an R5 cut, tip at the outer corner; serves a
    free tip and an end buried in a stem alike) or 'flat'.  Use horizontal() for bars that
    sit away from the metric lines.  Lifted from glyphs/set_straight.py."""
    y_out, sgn, body = (CAP, -1, 'down') if outer == 'top' else (0.0, 1, 'up')
    L = x1 - x0
    outer_l = line((x0, y_out), (1, 0))
    inner_l = line_2pt((x0, y_out + sgn * w_horizontal(L, 0, mid)), (x1, y_out + sgn * w_horizontal(L, 1, mid)))
    def end(spec, x_end, face):
        if spec == 'flat': return line((x_end, y_out), (0, 1))
        other = x1 if face == 'left' else x0
        _, angle, _ = cut_for((x_end, y_out), (other, y_out), face, body, CUT_DEG)
        return line_ang((x_end, y_out), angle)
    l_end, r_end = end(left, x0, 'left'), end(right, x1, 'right')
    return from_poly(ccw([isect(outer_l, l_end), isect(inner_l, l_end), isect(inner_l, r_end), isect(outer_l, r_end)]))
