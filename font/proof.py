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

def overlay(path, S=9, PAD=4.0):
    """The font's A and O mapped back into the source's coordinates (points), drawn over the source objects.

    The frame is the BBOX of everything drawn, padded -- not the source artboard.  The artboard is
    100x100 and the mapped-back A runs past it on three sides (its apex overshoots the cap line by
    OVER_POINT and its feet sit below the baseline), so an artboard-sized frame cut the apex off.
    """
    W, H = SRC['w'], SRC['h']
    gA, gO = G['glyphs']['A'], G['glyphs']['O']; nA, nO = gA['notes'], gO['notes']
    # inverse of build_A: undo x_shift and scale, then rotate back about the apex
    def inv_A(p):
        q = ((p[0] - nA['x_shift']) / nA['scale'] + nA['apex_source'][0], p[1] / nA['scale'] + nA['y_feet_source'])
        return add(rot(sub(q, nA['apex_source']), -nA['rotated_by_deg']), nA['apex_source'])
    def inv_O(p):
        return add(mul(sub(p, nO['centre']), 1/nO['scale']), (nO['source_outer'][0], nO['source_outer'][1]))
    # One path per layer, not one per object: three overlapping 0.35 fills compounded to 0.72
    # where the A crossed the ring, which read as a defect.  Winding is already right in both
    # the source and the glyphs (counters wound against their outers), so nonzero unions them.
    src = " ".join(c.to_svg() for o in SRC['objects'] if o['role'] != 'white'
                              for c in source_contours(o['items']))
    dA = " ".join(Contour.from_json(c).map(inv_A).to_svg() for c in gA['contours'])
    dO = " ".join(Contour.from_json(c).map(inv_O).to_svg() for c in gO['contours'])
    pts = [q for o in SRC['objects'] if o['role'] != 'white'
             for c in source_contours(o['items']) for q in c.flatten()]
    pts += [q for c in gA['contours'] for q in Contour.from_json(c).map(inv_A).flatten()]
    pts += [q for c in gO['contours'] for q in Contour.from_json(c).map(inv_O).flatten()]
    x0 = min(q[0] for q in pts) - PAD; x1 = max(q[0] for q in pts) + PAD
    y0 = min(q[1] for q in pts) - PAD; y1 = max(q[1] for q in pts) + PAD - 2.4
    W, H = x1 - x0, y1 - y0
    cap = ('source (grey) &#183; font O (blue) &#183; font A (red), mapped back to the source frame. '
           'Where a coloured edge hugs the grey, they register.')
    note1 = ('Apex 0.000 pt off, counter apex 0.069. The four FOOT vertices sit 0.83-0.89 off, and cannot '
             'do better: the source A&#8217;s two feet differ by 8.54 pt in y and build_A levels them.')
    note2 = ('The two small red shapes on the legs are the ring&#8217;s tails, which continue behind the legs '
             'in the font and have no counterpart in the source A.')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S:.0f}" height="{H*S+62:.0f}">'
           f'<rect width="100%" height="100%" fill="{BG}"/>'
           f'<g transform="translate({-x0*S:.2f},{y1*S:.2f}) scale({S},{-S})">'
           f'<path d="{src}" fill="{INK}" fill-opacity="0.42" fill-rule="nonzero"/>'
           f'<path d="{dO}" fill="none" stroke="{ACC}" stroke-width="{2.0/S}"/>'
           f'<path d="{dA}" fill="none" stroke="{RED}" stroke-width="{2.0/S}"/>'
           f'</g>'
           f'<text x="10" y="{H*S+20:.0f}" fill="{INK}" font-family="monospace" font-size="12">{cap}</text>'
           f'<text x="10" y="{H*S+38:.0f}" fill="#8FA3B0" font-family="monospace" font-size="11">{note1}</text>'
           f'<text x="10" y="{H*S+54:.0f}" fill="#8FA3B0" font-family="monospace" font-size="11">{note2}</text>'
           f'</svg>')
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
