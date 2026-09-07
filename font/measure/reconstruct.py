"""
Rebuild the mark from measurements.json + traced.json, in the mark's own
coordinates, and score it against the original path by intersection-over-union.

If this scores high, the measurements are trustworthy and every later glyph can
be built from them.  If it doesn't, the diff image says where to look.
"""
from pathlib import Path
import json, math, re, numpy as np
from PIL import Image, ImageDraw
from svgpathtools import parse_path
HERE = str(Path(__file__).resolve().parent)
M = json.load(open(f"{HERE}/measurements.json")); TR = json.load(open(f"{HERE}/traced.json"))
src = open(f"{Path(__file__).resolve().parents[2]}/src/components/Logo.astro").read()
d = re.findall(r'class="site-logo-mark"[^>]*><path d="([^"]+)"', src)[0]
subs = parse_path(d).continuous_subpaths()
A = lambda *a: np.array(a, float)

def isect(l1, l2):
    (c1, v1), (c2, v2) = [(A(*c), A(*v)) for c, v in (l1, l2)]
    t = np.linalg.solve(np.array([v1, -v2]).T, c2-c1); return c1+t[0]*v1
def line_circle(line, c, r, pick):
    """Intersections of a line with a circle; pick='min'|'max' by the line parameter, or a point to be nearest to."""
    p, v = A(*line[0]), A(*line[1]); f = p - A(*c)
    b = 2*(f@v); cc = f@f - r*r; disc = b*b-4*cc
    ts = [(-b-math.sqrt(disc))/2, (-b+math.sqrt(disc))/2]
    if pick == 'min': t = min(ts)
    elif pick == 'max': t = max(ts)
    else: t = min(ts, key=lambda t: np.linalg.norm(p+v*t-A(*pick)))
    return p+v*t
def circle_poly(c, r, n=720):
    return [(c[0]+r*math.cos(2*math.pi*i/n), c[1]+r*math.sin(2*math.pi*i/n)) for i in range(n)]
def arc_poly(c, r, p_from, p_to, ccw, n=60):
    a0 = math.atan2(p_from[1]-c[1], p_from[0]-c[0]); a1 = math.atan2(p_to[1]-c[1], p_to[0]-c[0])
    if ccw and a1 < a0: a1 += 2*math.pi
    if not ccw and a1 > a0: a1 -= 2*math.pi
    return [(c[0]+r*math.cos(a0+(a1-a0)*i/n), c[1]+r*math.sin(a0+(a1-a0)*i/n)) for i in range(n+1)]
def line_from_angle(p, deg): return (tuple(p), (math.cos(math.radians(deg)), math.sin(math.radians(deg))))

O  = (M['outer']['cx'], M['outer']['cy']); RO = M['outer']['r']
I  = (M['inner']['cx'], M['inner']['cy']); RI = M['inner']['r']
S  = M['strokes']; T = M['terminals']; tips = M['tips']
# edge lines: strokes[...]['edges'] = [[c, v], [c, v]] ; for legs edge 0 borders counters on the OUTER side
legL_out, legL_in = S['leg_L']['edges']; legR_in, legR_out = S['leg_R']['edges']; bar_top, bar_bot = S['bar']['edges']

# ------------------------------------------------------------------ pieces
pieces, holes = {}, {}
pieces['ring_outer'] = circle_poly(O, RO); holes['ring_inner'] = circle_poly(I, RI)

apex_tip     = isect(legL_out, legR_out)
counter_apex = isect(legL_in,  legR_in)
cutL = line_from_angle(tips['foot_L'], T['foot_L']['cut_angle_deg']); cutR = line_from_angle(tips['foot_R'], T['foot_R']['cut_angle_deg'])
# foot tips sit on the outer edge lines by construction: check how far the measured tips are from those lines
def dist_to_line(p, line):
    c, v = A(*line[0]), A(*line[1]); n = A(-v[1], v[0]); return float((A(*p)-c)@n)
print(f"  foot tips vs outer edge lines: L {dist_to_line(tips['foot_L'], legL_out):+.0f}  R {dist_to_line(tips['foot_R'], legR_out):+.0f}   apex tip vs edge meet: {np.linalg.norm(apex_tip-A(*tips['apex'])):.0f}")
footL_tip = isect(legL_out, cutL); footR_tip = isect(legR_out, cutR)
pieces['leg_L'] = [tuple(footL_tip), tuple(apex_tip), tuple(counter_apex), tuple(isect(legL_in, cutL))]
pieces['leg_R'] = [tuple(footR_tip), tuple(apex_tip), tuple(counter_apex), tuple(isect(legR_in, cutR))]
# bar: the region between two circular arcs (measured in bar_curve.py), ending
# where each arc crosses the ring's outer circle
def circle_circle(c1, r1, c2, r2, pick):
    (x1, y1), (x2, y2) = c1, c2; dd = math.hypot(x2-x1, y2-y1)
    a = (r1*r1-r2*r2+dd*dd)/(2*dd); h = math.sqrt(max(0, r1*r1-a*a))
    mx, my = x1+a*(x2-x1)/dd, y1+a*(y2-y1)/dd
    cands = [(mx+h*(y2-y1)/dd, my-h*(x2-x1)/dd), (mx-h*(y2-y1)/dd, my+h*(x2-x1)/dd)]
    return min(cands, key=lambda q: q[0]) if pick == 'min' else max(cands, key=lambda q: q[0])
BT, BB = M['bar_arcs']['top'], M['bar_arcs']['bottom']
bt_L = circle_circle(BT[:2], BT[2], O, RO, 'min'); bt_R = circle_circle(BT[:2], BT[2], O, RO, 'max')
bb_L = circle_circle(BB[:2], BB[2], O, RO, 'min'); bb_R = circle_circle(BB[:2], BB[2], O, RO, 'max')
top_arc = arc_poly(BT[:2], BT[2], bt_L, bt_R, ccw=False, n=80)   # left to right along the top
bot_arc = arc_poly(BB[:2], BB[2], bb_R, bb_L, ccw=True,  n=80)   # right to left along the bottom
pieces['bar'] = top_arc + bot_arc
# hooks: traced lobe outer curve, closed along the ring's outer arc
for nm in ('bar_L', 'bar_R'):
    lobe = [tuple(p) for p in TR['lobes'][nm]]
    # the traced run starts and ends just outside the circle; snap both ends onto it
    def snap(p):
        a = math.atan2(p[1]-O[1], p[0]-O[0]); return (O[0]+RO*math.cos(a), O[1]+RO*math.sin(a))
    lobe = [snap(lobe[0])] + lobe + [snap(lobe[-1])]
    # close along the arc that stays outside the A (the short way round)
    back = arc_poly(O, RO, lobe[-1], lobe[0], ccw=(nm == 'bar_L'))
    pieces['hook_'+nm] = lobe + back[1:-1]
    holes['eye_'+nm] = [tuple(p) for p in TR['eyes'][nm]['pts']]

# ------------------------------------------------------------------ raster + IoU
SC = 0.25; W = H = int(11200*SC)
def to_px(poly): return [(x*SC, H - y*SC) for x, y in poly]
def sample(sub, per=3):
    out = []
    for seg in sub:
        m = max(2, int(seg.length()/per))
        for i in range(m): p = seg.point(i/m); out.append((p.real, p.imag))
    return out
orig = Image.new('1', (W, H), 0); dr = ImageDraw.Draw(orig)
dr.polygon(to_px(sample(subs[0])), fill=1)
for s in subs[1:]: dr.polygon(to_px(sample(s)), fill=0)
reco = Image.new('1', (W, H), 0); dr = ImageDraw.Draw(reco)
for k, p in pieces.items(): dr.polygon(to_px(p), fill=1)
for k, p in holes.items(): dr.polygon(to_px(p), fill=0)
# the ring's hole must not punch through the legs/bar: redraw strokes over it
for k in ('leg_L', 'leg_R', 'bar'): dr.polygon(to_px(pieces[k]), fill=1)
for k in ('eye_bar_L', 'eye_bar_R'): dr.polygon(to_px(holes[k]), fill=0)
a, b = np.array(orig, bool), np.array(reco, bool)
inter, union = (a & b).sum(), (a | b).sum()
print(f"  IoU = {inter/union:.4f}   original {a.sum()} px, reconstruction {b.sum()} px, missing {(a&~b).sum()} px, extra {(~a&b).sum()} px  (1 px = {1/SC:.0f} units)")
# where are the errors? bucket by bearing from the ring centre
ys, xs = np.nonzero(a ^ b); bx = xs/SC; by = H/SC - ys/SC
bear = (np.degrees(np.arctan2(by-O[1], bx-O[0])) + 360) % 360; rad = np.hypot(bx-O[0], by-O[1])
hist = np.histogram(bear, bins=12, range=(0, 360))[0]
print("  mismatched px by 30deg sector from the ring centre: " + " ".join(f"{i*30}:{h}" for i, h in enumerate(hist)))
print(f"  mismatched px inside the inner circle {(rad < RI).sum()}, in the ring band {((rad >= RI) & (rad <= RO)).sum()}, outside {(rad > RO).sum()}")
# diff image: original-only red, reconstruction-only blue, both light
img = Image.new('RGB', (W, H), (29, 43, 53)); px = np.array(img)
px[a & b] = (238, 229, 233); px[a & ~b] = (209, 102, 102); px[~a & b] = (40, 146, 215)
Image.fromarray(px).save(f"{HERE}/reconstruct_diff.png")
json.dump({'pieces': pieces, 'holes': holes, 'apex_tip': apex_tip.tolist(), 'counter_apex': counter_apex.tolist(),
           'footL_tip': footL_tip.tolist(), 'footR_tip': footR_tip.tolist()}, open(f"{HERE}/reconstruction.json", "w"))
print("  wrote reconstruct_diff.png, reconstruction.json")
