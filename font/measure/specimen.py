"""A specimen sheet for review: the set at several sizes, and the A and O on their source.

Writes measure/evidence/specimen.svg.  Rasterise it with measure/rasterize.mjs or any
headless browser; measure/evidence/specimen.png is the committed render.
"""
import json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
from pen import Contour

G = json.load(open(os.path.join(HERE, 'build', 'glyphs.json')))
CAP, GL = G['cap'], G['glyphs']
BG, INK, ACC, DIM = '#1D2B35', '#EEE5E9', '#2892D7', '#8b9fac'
NAME = {' ': 'space', '&': 'ampersand', '@': 'at', '.': 'period', ',': 'comma', '-': 'hyphen',
        '!': 'exclam', '?': 'question', '#': 'numbersign', '%': 'percent', '(': 'parenleft',
        ')': 'parenright', '[': 'bracketleft', ']': 'bracketright', '/': 'slash', '+': 'plus',
        '=': 'equal', ':': 'colon', ';': 'semicolon', '_': 'underscore', '*': 'asterisk',
        '"': 'quotedbl', "'": 'quotesingle'}
for d, n in zip('0123456789', ('zero one two three four five six seven eight nine').split()):
    NAME[d] = n

P = []
def txt(x, y, t, c=DIM, s=13):
    P.append(f'<text x="{x:.0f}" y="{y:.0f}" fill="{c}" font-family="monospace" font-size="{s}">{t}</text>')
def draw(t, x, base, S, col=INK):
    for ch in t:
        n = NAME.get(ch, ch); g = GL.get(n)
        if not g: continue
        d = " ".join(Contour.from_json(c).to_svg() for c in g['contours'])
        if d.strip():
            P.append(f'<g transform="translate({x:.2f},{base:.2f}) scale({S},{-S})"><path d="{d}" fill="{col}"/></g>')
        x += g['adv'] * S
    return x
def wid(t, S):
    return sum(GL[NAME.get(c, c)]['adv'] for c in t if NAME.get(c, c) in GL) * S

W = 1800; y = 44
txt(30, y, 'Orphan Display', INK, 22); y += 24
txt(30, y, f"{len(GL)} glyphs drawn from the AO mark: 26 uppercase, 10 figures, {len(GL)-36} punctuation.", DIM, 13); y += 34

# The alphabet at 92 does not fit 1800 wide on one line, so the large size is split;
# below that it fits, and each row gets a full line advance so nothing overlaps.
for size, lines in ((92, ('ABCDEFGHIJKLM', 'NOPQRSTUVWXYZ', '0123456789')),
                    (46, ('ABCDEFGHIJKLMNOPQRSTUVWXYZ', '0123456789')),
                    (27, ('ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789',)),
                    (17, ('ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789',))):
    txt(30, y, f'cap {size}px', ACC, 12); y += 8
    for line in lines:
        y += size + int(size * 0.30)
        draw(line, 34, y, size / CAP)
    y += 26

txt(30, y, 'punctuation', ACC, 12); y += 12
draw('&@#%*()[]{}.,:;!?"\'-+=/_', 34, y + 54, 54 / CAP); y += 96

txt(30, y, 'in words', ACC, 12); y += 12
for size, line in ((60, 'HAMBURGEFONS'), (44, 'ORPHAN DISPLAY & CO.'), (30, 'THE QUICK BROWN FOX JUMPS OVER 13 LAZY DOGS'),
                   (19, 'MEMBER WOMAN MINIMUM · BEACH PARAGRAPH GRAPHITE · 0123456789')):
    y += size + 10
    draw(line, 34, y, size / CAP)
    y += 14

H = int(y + 34)
open(os.path.join(HERE, 'measure', 'evidence', 'specimen.svg'), 'w').write(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
    f'<rect width="{W}" height="{H}" fill="{BG}"/>' + "".join(P) + '</svg>')
print(f"  wrote measure/evidence/specimen.svg  {W}x{H}")
