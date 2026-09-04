#!/usr/bin/env python3
"""build/glyphs.json -> build/OrphanDisplay-Regular.otf   (needs the fontforge Python module)"""
import argparse, json, os, sys
import fontforge
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('--in', dest='inp', default=os.path.join(HERE, 'build', 'glyphs.json'))
ap.add_argument('--out', default=os.path.join(HERE, 'build', 'OrphanDisplay-Regular.otf')); args = ap.parse_args()
G = json.load(open(args.inp))
FAMILY = "Orphan Display"
f = fontforge.font()
f.em = G['upm']; f.ascent = G['ascent']; f.descent = G['descent']
f.familyname = FAMILY; f.fontname = "OrphanDisplay-Regular"; f.fullname = FAMILY + " Regular"
f.weight = "Regular"; f.copyright = "Austin Orphan. Derived from the AO mark."
f.encoding = "UnicodeFull"
# line metrics pinned, not derived from whatever the glyph set's bounding box happens to be.
# fontforge treats these as offsets from f.ascent/f.descent unless the *_add flags are cleared.
for flag in ('hhea_ascent_add', 'hhea_descent_add', 'os2_typoascent_add', 'os2_typodescent_add', 'os2_winascent_add', 'os2_windescent_add'):
    setattr(f, flag, False)
f.hhea_ascent = G['ascent']; f.hhea_descent = -G['descent']; f.hhea_linegap = 0
f.os2_typoascent = G['ascent']; f.os2_typodescent = -G['descent']; f.os2_typolinegap = 0
f.os2_winascent = G['ascent']; f.os2_windescent = G['descent']
f.os2_capheight = G['cap']; f.os2_xheight = G['cap']          # unicase: the x-height is the cap height
f.os2_use_typo_metrics = True
for name, g in G['glyphs'].items():
    ch = f.createChar(g['cp'], name)
    pen = ch.glyphPen()
    for c in g['contours']:
        pen.moveTo(tuple(c['start']))
        for seg in c['segs']:
            if seg[0] == 'l': pen.lineTo(tuple(seg[1]))
            else:             pen.curveTo(tuple(seg[1]), tuple(seg[2]), tuple(seg[3]))
        pen.closePath()
    pen = None
    if g['contours']: ch.removeOverlap(); ch.correctDirection(); ch.round()
    ch.width = g['adv']
# unicase: lowercase reuses the capitals
for name, g in list(G['glyphs'].items()):
    if len(name) == 1 and 'A' <= name <= 'Z':
        lc = f.createChar(ord(name.lower()), name.lower())
        lc.addReference(name); lc.width = g['adv']
out = args.out
f.generate(out)
print(f"  wrote {out}: {sum(1 for _ in f.glyphs())} glyphs")
