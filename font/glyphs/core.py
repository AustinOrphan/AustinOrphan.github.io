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
  4. hooks returned to the legs: in the mark each hook's return stroke ends
     where it meets the ring.  With the ring gone, each hook is slid inward
     along the bar's own arc (a rotation about the bottom edge's circle centre)
     until its return's end face touches its leg's outer edge, and the bar
     between the hooks is rebuilt as arcs of the original radii through the
     moved junctions.  A short tail then carries the return to the leg's
     centre-line so the union is seamless.  The hooks themselves are untouched;
     the eye each encloses with bar and leg is the mark's eye with the leg
     standing in for the ring.  Slides: left 92 units, right 189.
     (tuck=True, slide=False would instead continue each return straight along
     its end tangent; on the right that is a 200-unit hairline, so it is not
     used.)  The verbatim bar is kept as the unencoded alternate 'A.open'.
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

def build_A(tuck=True, slide=True, name='A', cp=ord('A')):
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
        # -- 4. hook tails.  The bar outline's segments follow the source order, so the
        #       end faces are known by index: seg 7 (left) and seg 16 (right).  Each face
        #       is bracketed by the return's outer edge (seg 6 / 15, arriving) and inner
        #       edge (seg 8 / 17, departing).
        def seg_pts(k):
            pts = [bar_f.start] + [sg[-1] for sg in bar_f.segs]
            return pts[k], bar_f.segs[k]
        def tangent_end(k):     # direction of travel at the end of segment k
            p0, sg = seg_pts(k); return unit(sub(sg[-1], sg[2] if sg[0] == 'c' else p0))
        def tangent_start(k):   # direction of travel at the start of segment k
            p0, sg = seg_pts(k); return unit(sub(sg[1] if sg[0] == 'c' else sg[-1], p0))
        legs = {'L': (line_2pt(poly[0], poly[5]), line_2pt(poly[1], poly[2])),
                'R': (line_2pt(poly[4], poly[5]), line_2pt(poly[3], poly[2]))}
        # face / arriving-edge / departing-edge segment indices in the outline.  After a slide the
        # outline is rebuilt as [top arc (n_top segs)] [left hook segs 4..10] [bottom arc] [right hook 13..17,0,1]
        if slid:
            nt, nb = slid['n_top'], slid['n_bottom']
            iL = nt; iR = nt + 7 + nb           # first segment of each hook piece
            idx = {'L': (iL + 3, iL + 2, iL + 4), 'R': (iR + 3, iR + 2, iR + 4)}
        else:
            idx = {'L': (7, 6, 8), 'R': (16, 15, 17)}
        for side in ('L', 'R'):
            face_k, out_k, in_k = idx[side]
            f0, fseg = seg_pts(face_k); f1 = fseg[-1]
            mid = mul(add(f0, f1), 0.5); width = norm(sub(f1, f0))
            d = unit(add(tangent_end(out_k), mul(tangent_start(in_k), -1)))
            outer_l, inner_l = legs[side]
            leg_centre = line(mul(add(outer_l[0], inner_l[0]), 0.5), unit(add(outer_l[1], inner_l[1])))
            n = perp(d); h = width / 2
            # The return is straight where it ends (its end curvature is negligible, see notes),
            # so the tail continues the face's two corners parallel to the end tangent.
            land = isect(line(mid, d), leg_centre); L = norm(sub(land, mid))
            tailc = from_poly([f0, add(f0, mul(d, L)), add(f1, mul(d, L)), f1]).ccw()
            def kappa_end(k):
                p0, sg = seg_pts(k)
                if sg[0] != 'c': return 0.0
                P0, P1, P2, P3 = p0, sg[1], sg[2], sg[3]
                d1 = mul(sub(P3, P2), 3); d2 = mul(add(sub(P3, mul(P2, 2)), P1), 6)
                return (d1[0]*d2[1] - d1[1]*d2[0]) / max(1e-9, norm(d1)**3)
            k_c = kappa_end(out_k); arc_deg = 0.0
            contours.append(tailc)
            tails[side] = dict(from_=mid, to=land, length=norm(sub(land, mid)), direction_deg=ang(d), width=width,
                               end_radius_of_return=(1/k_c if abs(k_c) > 1e-6 else 0.0))
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
    notes = dict(rotated_by_deg=R, lean_deg=lean, scale=s, y_feet_source=y_feet, apex_source=apex,
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
    return build_A(tuck=False, slide=False, name='A.open', cp=-1)

def build_space():
    return dict(cp=32, adv=SPACE_ADV, contours=[], notes={})

GLYPHS = {'O': build_O, 'A': build_A, 'A.open': build_A_open, 'space': build_space}
