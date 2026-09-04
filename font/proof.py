#!/usr/bin/env python3
"""Proof sheets from build/glyphs.json: a specimen row, and A/O mapped back onto the Illustrator source."""
import argparse, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'lib'))
from pen import Contour, source_contours, add, sub, mul, rot
ap = argparse.ArgumentParser(); ap.add_argument('--in', dest='inp', default=os.path.join(HERE, 'build', 'glyphs.json'))
ap.add_argument('--out', default=os.path.join(HERE, 'build', 'proof.svg'), help='specimen sheet path')
ap.add_argument('--overlay', action='store_true', help='also write the A/O source overlay next to it'); args = ap.parse_args()
G = json.load(open(args.inp))
SRC = json.load(open(os.path.join(HERE, 'source', 'ai_objects.json')))['AO'][0]
OBJ = {o['role']: o for o in SRC['objects']}
CAP = G['cap']
BG, INK, ACC, RED, DIM = '#1D2B35', '#EEE5E9', '#2892D7', '#D16666', '#5a6e7c'

def sheet(names, path, scale=0.32, pad=40):
    x, parts = pad, []
    H = int((G['ascent'] + G['descent']) * scale) + 2*pad
    base = pad + G['ascent'] * scale
    for n in names:
        g = G['glyphs'][n]; adv = g['adv'] * scale
        parts.append(f'<rect x="{x}" y="{pad}" width="{adv}" height="{H-2*pad}" fill="none" stroke="{DIM}" stroke-dasharray="3 3"/>')
        d = " ".join(Contour.from_json(c).to_svg() for c in g['contours'])
        parts.append(f'<g transform="translate({x},{base}) scale({scale},{-scale})"><path d="{d}" fill="{INK}" fill-rule="nonzero"/></g>')
        parts.append(f'<text x="{x+4}" y="{pad+14}" fill="{DIM}" font-family="monospace" font-size="12">{n} · adv {g["adv"]}</text>')
        x += adv + pad
    W = int(x)
    lines = [(0, 'baseline'), (CAP, 'cap'), (CAP + 10, ''), (-10, '')]
    guides = "".join(f'<line x1="{pad/2}" y1="{base - y*scale}" x2="{W-pad/2}" y2="{base - y*scale}" stroke="{ACC}" stroke-opacity="{0.6 if l else 0.25}" stroke-width="0.8"/>'
                     + (f'<text x="4" y="{base - y*scale - 3}" fill="{ACC}" font-family="monospace" font-size="10">{l}</text>' if l else '') for y, l in lines)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="{BG}"/>{guides}{"".join(parts)}</svg>'
    open(path, 'w').write(svg)

def overlay(path, S=9):
    """The font's A and O mapped back into the source's coordinates (points), drawn over the source objects."""
    W, H = SRC['w'], SRC['h']
    gA, gO = G['glyphs']['A'], G['glyphs']['O']; nA, nO = gA['notes'], gO['notes']
    # inverse of build_A: undo x_shift and scale, then rotate back about the apex
    def inv_A(p):
        q = ((p[0] - nA['x_shift']) / nA['scale'] + nA['apex_source'][0], p[1] / nA['scale'] + nA['y_feet_source'])
        return add(rot(sub(q, nA['apex_source']), -nA['rotated_by_deg']), nA['apex_source'])
    def inv_O(p):
        return add(mul(sub(p, nO['centre']), 1/nO['scale']), (nO['source_outer'][0], nO['source_outer'][1]))
    src = "".join(f'<path d="{" ".join(c.to_svg() for c in source_contours(o["items"]))}" fill="{INK}" fill-opacity="0.35" fill-rule="nonzero"/>' for o in SRC['objects'] if o['role'] != 'white')
    dA = " ".join(Contour.from_json(c).map(inv_A).to_svg() for c in gA['contours'])
    dO = " ".join(Contour.from_json(c).map(inv_O).to_svg() for c in gO['contours'])
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}"><rect width="100%" height="100%" fill="{BG}"/>'
           f'<g transform="translate(0,{H*S}) scale({S},{-S})">{src}'
           f'<path d="{dO}" fill="none" stroke="{ACC}" stroke-width="{2.2/S}" fill-rule="nonzero"/>'
           f'<path d="{dA}" fill="none" stroke="{RED}" stroke-width="{2.2/S}" fill-rule="nonzero"/></g>'
           f'<text x="8" y="20" fill="{INK}" font-family="monospace" font-size="13">source objects (light) · font O (blue) · font A (red), both mapped back to the source frame</text></svg>')
    open(path, 'w').write(svg)

os.makedirs(os.path.join(HERE, 'build'), exist_ok=True)
names = [n for n in ['A', 'O'] if n in G['glyphs']] + sorted(n for n in G['glyphs'] if n not in ('A', 'O'))
sheet(names, args.out)
if args.overlay and 'A' in G['glyphs'] and 'O' in G['glyphs']:
    overlay(os.path.join(os.path.dirname(args.out), 'overlay.svg'))
for n in [n for n in ('A', 'O') if n in G['glyphs'] and args.overlay]:
    print(f"  {n}: " + json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in G['glyphs'][n]['notes'].items()
                                    if k in ('scale', 'lean_deg', 'foot_level_residual_font', 'leg_L_width_foot_apex', 'leg_R_width_foot_apex', 'apex_angle', 'cut_angles', 'leg_angles', 'width_thick', 'width_thin', 'width_mean', 'offset_len', 'offset_dir_deg', 'r_in', 'r_out')}))
print(f"  wrote {os.path.relpath(args.out, HERE)}" + (" and overlay.svg" if args.overlay else ""))
