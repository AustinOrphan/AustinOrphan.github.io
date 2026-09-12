"""
Measure the mark.  Every number the typeface inherits is read off here, from
the path in src/components/Logo.astro, and written to measurements.json.

Coordinate system: the path is drawn inside scale(0.1,-0.1), so path-space is
y-UP, the same as font space.  Nothing here flips anything except the final
display renders.

Counter numbering (see upright.png):  0 outer silhouette, 1 top-left, 2 top-right,
3 between the legs above the bar, 4 right hook's eye, 5 lower-right, 6 between
the legs below the bar, 7 lower-left, 8 left hook's eye.
"""
from pathlib import Path
import json, math, re
import numpy as np
from svgpathtools import parse_path

HERE = str(Path(__file__).resolve().parent)
REPO = str(Path(__file__).resolve().parents[2])
src = open(f"{REPO}/src/components/Logo.astro").read()
d = re.findall(r'class="site-logo-mark"[^>]*><path d="([^"]+)"', src)[0]
subs = parse_path(d).continuous_subpaths()
unit = lambda v: np.asarray(v, float)/np.linalg.norm(v)
deg = lambda v: math.degrees(math.atan2(v[1], v[0]))

def sample(sub, per=5.0):
    P, T = [], []
    for seg in sub:
        m = max(3, int(seg.length()/per))
        for i in range(m):
            t = i/m; p = seg.point(t); dv = seg.derivative(t)
            if abs(dv) == 0: continue
            P.append((p.real, p.imag)); dv /= abs(dv); T.append((dv.real, dv.imag))
    return np.array(P), np.array(T)
S = [sample(s) for s in subs]
P0, T0 = S[0]
BIG = [1, 2, 3, 5, 6, 7]                     # counters whose outer arcs are the ring's inner edge

def fit_circle(P):
    x, y = P[:,0], P[:,1]; A = np.c_[2*x, 2*y, np.ones(len(x))]
    c, *_ = np.linalg.lstsq(A, x*x+y*y, rcond=None)
    return float(c[0]), float(c[1]), float(math.sqrt(c[2]+c[0]**2+c[1]**2))
def fitline(Q):
    c = Q.mean(0); _,_,vt = np.linalg.svd(Q-c); return c, unit(vt[0])
def isect(l1, l2):
    (c1, v1), (c2, v2) = [(np.array(c), np.array(v)) for c, v in (l1, l2)]
    t = np.linalg.solve(np.array([v1, -v2]).T, c2-c1); return c1+t[0]*v1
def arc_pts(P, T, cx, cy, rlo, rhi, tol=0.10):
    r = np.hypot(P[:,0]-cx, P[:,1]-cy); rd = np.c_[(P[:,0]-cx)/r, (P[:,1]-cy)/r]
    return P[(np.abs((T*rd).sum(1)) < tol) & (r > rlo) & (r < rhi)]

R = {}
# ------------------------------------------------------------------ outer ring
cx, cy = P0.mean(0)
for _ in range(3):
    oa = arc_pts(P0, T0, cx, cy, 3600, 5200); cx, cy, ro = fit_circle(oa)
res = np.hypot(oa[:,0]-cx, oa[:,1]-cy) - ro
R['outer'] = dict(cx=cx, cy=cy, r=ro, residual_sd=float(res.std()), n=len(oa))
print(f"  OUTER ring: circle centre ({cx:.0f},{cy:.0f}) r {ro:.0f}   residual sd {res.std():.1f} over {len(oa)} pts  -> a true circle")

# ------------------------------------------------------------------ inner ring
ia = np.vstack([arc_pts(*S[i], cx, cy, 3300, 4200) for i in BIG])
icx, icy, ri = fit_circle(ia)
ires = np.hypot(ia[:,0]-icx, ia[:,1]-icy) - ri
off = math.hypot(icx-cx, icy-cy); off_dir = deg((icx-cx, icy-cy))
R['inner'] = dict(cx=icx, cy=icy, r=ri, residual_sd=float(ires.std()), n=len(ia), offset=off, offset_dir_deg=off_dir)
print(f"  INNER ring: circle centre ({icx:.0f},{icy:.0f}) r {ri:.0f}   residual sd {ires.std():.1f} over {len(ia)} pts")
print(f"              centre offset {off:.0f} toward {off_dir:.0f}deg  -> ring is {ro-ri-off:.0f} thin at {off_dir:.0f}deg, {ro-ri+off:.0f} thick at {off_dir+180:.0f}deg")
for i in BIG:
    a = arc_pts(*S[i], cx, cy, 3300, 4200); rr = np.hypot(a[:,0]-cx, a[:,1]-cy)
    b = np.degrees(np.arctan2(a[:,1]-cy, a[:,0]-cx))
    print(f"              counter {i}: arc bearings {b.min():5.0f}..{b.max():5.0f}deg  ring width {ro-rr.max():.0f}..{ro-rr.min():.0f}")

# ------------------------------------------------------------------ spike tips
r0 = np.hypot(P0[:,0]-cx, P0[:,1]-cy); spk = P0[r0 > ro+150]
bear = np.degrees(np.arctan2(spk[:,1]-cy, spk[:,0]-cx)) % 360
o = np.argsort(bear); bs = bear[o]; cuts = [0]+[i+1 for i in range(len(bs)-1) if bs[i+1]-bs[i] > 12]+[len(bs)]
tips, tip_pts = {}, {}
for i in range(len(cuts)-1):
    Q = spk[o[cuts[i]:cuts[i+1]]]; rq = np.hypot(Q[:,0]-cx, Q[:,1]-cy); tip = Q[rq.argmax()]
    b = math.degrees(math.atan2(tip[1]-cy, tip[0]-cx)) % 360
    nm = 'apex' if 60 < b < 120 else 'bar_R' if (b < 45 or b > 315) else 'bar_L' if 150 < b < 210 else 'foot_L' if 210 <= b < 260 else 'foot_R'
    tips[nm] = tip.tolist(); tip_pts[nm] = Q
R['tips'] = tips
print("  tips: " + "  ".join(f"{k} ({v[0]:.0f},{v[1]:.0f})" for k, v in tips.items()))

# ------------------------------------------------------------------ A strokes
def edge_pts(ids, seed, tol, rmax):
    P = np.vstack([S[i][0] for i in ids]); T = np.vstack([S[i][1] for i in ids])
    a = np.degrees(np.arctan2(T[:,1], T[:,0])) % 180
    # inside the INNER circle (measured from its own, offset centre), with margin
    keep = (np.abs(((a-seed+90) % 180)-90) < tol) & (np.hypot(P[:,0]-icx, P[:,1]-icy) < rmax)
    return P[keep]
SIDES = {'leg_L': ([1,7], [3,6], 63, 5), 'leg_R': ([3,6], [2,5], 105, 5), 'bar': ([1,3,2], [7,6,5], 10, 6)}
strokes = {}
for name, (sa, sb, seed, tol) in SIDES.items():
    E1, E2 = edge_pts(sa, seed, tol, ri-120), edge_pts(sb, seed, tol, ri-120)
    (c1, v1), (c2, v2) = fitline(E1), fitline(E2)
    ref = np.array([1.0, 0.0]) if name == 'bar' else np.array([0.0, 1.0])
    if v1@ref < 0: v1 = -v1
    if v2@ref < 0: v2 = -v2
    vv = unit(v1+v2); nn = np.array([-vv[1], vv[0]]); centre = (c1+c2)/2
    t1, t2 = (E1-centre)@vv, (E2-centre)@vv
    prof = []
    for lo in np.arange(max(t1.min(), t2.min()), min(t1.max(), t2.max()), 250):
        s1 = (t1 >= lo) & (t1 < lo+250); s2 = (t2 >= lo) & (t2 < lo+250)
        if s1.sum() > 3 and s2.sum() > 3:
            prof.append((round(float(lo+125)), round(float(abs(((E1[s1]-centre)@nn).mean()-((E2[s2]-centre)@nn).mean())))))
    # linear taper fit: width = w0 + k * station
    st = np.array([p[0] for p in prof]); wd = np.array([p[1] for p in prof])
    k, w0 = np.polyfit(st, wd, 1)
    strokes[name] = dict(angle=deg(vv), edge_angles=[deg(v1), deg(v2)], centre=centre.tolist(), dir=vv.tolist(),
                         width_at_centre=float(w0), taper_per_1000=float(k*1000), width_profile=prof,
                         edges=[[c1.tolist(), v1.tolist()], [c2.tolist(), v2.tolist()]], n=[len(E1), len(E2)])
    print(f"  {name:6s} axis {deg(vv):7.2f}deg  edges {deg(v1):7.2f}/{deg(v2):7.2f}  width {w0:.0f} at centre, {k*1000:+.0f} per 1000 along  [{len(E1)}+{len(E2)} pts]")
    print(f"         " + " ".join(f"{t}:{w}" for t, w in prof))
R['strokes'] = strokes
L = {k: (v['centre'], v['dir']) for k, v in strokes.items()}
apex = isect(L['leg_L'], L['leg_R']); bL = isect(L['bar'], L['leg_L']); bR = isect(L['bar'], L['leg_R'])
axis = unit(np.array(L['leg_L'][1]) + np.array(L['leg_R'][1])); lean = deg(axis)-90
apex_angle = strokes['leg_R']['angle'] - strokes['leg_L']['angle']
R['A'] = dict(apex_centreline=apex.tolist(), bar_junctions=[bL.tolist(), bR.tolist()], lean_deg=float(lean), apex_angle_deg=float(apex_angle),
              bar_angle_deg=strokes['bar']['angle'], bar_angle_in_A_frame_deg=strokes['bar']['angle']-lean)
print(f"  A: centre-line apex ({apex[0]:.0f},{apex[1]:.0f})  lean {lean:+.2f}deg  apex angle {apex_angle:.2f}deg  bar {strokes['bar']['angle']:+.2f}deg absolute, {strokes['bar']['angle']-lean:+.2f}deg in the A's frame")
# bar height along the axis, from the ring's bottom (the only baseline the mark has) and from the feet
feet_mid = (np.array(tips['foot_L'])+np.array(tips['foot_R']))/2
bar_mid = (bL+bR)/2
h_feet = (apex-feet_mid)@axis; hb_feet = (bar_mid-feet_mid)@axis
print(f"  bar sits {100*hb_feet/h_feet:.1f}% of the way from feet-tips to apex (axis-projected)")
print(f"  bar centre y {bar_mid[1]:.0f} vs ring centre y {cy:.0f}: {bar_mid[1]-cy:+.0f}  ({100*(bar_mid[1]-(cy-ro))/(2*ro):.1f}% of the ring's height)")
R['A']['bar_frac_of_feet_to_apex'] = float(hb_feet/h_feet); R['A']['bar_frac_of_ring_height'] = float((bar_mid[1]-(cy-ro))/(2*ro))

# ------------------------------------------------------------------ terminals
def local_dirs(Q, T, tip, radius):
    m = np.hypot(Q[:,0]-tip[0], Q[:,1]-tip[1]) < radius
    return Q[m], T[m]
term = {}
# apex: outer edges near the tip
Qa, Ta = local_dirs(P0, T0, tips['apex'], 1400)
aa = np.degrees(np.arctan2(Ta[:,1], Ta[:,0])) % 180
eL = Qa[np.abs(aa-strokes['leg_L']['angle']) < 4]; eR = Qa[np.abs(aa-strokes['leg_R']['angle']) < 4]
(cL, vL), (cR, vR) = fitline(eL), fitline(eR)
tip_fit = isect((cL, vL), (cR, vR))
counter_apex = S[3][0][S[3][0][:,1].argmax()]
term['apex'] = dict(tip=tips['apex'], outer_edges_meet=tip_fit.tolist(), counter_apex=counter_apex.tolist(),
                    tip_above_ring=float(tips['apex'][1]-(cy+ro)), outer_edge_angles=[deg(vL), deg(vR)])
print(f"  APEX: tip ({tips['apex'][0]:.0f},{tips['apex'][1]:.0f}), outer edges meet at ({tip_fit[0]:.0f},{tip_fit[1]:.0f}); counter apex ({counter_apex[0]:.0f},{counter_apex[1]:.0f}); tip is {tips['apex'][1]-(cy+ro):.0f} above the ring")
# feet: the cut facet is the edge run near the tip that is NOT parallel to the leg
for nm, leg in (('foot_L', 'leg_L'), ('foot_R', 'leg_R')):
    Q, T = local_dirs(P0, T0, tips[nm], 1000)
    a = np.degrees(np.arctan2(T[:,1], T[:,0])) % 180
    facet = Q[np.abs(((a-strokes[leg]['angle']+90) % 180)-90) > 12]
    cf, vf = fitline(facet)
    if vf[0] < 0: vf = -vf
    v = np.array(strokes[leg]['dir'])
    # where the leg's centre-line meets the ring's outer edge -> how far the foot runs past it
    c0 = np.array(strokes[leg]['centre']); 
    tt = [t for t in np.roots([1, 2*((c0-[cx,cy])@v), (c0-[cx,cy])@(c0-[cx,cy])-ro*ro]) if np.isreal(t)]
    exit_pt = c0 + min(tt, key=lambda t: t.real).real*v
    run = float((np.array(tips[nm])-exit_pt)@(-v))
    term[nm] = dict(tip=tips[nm], cut_angle_deg=deg(vf), cut_angle_in_A_frame_deg=deg(vf)-lean, cut_len=float(np.ptp(facet@vf)),
                    ring_exit=exit_pt.tolist(), run_past_ring=run, width_at_exit=float(strokes[leg]['width_at_centre']+strokes[leg]['taper_per_1000']/1000*((exit_pt-c0)@v)))
    print(f"  {nm}: cut {deg(vf):+.1f}deg absolute ({deg(vf)-lean:+.1f} in A frame), cut length {np.ptp(facet@vf):.0f}; leg leaves ring at ({exit_pt[0]:.0f},{exit_pt[1]:.0f}) and runs {run:.0f} further to the tip")
# hooks: everything outside the ring around each bar end
for nm, eye in (('bar_L', 8), ('bar_R', 4)):
    tip = np.array(tips[nm]); Q = tip_pts[nm]
    v = np.array(strokes['bar']['dir']); n = np.array([-v[1], v[0]]); c0 = np.array(strokes['bar']['centre'])
    sgn = -1 if nm == 'bar_L' else 1
    tt = [t.real for t in np.roots([1, 2*((c0-[cx,cy])@v), (c0-[cx,cy])@(c0-[cx,cy])-ro*ro]) if np.isreal(t)]
    exit_pt = c0 + (min(tt) if sgn < 0 else max(tt))*v
    along = (Q-exit_pt)@(v*sgn); across = (Q-c0)@n
    eyeP = S[eye][0]; eb = eyeP.min(0), eyeP.max(0)
    term[nm] = dict(tip=tip.tolist(), ring_exit=exit_pt.tolist(), run_past_ring=float(along.max()),
                    droop_of_tip_below_bar_axis=float(-((tip-c0)@n)), lobe_extent_across=[float(across.min()), float(across.max())],
                    eye_bbox=[eb[0].tolist(), eb[1].tolist()], eye_area=float(abs(subs[eye].area())))
    print(f"  {nm}: leaves ring at ({exit_pt[0]:.0f},{exit_pt[1]:.0f}), runs {along.max():.0f} past it; tip sits {-((tip-c0)@n):.0f} below the bar's axis;"
          f" lobe spans {across.min():.0f}..{across.max():.0f} across the axis (bar is ~{strokes['bar']['width_at_centre']:.0f}); eye {eb[1][0]-eb[0][0]:.0f}x{eb[1][1]-eb[0][1]:.0f}")
R['terminals'] = term
R['bbox'] = [float(P0[:,0].min()), float(P0[:,1].min()), float(P0[:,0].max()), float(P0[:,1].max())]
json.dump(R, open(f"{HERE}/measurements.json", "w"), indent=1)

# ------------------------------------------------------------------ overlay
def render(fname, x0, y0, x1, y1, W=1000):
    sc = W/(x1-x0); H = int((y1-y0)*sc); X = lambda x: (x-x0)*sc; Y = lambda y: H-(y-y0)*sc
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#1D2B35"/>',
         f'<g transform="translate({X(0)},{Y(0)}) scale({sc},{-sc})"><path d="{d}" fill="#EEE5E9" fill-opacity="0.25" stroke="#EEE5E9" stroke-width="{max(6, 4/sc)}"/></g>']
    for (ecx, ecy, er), col in (((cx, cy, ro), '#2892D7'), ((icx, icy, ri), '#2892D7')):
        s.append(f'<circle cx="{X(ecx)}" cy="{Y(ecy)}" r="{er*sc}" fill="none" stroke="{col}" stroke-width="1.4" stroke-dasharray="6 4"/>')
        s.append(f'<circle cx="{X(ecx)}" cy="{Y(ecy)}" r="3" fill="{col}"/>')
    for k, st in strokes.items():
        for (c, v), col in ((st['edges'][0], '#D16666'), (st['edges'][1], '#D16666'), ((st['centre'], st['dir']), '#f3c969')):
            c, v = np.array(c), np.array(v)*9000
            s.append(f'<line x1="{X(c[0]-v[0])}" y1="{Y(c[1]-v[1])}" x2="{X(c[0]+v[0])}" y2="{Y(c[1]+v[1])}" stroke="{col}" stroke-width="1.2" stroke-dasharray="6 4"/>')
    for k, t in tips.items():
        s.append(f'<circle cx="{X(t[0])}" cy="{Y(t[1])}" r="4" fill="#2892D7"/>')
    for gx in range(int(x0//500)*500, int(x1)+1, 500):
        s.append(f'<line x1="{X(gx)}" y1="0" x2="{X(gx)}" y2="{H}" stroke="#fff" stroke-opacity="0.10"/><text x="{X(gx)+2}" y="11" fill="#9ab" font-size="10" font-family="monospace">{gx}</text>')
    for gy in range(int(y0//500)*500, int(y1)+1, 500):
        s.append(f'<line x1="0" y1="{Y(gy)}" x2="{W}" y2="{Y(gy)}" stroke="#fff" stroke-opacity="0.10"/><text x="2" y="{Y(gy)-2}" fill="#9ab" font-size="10" font-family="monospace">{gy}</text>')
    s.append('</svg>'); open(f"{HERE}/{fname}.svg", "w").write("\n".join(s))
render('overlay', -200, -200, 11000, 10600)
print("  wrote measurements.json, overlay.svg")
