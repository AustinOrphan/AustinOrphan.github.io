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
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from pen import *
from metrics import *

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
    _, segs_t = arc_segments(ct, r_top, a0, a1)
    for sg in segs_t: out.curve_to(sg[1], sg[2], sg[3])
    for sg in hL.segs: out.segs.append(sg)
    # bottom edge runs left-to-right: clockwise, the short way
    a0, a1 = ang(sub(BL, cb)), ang(sub(BR, cb))
    if a1 > a0: a1 -= 360
    _, segs_b = arc_segments(cb, r_bot, a0, a1)
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
    outer, inner = OBJ['ring']['outer'], OBJ['ring']['inner']          # [cx, cy, r, fit_sd]
    s = (CAP + 2*OVER_ROUND) / (2*outer[2])
    r_out, r_in = outer[2]*s, inner[2]*s
    off = ((inner[0]-outer[0])*s, (inner[1]-outer[1])*s)
    c = (SB_ROUND + r_out, CAP/2)
    contours = [circle_contour(c, r_out, ccw=True), circle_contour(add(c, off), r_in, ccw=False)]
    return dict(cp=ord('O'), adv=round(2*SB_ROUND + 2*r_out), contours=contours,
                notes=dict(scale=s, centre=c, r_out=r_out, r_in=r_in, offset=off, offset_len=norm(off), offset_dir_deg=ang(off),
                           width_thick=r_out-r_in+norm(off), width_thin=r_out-r_in-norm(off), width_mean=r_out-r_in,
                           source_outer=outer[:3], source_inner=inner[:3]))

def build_A(tuck=True, slide=False, name='A', cp=ord('A'), clip_legs=True):
    global O_THIN
    O_THIN = build_O()['notes']['width_thin']
    tipL, cutL, cApex, cutR, tipR, apex = [tuple(v) for v in OBJ['A']['vertices']]
    (bar_src,) = source_contours(OBJ['bar']['items'])   # one closed outline: bar + both hooks
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

GLYPHS = {'O': build_O, 'A': build_A, 'A.open': build_A_open, 'space': build_space}
