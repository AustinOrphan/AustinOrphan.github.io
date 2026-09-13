"""
The two letters the mark actually contains, O and A, taken from the
Illustrator construction in source/ai_objects.json (see measure/extract_ai.py).

  O   the ring object: an outer circle and an inner circle whose centre is
      displaced toward the upper right.  Both circles are fitted to the source
      path (residual 0.005 pt) and rebuilt as clean four-segment circles.
  A   the six-vertex A polygon united with the crossbar object, whose eighteen
      cubic segments (the bar and both hooks) are carried through unchanged
      except as described in step 4.

A typeface forces four changes to the A, each recorded in the glyph's notes:
  1. stood upright: rotated by -lean about the apex, where lean is the angle
     between the vertical and the bisector of the two outer leg edges.
     Upright, the two feet come within 1.8% of a leg length of level, which is
     how we know the lean is placement inside the ring, not part of the letter.
  2. feet levelled: each foot's cut is slid along its own leg by half the
     residual, so both tips sit on the baseline.
  3. scaled so the feet sit on the baseline and the apex tip at cap + point
     overshoot.  (The O is scaled separately so its outer circle spans the cap
     height plus round overshoot; the mark's A-to-O size ratio is composition.)
  4. the ring's back half: the crossbar is the front half of a planetary ring,
     an elliptical annulus (measure/extract_ai.py fits it: 103 x 22.6 pt,
     tilted 14 degrees, centred within 2.6 pt of the O's centre; the bar's edges
     and the hooks' curls sit on it to a few tenths of a point).  The hooks are
     the ring's ends and each return stroke is the start of the back half,
     which in the mark disappears behind the O.  With no planet, the back half
     is continued from each face along the ring's centre ellipse until it
     passes behind the nearer leg, thinning from the face width to the face's
     thinnest stroke (the O's thin side) where it meets the leg, as the mark's
     own returns thin toward the planet.  The bar and hooks are verbatim.
     The bar without tails is kept as the unencoded alternate 'A.open'.
"""
import copy, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from pen import *
from metrics import *
import rules   # for RING_W / RING_OFF, so the O follows the weight and contrast knobs

SRC = json.load(open(os.path.join(FONT, 'source', 'ai_objects.json')))['AO'][0]
OBJ = {o['role']: o for o in SRC['objects']}


def _fit_circle(pts):
    n = len(pts); sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
    sxx = sum(p[0]*p[0] for p in pts); syy = sum(p[1]*p[1] for p in pts); sxy = sum(p[0]*p[1] for p in pts)
    sxxx = sum(p[0]**3 for p in pts); syyy = sum(p[1]**3 for p in pts); sxyy = sum(p[0]*p[1]*p[1] for p in pts); sxxy = sum(p[0]*p[0]*p[1] for p in pts)
    # least squares for x^2+y^2 + D x + E y + F = 0
    A = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, n]]; b = [-(sxxx+sxyy), -(sxxy+syyy), -(sxx+syy)]
    # solve 3x3 by Cramer's rule
    def det3(m): return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0]) + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
    D = det3(A)
    sol = []
    for i in range(3):
        M = [row[:] for row in A]
        for r in range(3): M[r][i] = b[r]
        sol.append(det3(M)/D)
    cx, cy = -sol[0]/2, -sol[1]/2; r = math.sqrt(cx*cx + cy*cy - sol[2])
    return (cx, cy), r

def _slide_hooks(bar_f, poly):
    """Option 'slide': cut the bar outline into top edge, bottom edge and two hook pieces
    (segment indices follow the source order), rotate each hook piece about the bottom
    edge's arc centre until its return's end face touches its leg's outer edge, then
    rebuild the two long edges as arcs of their original radii through the moved junctions."""
    pts = [bar_f.start] + [sg[-1] for sg in bar_f.segs]; segs = bar_f.segs
    def piece(a, b):            # segments a..b inclusive (wrapping), as a Contour
        idx = list(range(a, b+1)) if a <= b else list(range(a, len(segs))) + list(range(0, b+1))
        c = Contour(pts[idx[0]])
        for k in idx: c.segs.append(segs[k])
        return c
    top, bottom = piece(2, 3), piece(11, 12)
    c_top, r_top = _fit_circle(top.flatten(2.0)); c_bot, r_bot = _fit_circle(bottom.flatten(2.0))
    legs = {'L': (line_2pt(poly[0], poly[5]), line_2pt(poly[1], poly[2])),
            'R': (line_2pt(poly[4], poly[5]), line_2pt(poly[3], poly[2]))}
    hooks, moved = {}, {}
    for side, (a, b, face_k) in (('L', (4, 10, 7)), ('R', (13, 1, 16))):
        hk = piece(a, b)
        face_i = (face_k - a) % len(segs)                   # index of the face segment inside the piece
        hpts = [hk.start] + [sg[-1] for sg in hk.segs]
        face_mid0 = mul(add(hpts[face_i], hpts[face_i+1]), 0.5)
        outer_l = legs[side][0]; nrm = perp(outer_l[1])
        def dist_after(phi):
            q = add(rot(sub(face_mid0, c_bot), phi), c_bot); return dot(sub(q, outer_l[0]), nrm)
        # signed distance changes sign as the face crosses the leg's outer edge; bisection over the rotation
        lo, hi = 0.0, (1.0 if side == 'R' else -1.0) * 12.0
        d_lo, d_hi = dist_after(lo), dist_after(hi)
        if (d_lo > 0) == (d_hi > 0): raise RuntimeError(f'hook {side}: cannot reach the leg within 12 degrees')
        for _ in range(60):
            m = (lo + hi) / 2
            if (dist_after(m) > 0) == (d_lo > 0): lo = m
            else: hi = m
        phi = (lo + hi) / 2
        hooks[side] = hk.map(lambda p: add(rot(sub(p, c_bot), phi), c_bot))
        moved[side] = dict(rotated_deg=phi, along_arc=abs(math.radians(phi)) * r_bot)
    # rebuild: top arc TR' -> TL' with radius r_top, bottom arc BL' -> BR' with radius r_bot
    # Fixed pieces, for the reason pen.arc_segments gives: the default ceil(span / 90) rule
    # made the bar's lower edge four cubics in some masters and three in others -- the span
    # sits either side of 270 degrees across the axis box -- and varLib drops a glyph whose
    # masters disagree about point counts.  Four is the most that rule asks of these arcs.
    BAR_SEGS = 4

    def arc_through(p, q, r, near):
        # centre of the circle of radius r through p and q, nearest to `near`
        m = mul(add(p, q), 0.5); dpq = norm(sub(q, p)); h = math.sqrt(max(0.0, r*r - (dpq/2)**2)); nn = perp(unit(sub(q, p)))
        c = min((add(m, mul(nn, h)), sub(m, mul(nn, h))), key=lambda c: norm(sub(c, near)))
        return c
    hL, hR = hooks['L'], hooks['R']
    TL, BL = hL.start, hL.end(); BR, TR = hR.start, hR.end()
    ct = arc_through(TR, TL, r_top, c_top); cb = arc_through(BL, BR, r_bot, c_bot)
    out = Contour(TR)
    # top edge runs right-to-left over the top of its circle: counter-clockwise, the short way
    a0, a1 = ang(sub(TR, ct)), ang(sub(TL, ct))
    if a1 < a0: a1 += 360
    _, segs_t = arc_segments(ct, r_top, a0, a1, BAR_SEGS)
    for sg in segs_t: out.curve_to(sg[1], sg[2], sg[3])
    for sg in hL.segs: out.segs.append(sg)
    # bottom edge runs left-to-right: clockwise, the short way
    a0, a1 = ang(sub(BL, cb)), ang(sub(BR, cb))
    if a1 > a0: a1 -= 360
    _, segs_b = arc_segments(cb, r_bot, a0, a1, BAR_SEGS)
    for sg in segs_b: out.curve_to(sg[1], sg[2], sg[3])
    for sg in hR.segs: out.segs.append(sg)
    # the new outline keeps the source's segment indices for the hooks shifted by the arc segment counts;
    # record where the faces are so the tail code can find them
    out = out.ccw()
    return out, dict(moved=moved, top_radius=r_top, bottom_radius=r_bot, n_top=len(segs_t), n_bottom=len(segs_b))

def _ring_tails(vertices, width_end):
    """The bar is the front half of a planetary ring (an elliptical annulus fitted in
    measure/extract_ai.py, stored as OBJ['bar']['ring']).  Each hook's return stroke is the
    start of the ring's back half.  With no planet to hide behind, the back half is continued
    from each return's end face along the ring's centre ellipse until it passes behind the
    nearer leg, thinning from the face width to `width_end` (the face's thinnest stroke, the
    O's thin side, in source units) where it meets the leg's outer edge; the last stretch to
    the leg's centre-line is buried.  Returns {side: {'poly': [...source points...], 'notes': {...}}}."""
    R = OBJ['bar']['ring']; C = tuple(R['centre']); axv = tuple(R['axis']); nv = perp(axv)
    a_m, b_m = (R['a_outer'] + R['a_inner']) / 2, (R['b_outer'] + R['b_inner']) / 2      # the centre ellipse of the band
    back = -R['front_sign']
    def E(t): return add(C, add(mul(axv, a_m*math.cos(t)), mul(nv, b_m*math.sin(t))))
    def uv(p): d = sub(p, C); return (dot(d, axv), dot(d, nv))
    (barc,) = source_contours(OBJ['bar']['items']); pts = [barc.start] + [sg[-1] for sg in barc.segs]
    tipL, cutL, cApex, cutR, tipR, apex = [tuple(v) for v in vertices]
    legs = {'L': (line_2pt(tipL, apex), line_2pt(cutL, cApex)), 'R': (line_2pt(tipR, apex), line_2pt(cutR, cApex))}
    out = {}
    for side, face_k in (('L', 7), ('R', 16)):
        f0, f1 = pts[face_k], pts[face_k + 1]; mid = mul(add(f0, f1), 0.5); width = norm(sub(f1, f0))
        # start on the centre ellipse at the face's position along the axis, on the back side
        u0, v0 = uv(mid); t0 = math.atan2(back * math.sqrt(max(0.0, 1 - (u0/a_m)**2)), u0 / a_m)
        # walk toward the ring's middle on the back side, i.e. toward t = +90 (back above the
        # axis) or -90 degrees (back below), by the shorter way round
        t_target = back * math.pi / 2
        direction = 1.0 if ((t_target - t0 + math.pi) % (2*math.pi) - math.pi) > 0 else -1.0
        outer_l, inner_l = legs[side]; legc = line(mul(add(outer_l[0], inner_l[0]), 0.5), unit(add(outer_l[1], inner_l[1])))
        n_out, n_c = perp(outer_l[1]), perp(legc[1])
        s_out0 = dot(sub(mid, outer_l[0]), n_out) > 0; s_c0 = dot(sub(mid, legc[0]), n_c) > 0
        # sample the ellipse finely; blend the start from the actual face midpoint onto the ellipse
        centre_pts, k_cross = [mid], None
        off0 = sub(mid, E(t0)); dt = math.radians(0.25); blend_len = 8.0; dist = 0.0
        for i in range(1, 4000):
            q = E(t0 + direction*dt*i); dist += norm(sub(q, E(t0 + direction*dt*(i-1))))
            w = max(0.0, 1 - dist/blend_len); q = add(q, mul(off0, w))
            centre_pts.append(q)
            if k_cross is None and (dot(sub(q, outer_l[0]), n_out) > 0) != s_out0: k_cross = i
            if (dot(sub(q, legc[0]), n_c) > 0) != s_c0: break
        if k_cross is None: raise RuntimeError(f'ring tail {side}: the back arc never reached the leg')
        # offsets: start at the face corners' offsets, taper to width_end at the leg's outer edge
        d0 = unit(sub(centre_pts[1], centre_pts[0])); h0, h1 = dot(sub(f0, mid), perp(d0)), dot(sub(f1, mid), perp(d0))
        s_face = max(abs(dot(sub(f0, mid), d0)), abs(dot(sub(f1, mid), d0)))
        left, right, run = [], [], [0.0]
        for i in range(1, len(centre_pts)): run.append(run[-1] + norm(sub(centre_pts[i], centre_pts[i-1])))
        s_cross = run[k_cross]
        for i, q in enumerate(centre_pts):
            tv = unit(sub(centre_pts[min(i+1, len(centre_pts)-1)], centre_pts[max(i-1, 0)])); nn = perp(tv)
            if run[i] >= s_cross or run[i] <= s_face: k = 1.0 if run[i] <= s_face else width_end / width
            else: k = 1.0 - (1.0 - width_end / width) * ((run[i] - s_face) / max(1e-9, s_cross - s_face))
            left.append(add(q, mul(nn, h0*k))); right.append(add(q, mul(nn, h1*k)))
        i0 = next(i for i, r_ in enumerate(run) if r_ > s_face)
        # the back edge sits a hair inside the return, so the union has no shared edge to seam on
        back_in = mul(d0, -0.15)
        poly = [add(f0, back_in)] + left[i0:] + right[i0:][::-1] + [add(f1, back_in)]
        out[side] = dict(poly=poly, notes=dict(face_width=width, width_at_leg=width_end, arc_to_leg=s_cross, start_offset_from_ellipse=norm(off0),
                                                 ring=dict(a=a_m, b=b_m, tilt_deg=R['tilt_deg'])))
    return out

def build_O():
    """The mark's ring.

    Its counter is DERIVED, not transcribed. The traced ring is exactly two circles -- outer
    360.000 and inner 326.813, which is 360 - RING_W, displaced by exactly RING_OFF -- so
    r_in = r_out - RING_W reproduces the source to the last bit at the mark's own numbers and,
    unlike the traced value, follows the WEIGHT and PUSH knobs. Transcribing it left the O
    frozen while every other glyph moved: on the weight axis the whole face thickened around
    an O that did not.

    The outer radius stays the traced one. It is the letter's silhouette and the face's widest
    round; nothing about weight should move it.
    """
    outer, inner = OBJ['ring']['outer'], OBJ['ring']['inner']          # [cx, cy, r, fit_sd]
    s = (CAP + 2*OVER_ROUND) / (2*outer[2])
    r_out = outer[2]*s
    r_in  = r_out - rules.RING_W
    off   = tuple(rules.RING_OFF)
    c = (SB_ROUND + r_out, CAP/2)
    contours = [circle_contour(c, r_out, ccw=True), circle_contour(add(c, off), r_in, ccw=False)]
    return dict(cp=ord('O'), adv=round(2*SB_ROUND + 2*r_out), contours=contours,
                notes=dict(scale=s, centre=c, r_out=r_out, r_in=r_in, offset=off, offset_len=norm(off), offset_dir_deg=ang(off),
                           width_thick=r_out-r_in+norm(off), width_thin=r_out-r_in-norm(off), width_mean=r_out-r_in,
                           source_outer=outer[:3], source_inner=inner[:3],
                           traced_r_in=inner[2]*s,
                           traced_offset=((inner[0]-outer[0])*s, (inner[1]-outer[1])*s)))

# ---- the ring's band, derived rather than transcribed -------------------------------
#
# The A's crossbar is the front half of the mark's ring, and the ring is an annulus between two
# concentric coaxial ellipses (SPEC 2.2: outer 51.46 x 11.32, inner 45.41 x 4.98, both centred
# at 50.04, 51.52 and tilted 14.09 deg, fitting the drawn edges to 0.10 and 0.13 pt).
#
# Transcribing that band left the bar frozen, exactly as transcribing the counter left the O
# frozen. It is worse for the bar than it was for the O, because R4b makes every interior
# horizontal in the face a chord of this ring and those chords DO follow the knobs: at
# WEIGHT 1.45 an H's bar is 62.2 while the A's own bar stayed 48.4, so the source of the rule
# was lighter than everything derived from it.
#
# So the inner ellipse is derived. The OUTER stays traced -- it is the silhouette, the same
# reasoning build_O gives for keeping the outer radius -- and the inner is inset from it by the
# traced amount scaled by R4's own join weight. That law is not a new one: HORIZ_JOIN is
# RING_W + RING_OFF[1], which is what every chord in the face already scales by, so the A's bar
# and the chords that borrow from it now move together. At the mark's own knobs the factor is
# exactly 1 and the derived band reproduces the traced ellipse.
#
# A.open keeps the traced outline with its hooks: it is a transcription of the mark rather than
# a stroke of a letter, so it is not the knobs' to move.
_RING_FIT   = OBJ['bar']['ring']
_JOIN_AT_11 = 47.22547582144795         # RING_W + RING_OFF[1] at WEIGHT 1, PUSH 1

# The ellipse pair is a FIT to the drawn edges, good to 0.10 and 0.13 pt mean, and it runs a
# little thicker than the outline actually drawn. Where the fit and the drawing disagree the
# drawing wins -- the drawing is the source and the fit is a reading of it -- so the inset
# carries one calibration, solved so the derived band's MEAN over the visible span equals the
# drawn band's mean. Solved on the mean rather than at a point because the drawing wanders
# around its own ring: matched at one place it was 1.15 units out at another, matched on the
# mean it is never more than 0.84 out, which is inside the fit residual SPEC 2.2 records.
_BAR_CAL = 0.972933104

def _band_k():
    """R4's join weight against its value at the mark's own knobs."""
    return (rules.RING_W + rules.RING_OFF[1]) / _JOIN_AT_11

def _ring_ellipses(band_k=None):
    """Outer (traced) and inner (derived) semi-axes of the ring, in source points.

    band_k defaults to this instance's; _bar_ranges passes 1.0, the axis origin, where
    _band_k() is 1 by its own definition (R4's join weight over its value at the mark)."""
    R = _RING_FIT
    ao, bo, ai, bi = R['a_outer'], R['b_outer'], R['a_inner'], R['b_inner']
    k = (_band_k() if band_k is None else band_k) * _BAR_CAL
    return (ao, bo), (ao - (ao - ai) * k, bo - (bo - bi) * k)

_BAR_ARC = (18.0, 152.0)   # theta range drawn, generous: the legs clip it back

def _bar_samples(band_k=None):
    """The bar's two edges as dense samples, with a numeric unit tangent along each."""
    R = _RING_FIT
    C, tl = tuple(R['centre']), math.radians(R['tilt_deg'])
    ct, st = math.cos(tl), math.sin(tl)
    def E(a, b, th):
        x, y = a * math.cos(th), b * math.sin(th)
        return (C[0] + x * ct - y * st, C[1] + x * st + y * ct)
    (ao, bo), (ai, bi) = _ring_ellipses(band_k)
    t0, t1 = (math.radians(t) for t in _BAR_ARC)
    N = 120
    up = [E(ao, bo, t0 + (t1 - t0) * i / N) for i in range(N + 1)]
    lo = [E(ai, bi, t0 + (t1 - t0) * i / N) for i in range(N + 1)]
    tg = lambda P: [unit(sub(P[min(i + 1, len(P) - 1)], P[max(i - 1, 0)])) for i in range(len(P))]
    return up, lo, tg


_BAR_RANGES = []
def _bar_ranges():
    """Where the bar's cubics start and end, taken ONCE at the axis origin and held.

    Sample i is a fixed angle on the ellipse at every instance, so it is the same place on the
    bar in every master; the fit's own choice of cut is not, because it is an argmax over
    residuals that move with the band.  See pen.fit_ranges."""
    if not _BAR_RANGES:
        up, lo, tg = _bar_samples(1.0)
        _BAR_RANGES.append(fit_ranges(up, tg(up), 13))
        _BAR_RANGES.append(fit_ranges(lo[::-1], tg(lo[::-1]), 11))
    return _BAR_RANGES


def _derived_bar():
    """The bar as a piece of the ring's annulus, in SOURCE coordinates, so it goes through
    build_A's own lean/scale untouched.  Upper edge on the outer ellipse, lower on the derived
    inner one; the ends run well past the legs and are cut by clip_legs like the traced bar."""
    up, lo, tg = _bar_samples()
    # Fixed piece counts, not a tolerance: the outer edge is knob-independent and always came out
    # at 13, but the inner one is derived from the ring's band and ran 6 to 11 across the masters,
    # which is why the A would not interpolate.  13 and 11 are those maxima.  See pen.fit_cubics.
    # Fixed KNOTS as well, for the reason set out there: a fixed count makes the masters agree on
    # how many control points there are and not on what each one means, and the inner edge moves
    # with the band, so its cuts would slide along the curve from master to master.
    rgu, rgl = _bar_ranges()
    su, _eu = fit_cubics(up, tg(up), ranges=rgu)
    sl, _el = fit_cubics(lo[::-1], tg(lo[::-1]), ranges=rgl)
    k = Contour(up[0])
    for sg in su: k.curve_to(*sg)
    k.line_to(lo[-1])
    for sg in sl: k.curve_to(*sg)
    return k.ccw()


def _derive_counter(poly):
    """The A's counter, from R2 rather than from the trace.

    The three counter points were transcribed, so the counter never moved: at WEIGHT 1.45 the
    A wore Light legs beside a heavy V, the same freeze the O had before build_O derived its
    counter.  They are solved now -- the two outer edges inset by R2's own widths, which is
    what every other diagonal in the face already does.

    Both inner edges come out STRAIGHT, so there is nothing to fit: R2's width is linear in y
    and the offset direction is fixed along a straight leg, so a varying inset still traces a
    line.  The counter apex is where the two meet; each cut point is where an inner edge meets
    that foot's own cut, whose direction stays the traced one (R5 sets it, not R2).
    """
    tipL, cutL, cApex, cutR, tipR, apex = poly
    mid_x = (tipL[0] + tipR[0]) / 2
    def inner(tip, wf):
        u = unit(sub(apex, tip)); n = perp(u)
        s = 1.0 if (mid_x - tip[0]) * n[0] > 0 else -1.0
        def at(y):
            t = (y - tip[1]) / (apex[1] - tip[1])
            return add(add(tip, mul(sub(apex, tip), t)), mul(n, s * wf(y)))
        return line_2pt(at(0.0), at(CAP))
    Li, Ri = inner(tipL, rules.w_slash), inner(tipR, rules.w_backslash)
    return [tipL,
            isect(Li, line_2pt(tipL, cutL)),
            isect(Li, Ri),
            isect(Ri, line_2pt(tipR, cutR)),
            tipR, apex]


def build_A(tuck=True, slide=False, name='A', cp=ord('A'), clip_legs=True):
    global O_THIN
    O_THIN = build_O()['notes']['width_thin']
    tipL, cutL, cApex, cutR, tipR, apex = [tuple(v) for v in OBJ['A']['vertices']]
    (bar_src,) = source_contours(OBJ['bar']['items'])   # one closed outline: bar + both hooks
    if clip_legs:
        bar_src = _derived_bar()    # the encoded A's bar follows the knobs; A.open stays traced
    # -- 1. lean: bisector of the outer edges vs the vertical
    bis = unit(add(unit(sub(apex, tipL)), unit(sub(apex, tipR))))
    lean = ang(bis) - 90.0
    R = -lean
    xp = lambda p: add(rot(sub(p, apex), R), apex)
    tipL, cutL, cApex, cutR, tipR = map(xp, (tipL, cutL, cApex, cutR, tipR))
    bar = bar_src.map(xp)
    # -- 2. level the feet along their own legs
    y_feet = (tipL[1] + tipR[1]) / 2
    residual_pt = tipL[1] - tipR[1]
    def relevel(tip, cut, leg_out, leg_in):
        new_tip = (line_x_at_y(leg_out, y_feet), y_feet)
        new_cut = isect(leg_in, line(new_tip, unit(sub(cut, tip))))
        return new_tip, new_cut
    tipL, cutL = relevel(tipL, cutL, line_2pt(tipL, apex), line_2pt(cutL, cApex))
    tipR, cutR = relevel(tipR, cutR, line_2pt(tipR, apex), line_2pt(cutR, cApex))
    # -- 3. scale + place
    s = (CAP + OVER_POINT) / (apex[1] - y_feet)
    fp = lambda p: ((p[0] - apex[0]) * s, (p[1] - y_feet) * s)
    poly = [fp(p) for p in (tipL, cutL, cApex, cutR, tipR, apex)]
    traced_counter = poly[1:4]
    poly = _derive_counter(poly)
    bar_f = bar.map(fp).ccw()
    slid = {}
    if slide:
        bar_f, slid = _slide_hooks(bar_f, poly)
    contours = [from_poly(poly).ccw(), bar_f]
    tails = {}
    if tuck:
        for side, poly_src in _ring_tails(OBJ['A']['vertices'], width_end=O_THIN / s).items():
            contours.append(from_poly([fp(xp(p)) for p in poly_src['poly']]).ccw())
            tails[side] = poly_src['notes']
    clipped = {}
    if clip_legs:
        # The ring runs 105 units past each leg, which made the A 847 wide against 638 for
        # its own width class and left it colliding with whatever it stood next to.  Clipping
        # the ring on the legs' own OUTER EDGES is the natural cut: the ring is meant to pass
        # BEHIND the letter, so the legs are exactly what should hide it, and the cut faces
        # come out parallel to the legs.  What is left of the ring inside the legs is the
        # crossbar, still carrying the ring's tilt.  The full ring is kept as 'A.open'.
        mid = ((poly[0][0] + poly[4][0] + poly[5][0]) / 3,
               (poly[0][1] + poly[4][1] + poly[5][1]) / 3)   # inside the legs' wedge
        L = (poly[5], poly[0])                            # apex -> tipL, the left outer edge
        Rr = (poly[5], poly[4])                           # apex -> tipR
        keep, out = [contours[0]], 0
        for c in contours[1:]:
            k = clip_half(c, L[0], L[1], mid)
            k = clip_half(k, Rr[0], Rr[1], mid) if k is not None else None
            if k is None: out += 1
            else: keep.append(k)
        contours = keep
        clipped = dict(dropped_contours=out,
                       cut_on=[[list(L[0]), list(L[1])], [list(Rr[0]), list(Rr[1])]])
    x0, y0, x1, y1 = bbox([c.flatten() for c in contours])
    dx = SB_ROUND - x0
    contours = [c.map(lambda p: (p[0] + dx, p[1])) for c in contours]
    poly = [(p[0] + dx, p[1]) for p in poly]
    tipL_f, cutL_f, cApex_f, cutR_f, tipR_f, apex_f = poly
    # -- for the record: widths, angles
    def width(outer_a, outer_b, inner_pt):
        l = line_2pt(outer_a, outer_b); return abs(dot(sub(inner_pt, l[0]), perp(l[1])))
    legL = (width(tipL_f, apex_f, cutL_f), width(tipL_f, apex_f, cApex_f))
    legR = (width(tipR_f, apex_f, cutR_f), width(tipR_f, apex_f, cApex_f))
    notes = dict(clipped_to_legs=clipped, rotated_by_deg=R, lean_deg=lean, scale=s, y_feet_source=y_feet, apex_source=apex,
                 foot_level_residual_font=residual_pt*s, x_shift=dx,
                 vertices=dict(tipL=tipL_f, cutL=cutL_f, counter_apex=cApex_f, cutR=cutR_f, tipR=tipR_f, apex=apex_f),
                 leg_L_width_foot_apex=legL, leg_R_width_foot_apex=legR,
                 leg_angles=(ang(sub(apex_f, tipL_f)), ang(sub(apex_f, tipR_f))),
                 apex_angle=ang(sub(apex_f, tipR_f)) - ang(sub(apex_f, tipL_f)),
                 cut_angles=(ang(sub(cutL_f, tipL_f)), ang(sub(tipR_f, cutR_f))),
                 bar_bbox=contours[1].bbox(), bbox=(x0+dx, y0, x1+dx, y1),
                 tucked=tuck, slid=slid, tails={k: {kk: (tuple(round(c, 1) for c in vv) if isinstance(vv, tuple) else (round(vv, 2) if isinstance(vv, float) else vv)) for kk, vv in v.items()} for k, v in tails.items()})
    return dict(cp=cp, adv=round(x1 - x0 + 2*SB_ROUND), contours=contours, notes=notes)

def build_A_open():
    """The bar and hooks verbatim, hooks ending in space where the ring was.  Unencoded alternate."""
    return build_A(tuck=False, slide=False, name='A.open', cp=-1, clip_legs=False)

def build_space():
    return dict(cp=32, adv=SPACE_ADV, contours=[], notes={})


# ---- R4b: the ring the rest of the face borrows --------------------------------------
#
# The A's crossbar IS the mark's ring, clipped on the legs. So the ring's gesture can be read
# straight off it: the two cut faces clip_legs leaves are its ends, and the line between their
# midpoints is the chord the ring draws through this letter.
#
# Under R4b every INTERIOR horizontal in the face -- one lying on no metric line -- is a chord
# of that same ring. What they share is the RISE, not the angle: one angle is not one gesture,
# because an H bar spans 1.6x an E arm and the same tilt would give them different lifts. One
# rise is. So tilt(L) = min(RING_TILT, atan(RISE / L)): a chord shorter than the A's own bar
# takes the ring's angle verbatim, a longer one relaxes until its rise matches.
#
# The A itself does NOT move. Dropping its bar onto MID_Y was considered -- it would put the
# mark on the line E F H K X Y are built on -- but the A is the mark, and the rest of the face
# borrows from it rather than the other way round. ORPHAN_RING_DROP=1 tries the other reading.
#
# The drop is not a translation of the ring's gesture, so it does change these numbers: the bar
# is an arc cut on the legs' outer edges, which converge upward, so lowering it cuts a wider
# span. Undropped the ring gives RISE 90.77 and TILT 19.87; dropped, 100.09 and 19.93.
#
# CROSSOVER is where the two halves of the rule meet, and it equals the A's own span BY
# CONSTRUCTION, not by coincidence: it is RISE/tan(RING_TILT), and both are measured off the
# A's bar. It is worth stating plainly because it looks like a discovered fact and is not one.
RING      = os.environ.get('ORPHAN_RING', '1') not in ('0', 'false', 'off')
RING_DROP = os.environ.get('ORPHAN_RING_DROP', '0') not in ('0', 'false', 'off')

MID_LINE = CAP / 2 + rules.HORIZ_MID / 4       # 361.81, the face's optical middle

_BAR_SRC = copy.deepcopy(OBJ['bar'])

def _drop_bar(d):
    """Shift the SOURCE bar so that, once build_A stands the A upright, the bar has dropped d
    straight down. Everything else about the A -- legs, clip, tails, advance -- is build_A's."""
    n = build_A.__wrapped__ if hasattr(build_A, '__wrapped__') else None
    b = copy.deepcopy(_BAR_SRC)
    lean = _A_LEAN[0]
    v = rot((0.0, -d / _A_SCALE[0]), lean)
    sh = lambda p: (p[0] + v[0], p[1] + v[1])
    b['items'] = [[it[0]] + [list(sh(p)) for p in it[1:]] for it in b['items']]
    if 'ring' in b:
        b['ring'] = dict(b['ring']); b['ring']['centre'] = list(sh(b['ring']['centre']))
    OBJ['bar'] = b

def bar_faces(A):
    """Midpoints of the A's two cut faces -- the straight edges clip_legs leaves, each parallel
    to the leg it was cut on. Left first."""
    legs = A['notes']['leg_angles']
    bar = A['contours'][1]
    pts = [bar.start] + [sg[-1] for sg in bar.segs]
    edges = [(pts[i], sg[-1], sg[0]) for i, sg in enumerate(bar.segs)] + [(pts[-1], pts[0], 'l')]
    faces = [mul(add(p0, p1), 0.5) for p0, p1, kind in edges
             if kind == 'l' and min(abs(ang(sub(p1, p0)) % 180 - legs[0]),
                                    abs(ang(sub(p1, p0)) % 180 - legs[1])) < 1.0]
    return sorted(faces, key=lambda p: p[0])

_A0 = build_A()
_A_LEAN, _A_SCALE = [_A0['notes']['lean_deg']], [_A0['notes']['scale']]
ARC_R = 308.0 * _A_SCALE[0]        # SPEC 2.2: the bar's lower edge is an arc of about 308 pt

A_DROP = 0.0
if RING_DROP:
    for _ in range(8):
        _drop_bar(A_DROP)
        _lo, _hi = bar_faces(build_A())
        A_DROP += (_lo[1] + _hi[1]) / 2 - MID_LINE
    _drop_bar(A_DROP)

_lo, _hi = bar_faces(build_A())
RISE      = _hi[1] - _lo[1]                                    # 100.09
RING_TILT = ang(sub(_hi, _lo))                                 # 19.93 deg
CROSSOVER = RISE / math.tan(math.radians(RING_TILT))           # 276.1 -- the A's own span

GLYPHS = {'O': build_O, 'A': build_A, 'A.open': build_A_open, 'space': build_space}
