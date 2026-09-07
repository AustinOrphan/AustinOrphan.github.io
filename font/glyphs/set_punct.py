"""
Punctuation and symbols for Orphan Display, extrapolated from the A and O under
SPEC section 5.  Every weight, taper, cut angle and displacement comes from
lib/rules.py and lib/metrics.py; the proportions come from the two exemplars
(the O's diameter, the A's foot spread, leg angle and apex angle), read off
glyphs/core.py at import.  Strokes are rules.stem / diagonal / horizontal /
arm and the R1 rounds; nothing about a cut or a width is decided here.

Decisions that the rules leave open, taken once here and used throughout:

  THE DOT.  A filled circle of diameter ROUND_THICK (53.0): the O's stroke at
  its heaviest point, which is RING_W + |RING_OFF|, 1.6 x RING_W, 1.34 x the
  baseline stem and 1.12 x the horizontal.  A dot is a round with no counter,
  and the one place the face is at full weight.  It overshoots the baseline by
  OVER_ROUND like every round.  The same dot serves period, comma, colon,
  semicolon, exclam and question.

  LONE STROKES.  R5 puts the tip of a cut at the corner farther from the
  letter's centre.  A stroke that IS the letter's centre (the exclam's stem,
  the quotesingle, the hyphen, the slash) has no farther corner, so its two
  ends are cut as one nib held at CUT_DEG would cut them: the tip at the
  lower-left end and at the upper-right end, the two cuts parallel.  A stem
  gets bottom='right', top='left'; a horizontal gets left='up', right='down'.
  This points every lone stroke along the face's weight axis (R7).  Where a
  glyph has a body off the cut face (quotedbl, brackets, equal, numbersign,
  the question's and ampersand's junctions) R5 is applied literally.

  ROUND ARCS keep the O's absolute stroke and page-fixed displacement (R1)
  everywhere, including where it costs.  A right parenthesis is the side of a
  round the O is thin on, so R1 makes it about a third of its partner's weight
  and gives the pair two different advances.  A mirrored pair -- the right
  glyph built as the left one reflected about a vertical axis -- evens that out
  and was built, but it reverses R1's page-fixed displacement and R4's taper
  with it, which is an exemption for a whole class of glyphs and so a
  SPEC-level decision, not one a glyph module can take.  R1 therefore stands
  here, and the measured price is written out in _PAIR_NOTE and repeated in
  all four glyphs' notes for whoever weighs the clause.

  OVERSHOOTS.  A round body overshoots (R1: -10 / 710), a point overshoots
  (R6: -16 / 716), and an R5 cut is neither -- it is a flat oblique face, not
  a vertex, so it sits exactly on its metric line.  So the dots, the
  question's bowl, the at's ring, the percent's rings and the ampersand's loop
  and bowl reach -10 and 710, while the slash's two cut tips and the percent's
  diagonal sit on 0 and 700, where set_diagonal's X, Y and Z put the same
  construction's.

  CENTRED BARS sit on BAR_Y, the face's mid line (CAP/2 + HORIZ_MID/4,
  cross-checked against set_straight.MID_Y at import), not on half the cap:
  hyphen, en dash, em dash, plus and equals therefore line up with the H's
  bar, the E's middle arm and the K's junction.  MID (half the cap) is kept
  for centring a round BODY, where it is the middle of the shape's own
  extremes: the at's ring and the parens' span.

  A RULE THAT HAS TO JOIN.  The underscore alone has flat ends and no side
  bearings, so consecutive underscores meet; R9 and R5 are read against the
  glyph's job in its notes.  Every other free end in the module is an R5 cut
  and every other glyph carries R9's bearings.

  STEMS ENDING IN A ROUND (the question's stem hanging from its bowl).  A flat
  stem end inside an R1 band cannot be hidden: the band's inner circle is
  displaced toward the upper right, so its lowest point is off the stem's axis
  and a flat end shows as a 2-3 unit step on one side.  Such a stem end is a
  chord instead: its two corners are put on the counter circle it meets, so
  the end is buried in the band.  _stem_on_circle() does this.

  ARMS MEETING A STEM AT A CORNER (the brackets, the at's tail) follow
  set_straight: the stem alone supplies the outer edge, its end cut with the
  tip at the corner; the arm is rules.arm(), whose outer edge is level and
  starts at that corner and whose buried end is an R5 cut running from the
  corner into the stem's interior, so the union never resolves a coincident
  edge.  rules.arm() is written against the cap line and the baseline; where
  an arm's outer edge is level somewhere else (the brackets on 800 / -100,
  the at's tail on its bowl's baseline) _arm_at() builds it there and
  translates it, which changes nothing about it.

  ARCS BURIED IN A STROKE.  An R1 arc's radial end has to disappear inside the
  stroke it runs into (the question's bowl into its stem, the at's bowl into
  its stem, both ends of the ampersand's bowl into its leg).  In every case
  the angle is SOLVED, not chosen: _band_end() gives the end's two corners and
  the glyph scans for the middle of the window of angles at which both corners
  are inside the stroke.  The ampersand also runs the test the other way --
  a STRAIGHT stroke's R5 cut buried inside an R1 BAND -- and the band's own
  geometry decides where that is possible; see the ampersand's own comment.
  Nothing here is placed by eye.

Built locally from pen primitives because lib/rules.py has no such
constructor (lib/ is not edited here):
  _side_diagonal(): an R2 diagonal whose ends lie on the glyph's LEFT and
  RIGHT faces (the asterisk's 30-degree arms), so R5's cut is 20.6 deg off
  the vertical.  rules.diagonal() only knows top/bottom faces.  Same
  stroke(), same R2 widths, cut_for() for the angle and side.
  _diag_span(): an R2 diagonal whose INK spans two given heights.  R2's
  constructor takes centre-line ends and R5 puts the tip off the centre-line,
  so the slash's and percent's tips are landed exactly on 0 and CAP by solving
  the centre-line ends for them (six fixpoint steps).
  _arm_at(), _a_form(): above and at build_at.
  _inside(), _dist_to_poly(), _cut_corners(), _cut_samples(): the ampersand's
  burial tests -- is this radial end inside that leg, is this leg's whole R5
  cut inside that band, does this leg keep clear of that counter.

There is no cut, taper or side-bearing workaround anywhere in this module.
pen.stroke places a cut correctly at both ends, so every terminal here comes
straight from rules.stem / diagonal / horizontal / arm with a bottom=/top=/
left=/right= body direction, and every weight and angle from lib/rules.py.
The one place a rule is read against itself -- the underscore's flat,
bearingless ends, because a rule that cannot meet the next one is not a rule --
is argued out in that glyph's own `deviations` note, not fixed silently.
Everything else in the module follows R1-R9 literally, and where that costs
something (the right parenthesis's weight, the thin tail an R1 arc offers an
ampersand) the cost is measured and recorded rather than designed away.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib')); sys.path.insert(0, FONT)
from pen import *
from metrics import *
from rules import (RING_W, RING_OFF, ROUND_THICK, ROUND_THIN, round_ring, round_arc,
                   w_slash, w_backslash, w_stem, w_horizontal, HORIZ_MID, HORIZ_TAPER, CUT_DEG,
                   glyph, stem, diagonal, horizontal, arm)
from glyphs import core

# ---- proportions read from the exemplars ---------------------------------------
_A = core.build_A()['notes']
_spread = _A['vertices']['tipR'][0] - _A['vertices']['tipL'][0]  # 558.05: the A's foot spread, for the record
MEDIUM  = 558.0                                                    # R8 medium: the A's foot spread as the spec states it
WIDE    = CAP + 2*OVER_ROUND                                       # 720: the O's diameter (R8 wide)
NARROW  = 420.0                                                    # R8 narrow: three quarters of medium (418.5), stated as 420
LEG_DEG = _A['leg_angles'][0]                                      # 68.7: the "/" leg's angle from the horizontal
BACK_DEG = _A['leg_angles'][1]                                     # 111.3: the "\" leg's angle from the horizontal
APEX_DEG = _A['apex_angle']                                        # 42.6: the A's apex angle
MID     = CAP / 2                                                  # 350: the geometric half-cap.  The centre of a round BODY (the at's ring,
                                                                   # the parens' span), where it is the middle of the shape's own extremes.
BAR_Y   = CAP / 2 + HORIZ_MID / 4                                  # 361.875: the face's mid line, the height every off-metric horizontal in
                                                                   # the face sits on -- set_straight's E middle arm, F arm and H bar,
                                                                   # set_bowl's P and R bowl bottoms, set_diagonal's K junction, X crossing
                                                                   # and Y fork.  A quarter of the arm's own weight above half the cap, so
                                                                   # the lower counter is the larger (set_straight.MID_Y).  Every centred
                                                                   # BAR here -- hyphen, en dash, em dash, plus, equals -- is on it, so a
                                                                   # hyphen between capitals lines up with the H's bar instead of sitting
                                                                   # 11.9 below it.

def _check_bar_y():
    """BAR_Y must be the same line set_straight puts the E's middle arm and the H's bar on;
    set_bowl cross-checks its MID_LINE the same way."""
    import importlib
    try: ss = importlib.import_module('glyphs.set_straight')
    except ImportError as e:
        if e.name != 'glyphs.set_straight': raise
        return 'set_straight not present; cross-check skipped'
    if abs(ss.MID_Y - BAR_Y) > 1e-9:
        raise RuntimeError(f'set_punct.BAR_Y ({BAR_Y}) != set_straight.MID_Y ({ss.MID_Y})')
    return 'equals set_straight.MID_Y (checked at import)'
_BAR_CHECK = _check_bar_y()

# ---- the dot ----------------------------------------------------------------------
DOT_D = ROUND_THICK                  # 53.0
DOT_R = DOT_D / 2
DOT_CY = DOT_R - OVER_ROUND          # a dot on the baseline: bottom at -OVER_ROUND like every round
def _dot(cx, cy):
    return circle_contour((cx, cy), DOT_R, ccw=True)

# ---- local helpers ------------------------------------------------------------------
def _side_diagonal(p0, p1, faces, bodies):
    """An R2 diagonal from its lower point p0 to its upper point p1 whose ends are on the glyph's
    left/right faces: faces = (face at p0, face at p1) in ('left', 'right'), bodies = the body
    direction along each face ('up'/'down').  See the module docstring."""
    if p0[1] > p1[1]: p0, p1 = p1, p0
    wf = w_slash if p1[0] >= p0[0] else w_backslash
    e0 = cut_for(p0, p1, faces[0], bodies[0], CUT_DEG)
    e1 = cut_for(p1, p0, faces[1], bodies[1], CUT_DEG)
    return stroke(p0, p1, wf(p0[1]), wf(p1[1]), e0, e1)

def _diag_span(x_lo, y_lo, y_hi, ang_deg, bottom, top):
    """A cut R2 diagonal whose ink spans exactly y_lo..y_hi (tips included), at ang_deg from
    the horizontal, its centreline through (x_lo, y_lo).  The tip corners of a cut diagonal
    sit off the centreline, so the endpoints are solved for by a short fixpoint."""
    v = from_ang(ang_deg); k = v[0] / v[1]
    y0, y1 = y_lo, y_hi
    for _ in range(6):
        p0 = (x_lo + (y0 - y_lo) * k, y0); p1 = (x_lo + (y1 - y_lo) * k, y1)
        d = diagonal(p0, p1, bottom=bottom, top=top)
        _, ymin, _, ymax = d.bbox()
        y0 += y_lo - ymin; y1 += y_hi - ymax
    return d

def _band_end(c, r_out, a_deg):
    """Outer and inner corners of an R1 arc's radial end at a_deg (as arc_band cuts it)."""
    outer = add(c, mul(from_ang(a_deg), r_out))
    inner = line_circle(line_ang(c, a_deg), add(c, RING_OFF), r_out - RING_W, pick='max')
    return outer, inner

def _arm_at(x0, x1, outer, y, left='cut', right='cut'):
    """rules.arm() on a level line other than the cap line or the baseline: arm() is written
    against CAP / 0, so it is built there and translated by the difference, which changes
    nothing about its widths, its cuts or the fact that its outer edge is exactly level (SPEC
    R4).  Used by the brackets (outer edges on 800 / -100) and by the at's tail."""
    dy = y - (CAP if outer == 'top' else 0.0)
    return arm(x0, x1, outer, left=left, right=right).map(lambda p: (p[0], p[1] + dy))

def _in_band(p, c, r_out, margin=0.0):
    """Is p inside an R1 band of outer radius r_out about c, by at least `margin`?"""
    return norm(sub(p, c)) <= r_out - margin and norm(sub(p, add(c, RING_OFF))) >= r_out - RING_W + margin

def _stem_on_circle(x, y_free, free, c, r, end):
    """An R3 stem centred on x with one free end (an R5 cut, body direction `free`) at y_free,
    and its other end (`end` = 'top' or 'bottom') a chord of the circle (c, r): both corners
    on the circle's lower half.  See the module docstring.  Returns (contour, [left, right])
    with the two on-circle corners."""
    def y_on(xx): return c[1] - math.sqrt(r*r - (xx - c[0])**2)
    y_end = y_on(x)
    if end == 'top': s = stem(x, y_free, y_end, bottom=free, top=None)
    else:            s = stem(x, y_end, y_free, bottom=None, top=free)
    pts = s.flatten()
    order = sorted(range(len(pts)), key=lambda i: pts[i][1], reverse=(end == 'top'))
    corners = []
    for i in order[:2]:
        pts[i] = (pts[i][0], y_on(pts[i][0])); corners.append(pts[i])
    return from_poly(ccw(pts)), sorted(corners)

def _notes(construction, deviations='none', **kw):
    return dict(construction=construction, deviations=deviations, **kw)

# ==================================================================================
# dots
# ==================================================================================
def build_period():
    return glyph(46, [_dot(0, DOT_CY)], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "The dot: a circle of diameter ROUND_THICK (53.0), the O's heaviest stroke, bottom at -OVER_ROUND.",
        dot_diameter=DOT_D, centre_y=DOT_CY))

COMMA_TIP_Y = -2.6 * DOT_D          # the tail's tip, 138 below the baseline
def comma_parts(cx):
    """The comma: the dot, and an R2 '/' tail at the A's leg angle from the dot's centre down to
    the lower left, cut at its tip like the A's left foot (tip at the outer lower-left corner)."""
    c = (cx, DOT_CY)
    v = from_ang(LEG_DEG)                               # up-right along the tail
    # the tip corner of a cut '/' sits off the centreline end; solve the end for the tip height
    y0 = COMMA_TIP_Y
    for _ in range(6):
        p0 = add(c, mul(v, (y0 - c[1]) / v[1]))
        tail = diagonal(p0, c, bottom='right', top=None)
        y0 += COMMA_TIP_Y - tail.bbox()[1]
    return [_dot(cx, DOT_CY), tail]

def build_comma():
    return glyph(44, comma_parts(0), sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "The dot with an R2 '/' tail at the A's leg angle (68.7 deg) running from the dot's centre "
        "down-left to a tip 2.6 dots below the baseline, cut per R5 with the tip at the outer lower-left "
        "corner; the tail's flat upper end is buried in the dot.",
        "R2's height field is read below the baseline (39.5 at 0 growing to 41.9 at the tip), so the tail "
        "is very slightly heavier at its tip than at the dot, which is R7's direction.",
        tail_tip_y=COMMA_TIP_Y, tail_angle_deg=LEG_DEG))

COLON_TOP = 0.75 * CAP              # top of the upper dot: three quarters of the cap height
def upper_dot(cx):
    return _dot(cx, COLON_TOP - DOT_R)

def build_colon():
    return glyph(58, [_dot(0, DOT_CY), upper_dot(0)], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "Two dots: the period, and the same dot with its top at 3/4 cap (525), the height a caps-only "
        "colon conventionally reaches; nothing in the mark fixes this, so it is a design choice.",
        upper_dot_top=COLON_TOP))

def build_semicolon():
    return glyph(59, comma_parts(0) + [upper_dot(0)], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "The comma with the colon's upper dot above it."))

# ==================================================================================
# exclam, question
# ==================================================================================
DOT_GAP = DOT_D                     # clear space between a dot and the stroke above it: one dot
STEM_FOOT_Y = DOT_CY + DOT_R + DOT_GAP     # 96: where the exclam's and question's stems end

def build_exclam():
    s = stem(0, STEM_FOOT_Y, CAP, bottom='right', top='left')
    return glyph(33, [s, _dot(0, DOT_CY)], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "An R3 stem from cap down to one dot's clearance above the dot, tips cut per the lone-stroke "
        "convention (lower-left, upper-right), over the dot.",
        "The stem is heavier at its foot than at the cap (R3/R7), the reverse of the conventional "
        "exclamation mark; the rule wins.",
        stem_foot_y=STEM_FOOT_Y))

Q_R = NARROW / 2                    # 210: the bowl is a narrow-width round
Q_START = 180.0                     # the bowl's free end, a radial cut on the left
def build_question():
    cx = 0.0; cy = CAP + OVER_ROUND - Q_R                # bowl top at 710
    c = (cx, cy); ci = add(c, RING_OFF); r_in = Q_R - RING_W
    # the stem hangs from the bowl's bottom: R5 foot (body to the right, tip at the lower-left corner),
    # top a chord of the counter circle
    s, (tl, tr) = _stem_on_circle(cx, STEM_FOOT_Y, 'right', ci, r_in, 'top')
    # the arc runs past the bottom until its OUTER end corner lands on the stem's left edge, so the
    # band covers the stem's full width and the whole radial end is buried in the stem
    a_end = -math.degrees(math.acos(max(-1.0, min(1.0, (tl[0] - cx) / Q_R))))
    Q_PAST = -90 - a_end
    bowl = round_arc(c, Q_R, a_end, Q_START)
    o, i = _band_end(c, Q_R, a_end)
    return glyph(63, [bowl, s, _dot(cx, DOT_CY)], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "An R1 arc of a narrow-width round (outer diameter 420, top at 710) from the left (180 deg, radial cut) "
        "over the top and down the right to the bottom, an R3 stem hanging from its bottom to one dot's "
        "clearance above the dot, and the dot (the period's, same diameter and same -10).  The arc is not "
        "stopped at the bottom but carried %.2f deg past it, to the angle whose OUTER corner (x %.1f) lands "
        "on the stem's left edge at the join (x %.1f): from there the band covers the stem's full width, and "
        "the arc's whole radial end -- outer corner and inner corner (x %.1f) -- is inside the stem.  The "
        "stem's top is a chord of the counter circle (corners at y %.1f and %.1f), the one stem end an R1 "
        "band can hide completely (see the module docstring)."
        % (Q_PAST, o[0], tl[0], i[0], tl[1], tr[1]),
        "none; the chord across the counter circle stands at most %.2f above it (its sagitta over a %.1f-unit "
        "chord at radius %.1f), a tenth of a unit at the proof size and the only mark the join leaves."
        % (r_in - math.sqrt(r_in**2 - (norm(sub(tr, tl))/2)**2), norm(sub(tr, tl)), r_in),
        bowl_r=Q_R, bowl_centre=c, arc=(a_end, Q_START), stem_top_corners=(tl, tr)))

# ==================================================================================
# quotes
# ==================================================================================
QUOTE_LEN = NARROW / 2              # 210: a quote is as long as the hyphen
QUOTE_GAP = DOT_D                   # clear space between the two strokes of quotedbl, at their feet
def build_quotesingle():
    s = stem(0, CAP - QUOTE_LEN, CAP, bottom='right', top='left')
    return glyph(39, [s], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=_notes(
        "A straight R3 stem hanging 210 (the hyphen's length) from the cap line, both ends cut per the "
        "lone-stroke convention.  Straight, because U+0027 is the neutral quote.",
        length=QUOTE_LEN))

def build_quotedbl():
    y0 = CAP - QUOTE_LEN
    dx = w_stem(y0) + QUOTE_GAP
    left  = stem(0,  y0, CAP, bottom='right', top='right')
    right = stem(dx, y0, CAP, bottom='left',  top='left')
    def corner(k, y, pick): return pick(p[0] for p in k.flatten() if abs(p[1] - y) < 0.5)
    tips = dict(left_cap=corner(left, CAP, min), left_foot=corner(left, y0, min),
                right_cap=corner(right, CAP, max), right_foot=corner(right, y0, max))
    return glyph(34, [left, right], sb=(SB_STRAIGHT, SB_STRAIGHT), notes=_notes(
        "Two R3 stems of the quotesingle's length, one dot's clear space apart at their feet.  R5 literally, "
        "and taken from the constructors: the glyph's centre is between the stems, so the left stem is built "
        "with the body to its right at BOTH ends and the right stem with the body to its left at both, which "
        "puts all four tips at the outer corners -- the left stem's on the left, the right stem's on the "
        "right, at the cap line and at the feet, the four cuts receding inward.  No cut is constructed here; "
        "rules.stem's bottom=/top= body direction is the whole of it.",
        "none; the pair flares outward rather than following the lone-stroke nib of the quotesingle, because "
        "the quotedbl has a body off each cut face and R5 then applies literally.",
        spacing=dx, tip_x=tips, foot_y=y0))

# ==================================================================================
# horizontals: hyphen, dashes, underscore, plus, equal
# ==================================================================================
HYPHEN_LEN = NARROW / 2             # 210
def _bar(length, y, left='up', right='down'):
    return horizontal(0, length, y, left=left, right=right)

def build_hyphen():
    return glyph(45, [_bar(HYPHEN_LEN, BAR_Y)], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "An R4 horizontal 210 long (half the narrow width) on the face's mid line (%.3f = CAP/2 + HORIZ_MID/4, "
        "%s), ends cut per the lone-stroke convention (tip lower-left, tip upper-right)." % (BAR_Y, _BAR_CHECK),
        length=HYPHEN_LEN, y=BAR_Y))

def build_endash():
    return glyph(8211, [_bar(NARROW, BAR_Y)], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "The hyphen at the narrow width, 420: twice the hyphen, half the em with its bearings; the face's mid "
        "line like every other bar here.", length=NARROW, y=BAR_Y))

def build_emdash():
    L = UPM - 2*SB_ROUND
    return glyph(8212, [_bar(L, BAR_Y)], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "The hyphen run out to fill the em: %d long, advance exactly %d, R8's ceiling.  Unlike the "
        "underscore it keeps R9's %d bearings and R5's cut ends, so a run of em dashes shows %d units of "
        "white at each join." % (L, UPM, SB_ROUND, 2 * SB_ROUND),
        "None.  The gap in a run is a decision, not an oversight: an em dash is a mark set between words, "
        "with letters either side, and it needs the bearings that keep it off them; its ends are free ends "
        "and R5 cuts them.  The underscore, which drops both, is the face's rule -- the glyph whose whole "
        "job is to join.  A dash used as a rule would be a second glyph, not this one.",
        length=L, y=BAR_Y))

UNDERSCORE_Y = -DESCENT / 2
def build_underscore():
    bar = horizontal(0, NARROW, UNDERSCORE_Y)            # flat ends: they meet the next underscore's
    step = HORIZ_TAPER * NARROW                          # R4's loss over the bar, the step at a join
    notch = w_horizontal(NARROW, 0.5) * math.tan(math.radians(CUT_DEG))   # white a pair of R5 cuts would leave
    return glyph(95, [bar], sb=(0, 0), notes=_notes(
        "An R4 horizontal at the narrow width (%d) centred half the descent below the baseline, with FLAT "
        "ends and NO side bearings, so the bar is the whole advance and consecutive underscores meet.  An "
        "underscore's one job is to rule under text; a rule that cannot join the next one does not do it."
        % NARROW,
        "Two, R9 and R5 both read against that job.  (1) R9's %d beside a round or a point is dropped to 0 "
        "at both ends.  The underscore's extremes are not a stem, a round or a point but the ends of a rule "
        "that has to meet the next one; with the bearings the run was a dashed line, %d units of white every "
        "%d.  (2) R5's oblique cuts are dropped for flat ends.  A run's two cut faces are parallel (R5's "
        "%.1f deg off the vertical, one tip at the low left, the next at the high right), so butting them "
        "leaves a lozenge of white %.1f long and the bar's full thickness high at every join -- a serration "
        "down the rule, worse than the square end a lone underscore now shows.  What is left at a join is "
        "R4's own taper: each bar runs %.1f thick at its left end to %.1f at its right, so the rule steps "
        "back up %.1f (%.1f a side) every %d units.  That is R4 doing what it says, a scallop of a tenth of "
        "the stroke rather than a break in the line, and it is the reason the underscore keeps the narrow "
        "width instead of a longer bar, which would taper further."
        % (SB_ROUND, 2 * SB_ROUND, NARROW + 2 * SB_ROUND, CUT_DEG, notch, w_horizontal(NARROW, 0),
           w_horizontal(NARROW, 1), step, step / 2, NARROW),
        y=UNDERSCORE_Y, length=NARROW, join_step=step))

def build_plus():
    L = NARROW
    return glyph(43, [_bar(L, BAR_Y), stem(L/2, BAR_Y - L/2, BAR_Y + L/2, bottom='right', top='left')],
                 sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "An R4 horizontal and an R3 stem, both 420 long, crossing at their centres on the face's mid line "
        "(%.3f, the height of the H's bar); all four ends are lone-stroke cuts (the crossing is the centre, so "
        "no corner is farther from it)." % BAR_Y, arm=L, y=BAR_Y))

EQUAL_GAP = HORIZ_MID               # the clear gap between the bars is one bar thick
def build_equal():
    d = (HORIZ_MID + EQUAL_GAP) / 2
    return glyph(61, [_bar(NARROW, BAR_Y + d, left='down', right='down'),
                      _bar(NARROW, BAR_Y - d, left='up', right='up')],
                 sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "Two R4 horizontals at the narrow width, one bar's thickness apart about the face's mid line (%.3f), "
        "so the pair straddles the height the H's bar sits on.  Each end is cut per R5 toward the other bar "
        "(tips at the outer corners), so the pair flares outward." % BAR_Y,
        bar_centres=(BAR_Y - d, BAR_Y + d)))

# ==================================================================================
# slash
# ==================================================================================
def build_slash():
    d = _diag_span(0, 0.0, float(CAP), LEG_DEG, bottom='right', top='left')
    x0, y0, x1, y1 = d.bbox()
    return glyph(47, [d], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "One R2 '/' diagonal at the A's leg angle (%.2f deg), %.1f wide at the baseline and %.1f at the cap "
        "line, its ink spanning exactly 0..%d: the foot is cut like the A's left foot (tip at the lower-left "
        "corner, ON the baseline) and the top is that cut turned about the centre (tip at the upper-right "
        "corner, ON the cap line), the lone-stroke convention.  R5 puts a tip off the centre-line, so the "
        "centre-line ends are solved for the tips by _diag_span, not set to the metric values.  Both ends are "
        "plain R5 cuts, not points, so neither takes an overshoot: R6 grants OVER_POINT to a vertex where two "
        "outer edges meet, which this stroke has nowhere.  That puts the slash's tips exactly where "
        "set_diagonal puts the same construction's -- X 0..%d, Z 0..%d, V's cut tops on %d -- so a slash "
        "between capitals lines up with them instead of standing %d proud at each end."
        % (LEG_DEG, w_slash(0), w_slash(CAP), CAP, CAP, CAP, CAP, OVER_POINT),
        angle_deg=LEG_DEG, extent=(x0, y0, x1, y1), tip_low=(x0, y0), tip_high=(x1, y1)))

# ==================================================================================
# parentheses and brackets
# ==================================================================================
PAREN_LO, PAREN_HI = -DESCENT / 2, float(ASCENT)     # -100 .. 800, symmetric about the cap midline
PAREN_HALF = APEX_DEG                                # each paren subtends twice the A's apex angle
_h = (PAREN_HI - PAREN_LO) / 2
PAREN_R = _h / math.sin(math.radians(PAREN_HALF))    # 664.6

# The one place R1's page-fixed displacement is felt as a whole glyph's weight rather than as
# one thin passage.  It is applied literally all the same; the price and the rejected
# alternative are recorded here and repeated in all four glyphs' notes.
_PAIR_NOTE = (
    "R1 LITERALLY, AND WHAT IT COSTS.  R1's counter displacement is fixed to the page, not to the glyph, so "
    "the two halves of a bracketing pair cannot be the same weight.  Measured: the left paren is %.1f at "
    "mid-height, %.1f at the foot and %.1f at the head; the right paren, the same arc seen from the other "
    "side, is %.1f, %.1f and %.1f -- at mid-height a little over a third of its partner -- and the two "
    "advances differ, %d against %d.  The brackets carry the same reading in miniature: R4 tapers left to "
    "right in both, so the left bracket's arms run %.1f at the stem to %.1f at the tip and the right "
    "bracket's %.1f at the tip to %.1f at the stem, a %.1f-unit difference at the stem, the A's own 6%% "
    "left-to-right leg difference.  An earlier draft built each right glyph as its left partner's contours "
    "reflected about a vertical axis: that matches the pair and shares one advance, but it reverses R1's "
    "page-fixed displacement (the counter then runs toward 135 deg) and R4's taper with it, which is exactly "
    "what R1 and R7 forbid.  Exempting a class of glyphs from R1 is a SPEC-level decision and a glyph module "
    "is not where it can be taken, so it is not taken: R1 stands, the numbers above are its price, and if the "
    "face wants bracketing pairs exempted the clause belongs in SPEC section 5, where it can be weighed "
    "against R7 and the O.")

def _paren_arc(side):
    """An R1 arc of a round of radius PAREN_R subtending 2 x the A's apex angle, radial ends: the
    left paren about a centre to its right, the right paren about a centre to its left.  Both are
    round_arc(), so both carry the O's absolute stroke and the O's page-fixed displacement."""
    if side == 'left': return round_arc((PAREN_R, MID), PAREN_R, 180 - PAREN_HALF, 180 + PAREN_HALF)
    return round_arc((-PAREN_R, MID), PAREN_R, -PAREN_HALF, PAREN_HALF)

def _paren_widths():
    """(mid-height, bottom, top) band widths of each paren as R1 builds it."""
    def w(c, a): o, i = _band_end(c, PAREN_R, a); return norm(sub(o, i))
    cl, cr = (PAREN_R, MID), (-PAREN_R, MID)
    return ([w(cl, a) for a in (180, 180 + PAREN_HALF, 180 - PAREN_HALF)],
            [w(cr, a) for a in (0, -PAREN_HALF, PAREN_HALF)])

def _paren_adv(side):
    x0, _, x1, _ = _paren_arc(side).bbox(); return round(x1 - x0 + 2 * SB_ROUND)

def _bracket_arm_widths():
    """(at the stem, at the tip) for the left bracket and for the right one, from R4's taper."""
    L = abs(BRACKET_ARM + w_stem(PAREN_HI) / 2)
    return (w_horizontal(L, 0), w_horizontal(L, 1)), (w_horizontal(L, 1), w_horizontal(L, 0))

def _pair_note():
    """_PAIR_NOTE with this face's measured numbers."""
    L, R = _paren_widths(); bl, br = _bracket_arm_widths()
    return _PAIR_NOTE % (L[0], L[1], L[2], R[0], R[1], R[2], _paren_adv('left'), _paren_adv('right'),
                         bl[0], bl[1], br[1], br[0], bl[0] - br[0])

def _paren_note(side):
    L, R = _paren_widths(); w = L if side == 'left' else R
    return _notes(
        "An R1 arc (the O's absolute stroke and page-fixed displacement) of a round of radius %.1f, "
        "subtending 2 x %.1f deg (the A's apex angle) about a centre to its %s, spanning %d..%d about the "
        "cap midline; radial ends.  %.1f wide at mid-height, %.1f at the bottom end and %.1f at the top: "
        "heavy low, light high (R7).%s"
        % (PAREN_R, PAREN_HALF, 'right' if side == 'left' else 'left', PAREN_LO, PAREN_HI, w[0], w[1], w[2],
           "" if side == 'left' else "  Light throughout, because the whole glyph stands on the side of a "
                                     "round the O is thin on: R1's displacement is fixed to the page, so the "
                                     "arc that opens to the left carries the O's 45 deg thin passage down its "
                                     "whole length."),
        _pair_note(),
        r=PAREN_R, span=(PAREN_LO, PAREN_HI), widths_mid_bottom_top=w, mirrored=False)

def build_parenleft():
    return glyph(40, [_paren_arc('left')], sb=(SB_ROUND, SB_ROUND), notes=_paren_note('left'))

def build_parenright():
    return glyph(41, [_paren_arc('right')], sb=(SB_ROUND, SB_ROUND), notes=_paren_note('right'))

BRACKET_ARM = 150                   # arm length from the stem's centre
def _shifted_arm(x0, x1, outer):
    """rules.arm() on the parens' span (see _arm_at and the module docstring)."""
    return _arm_at(x0, x1, outer, PAREN_HI if outer == 'top' else PAREN_LO)

def _bracket(cp, side):
    x, L = 0.0, BRACKET_ARM
    y_lo, y_hi = PAREN_LO, PAREN_HI
    if side == 'left':
        st = stem(x, y_lo, y_hi, bottom='right', top='right')        # tips at the outer (left) corners
        x_top, x_bot = x - w_stem(y_hi) / 2, x - w_stem(y_lo) / 2    # the stem's tips: the arms' corners
        top_span, bot_span = (x_top, x + L), (x_bot, x + L)
        sb = (SB_STRAIGHT, SB_ROUND)
    else:
        st = stem(x, y_lo, y_hi, bottom='left', top='left')          # tips at the outer (right) corners
        x_top, x_bot = x + w_stem(y_hi) / 2, x + w_stem(y_lo) / 2
        top_span, bot_span = (x - L, x_top), (x - L, x_bot)
        sb = (SB_ROUND, SB_STRAIGHT)
    parts = [st, _shifted_arm(*top_span, 'top'), _shifted_arm(*bot_span, 'bottom')]
    L_top, L_bot = top_span[1] - top_span[0], bot_span[1] - bot_span[0]   # arm lengths, the same either way round
    w_left, w_right = w_horizontal(L_top, 0), w_horizontal(L_top, 1)
    at_stem, at_tip = (w_left, w_right) if side == 'left' else (w_right, w_left)
    return glyph(cp, parts, sb=sb, notes=_notes(
        "An R3 stem over the parens' span (%d..%d), its ends cut per R5 with the tips at the outer (%s) "
        "corners, and two R4 arms (rules.arm) running %d from the stem's centre to the %s.  Each arm's outer "
        "edge is level on %d / %d from the stem's tip; its free end is an R5 cut with the tip at the outer "
        "corner and its buried end an R5 cut running from the shared corner into the stem (set_straight's "
        "corner).  Arms %.1f thick at the stem and %.1f at the tip: R4 tapers left to right whichever way the "
        "bracket faces, so this half's arms are the %s where they meet the stem."
        % (PAREN_LO, PAREN_HI, side, L, 'right' if side == 'left' else 'left', PAREN_HI, PAREN_LO,
           at_stem, at_tip, 'heavier' if side == 'left' else 'lighter'),
        "Two.  (1) The arms are not on a metric line: rules.arm() builds them on CAP / 0 and they are "
        "translated by %d / %d to the parens' span.  Widths (%.1f to %.1f over %.0f), cuts and the level "
        "outer edge are exactly arm()'s; R4's symmetric taper for off-metric horizontals would tilt the "
        "bracket's flat top %.1f over the arm and break the corner it shares with the stem's tip.  (2) %s"
        % (PAREN_HI - CAP, PAREN_LO, w_horizontal(L_top, 0), w_horizontal(L_top, 1), L_top,
           HORIZ_TAPER / 2 * L_top, _pair_note()),
        arm=L, arm_lengths=(L_top, L_bot), arm_widths=dict(at_stem=at_stem, at_tip=at_tip), mirrored=False))

def build_bracketleft():  return _bracket(91, 'left')
def build_bracketright(): return _bracket(93, 'right')

# ==================================================================================
# asterisk, numbersign
# ==================================================================================
AST_R = 180                         # arm length from the centre
def build_asterisk():
    cy = CAP - AST_R                                    # the top arm's tip on the cap line
    c = (0.0, cy)
    a = math.radians(30)
    d = (AST_R * math.cos(a), AST_R * math.sin(a))
    st = stem(0, cy - AST_R, cy + AST_R, bottom='right', top='left')
    arm1 = _side_diagonal(sub(c, d), add(c, d), faces=('left', 'right'), bodies=('up', 'down'))                    # '/'
    arm2 = _side_diagonal((c[0] + d[0], cy - d[1]), (c[0] - d[0], cy + d[1]), faces=('right', 'left'), bodies=('up', 'down'))   # '\'
    return glyph(42, [st, arm1, arm2], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "Six arms: an R3 stem and two R2 diagonals at 30 deg to the horizontal crossing at a centre 180 "
        "below the cap line, so the top arm's tip sits on the cap.  The stem's tips follow the lone-stroke "
        "convention; the shallow arms end on the left/right faces (cut CUT_DEG off the vertical, R5 for arms, "
        "built by _side_diagonal because rules.diagonal only knows top/bottom faces) and, a 20.6 deg cut on a "
        "30 deg stroke only runs into the stroke from one corner, which fixes the tip at the corner nearer the "
        "vertical axis on each arm.",
        "R2 is written for steep strokes; here its height field is applied to 30 deg arms.",
        r=AST_R, centre=c))

NS_W = MEDIUM                       # the bars' length
NS_STEM_AT = (0.3, 0.7)             # stems at 30% and 70% of the bar
def build_numbersign():
    xs = [NS_W * t for t in NS_STEM_AT]
    ys = [CAP / 3, 2 * CAP / 3]
    parts = [stem(xs[0], 0, CAP, bottom='right', top='right'),
             stem(xs[1], 0, CAP, bottom='left', top='left'),
             _bar(NS_W, ys[0], left='up', right='up'),
             _bar(NS_W, ys[1], left='down', right='down')]
    return glyph(35, parts, sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "Two R3 stems over the cap height at 30%% and 70%% of two R4 bars %d long (the medium width) at "
        "thirds of the cap height.  All eight ends are cut per R5 away from the glyph's centre, tips at the "
        "outer corners." % NS_W, width=NS_W, stems=xs, bars=ys))

# ==================================================================================
# percent, at
# ==================================================================================
PCT_R = 150                         # the rings' outer radius
PCT_GAP = 30                        # clear space between the slash and each ring
def build_percent():
    th = math.radians(LEG_DEG); s, co = math.sin(th), math.cos(th)
    c1 = (PCT_R, CAP + OVER_ROUND - PCT_R)              # upper ring, top at 710
    # distance from a ring's centre to the slash's centreline = r + half the slash + the gap
    def clear(y): return PCT_R + w_slash(y) / 2 + PCT_GAP
    # slash centreline through (x_s, 0) at LEG_DEG: signed distance of (px,py) = (px-x_s)*s - py*co
    x_s = c1[0] + (clear(c1[1]) - c1[1] * co) / s
    y2 = PCT_R - OVER_ROUND                             # lower ring, bottom at -10
    x2 = x_s + (clear(y2) + y2 * co) / s
    c2 = (x2, y2)
    slash = _diag_span(x_s, 0.0, float(CAP), LEG_DEG, bottom='right', top='left')
    return glyph(37, round_ring(c1, PCT_R) + round_ring(c2, PCT_R) + [slash], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "Two complete R1 rounds of outer diameter %.0f -- the O's construction at that size, absolute stroke "
        "and absolute page-fixed displacement, so %.1f at the lower left and %.1f at the upper right like the "
        "O itself -- and the slash between them.  Each form takes the overshoot its own shape earns and no "
        "other: the rounds overshoot, the upper ring's top exactly %d and the lower ring's bottom exactly "
        "-%d, while the slash is the slash glyph's own construction (R2 at %.2f deg, lone-stroke R5 cuts) "
        "with its cut tips exactly on 0 and %d, because a cut is not a point and R6's %d belongs to a vertex. "
        " Each ring's centre is set by solving the ring's distance to the slash's centre-line, so both stand "
        "%d clear of it: R1 for the rounds, R2 and R5 for the diagonal, nothing measured by eye."
        % (2*PCT_R, ROUND_THICK, ROUND_THIN, CAP + OVER_ROUND, OVER_ROUND, LEG_DEG, CAP, OVER_POINT,
           PCT_GAP),
        rings=(c1, c2), r=PCT_R, gap=PCT_GAP, slash_extent=slash.bbox(),
        ring_extents=((c1[1] + PCT_R, c1[1] - PCT_R), (c2[1] + PCT_R, c2[1] - PCT_R))))

AT_BOWL_R = 168.0                   # the inner a's bowl: outer radius
AT_TAIL   = 135.0                   # the a's tail, from the stem's centre to the tip
AT_MARGIN = 1.5                     # how far inside the stem an arc end has to sit to count as buried

def _a_form(cb, rb, tail_len):
    """A single-storey 'a', built from an R1 bowl and an R3 stem, for the inside of the at.

    The bowl is an R1 arc open on the right; the stem's right edge is flush with the bowl's
    rightmost point.  Three joins, each solved rather than eyeballed:
      * the bowl's two radial ends are carried round until BOTH corners of each lie inside the
        stem (scanned, AT_MARGIN clear of its left edge), so neither end shows;
      * the stem's top is an R5 cut whose tip is at the upper LEFT, placed at the height where
        the stem's left edge meets the bowl's outer circle -- the tip therefore sits exactly ON
        that circle and the shoulder is one shared point, no notch and no beak.  R5's own
        'corner farther from the centre' does not apply: this end is a junction, not a free
        end, and takes the shared-corner cut set_straight uses where an arm meets a stem;
      * the foot is set_straight's L: the stem's R5 foot tip and the tail's outer edge share
        the bottom-left corner, the tail is rules.arm (via _arm_at) with its bottom edge level
        on the bowl's own baseline, and its buried end is an R5 cut running from that corner
        into the stem.
    Returns (contours, info)."""
    xr = cb[0] + rb                                     # the bowl's rightmost point = the stem's right edge
    xs = xr - w_stem(cb[1]) / 2                         # the stem's centre
    def left_edge(y): return xs - w_stem(y) / 2
    def buried(a): return all(left_edge(p[1]) + AT_MARGIN <= p[0] <= xr for p in _band_end(cb, rb, a))
    a_hi = max(a for a in [i * 0.25 for i in range(0, 260)] if buried(a))
    a_lo = min(a for a in [-i * 0.25 for i in range(0, 260)] if buried(a))
    bowl = round_arc(cb, rb, a_hi, 360 + a_lo)
    y_top = cb[1] + rb * 0.6                            # solve: left edge meets the bowl's outer circle
    for _ in range(40):
        y_top = cb[1] + math.sqrt(max(1.0, rb * rb - (left_edge(y_top) - cb[0]) ** 2))
    y_arm = cb[1] - rb                                  # the tail's outer edge, level with the bowl's bottom
    st = stem(xs, y_arm, y_top, bottom='right', top='right')
    tail = _arm_at(left_edge(y_arm), xs + tail_len, 'bottom', y_arm)
    return [bowl, st, tail], dict(a_hi=a_hi, a_lo=a_lo, stem_x=xs, y_top=y_top, y_arm=y_arm, xr=xr)

def build_at():
    R = WIDE / 2; c = (R, MID); ci = add(c, RING_OFF)    # the ring: the O's own construction
    cb = (ci[0] - (AT_TAIL - w_stem(MID) / 2) / 2, ci[1])   # centre the a's box on the ring's counter
    inner, k = _a_form(cb, AT_BOWL_R, AT_TAIL)
    clear = (R - RING_W) - max(norm(sub(p, ci)) for q in inner for p in q.flatten())
    return glyph(64, round_ring(c, R) + inner, sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "A complete R1 ring -- the O's construction at the O's size, outer radius %.0f, spanning -10..710, "
        "heavy at the lower left and light at the upper right -- enclosing a small single-storey a: an R1 "
        "bowl of outer radius %.0f open on the right between %.1f and %.1f deg, an R3 stem flush with the "
        "bowl's rightmost point closing that opening, and an R4 tail (rules.arm through _arm_at) running "
        "%.0f right from the stem's centre with its outer edge level on the bowl's baseline and an R5 tip at "
        "the bottom-right corner.  The a's box is centred on the ring's counter, standing %.1f clear of it "
        "at its nearest point." % (R, AT_BOWL_R, k['a_lo'], k['a_hi'], AT_TAIL, clear),
        "none in weight, taper, cut or displacement.  Two readings the rules leave open: the a's size and "
        "tail length (chosen so the a fills the ring and keeps a clear counter of its own), and the stem's "
        "top cut, which is a junction cut with its tip at the shared corner on the bowl's outer circle "
        "rather than R5's free-end corner, exactly as set_straight cuts an arm's buried end.",
        ring=(c, R), bowl=(cb, AT_BOWL_R), bowl_arc=(k['a_hi'], 360 + k['a_lo']), stem_x=k['stem_x'],
        stem_top_y=k['y_top'], tail_outer_y=k['y_arm'], clearance=clear))

# ==================================================================================
# ampersand
# ==================================================================================
# A small closed upper loop, a large lower bowl open where the leg passes through it, and one
# R2 '\' leg running from a junction buried in the loop's lower-left band, down across the
# bowl, to a free R5 foot on the baseline.  The bowl's two radial ends are buried in the leg,
# so the leg is the bowl's right-hand wall and nothing crosses it: one leg leaves the letter
# at the lower right, and there is no second stroke to make an X with.
#
# WHY THE LEG'S TOP GOES IN THE LOOP'S LOWER LEFT.  R5 cuts a diagonal 20.6 deg off the
# HORIZONTAL, so its terminal is a near-level segment about 40 units long -- half again the
# stroke's own width.  To hide inside an R1 band that cut needs the band to run nearly level
# there AND to be thicker than the cut's rise across it.  An R1 band is level at its 69.4 and
# 249.4 deg points and thickest at 225 (53.0 against 13.4 at 45), so only the lower left is
# both.  On a ring's right the band is 15 wide and any line that could carry the cut passes
# 40 units inside the counter.  That is measured, not assumed: it is why the previous version
# of this glyph, which ended the leg at the loop's upper right, could not bury its terminal
# and left the cut's far corner 15 units proud of the outer circle as a lump on the loop.
AMP_BOWL_R = 250.0                  # bowl outer radius: bottom on -OVER_ROUND, so the bowl is 500 across
AMP_LOOP_R = 145.0                  # loop outer radius: top on CAP + OVER_ROUND; 58% of the bowl, so the
                                    # counter it can keep at R1's absolute stroke is still a clear eye
AMP_BURY   = 2.0                    # how far inside an outline an end must sit to count as buried
AMP_BOWL_C = (0.0, AMP_BOWL_R - OVER_ROUND)
AMP_LOOP_X = MEDIUM - AMP_BOWL_R - AMP_LOOP_R      # 163: the bowl's left and the loop's right are the
                                                   # glyph's extremes, so R8's medium body fixes this
AMP_LOOP_C = (AMP_LOOP_X, CAP + OVER_ROUND - AMP_LOOP_R)

def _inside(p, k):
    """Is p inside the (convex) stroke contour k?"""
    poly = k.flatten(); n = len(poly); inside = False
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > p[1]) != (y1 > p[1]) and p[0] < x0 + (p[1] - y0) * (x1 - x0) / (y1 - y0): inside = not inside
    return inside

def _cut_corners(k, top=True):
    """The two corners of a steep diagonal's top (or bottom) R5 cut."""
    s = -1 if top else 1
    return sorted(sorted(k.flatten(), key=lambda p: s * p[1])[:2], key=lambda p: p[0])

def _amp_foot_x(d):
    """x on the baseline for a leg centre-line standing d from the loop's centre, on its lower-left."""
    v = from_ang(BACK_DEG); n = (v[1], -v[0])          # n: the up-right normal, toward the loop's centre
    return AMP_LOOP_C[0] + (AMP_LOOP_C[1] * n[1] - d) / n[0]

def _amp_leg_base(fx):
    """The leg's centre-line lower end, solved so the R5 foot's tip sits exactly on the baseline."""
    v = from_ang(BACK_DEG); y0 = 0.0
    for _ in range(20):
        p0 = (fx + y0 * v[0] / v[1], y0)
        y0 += 0 - diagonal(p0, add(p0, mul(v, 500.0)), bottom='left', top='right').bbox()[1]
    return (fx + y0 * v[0] / v[1], y0)

def _amp_leg(p0, t):
    return diagonal(p0, add(p0, mul(from_ang(BACK_DEG), t)), bottom='left', top='right')

def _dist_to_poly(p, k):
    """Distance from p to the filled convex contour k (0 if inside)."""
    if _inside(p, k): return 0.0
    poly = k.flatten(); best = 1e18
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ab = sub(b, a); t = max(0.0, min(1.0, dot(sub(p, a), ab) / dot(ab, ab)))
        best = min(best, norm(sub(p, add(a, mul(ab, t)))))
    return best

def _cut_samples(k, n=24):
    a, b = _cut_corners(k)
    return [add(a, mul(sub(b, a), j / float(n))) for j in range(n + 1)]

def _amp_clear_of_eye(k):
    """How far the leg keeps clear of the loop's counter circle (negative: it eats the eye)."""
    return _dist_to_poly(add(AMP_LOOP_C, RING_OFF), k) - (AMP_LOOP_R - RING_W)

def _amp_top_window(p0):
    """Centre-line lengths at which the leg's whole top cut lies inside the loop's band AND the leg
    keeps out of the loop's counter, so nothing of it shows in the eye."""
    ok = []
    for i in range(260, 900, 4):
        k = _amp_leg(p0, float(i))
        if (all(_in_band(q, AMP_LOOP_C, AMP_LOOP_R, AMP_BURY) for q in _cut_samples(k))
                and _amp_clear_of_eye(k) >= AMP_BURY):
            ok.append(float(i))
    return ok

def _amp_leg_offsets():
    """The window of perpendicular distances from the loop's centre within which the leg's whole
    cross-section lies inside the loop's band where it crosses: its near edge outside the counter
    and its far edge inside the outer circle, both by AMP_BURY.  The window is one-sided about the
    ring because RING_OFF's component along the leg's normal (R1's page-fixed displacement, seen
    edge-on) moves the counter away from the leg's lower-left side."""
    v = from_ang(BACK_DEG); n = (v[1], -v[0])             # the normal pointing at the loop's centre
    half = w_backslash(AMP_LOOP_C[1]) / 2                 # the leg's half width at the loop's centre height
    off = dot(RING_OFF, n)
    return ((AMP_LOOP_R - RING_W) + AMP_BURY + half - off, AMP_LOOP_R - AMP_BURY - half)

def _amp_solve():
    """The leg's line, its top, and the bowl's two ends -- each the middle of its own window."""
    ds = _amp_leg_offsets()
    if ds[0] >= ds[1]: raise RuntimeError(f'ampersand: no leg offset fits the loop band {ds}')
    d = (ds[0] + ds[1]) / 2
    p0 = _amp_leg_base(_amp_foot_x(d))
    ts = _amp_top_window(p0)
    if not ts: raise RuntimeError('ampersand: no leg length buries the top cut in the loop band')
    leg = _amp_leg(p0, (ts[0] + ts[-1]) / 2)
    def burial(lo, hi):
        w = [a / 4 for a in range(4 * lo, 4 * hi)
             if all(_inside(q, leg) for q in _band_end(AMP_BOWL_C, AMP_BOWL_R, a / 4))]
        if not w: raise RuntimeError(f'ampersand: bowl end has no window in {lo}..{hi}')
        return (w[0] + w[-1]) / 2, (w[0], w[-1])
    a0, w0 = burial(40, 180)        # the bowl's upper end, buried in the leg
    a1, w1 = burial(-110, 20)       # the bowl's lower end, buried in the leg
    return dict(d=d, ds=ds, leg=leg, p0=p0, t=(ts[0] + ts[-1]) / 2, ts=(ts[0], ts[-1]),
                a0=a0, w0=w0, a1=a1, w1=w1)

def build_ampersand():
    k = _amp_solve()
    leg = k['leg']; cl, cb = AMP_LOOP_C, AMP_BOWL_C
    loop = round_ring(cl, AMP_LOOP_R)
    bowl = round_arc(cb, AMP_BOWL_R, k['a0'], k['a1'] + 360)
    cut = _cut_corners(leg); y_cut = (cut[0][1] + cut[1][1]) / 2
    ci = add(cl, RING_OFF); r_in = AMP_LOOP_R - RING_W
    eye_clear = _amp_clear_of_eye(leg)
    out_clear = AMP_LOOP_R - max(norm(sub(q, cl)) for q in _cut_samples(leg))
    in_clear = min(norm(sub(q, ci)) for q in _cut_samples(leg)) - r_in
    foot = min(leg.flatten(), key=lambda p: p[1])
    x0, y0, x1, y1 = bbox([c.flatten() for c in loop + [bowl, leg]])
    return glyph(38, loop + [bowl, leg], sb=(SB_ROUND, SB_ROUND), notes=_notes(
        "Three parts and no free end but the foot.  A closed upper loop: a complete R1 round of outer radius "
        "%.0f, top on %d.  A lower bowl: an R1 arc of outer radius %.0f, bottom on -%d, running from %.1f deg "
        "counter-clockwise over the top, down the left, round the bottom and up the right to %.1f deg -- both "
        "radial ends buried inside the leg, which is therefore the bowl's whole right-hand wall.  A leg: one "
        "R2 '\\\\' at the A's right-leg angle (%.1f deg), %.1f wide where it leaves the loop and %.1f at the "
        "foot, whose top is a JUNCTION cut lying wholly inside the loop's lower-left band and whose foot is a "
        "free R5 cut like the A's right foot, its tip exactly on the baseline at x %.2f.  The bowl and the "
        "loop meet where the leg crosses them, so the three parts union into one outline with no terminal "
        "showing anywhere above the baseline.  Body %.0f wide, R8's medium exactly, which is what fixes the "
        "loop's centre once the two radii are chosen."
        % (AMP_LOOP_R, CAP + OVER_ROUND, AMP_BOWL_R, OVER_ROUND, k['a0'], k['a1'], BACK_DEG,
           w_backslash(y_cut), w_backslash(0), foot[0], x1 - x0),
        "None in weight, taper, cut, displacement or overshoot; the glyph spans -%d..%d, the round overshoots "
        "of the bowl and the loop, and the leg's foot tip sits on 0 like the A's.  Four readings the rules "
        "leave open, each solved by scanning rather than chosen: (1) the leg's centre-line stands %.1f from "
        "the loop's centre, the middle of the window %.1f..%.1f in which its whole cross-section fits the band and "
        "the leg still keeps out of the eye -- at %.1f the leg clears the loop's counter by %.1f and the cut "
        "lies %.1f inside the outer circle and %.1f outside the counter; (2) the top cut is at %.0f along "
        "the centre-line, "
        "the middle of %.0f..%.0f, every point of it at least %.1f inside the band; (3) and (4) the bowl's "
        "ends are the middles of %.2f..%.2f and %.2f..%.2f deg, the windows in which their radial ends lie "
        "wholly inside the leg.  The sizes themselves -- a bowl %.0f across and a loop %.0f%% of it -- are "
        "the one thing read by eye, and they are what R8's medium body then measures.  Two things this glyph "
        "deliberately does NOT have.  There is no tail past the leg: an R1 arc carried beyond the crossing "
        "leaves the bowl's band at its thinnest (%.1f at 45 deg, ROUND_THIN) and reads as a second spike "
        "crossing the first, so the bowl stops inside the leg instead and one stroke, the leg, leaves the "
        "letter at the lower right.  And there is no straight arm in its place: R5 cuts a shallow '/' only "
        "%.1f deg off its own axis, so its terminal would be a %.0f-unit sliver, far longer than any band it "
        "could hide in.  The bowl's lowest point measures %.4f rather than -%d because pen.arc_segments "
        "splits the arc into equal cubics and the baseline falls inside one of them: the pen's "
        "approximation, the same in every partial round in the face, not a placement."
        % (OVER_ROUND, CAP + OVER_ROUND, k['d'], k['ds'][0], k['ds'][1], k['d'], eye_clear, out_clear, in_clear,
           k['t'], k['ts'][0], k['ts'][1], AMP_BURY, k['w0'][0], k['w0'][1], k['w1'][0], k['w1'][1],
           2 * AMP_BOWL_R, 100 * AMP_LOOP_R / AMP_BOWL_R, ROUND_THIN, APEX_DEG - CUT_DEG,
           w_slash(100) / math.sin(math.radians(APEX_DEG - CUT_DEG)),
           min(p[1] for p in bowl.flatten(per=0.02)), OVER_ROUND),
        loop=(cl, AMP_LOOP_R), bowl=(cb, AMP_BOWL_R, k['a0'], k['a1']), leg_offset=k['d'],
        leg_top_cut=cut, leg_foot_tip=foot, extent=(x0, y0, x1, y1),
        eye_clearance=eye_clear, cut_inside_outer=out_clear, cut_outside_counter=in_clear))

GLYPHS = {
    'period': build_period, 'comma': build_comma, 'colon': build_colon, 'semicolon': build_semicolon,
    'exclam': build_exclam, 'question': build_question,
    'quotesingle': build_quotesingle, 'quotedbl': build_quotedbl,
    'hyphen': build_hyphen, 'endash': build_endash, 'emdash': build_emdash, 'underscore': build_underscore,
    'parenleft': build_parenleft, 'parenright': build_parenright,
    'bracketleft': build_bracketleft, 'bracketright': build_bracketright,
    'slash': build_slash, 'plus': build_plus, 'equal': build_equal,
    'asterisk': build_asterisk, 'numbersign': build_numbersign,
    'percent': build_percent, 'at': build_at, 'ampersand': build_ampersand,
}
