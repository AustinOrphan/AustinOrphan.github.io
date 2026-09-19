"""The lowercase stems: i and l, and the dot they share with the face's punctuation.

Neither letter decides anything on its own.  The stem is R3's field, cut at both ends by the
convention the capital I states and every free stem end in the face follows; the dot is the
period, at the clearance the exclamation mark already uses.  What is left to say is only how tall
each stem is, and the lowercase metrics have already said that.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from metrics import ASC_LC, CAP, OVER_ROUND, SB_ROUND, SB_STRAIGHT, XH
import rules
from rules import glyph, w_stem, RING_W
from glyphs import set_punct as SP
from glyphs import set_straight as SS

# The dot is the face's own: a circle of the undirected R2 weight at the baseline, which is what
# the period, the colon, the exclamation and the question mark are all built from.  Taking any
# other size here would give the i a dot that no other dot in the font matches.
DOT_R = SP.DOT_R
# ... and the clear space under it is the one the exclamation mark uses, held at the axis origin
# so it stays 65 in every master rather than compounding with the dot's own growth.
DOT_GAP = SP.DOT_GAP
DOT_CY = XH + DOT_GAP + DOT_R


def _stem(y1):
    """A lone lowercase stem.  R7 picks the cuts, as it does for the I: body 'right' at both ends
    puts the foot's tip at the lower left and cuts the upper right away, heavy low and light
    high, which is how every free stem end on a left stem in this face is cut."""
    return rules.stem(0.0, 0.0, y1, bottom='right', top='right')


def _notes(y1, extra=None):
    n = dict(
        construction=f"One R3 stem, {w_stem(0.0):.2f} at the baseline tapering to "
                     f"{w_stem(y1):.2f} at y={y1:g}, both ends free with R5 cuts.",
        cuts="R7, as the capital I: body 'right' at both ends, so the foot's tip is the lower-left "
             "corner and the upper-right corner is cut away.  Every free stem end on a left stem "
             "in the face is cut this way.",
        spacing=f"{SB_STRAIGHT}/{SB_STRAIGHT}.",
        deviations="none from R1-R9.")
    if extra: n.update(extra)
    return n


def build_l():
    """The ascender, alone.  Nothing distinguishes it from the h's leg but the missing shoulder."""
    return glyph(ord('l'), [_stem(ASC_LC)], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=_notes(
        ASC_LC, dict(height=f"{ASC_LC:g}, the ascender line, which is the cap line -- the same "
                             f"height the b, the d and the h reach, and level with the capitals "
                             f"rather than above them.")))


def build_i():
    """The x-height stem with the face's own dot over it."""
    return glyph(ord('i'), [_stem(XH), SP._dot(0.0, DOT_CY)],
                 sb=(SB_STRAIGHT, SB_STRAIGHT), notes=_notes(XH, dict(
        dot=f"The period: a circle of diameter {2*DOT_R:.2f}, the R2 stem's width at the baseline, "
            f"which is the face's undirected weight and the same dot the period, colon, exclam and "
            f"question are built from.",
        dot_height=f"Its underside sits {DOT_GAP:g} above the x-height and its centre at "
                   f"{DOT_CY:.2f}.  The gap is the exclamation mark's DOT_GAP, taken at the axis "
                   f"origin and held, so it stays {DOT_GAP:g} in every master instead of growing "
                   f"with the dot; the exclam's note explains why that compounds otherwise.",
        top=f"The dot's top reaches {DOT_CY + DOT_R:.2f}, short of the ascender at {ASC_LC:g}: the "
            f"i is not an ascending letter and the gap is the one the face already uses, not a "
            f"height chosen to reach something.")))


# ---- t and f ------------------------------------------------------------------------
# Both are a stem with a bar across it at the x-height, and the bar is the same bar: one measure
# for the two of them, as E, F and H share one horizontal through a word in the capitals.
#
# Its length is the capital T's bar at the lowercase factor -- 558 * 405/720 -- which is the same
# scaling the s takes from the capital S and the o from the O.  Symmetric about the stem, as the
# capital T's is: the rightward bias a text face gives its t is a serif inheritance, and there is
# nothing in this mark to derive it from.
S_K    = (XH + 2 * OVER_ROUND) / float(CAP + 2 * OVER_ROUND)
BAR_L  = SS.BODY_MEDIUM * S_K
# How high the t rises above the bar: to the top of the i's dot, TAKEN AT THE AXIS ORIGIN.  Those
# are the face's only two heights between the x-height and the ascender and there is no reason for
# them to differ -- but a dot grows with the weight and a height must not.  At the origin the gap
# and the dot are both ROUND_THICK_1, so the top is simply two of them above the x-height, and it
# stays there in every master as the x-height and the ascender do.  Following the dot instead put
# the t at 515 at the origin and 580 at Black.
T_TOP  = XH + 2 * DOT_GAP
# The f's hook fills the ascender gap exactly: a quarter of an R1 round whose radius is half of
# it, so the hook's top is the ascender line and its left edge is the stem.
HOOK_R = (ASC_LC - XH) / 2.0


def _bar(cx, y=XH):
    # body 'down' at both ends, which is what the capital T's arm does: the tips land on the
    # bar's top corners and the underside is cut away.
    return rules.horizontal(cx - BAR_L / 2.0, cx + BAR_L / 2.0, y, left='down', right='down')


def build_t():
    """A stem through a bar.  The stem runs the whole height; nothing is buried."""
    return glyph(ord('t'), [_stem(T_TOP), _bar(0.0)], sb=(SB_STRAIGHT, SB_ROUND), notes=dict(
        construction=f"An R3 stem from the baseline to {T_TOP:.2f} with free R5 cuts at both ends, "
                     f"crossed by an R4 bar {BAR_L:.2f} long centred on the x-height.",
        height=f"{T_TOP:.2f}: the top of the i's dot at the axis origin -- two of the face's own "
               f"dot diameters above the x-height.  Those are the only two heights this face puts "
               f"between the x-height ({XH:g}) and the ascender ({ASC_LC:g}) and no reason was "
               f"found to make them differ.  Held at the origin, because a dot grows with weight "
               f"and a height must not: following the master's dot put the t at 515 here and 580 "
               f"at Black.  It sits {100*(T_TOP-XH)/(ASC_LC-XH):.0f}% of the way up the gap.",
        bar=f"{BAR_L:.2f} long -- the capital T's bar ({SS.BODY_MEDIUM:g}) at the lowercase factor "
            f"{S_K:.4f}, the same scaling the o takes from the O and the s from the S.  Centred on "
            f"the stem as the capital T's is; the rightward bias a text face gives its t comes "
            f"from serifs this face does not have.",
        spacing=f"{SB_STRAIGHT}/{SB_ROUND}: a stem on the left, the bar's R5 tip on the right.",
        deviations="none from R1-R9."))


def build_f():
    """A stem that turns over at the top, and the t's bar."""
    y_turn = ASC_LC - HOOK_R
    hook = rules.round_arc((HOOK_R, y_turn), HOOK_R, 90.0, 180.0)
    return glyph(ord('f'), [rules.stem(0.0, 0.0, y_turn, bottom='right', top=None), hook,
                            _bar(0.0)], sb=(SB_STRAIGHT, SB_ROUND), notes=dict(
        construction=f"An R3 stem from the baseline to {y_turn:.2f}, where it turns over into a "
                     f"quarter of an R1 round of radius {HOOK_R:g} centred at "
                     f"({HOOK_R:g}, {y_turn:.2f}); the t's bar crosses at the x-height.",
        hook=f"The radius is half the ascender gap, {ASC_LC:g} - {XH:g}, so the quarter fills that "
             f"gap exactly: its top is the ascender line and its left edge is the stem's own line. "
             f"Nothing about the hook is chosen -- the band is R1's at each angle, as the o's is.",
        stem_top="flat and buried where the hook takes over; the hook's own band carries the "
                 "silhouette from there.",
        bar="the t's bar, same length and same height, so f and t share one horizontal through a "
            "word as E, F and H do in the capitals.",
        spacing=f"{SB_STRAIGHT}/{SB_ROUND}.",
        deviations="none from R1-R9."))


GLYPHS = {'f': build_f, 'i': build_i, 'l': build_l, 't': build_t}
