"""Independent check of the stroke widths by pixel scan, plus hook tracing."""
from pathlib import Path
import json, math, re, numpy as np
from PIL import Image, ImageDraw
from svgpathtools import parse_path
HERE = str(Path(__file__).resolve().parent)
M = json.load(open(f"{HERE}/measurements.json"))
src = open(f"{Path(__file__).resolve().parents[2]}/src/components/Logo.astro").read()
d = re.findall(r'class="site-logo-mark"[^>]*><path d="([^"]+)"', src)[0]
subs = parse_path(d).continuous_subpaths()

SC = 0.2                                   # 5 mark units per pixel
W = H = int(11000*SC)
def poly(sub, per=4):
    pts = []
    for seg in sub:
        m = max(2, int(seg.length()/per))
        for i in range(m):
            p = seg.point(i/m); pts.append((p.real*SC, H - p.imag*SC))
    return pts
img = Image.new('1', (W, H), 0); dr = ImageDraw.Draw(img)
dr.polygon(poly(subs[0]), fill=1)
for s in subs[1:]: dr.polygon(poly(s), fill=0)
A = np.array(img, dtype=bool)
img.convert('L').point(lambda v: 255 if v else 0).save(f"{HERE}/raster.png")

def width_across(p, n):
    """Filled run length through point p along unit direction n (both ways)."""
    def run(sign):
        k = 0
        while True:
            q = (p[0] + sign*n[0]*k*5, p[1] + sign*n[1]*k*5)          # step 5 units
            x, y = int(q[0]*SC), int(H - q[1]*SC)
            if not (0 <= x < W and 0 <= y < H) or not A[y, x]: return k*5
            k += 1
    return run(1) + run(-1)

print("  pixel scan (5 units/px), perpendicular filled run through the stroke's centre-line:")
for name in ('leg_L', 'leg_R', 'bar'):
    st = M['strokes'][name]; c = np.array(st['centre']); v = np.array(st['dir']); n = np.array([-v[1], v[0]])
    rows = []
    for t in (-2500, -1500, 1000, 2000):
        p = c + v*t
        rows.append(f"{t:+5d}:{width_across(p, n):4d}")
    print(f"    {name:6s} " + "  ".join(rows) + f"    (line-fit said {st['width_at_centre']:.0f} centre, {st['taper_per_1000']:+.0f}/1000)")
cx, cy, ro = M['outer']['cx'], M['outer']['cy'], M['outer']['r']
rows = []
for bdeg in (0, 45, 90, 135, 180, 225, 270, 315):
    b = math.radians(bdeg); p = (cx + (ro-30)*math.cos(b), cy + (ro-30)*math.sin(b))
    # radial run inward from just inside the outer edge
    k = 0
    while True:
        q = (p[0] - math.cos(b)*k*5, p[1] - math.sin(b)*k*5); x, y = int(q[0]*SC), int(H - q[1]*SC)
        if not A[y, x]: break
        k += 1
    rows.append(f"{bdeg}:{k*5+30}")
icx, icy, ri, off = M['inner']['cx'], M['inner']['cy'], M['inner']['r'], M['inner']['offset']
pred = [f"{b}:{ro - (ri + off*math.cos(math.radians(b-M['inner']['offset_dir_deg']))):.0f}" for b in (0,45,90,135,180,225,270,315)]
print("    ring   " + "  ".join(rows) + "   (two-circle model predicts " + "  ".join(pred) + ")")

# ------------------------------------------------------------ trace the hooks
# The lobe's outer curve: silhouette points outside the ring near each bar end,
# ordered along the contour.  The eye: the whole small counter minus its ring arc.
def ordered_samples(sub, per=8):
    out = []
    for seg in sub:
        m = max(2, int(seg.length()/per))
        for i in range(m):
            p = seg.point(i/m); out.append((p.real, p.imag))
    return np.array(out)
S0 = ordered_samples(subs[0])
r = np.hypot(S0[:,0]-cx, S0[:,1]-cy)
outside = r > ro + 8
# split the outside mask into contiguous runs along the contour (wrapping)
runs, start = [], None
n = len(S0)
for i in list(range(n)) + [0]:
    if outside[i] and start is None: start = i
    if (not outside[i] or i == 0 and start is not None and i != start) and start is not None:
        runs.append((start, i)); start = None
def run_pts(a, b): return S0[a:b] if b > a else np.vstack([S0[a:], S0[:b]])
hooks = {}
for a, b in runs:
    Q = run_pts(a, b)
    if len(Q) < 4: continue
    c = Q.mean(0); bdeg = math.degrees(math.atan2(c[1]-cy, c[0]-cx)) % 360
    nm = 'apex' if 60 < bdeg < 120 else 'bar_R' if (bdeg < 45 or bdeg > 315) else 'bar_L' if 150 < bdeg < 210 else 'foot_L' if 210 <= bdeg < 260 else 'foot_R'
    hooks[nm] = Q
    print(f"    outside-ring run '{nm}': {len(Q)} pts, from ({Q[0][0]:.0f},{Q[0][1]:.0f}) to ({Q[-1][0]:.0f},{Q[-1][1]:.0f})")
eyes = {}
for nm, i in (('bar_L', 8), ('bar_R', 4)):
    E = ordered_samples(subs[i], per=6); er = np.hypot(E[:,0]-cx, E[:,1]-cy)
    on_ring = np.abs(er-ro) < 12
    eyes[nm] = dict(pts=E.tolist(), on_ring=on_ring.tolist())
    print(f"    eye {nm}: {len(E)} pts, {on_ring.sum()} on the ring's outer circle")
json.dump({'lobes': {k: v.tolist() for k, v in hooks.items()}, 'eyes': eyes},
          open(f"{HERE}/traced.json", "w"))
print("  wrote traced.json, raster.png")
