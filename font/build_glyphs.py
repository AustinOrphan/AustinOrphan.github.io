#!/usr/bin/env python3
"""Build every glyph's outline polygons into build/glyphs.json (run with the venv)."""
import argparse, glob, importlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('--only', help='comma-separated glyph module names, e.g. core,set_straight')
ap.add_argument('--out', default=os.path.join(HERE, 'build', 'glyphs.json')); args = ap.parse_args()
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'lib'))
from metrics import UPM, CAP, ASCENT, DESCENT
out = dict(upm=UPM, cap=CAP, ascent=ASCENT, descent=DESCENT, glyphs={})
for path in sorted(glob.glob(os.path.join(HERE, 'glyphs', '*.py'))):
    mod = os.path.basename(path)[:-3]
    if mod.startswith('_'): continue
    if args.only and mod not in args.only.split(','): continue
    m = importlib.import_module(f'glyphs.{mod}')
    for name, build in getattr(m, 'GLYPHS', {}).items():
        g = build()
        g['contours'] = [c.to_json() for c in g['contours']]
        g['source'] = mod
        out['glyphs'][name] = g
        print(f"  {name:8s} cp {g['cp']:5d}  adv {g['adv']:4d}  {len(g['contours'])} contours   ({mod})")
os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
json.dump(out, open(args.out, 'w'))
print(f"  wrote {os.path.relpath(args.out, HERE)} with {len(out['glyphs'])} glyphs")
