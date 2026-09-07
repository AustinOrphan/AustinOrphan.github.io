"""
set_digits: the lining figures 0-9.

One weight system and one width system.  Every straight stroke is a lib constructor --
rules.stem, rules.diagonal, rules.arm, rules.horizontal -- and every round is R1's
construction on an ellipse, built here because lib/rules.py has only the circular
round (rules.round_ring / rules.round_arc), which no figure in this set can use.

The narrowed round (`_ring`, `_arc`).  R8 gives the digits the medium body, 558,
and the vertical metrics give every round the O's full 720 span (-10 to 710).  A
circle cannot do both, so the digits' rounds are ellipses: the outer contour is an
ellipse of semi-axes (a, b) and the counter is R1's counter -- that contour brought
in by RING_W and then displaced by RING_OFF on the page.  The inward offset of an
ellipse is not an ellipse, so the counter is not faked with a scaled one: `_off_pt`
is R1's offset point itself and `_off_segs` draws it as one cubic per 20 degrees
through its own points and tangents, which follows it to a few thousandths of a
unit (counter_fit_error in each glyph's notes).  R1 then holds exactly: an offset
curve runs parallel to its parent, so the band's perpendicular thickness is
RING_W + RING_OFF . n at every point -- 53.02 where the normal points to 225
degrees and 13.36 at 45, the O's own thick and thin, whatever the round's size
(band_perp_min_max in the notes).  Partial narrowed rounds end in cuts along the
ray from the outer centre, which is what pen.arc_band does for a circle.

Joins.  Where a straight meets a round, the straight is tangent to the round's
mid-line at the join, so the two run in the same direction there and the only
mismatch is the width difference between R2/R3's field and R1's band (under 3
units, recorded per glyph).  Where two rounds meet (3, 6, 8, 9) the bands
overlap, and the buried end is placed by measurement: `_merge_t` scans for the cut
that sits deepest inside the other band, and the clearance it finds is recorded.
Where a horizontal meets the top of a round (5) the join is set_bowl's wedge: the
underside runs level past the round's top and meets the counter in a corner,
because a 47.5 horizontal cannot coincide with a band that is 19.2 thick there.

Proportions.  Body 558 (R8 medium) for every figure but 1, which is a stem and its
flag and is left at its own width, so nine figures take a 638 advance and the 1 takes
272: the set is proportional.  SPEC does not say whether the figures should be tabular
(R8 gives bodies, R9 gives bearings, neither mentions the ten advances agreeing), so
both settings were built and looked at and the proportional one encoded; the argument
is in build_one's `tabular` note, and the tabular setting -- the same ink centred in
638 -- ships beside it as the unencoded alternate `one.tab`.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib')); sys.path.insert(0, FONT)
from pen import (Contour, add, sub, mul, dot, unit, perp, norm, ang, arc_segments,
                 line_2pt, line_ang, isect, from_poly, ccw)
from metrics import CAP, OVER_ROUND, SB_STRAIGHT, SB_ROUND
from rules import (glyph, stem, diagonal, horizontal, arm,
                   RING_W, RING_OFF, ROUND_THICK, ROUND_THIN, CUT_DEG, HORIZ_MID, HORIZ_TAPER,
                   w_stem, w_slash, w_backslash, w_horizontal)

BODY = 558                      # R8 medium: the A's foot spread, the digits' body
DIGIT_ADV = BODY + 2 * SB_ROUND  # 638: the advance a full-body figure takes under R8 + R9
TOP, BOT = CAP + OVER_ROUND, -OVER_ROUND     # 710 / -10: where a round's extremes sit

# ---- the narrowed round: R1 on an ellipse ------------------------------------------
def _ell(c, a, b, t):
    """Point at parametric angle t (degrees) on the ellipse (c, a, b)."""
    r = math.radians(t); return (c[0] + a * math.cos(r), c[1] + b * math.sin(r))

def _ell_segs(c, a, b, t0, t1):
    """(start, cubic segments) of the elliptical arc t0 -> t1, the unit-circle arc pen.arc_segments
    builds mapped by the affine (x, y) -> c + (a x, b y), which carries cubics to cubics."""
    start, segs = arc_segments((0.0, 0.0), 1.0, t0, t1)
    m = lambda p: (c[0] + a * p[0], c[1] + b * p[1])
    return m(start), [(s[0], m(s[1]), m(s[2]), m(s[3])) for s in segs]

def _ell_contour(c, a, b, t0, t1):
    start, segs = _ell_segs(c, a, b, t0, t1)
    k = Contour(start)
    for s in segs: k.curve_to(s[1], s[2], s[3])
    return k

def _n_in(bowl, t):
    """Inward unit normal of the outer ellipse at parametric angle t."""
    r = math.radians(t)
    return unit((-bowl['b'] * math.cos(r), -bowl['a'] * math.sin(r)))

def _off_pt(bowl, t):
    """R1's counter point for t: the outer point brought in RING_W along the inward normal and then
    displaced by RING_OFF on the page.  This is R1 verbatim -- an offset curve, not a scaled ellipse."""
    return add(add(_ell(bowl['c'], bowl['a'], bowl['b'], t), mul(_n_in(bowl, t), RING_W)), RING_OFF)

def _off_tan(bowl, t):
    """Unit tangent of the counter at t (direction of increasing t).  An offset curve is parallel to
    its parent, so this is the outer ellipse's own tangent -- which is why the band's perpendicular
    thickness is exactly RING_W + RING_OFF . n everywhere (see _band_perp)."""
    r = math.radians(t)
    return unit((-bowl['a'] * math.sin(r), bowl['b'] * math.cos(r)))

OFF_STEP = 20.0          # counter is drawn as one cubic per this many degrees

def _off_segs(bowl, t0, t1):
    """Cubic segments along the counter from t0 to t1: each piece is the cubic with the curve's own
    end points and end tangents that also passes through the curve's mid point (a 2x2 solve), so the
    drawn contour follows R1's offset to a small fraction of a unit (measured in _fit_error)."""
    n = max(1, int(math.ceil(abs(t1 - t0) / OFF_STEP)))
    segs = []
    for i in range(n):
        u0, u1 = t0 + (t1-t0)*i/n, t0 + (t1-t0)*(i+1)/n
        P0, P1 = _off_pt(bowl, u0), _off_pt(bowl, u1)
        T0, T1 = _off_tan(bowl, u0), _off_tan(bowl, u1)
        if t1 < t0: T0, T1 = mul(T0, -1), mul(T1, -1)
        V = mul(sub(_off_pt(bowl, (u0+u1)/2), mul(add(P0, P1), 0.5)), 1/0.375)
        den = T0[0]*(-T1[1]) - T0[1]*(-T1[0])
        k0 = (V[0]*(-T1[1]) - V[1]*(-T1[0])) / den
        k1 = (T0[0]*V[1] - T0[1]*V[0]) / den
        segs.append(('c', add(P0, mul(T0, k0)), sub(P1, mul(T1, k1)), P1))
    return _off_pt(bowl, t0), segs

def _off_contour(bowl, t0, t1):
    start, segs = _off_segs(bowl, t0, t1)
    k = Contour(start)
    for sg in segs: k.curve_to(sg[1], sg[2], sg[3])
    return k

def _ray_s(bowl, t, span=100.0):
    """The counter parameter where the ray from the outer centre through the outer point at t meets
    the counter -- the inner end of R1's radial cut, which is what pen.arc_band takes on a circle."""
    u = unit(sub(_ell(bowl['c'], bowl['a'], bowl['b'], t), bowl['c']))
    def g(s):
        v = sub(_off_pt(bowl, s), bowl['c'])
        return u[0]*v[1] - u[1]*v[0]
    lo, hi = t - span, t + span
    glo = g(lo)
    for _ in range(80):
        m = (lo + hi) / 2
        if glo * g(m) <= 0: hi = m
        else: lo, glo = m, g(m)
    return (lo + hi) / 2

def _counter_dist(bowl, p, n=90):
    """Signed distance from p to the counter, positive outside it (i.e. in the band or beyond)."""
    best = min(range(n), key=lambda i: math.dist(p, _off_pt(bowl, 360.0*i/n)))
    s, step = 360.0*best/n, 360.0/n
    for _ in range(40):
        cands = [s - step, s, s + step]
        s = min(cands, key=lambda x: math.dist(p, _off_pt(bowl, x))); step /= 2
    q = _off_pt(bowl, s)
    return math.dist(p, q) * (1 if dot(sub(p, q), mul(_n_in(bowl, s), -1)) > 0 else -1)

def _band_perp(bowl, t):
    """Thickness of the band at t along the outer curve's normal.  Exactly R1's law, because the
    counter is a true offset: RING_W plus the part of the displacement that lies along the normal."""
    n = _n_in(bowl, t)
    return RING_W + RING_OFF[0]*n[0] + RING_OFF[1]*n[1]

def _fit_error(bowl, t0=0.0, t1=360.0, n=200):
    """How far the drawn counter (cubics through the offset every OFF_STEP degrees) departs from
    R1's exact offset curve, in units: the largest gap over the drawn range."""
    start, segs = _off_segs(bowl, t0, t1)
    worst, last = 0.0, start
    for sg in segs:
        c1, c2, p1 = sg[1], sg[2], sg[3]
        for i in range(1, 8):
            u = i/8.0; m = 1-u
            q = (m**3*last[0] + 3*m*m*u*c1[0] + 3*m*u*u*c2[0] + u**3*p1[0],
                 m**3*last[1] + 3*m*m*u*c1[1] + 3*m*u*u*c2[1] + u**3*p1[1])
            worst = max(worst, abs(_counter_dist(bowl, q)))
        last = p1
    return worst

def _ring(c, a, b):
    """A complete narrowed round (R1 on an ellipse). -> [outer ccw, counter cw]"""
    bowl = dict(c=c, a=a, b=b)
    return [_ell_contour(c, a, b, 0, 360).ccw(), _off_contour(bowl, 0, 360).cw()]

def _arc(bowl, t0, t1):
    """A partial narrowed round between parametric angles t0 -> t1 (ccw), both ends cut along the ray
    from the outer centre, as pen.arc_band cuts a circle. -> one ccw Contour"""
    start, outer = _ell_segs(bowl['c'], bowl['a'], bowl['b'], t0, t1)
    s1, s0 = _ray_s(bowl, t1), _ray_s(bowl, t0)
    if s0 > s1: s0 -= 360
    k = Contour(start)
    for sg in outer: k.curve_to(sg[1], sg[2], sg[3])
    k.line_to(_off_pt(bowl, s1))
    for sg in _off_segs(bowl, s1, s0)[1]: k.curve_to(sg[1], sg[2], sg[3])
    return k.ccw()

def _seg(p, q, n=12):
    return [(p[0] + (q[0]-p[0])*i/n, p[1] + (q[1]-p[1])*i/n) for i in range(n+1)]

# ---- straights: corners, and the tangent join to a round ---------------------------
def _centres(E0, s0, E1, s1, wf=None, iters=24):
    """Centre-line ends (c0, c1) of a stroke whose corner on side s0 sits exactly on E0 (the lower
    end) and whose corner on side s1 on E1.  s = +1 the stroke's own left side (left of p0->p1),
    -1 its right, 0 the centre-line end itself.  R5 and R6 fix corners while rules.diagonal and
    rules.stem take centre-line ends, and lib/rules.py has no primitive for the conversion, so it
    is solved here by fixed-point iteration (the taper leaves edge and centre-line about half a
    degree apart, so one step will not do).  Same device as set_straight's _stem_x."""
    if wf is None: wf = w_slash if E1[0] >= E0[0] - 1e-9 else w_backslash
    c0, c1 = E0, E1
    for _ in range(iters):
        n = perp(unit(sub(c1, c0)))
        c0, c1 = sub(E0, mul(n, s0 * wf(c0[1]) / 2)), sub(E1, mul(n, s1 * wf(c1[1]) / 2))
    return c0, c1

def _mid(bowl, t):
    """Mid-line point of the band at parametric angle t: halfway along the ray cut."""
    p = _ell(bowl['c'], bowl['a'], bowl['b'], t)
    return mul(add(p, _off_pt(bowl, _ray_s(bowl, t))), 0.5)

def _mid_dir(bowl, t, h=1e-4):
    return unit(sub(_mid(bowl, t + h), _mid(bowl, t - h)))

def _tangent_t(bowl, target, lo, hi, iters=80):
    """The t in (lo, hi) where the band's mid-line runs straight at `target`: the tangent to the
    mid-line at t passes through it.  This is how a straight meets a round in this set -- the
    stroke leaves in the mid-line's own direction, so there is no kink, only the width difference
    between the R2/R3 field and the R1 band."""
    def f(t):
        m = _mid(bowl, t); d = _mid_dir(bowl, t); v = sub(target, m)
        return d[0]*v[1] - d[1]*v[0]
    a, b = lo, hi
    fa = f(a)
    for _ in range(iters):
        m = (a + b) / 2
        if fa * f(m) <= 0: b = m
        else: a, fa = m, f(m)
    return (a + b) / 2

def _round_note(bowl, arc=None):
    c, a, b = bowl['c'], bowl['a'], bowl['b']
    lo, hi = arc if arc else (0.0, 360.0)
    n = dict(centre=c, semi_axes=(a, b), stroke_thick_thin=(round(ROUND_THICK, 2), round(ROUND_THIN, 2)),
             band_perp_min_max=(round(min(_band_perp(bowl, lo + (hi-lo)*i/200) for i in range(201)), 2),
                                round(max(_band_perp(bowl, lo + (hi-lo)*i/200) for i in range(201)), 2)),
             counter_fit_error=round(_fit_error(bowl, lo, hi), 3))
    if arc: n['arc_parametric_deg'] = arc
    return n

_R1_NOTE = ("R1 on an ellipse (module docstring): outer semi-axes as given, counter the same contour "
            f"brought in by RING_W {RING_W:.2f} and displaced {norm(RING_OFF):.1f} toward 45 deg on the page, so "
            f"the band is {ROUND_THICK:.1f} at its lower left and {ROUND_THIN:.1f} at its upper right exactly as "
            "the O's is (R1, R7).  The counter is R1's offset curve itself, not a scaled ellipse: because an "
            "offset curve runs parallel to its parent, the band's perpendicular thickness comes out exactly "
            f"RING_W + RING_OFF . n at every point, {ROUND_THICK:.2f} where the normal points at 225 deg and "
            f"{ROUND_THIN:.2f} at 45 (band_perp_min_max reports the range over the drawn arc).  It is drawn as "
            f"one cubic per {OFF_STEP:g} deg through the offset's own points and tangents; counter_fit_error is "
            "how far that drawing departs from the offset, in units.")

# ---- 0 ----------------------------------------------------------------------------
def build_zero():
    b = dict(c=(BODY/2, (TOP + BOT)/2), a=BODY/2, b=(TOP - BOT)/2)
    return glyph(ord('0'), _ring(b['c'], b['a'], b['b']), sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=(f"One narrowed round: an ellipse {BODY} wide (R8 medium) and {TOP - BOT} tall, its extremes "
                      f"on the round overshoots {BOT} and {TOP} exactly as the O's are, with R1's counter.  "
                      f"That is the whole figure; nothing is added to distinguish it from the O, because the "
                      f"width already does: the O is a 720 circle, the zero a {BODY} ellipse, {720 - BODY} units "
                      f"narrower, and it stands among figures of its own width."),
        round=_round_note(b), r1=_R1_NOTE,
        weight=(f"The band is the O's own: {ROUND_THICK:.1f} at the lower left, {ROUND_THIN:.1f} at the upper "
                f"right.  Narrowing the round does not thin it -- R1's stroke and displacement are absolute -- "
                f"so the zero is exactly as heavy as the O and as the other figures' bowls."),
        spacing=f"{SB_ROUND}/{SB_ROUND}, round both sides.",
        deviations=("none from R1-R9.  The counter is R1's own offset curve, drawn as cubics that follow it to "
                    "counter_fit_error (thousandths of a unit).  No slash or dot: the mark supplies no such form.")))

# ---- 1 ----------------------------------------------------------------------------
FLAG_DEG = 50.0          # the flag's lean off the horizontal (see build_one notes)
FLAG_DROP = 165.0        # how far the flag falls from the cap line

def _one_TL(x_s):
    """The stem's upper-LEFT corner once its R5 top cut is taken with the body to the left
    (tip at the upper-right corner on CAP): the corner is where the cut meets the stem's own
    left edge, CUT_DEG below the cap line.  Same device as build_four's TLc."""
    left_edge = line_2pt((x_s - w_stem(0)/2, 0.0), (x_s - w_stem(CAP)/2, CAP))
    top_cut = line_ang((x_s + w_stem(CAP)/2, CAP), 180 + CUT_DEG)
    return isect(left_edge, top_cut)

def _one_parts():
    """The 1's ink, and the numbers its notes quote.  build_one and build_one_tab share it:
    the two glyphs are the same two strokes, set differently in their advance."""
    run = FLAG_DROP / math.tan(math.radians(FLAG_DEG))                       # the flag's horizontal reach
    x_s = run - _one_TL(0.0)[0]                                              # tip of the flag at x = 0
    TL = _one_TL(x_s)                                                        # the stem's upper-left corner
    st = stem(x_s, 0, CAP, bottom='left', top='left')
    tip = (TL[0] - run, TL[1] - FLAG_DROP)
    c0, c1 = _centres(tip, +1, TL, +1, w_slash)
    flag = diagonal(c0, c1, bottom='right', top=None)
    n1 = perp(unit(sub(c1, c0)))
    far = add(c1, mul(n1, -w_slash(c1[1])/2))                # the buried flat end's far corner
    clear = (x_s + w_stem(far[1])/2) - far[0]                # how far it stands inside the stem's right edge
    body = x_s + w_stem(0)/2
    return dict(strokes=[st, flag], x_s=x_s, TL=TL, far=far, clear=clear, body=body)

def build_one():
    p = _one_parts()
    x_s, TL, far, clear, body = p['x_s'], p['TL'], p['far'], p['clear'], p['body']
    return glyph(ord('1'), p['strokes'], sb=(SB_ROUND, SB_STRAIGHT), notes=dict(
        construction=(f"An R3 stem (rules.stem) with free R5 cuts at both ends, no serif, and a short R2 \"/\" "
                      f"flag (rules.diagonal) falling {FLAG_DROP:g} units from the stem's upper-left corner at "
                      f"{FLAG_DEG:g} deg.  The flag's upper edge ends exactly on that corner -- the point where "
                      f"the stem's R5 top cut meets its left edge, at y {TL[1]:.1f}, {CAP - TL[1]:.1f} units below the cap "
                      f"line -- so the two strokes share one outline point and the top of the figure is one "
                      f"rising line: the flag's upper edge at {FLAG_DEG:g} deg, then the cut at {CUT_DEG:g} deg "
                      f"on up to the stem's tip on CAP.  The flag's flat end is buried in the stem: its far "
                      f"corner ({far[0]:.1f}, {far[1]:.1f}) stands {clear:.1f} units inside the stem's right "
                      f"edge and well below its top cut, so nothing of it shows."),
        cuts=(f"R5 names every tip here by the corner farther from the letter's centre.  The figure spans "
              f"x 0..{body:.1f}, so its centre is x={body/2:.1f} and the stem, centred on x={x_s:.1f}, stands "
              f"right of it: the stem's far corners are its RIGHT ones ({body - body/2:.1f} units from the centre "
              f"against {(x_s - w_stem(0)/2) - body/2:.1f} for its left ones, at the baseline), so the stem is cut "
              f"body='left' at both ends "
              f"and its tips fall at the lower-right and the upper-right -- the same reading, and the same "
              f"direction of cut, as the 4's stem, which also stands right of its letter's centre.  The flag's "
              f"free end is the figure's left extreme, its tip the corner away from the body (body='right').  "
              f"R7 does not enter: it chooses only where R5 leaves a symmetric letter undecided "
              f"(set_straight's I and T), and the flag makes this figure asymmetric."),
        flag=(f"tip at ({0:.0f}, {TL[1] - FLAG_DROP:.1f}), an R5 cut with the body to the right, {CUT_DEG:g} deg off "
              f"the horizontal as R5 gives a diagonal.  {FLAG_DEG:g} deg is chosen: shallower reads better as a "
              f"flag but R5's horizontal-referenced cut degenerates into a spike as the stroke approaches it "
              f"(K's terminals, set_diagonal), and at {FLAG_DEG:g} deg the wedge is "
              f"{FLAG_DEG - CUT_DEG:.1f} deg and the cut about {w_slash(TL[1] - FLAG_DROP)/math.sin(math.radians(FLAG_DEG - CUT_DEG)):.0f} units, "
              f"in the range the rest of the face keeps."),
        proportion=(f"Body {body:.0f}, not R8's medium {BODY}: the figure is a stem and its flag and has no bowl "
                    f"or arm to fill a {BODY} box, and R8 is a table of body widths, not a demand that a stroke "
                    f"be stretched to reach one.  R9's bearings then give it advance "
                    f"{round(body) + SB_ROUND + SB_STRAIGHT} against the other nine figures' {DIGIT_ADV}."),
        tabular=(f"SPEC is silent on whether the figures are tabular: R8 gives bodies, R9 gives bearings by the "
                 f"shape of the extreme, and neither says the ten advances must agree.  Decided here by looking, "
                 f"and the decision is the encoded 1's: PROPORTIONAL.  Both were built and rendered at 110 and "
                 f"240 px ('0123456789', '1971 1471', '11 111', '2026').  Tabular sets this ink in the "
                 f"others' {DIGIT_ADV}, which leaves {(DIGIT_ADV - body)/2:.0f} units of space on each side of a "
                 f"stroke {body:.0f} wide: '11' then stands {DIGIT_ADV:.0f} units apart, more than three times "
                 f"the figure's own body, and '1971' and '11 111' break into islands -- the ordinary cost of "
                 f"tabular figures, but this is a display face, set large and in short strings, where that hole "
                 f"is the thing the eye lands on.  Proportional shows no matching fault: at 240 px the 1 in "
                 f"'0123456789' sits in the rhythm, tight rather than gappy.  The tabular setting is not thrown "
                 f"away -- the same two strokes centred in {DIGIT_ADV} are the unencoded alternate 'one.tab' "
                 f"(cp -1, core's 'A.open' precedent), so if SPEC later rules the figures tabular the change is "
                 f"a substitution, not a redraw."),
        spacing=(f"{SB_ROUND}/{SB_STRAIGHT}: R9 spaces by the shape of the extreme, and the two extremes differ.  "
                 f"The right one is the stem, so {SB_STRAIGHT}; the left one is the flag's R5 tip at "
                 f"(0, {TL[1] - FLAG_DROP:.1f}), a point over open space, which D6/R9 give {SB_ROUND} -- the same "
                 f"bearing this module gives the 2's and 4's bar tips, the 5's and 7's arm tips.  Taking "
                 f"{SB_STRAIGHT} on the left instead -- the stem's bearing, measured from a tip that stands "
                 f"{x_s - w_stem(0)/2:.0f} units left of the stem's edge -- would "
                 f"leave two adjacent 1s about {2*SB_STRAIGHT + 2*(x_s - w_stem(0)/2):.0f} units apart at the "
                 f"baseline, more than the figure's own body, and '11' would show the hole."),
        deviations=(f"Body width, recorded above, and with it the advance: {round(body) + SB_ROUND + SB_STRAIGHT} "
                    f"where the other nine take {DIGIT_ADV}, so the figures are proportional.  R8 and R9 permit "
                    f"both settings and neither names one, so this is a decision, not a breach; it is argued "
                    f"from rendered evidence under 'tabular' above and the alternative ships as 'one.tab'.  "
                    f"Nothing else departs from R1-R9.")))

def build_one_tab():
    """The tabular 1: the encoded 1's ink, untouched, centred in the other nine figures' advance.
    Unencoded (cp -1), like core's 'A.open' -- the set is proportional by default (build_one's
    'tabular' note), and this is the glyph a tnum substitution would put in its place."""
    p = _one_parts()
    body = p['body']
    pad = (DIGIT_ADV - body) / 2
    return glyph(-1, p['strokes'], adv=DIGIT_ADV, sb=(pad, pad), notes=dict(
        construction=("build_one's two strokes verbatim -- the R3 stem with R5 cuts and the R2 flag -- with no "
                      "change to the ink, only to how it is set.  See build_one for the construction."),
        proportion=(f"Body {body:.1f} as drawn, set in the {DIGIT_ADV} advance the other nine figures take "
                    f"({BODY} + 2 x {SB_ROUND}), so all ten line up in a column."),
        spacing=(f"{pad:.1f} both sides, the padding that centres the ink, not R9's bearings: R9 spaces by the "
                 f"shape of the extreme and would give {SB_ROUND}/{SB_STRAIGHT} (build_one).  A tabular figure "
                 f"gives that up on purpose -- the advance is fixed by the set, and the only question left is "
                 f"where in it the ink sits.  Centred, so a column of figures balances."),
        deviations=(f"R9, deliberately and only here: the bearings are the tabular padding, not the shape's own "
                    f"{SB_ROUND}/{SB_STRAIGHT}.  That is what tabular means, and it is why this is the unencoded "
                    f"alternate rather than the encoded 1.  R1-R8 untouched: the ink is build_one's.")))

# ---- 4 ----------------------------------------------------------------------------
BAR4_Y = 200.0                       # centre-line of the 4's crossbar
STEM4_RIGHT = 0.78 * BODY            # the stem's right edge at the baseline

def build_four():
    x_v = STEM4_RIGHT - w_stem(0)/2
    bar = horizontal(0.0, BODY, BAR4_Y, left='up', right='up')
    w0 = w_horizontal(BODY, 0)
    P = (w0 / math.tan(math.radians(90 - CUT_DEG)), BAR4_Y + w0/2)     # bar's inner (upper) left corner
    left_edge = line_2pt((x_v - w_stem(0)/2, 0.0), (x_v - w_stem(CAP)/2, CAP))
    top_cut = line_ang((x_v + w_stem(CAP)/2, CAP), 180 + CUT_DEG)
    TLc = isect(left_edge, top_cut)                                     # stem's upper-left corner
    c0, c1 = _centres(P, +1, TLc, +1, w_slash)
    diag = diagonal(c0, c1)                                             # both ends buried (bar, stem)
    st = stem(x_v, 0, CAP, bottom='left', top='left')
    slope = ang(sub(c1, c0))
    return glyph(ord('4'), [bar, st, diag], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=(f"A diagonal, a stem and a horizontal (the group's third option): an R2 \"/\" "
                      f"(rules.diagonal) at {slope:.1f} deg from the crossbar to the stem, an R3 stem "
                      f"(rules.stem) at x={x_v:.1f} with its right edge at {STEM4_RIGHT:.0f} "
                      f"({STEM4_RIGHT/BODY:.2f} of the body) and free R5 cuts at both ends, and an R4 crossbar "
                      f"(rules.horizontal, centre-line y={BAR4_Y:g}, away from both metric lines so it tapers "
                      f"symmetrically) running the full body {BODY} with free R5 tips at both ends.  Closed top: "
                      f"the diagonal's upper edge ends exactly on the stem's upper-left corner, where the stem's "
                      f"R5 top cut lands, so the two share one outline point."),
        junctions=(f"Bottom: the diagonal's lower-left corner sits exactly on the crossbar's inner (upper) left "
                   f"corner ({P[0]:.1f}, {P[1]:.1f}), the far end of the bar's R5 left cut, so the outline runs "
                   f"from the bar's tip at (0, {BAR4_Y - w0/2:.1f}) up that cut and straight on up the diagonal "
                   f"with one corner and no shelf; the diagonal's flat end lies inside the bar.  Top: as above, "
                   f"the flat end lies inside the stem, whose width there ({w_stem(TLc[1]):.1f}) covers it."),
        cuts=(f"R5 decides every free end by the corner farther from the letter's centre: the bar's two tips are "
              f"its lower corners (body 'up'), the stem's foot is its lower-right corner and its top the "
              f"upper-right (body 'left'), the stem standing right of centre.  R7's preference for the lower-left "
              f"corner does not apply -- it is R5 that names the tip, and only where R5 leaves a symmetric letter "
              f"undecided (set_straight's I and T) does R7 choose."),
        proportion=f"Body {BODY} (R8 medium), the bar's two tips; the bar reaches {BODY - STEM4_RIGHT:.0f} past the stem.",
        spacing=f"{SB_ROUND}/{SB_ROUND}: both extremes are the bar's R5 tips, points over open space.",
        deviations="none from R1-R9.",
        geometry=dict(stem_x=x_v, bar_y=BAR4_Y, diagonal_deg=slope, diagonal_ends=(c0, c1))))

# ---- 7 ----------------------------------------------------------------------------
def build_seven():
    L = float(BODY)
    bar = arm(0.0, L, 'top', left='cut', right='cut')
    inner = line_2pt((0.0, CAP - w_horizontal(L, 0)), (L, CAP - w_horizontal(L, 1)))
    cut = line_ang((L, CAP), 270 - CUT_DEG)                 # the arm's right R5 cut, from its tip
    Q = isect(inner, cut)                                   # the arm's inner (lower) right corner
    tail_deg = 90 - CUT_DEG                                 # the cut's own direction: the tail continues it
    lo, hi = 0.0, L
    for _ in range(80):                                     # foot tip x that makes the tail's right edge that line
        x_f = (lo + hi) / 2
        c0, c1 = _centres((x_f, 0.0), +1, Q, -1, w_slash)
        n = perp(unit(sub(c1, c0)))
        e0, e1 = sub(c0, mul(n, w_slash(c0[1])/2)), sub(c1, mul(n, w_slash(c1[1])/2))
        if ang(sub(e1, e0)) > tail_deg: hi = x_f
        else: lo = x_f
    tail = diagonal(c0, c1, bottom='right', top=None)
    return glyph(ord('7'), [bar, tail], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=(f"An R4 cap-line arm (rules.arm, top edge level on {CAP}, the whole R4 taper on its "
                      f"underside, R5 tips at both upper corners) the full body {BODY}, and an R2 \"/\" tail "
                      f"(rules.diagonal) hanging from its right end with a free R5 foot -- tip at the lower-left "
                      f"corner on the baseline, at x={x_f:.1f}."),
        join=(f"The tail leans {tail_deg:.1f} deg, which is 90 - CUT_DEG: exactly the direction of the arm's own "
              f"R5 right cut.  Its right edge is placed on that cut's line, with its upper-right corner on the "
              f"arm's inner corner ({Q[0]:.1f}, {Q[1]:.1f}) where the cut ends, so the figure's whole right side "
              f"is one straight line from the tip at ({BODY}, {CAP}) to the foot -- no kink, no coincident edge, "
              f"the two strokes sharing a single outline point.  The tail's flat top end lies inside the arm."),
        terminals=(f"The foot's R5 cut is {CUT_DEG:g} deg off the horizontal against a stroke at {tail_deg:.1f} "
                   f"deg, a {tail_deg - CUT_DEG:.1f} deg wedge about "
                   f"{w_slash(0)/math.sin(math.radians(tail_deg - CUT_DEG)):.0f} units long: an ordinary terminal, "
                   f"not one of K's spikes."),
        proportion=f"Body {BODY} (R8 medium), the arm's two tips on the cap line.",
        spacing=f"{SB_ROUND}/{SB_ROUND}: both extremes are R5 tips (points).",
        deviations="none from R1-R9.",
        geometry=dict(arm_inner_right=Q, tail_deg=tail_deg, foot_tip_x=x_f, tail_ends=(c0, c1))))


# ---- margins: how deeply one round's end cut sits inside another's band -------------
def _margin(p, bowl):
    """Signed distance from p to the nearer edge of `bowl`'s band, positive inside: first order from
    the outer ellipse's implicit form, exact (nearest point) against the counter."""
    c, a, b = bowl['c'], bowl['a'], bowl['b']
    fo = ((p[0]-c[0])/a)**2 + ((p[1]-c[1])/b)**2
    go = math.hypot(2*(p[0]-c[0])/a**2, 2*(p[1]-c[1])/b**2)
    return min((1 - fo)/go, _counter_dist(bowl, p))

def _cut_pts(bowl, t, n=10):
    """The end cut of `bowl`'s band at parametric angle t, sampled: outer point to counter point."""
    return _seg(_ell(bowl['c'], bowl['a'], bowl['b'], t), _off_pt(bowl, _ray_s(bowl, t)), n)

def _merge_t(bowl, target, lo, hi, n=301):
    """The parametric angle in [lo, hi] whose end cut sits most deeply inside `target`'s band, and
    that depth in units (negative: the cut leaves the band by that much).  Used wherever two rounds
    meet, so the buried end is placed by measurement rather than by eye."""
    best = None
    for i in range(n):
        t = lo + (hi - lo) * i / (n - 1)
        m = min(_margin(x, target) for x in _cut_pts(bowl, t))
        if best is None or m > best[1]: best = (t, m)
    return best

# ---- 2 ----------------------------------------------------------------------------
BOWL2 = dict(c=(BODY - 245.0, TOP - 175.0), a=245.0, b=175.0)   # the 2's top round
TERM2 = 200.0        # its free terminal, parametric degrees
OVER2 = 3.0          # how far the round runs past the join, into the diagonal

def build_two():
    b = BOWL2
    bar = arm(0.0, float(BODY), 'bottom', left='cut', right='cut')
    w0 = w_horizontal(float(BODY), 0)
    P = (w0 / math.tan(math.radians(90 - CUT_DEG)), w0)         # the bar's inner (upper) left corner
    target, t_j = P, -50.0
    for _ in range(6):                                          # tangency and the R2 taper, solved together
        t_j = _tangent_t(b, target, -85.0, -15.0)
        c0, c1 = _centres(P, +1, _mid(b, t_j), 0, w_slash)
        target = c0
    diag = diagonal(c0, c1)                                     # both ends buried (bar, round)
    arc = _arc(b, t_j - OVER2, TERM2)
    mis = w_slash(c1[1]) - _band_perp(b, t_j)
    term = _ell(b['c'], b['a'], b['b'], TERM2)
    return glyph(ord('2'), [arc, diag, bar], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=(f"A narrowed round for the top (semi-axes {b['a']:g} x {b['b']:g}, top edge on the round "
                      f"overshoot {TOP} and right extreme on the body {BODY}), an R2 \"/\" diagonal "
                      f"(rules.diagonal) falling from it to the baseline, and an R4 baseline arm (rules.arm, "
                      f"bottom edge level on 0, the whole taper on its top edge) the full body with R5 tips at "
                      f"both lower corners.  The round is cut off at its free terminal at t={TERM2:g} deg "
                      f"({term[0]:.0f}, {term[1]:.0f}), a cut along the ray from its centre as R5 asks of a "
                      f"partial round."),
        join_to_round=(f"The diagonal leaves the round tangentially: its centre-line is the tangent to the band's "
                       f"mid-line at t={t_j:.1f} deg, solved with the R2 taper, so stroke and band run in the "
                       f"same direction there and the diagonal is {ang(sub(c1, c0)):.1f} deg from the horizontal.  "
                       f"The round is drawn {OVER2:g} deg past the join so its end cut lies inside the diagonal.  "
                       f"What remains is the width difference between R2's field and R1's band at that point: "
                       f"the diagonal is {w_slash(c1[1]):.1f} against the band's {_band_perp(b, t_j):.1f}, so the "
                       f"band stands {abs(mis)/2:.1f} units proud of it on each side where the two overlap.  The "
                       f"round's proportions were chosen to make that difference as small as the shape allows "
                       f"(a taller round moves the tangency down its heavier flank and doubles it); it is the "
                       f"R1-against-R2 counterpart of the R1-against-R4 steps set_bowl records on B, D, P and R, "
                       f"and smaller than any of those.  What it looks like: at 7 px per unit both flanks show a "
                       f"small concave step, one on each edge of the stroke; at 240 px and at the proof size "
                       f"neither is visible.  Removing it would mean either re-solving the round's semi-axes so "
                       f"the band at the tangency equals w_slash exactly -- two constraints on a shape that has "
                       f"to keep its top on 710 and its right extreme on the body -- or taking the diagonal's "
                       f"width from the band instead of from R2's field, which would be an R2 departure.  "
                       f"Neither is worth a step this size, so it stands, recorded."),
        join_to_bar=(f"The diagonal's lower-left corner sits exactly on the bar's inner (upper) left corner "
                     f"({P[0]:.1f}, {P[1]:.1f}), where the bar's R5 left cut ends, so the outline runs from the "
                     f"bar's tip at (0, 0) up that cut and straight on up the diagonal: one corner, no shelf, "
                     f"and the diagonal's flat end buried in the bar."),
        proportion=f"Body {BODY} (R8 medium): the round's right extreme and the bar's tips.",
        round=_round_note(b, (t_j - OVER2, TERM2)), r1=_R1_NOTE,
        spacing=f"{SB_ROUND}/{SB_ROUND}: a round on the right, the bar's R5 tip on the left.",
        deviations="none from R1-R9 beyond the recorded join mismatch."))

# ---- 3 ----------------------------------------------------------------------------
A3_UP, B3_UP = 250.0, 175.0        # the 3's upper round
A3_LO, B3_LO = 281.0, 200.0        # its lower round: wider and taller (R7, the heavier below)
T3_UP, T3_LO = 165.0, 190.0        # the two outer terminals, parametric degrees
T3_WAIST = -105.0                  # where the upper round's band ends at the waist, on the left

def _rounds3():
    up = dict(c=(BODY - A3_UP, TOP - B3_UP), a=A3_UP, b=B3_UP)
    lo = dict(c=(BODY - A3_LO, BOT + B3_LO), a=A3_LO, b=B3_LO)
    t_lo, m_lo = _merge_t(lo, up, 20.0, 180.0)      # the lower round's thin top end, buried in the upper band
    return up, lo, t_lo, m_lo

def build_three():
    up, lo, t_lo, m_lo = _rounds3()
    over = 2*B3_UP + 2*B3_LO - (TOP - BOT)
    arcs = [_arc(up, T3_WAIST, T3_UP), _arc(lo, -(360 - T3_LO), t_lo)]
    return glyph(ord('3'), arcs, sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=(f"Two narrowed rounds, open on the left: the upper {A3_UP:g} x {B3_UP:g} with its top edge "
                      f"on {TOP}, the lower {A3_LO:g} x {B3_LO:g} with its bottom edge on {BOT}, both with their "
                      f"right extreme on the body {BODY} and the lower the larger (R7).  The upper is drawn from "
                      f"t={T3_WAIST:g} to {T3_UP:g} deg, the lower from {T3_LO - 360:g} to {t_lo:.1f}."),
        waist=(f"The waist is the upper round's own bottom, which R1 makes its thick side "
               f"({ROUND_THICK:.1f}, the O's bottom weight): the two ellipses are {over:g} units taller together "
               f"than the {TOP - BOT} they span, so the upper band's underside runs on past the lower round's "
               f"thin top ({ROUND_THIN:.1f}) and swallows it.  The lower round's end is therefore invisible -- "
               f"_merge_t places it at t={t_lo:.1f}, the cut with the deepest clearance inside the upper band, "
               f"{m_lo:.1f} units at its shallowest point.  The ink between the two counters there is "
               f"{ROUND_THICK + ROUND_THIN - over:.1f} units, one stroke; a larger overlap would thin it to nothing and then open an "
               f"eye where the counters cross, a smaller one would leave the lower round's end sticking out."),
        terminals=(f"Three free ends, each cut along the ray from its own round's centre as R5 asks of a partial "
                   f"round: the upper round's at t={T3_UP:g} (upper left) and at t={T3_WAIST:g}, which is the "
                   f"left end of the waist, and the lower round's at t={T3_LO:g} (lower left).  The waist end is "
                   f"a free terminal, not a junction, so it takes the same radial cut as the others."),
        proportion=(f"Body {BODY} (R8 medium): the rounds' right extremes, and the lower terminal placed so its "
                    f"outer corner falls on x=0.  The upper round is {A3_LO - A3_UP:g} narrower and "
                    f"{2*(B3_LO - B3_UP):g} shorter, so the upper bowl reads as the smaller."),
        rounds=dict(upper=_round_note(up, (T3_WAIST, T3_UP)), lower=_round_note(lo, (T3_LO - 360, t_lo))), r1=_R1_NOTE,
        spacing=f"{SB_ROUND}/{SB_ROUND}, round both sides.",
        deviations="none from R1-R9."))

# ---- burying a horizontal's end in a round (set_bowl's wedge, on an ellipse) --------
BURY_IN = 0.5        # how far inside the outer contour a buried end's chord is laid

def _ell_y(bowl, x, side):
    """y of the outer ellipse at x; side +1 upper half, -1 lower."""
    c, a, b = bowl['c'], bowl['a'], bowl['b']
    return c[1] + side * b * math.sqrt(max(0.0, 1 - ((x - c[0])/a)**2))

def _line_counter_x(bowl, p0, p1, n=720):
    """Largest x where the line p0->p1 crosses the counter: the wedge point, where a horizontal's
    inner edge runs into the round's counter (set_bowl's _wedge_x, on R1's offset curve)."""
    u = unit(sub(p1, p0))
    side = lambda s: dot(sub(_off_pt(bowl, s), p0), perp(u))
    best = None
    for i in range(n):
        s0, s1 = 360.0*i/n, 360.0*(i+1)/n
        if side(s0) == 0 or side(s0)*side(s1) < 0:
            lo, hi, g = s0, s1, side(s0)
            for _ in range(60):
                m = (lo+hi)/2
                if g*side(m) <= 0: hi = m
                else: lo, g = m, side(m)
            x = _off_pt(bowl, (lo+hi)/2)[0]
            if best is None or x > best: best = x
    return best

def _bury_end(bar, bowl, T, x1, outer='top'):
    """set_bowl's _bury on an ellipse: reshape the flat right end of a rules.horizontal so it lies
    inside the round's band -- from the inner corner to a point BURY_IN inside the outer contour at
    x1, then a chord back to the contact point T.  Tooling: none of it is ever on the outline."""
    pts = bar.flatten()
    xmax = max(p[0] for p in pts)
    right = [p for p in pts if abs(p[0] - xmax) < 1e-6]
    side = 1 if outer == 'top' else -1
    OR = max(right, key=lambda p: p[1]) if outer == 'top' else min(right, key=lambda p: p[1])
    E = (x1, _ell_y(bowl, x1, side) - side * BURY_IN)
    i = pts.index(OR); n = len(pts)
    before = pts[(i - 1) % n]
    rep = [E, T] if abs(before[0] - xmax) < 1e-6 else [T, E]
    return from_poly(ccw(pts[:i] + rep + pts[i+1:]))

# ---- 5 ----------------------------------------------------------------------------
A5, B5 = 279.0, 215.0        # the 5's bowl
T5 = 165.0                   # its free terminal, parametric degrees
ARC5_END = 92.0              # where its band ends under the bar

def _five_parts():
    """The 5's stem, bar and bowl solved together: the bar's top edge passes through the bowl's top
    point, its underside starts at the stem's foot tip (set_straight's L junction, turned over), and
    its right end runs to the wedge where the underside meets the counter.  Each of those depends on
    the bar's length through R4's taper, so they are solved by fixed point."""
    bowl = dict(c=(BODY - A5, BOT + B5), a=A5, b=B5)
    T = (bowl['c'][0], BOT + 2*B5)
    x_s = w_stem(0)/2
    x1 = bowl['c'][0] + 2*RING_W
    y0 = T[1] - HORIZ_MID
    for _ in range(100):
        x0 = x_s - w_stem(y0)/2
        L = x1 - x0
        y_c = T[1] - w_horizontal(L, (T[0] - x0)/L)/2          # top edge through the bowl's top
        y0 = y_c - w_horizontal(L, 0)/2                        # underside at the stem: the stem's foot
        e1 = (x1, y_c - w_horizontal(L, 1)/2)
        x = _line_counter_x(bowl, (x0, y0), e1)                # wedge: underside meets the counter
        if x is None: break
        x1 = x
    return bowl, T, x_s, x0, y0, y_c, x1

def build_five():
    bowl, T, x_s, x0, y0, y_c, x1 = _five_parts()
    top = arm(x_s - w_stem(CAP)/2, float(BODY), 'top', left='cut', right='cut')
    bar = _bury_end(horizontal(x0, x1, y_c, left='up'), bowl, T, x1, outer='top')
    st = stem(x_s, y0, CAP, bottom='right', top='right')
    arc = _arc(bowl, T5 - 360, ARC5_END)
    cut = _cut_pts(bowl, ARC5_END)
    L = x1 - x0
    inside = all(y_c - w_horizontal(L, (p[0]-x0)/L)/2 - 1e-6 <= p[1] <= _ell_y(bowl, p[0], 1) + 1e-6 for p in cut)
    return glyph(ord('5'), [top, st, bar, arc], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=(f"An R4 cap-line arm (rules.arm) the full body {BODY} with an R5 tip at its right end on "
                      f"{CAP}, an R3 stem (rules.stem) down the left from the cap to y={y0:.1f}, an R4 bar "
                      f"(rules.horizontal, centre-line y={y_c:.1f}) carrying the stem into the bowl, and a "
                      f"narrowed round ({A5:g} x {B5:g}, bottom edge on {BOT}, right extreme on the body) drawn "
                      f"from t={T5:g} deg -- its free terminal at the upper left -- clockwise round the bottom "
                      f"and up to t={ARC5_END:g}, where it is swallowed by the bar."),
        arm=("The arm's left end is the R5 cut set_straight uses at a stem: its tip is the stem's own upper-left "
             "corner on the cap line, so stem and arm share exactly one outline point and the arm alone supplies "
             "the top edge.  The stem's top R5 cut is swallowed under it."),
        stem_to_bar=(f"set_straight's L corner, turned over: the bar's underside starts exactly at the stem's foot "
                     f"tip ({x0:.1f}, {y0:.1f}) and the bar's left end is the R5 cut with its tip there, running "
                     f"up into the stem at {90 - CUT_DEG:.1f} deg; the stem's own R5 foot cut runs the other way, "
                     f"{CUT_DEG:g} deg off the horizontal, and is swallowed by the bar.  So the stem alone supplies "
                     f"the left edge, the bar alone the underside, and they share one point."),
        join=(f"Bar to bowl, the wedge join set_bowl makes at a cap-line arm, turned over: a {HORIZ_MID:g} R4 "
              f"horizontal cannot coincide with an R1 band that is only {_band_perp(bowl, 90):.1f} thick at the "
              f"top of a round, so the bar's top edge is laid through the bowl's top point "
              f"({T[0]:.0f}, {T[1]:.0f}) -- tangent to within the "
              f"{math.degrees(math.atan(HORIZ_TAPER/2)):.2f} deg slope R4's taper gives that edge -- and its "
              f"underside runs on level past the top until it meets the counter in a corner at x={x1:.1f}.  "
              f"Everything of the bar past the contact point is buried inside the band (_bury_end, set_bowl's "
              f"tooling), so the outline runs along the bar's top edge, onto the bowl at the contact point and "
              f"away round the bowl.  The bowl's own end cut at t={ARC5_END:g} lies inside the bar: "
              f"{'checked' if inside else 'NOT INSIDE -- fix'}."),
        proportion=(f"Body {BODY} (R8 medium): the arm's tip and the bowl's extremes.  The bowl is {2*B5:g} tall, "
                    f"{200*B5/(TOP-BOT):.0f}% of the figure, and its left extreme is {x0:.1f} units left of the "
                    f"stem's edge, so the bowl, not the stem, sets the left of the box."),
        round=_round_note(bowl, (T5 - 360, ARC5_END)), r1=_R1_NOTE,
        spacing=(f"{SB_ROUND}/{SB_ROUND}: the extremes are the bowl both sides (R9 by the shape of the extreme).  "
                 f"The stem stands {x0:.1f} units inside the bowl's left extreme, so it is effectively spaced "
                 f"{SB_ROUND + x0:.0f}, close to the {SB_STRAIGHT} a stem asks for, and the figure keeps the "
                 f"{BODY + 2*SB_ROUND} advance the other nine rounds have."),
        deviations="none from R1-R9."))

# ---- 8 ----------------------------------------------------------------------------
A8_UP, B8_UP = 246.0, 175.0        # the 8's upper round
A8_LO, B8_LO = 279.0, 195.0        # its lower round: the wider and taller (R7)

def build_eight():
    up = dict(c=(BODY/2, TOP - B8_UP), a=A8_UP, b=B8_UP)
    lo = dict(c=(BODY/2, BOT + B8_LO), a=A8_LO, b=B8_LO)
    over = 2*B8_UP + 2*B8_LO - (TOP - BOT)
    return glyph(ord('8'), _ring(up['c'], up['a'], up['b']) + _ring(lo['c'], lo['a'], lo['b']),
                 sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=(f"Two complete narrowed rounds on one axis (x={BODY/2:g}): the upper {A8_UP:g} x {B8_UP:g} "
                      f"with its top edge on {TOP}, the lower {A8_LO:g} x {B8_LO:g} with its bottom edge on "
                      f"{BOT} and its extremes on the body {BODY}.  Nothing else: no end cuts anywhere, both "
                      f"rounds closed, the two counters left as they fall."),
        waist=(f"The two ellipses are {over:g} units taller together than the {TOP - BOT} they span, so they "
               f"cross and the union is one shape.  The ink between the two counters at the waist is "
               f"{ROUND_THICK + ROUND_THIN - over:.1f} units -- the upper round's thick bottom ({ROUND_THICK:.1f}) less the lower "
               f"round's thin top ({ROUND_THIN:.1f}) plus the overlap -- so the waist carries a full stroke.  "
               f"More overlap would thin it and then open a third counter where the two counters cross; less "
               f"would fatten it toward a blob."),
        proportion=(f"Body {BODY} (R8 medium), the lower round.  The upper is {A8_LO - A8_UP:g} narrower and "
                    f"{2*(B8_LO - B8_UP):g} shorter, so the lower bowl is the larger both ways (R7), as it is "
                    f"in the 3."),
        rounds=dict(upper=_round_note(up), lower=_round_note(lo)), r1=_R1_NOTE,
        spacing=f"{SB_ROUND}/{SB_ROUND}, round both sides.",
        deviations="none from R1-R9."))

# ---- 6 and 9 ----------------------------------------------------------------------
A69, B69 = BODY/2, 205.0          # the bowl of both figures
A_SP, B_SP = 250.0, 515.0         # the spine: the tall round the bowl's tangent point sits on
T6_TERM, T9_TERM = 45.0, -115.0   # the free terminals, parametric degrees

def _spine_note(spine, bowl, t_merge, term):
    m = min(_margin(p, bowl) for p in _cut_pts(spine, t_merge)[1:])
    return (f"The spine is an arc of a second narrowed round, {A_SP:g} x {B_SP:g}, placed so that its own "
            f"extreme falls exactly on the bowl's -- the two outer ellipses touch there, with the same "
            f"tangent, and because both counters are R1's (the same {RING_W:.2f} inset and the same "
            f"{norm(RING_OFF):.1f} displacement) they touch at that point too.  So the spine's band and the "
            f"bowl's band coincide at the join instead of crossing it: the outline runs off one contour onto "
            f"the other with no step and no kink, and the spine's end cut, taken at the touching point "
            f"(t={t_merge:g}), lies inside the bowl's band, clearing its counter by {m:.1f} units.  The free "
            f"end at t={term:g} is the terminal, cut along the ray from the spine's centre (R5).")

def build_six():
    bowl = dict(c=(A69, BOT + B69), a=A69, b=B69)
    spine = dict(c=(A_SP, bowl['c'][1]), a=A_SP, b=B_SP)          # left extreme on the bowl's, top on TOP
    arc = _arc(spine, T6_TERM, 180.0)
    return glyph(ord('6'), _ring(bowl['c'], bowl['a'], bowl['b']) + [arc], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=(f"A complete narrowed round for the bowl ({2*A69:g} x {2*B69:g}, bottom edge on {BOT}, "
                      f"extremes on the body {BODY}) and, rising out of its left extreme, an arc of a taller "
                      f"narrowed round ({A_SP:g} x {B_SP:g}) whose top edge is the figure's, on {TOP}.  The arc "
                      f"runs from t=180 deg -- the point the two rounds share -- counter-clockwise up and over "
                      f"to its terminal at t={T6_TERM:g} deg "
                      f"({_ell(spine['c'], A_SP, B_SP, T6_TERM)[0]:.0f}, {_ell(spine['c'], A_SP, B_SP, T6_TERM)[1]:.0f})."),
        join=_spine_note(spine, bowl, 180.0, T6_TERM),
        proportion=(f"Body {BODY} (R8 medium), the bowl.  The bowl is {2*B69:g} tall, "
                    f"{200*B69/(TOP-BOT):.0f}% of the figure, and the spine covers the rest; the spine's own "
                    f"width is {2*A_SP:g}, inside the body, so the bowl sets the box."),
        rounds=dict(bowl=_round_note(bowl), spine=_round_note(spine, (T6_TERM, 180.0))), r1=_R1_NOTE,
        spacing=f"{SB_ROUND}/{SB_ROUND}, round both sides.",
        deviations="none from R1-R9."))

def build_nine():
    bowl = dict(c=(A69, TOP - B69), a=A69, b=B69)
    spine = dict(c=(BODY - A_SP, bowl['c'][1]), a=A_SP, b=B_SP)   # right extreme on the bowl's, bottom on BOT
    arc = _arc(spine, T9_TERM, 0.0)
    return glyph(ord('9'), _ring(bowl['c'], bowl['a'], bowl['b']) + [arc], sb=(SB_ROUND, SB_ROUND), notes=dict(
        construction=(f"The 6's two rounds, reflected in the figure's own centre but built the same way up, so "
                      f"the weight still falls at the lower left (R7): a complete narrowed round for the bowl "
                      f"({2*A69:g} x {2*B69:g}, top edge on {TOP}, extremes on the body {BODY}) and an arc of "
                      f"the taller round ({A_SP:g} x {B_SP:g}) whose bottom edge is on {BOT}, running from t=0 "
                      f"-- the point the two rounds share, the bowl's right extreme -- clockwise down and round "
                      f"to its terminal at t={T9_TERM:g} deg "
                      f"({_ell(spine['c'], A_SP, B_SP, T9_TERM)[0]:.0f}, {_ell(spine['c'], A_SP, B_SP, T9_TERM)[1]:.0f})."),
        join=_spine_note(spine, bowl, 0.0, T9_TERM),
        proportion=f"Body {BODY} (R8 medium), the bowl; the tail stays inside it.",
        rounds=dict(bowl=_round_note(bowl), spine=_round_note(spine, (T9_TERM, 0.0))), r1=_R1_NOTE,
        spacing=f"{SB_ROUND}/{SB_ROUND}, round both sides.",
        deviations=("The 9 is not the 6 turned round: R7 fixes the heavy side to the page, so both figures are "
                    "built upright and the 9's bowl and tail each carry their weight at their own lower left.  "
                    "Nothing else departs from R1-R9.")))

GLYPHS = {'zero': build_zero, 'one': build_one, 'two': build_two, 'three': build_three,
          'four': build_four, 'five': build_five, 'six': build_six, 'seven': build_seven,
          'eight': build_eight, 'nine': build_nine,
          'one.tab': build_one_tab}       # unencoded alternate: the 1 set tabular (see build_one's notes)
