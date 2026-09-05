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

# ---- R1 rounds: the O's construction in absolute units, so every round in the face
#      carries the O's stroke and the O's displacement whatever its size.
RING_W   = (_ring['outer'][2] - _ring['inner'][2]) * _sO                          # 33.19: mean stroke of a round
RING_OFF = ((_ring['inner'][0]-_ring['outer'][0]) * _sO, (_ring['inner'][1]-_ring['outer'][1]) * _sO)   # (14.0, 14.0): counter displacement
ROUND_THICK, ROUND_THIN = RING_W + norm(RING_OFF), RING_W - norm(RING_OFF)         # 53.0 and 13.4

def round_ring(c, r_out):
    """A complete round: outer radius r_out, counter per R1. -> [outer, inner] contours."""
    return ring(c, r_out, r_out - RING_W, RING_OFF)

def round_arc(c, r_out, a0, a1):
    """A partial round between polar angles a0 -> a1 (ccw, degrees), radial ends. -> Contour"""
    return arc_band(c, r_out, r_out - RING_W, RING_OFF, a0, a1)

# ---- R2 / R3 straight-stroke weights as a field over height (units)
SLASH_BASE, SLASH_CAP = 39.5, 27.1        # strokes leaning like "/" and all vertical stems
BACK_BASE,  BACK_CAP  = 37.2, 25.5        # strokes leaning like "\\"
def w_slash(y):     return SLASH_BASE + (SLASH_CAP - SLASH_BASE) * (y / CAP)
def w_backslash(y): return BACK_BASE  + (BACK_CAP  - BACK_BASE)  * (y / CAP)
w_stem = w_slash

# ---- R4 horizontals
HORIZ_MID, HORIZ_TAPER = 47.5, 0.018     # width at mid-length; loss per unit length, left to right
def w_horizontal(length, t):
    """Width of a horizontal of `length` at fraction t along it (0 = left end, 1 = right end)."""
    return HORIZ_MID + HORIZ_TAPER * length * (0.5 - t)

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

def horizontal(x0, x1, y, left=None, right=None):
    """A level horizontal from x0 to x1 centred on y, R4 widths.  left/right: None for
    flat, or the direction of the letter's body along that end ('up'/'down') for an R5 cut."""
    L = abs(x1 - x0)
    e0 = cut_for((x0, y), (x1, y), 'left', left, CUT_DEG) if left else ('flat',)
    e1 = cut_for((x1, y), (x0, y), 'right', right, CUT_DEG) if right else ('flat',)
    return stroke((x0, y), (x1, y), w_horizontal(L, 0), w_horizontal(L, 1), e0, e1)

def glyph(cp, contours, adv=None, sb=(SB_STRAIGHT, SB_STRAIGHT), notes=None):
    """Package a glyph: shifts the contours so the left extreme sits at sb[0] and sets the
    advance from the right extreme plus sb[1], unless adv is given."""
    x0, y0, x1, y1 = bbox([c.flatten() for c in contours])
    dx = sb[0] - x0
    contours = [c.map(lambda p: (p[0] + dx, p[1])) for c in contours]
    return dict(cp=cp, adv=adv if adv is not None else round(x1 - x0 + sb[0] + sb[1]), contours=contours, notes=notes or {})

def arm(x0, x1, outer, left='cut', right='cut'):
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
    inner_l = line_2pt((x0, y_out + sgn * w_horizontal(L, 0)), (x1, y_out + sgn * w_horizontal(L, 1)))
    def end(spec, x_end, face):
        if spec == 'flat': return line((x_end, y_out), (0, 1))
        other = x1 if face == 'left' else x0
        _, angle, _ = cut_for((x_end, y_out), (other, y_out), face, body, CUT_DEG)
        return line_ang((x_end, y_out), angle)
    l_end, r_end = end(left, x0, 'left'), end(right, x1, 'right')
    return from_poly(ccw([isect(outer_l, l_end), isect(inner_l, l_end), isect(inner_l, r_end), isect(outer_l, r_end)]))
