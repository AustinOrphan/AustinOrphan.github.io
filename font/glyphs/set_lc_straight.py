"""The lowercase stems: i and l, and the dot they share with the face's punctuation.

Neither letter decides anything on its own.  The stem is R3's field, cut at both ends by the
convention the capital I states and every free stem end in the face follows; the dot is the
period, at the clearance the exclamation mark already uses.  What is left to say is only how tall
each stem is, and the lowercase metrics have already said that.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from metrics import ASC_LC, CAP, DESC_LC, OVER_ROUND, SB_ROUND, SB_STRAIGHT, XH
from pen import (add, arc_band, Contour, fit_cubics, fit_ranges, from_ang, mul, norm,
                 perp, sub, unit)
import rules
from rules import glyph, w_stem, RING_W
from glyphs import set_punct as SP
from glyphs import set_straight as SS
from glyphs import set_round as SR
from glyphs import set_lc_round as LR

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


HOOK_SAMP = 150                 # spine samples round the hook
HOOK_NSEG = 16                  # cubics per edge, frozen at the axis origin


def _hook_spine(wf, ring_w, ring_off):
    """(point, unit tangent, width) round the f's hook.

    The hook is NOT an R1 arc.  An arc carries R1's whole band -- 57.86 units at the junction --
    and the stem it grows out of is 26 there, so the two met in a 2.2x step.  It is the n's
    shoulder instead: the same quarter turn, with the width blended from R3's field at the stem to
    R1's own top band at the top by the spine's own tangent.  At the junction the tangent is
    vertical, so the hook starts at exactly the stem's width; at the top it is horizontal, so it
    ends at exactly the band the o has there."""
    apex_w = LR._band_at(90.0, ring_w, ring_off)
    y_turn = ASC_LC - HOOK_R - apex_w / 2.0
    cx, cy = HOOK_R, y_turn
    pts = []
    for i in range(HOOK_SAMP + 1):
        th = math.radians(180.0 - 90.0 * i / HOOK_SAMP)
        p = (cx + HOOK_R * math.cos(th), cy + HOOK_R * math.sin(th))
        t = unit((math.sin(th), -math.cos(th)))          # travelling 180 -> 90, i.e. up and over
        turn = abs(t[0]); k = turn * turn * (3 - 2 * turn)
        pts.append((p, t, wf(p[1]) * (1 - k) + apex_w * k))
    return pts, y_turn


def _hook_edges(pts):
    L = [add(p, mul(perp(t), w / 2.0)) for p, t, w in pts]
    Rt = [sub(p, mul(perp(t), w / 2.0)) for p, t, w in pts]
    return L, Rt


_HOOK_RANGES = (lambda L, Rt: (fit_ranges(L, LR._g_tan(L), HOOK_NSEG),
                               fit_ranges(Rt[::-1], [mul(t, -1) for t in LR._g_tan(Rt)[::-1]], HOOK_NSEG))
                )(*_hook_edges(_hook_spine(LR._w1, rules.RING_W_1, rules.RING_OFF_1)[0]))


def build_f():
    """A stem that turns over at the top, and the t's bar."""
    pts, y_turn = _hook_spine(w_stem, RING_W, rules.RING_OFF)
    L, Rt = _hook_edges(pts)
    rg_out, rg_in = _HOOK_RANGES
    so, eo = fit_cubics(L, LR._g_tan(L), tol=9e9, ranges=[tuple(r) for r in rg_out])
    si, ei = fit_cubics(Rt[::-1], [mul(x, -1) for x in LR._g_tan(Rt)[::-1]], tol=9e9,
                        ranges=[tuple(r) for r in rg_in])
    k = Contour(L[0])
    for sg in so: k.curve_to(*sg)
    k.line_to(Rt[-1])
    for sg in si: k.curve_to(*sg)
    return glyph(ord('f'), [rules.stem(0.0, 0.0, y_turn, bottom='right', top=None), k.ccw(),
                            _bar(0.0)], sb=(SB_STRAIGHT, SB_ROUND), notes=dict(
        construction=f"An R3 stem from the baseline to {y_turn:.2f}, where it turns over through a "
                     f"quarter of radius {HOOK_R:g}; the t's bar crosses at the x-height.",
        hook=f"The n's shoulder, not an R1 arc.  An arc carries R1's whole band -- "
             f"{LR._band_at(180.0):.2f} at the junction -- against a stem of "
             f"{w_stem(y_turn):.2f} there, and the two met in a step of 2.2 to 1.  This blends "
             f"R3's field into R1's own top band ({LR._band_at(90.0):.2f}) by the spine's own "
             f"tangent, exactly as the n's shoulder does: vertical at the junction, so the hook "
             f"starts at the stem's width; horizontal at the top, so it ends at the o's band.",
        radius=f"{HOOK_R:g}, half the ascender gap, so the quarter fills it: the hook's top edge "
               f"lands on the ascender line and its left edge is the stem's own line.",
        knots=f"{HOOK_NSEG} cubics per edge, taken once at the axis origin and held.  Worst fit "
              f"{max(eo, ei):.3f}.",
        bar="the t's bar, same length and height, so f and t hold one horizontal through a word.",
        spacing=f"{SB_STRAIGHT}/{SB_ROUND}.",
        deviations="none from R1-R9."))


# ---- j ------------------------------------------------------------------------------
# The i's stem and the i's dot, with the capital J's hook under it at the lowercase factor.  Every
# number below is the capital's scaled by S_K except the depth, which is the g's: a lowercase
# descender goes as deep as the lowercase descender line, not as deep as the capital J's baseline.
J_R         = SS.BODY_NARROW / 2.0 * S_K        # 118.12, the capital J's bowl scaled
J_BOT       = DESC_LC - OVER_ROUND              # -195, the g's own depth
J_C         = (J_R, J_BOT + J_R)
J_END       = SR.J_END                          # 165 deg: where the bowl ends and the curl begins


def build_j():
    """The i, with the capital J's hook."""
    x_s, a1, y0 = SR._light_junction(J_C, J_R, +1)
    arc = rules.round_arc(J_C, J_R, J_END, a1 + 360.0)
    st = rules.stem(x_s, y0, XH, bottom=None, top='right')
    fill = SR._fill_in(x_s, J_C, J_R)
    return glyph(ord('j'), [arc, st, fill, SP._dot(x_s, DOT_CY)],
                 sb=(SB_ROUND, SB_STRAIGHT), notes=dict(
        construction=f"The i's stem and the i's dot over the capital J's hook at the lowercase "
                     f"factor {S_K:.4f}: an R1 arc of radius {J_R:.2f} centred "
                     f"{tuple(round(v,2) for v in J_C)} from {J_END:g} deg round to the stem.",
        depth=f"The bowl sits on {J_BOT:g}, the descender line with the round's own overshoot -- "
              f"the g's depth, not the capital J's baseline.",
        terminal=f"The bowl ends at {J_END:g} deg on R1's own radial cut, as the c's and the e's "
                 f"ends do -- NOT on the capital J's curl.  The curl cannot survive the scaling: "
                 f"its radius is a length and scales to {SR.J_CURL_R * S_K:.2f}, while the band it has "
                 f"to carry is ABSOLUTE and runs 32.34 at Light to 100.14 at Black.  Once the "
                 f"band passes the radius the solved counter goes inside out -- measured, the "
                 f"depth d falls to -1.10 at WEIGHT 1.45 and the construction throws, and by 2.00 "
                 f"it is -38.27 and would build something wrong in silence.  The capital's own "
                 f"radius is 110 and never meets that.  A curl is not needed here in any case: the "
                 f"capital's argument for it is that a J without one reads as a U, and a j has a "
                 f"dot and a stem.",
        dot=f"The i's, at the i's height: centre {DOT_CY:.2f}.",
        spacing=f"{SB_ROUND}/{SB_STRAIGHT}: the curl on the left, the stem on the right.",
        deviations="none from R1-R9."))


GLYPHS = {'f': build_f, 'i': build_i, 'j': build_j, 'l': build_l, 't': build_t}
