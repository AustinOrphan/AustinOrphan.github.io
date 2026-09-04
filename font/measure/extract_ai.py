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
json.dump(out, open(SRC/'ai_objects.json', 'w'))
print(f"  wrote {SRC/'ai_objects.json'}")
