"""The two axes, shown as a grid: WEIGHT across, PUSH down.

Every cell is a real master build -- build_glyphs.py re-run at that (WEIGHT, PUSH) -- not an
interpolation, so what the sheet shows is what the variable font is built from.

    python3 measure/axes.py        # writes measure/evidence/axes.svg

Rasterise with measure/rasterize.mjs.
"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)

WORD = 'ORPHAN'
WEIGHTS = [0.70, 1.00, 1.45, 2.00]
PUSHES  = [0.30, 0.65, 1.00]
BG, INK, DIM, ACC = '#1D2B35', '#EEE5E9', '#8b9fac', '#2892D7'
NAME = dict(zip('0123456789', 'zero one two three four five six seven eight nine'.split()))

def build(w, p):
    env = dict(os.environ, ORPHAN_WEIGHT=str(w), ORPHAN_PUSH=str(p))
    subprocess.run([sys.executable, os.path.join(HERE, 'build_glyphs.py')],
                   check=True, env=env, cwd=HERE, capture_output=True)
    return json.load(open(os.path.join(HERE, 'build', 'glyphs.json')))

def path(g):
    out = []
    for c in g['contours']:
        out.append('M %.1f %.1f' % tuple(c['start']))
        for sg in c['segs']:
            out.append('L %.1f %.1f' % tuple(sg[1]) if sg[0] == 'l'
                       else 'C %.1f %.1f %.1f %.1f %.1f %.1f' % (*sg[1], *sg[2], *sg[3]))
        out.append('Z')
    return ' '.join(out)

def main():
    S, PAD, TOP = 0.115, 26, 150
    cells = [[build(w, p) for w in WEIGHTS] for p in PUSHES]
    colw = max(sum(G['glyphs'][NAME.get(ch, ch)]['adv'] for ch in WORD) for row in cells for G in row) * S
    W = 150 + len(WEIGHTS) * (colw + PAD) + 40
    H = TOP + len(PUSHES) * 120 + 90
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
           f'viewBox="0 0 {W:.0f} {H:.0f}"><rect width="{W:.0f}" height="{H:.0f}" fill="{BG}"/>']
    def txt(x, y, s, f=DIM, sz=12, wt=400):
        out.append(f'<text x="{x:.0f}" y="{y:.0f}" fill="{f}" font-family="ui-monospace,Menlo,'
                   f'monospace" font-size="{sz}" font-weight="{wt}">{s}</text>')
    txt(30, 42, 'Orphan Display: the two axes', INK, 20, 600)
    txt(30, 70, 'WEIGHT across, PUSH down. Every cell is a real master build, not an interpolation.', DIM, 12.5)
    txt(30, 90, 'PUSH moves thin and thick apart around a fixed mean, so it changes contrast at near-constant colour.', DIM, 12.5)
    for j, w in enumerate(WEIGHTS):
        txt(150 + j*(colw+PAD), TOP - 22, 'wght %d' % round(400*w), ACC, 12, 600)
    for i, p in enumerate(PUSHES):
        y = TOP + i*120 + 60
        txt(30, y - 18, 'PUSH %d' % round(p*100), ACC, 12, 600)
        for j, w in enumerate(WEIGHTS):
            G = cells[i][j]; x = 150 + j*(colw+PAD)
            for ch in WORD:
                g = G['glyphs'][NAME.get(ch, ch)]
                out.append(f'<g transform="translate({x:.1f},{y:.0f}) scale({S},{-S})">'
                           f'<path d="{path(g)}" fill="{INK}"/></g>')
                x += g['adv'] * S
    txt(30, H - 46, 'wght 280 is Thin and 800 is Black; the axis runs continuously between them.', DIM, 12)
    txt(30, H - 26, 'The buildable region is mapped in measure/bowl_region.py -- the bowl letters set the limits, not the diagonals.', DIM, 12)
    out.append('</svg>')
    path_out = os.path.join(HERE, 'measure', 'evidence', 'axes.svg')
    open(path_out, 'w').write(''.join(out))
    print('  wrote %s  %.0fx%.0f' % (os.path.relpath(path_out, HERE), W, H))

if __name__ == '__main__':
    main()
