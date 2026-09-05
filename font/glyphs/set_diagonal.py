"""
set_diagonal: the letters made of R2 diagonals -- V W M N K X Y Z.

Every stroke is an R2 diagonal (rules.diagonal), an R3 stem (rules.stem) or an
R4 metric-line arm (rules.arm); every free end is the R5 cut cut_for() builds,
passed to the pen unchanged; every junction is a plain overlap unioned at
compile time (R6).  The A's leg angles and apex angle are read off
glyphs/core.py at import, never retyped.  The only numbers chosen here are
proportions and junction heights, each written into the glyph's notes.

pen.stroke() reads a cut's tip side in cut_for's OUTWARD frame at both ends, so
nothing in this module compensates for the side of a start-end cut: X and Y are
rules.diagonal and rules.stem calls, K's stem is rules.stem, Z's horizontals are
rules.arm, and every free end anywhere in the module is cut_for's own spec
handed straight to the pen.  The module carries no local re-implementation of a
rules constructor and no local cut angle.

Two pieces are still built here from pen primitives, because lib/rules.py has
no primitive for either.  Both are about placement and about which face an end
presents, not about the rules' weights, angles or cuts:

1. `_centres()`: the centre-line ends of a stroke fixed by where its CORNERS
   land.  R6 puts a point where two OUTER EDGES meet and R5 puts a cut's tip at
   a corner, so what these letters fix is a corner, not a centre-line, while
   rules.diagonal/rules.stem take centre-line ends.  Given the target corner at
   each end and which side of the stroke it is on, the centre-line is solved by
   fixed-point iteration (the R2 taper leaves the edges and the centre-line
   about half a degree apart, so one step will not do it).  `_diag()` hands the
   result to rules.diagonal, so X, Y and K are diagonals with each R5 tip
   sitting exactly on its corner, the way core.py places the A's foot tips.
   It is the diagonal's analogue of set_straight's `_stem_x()`.

2. `_placed_stroke()`, the pen.stroke() call rules.diagonal and rules.stem
   themselves make, for the two ends rules.diagonal has no way to ask for:

   a. the BURIED ends where two strokes meet in a point (V, W, M, N) and where
      Z's diagonal enters its arms (`_point_cuts`).  Two strokes meeting in a
      point cannot both end flat (either flat end pokes out past the other
      stroke's outer edge) and cannot be cut along each other's outer edge
      (that lays an internal edge exactly on the outline).  Each end is instead
      cut from the tip two thirds of the way from its own outer edge toward the
      other stroke's, so the two ends nest inside one another, each end's
      material lies entirely inside the other stroke, and the union's boundary
      at the tip is exactly the two outer edges.

   b. a free R5 end on a face the end's index does not give (K's arm and leg,
      whose upper and lower ends both present the letter's RIGHT face and so
      take R5's cut turned 90 deg).  rules.diagonal hardcodes face 'bottom' at
      p0 and 'top' at p1; `_end()` takes the face as well, and the cut is still
      cut_for's untouched spec, checked to have its tip on the placed corner.

R5 fixes the ANGLE of a terminal cut and nothing else, so a cut's LENGTH is
whatever the stroke makes it: width over the sine of the wedge the cut makes
with the stroke's edge, the wedge being the stroke's angle to the face it
presents less CUT_DEG.  Both factors move across this group -- a stem foot is
at its widest and meets its cut nearly square, an X foot is as wide but lies
far over, a Y arm at the cap is thin and lies further over still -- so one
rule, followed exactly, produces terminals of very different length and
bluntness.  Every glyph records its own in `terminal_cuts` and
`terminal_spread()` prints the group's, shortest first.  Nothing here corrects
for it: capping a cut on a shallow stroke would be a change to R5 itself,
reaching K, Z, the 7 and the asterisk together, so it is raised with SPEC
instead of patched glyph by glyph.

Proportions that R8 cannot satisfy at once are settled the same way in every
glyph and recorded in its notes: where a letter has a vertical stem (N, K, Y)
the A's apex angle and the medium width 558 cannot both hold, and the width
wins because it is the explicit table; the diagonal then takes the angle the
width and the junction height dictate.  Junction heights (K, X, Y) sit on the
face's optical middle, CAP/2 + HORIZ_MID/4, the line set_straight put the E's
middle arm and the H's bar on, so the middles of E H K X Y agree in a word.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib')); sys.path.insert(0, FONT)
from pen import stroke, cut_for, ang, perp, unit, sub, mul, dot
from metrics import CAP, OVER_POINT, SB_STRAIGHT, SB_ROUND, UPM
from rules import glyph, stem, diagonal, arm, w_slash, w_backslash, w_stem, w_horizontal, CUT_DEG, HORIZ_MID, HORIZ_TAPER
from glyphs import core

# ---- the exemplars, read off core.py ------------------------------------------
_A = core.build_A()['notes']
LEG_SLASH, LEG_BACK = _A['leg_angles']          # 68.71 and 111.29 degrees from the horizontal
APEX_DEG = _A['apex_angle']                     # 42.58
HALF_APEX = APEX_DEG / 2                        # a leg's lean off the vertical, 21.29
TIP_Y, POINT_Y = CAP + OVER_POINT, -OVER_POINT  # where a point's tip sits (R6)

# ---- proportions (R8) ---------------------------------------------------------
BODY_MEDIUM = 558                               # V N K X Y Z: the A's foot spread
W_MAX_ADV = round(0.95 * UPM)                   # R8: the W is steepened only until its advance is 950
MID_Y = CAP / 2 + HORIZ_MID / 4                 # the face's optical middle (see module docstring)

# ---- local constructors (see module docstring) --------------------------------
def _centres(E0, s0, E1, s1, wf=None, iters=16):
    """Centre-line ends (c0, c1) of a stroke whose corner on side s0 sits exactly on E0 (the
    lower end) and whose corner on side s1 sits on E1.  s = +1 is the stroke's own left side
    (left of p0->p1), -1 its right, 0 means the point is the centre-line end itself.  Widths
    from the R2 field by the stroke's lean (or wf), taken at each end's centre height."""
    if wf is None: wf = w_slash if E1[0] >= E0[0] - 1e-9 else w_backslash
    c0, c1 = E0, E1
    for _ in range(iters):
        n = perp(unit(sub(c1, c0)))
        c0, c1 = sub(E0, mul(n, s0 * wf(c0[1]) / 2)), sub(E1, mul(n, s1 * wf(c1[1]) / 2))
    return c0, c1

def _tip_side(s, at):
    """pen.stroke names a cut's tip corner in cut_for's OUTWARD frame -- along p0->p1 at the
    upper end, along p1->p0 at the lower one.  A corner named on the stroke's own left/right
    (the frame _centres uses) is therefore itself at the upper end and mirrored at the lower."""
    return ('L' if s > 0 else 'R') if at == 1 else ('R' if s > 0 else 'L')

def _end(spec, s, at, p_end, p_other):
    """pen.stroke() end spec for the end `at` (0 = p0, the lower end; 1 = p1) whose corner
    placed by _centres is on the stroke's side s.  spec:

      None                free (flat)
      body                the free R5 end on the face the end index gives ('bottom' at p0,
                          'top' at p1): cut_for(face, body) exactly as rules.diagonal and
                          rules.stem build it
      (face, body)        the free R5 end on the face NAMED.  R5 keys its cut to the face an
                          end presents -- 20.6 deg off the horizontal on a top or bottom face,
                          the same cut turned 90 deg on a left or right one -- and which face
                          that is does not follow from which end of the stroke it is: K's arm
                          and leg both present the letter's right face at their upper and lower
                          ends.  rules.diagonal cannot say this (it hardcodes 'bottom' at p0,
                          'top' at p1), so a stroke with such an end is built here.
      a number            a buried point cut leaving the placed corner at that absolute angle
                          (_point_cuts).

    Either free form is cut_for's untouched spec, with a check that its tip is the placed corner."""
    if spec is None: return ('flat',)
    if isinstance(spec, (str, tuple)):
        face, body = spec if isinstance(spec, tuple) else (('top' if at == 1 else 'bottom'), spec)
        cut = cut_for(p_end, p_other, face, body, CUT_DEG)
        if cut[2] != _tip_side(s, at): raise ValueError(f'R5 tip ({cut[2]}) is not the placed corner at {p_end}')
        return cut
    return ('cut', float(spec), _tip_side(s, at))

def _short(a, b):
    """The signed short way round from direction a to direction b, degrees."""
    return (b - a + 180) % 360 - 180

def _bisect(a, b):
    """The direction halfway from a to b the short way round."""
    return a + _short(a, b) / 2

def _point_cuts(a, b):
    """Cut angles for two strokes A and B meeting in a point whose outer edges leave the
    tip at absolute angles a and b: (cut for A, cut for B), each two thirds of the way
    from its own outer edge to the other's (module docstring, item 2)."""
    d = _short(a, b)
    return a + 2 * d / 3, b - 2 * d / 3

def _placed_stroke(E0, s0, E1, s1, end0=None, end1=None, wf=None):
    """The pen.stroke() call rules.diagonal/rules.stem make, for a stroke rules.diagonal
    cannot express: one with a buried point end (V W M N Z) or with a free R5 end on a face
    the end index does not give (K).  Its corner on side s0 at the lower end sits exactly on
    E0 and its corner on side s1 on E1 (_centres), each being that end's cut tip (_end).
    The widths, the taper and every cut angle are still the rules' own."""
    if E0[1] > E1[1]: E0, s0, E1, s1, end0, end1 = E1, s1, E0, s0, end1, end0
    if wf is None: wf = w_slash if E1[0] >= E0[0] - 1e-9 else w_backslash
    c0, c1 = _centres(E0, s0, E1, s1, wf)
    return stroke(c0, c1, wf(c0[1]), wf(c1[1]), _end(end0, s0, 0, c0, c1), _end(end1, s1, 1, c1, c0))

def _diag(E0, s0, E1, s1, bottom=None, top=None):
    """rules.diagonal with its centre-line ends solved (_centres) so the corner on side s0
    sits on E0 and the corner on side s1 on E1 (s = 0: the point is the centre-line end,
    flat and buried).  Each R5 tip is then exactly the placed corner, which is checked.
    An end given as (face, body) names the face it presents, which rules.diagonal has no way
    to be told, so that stroke goes through _placed_stroke -- the same pen.stroke call, the
    same R2 widths, the same cut_for cut."""
    if E0[1] > E1[1]: E0, s0, E1, s1, bottom, top = E1, s1, E0, s0, top, bottom
    if isinstance(bottom, tuple) or isinstance(top, tuple):
        return _placed_stroke(E0, s0, E1, s1, end0=bottom, end1=top)
    c0, c1 = _centres(E0, s0, E1, s1)
    if bottom: _end(bottom, s0, 0, c0, c1)
    if top: _end(top, s1, 1, c1, c0)
    return diagonal(c0, c1, bottom=bottom, top=top)

def _stem_edge_angle(x, y_tip, side, y_far):
    """Absolute direction of a stem's `side` ('L'/'R') edge leaving its corner at y_tip toward y_far."""
    s = 1 if side == 'L' else -1
    return ang(sub((x - s * w_stem(y_far) / 2, y_far), (x - s * w_stem(y_tip) / 2, y_tip)))

def _spread(h, lean_deg):
    """Horizontal run of an edge leaning lean_deg off the vertical over a height h."""
    return h * math.tan(math.radians(lean_deg))

def _wedge(contour, tip):
    """(wedge angle in degrees, cut length) at the terminal whose tip corner is `tip`: the
    angle between the two outline edges leaving the tip, and the length of the shorter
    one (the cut).  For notes and verification only."""
    pts = contour.flatten(); i = min(range(len(pts)), key=lambda k: math.hypot(pts[k][0] - tip[0], pts[k][1] - tip[1]))
    a, b = sub(pts[i - 1], pts[i]), sub(pts[(i + 1) % len(pts)], pts[i])
    wedge = math.degrees(math.acos(max(-1.0, min(1.0, dot(a, b) / (math.hypot(*a) * math.hypot(*b))))))
    return wedge, min(math.hypot(*a), math.hypot(*b))

def _terminals(*items):
    """{label: (wedge angle deg, cut length units)} for every FREE R5 terminal of a glyph,
    measured on the built contour; items are (label, contour, tip corner).  R5 fixes a cut's
    ANGLE (CUT_DEG off the face's axis) and says nothing about its length, and the length
    that angle produces is the stroke's width divided by the sine of the wedge -- the angle
    between the cut and the stroke's own edge -- so it grows as a stroke lies over toward its
    face.  Recorded in every glyph's notes here so the spread is on the record;
    terminal_spread() collects the whole group's."""
    out = {}
    for lab, c, t in items:
        w, l = _wedge(c, t)
        out[lab] = dict(wedge_deg=round(w, 1), cut_len=round(l, 1), cut_in_widths=round(1 / math.sin(math.radians(w)), 2))
    return out

def _survey(exclude=None, own=None):
    """[(cut length, wedge deg, glyph, terminal)] for every free R5 terminal in the group,
    shortest cut first, measured live off the builders.  A builder that wants the group's
    spread in its own notes passes its own name and its own _terminals() dict, so it is not
    rebuilt inside itself; no builder other than K calls this, so there is no recursion."""
    rows = [(v['cut_len'], v['wedge_deg'], exclude, lab) for lab, v in (own or {}).items()]
    for name, fn in GLYPHS.items():
        if name == exclude: continue
        rows += [(v['cut_len'], v['wedge_deg'], name, lab) for lab, v in fn()['notes'].get('terminal_cuts', {}).items()]
    return sorted(rows)

def terminal_spread():
    """The group's R5 terminal record, shortest cut first (see the module docstring's note on
    terminal length).  Kept as a function rather than a constant so it is always measured off
    the glyphs as they currently build."""
    return _survey()

# ---- V --------------------------------------------------------------------------
def build_V():
    half = _spread(CAP - POINT_Y, HALF_APEX)                 # 279: the A's half foot spread
    T = (half, POINT_Y); TL, TR = (0.0, CAP), (2 * half, CAP)
    cL, cR = _point_cuts(ang(sub(TL, T)), ang(sub(TR, T)))   # buried cuts nested at the point
    left = _placed_stroke(T, +1, TL, +1, end0=cL, end1='right')    # outer edge = left edge, T to the cap-line tip
    right = _placed_stroke(T, -1, TR, -1, end0=cR, end1='left')
    cuts = _terminals(('top left', left, TL), ('top right', right, TR))
    return glyph(ord('V'), [left, right], sb=(SB_ROUND, SB_ROUND), notes=dict(
        terminal_cuts=cuts,
        construction=('The A\'s legs inverted: two R2 diagonals leaning HALF_APEX off the vertical whose outer '
                      'edges meet in a point at y = -OVER_POINT (R6) and whose tops are R5 cuts with the tip at the '
                      'outer corner on the cap line (left leg body \'right\', right leg body \'left\'); the buried '
                      'lower ends nest per _point_cuts.'),
        body_width=2 * half, half_apex_deg=HALF_APEX, point=T, point_cuts_deg=_point_cuts(LEG_BACK, LEG_SLASH),
        proportion=('R8 medium: the body is not set to 558 and then checked, it IS the A\'s foot spread -- the two '
                    'legs are laid at the A\'s own half-apex lean from the point at -OVER_POINT up to the cap line, '
                    f'which comes to {2 * half:.2f}, the 558 of R8\'s table to a twentieth of a unit.'),
        vertices=('one point, at the baseline overshoot: the two legs\' outer edges are the union\'s whole boundary '
                  'there and meet at T with no spur or notch (zoomed at 4x from the compiled outline).'),
        sb='SB_ROUND both sides: cut tips above, a point below', deviations='none'))

# ---- W --------------------------------------------------------------------------
def build_W():
    # With the A's lean the four legs would span 2*716*tan + 2*732*tan = 1129 units, so the
    # lean is reduced until the advance is exactly W_MAX_ADV (R8).
    body = W_MAX_ADV - 2 * SB_ROUND
    h_out, h_in = CAP - POINT_Y, TIP_Y - POINT_Y
    lean = math.degrees(math.atan(body / (2 * h_out + 2 * h_in)))
    r_out, r_in = _spread(h_out, lean), _spread(h_in, lean)
    T1 = (r_out, POINT_Y); apex = (r_out + r_in, TIP_Y); T2 = (r_out + 2 * r_in, POINT_Y)
    TL, TR = (0.0, CAP), (2 * r_out + 2 * r_in, CAP)
    # points: outer-edge directions from each tip, then the nested buried cuts
    c1a, c2a = _point_cuts(ang(sub(TL, T1)), ang(sub(apex, T1)))
    c2b, c3b = _point_cuts(ang(sub(T1, apex)), ang(sub(T2, apex)))
    c3a, c4a = _point_cuts(ang(sub(apex, T2)), ang(sub(TR, T2)))
    leg1 = _placed_stroke(T1, +1, TL, +1, end0=c1a, end1='right')
    leg2 = _placed_stroke(T1, -1, apex, +1, end0=c2a, end1=c2b)      # outer edge swaps sides: lower-right at T1, upper-left at the apex
    leg3 = _placed_stroke(T2, +1, apex, -1, end0=c3a, end1=c3b)
    leg4 = _placed_stroke(T2, -1, TR, -1, end0=c4a, end1='left')
    cuts = _terminals(('top left', leg1, TL), ('top right', leg4, TR))
    return glyph(ord('W'), [leg1, leg2, leg3, leg4], sb=(SB_ROUND, SB_ROUND), notes=dict(
        terminal_cuts=cuts,
        construction=('Two vees: four R2 diagonals, points at y = -OVER_POINT under each vee and at y = CAP + '
                      'OVER_POINT where the inner legs meet (R6), outer tops R5 cuts with the tip at the outer corner '
                      'on the cap line; every buried end nests per _point_cuts.  All four legs share one lean so the '
                      'letter is symmetric.'),
        body_width=TR[0], lean_deg=lean, apex_deg=2 * lean, points=(T1, apex, T2),
        vertices=('three points -- two at the baseline overshoot, one at the cap overshoot -- each the meeting of two '
                  'outer edges, all three zoomed at 4x from the compiled outline: clean, no spur, no notch.'),
        deviations=(f'R8: at the A\'s lean ({HALF_APEX:.2f} deg) the body would be '
                    f'{2 * _spread(h_out, HALF_APEX) + 2 * _spread(h_in, HALF_APEX):.0f} units and the advance well past 0.95 em; '
                    f'the legs are steepened to {lean:.2f} deg off the vertical (apex {2 * lean:.2f} deg), the least that '
                    f'brings the advance to {W_MAX_ADV}, as R8 directs for the W.')))

# ---- M --------------------------------------------------------------------------
def build_M():
    xL = w_stem(0) / 2                                          # left stem: left foot corner at x = 0
    P_TL = (xL - w_stem(TIP_Y) / 2, TIP_Y)                      # top-left point: stem's left edge meets the leg's upper edge
    run = _spread(TIP_Y - POINT_Y, HALF_APEX)                   # a leg's run at the A's lean, point to point
    T = (P_TL[0] + run, POINT_Y)                                # the vee's point, on the baseline overshoot
    P_TR = (T[0] + run, TIP_Y)
    xR = P_TR[0] - w_stem(TIP_Y) / 2
    F_L, F_R = (xL - w_stem(0) / 2, 0.0), (xR + w_stem(0) / 2, 0.0)   # the two R5 foot tips, on the baseline
    aL_stem, aL_leg = _stem_edge_angle(xL, TIP_Y, 'L', 0), ang(sub(T, P_TL))
    aR_stem, aR_leg = _stem_edge_angle(xR, TIP_Y, 'R', 0), ang(sub(T, P_TR))
    cLs, cLl = _point_cuts(aL_stem, aL_leg); cRs, cRl = _point_cuts(aR_stem, aR_leg)
    cTl, cTr = _point_cuts(ang(sub(P_TL, T)), ang(sub(P_TR, T)))
    stemL = _placed_stroke(F_L, +1, P_TL, +1, end0='right', end1=cLs, wf=w_stem)
    stemR = _placed_stroke(F_R, -1, P_TR, -1, end0='left', end1=cRs, wf=w_stem)
    legL = _placed_stroke(T, +1, P_TL, -1, end0=cTl, end1=cLl)   # outer edge: lower-left at T, upper-right at the stem
    legR = _placed_stroke(T, -1, P_TR, +1, end0=cTr, end1=cRl)
    body = F_R[0]                                               # right foot's right corner
    cuts = _terminals(('left foot', stemL, F_L), ('right foot', stemR, F_R))
    return glyph(ord('M'), [stemL, legL, legR, stemR], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=dict(
        terminal_cuts=cuts,
        construction=('Two R3 stems with R5 feet (tips at the outer foot corners on the baseline, cuts rising '
                      'inward) and, between them, the V: two R2 diagonals at the A\'s lean whose outer edges meet in '
                      'a point at y = -OVER_POINT and whose upper edges meet the stems\' outer edges in points at '
                      'y = CAP + OVER_POINT (R6); the three points\' buried ends nest per _point_cuts.'),
        body_width=body, half_apex_deg=HALF_APEX, points=(P_TL, T, P_TR), stem_x=(xL, xR), leg_run=run, feet=(F_L, F_R),
        vertices=('three points: the two shoulders at the cap overshoot, where each stem\'s outer edge meets its '
                  'leg\'s upper edge, and the vee at the baseline overshoot.  All three zoomed at 4x from the '
                  'compiled outline: two edges, one tip, no spur, no notch.'),
        proportion=(f'M is not in R8\'s width table, so the width follows from the construction: R8 asks pointed '
                    f'constructions to use the A\'s apex angle, and at the A\'s lean each leg runs {run:.1f} units '
                    f'over the {TIP_Y - POINT_Y:g} from point to point, so with the stems the body is {body:.1f} '
                    f'(foot corner to foot corner), {body - BODY_MEDIUM:.1f} over the medium 558 and '
                    f'{100 * body / UPM:.0f}% of the em.  Narrowing the vee to reach 558 would steepen the legs to '
                    f'{math.degrees(math.atan((BODY_MEDIUM - 2 * xL + w_stem(TIP_Y)) / 2 / (TIP_Y - POINT_Y))):.1f} '
                    f'deg off the vertical and give up the A\'s angle for a letter R8 does not size.'),
        deviations='none: width from the construction (see proportion)'))

# ---- N --------------------------------------------------------------------------
def build_N():
    xL = w_stem(0) / 2
    P_TL = (xL - w_stem(TIP_Y) / 2, TIP_Y)                      # top-left point
    P_BR = (BODY_MEDIUM, POINT_Y)                               # bottom-right point, on the body's right edge
    xR = P_BR[0] - w_stem(POINT_Y) / 2
    F_L, TOP_R = (xL - w_stem(0) / 2, 0.0), (xR + w_stem(CAP) / 2, CAP)
    aL_stem, aL_diag = _stem_edge_angle(xL, TIP_Y, 'L', 0), ang(sub(P_BR, P_TL))
    aR_stem, aR_diag = _stem_edge_angle(xR, POINT_Y, 'R', CAP), ang(sub(P_TL, P_BR))
    cLs, cLd = _point_cuts(aL_stem, aL_diag); cRs, cRd = _point_cuts(aR_stem, aR_diag)
    stemL = _placed_stroke(F_L, +1, P_TL, +1, end0='right', end1=cLs, wf=w_stem)
    stemR = _placed_stroke(P_BR, -1, TOP_R, -1, end0=cRs, end1='left', wf=w_stem)
    diag = _placed_stroke(P_BR, +1, P_TL, -1, end0=cRd, end1=cLd)  # outer edge: lower-left at P_BR, upper-right at P_TL
    slope = 180 - ang(sub(P_TL, P_BR))                          # the diagonal's fall, degrees below the horizontal
    cuts = _terminals(('left foot', stemL, F_L), ('right top', stemR, TOP_R))
    return glyph(ord('N'), [stemL, diag, stemR], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=dict(
        terminal_cuts=cuts,
        construction=('Two R3 stems and an R2 "\\" diagonal whose upper edge meets the left stem\'s outer edge in a '
                      'point at y = CAP + OVER_POINT and whose lower edge meets the right stem\'s outer edge in a '
                      'point at y = -OVER_POINT (R6); the left foot (body \'right\') and the right top (body \'left\') '
                      'are R5 cuts with tips at the outer corners; buried ends nest per _point_cuts.'),
        body_width=BODY_MEDIUM, diagonal_deg_from_horizontal=slope, point_deg=90 - slope, points=(P_TL, P_BR),
        vertices=('two points, diagonally opposite: the top-left shoulder at the cap overshoot and the bottom-right '
                  'at the baseline overshoot, each two outer edges meeting at one tip.  Both zoomed at 4x from the '
                  'compiled outline: clean.'),
        deviations=(f'R8 asks both for the medium width 558 and for the A\'s apex angle; with vertical stems the two '
                    f'cannot hold together (a diagonal at the A\'s lean would make the N {2 * xL + _spread(TIP_Y - POINT_Y, HALF_APEX):.0f} '
                    f'wide, one opening the full apex angle from the stem {2 * xL + _spread(TIP_Y - POINT_Y, APEX_DEG):.0f}).  The '
                    f'width wins, being the explicit table; the diagonal runs point to point, falling {slope:.1f} deg below '
                    f'the horizontal, so each point is {90 - slope:.1f} deg wide.')))

# ---- K --------------------------------------------------------------------------
def build_K():
    xL = w_stem(0) / 2
    J = (xL, MID_Y)                                             # arm and leg centre-lines meet on the stem's centre
    st = stem(xL, 0, CAP, bottom='right', top='right')
    E_arm, E_leg = (BODY_MEDIUM, CAP), (BODY_MEDIUM, 0.0)
    # Both free ends present the letter's RIGHT face -- the arm lies 32 deg from the horizontal and
    # the leg 34, nearer a horizontal than a vertical -- so R5's second case applies: the same cut
    # turned 90 deg, CUT_DEG off the VERTICAL, tip at the outer corner (the arm's on the cap line,
    # the leg's on the baseline, both at x = BODY_MEDIUM, the letter's right extreme).  The face is
    # named to _end/_placed_stroke because rules.diagonal keys it to the end index instead.
    arm_ = _diag(J, 0, E_arm, +1, top=('right', 'down'))        # "/": tip top-right on CAP, cut running down into the stroke
    leg = _diag(E_leg, +1, J, 0, bottom=('right', 'up'))        # "\": tip bottom-right on 0, cut running up into the stroke
    a_arm, a_leg = ang(sub(E_arm, J)), -ang(sub(E_leg, J))
    cuts = _terminals(('stem foot', st, (xL - w_stem(0) / 2, 0.0)), ('stem top', st, (xL - w_stem(CAP) / 2, CAP)),
                      ('arm tip', arm_, E_arm), ('leg tip', leg, E_leg))
    wedge_arm, wedge_leg, wedge_stem = cuts['arm tip'], cuts['leg tip'], cuts['stem foot']
    return glyph(ord('K'), [st, arm_, leg], sb=(SB_STRAIGHT, SB_ROUND), notes=dict(
        terminal_cuts=cuts,
        construction=('rules.stem with R5 foot and top (body \'right\': tips at the lower-left and upper-left '
                      'corners), and two R2 diagonals whose centre-lines start flat on the stem\'s centre at MID_Y '
                      '(buried) and end in R5 cuts on the letter\'s right face: the arm ("/") tips at the '
                      'upper-right corner on the cap line (face \'right\', body \'down\') and the leg ("\\") at the '
                      'lower-right corner on the baseline (face \'right\', body \'up\'), each cut CUT_DEG off the '
                      'vertical and running back into the stroke.  Each tip is placed exactly on its corner by '
                      '_centres, and each cut removes the corner that would otherwise pass the metric line.'),
        body_width=BODY_MEDIUM, junction=J, arm_deg=a_arm, leg_deg=a_leg,
        junction_height=('MID_Y = CAP/2 + HORIZ_MID/4, the optical middle set_straight puts the E arm and H bar on, '
                         'so the lower counter is the larger one and K\'s waist agrees with E and H in a word.'),
        terminals=(f'R5 keys a cut to the FACE the end presents, not to the stroke\'s weight class: a top or bottom '
                   f'face is cut CUT_DEG off the horizontal, "arms take the same cut turned 90 deg", tip at the '
                   f'outer corner.  Both of these ends present the letter\'s right face -- the arm lies {a_arm:.1f} '
                   f'deg from the horizontal and the leg {a_leg:.1f}, nearer a horizontal than a vertical -- so both '
                   f'take the turned cut, {CUT_DEG} deg off the vertical, tips at the upper-right corner on the cap '
                   f'line and the lower-right corner on the baseline.  The terminals are then {wedge_arm["wedge_deg"]:.1f} and '
                   f'{wedge_leg["wedge_deg"]:.1f} deg wedges {wedge_arm["cut_len"]:.0f} and {wedge_leg["cut_len"]:.0f} units long (see '
                   f'terminal_length below for how those lengths sit in the group).  Reading these as '
                   f'diagonal ends instead (CUT_DEG off the horizontal, which is what R2\'s weight classification '
                   f'would suggest) puts the cut nearly parallel to the stroke and yields 13.0 and 14.7 deg needles '
                   f'125 and 142 units long, which fade out below about 48 px; that was the previous version and it '
                   f'was the wrong branch of R5.'),
        terminal_length=(f'R5 fixes a cut\'s ANGLE ({CUT_DEG} deg off the face\'s axis) and says nothing about its '
                         f'LENGTH, and the length follows from the stroke: a cut is the stroke\'s width over the sine '
                         f'of the wedge it makes with the stroke\'s own edge, and that wedge is the stroke\'s angle to '
                         f'the face it presents less {CUT_DEG} deg.  K\'s arm and leg lie {a_arm:.1f} and {a_leg:.1f} '
                         f'deg from the horizontal but present the letter\'s vertical right face, so the cut crosses '
                         f'them at only {wedge_arm["wedge_deg"]:.1f} and {wedge_leg["wedge_deg"]:.1f} deg and runs '
                         f'{wedge_arm["cut_len"]:.0f} and {wedge_leg["cut_len"]:.0f} units, against {wedge_stem["cut_len"]:.0f} on this '
                         f'same glyph\'s vertical stem foot (w_stem(0)/cos({CUT_DEG}) = '
                         f'{w_stem(0) / math.cos(math.radians(CUT_DEG)):.0f}).  That spread is R5 working as written, '
                         f'not a defect in this glyph -- see terminal_spread for what the same rule does across the '
                         f'group.  Nothing is compensated for here -- a cap on a cut\'s length '
                         f'would be a change to R5 and would touch K, Z, the 7 and the asterisk together, so it is '
                         f'raised with SPEC rather than patched at glyph level.'),
        terminal_spread=(lambda r: (
            f'The group\'s {len(r)} free R5 terminals, measured live by terminal_spread(): cuts from {r[0][0]:.0f} '
            f'units ({r[0][2]}\'s {r[0][3]}, a {r[0][1]:.0f} deg wedge) to {r[-1][0]:.0f} ({r[-1][2]}\'s {r[-1][3]}, '
            f'{r[-1][1]:.0f} deg), a factor of {r[-1][0] / r[0][0]:.1f}.  The longest are not K\'s: length is width '
            f'over the sine of the wedge, so a cut is shortest where a stroke is thin and meets it nearly square '
            f'and longest where a full-width stroke lies far over toward the face it presents.  Measured in stroke '
            f'widths -- 1/sin(wedge), which is the shape of the terminal rather than its size -- they run '
            f'{1 / math.sin(math.radians(max(w for _, w, _, _ in r))):.2f} to '
            f'{1 / math.sin(math.radians(min(w for _, w, _, _ in r))):.2f}, and they fall in three bands: every '
            f'stem end and both of Z\'s arm tips are near-square cuts just over one width; V\'s and W\'s tops sit a '
            f'third longer; and the ends whose stroke lies far from the normal of the face it presents (X, Y, and '
            f'K\'s arm and leg) run past one and a half.  Z\'s arm tips are long in units only because a horizontal '
            f'is thick; in shape they are the bluntest ends in the group, not spikes.'))(_survey('K', cuts)),
        deviations=(f'R8: the A\'s apex angle cannot hold at the medium width with a vertical stem (a 42.6 deg '
                    f'fork would be {xL + (CAP - MID_Y) / math.tan(math.radians(HALF_APEX)):.0f} '
                    f'wide from arm tip to stem); the width wins, being the explicit table, and the arm and leg '
                    f'take the angles the 558 body and the MID_Y junction dictate, {a_arm:.1f} and {a_leg:.1f} deg '
                    f'from the horizontal.  Nothing else departs; see terminals for which branch of R5 those two '
                    f'angles put the free ends in.')))

# ---- X --------------------------------------------------------------------------
def build_X():
    xc = BODY_MEDIUM / 2
    def top_x(E0, s0, s1, lo, hi):
        # the top tip's x at which this stroke's centre-line crosses the letter's axis at MID_Y
        for _ in range(60):
            t = (lo + hi) / 2
            c0, c1 = _centres(E0, s0, (t, CAP), s1)
            x_mid = c0[0] + (c1[0] - c0[0]) * (MID_Y - c0[1]) / (c1[1] - c0[1])
            if x_mid < xc: lo = t                                # a higher tip moves the crossing right
            else: hi = t
        return (lo + hi) / 2
    tR = top_x((0.0, 0.0), +1, -1, xc, BODY_MEDIUM)              # "/": foot tip at the left corner, top tip at the right corner
    tL = top_x((BODY_MEDIUM, 0.0), -1, +1, 0.0, xc)              # "\": foot tip at the right corner, top tip at the left corner
    slash = _diag((0.0, 0.0), +1, (tR, CAP), -1, bottom='right', top='left')
    back = _diag((BODY_MEDIUM, 0.0), -1, (tL, CAP), +1, bottom='left', top='right')
    cuts = _terminals(('left foot', slash, (0.0, 0.0)), ('right top', slash, (tR, CAP)),
                      ('right foot', back, (BODY_MEDIUM, 0.0)), ('left top', back, (tL, CAP)))
    return glyph(ord('X'), [slash, back], sb=(SB_ROUND, SB_ROUND), notes=dict(
        terminal_cuts=cuts,
        construction=('Two rules.diagonal strokes, "/" and "\\", each ending in R5 cuts with the tip at the outer '
                      'corner on the baseline and the cap line (feet: body toward the other foot; tops likewise), '
                      'their centre-lines crossing on the letter\'s axis at MID_Y.'),
        body_width=BODY_MEDIUM, foot_tips=(0.0, BODY_MEDIUM), top_tips=(tL, tR), top_spread=tR - tL, crossing=(xc, MID_Y),
        proportion=(f'R8 medium, exactly {BODY_MEDIUM}: the "/" foot tip is placed at x = 0 and the "\\" foot tip at '
                    f'x = {BODY_MEDIUM}, both on the baseline, and they are the letter\'s outer extremes, so the '
                    f'built outline measures {BODY_MEDIUM} outer edge to outer edge and the advance is '
                    f'{BODY_MEDIUM + 2 * SB_ROUND}.  The cap-line spread is the narrower {tR - tL:.0f} because the '
                    f'crossing sits {MID_Y - CAP / 2:.1f} above mid-height, which makes the upper half the shorter; '
                    f'R8 measures the widest line, the feet.'),
        crossing_height=('MID_Y = CAP/2 + HORIZ_MID/4, the face\'s optical middle (E arm, H bar, K junction): a '
                         'crossing at the geometric centre reads low, and this keeps the X\'s waist on the same line '
                         'as its neighbours.  The feet keep the A\'s spread and the top closes to '
                         f'{tR - tL:.0f} in consequence.'),
        deviations='none'))

# ---- Y --------------------------------------------------------------------------
def build_Y():
    xs = BODY_MEDIUM / 2
    J = (xs, MID_Y)                                             # the arms' centre-lines meet on the stem's centre
    E_L, E_R = (0.0, CAP), (BODY_MEDIUM, CAP)
    armL = _diag(J, 0, E_L, +1, top='right')                    # "\": R5 tip at the upper-left corner
    armR = _diag(J, 0, E_R, -1, top='left')                     # "/": R5 tip at the upper-right corner
    y_top = MID_Y + w_stem(MID_Y) / 2                           # buried half a stem width above the junction, below the counter apex
    st = stem(xs, 0, y_top, bottom='right')
    lean = 90 - ang(sub(E_R, J))
    cuts = _terminals(('left arm top', armL, E_L), ('right arm top', armR, E_R),
                      ('stem foot', st, (xs - w_stem(0) / 2, 0.0)))
    return glyph(ord('Y'), [st, armL, armR], sb=(SB_ROUND, SB_ROUND), notes=dict(
        terminal_cuts=cuts,
        construction=('Two rules.diagonal arms whose centre-lines start flat on the stem\'s centre at MID_Y (buried) '
                      'and end in R5 cuts with the tip at the outer corner on the cap line (left arm body \'right\', '
                      'right arm body \'left\'), over a rules.stem whose top ends flat inside the arms and whose foot '
                      'is an R5 cut with the tip at the lower left (body \'right\', the lone-stroke convention '
                      'set_punct and set_straight\'s T use for a centred stem).'),
        body_width=BODY_MEDIUM, junction=J, stem_top=y_top, arm_lean_deg=lean, fork_deg=2 * lean,
        junction_height='MID_Y = CAP/2 + HORIZ_MID/4, the optical middle shared with E H K X.',
        vertices=('the fork is a junction, not an R6 point: both arms end flat on the stem\'s centre-line, well '
                  f'inside the stem (their buried corners lie between the stem\'s edges and {y_top - MID_Y:.1f} '
                  'units below its flat top), so the union\'s two shoulders are each one arm\'s lower edge crossing '
                  'the stem\'s edge.  Zoomed at 4x from the compiled outline: no spur and no notch on either side.'),
        deviations=(f'R8: at the A\'s lean, arms 558 apart meet at y = {CAP - _spread(BODY_MEDIUM / 2, 90 - HALF_APEX):.0f}, '
                    f'leaving no stem; width and a stem both being what make a Y, the arms take the lean the 558 body '
                    f'and the MID_Y junction dictate, {lean:.1f} deg off the vertical (fork {2 * lean:.1f} deg).')))

# ---- Z --------------------------------------------------------------------------
def build_Z():
    L = BODY_MEDIUM
    top = arm(0.0, L, 'top', left='cut', right='flat')          # outer edge level on CAP, R5 tip at the top-left corner
    bot = arm(0.0, L, 'bottom', left='flat', right='cut')       # outer edge level on 0, R5 tip at the bottom-right corner
    # The arms' inner edges, laid exactly as rules.arm lays them: from (x0, y_out + sgn*w(L,0)) to
    # (x1, y_out + sgn*w(L,1)).  R4 puts the whole taper on that edge, so neither is level -- both
    # slope atan(HORIZ_TAPER) -- and the buried cuts must bisect the sloping edge, not a level one.
    bot_inner = ((0.0, w_horizontal(L, 0)), (L, w_horizontal(L, 1)))
    top_inner = ((0.0, CAP - w_horizontal(L, 0)), (L, CAP - w_horizontal(L, 1)))
    E0, E1 = bot_inner[0], top_inner[1]                         # the two corners the diagonal's outer edges leave from
    c0 = _bisect(270.0, ang(sub(bot_inner[1], bot_inner[0])))   # bottom arm's left end face (down) and its inner edge (rightward)
    c1 = _bisect(90.0, ang(sub(top_inner[0], top_inner[1])))    # top arm's right end face (up) and its inner edge (leftward)
    diag = _placed_stroke(E0, +1, E1, -1, end0=c0, end1=c1)
    slope = ang(sub(E1, E0))
    cuts = _terminals(('top arm, left tip', top, (0.0, CAP)), ('bottom arm, right tip', bot, (L, 0.0)))
    return glyph(ord('Z'), [top, diag, bot], sb=(SB_ROUND, SB_ROUND), notes=dict(
        terminal_cuts=cuts,
        construction=('Two rules.arm horizontals with their outer edges level on the cap line and baseline (R4), '
                      f'{w_horizontal(L, 0):.1f} thick at the left end and {w_horizontal(L, 1):.1f} at the right, the '
                      'whole 1.8%-of-length taper on the inner edge; the top arm\'s left end and the bottom arm\'s '
                      'right end are R5 cuts with the tip at the outer corner (top-left on the cap line, '
                      'bottom-right on the baseline), the other two ends square, since each is the letter\'s own '
                      'vertical edge where the diagonal arrives.  Between them an R2 "/" whose upper edge leaves the '
                      'bottom arm\'s top-left corner and whose lower edge arrives at the top arm\'s bottom-right '
                      'corner, its buried ends cut along the bisector of the arm\'s end face and its inner edge so '
                      'each lies wholly inside its arm.'),
        buried_ends=(f'Both bisectors are taken against the arm\'s inner edge as rules.arm actually lays it, not '
                     f'against a level line: R4 puts the whole taper there, so the inner edge slopes '
                     f'{math.degrees(math.atan(HORIZ_TAPER)):.2f} deg and the cuts come out at {c0:.2f} and '
                     f'{c1:.2f} deg rather than the 315 and 135 a level edge would give.  Every angle in the glyph '
                     f'is therefore derived from lib/rules.py; none is typed in.'),
        arms=(f'rules.arm both, so the top edge is exactly on {CAP} and the bottom edge exactly on 0 across the full '
              f'{L}, like the H\'s tops and the I\'s foot, and the R4 taper is taken on the inner edge alone.'),
        body_width=L, diagonal_deg_from_horizontal=slope, arm_widths_left_right=(w_horizontal(L, 0), w_horizontal(L, 1)),
        deviations=('none: the diagonal\'s slope follows from the body and the arm weights, not from the A\'s angle, '
                    'which R8 reserves for pointed constructions.')))

GLYPHS = {'V': build_V, 'W': build_W, 'M': build_M, 'N': build_N, 'K': build_K, 'X': build_X, 'Y': build_Y, 'Z': build_Z}
