"""Draw where the swash leaves the A's right foot, three ways.

The artwork grows the swash straight out of the leg -- its outer edge leaves V[3] collinear
with the leg edge arriving there, 1.04 deg off.  Warping the swash onto the re-derived
mark does not keep that on its own: scaling about a centre-line rotates a tangent wherever
the edge and the centre-line are not parallel, and at a cut they never are.  This is the
sheet that shows it, and that measure/swash_derived's departure matching puts it back.

    <venv>/bin/python design/logo-animation/plot_swash_departure.py
"""
import json, math, cmath, os, subprocess, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EMIT = os.path.join(ROOT, 'font', 'measure', 'emit_derived_objects.py')
DERIVED = os.path.join(HERE, 'ai_objects_derived.json')
OUT = os.path.join(HERE, 'swash-departure.png')

X0, X1, Y0, Y1, WP, HP = 64.0, 90.0, -2.0, 22.0, 600, 560


def objects(path):
    return {o['role']: o for o in json.load(open(path))['AO'][0]['objects']}


def flatten(items, n=140):
    out = []
    for it in items:
        P = [complex(*q) for q in it[1:]]
        ts = [i / (n - 1.) for i in range(n)]
        out += ([P[0] + (P[1] - P[0]) * t for t in ts] if it[0] == 'l' else
                [(1-t)**3*P[0] + 3*(1-t)**2*t*P[1] + 3*(1-t)*t*t*P[2] + t**3*P[3] for t in ts])
    return out


def turn(O):
    """The swash's outer edge leaving V[3], measured against the leg edge arriving there."""
    V = [complex(*v) for v in O['A']['vertices']]
    w = O['white']['items']
    t = complex(*w[3][4]) - complex(*w[3][3])
    return (math.degrees(cmath.phase(t / (V[3] - V[2]))) + 180) % 360 - 180


def panel(O, label):
    im = Image.new('RGB', (WP + 40, HP + 40), (29, 43, 53))
    d = ImageDraw.Draw(im)
    T = lambda z: ((z.real - X0) / (X1 - X0) * WP + 20, HP - (z.imag - Y0) / (Y1 - Y0) * HP + 20)
    V = [complex(*v) for v in O['A']['vertices']]
    d.line([T(z) for z in V + [V[0]]], fill=(238, 229, 233), width=3)
    d.line([T(z) for z in flatten(O['white']['items'])], fill=(40, 146, 215), width=3)
    for i in (3, 4):
        x, y = T(V[i]); d.ellipse([x-5, y-5, x+5, y+5], fill=(209, 102, 102))
        d.text((x + 8, y - 14), 'V[%d]' % i, fill=(209, 102, 102))
    return im, label


def main():
    env = dict(os.environ)
    cols = []
    art = objects(os.path.join(ROOT, 'font', 'source', 'ai_objects.json'))
    cols.append(panel(art, 'the artwork  --  %.2f deg, collinear with the leg' % turn(art)))
    for flag, name in (('0', 'warped onto the new cut, angles left to the warp'),
                       ('1', 'departures matched back to the artwork  (landed)')):
        subprocess.run([sys.executable, EMIT], check=True, capture_output=True,
                       env=dict(env, ORPHAN_SWASH_DEPART=flag))
        O = objects(DERIVED)
        cols.append(panel(O, '%s  --  %.2f deg' % (name, turn(O))))

    sheet = Image.new('RGB', (len(cols) * (WP + 50) + 20, HP + 100), (13, 20, 26))
    d = ImageDraw.Draw(sheet)
    d.text((16, 10), "Where the swash leaves the A's right foot", fill=(235, 229, 233))
    d.text((16, 26), "white = the A, blue = the swash.  The artwork grows the swash straight "
                     "out of the leg edge; the warp turns it off by 20 deg.",
           fill=(140, 160, 175))
    for i, (im, lab) in enumerate(cols):
        sheet.paste(im, (20 + i * (WP + 50), 66))
        d.text((26 + i * (WP + 50), 50), lab, fill=(160, 180, 195))
    sheet.save(OUT)
    print('  wrote %s (%dx%d)' % (os.path.relpath(OUT, ROOT), *sheet.size))


if __name__ == '__main__':
    main()
