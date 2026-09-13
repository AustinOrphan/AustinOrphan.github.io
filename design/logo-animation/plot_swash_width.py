"""The swash's width along its length: the artwork, the gain it is owed, and what it is.

    <venv>/bin/python design/logo-animation/plot_swash_width.py

Width here is a TRUE perpendicular section, not a paired distance.  The spine is the
paired midline; at every sample the normal is cast both ways and intersected with the two
edges within a local window, so the number is the width of the ribbon at that station and
does not inherit the pairing's habit of over-reading where the ribbon turns.
"""
import json, os, sys
import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'font', 'measure'))
import swash_derived as sd
import rules

BG, PANEL, INK, DIM, GRID = (13, 20, 26), (23, 34, 43), (238, 229, 233), (150, 168, 182), (44, 62, 76)
BLUE, RED, GOLD, GREY = (40, 146, 215), (209, 102, 102), (222, 178, 90), (120, 138, 152)

def F(sz, bold=False):
    for p in ('/System/Library/Fonts/Supplemental/Helvetica.ttc',
              '/System/Library/Fonts/HelveticaNeue.ttc'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz, index=1 if bold else 0)
    return ImageFont.load_default()

def profile(items, n=420, lo=0.02):
    """Width against arc fraction, from the module's own section measure."""
    _, w, u = sd._section(sd._walk(items, sd.EDGE_OUTER, 400),
                          sd._walk(items, sd.EDGE_INNER, 400), step=3)
    g = np.linspace(lo, 1 - lo, n)
    return g, np.interp(g, u, w), float(np.abs(np.diff(
        (lambda o, i: (o + sd._at(i, np.clip(np.maximum.accumulate(
            sd._smooth(sd._arcfrac(i)[sd._pair(o, i)], 0.02)), 0, 1))) / 2)(
            sd._walk(items, sd.EDGE_OUTER, 400), sd._walk(items, sd.EDGE_INNER, 400)))).sum())


def paired(items, n=420, lo=0.02):
    """The width the CODE works in: |outer - inner| at the smoothed pairing."""
    o = sd._walk(items, sd.EDGE_OUTER, 400)
    i = sd._walk(items, sd.EDGE_INNER, 400)
    t = np.clip(np.maximum.accumulate(sd._smooth(sd._arcfrac(i)[sd._pair(o, i)], 0.02)), 0, 1)
    mid = (o + sd._at(i, t)) / 2
    u = sd._arcfrac(mid)
    g = np.linspace(lo, 1 - lo, n)
    return np.interp(g, u, np.abs(o - sd._at(i, t)))


def raster(items, us, K=24):
    """A second opinion that shares nothing with the first: rasterise the ribbon and read
    twice the distance to its boundary on the spine -- the inscribed-circle width."""
    P = np.concatenate([np.array(sd._seg_pts(it, 400)) for it in items])
    x0, y0 = P.real.min() - 2, P.imag.min() - 2
    W, H = int((P.real.max() - x0 + 2) * K), int((P.imag.max() - y0 + 2) * K)
    im = Image.new('1', (W, H), 0)
    ImageDraw.Draw(im).polygon([((z.real - x0) * K, (z.imag - y0) * K) for z in P], fill=1)
    dt = distance_transform_edt(np.array(im))
    o = sd._walk(items, sd.EDGE_OUTER, 400)
    i = sd._walk(items, sd.EDGE_INNER, 400)
    t = np.clip(np.maximum.accumulate(sd._smooth(sd._arcfrac(i)[sd._pair(o, i)], 0.02)), 0, 1)
    mid = (o + sd._at(i, t)) / 2
    out = []
    for u in us:
        z = sd._at(mid, np.array([u]))[0]
        px, py = int(round((z.real - x0) * K)), int(round((z.imag - y0) * K))
        out.append(2 * float(dt[max(0, py - K):py + K, max(0, px - K):px + K].max()) / K)
    return np.array(out)


def poly_area(items):
    P = np.concatenate([np.array(sd._seg_pts(it, 300)) for it in items])
    x, y = P.real, P.imag
    return abs(float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) / 2)

art = {o['role']: o for o in json.load(open(os.path.join(ROOT, 'font', 'source', 'ai_objects.json')))['AO'][0]['objects']}
now = {o['role']: o for o in json.load(open(os.path.join(HERE, 'ai_objects_derived.json')))['AO'][0]['objects']}
A_it, N_it = art['white']['items'], now['white']['items']

aa, an = poly_area(A_it), poly_area(N_it)
ua, wa, la = profile(A_it)
un, wn, ln = profile(N_it)
G = rules.RING_GAIN
HEAD = 1.5978          # the A's foot cut grew by this
REACH = sd.HEAD_REACH
BODY = sd.HEAD_REACH        # the body starts where the cut's own flare is spent
target = wa * (G + (HEAD - G) * sd._ease(1.0 - np.minimum(1.0, ua / REACH)))
ratio = np.where((ua >= BODY) & (ua <= 1 - sd.END_BLEND), wn / wa, np.nan)
uk = np.arange(0.15, 0.96, 0.05)
rk = raster(N_it, uk) / raster(A_it, uk)
print('spine len art %.2f now %.2f   area art %.1f now %.1f' % (la, ln, aa, an))

print('area/length  artwork %.4f   now %.4f   ratio %.4f' % (aa / la, an / ln, (an / ln) / (aa / la)))
print('width ratio  p10 %.3f  p50 %.3f  p90 %.3f' % tuple(np.nanpercentile(ratio, (10, 50, 90))))

# ---------------------------------------------------------------- plot
PW, PH, L, T = 1180, 420, 92, 34
def axes(d, ox, oy, ylo, yhi, yticks, ylab, xlab='position along the swash, head to tail'):
    X = lambda u: ox + L + u * (PW - L - 24)
    Y = lambda v: oy + T + (yhi - v) / (yhi - ylo) * (PH - T - 46)
    d.rectangle([ox, oy, ox + PW, oy + PH], fill=PANEL)
    for v in yticks:
        d.line([X(0), Y(v), X(1), Y(v)], fill=GRID)
        d.text((ox + L - 10, Y(v) - 8), ('%g' % v), fill=DIM, font=F(15), anchor='ra')
    for u in np.arange(0, 1.01, 0.1):
        d.line([X(u), Y(ylo), X(u), Y(yhi)], fill=(34, 49, 60))
        d.text((X(u), Y(ylo) + 8), '%d%%' % round(u * 100), fill=DIM, font=F(14), anchor='ma')
    d.text((ox + 14, oy + 10), ylab, fill=INK, font=F(16, True))
    d.text((X(1), Y(ylo) + 26), xlab, fill=DIM, font=F(14), anchor='ra')
    return X, Y

im = Image.new('RGB', (PW + 40, PH * 2 + 108), BG)
d = ImageDraw.Draw(im)
d.text((20, 14), 'How thick the swash is, all the way along', fill=INK, font=F(20, True))
d.text((20, 40), 'true perpendicular sections through the ribbon, in mark units '
                 '(the mark is 95 tall).  head = where it leaves the A\'s foot, tail = the hoop.',
       fill=DIM, font=F(14))

X, Y = axes(d, 20, 66, 0, 8, [0, 1, 2, 3, 4, 5, 6, 7, 8], 'width, mark units')
def series(X, Y, u, v, col, w=3):
    d.line([(X(a), Y(b)) for a, b in zip(u, v) if np.isfinite(b)], fill=col, width=w, joint='curve')
series(X, Y, ua, wa, GREY, 2)
series(X, Y, ua, target, GOLD, 2)
series(X, Y, un, wn, BLUE, 3)
for u, lab in ((0.05, 'bottom of the hook'), (0.27, 'outside of the bowl'),
               (0.50, 'crossing the A'), (0.85, 'the run out to the tip')):
    d.line([X(u), Y(0), X(u), Y(8)], fill=(62, 84, 100), width=1)
    d.text((X(u) + 5, Y(0) - 16), lab, fill=(110, 130, 145), font=F(13))
for i, (c, s) in enumerate(((GREY, 'the artwork swash'),
                            (GOLD, 'what it is owed  =  artwork x1.226, x1.598 at the cut'),
                            (BLUE, 'now'))):
    d.line([X(0.40) + 8, 66 + 26 + i * 20, X(0.40) + 40, 66 + 26 + i * 20], fill=c, width=3)
    d.text((X(0.40) + 48, 66 + 18 + i * 20), s, fill=DIM, font=F(14))

X2, Y2 = axes(d, 20, 66 + PH + 22, 0.9, 1.8, [1.0, 1.226, 1.4, 1.598, 1.8], 'how much wider than the artwork')
d.line([X2(0), Y2(G), X2(1), Y2(G)], fill=GOLD, width=2)
d.text((X2(1) - 6, Y2(G) - 20), 'x%.4f  the gain the rounds took' % G, fill=GOLD, font=F(14), anchor='ra')
series(X2, Y2, ua, ratio, BLUE, 3)
for u, r in zip(uk, rk):
    d.ellipse([X2(u) - 4, Y2(r) - 4, X2(u) + 4, Y2(r) + 4], outline=INK, width=2)
for k, (c, lab) in enumerate(((BLUE, 'true perpendicular section  --  what the eye reads'),)):
    d.line([X2(0.52), Y2(1.74) + k * 22, X2(0.52) + 32, Y2(1.74) + k * 22], fill=c, width=3)
    d.text((X2(0.52) + 40, Y2(1.74) - 9 + k * 22), lab, fill=DIM, font=F(14))
d.ellipse([X2(0.52) + 12, Y2(1.74) + 40, X2(0.52) + 20, Y2(1.74) + 48], outline=INK, width=2)
d.text((X2(0.52) + 40, Y2(1.74) + 35), 'a second opinion: twice the distance transform on a '
       'raster of the ribbon', fill=DIM, font=F(14))
p10, p50, p90 = np.nanpercentile(ratio, (10, 50, 90))
d.text((X2(0) + 10, Y2(1.8) + 6),
       'body (past the head flare) median x%.3f   p10 x%.3f, p90 x%.3f   --   ink area / centreline length x%.3f'
       % (p50, p10, p90, (an / ln) / (aa / la)), fill=INK, font=F(15))
im.save(os.path.join(HERE, 'swash-width.png'))
print('wrote swash-width.png')
