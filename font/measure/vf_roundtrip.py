#!/usr/bin/env python3
"""Does the variable font reproduce each master at that master's own axis location?

This is the test that makes the master-alignment in build_variable safe to trust.  Inserting
points to make masters compatible is easy to get half right: the counts match, varLib stops
complaining, and the interpolation is quietly wrong -- a corner slid into the middle of a
curve, a point paired with the wrong point.  Nothing downstream notices, because the default
instance still looks correct.

At a master's own location the variable font must be that master, exactly.  If the points
were paired wrongly the deltas cannot cancel and the instance comes out somewhere else.  So
this instantiates at all 18 grid points and compares every glyph's outline against the master
built for that point.

  <venv>/bin/python measure/vf_roundtrip.py
"""
import glob
import os
import re
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.recordingPen import RecordingPen

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(HERE, 'build')
VF = os.path.join(BUILD, 'OrphanDisplay-VF.ttf')
# Font units.  Outlines are rounded to integers and gvar stores integer deltas, so a unit of
# disagreement between a master and the instance rebuilt from it is arithmetic, not error:
# each end can round its own way.  1.0 flagged comma and semicolon at 1.2 and had them frozen
# for nothing.  The real failures are two orders of magnitude larger -- 70 units and 304 --
# so there is no danger of this hiding one.
TOL = 2.0


def axis_map(vf):
    """The user-space value each master's file name stands for."""
    return {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in vf['fvar'].axes}


def outline(font, name):
    gs = font.getGlyphSet()
    if name not in gs:
        return None
    rp = RecordingPen()
    gs[name].draw(rp)
    return rp.value


def _contours(rec):
    out, cur = [], []
    for op, args in rec:
        cur.append((op, args))
        if op in ('closePath', 'endPath'):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def _key(con):
    pts = [a[-1] for _, a in con if a]
    n = len(pts) or 1
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)


def compare(a, b):
    """Worst distance between two recordings, or inf if their structure differs.

    Contours are matched by where they sit, not by the order they are written in.  The build
    puts every master's contours into one order so they can interpolate, so an instance is
    allowed to list them differently from the master file it came from -- that is a rewrite,
    not a different shape, and comparing them in file order reports most of the cap height.
    """
    if a is None or b is None:
        return None if a is b else float('inf')
    ca, cb = _contours(a), _contours(b)
    if len(ca) != len(cb):
        return float('inf')
    used, worst = set(), 0.0
    for x in ca:
        ka = _key(x)
        cand = [j for j in range(len(cb)) if j not in used
                and [op for op, _ in cb[j]] == [op for op, _ in x]]
        if not cand:
            return float('inf')
        j = min(cand, key=lambda j: (_key(cb[j])[0] - ka[0]) ** 2 + (_key(cb[j])[1] - ka[1]) ** 2)
        used.add(j)
        for (_, pa), (_, pb) in zip(x, cb[j]):
            for qa, qb in zip(pa, pb):
                if qa is None or qb is None:
                    continue
                worst = max(worst, abs(qa[0] - qb[0]), abs(qa[1] - qb[1]))
    return worst


def main():
    if not os.path.exists(VF):
        raise SystemExit('  no variable font; run build_variable.py first')
    masters = sorted(glob.glob(os.path.join(BUILD, 'masters', 'master-*.ttf')))
    if not masters:
        raise SystemExit('  no masters on disk; run build_variable.py first')
    vf = TTFont(VF)
    ax = axis_map(vf)
    wmin, _, wmax = ax['wght']
    pmin, _, pmax = ax['PUSH']

    # The file names carry the design-space knobs; map them onto the axes the same way
    # build_variable does: weight 0.70..2.00 -> wght min..max, push 0.30..1.00 -> PUSH.
    ws = sorted({float(re.search(r'w(\d+)', m).group(1)) / 100 for m in masters})
    ps = sorted({float(re.search(r'p(\d+)', m).group(1)) / 100 for m in masters})
    lerp = lambda v, lo, hi, a, b: a + (b - a) * (v - lo) / (hi - lo)

    bad, checked = [], 0
    for path in masters:
        w = float(re.search(r'w(\d+)', path).group(1)) / 100
        p = float(re.search(r'p(\d+)', path).group(1)) / 100
        loc = {'wght': lerp(w, ws[0], ws[-1], wmin, wmax),
               'PUSH': lerp(p, ps[0], ps[-1], pmin, pmax)}
        inst = instancer.instantiateVariableFont(TTFont(VF), loc)
        master = TTFont(path)
        for name in master.getGlyphOrder():
            d = compare(outline(master, name), outline(inst, name))
            checked += 1
            if d is None:
                continue
            if d > TOL:
                bad.append((os.path.basename(path), name, d))
    print(f'  checked {checked} glyph instances across {len(masters)} masters')
    if not bad:
        print('  every master is reproduced at its own axis location')
        return
    worst = {}
    for m, n, d in bad:
        worst[n] = max(worst.get(n, 0.0), d)
    print(f'  {len(worst)} glyphs do NOT come back at their own location:')
    for n, d in sorted(worst.items(), key=lambda kv: -kv[1])[:20]:
        print(f'    {n:10s} off by {d:.1f} units' if d != float('inf')
              else f'    {n:10s} different structure')
    sys.exit(1)


if __name__ == '__main__':
    main()
