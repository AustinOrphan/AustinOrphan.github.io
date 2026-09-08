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
# and at (1.0, 1.0) every glyph is byte for byte what the mark produces -- that is the test.
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
RING_W   = (_ring['outer'][2] - _ring['inner'][2]) * _sO * WEIGHT                 # 33.19 at WEIGHT 1
_OFF0    = ((_ring['inner'][0]-_ring['outer'][0]) * _sO, (_ring['inner'][1]-_ring['outer'][1]) * _sO)   # (14.0, 14.0)
RING_OFF = (_OFF0[0] * PUSH, _OFF0[1] * PUSH)                                     # counter displacement
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
SLASH_BASE, SLASH_CAP = 39.899 * WEIGHT, 25.987 * WEIGHT   # strokes leaning "/" and all stems
BACK_BASE,  BACK_CAP  = 37.544 * WEIGHT, 24.464 * WEIGHT   # strokes leaning like "\\"

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
