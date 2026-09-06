#!/usr/bin/env python3
"""Derive the animation geometry for the AO mark from the Illustrator source.

Reads  font/source/ai_objects.json (key "AO", page 0) and src/components/logo-mark.ts;
writes design/logo-animation/geometry.json and geometry-overlay.svg (site path units,
y-up, i.e. coordinates valid inside Logo.astro's
<g transform="translate(0,1084) scale(0.1,-0.1)"> group).

Needs numpy + svgpathtools. Run from anywhere:
  python design/logo-animation/derive_geometry.py [--ai path/to/ai_objects.json]
"""
import argparse, json, math, re, sys
from pathlib import Path as FsPath
import numpy as np
from svgpathtools import Path, CubicBezier, Line, parse_path

HERE = FsPath(__file__).resolve().parent
ROOT = HERE.parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--ai', default=str(ROOT.parent / 'font' / 'font' / 'source' / 'ai_objects.json'))
ap.add_argument('--logo', default=str(ROOT / 'src' / 'components' / 'logo-mark.ts'),
                help='the site path: logo-mark.ts (LOGO_MARK_D) or an .astro/.svg file with <path d="...">')
args = ap.parse_args()

# ---------------------------------------------------------------- source objects
page = json.load(open(args.ai))['AO'][0]
objs = {o['role']: o for o in page['objects']}
C = lambda p: complex(p[0], p[1])

def seg(item):
    if item[0] == 'c':
        return CubicBezier(C(item[1]), C(item[2]), C(item[3]), C(item[4]))
    return Line(C(item[1]), C(item[2]))

bar_segs = [seg(i) for i in objs['bar']['items']]
sw_segs = [seg(i) for i in objs['white']['items']]
A_v = [C(v) for v in objs['A']['vertices']]  # ltip, lcut, counter, rcut, rtip, apex
L_TIP, L_CUT, COUNTER, R_CUT, R_TIP, APEX = A_v
ring_o = objs['ring']['outer']; ring_i = objs['ring']['inner']

# ---------------------------------------------------------------- similarity transform
# source pt -> site path units, from the two vertex correspondences given in the brief
src1, dst1 = APEX, complex(5916, 10247)
src2, dst2 = R_TIP, complex(8737, 194)
a = (dst2 - dst1) / (src2 - src1)          # complex scale*rotation
b = dst1 - a * src1
S = abs(a); THETA = math.degrees(math.atan2(a.imag, a.real))
T = lambda z: a * z + b                    # complex -> complex
def Tseg(s):
    if isinstance(s, CubicBezier):
        return CubicBezier(*[T(p) for p in (s.start, s.control1, s.control2, s.end)])
    return Line(T(s.start), T(s.end))

bar = [Tseg(s) for s in bar_segs]
sw = [Tseg(s) for s in sw_segs]
V = {k: T(v) for k, v in zip(['ltip', 'lcut', 'counter', 'rcut', 'rtip', 'apex'], A_v)}
RING_O = (T(complex(ring_o[0], ring_o[1])), ring_o[2] * S)
RING_I = (T(complex(ring_i[0], ring_i[1])), ring_i[2] * S)

# ---------------------------------------------------------------- site path + residual
logo = open(args.logo).read()
d_site = (re.findall(r"LOGO_MARK_D\s*=\s*'([^']+)'", logo) or re.findall(r'<path d="([^"]+)"', logo))[0]
site = parse_path(d_site)

def sample_path(p, n):
    L = p.length(); ts = np.linspace(0, 1, n)
    return np.array([p.point(p.ilength(t * L)) if 0 < t < 1 else p.point(t) for t in ts])

def sample_segs(segs, per=40):
    pts = []
    for s in segs:
        pts.extend(s.point(t) for t in np.linspace(0, 1, per, endpoint=False))
    return np.array(pts)

def circle_pts(c, r, n=2000):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return c + r * np.exp(1j * th)

A_outline = [Line(V['ltip'], V['lcut']), Line(V['lcut'], V['counter']), Line(V['counter'], V['rcut']),
             Line(V['rcut'], V['rtip']), Line(V['rtip'], V['apex']), Line(V['apex'], V['ltip'])]
src_pts = np.concatenate([sample_segs(bar, 120), sample_segs(A_outline, 600),
                          circle_pts(*RING_O, 4000), circle_pts(*RING_I, 4000)])
site_pts = np.concatenate([np.array([s.point(t) for t in np.linspace(0, 1, 6, endpoint=False)]) for s in site])

def nearest_dist(P, Q):
    out = np.empty(len(P))
    for i in range(0, len(P), 500):
        blk = P[i:i + 500]
        out[i:i + 500] = np.abs(blk[:, None] - Q[None, :]).min(axis=1)
    return out

res = nearest_dist(site_pts, src_pts)
residual = dict(samples=int(len(site_pts)), mean=float(res.mean()), p95=float(np.percentile(res, 95)),
                max=float(res.max()), unit='site path units (1 unit = 0.1 viewBox unit)',
                note='distance from each site-path sample to the nearest transformed source outline')

# ---------------------------------------------------------------- centre-line helpers
def rev(s):
    return s.reversed()

def arc_samples(segs, n):
    """n points uniformly spaced in arc length along a chain of segments."""
    p = Path(*segs); L = p.length()
    return np.array([p.point(p.ilength(L * t)) if 0 < t < 1 else p.point(t) for t in np.linspace(0, 1, n)])

def paired_centre(outer_chain, inner_chain, n_per=40):
    """Pair corresponding segments by normalised arc length; midpoints + half widths."""
    pts, hw = [], []
    for so, si in zip(outer_chain, inner_chain):
        po = arc_samples([so], n_per); pi = arc_samples([si], n_per)
        pts.append((po + pi) / 2); hw.append(np.abs(po - pi) / 2)
    return np.concatenate(pts), np.concatenate(hw)

def nearest_centre(inner_pts, outer_pts):
    """For every inner point take the nearest outer point; midpoints + half widths."""
    d = np.abs(inner_pts[:, None] - outer_pts[None, :])
    j = d.argmin(axis=1)
    return (inner_pts + outer_pts[j]) / 2, d[np.arange(len(inner_pts)), j] / 2

def dedupe(pts, eps=1e-6):
    keep = [pts[0]]
    for p in pts[1:]:
        if abs(p - keep[-1]) > eps: keep.append(p)
    return np.array(keep)

def cum_len(pts):
    return np.concatenate([[0], np.cumsum(np.abs(np.diff(pts)))])

def resample(pts, step):
    s = cum_len(pts); n = max(2, int(round(s[-1] / step)) + 1)
    u = np.linspace(0, s[-1], n)
    return np.interp(u, s, pts.real) + 1j * np.interp(u, s, pts.imag)

def smooth(pts, k=5):
    if k < 2 or len(pts) < k: return pts
    out = pts.copy(); h = k // 2
    for i in range(h, len(pts) - h):
        out[i] = pts[i - h:i + h + 1].mean()
    return out

# ---- cubic fitting (Schneider): fixed end points, least-squares inner controls, split on error
def fit_cubics(pts, tol=4.0, depth=0):
    pts = dedupe(pts)
    if len(pts) < 2: return []
    p0, p3 = pts[0], pts[-1]
    if len(pts) == 2: return [(p0, p0 + (p3 - p0) / 3, p3 - (p3 - p0) / 3, p3)]
    u = cum_len(pts); u /= u[-1]
    t0 = pts[1] - pts[0]; t0 /= abs(t0); t1 = pts[-2] - pts[-1]; t1 /= abs(t1)
    best = None
    for _ in range(4):  # a few reparameterisation passes
        B1 = 3 * u * (1 - u) ** 2; B2 = 3 * u ** 2 * (1 - u)
        B0 = (1 - u) ** 3; B3 = u ** 3
        A1 = t0 * B1; A2 = t1 * B2
        # solve 2x2 real normal equations for alphas
        c11 = np.sum(np.abs(A1) ** 2); c22 = np.sum(np.abs(A2) ** 2); c12 = np.sum((A1 * np.conj(A2)).real)
        tmp = pts - (B0 * p0 + B1 * p0 + B2 * p3 + B3 * p3)
        x1 = np.sum((A1 * np.conj(tmp)).real); x2 = np.sum((A2 * np.conj(tmp)).real)
        det = c11 * c22 - c12 * c12
        if abs(det) < 1e-12:
            al1 = al2 = abs(p3 - p0) / 3
        else:
            al1 = (x1 * c22 - x2 * c12) / det; al2 = (c11 * x2 - c12 * x1) / det
        seglen = abs(p3 - p0)
        if al1 < 1e-6 * seglen or al2 < 1e-6 * seglen or not np.isfinite(al1) or not np.isfinite(al2):
            al1 = al2 = seglen / 3
        c1 = p0 + t0 * al1; c2 = p3 + t1 * al2
        bez = CubicBezier(p0, c1, c2, p3)
        curve = np.array([bez.point(t) for t in u])
        err = np.abs(curve - pts); i_max = int(err.argmax())
        if best is None or err.max() < best[0]:
            best = (err.max(), bez, i_max)
        if err.max() <= tol: break
        # Newton step on parameters
        for k in range(1, len(u) - 1):
            d1 = bez.derivative(u[k]); d2 = bez.derivative(u[k], n=2); q = bez.point(u[k]) - pts[k]
            den = (d1 * np.conj(d1)).real + (q * np.conj(d2)).real
            if den != 0:
                u[k] = min(max(u[k] - (q * np.conj(d1)).real / den, 0), 1)
        u = np.maximum.accumulate(u)
    e, bez, i_max = best
    if e <= tol or depth > 12 or len(pts) < 6:
        return [(bez.start, bez.control1, bez.control2, bez.end)]
    i_max = min(max(i_max, 2), len(pts) - 3)
    return fit_cubics(pts[:i_max + 1], tol, depth + 1) + fit_cubics(pts[i_max:], tol, depth + 1)

def fmt(z): return f'{z.real:.0f} {z.imag:.0f}'
def cubics_to_d(cubs):
    out = [f'M{fmt(cubs[0][0])}']
    for _, c1, c2, p in cubs: out.append(f'C{fmt(c1)} {fmt(c2)} {fmt(p)}')
    return ' '.join(out)
def poly_to_d(pts, close=False):
    return 'M' + ' L'.join(fmt(p) for p in pts) + (' Z' if close else '')
def segs_to_d(segs):
    out = [f'M{fmt(segs[0].start)}']
    for s in segs:
        out.append(f'C{fmt(s.control1)} {fmt(s.control2)} {fmt(s.end)}' if isinstance(s, CubicBezier) else f'L{fmt(s.end)}')
    return ' '.join(out) + ' Z'

def path_from_cubics(cubs): return Path(*[CubicBezier(*c) for c in cubs])

def covering_halfwidth(outline_pts, centre_pts):
    """max distance from any outline point to the centre polyline (what a round-capped mask needs)."""
    dens = resample(centre_pts, 5.0)
    return float(nearest_dist(outline_pts, dens).max())

def frac_at(pts, target):
    s = cum_len(pts); i = int(np.abs(pts - target).argmin()); return float(s[i] / s[-1])

def first_crossing(pts, p, q):
    """arc-length fraction where polyline pts first crosses segment p-q (None if never)."""
    s = cum_len(pts); d = q - p
    for i in range(len(pts) - 1):
        r = pts[i + 1] - pts[i]; den = (r * np.conj(d)).imag
        if abs(den) < 1e-9: continue
        w = p - pts[i]
        t = (w * np.conj(d)).imag / den; u_ = (w * np.conj(r)).imag / den
        if 0 <= t <= 1 and 0 <= u_ <= 1:
            return float((s[i] + t * abs(r)) / s[-1]), pts[i] + t * r
    return None, None

# ---------------------------------------------------------------- legs
l_mid = (V['ltip'] + V['lcut']) / 2; r_mid = (V['rtip'] + V['rcut']) / 2
leg_L = np.array([l_mid, V['apex']]); leg_R = np.array([V['apex'], r_mid])   # each in the pen's direction
quad_L = [V['apex'], V['ltip'], V['lcut'], V['counter']]
quad_R = [V['apex'], V['counter'], V['rcut'], V['rtip']]

# The two pieces split the A along apex->counter.  Abutting fills are antialiased
# independently, so a hairline of background shows down the apex for the whole animated
# span; the same problem derive_trail.py solves at the swash's two ends with OVERLAP.
# Fix it the same way: grow the LEFT piece LEG_OVERLAP units past the split so the fills
# interpenetrate.  The split edge is offset into the right leg and then clipped back to
# the A's own right outer edge (apex->rtip), so the grown piece still lies inside the A
# and the union of the two pieces is still the A polygon; only the last LEG_OVERLAP/
# sin(20.6 deg) = 170 units below the apex, where the offset edge meets the outline, keep
# a butt joint, and there the A has narrowed to its tip.
LEG_OVERLAP = 60.0
def _cross(a, b): return a.real * b.imag - a.imag * b.real
def _isect(p, d, q, e): return p + d * (_cross(q - p, e) / _cross(d, e))
if LEG_OVERLAP > 0:
    _u = (V['apex'] - V['counter']); _u /= abs(_u)
    _n = _u * -1j                                                   # unit normal to the split
    if ((V['rcut'] - V['counter']) / _n).real < 0: _n = -_n         # point it at the right leg
    _c = V['counter'] + _n * LEG_OVERLAP
    quad_L = [V['apex'], V['ltip'], V['lcut'], _c,
              _isect(_c, _u, V['apex'], V['rtip'] - V['apex'])]     # clipped to the A's edge
def _hw(quad, centre):
    n = len(quad)
    return covering_halfwidth(sample_segs([Line(quad[i], quad[(i + 1) % n]) for i in range(n)], 300), centre)
legL_hw = _hw(quad_L, leg_L)
legR_hw = _hw(quad_R, leg_R)

# ---------------------------------------------------------------- bar centre-line
# outline order: 0 R-hook outer(upper) | 1-4 top run (R->L) | 5-6 L-hook outer | 7 L tip cut |
# 8-9 L-hook inner | 10-13 bottom run (L->R) | 14-15 R-hook inner | 16 R tip cut | 17 R-hook outer(lower)
top_run = bar[1:5]; bottom_run = bar[10:14]
lhook_outer = bar[5:7]; lhook_inner = [rev(bar[9]), rev(bar[8])]
rhook_outer = [rev(bar[0]), rev(bar[17])]; rhook_inner = bar[14:16]
l_tip_mid = (bar[7].start + bar[7].end) / 2; r_tip_mid = (bar[16].start + bar[16].end) / 2
l_end_mid = (bar[4].end + bar[10].start) / 2; r_end_mid = (bar[1].start + bar[13].end) / 2

lh_c, lh_hw = paired_centre(lhook_outer, lhook_inner)           # bar-left-end -> tip
rh_c, rh_hw = paired_centre(rhook_outer, rhook_inner)           # bar-right-end -> tip
top_pts = arc_samples([rev(s) for s in reversed(top_run)], 400)  # L -> R
bot_pts = arc_samples(bottom_run, 400)                           # L -> R
run_c, run_hw = nearest_centre(bot_pts, top_pts)
run_c[0], run_c[-1] = l_end_mid, r_end_mid
bar_centre = np.concatenate([lh_c[::-1], run_c, rh_c])           # L tip -> around hook -> bar -> R tip
bar_centre[0], bar_centre[-1] = l_tip_mid, r_tip_mid
bar_centre = dedupe(bar_centre)
bar_widths = dict(left_hook=float(2 * lh_hw.max()), run_mid=float(2 * run_hw[len(run_hw) // 2]),
                  run_left=float(2 * run_hw[5]), run_right=float(2 * run_hw[-6]), right_hook=float(2 * rh_hw.max()))
bar_outline_pts = sample_segs(bar, 150)
bar_hw = covering_halfwidth(bar_outline_pts, bar_centre)
bar_cubics = fit_cubics(smooth(resample(bar_centre, 20.0), 3), tol=5.0)
bar_fit = path_from_cubics(bar_cubics)
bar_fit_pts = sample_path(bar_fit, 1500)
bar_len = float(bar_fit.length())
def bar_marks():
    m = {}
    m['left_hook_tip'] = 0.0
    m['left_hook_bend'] = frac_at(bar_fit_pts, (bar[5].end + bar[9].start) / 2)
    m['bar_left_end'] = frac_at(bar_fit_pts, l_end_mid)
    f, p = first_crossing(bar_fit_pts, V['apex'], l_mid); m['crosses_left_leg'] = f
    f, p = first_crossing(bar_fit_pts, V['apex'], r_mid); m['crosses_right_leg'] = f
    m['bar_right_end'] = frac_at(bar_fit_pts, r_end_mid)
    m['right_hook_bend'] = frac_at(bar_fit_pts, (bar[0].start + bar[14].end) / 2)
    m['right_hook_tip'] = 1.0
    return m

# The trail is NOT derived here.  It is the Illustrator swash, and design/logo-animation/
# derive_trail.py owns it end to end (outline, centre-line, the join into the bar's hook and
# the marks that time the head); it writes the `trail_from_swash` block of geometry.json,
# which is what LogoAnimated.astro renders.  An earlier coarse fit lived here and disagreed
# with it - half the true band width, marks 0.03 out - so it is gone rather than kept as a
# second answer to the same question.  `sw` is still read above: the overlay draws the swash
# outline, and the A/bar numbers below are what derive_trail.py pins the swash onto.

# ---------------------------------------------------------------- ring numbers
ro_c, ro_r = RING_O; ri_c, ri_r = RING_I
off = ri_c - ro_c
ring = dict(
    outer=dict(cx=ro_c.real, cy=ro_c.imag, r=ro_r),
    inner=dict(cx=ri_c.real, cy=ri_c.imag, r=ri_r),
    counter_offset=dict(dx=off.real, dy=off.imag, length=abs(off), angle_deg=math.degrees(math.atan2(off.imag, off.real))),
    stroke=dict(thick=ro_r - ri_r + abs(off), thin=ro_r - ri_r - abs(off), mean=ro_r - ri_r),
    thin_circle=dict(
        cx=ro_c.real, cy=ro_c.imag,
        r=(ro_r + (ri_r + abs(off))) / 2,
        note='centred on the OUTER circle; this radius keeps a thin stroke inside the ring band all round '
             '(band from the outer centre is [r_inner+offset, r_outer] at the thin side)'),
)
ring['thin_circle']['band_inner_at_thin_side'] = ri_r + abs(off)
ring['thicken'] = dict(
    note='to thicken with the outer edge fixed: r(t) = r_outer - w(t)/2 while w goes thin -> mean; '
         'at w = mean the uniform circle matches the true ring on the outer edge and on the average inner edge',
    r_at_mean_weight=ro_r - (ro_r - ri_r) / 2,
)

# ---------------------------------------------------------------- stroke widths
PT = S  # site units per source point
widths = dict(
    unit='site path units',
    pt=PT,
    leg_mask=dict(covering_halfwidth_L=legL_hw, covering_halfwidth_R=legR_hw,
                  recommended=float(math.ceil(2 * max(legL_hw, legR_hw) * 1.08 / 10) * 10),
                  note='stroke along apex->foot-cut midpoint, round caps; must be >= 2*covering halfwidth'),
    bar_mask=dict(covering_halfwidth=bar_hw, recommended=float(math.ceil(2 * bar_hw * 1.08 / 10) * 10),
                  bar_widths=bar_widths,
                  note='the hooks are wider across the curl than the runs; the recommended value covers the whole outline'),
    trail=dict(recommended=float(round(0.6 * (bar_widths['run_left'] + bar_widths['run_mid']) / 2 / 10) * 10),
               note='0.6 of the bar run weight (the clip measures 0.55-0.62), round caps; '
                    'the weight of the trail="stroke" mode, and only that mode: the default draws the '
                    'swash outline itself. See trail_from_swash in derive_trail.py.'),
    thin_circle=dict(recommended=float(round(ring['stroke']['mean'] / 4 / 10) * 10),
                     note='about a quarter of the ring mean weight'),
    ring_mean=ring['stroke']['mean'],
)

# ---------------------------------------------------------------- output
def pt_obj(z): return dict(x=round(z.real, 1), y=round(z.imag, 1))

geometry = dict(
    units='site path units, y-up: the coordinates inside Logo.astro\'s '
          '<g transform="translate(0,1084) scale(0.1,-0.1)"> group (viewBox "-70 -70 1246 1246"). '
          '1 source pt = %.4f units.' % S,
    transform=dict(
        description='site = a*src + b (complex), i.e. uniform scale S, rotation THETA about origin, then translate',
        scale=S, rotation_deg=THETA, translate=dict(x=b.real, y=b.imag),
        matrix_source_pt_to_site=[a.real, a.imag, -a.imag, a.real, b.real, b.imag],
        anchors=dict(apex=dict(src=pt_obj(APEX), site=pt_obj(dst1)), right_foot_tip=dict(src=pt_obj(R_TIP), site=pt_obj(dst2))),
        residual=residual,
    ),
    A=dict(
        vertices={k: pt_obj(v) for k, v in V.items()},
        left_foot_cut_mid=pt_obj(l_mid), right_foot_cut_mid=pt_obj(r_mid),
        leg_left_centre=dict(d=poly_to_d(leg_L), length=float(abs(leg_L[1] - leg_L[0]))),
        leg_right_centre=dict(d=poly_to_d(leg_R), length=float(abs(leg_R[1] - leg_R[0]))),
        polygon_d=poly_to_d([V[k] for k in ['ltip', 'lcut', 'counter', 'rcut', 'rtip', 'apex']], True),
        left_leg_quad_d=poly_to_d(quad_L, True),
        right_leg_quad_d=poly_to_d(quad_R, True),
        note='leg pieces: the A polygon splits at apex-counter into two quads, one per leg, so each leg\'s mask reveals only its own leg',
    ),
    bar=dict(
        outline_d=segs_to_d(bar),
        centre_d=cubics_to_d(bar_cubics), centre_segments=len(bar_cubics), centre_length=bar_len,
        centre_marks_fraction_of_length=bar_marks(),
        left_hook_tip=pt_obj(l_tip_mid), right_hook_tip=pt_obj(r_tip_mid),
        bar_left_end=pt_obj(l_end_mid), bar_right_end=pt_obj(r_end_mid),
        widths=bar_widths,
        note='runs from the LEFT hook tip, around the hook, left-to-right along the bar, to the RIGHT hook tip; '
             'the first point equals the last point of the trail',
    ),
    ring=ring,
    stroke_widths=widths,
)

# ---------------------------------------------------------------- blocks this script does not own
# geometry.json carries two trail blocks derived elsewhere; keep whatever is already there
# rather than dropping it when this script rewrites the file, and re-stamp each one's note so
# the file itself says which is authoritative:
#   trail_from_swash  the pen trail in use, written by derive_trail.py - re-run that after this
#                     script if the source or the transform changed.
#   trail_from_video  superseded: the clip's trail traced from its frames, before we found the
#                     swash in the Illustrator file. Kept as the record of that pass; nothing
#                     derives it any more. See choreography.md.
NOTES = dict(
    trail_from_swash='AUTHORITATIVE. The pen trail the component renders: written by derive_trail.py from the '
                     'Illustrator swash. Use centre_joined_d (the sweep path / the trail="stroke" line), '
                     'outline_joined_d (the filled swash) and mask (the reveal path and its fractions); '
                     'outline_d / centre_d are the same shape before the join fix, kept for reference.',
    trail_from_video='SUPERSEDED, kept only as the record of an earlier pass. The clip\'s trail traced from its '
                     'video frames and warped onto this geometry, before the swash was found in the Illustrator '
                     'file. The clip was rendered from a different drawing (registration reaches only IoU 0.55, '
                     'all of the residual in the A), so nothing here derives or renders it. See choreography.md.',
)
prev = HERE / 'geometry.json'
old = json.load(open(prev)) if prev.exists() else {}
for key, note in NOTES.items():
    if key in old:
        geometry[key] = old[key]
        geometry[key]['note'] = note
        print('kept', key, 'from the previous', prev.name)

# the overlay draws the authoritative trail, so it too comes from that block
trail_centre_d = old.get('trail_from_swash', {}).get('centre_joined_d')
trail_centre_pts = np.array([[float(v) for v in q.split()]
                             for q in trail_centre_d.lstrip('M').split(' L')]) if trail_centre_d else np.zeros((1, 2))
trail_marks = sorted(set(sum((v if isinstance(v, list) else [v]
                              for v in old.get('trail_from_swash', {}).get('marks', {}).values()
                              if isinstance(v, (int, float, list))), [])))

out = HERE / 'geometry.json'
json.dump(geometry, open(out, 'w'), indent=1)
print('wrote', out)
print('scale %.5f rot %.4f deg  translate (%.2f, %.2f)' % (S, THETA, b.real, b.imag))
print('residual', residual)
print('bar centre: %d cubics, len %.0f; marks %s' % (len(bar_cubics), bar_len, json.dumps(bar_marks(), indent=None)))
print('bar widths', bar_widths)
print('covering hw: legL %.1f legR %.1f bar %.1f' % (legL_hw, legR_hw, bar_hw))
print('ring', json.dumps(ring, indent=None))

# ---------------------------------------------------------------- overlay SVG
W = 1600
svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="-70 -70 1246 1246">')
svg.append('<rect x="-70" y="-70" width="1246" height="1246" fill="#1D2B35"/>')
svg.append('<g transform="translate(0,1084) scale(0.1,-0.1)" fill="none" stroke-linecap="round" stroke-linejoin="round">')
svg.append(f'<path d="{d_site}" fill="#EEE5E9" fill-opacity="0.35" stroke="none"/>')
# source objects transformed: outlines
svg.append(f'<path d="{segs_to_d(bar)}" stroke="#2892D7" stroke-width="12"/>')
svg.append(f'<path d="{geometry["A"]["polygon_d"]}" stroke="#2892D7" stroke-width="12"/>')
svg.append(f'<circle cx="{ro_c.real}" cy="{ro_c.imag}" r="{ro_r}" stroke="#2892D7" stroke-width="12"/>')
svg.append(f'<circle cx="{ri_c.real}" cy="{ri_c.imag}" r="{ri_r}" stroke="#2892D7" stroke-width="12"/>')
svg.append(f'<path d="{segs_to_d(sw)}" stroke="#7fd0ff" stroke-width="8" stroke-dasharray="40 30"/>')
# centre lines
svg.append(f'<path d="{poly_to_d(leg_L)}" stroke="#ffd166" stroke-width="16"/>')
svg.append(f'<path d="{poly_to_d(leg_R)}" stroke="#ffd166" stroke-width="16"/>')
svg.append(f'<path d="{cubics_to_d(bar_cubics)}" stroke="#D16666" stroke-width="16"/>')
if trail_centre_d: svg.append(f'<path d="{trail_centre_d}" stroke="#06d6a0" stroke-width="16"/>')
# thin growth circle
svg.append(f'<circle cx="{ro_c.real}" cy="{ro_c.imag}" r="{ring["thin_circle"]["r"]}" stroke="#ff9f1c" stroke-width="10" stroke-dasharray="60 40"/>')
# key points
for z, col in [(V['apex'], '#fff'), (l_mid, '#fff'), (r_mid, '#fff'), (l_tip_mid, '#fff'), (r_tip_mid, '#fff'),
               (l_end_mid, '#fff'), (r_end_mid, '#fff'), (ro_c, '#ff9f1c'), (ri_c, '#2892D7')]:
    svg.append(f'<circle cx="{z.real}" cy="{z.imag}" r="45" fill="{col}" stroke="none"/>')
# marks along bar and trail
for f in bar_marks().values():
    z = bar_fit.point(bar_fit.ilength(f * bar_len) if 0 < f < 1 else f)
    svg.append(f'<circle cx="{z.real}" cy="{z.imag}" r="30" fill="#D16666" stroke="#fff" stroke-width="8"/>')
for f in trail_marks:
    z = trail_centre_pts[min(int(round(f * (len(trail_centre_pts) - 1))), len(trail_centre_pts) - 1)]
    svg.append(f'<circle cx="{z[0]}" cy="{z[1]}" r="30" fill="#06d6a0" stroke="#fff" stroke-width="8"/>')
svg.append('</g>')
svg.append('<g font-family="sans-serif" font-size="26" fill="#EEE5E9">'
           '<text x="-50" y="-30">grey: Logo.astro path   blue: source ring/bar/A transformed   dashed light blue: swash object</text>'
           '<text x="-50" y="1160">yellow: leg centre-lines   red: bar centre-line   green: trail centre-line (from derive_trail.py)   dashed orange: thin growth circle</text></g>')
svg.append('</svg>')
open(HERE / 'geometry-overlay.svg', 'w').write('\n'.join(svg))
print('wrote', HERE / 'geometry-overlay.svg')
