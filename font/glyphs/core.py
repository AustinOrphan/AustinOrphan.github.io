"""
The two letters the mark actually contains, O and A, taken from the
Illustrator construction in source/ai_objects.json (see measure/extract_ai.py).

  O   the ring object: an outer circle and an inner circle whose centre is
      displaced toward the upper right.  Both circles are fitted to the source
      path (residual 0.005 pt) and rebuilt as clean four-segment circles.
  A   the six-vertex A polygon united with the crossbar object, whose eighteen
      cubic segments (the bar and both hooks) are carried through unchanged.

A typeface forces three changes to the A, each recorded in the glyph's notes:
  1. stood upright: rotated by -lean about the apex, where lean is the angle
     between the vertical and the bisector of the two outer leg edges.
     Upright, the two feet come within 1.8% of a leg length of level, which is
     how we know the lean is placement inside the ring, not part of the letter.
  2. feet levelled: each foot's cut is slid along its own leg by half the
     residual, so both tips sit on the baseline.
  3. scaled so the feet sit on the baseline and the apex tip at cap + point
     overshoot.  (The O is scaled separately so its outer circle spans the cap
     height plus round overshoot; the mark's A-to-O size ratio is composition.)
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT, 'lib'))
from pen import *
from metrics import *

SRC = json.load(open(os.path.join(FONT, 'source', 'ai_objects.json')))['AO'][0]
OBJ = {o['role']: o for o in SRC['objects']}

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

def build_A():
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
    contours = [from_poly(poly).ccw(), bar.map(fp).ccw()]
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
                 bar_bbox=contours[1].bbox(), bbox=(x0+dx, y0, x1+dx, y1))
    return dict(cp=ord('A'), adv=round(x1 - x0 + 2*SB_ROUND), contours=contours, notes=notes)

def build_space():
    return dict(cp=32, adv=SPACE_ADV, contours=[], notes={})

GLYPHS = {'O': build_O, 'A': build_A, 'space': build_space}
