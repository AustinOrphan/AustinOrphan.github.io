"""
Read the mark's construction straight out of the Illustrator files.

AO.ai page 1 (index 0) holds the mark as separate filled objects: a white
shape, the ring, the crossbar with its hooks, and a six-vertex A polygon.
Page 2 is the united export the site's SVG came from.  favicon.ai has the same
three black objects in the favicon colour.  This writes every object's segments
(y-up, in points) to source/ai_objects.json and fits the ring's two circles.
"""
from pathlib import Path
import json, math
import numpy as np
import pymupdf

HERE = Path(__file__).resolve().parent; SRC = HERE.parent / 'source'

def read(fn):
    doc = pymupdf.open(str(fn)); pages = []
    for page in doc:
        H = page.rect.height; objs = []
        for d in page.get_drawings():
            items = []
            for it in d['items']:
                if it[0] == 'l':   items.append(['l', [it[1].x, H-it[1].y], [it[2].x, H-it[2].y]])
                elif it[0] == 'c': items.append(['c'] + [[p.x, H-p.y] for p in it[1:5]])
            objs.append(dict(fill=d.get('fill'), items=items))
        pages.append(dict(w=page.rect.width, h=H, objects=objs))
    return pages

def flatten(obj, per=0.25):
    subs, cur, last = [], [], None
    for it in obj['items']:
        p0, p1 = it[1], it[-1]
        if last is None or math.dist(last, p0) > 1e-6:
            if cur: subs.append(cur)
            cur = []
        if it[0] == 'l':
            n = max(2, int(math.dist(p0, p1)/per)); cur += [(p0[0]+(p1[0]-p0[0])*k/n, p0[1]+(p1[1]-p0[1])*k/n) for k in range(n)]
        else:
            P0, P1, P2, P3 = it[1:5]; n = max(3, int((math.dist(P0,P1)+math.dist(P1,P2)+math.dist(P2,P3))/per))
            for k in range(n):
                t = k/n; m = 1-t
                cur.append((m**3*P0[0]+3*m*m*t*P1[0]+3*m*t*t*P2[0]+t**3*P3[0], m**3*P0[1]+3*m*m*t*P1[1]+3*m*t*t*P2[1]+t**3*P3[1]))
        last = p1
    if cur: subs.append(cur)
    return subs

def fit_circle(P):
    P = np.array(P); x, y = P[:,0], P[:,1]; A = np.c_[2*x, 2*y, np.ones(len(x))]
    c, *_ = np.linalg.lstsq(A, x*x+y*y, rcond=None); r = math.sqrt(c[2]+c[0]**2+c[1]**2)
    return [float(c[0]), float(c[1]), float(r), float((np.hypot(x-c[0], y-c[1])-r).std())]

out = {'AO': read(SRC/'AO.ai'), 'favicon': read(SRC/'favicon.ai')}
# identify the construction objects on AO page 1 by shape
pg = out['AO'][0]
for i, o in enumerate(pg['objects']):
    subs = flatten(o)
    if len(o['items']) == 6 and all(it[0] == 'l' for it in o['items']):
        o['role'] = 'A'; o['vertices'] = [it[1] for it in o['items']]
    elif len(subs) == 2:
        circles = sorted([fit_circle(s) for s in subs], key=lambda c: -c[2])
        o['role'] = 'ring'; o['outer'] = circles[0]; o['inner'] = circles[1]
    elif o['fill'] == [1.0, 1.0, 1.0] or o['fill'] == (1.0, 1.0, 1.0):
        o['role'] = 'white'
    else:
        o['role'] = 'bar'
    print(f"  AO page 1 object {i}: {o['role']:5s}  {len(o['items'])} segments  fill {o['fill']}")
ring = next(o for o in pg['objects'] if o['role'] == 'ring'); A = next(o for o in pg['objects'] if o['role'] == 'A')
print(f"  ring outer centre ({ring['outer'][0]:.4f},{ring['outer'][1]:.4f}) r {ring['outer'][2]:.4f}  fit sd {ring['outer'][3]:.4f}")
print(f"  ring inner centre ({ring['inner'][0]:.4f},{ring['inner'][1]:.4f}) r {ring['inner'][2]:.4f}  fit sd {ring['inner'][3]:.4f}")
off = (ring['inner'][0]-ring['outer'][0], ring['inner'][1]-ring['outer'][1])
print(f"  counter offset {math.hypot(*off):.4f} pt toward {math.degrees(math.atan2(off[1], off[0])):.2f} deg = {100*math.hypot(*off)/ring['outer'][2]:.2f}% of the outer radius")
print(f"  A vertices: " + " ".join(f"({x:.3f},{y:.3f})" for x, y in A['vertices']))
# ---- the bar's hooks: each is a band between two concentric ellipses.  The outer curve is
#      fitted freely; the inner curve, too short to constrain a free fit, is fitted with the
#      outer's centre and rotation and its own axes.  Segment indices follow the source order.
bar = next(o for o in pg['objects'] if o['role'] == 'bar')
segs = bar['items']; pts = [tuple(segs[0][1])] + [tuple(it[-1]) for it in segs]
def cubic_pts(it, n=120):
    if it[0] == 'l': return [tuple(it[1]), tuple(it[2])]
    P0, P1, P2, P3 = [np.array(q) for q in it[1:5]]
    return [tuple((1-t)**3*P0 + 3*(1-t)**2*t*P1 + 3*(1-t)*t*t*P2 + t**3*P3) for t in np.linspace(0, 1, n)]
def piece_pts(idx): return [q for k in idx for q in cubic_pts(segs[k])]
def fit_ellipse_free(P):
    P = np.array(P); x, y = P[:,0], P[:,1]; mx, my, sc = x.mean(), y.mean(), max(x.std(), y.std())
    x, y = (x-mx)/sc, (y-my)/sc
    D = np.c_[x*x, x*y, y*y, x, y, np.ones(len(x))]; Sm = D.T @ D
    C = np.zeros((6,6)); C[0,2] = C[2,0] = 2; C[1,1] = -1
    ev, vec = np.linalg.eig(np.linalg.solve(Sm, C)); k = np.argmax(ev.real); a,b,c,d,e,f = vec[:,k].real
    den = b*b-4*a*c; cx = (2*c*d-b*e)/den; cy = (2*a*e-b*d)/den
    num = 2*(a*e*e+c*d*d-b*d*e+den*f); t = math.sqrt((a-c)**2+b*b)
    r1 = math.sqrt(abs(num*(a+c+t)))/abs(den); r2 = math.sqrt(abs(num*(a+c-t)))/abs(den)
    return dict(cx=float(cx*sc+mx), cy=float(cy*sc+my), r1=float(r1*sc), r2=float(r2*sc), rot=float(0.5*math.atan2(-b, c-a)))
def fit_ellipse_concentric(P, E):
    """Axes of an ellipse sharing E's centre and rotation, least squares on (u/r1)^2 + (v/r2)^2 = 1."""
    P = np.array(P); c, s_ = math.cos(E['rot']), math.sin(E['rot'])
    dx, dy = P[:,0]-E['cx'], P[:,1]-E['cy']; u = dx*c + dy*s_; v = -dx*s_ + dy*c
    A = np.c_[u*u, v*v]; sol, *_ = np.linalg.lstsq(A, np.ones(len(P)), rcond=None)
    return dict(cx=E['cx'], cy=E['cy'], r1=float(1/math.sqrt(sol[0])), r2=float(1/math.sqrt(sol[1])), rot=E['rot'])
def resid(E, P):
    T = np.linspace(0, 2*math.pi, 4000); c, s_ = math.cos(E['rot']), math.sin(E['rot'])
    Q = np.c_[E['cx'] + E['r1']*np.cos(T)*c - E['r2']*np.sin(T)*s_, E['cy'] + E['r1']*np.cos(T)*s_ + E['r2']*np.sin(T)*c]
    d = np.array([np.min(np.hypot(Q[:,0]-p[0], Q[:,1]-p[1])) for p in P]); return float(d.mean()), float(d.max())
HOOKS = {'L': dict(outer=[4,5,6], inner=[8,9,10], face=7), 'R': dict(outer=[17,0], inner=[14,15], face=16)}
bar['hooks'] = {}
for side, h in HOOKS.items():
    Po, Pi = piece_pts(h['outer']), piece_pts(h['inner'])
    Eo = fit_ellipse_free(Po); Ei = fit_ellipse_concentric(Pi, Eo)
    ro, ri = resid(Eo, Po), resid(Ei, Pi)
    bar['hooks'][side] = dict(outer=Eo, inner=Ei, outer_segs=h['outer'], inner_segs=h['inner'], face_seg=h['face'],
                              outer_resid=ro, inner_resid=ri)
    print(f"  hook {side}: outer ellipse centre ({Eo['cx']:.2f},{Eo['cy']:.2f}) axes {Eo['r1']:.2f} x {Eo['r2']:.2f} rot {math.degrees(Eo['rot']):.1f}deg  resid mean {ro[0]:.3f} max {ro[1]:.3f}")
    print(f"           inner, concentric: axes {Ei['r1']:.2f} x {Ei['r2']:.2f}  resid mean {ri[0]:.3f} max {ri[1]:.3f}   band {Eo['r1']-Ei['r1']:.2f} / {Eo['r2']-Ei['r2']:.2f} across the two axes")
# ---- the crossbar as a planetary ring: an elliptical annulus whose front half is the bar.
#      Outer ellipse: major axis from hook tip to hook tip, height fitted to the bar's top edge
#      (the edge the hooks' outer curls continue from).  Inner: concentric and coaxial, ends at
#      the eyes' far points, height fitted to the bar's bottom edge.
def P(k, n=300): return cubic_pts(segs[k], n)
top, bottom = P(2) + P(3), P(11) + P(12); outerL, outerR = P(4) + P(5) + P(6), P(17) + P(0); eyeL, eyeR = P(8) + P(9) + P(10), P(14) + P(15)
ax0 = np.array(pts[0]) - np.array(pts[6]); ax0 /= np.linalg.norm(ax0)
tipLp = min(outerL, key=lambda q: np.dot(q, ax0)); tipRp = max(outerR, key=lambda q: np.dot(q, ax0))
C = (np.array(tipLp) + np.array(tipRp)) / 2; axv = np.array(tipRp) - np.array(tipLp); a_o = np.linalg.norm(axv) / 2; axv /= 2*a_o; nv = np.array([-axv[1], axv[0]])
def uv(q): d = np.array(q) - C; return float(d @ axv), float(d @ nv)
def fit_b(Q, a):
    vals = [v*v/(1-(u/a)**2) for u, v in map(uv, Q) if abs(u) < 0.98*a]; return float(math.sqrt(np.mean(vals)))
def eresid(Q, a, b):
    T = np.linspace(0, 2*math.pi, 6000); E = np.array([C + axv*a*math.cos(t) + nv*b*math.sin(t) for t in T])
    d = np.array([np.min(np.hypot(E[:,0]-q[0], E[:,1]-q[1])) for q in Q]); return [float(d.mean()), float(d.max())]
b_o = fit_b(top, a_o)
eL = min(eyeL, key=lambda q: np.dot(q, axv)); eR = max(eyeR, key=lambda q: np.dot(q, axv))
a_i = (uv(eR)[0] - uv(eL)[0]) / 2; b_i = fit_b(bottom, a_i)
front_sign = 1.0 if np.mean([uv(q)[1] for q in top]) > 0 else -1.0
bar['ring'] = dict(centre=[float(C[0]), float(C[1])], axis=[float(axv[0]), float(axv[1])], tilt_deg=float(math.degrees(math.atan2(axv[1], axv[0]))),
                   a_outer=float(a_o), b_outer=b_o, a_inner=float(a_i), b_inner=b_i, front_sign=front_sign,
                   resid_top=eresid(top, a_o, b_o), resid_bottom=eresid(bottom, a_i, b_i),
                   resid_hook_curls=[eresid(outerL, a_o, b_o), eresid(outerR, a_o, b_o)], resid_eyes=[eresid(eyeL, a_i, b_i), eresid(eyeR, a_i, b_i)])
r = bar['ring']
print(f"  ring: centre ({r['centre'][0]:.2f},{r['centre'][1]:.2f}) tilt {r['tilt_deg']:.2f} deg  outer {r['a_outer']:.2f} x {r['b_outer']:.2f}  inner {r['a_inner']:.2f} x {r['b_inner']:.2f}  top-edge resid {r['resid_top'][0]:.3f}  bottom-edge resid {r['resid_bottom'][0]:.3f}  hook curls {r['resid_hook_curls'][0][0]:.2f}/{r['resid_hook_curls'][1][0]:.2f}")
json.dump(out, open(SRC/'ai_objects.json', 'w'))
print(f"  wrote {SRC/'ai_objects.json'}")
