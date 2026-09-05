"""
set_straight: the letters made only of stems and level arms -- E F H I L T.

Everything here is R3 stems and R4 horizontals ending in R5 cuts, unioned at
compile time (R6), built with rules.stem, rules.arm and rules.horizontal as
they stand.  Widths, tapers, the cut angle and the bearings all come from
lib/rules.py and lib/metrics.py; the only numbers chosen in this module are
proportions, and each is written into the glyph's notes.

Arms on the cap line and baseline (the E's top and bottom arms, the F's top
arm, the L's arm, the T's bar) are rules.arm: the outer edge level on the
metric line, R4's widths measured from it, the whole 1.8%-of-length taper on
the inner edge (SPEC R4).  Arms on no metric line (the E/F middle arm, the H
bar) are rules.horizontal, tapering symmetrically about a level centreline.

Junctions where an arm meets a stem on a metric line (E, F, L) are arranged
so the union never has to resolve a coincident or near-coincident edge: the
stem alone supplies the letter's whole left edge, the arm alone supplies the
whole top or bottom edge, and the two share exactly one point, the corner.
The arm's buried end is an R5 cut with its tip at that corner (cut_for's own
angle for face 'left'), so from the corner it runs into the stem's interior
at 90 - 20.6 = 69.4 degrees off the horizontal, meeting the arm's inner edge
about 19 units in, where the stem is 28 to 39 wide, well clear of both the
stem's edge and the stem's own (swallowed) foot or top cut.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from metrics import CAP, SB_STRAIGHT, SB_ROUND
from rules import glyph, stem, arm, horizontal, w_stem, w_horizontal, CUT_DEG, HORIZ_MID, HORIZ_TAPER, RING_W, RING_OFF

# ---- proportions (R8) --------------------------------------------------------
BODY_NARROW = 420          # E F L
BODY_MEDIUM = 558          # H T
MID_ARM_FRAC = 0.82        # E/F middle arm tip as a fraction of the body width.  0.75 (the
                           # face's narrow/medium ratio) read stubby beside the full arms in
                           # words; 0.82 leaves a shortfall of ~76 units, one and a half arm
                           # weights, enough to read as the shorter arm without looking cut off.
MID_Y = CAP/2 + HORIZ_MID/4   # centreline of the E middle arm and the H bar: raised a quarter
                              # of the arm's own weight above mid-height so the lower counter
                              # is the larger one (optical); tied to the arm weight so it
                              # scales with the stroke, not the cap
F_ARM_Y = MID_Y               # F's arm on E's line.  The conventional drop (F's arm a little
                              # lower than E's middle arm; tried at CAP/2, a quarter arm-weight
                              # down) was rejected by eye: at this arm weight the 12-unit step
                              # reads as a wobble between E and F in FEE/LEFT/THEFT and against
                              # the H bar in FIFTH, while F on E's line is not top-heavy, so E, F
                              # and H share one horizontal through a word

# ---- shared pieces -------------------------------------------------------------
BURIED_CUT_DEG = 90 - CUT_DEG                   # the angle a buried arm end runs into its stem, off the horizontal
INNER_SLOPE_DEG = math.degrees(math.atan(HORIZ_TAPER))   # slope of a metric-line arm's inner edge (1.03 deg)

def _stem_x(): return w_stem(0) / 2             # stem centre when the foot's left edge is x = 0

def _top_arm(x_s, x_tip):
    """Cap-line arm from a stem at x_s to a tip at x_tip.  Its top edge is level on CAP and starts
    at the stem's top-left corner, the stem's cut tip on CAP; its buried end is an R5 cut from that
    corner running down into the stem at BURIED_CUT_DEG; its free end is the R5 tip at the top-right
    corner, on CAP (body 'down')."""
    return arm(x_s - w_stem(CAP) / 2, x_tip, 'top', left='cut', right='cut')

def _bottom_arm(x_s, x_tip):
    """Baseline arm from a stem at x_s to a tip at x_tip.  Its bottom edge is level on 0 and starts
    at the foot tip; its buried end is an R5 cut from that corner running up into the stem at
    BURIED_CUT_DEG, so the stem alone supplies the letter's left edge; its free end is the R5 tip
    at the bottom-right corner, on 0 (body 'up')."""
    return arm(x_s - w_stem(0) / 2, x_tip, 'bottom', left='cut', right='cut')

def _mid_arm(x_s, x_tip, y):
    """Middle arm from the stem centre (buried, square) to a tip at x_tip; follows the top arm (tip up)."""
    return horizontal(x_s, x_tip, y, right='down')

def _arm_note(L):
    """How the arms on the metric lines are built, with this glyph's own numbers."""
    return (f"Cap-line and baseline arms are rules.arm (SPEC R4): outer edge level on the metric line, R4's "
            f"widths measured from it, {w_horizontal(L, 0):.1f} at the left end to {w_horizontal(L, 1):.1f} at "
            f"the right for a {L:.1f}-long arm ({HORIZ_TAPER*100:g}% of its length), the whole change on the "
            f"inner edge, which slopes {INNER_SLOPE_DEG:.1f} deg.  So the box is exactly 0..{CAP}, the R5 tips "
            f"sit exactly on the lines, and the letter's top and bottom edges are level like the H's tops and "
            f"the I's foot.  Arms on no metric line (the middle arm, the H bar) are rules.horizontal, the same "
            f"taper symmetric about a level centreline.")

_WEIGHT_NOTE = (f"Arms carry R4's {HORIZ_MID:g} against a stem of {w_stem(CAP/2):.1f} at mid-height, the A's "
                f"own bar-to-leg ratio, so the three-arm letters are the darkest in the face; any optical "
                f"reduction for stacked arms would be a spec-level R4 departure and is not taken here.  Two "
                f"reviewers read E, F, H and T as reverse-contrast beside I and L; a height-field alternative "
                f"(a horizontal's mid-length width following the O's vertical stroke, {RING_W + RING_OFF[1]:.1f} at "
                f"the baseline, {RING_W:.1f} at mid-height, {RING_W - RING_OFF[1]:.1f} at the cap) was built for "
                f"comparison only "
                f"(build/set_straight_r4_options.png) and awaits a SPEC decision, since it would also change "
                f"Z, the brackets and every bar in the face.")

def _buried_note(which):
    """The R5 buried end of an arm on a metric line."""
    into = {'top': 'down', 'bottom': 'up'}[which]
    corner = {'top': "the stem's cut tip at the cap", 'bottom': "the foot tip on the baseline"}[which]
    return (f"{which} arm starts at {corner} with its buried end an R5 cut from that corner running {into} "
            f"into the stem at {BURIED_CUT_DEG:g} deg off the horizontal, so the stem alone supplies the "
            f"left edge and the arm alone the {which} edge")

_OPEN_READINGS = ("the middle-arm ratio, middle-arm height and the R5 buried arm ends are readings the rules "
                  "leave open, recorded above")

# ---- glyphs ---------------------------------------------------------------------
def build_E():
    x_s = _stem_x()
    x_mid = BODY_NARROW * MID_ARM_FRAC
    top = _top_arm(x_s, BODY_NARROW)
    mid = _mid_arm(x_s, x_mid, MID_Y)
    bot = _bottom_arm(x_s, BODY_NARROW)
    st = stem(x_s, 0, CAP, bottom='right', top='right')
    L_top, L_bot = BODY_NARROW - (x_s - w_stem(CAP) / 2), BODY_NARROW - (x_s - w_stem(0) / 2)
    return glyph(ord('E'), [st, top, mid, bot], sb=(SB_STRAIGHT, SB_ROUND), notes=dict(
        construction=f"Narrow body {BODY_NARROW}: one R3 stem (rules.stem) cut at both ends with the body to "
                     f"the right (both cuts are swallowed by the arms), a top arm and a bottom arm (rules.arm) "
                     f"reaching the full body width with R5 tips at the top-right and bottom-right corners on "
                     f"the cap line and baseline, and a shorter middle arm (rules.horizontal) cut like the top one.",
        arms=_arm_note(L_top),
        mid_arm=f"tip at {MID_ARM_FRAC:g} of the body width (x={x_mid:g}, {BODY_NARROW - x_mid:g} short of "
                f"the full arms, {(BODY_NARROW - x_mid)/HORIZ_MID:.1f} arm weights); rules.horizontal, "
                f"centreline y={MID_Y:.2f} = CAP/2 + HORIZ_MID/4, raised a quarter of the arm weight so the "
                f"lower counter is the larger (optical); the same height as F's arm and H's bar.  0.75 (the "
                f"face's narrow/medium ratio) was tried first and read stubby beside the full arms in words; "
                f"0.85 nearly erased the shorter-arm cue; 0.80 and 0.82 both read, 0.82 kept.",
        junctions=f"{_buried_note('top')}; {_buried_note('bottom')}; middle arm starts at the stem centre "
                  f"with a square buried end.",
        weight=_WEIGHT_NOTE,
        spacing=f"{SB_STRAIGHT} beside the stem, {SB_ROUND} on the open side whose extremes are the arm "
                f"tips (pointed).",
        deviations=f"none from R1-R9; {_OPEN_READINGS}.",
        geometry=dict(stem_x=x_s, mid_arm_y=MID_Y, top_arm=dict(outer_y=CAP, length=L_top, w_left=w_horizontal(L_top, 0), w_right=w_horizontal(L_top, 1)),
                      bottom_arm=dict(outer_y=0, length=L_bot, w_left=w_horizontal(L_bot, 0), w_right=w_horizontal(L_bot, 1)))))

def build_F():
    x_s = _stem_x()
    x_mid = BODY_NARROW * MID_ARM_FRAC
    top = _top_arm(x_s, BODY_NARROW)
    mid = _mid_arm(x_s, x_mid, F_ARM_Y)
    st = stem(x_s, 0, CAP, bottom='right', top='right')
    L_top = BODY_NARROW - (x_s - w_stem(CAP) / 2)
    return glyph(ord('F'), [st, top, mid], sb=(SB_STRAIGHT, SB_ROUND), notes=dict(
        construction=f"The E without its bottom arm: narrow body {BODY_NARROW}, R3 stem (rules.stem) with a "
                     f"free R5 foot (tip at the lower-left corner on the baseline, cut rising toward the arms) "
                     f"and a top cut swallowed by the top arm; top arm (rules.arm) to the full width with its "
                     f"tip on the cap line and a middle arm (rules.horizontal) of E's length.",
        arms=_arm_note(L_top),
        mid_arm=f"same length and height as E's middle arm (tip x={x_mid:g}, centreline y={F_ARM_Y:.2f}), so "
                f"E, F and H share one horizontal through a word.  The conventional drop for F (tried at "
                f"CAP/2, {MID_Y - CAP/2:.2f} lower, a quarter arm-weight) was rejected by eye in FEE, LEFT, "
                f"THEFT and FIFTH: at this arm weight the step reads as a wobble between E and F and "
                f"against the H bar, and F on E's line is not top-heavy.",
        junctions=f"{_buried_note('top')}; middle arm starts at the stem centre with a square buried end.",
        weight=_WEIGHT_NOTE,
        spacing=f"{SB_STRAIGHT} beside the stem, {SB_ROUND} on the open side (arm tips).",
        deviations=f"none from R1-R9; {_OPEN_READINGS}.",
        geometry=dict(stem_x=x_s, mid_arm_y=F_ARM_Y, top_arm=dict(outer_y=CAP, length=L_top, w_left=w_horizontal(L_top, 0), w_right=w_horizontal(L_top, 1)))))

def build_L():
    x_s = _stem_x()
    bot = _bottom_arm(x_s, BODY_NARROW)
    st = stem(x_s, 0, CAP, bottom='right', top='right')
    L_bot = BODY_NARROW - (x_s - w_stem(0) / 2)
    return glyph(ord('L'), [st, bot], sb=(SB_STRAIGHT, SB_ROUND), notes=dict(
        construction=f"Narrow body {BODY_NARROW}: R3 stem (rules.stem) with a free R5 top (tip at the "
                     f"upper-left corner on the cap line, cut falling toward the arm) and a foot cut swallowed "
                     f"by the arm; one baseline arm (rules.arm) to the full width with its R5 tip at the "
                     f"bottom-right corner on the baseline.",
        arms=_arm_note(L_bot),
        junctions=f"{_buried_note('bottom')}.",
        spacing=f"{SB_STRAIGHT} beside the stem, {SB_ROUND} on the open side (arm tip).",
        deviations="none from R1-R9; the R5 buried arm end is a reading the rules leave open, recorded above.",
        geometry=dict(stem_x=x_s, bottom_arm=dict(outer_y=0, length=L_bot, w_left=w_horizontal(L_bot, 0), w_right=w_horizontal(L_bot, 1)))))

def build_H():
    x_l = _stem_x()
    x_r = BODY_MEDIUM - w_stem(0) / 2
    left  = stem(x_l, 0, CAP, bottom='right', top='right')
    right = stem(x_r, 0, CAP, bottom='left',  top='left')
    bar   = horizontal(x_l, x_r, MID_Y)
    return glyph(ord('H'), [left, right, bar], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=dict(
        construction=f"Medium body {BODY_MEDIUM} measured at the feet: two R3 stems (rules.stem), each cut "
                     f"at both ends with the body toward the other stem, and an R4 bar (rules.horizontal) "
                     f"between the stem centres, both ends buried.",
        cuts="tips at the four outer corners, cuts receding toward the middle: R5's own definition (tip "
             "at the corner farther from the letter's centre), so the right stem mirrors the left.",
        bar=f"rules.horizontal, centreline y={MID_Y:.2f}, the same height as the E middle arm; R4's symmetric "
            f"{HORIZ_TAPER*100:g}%-of-length taper left to right about the level centreline (R7).",
        body=f"{BODY_MEDIUM} is the outer edge to outer edge at the baseline; at the cap the stems' taper "
             f"narrows the letter by {(w_stem(0) - w_stem(CAP))/2:.1f} a side.",
        weight=_WEIGHT_NOTE,
        spacing=f"{SB_STRAIGHT}/{SB_STRAIGHT}, stems both sides.",
        deviations="none."))

def build_I():
    x_s = _stem_x()
    st = stem(x_s, 0, CAP, bottom='right', top='right')
    return glyph(ord('I'), [st], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=dict(
        construction=f"A single R3 stem (rules.stem), {w_stem(0):g} at the baseline tapering to "
                     f"{w_stem(CAP):g} at the cap, both ends free with R5 cuts.",
        cuts="no body to either side, so the side is chosen by R7: body 'right' at both ends puts the "
             "foot tip at the lower-left corner on the baseline and cuts away the upper-right corner, "
             "heavy lower-left and light upper-right; it also matches F's foot and L's top, so every "
             "free stem end on a left stem in the face is cut the same way.",
        spacing=f"{SB_STRAIGHT}/{SB_STRAIGHT}.",
        deviations="none; no R8 width applies to I."))

def build_T():
    L = BODY_MEDIUM
    bar = arm(0, L, 'top', left='cut', right='cut')
    x_s = L / 2
    y_top = CAP - w_horizontal(L, 0.5) / 2          # the bar's mid-thickness at the stem: buried
    st = stem(x_s, 0, y_top, bottom='right', top=None)
    return glyph(ord('T'), [bar, st], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=f"Medium body {BODY_MEDIUM}: an R4 bar (rules.arm) the full width with its top edge "
                     f"level on the cap line, both ends R5-cut with tips at the top corners on the cap line "
                     f"(left cut body 'down', right cut body 'down'), and an R3 stem (rules.stem) centred "
                     f"under it, running from the baseline up into the bar (buried) with a free R5 foot.",
        arms=_arm_note(L),
        bar=f"rules.arm: top edge on {CAP} from x=0 to x={L}; {w_horizontal(L, 0):.1f} thick at the left end, "
            f"{w_horizontal(L, 1):.1f} at the right, the {HORIZ_TAPER*L:.1f}-unit R4 loss taken on the "
            f"underside, which rises {INNER_SLOPE_DEG:.1f} deg left to right.  Both tips on the cap line.",
        stem_top=f"flat and buried at y={y_top:.2f}, half the bar's mid-length width below its top edge, "
                 f"{y_top - (CAP - w_horizontal(L, 0.5)):.1f} above the bar's underside at the stem; a stem "
                 f"top on {CAP} itself would be an edge coincident with the bar's top edge, which the union "
                 f"should not be asked to resolve.",
        foot="body 'right' (tip at the lower-left corner, cut rising to the right): the letter is "
             "symmetric about the stem so R5's 'farther from the centre' does not decide it; R7 does, "
             "keeping the full corner at the lower left and matching I, F and L.",
        weight=_WEIGHT_NOTE,
        spacing=f"{SB_ROUND}/{SB_ROUND}: the extremes are the bar's pointed tips over open space.",
        deviations="none from R1-R9.",
        geometry=dict(stem_x=x_s, stem_top_y=y_top, bar=dict(outer_y=CAP, length=L, w_left=w_horizontal(L, 0), w_right=w_horizontal(L, 1)))))

GLYPHS = {'E': build_E, 'F': build_F, 'H': build_H, 'I': build_I, 'L': build_L, 'T': build_T}
