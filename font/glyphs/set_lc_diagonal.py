"""The lowercase diagonals: k v w x y z.

R2 gives a diagonal its width from its own lean, so none of these letters needs a weight decided
for it -- only where its ends are.  Those come from the capitals at the lowercase factor, the same
scaling the o takes from the O, the s from the S and the f/t bar from the T.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from metrics import ASC_LC, CAP, DESC_LC, OVER_ROUND, SB_ROUND, SB_STRAIGHT, XH
import rules
from rules import glyph, w_stem, w_horizontal
from glyphs import set_diagonal as SD
from pen import cut_for, stroke

S_K  = (XH + 2 * OVER_ROUND) / float(CAP + 2 * OVER_ROUND)      # 0.5625
BODY = SD.BODY_MEDIUM * S_K                                     # 313.88: the A's foot spread, scaled
MID  = XH / 2.0                                                 # where an arm and a leg meet on a stem
K_TOP = ASC_LC                                                  # the k ascends; v w x y z do not


def _sb(left_round, right_round):
    return (SB_ROUND if left_round else SB_STRAIGHT, SB_ROUND if right_round else SB_STRAIGHT)


def _note(what, **kw):
    n = dict(construction=what,
             widths=f"R2's field by each stroke's own lean, so nothing is chosen: the rule gives "
                    f"the weight from the angle the stroke runs at.",
             proportion=f"body {BODY:.2f} -- the capitals' {SD.BODY_MEDIUM:g} at the lowercase "
                        f"factor {S_K:.4f}, the same scaling the o takes from the O.",
             deviations="none from R1-R9.")
    n.update(kw)
    return n


def _right_face(p_in, p_end, body):
    """A diagonal whose free end presents the letter's RIGHT face.

    R5's second case: an end nearer a horizontal than a vertical is cut CUT_DEG off the VERTICAL,
    not off the horizontal -- the capital K's note states it and its arm and leg both take it.
    rules.diagonal cannot express it, since it names the face by the end's index (bottom for p0,
    top for p1) rather than by which side of the letter the end is on.  Taken the first way, the
    k's leg tip ran 78 units past the body and closed to 12.8 deg."""
    lo, hi = (p_in, p_end) if p_in[1] <= p_end[1] else (p_end, p_in)
    wf = rules.w_slash if hi[0] >= lo[0] else rules.w_backslash
    e_end = cut_for(p_end, p_in, 'right', body, rules.CUT_DEG)
    if p_end is hi:
        return stroke(lo, hi, wf(lo[1]), wf(hi[1]), ('flat',), e_end)
    return stroke(lo, hi, wf(lo[1]), wf(hi[1]), e_end, ('flat',))


def build_v():
    """Two diagonals to a point on the baseline."""
    T = (BODY / 2.0, 0.0)
    left = rules.diagonal(T, (0.0, XH), bottom=None, top='right')
    right = rules.diagonal(T, (BODY, XH), bottom=None, top='left')
    return glyph(ord('v'), [left, right], sb=_sb(True, True), notes=_note(
        f"Two R2 diagonals from the x-height corners to a point at ({T[0]:.2f}, 0), the capital "
        f"V's construction at the lowercase factor.",
        terminals="R5 at both tops, tips at the outer corners on the x-height line."))


def build_w():
    """Two v's sharing their middle top, as the capital W is two V's."""
    q = BODY * 0.92                                      # each v narrowed so the pair is not vast
    T1, T2 = (q / 2.0, 0.0), (q * 1.5, 0.0)
    mid = (q, XH)
    return glyph(ord('w'), [rules.diagonal(T1, (0.0, XH), top='right'),
                            rules.diagonal(T1, mid, top='left'),
                            rules.diagonal(T2, mid, top='right'),
                            rules.diagonal(T2, (2 * q, XH), top='left')],
                 sb=_sb(True, True), notes=_note(
        f"Two v's meeting at a shared top, the capital W's own arrangement.  Each is narrowed to "
        f"{q:.2f} ({q/BODY:.0%} of the v) so the pair does not run to twice the v's width.",
        terminals="R5 at the two outer tops; the middle two meet at a point and need none."))


def build_x():
    """Two diagonals crossing."""
    a = rules.diagonal((0.0, 0.0), (BODY, XH), bottom='right', top='left')
    b = rules.diagonal((BODY, 0.0), (0.0, XH), bottom='left', top='right')
    return glyph(ord('x'), [a, b], sb=_sb(True, True), notes=_note(
        f"Two R2 diagonals corner to corner across a {BODY:.2f} body, crossing at "
        f"({BODY/2.0:.2f}, {MID:.2f}).",
        terminals="R5 at all four, tips at the outer corners."))


def build_y():
    """The v, with its point carried on down to the descender."""
    J = (BODY / 2.0, MID)
    stem_bot = DESC_LC
    st = rules.stem(J[0], stem_bot, J[1] + w_stem(J[1]) / 2.0, bottom='right', top=None)
    return glyph(ord('y'), [rules.diagonal(J, (0.0, XH), top='right'),
                            rules.diagonal(J, (BODY, XH), top='left'), st],
                 sb=_sb(True, True), notes=_note(
        f"The capital Y's construction at the lowercase factor: two R2 arms meeting on the stem's "
        f"centre at ({J[0]:.2f}, {MID:.2f}), and an R3 stem from there down.",
        descender=f"The stem runs to {stem_bot:g}, the descender line -- a straight tail, as the "
                  f"p's and the q's are, not the g's curved one.  The g is the only lowercase tail "
                  f"in this face that turns.",
        stem_top=f"buried half a stem width above the junction, as the capital Y's is."))


def build_z():
    """Two arms and a diagonal."""
    # Only the FREE ends are cut.  The end that meets the diagonal is flat and buried, as the
    # capital Z's is: cutting it too left a 20.1 deg spike where the arm and the diagonal crossed,
    # against the capital's own sharpest corner of 48.5.
    top = rules.horizontal(0.0, BODY, XH - w_horizontal(BODY, 0.5) / 2.0, left='down', right=None)
    bot = rules.horizontal(0.0, BODY, w_horizontal(BODY, 0.5) / 2.0, left=None, right='up')
    # Both ends flat and buried in the arms, as the capital Z's are.  Cutting them put a free
    # R5 tip out past the arm and left a 20.1 deg spike, against the capital's sharpest of 48.5.
    dia = rules.diagonal((0.0, 0.0), (BODY, XH))
    return glyph(ord('z'), [top, dia, bot], sb=_sb(True, True), notes=_note(
        f"The capital Z at the lowercase factor: an R4 arm under the x-height, an R4 arm on the "
        f"baseline, and an R2 diagonal between their far ends.",
        terminals="R5 at both arm tips, bodies away from the diagonal."))


def build_k():
    """The l's stem with the capital K's arm and leg."""
    xL = w_stem(0.0) / 2.0
    J = (xL, MID)
    st = rules.stem(xL, 0.0, K_TOP, bottom='right', top='right')
    # Both free ends present the letter's RIGHT face and lie nearer a horizontal than a vertical,
    # so R5's SECOND case applies, exactly as the capital K's note says: the same cut turned 90
    # deg, taken off the VERTICAL, tip at the outer corner.  Naming the body left/right instead
    # left a 12.8 deg spike at the leg's tip against the capital's sharpest of 38.8.
    arm = _right_face(J, (BODY, XH), 'down')
    leg = _right_face(J, (BODY, 0.0), 'up')
    return glyph(ord('k'), [st, arm, leg], sb=_sb(False, True), notes=_note(
        f"The capital K's construction at the lowercase factor: an R3 stem to the ascender with "
        f"the arm and the leg meeting on its centre-line at ({J[0]:.2f}, {MID:.2f}).",
        height=f"The stem reaches {K_TOP:g}, the ascender -- the k is an ascending letter and takes "
               f"the same height as the b, the d, the h and the l.",
        junction=f"Both meet the stem at mid-x-height, as the capital's meet at mid-cap.",
        spacing=f"{SB_STRAIGHT}/{SB_ROUND}: a stem on the left, the leg's R5 tip on the right."))


GLYPHS = {'k': build_k, 'v': build_v, 'w': build_w, 'x': build_x, 'y': build_y, 'z': build_z}
