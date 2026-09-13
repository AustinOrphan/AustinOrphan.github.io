#!/usr/bin/env python3
"""Does every glyph stay inside the vertical metrics the font declares, everywhere on both axes?

A font states an ascent and a descent, and layout believes them.  Ink outside that band is not
a rounding question: GDI clips to it, several PDF paths clip to it, and a line box sized from it
leaves the overflow to collide with the line above or below.

The failure this exists to catch is quiet, because it does not happen at the default instance.
The comma's tail was written as 2.6 dots and a dot follows the stroke, so the tip sank from 137
below the baseline at the light end of the weight axis to 275 at the heavy one.  At the mark's
own cut it was fine.  From about wght 517 upward it was 75 units outside a declared descent of
200, and nothing in the build said so -- the outlines were valid, the masters interpolated, and
every proof sheet was drawn without a metric line on it.

So the check has to sweep the axes rather than look at one instance, and it has to be run on the
SOURCE, where a failure can be traced back to the rule that caused it.

  <venv>/bin/python measure/vertical_metrics.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'lib'))
from pen import Contour                                             # noqa: E402
from metrics import ASCENT, DESCENT                                 # noqa: E402

# The corners plus the middle of each axis.  The binding case is always a corner -- every rule in
# the face is monotonic in the two knobs -- but the middle is cheap and catches a rule that is not.
WEIGHTS = [0.70, 1.00, 1.45, 2.00]
PUSHES = [0.30, 0.65, 1.00]
TOL = 0.5          # units; below the compiler's own rounding, so a pass means a real pass


def build(w, p, out):
    subprocess.run([sys.executable, os.path.join(HERE, 'build_glyphs.py'), '--out', out],
                   env=dict(os.environ, ORPHAN_WEIGHT=str(w), ORPHAN_PUSH=str(p)),
                   capture_output=True, check=True)
    return json.load(open(out))['glyphs']


def main():
    tmp = os.path.join(HERE, 'build', '_vmetrics.json')
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    worst, checked = {}, 0
    for w in WEIGHTS:
        for p in PUSHES:
            for name, g in build(w, p, tmp).items():
                ys = [q[1] for c in g['contours'] for q in Contour.from_json(c).flatten()]
                if not ys:
                    continue
                checked += 1
                over = max(-DESCENT - min(ys), max(ys) - ASCENT)
                if over > worst.get(name, (0.0,))[0]:
                    worst[name] = (over, w, p, min(ys), max(ys))
    print(f'  checked {checked} glyph instances over {len(WEIGHTS) * len(PUSHES)} points of the '
          f'design space, against ascent {ASCENT} / descent {-DESCENT}')
    bad = [(n, v) for n, v in worst.items() if v[0] > TOL]
    if not bad:
        print('  every glyph is inside both, everywhere')
        return
    print(f'  {len(bad)} glyphs fall outside:')
    for n, (over, w, p, lo, hi) in sorted(bad, key=lambda kv: -kv[1][0]):
        print(f'    {n:12s} {over:6.1f} units outside, at WEIGHT {w:.2f} PUSH {p:.2f} '
              f'({lo:.1f} .. {hi:.1f})')
    sys.exit(1)


if __name__ == '__main__':
    main()
