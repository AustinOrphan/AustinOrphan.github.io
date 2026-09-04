"""The bar is an arc.  Fit both edges as circles; test the legs the same way."""
from pathlib import Path
import json, math, re, numpy as np
from svgpathtools import parse_path
HERE = str(Path(__file__).resolve().parent)
M = json.load(open(f"{HERE}/measurements.json"))
src = open(f"{Path(__file__).resolve().parents[2]}/src/components/Logo.astro").read()
d = re.findall(r'class="site-logo-mark"[^>]*><path d="([^"]+)"', src)[0]
subs = parse_path(d).continuous_subpaths()
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
icx, icy, ri = M['inner']['cx'], M['inner']['cy'], M['inner']['r']
def fit_circle(P):
    x, y = P[:,0], P[:,1]; A = np.c_[2*x, 2*y, np.ones(len(x))]
    c, *_ = np.linalg.lstsq(A, x*x+y*y, rcond=None); cx, cy, r = c[0], c[1], math.sqrt(c[2]+c[0]**2+c[1]**2)
    return cx, cy, r, np.hypot(x-cx, y-cy)-r
def fit_line(P):
    c = P.mean(0); _,_,vt = np.linalg.svd(P-c); v = vt[0]; n = np.array([-v[1], v[0]]); return c, v, (P-c)@n
def pts(ids, lo, hi):
    P = np.vstack([S[i][0] for i in ids]); T = np.vstack([S[i][1] for i in ids])
    a = np.degrees(np.arctan2(T[:,1], T[:,0])) % 180
    keep = (a > lo) & (a < hi) & (np.hypot(P[:,0]-icx, P[:,1]-icy) < ri-120)
    return P[keep]

out = {}
# bottom edge first (clean), then the top edge selected as "one bar-width above the bottom arc"
Eb = pts([7,6,5], 0, 30); bx, by, br, rb = fit_circle(Eb)
Et_all = pts([1,3,2], 0, 30); dt = np.hypot(Et_all[:,0]-bx, Et_all[:,1]-by) - br
Et = Et_all[(dt > 350) & (dt < 900)]; tx, ty, tr, rt = fit_circle(Et)
print(f"  bar bottom arc: centre ({bx:.0f},{by:.0f}) r {br:.0f}  sd {rb.std():.1f} max {np.abs(rb).max():.0f}  [{len(Eb)} pts]")
print(f"  bar top    arc: centre ({tx:.0f},{ty:.0f}) r {tr:.0f}  sd {rt.std():.1f} max {np.abs(rt).max():.0f}  [{len(Et)} of {len(Et_all)} pts]")
# width along the bar = distance between the arcs, measured radially from the bottom arc's centre
for x in (2000, 3500, 5000, 6500, 8000, 9500):
    # point on the bottom arc at this x
    yb = by + math.sqrt(br*br-(x-bx)**2); a = math.atan2(yb-by, x-bx)
    # top arc along the same ray from the bottom centre
    p = np.array([bx, by]); v = np.array([math.cos(a), math.sin(a)]); f = p-np.array([tx, ty])
    B = 2*(f@v); C = f@f-tr*tr; t = (-B+math.sqrt(B*B-4*C))/2
    print(f"     x={x}: width {t-br:.0f}", end="")
print()
chord = (Eb[:,0].max()-Eb[:,0].min()); print(f"  bottom arc: sagitta over the visible {chord:.0f} chord = {chord**2/(8*br):.0f} units; tangent sweeps {math.degrees(math.asin((Eb[:,0].min()-bx)/br)):.1f}..{math.degrees(math.asin((Eb[:,0].max()-bx)/br)):.1f} from the centre")
out['bar_arcs'] = dict(bottom=[bx, by, br], top=[tx, ty, tr], bottom_sd=float(rb.std()), top_sd=float(rt.std()))

# legs: line vs circle
for name, ids, lo, hi in (('leg_L outer', [1,7], 58, 69), ('leg_L inner', [3,6], 58, 69), ('leg_R inner', [3,6], 100, 111), ('leg_R outer', [2,5], 100, 111)):
    E = pts(ids, lo, hi); c, v, rl = fit_line(E); cx, cy, r, rc = fit_circle(E)
    print(f"  {name}: line sd {rl.std():.1f} max {np.abs(rl).max():.0f}   circle r {r:.0f} sd {rc.std():.1f}   -> {'straight' if rl.std() < 8 else 'curved'}  [{len(E)} pts]")
    out[name.replace(' ', '_')] = dict(line_sd=float(rl.std()), circle_r=float(r), circle_sd=float(rc.std()))
M['bar_arcs'] = out['bar_arcs']; M['leg_straightness'] = {k: v for k, v in out.items() if k.startswith('leg')}
json.dump(M, open(f"{HERE}/measurements.json", "w"), indent=1)
print("  measurements.json updated with bar_arcs")
