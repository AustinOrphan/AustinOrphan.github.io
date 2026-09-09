#!/usr/bin/env python3
"""Build the variable font: masters at the corners of WEIGHT x PUSH, interpolated.

Each master is a full run of build_glyphs with the two knobs set, compiled to its own OTF by
compile_font, and the set is merged by fontTools' varLib into one variable font with two axes.

  WGHT  the stroke.  The axis that changes colour.
  PUSH  the O counter's displacement, i.e. CONTRAST.  Colour barely moves along it.

varLib needs every master to have the same glyph set and compatible outlines -- same number of
contours, same number of points, in the same order.  That holds here because every master is
the SAME CODE with different constants, so a curve that is a curve in one is a curve in all.
The exception is a glyph whose construction changes shape with the knobs; if one ever does,
this is where it will show up, as an interpolation error naming the glyph.

  venv/bin/python build_variable.py           # default grid
  venv/bin/python build_variable.py --quick   # corners only, for a fast check
"""
import argparse, json, os, subprocess, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_ERR = 0.6   # units of curve error allowed when going cubic -> quadratic
BUILD = os.path.join(HERE, 'build')
MASTERS = os.path.join(BUILD, 'masters')

# The grid. Weight is sampled at six points because colour is not linear in it; push at three,
# because it is nearly linear and three is enough to carry the ends and the middle.
#
# The buildable region, mapped rather than assumed -- measure/bowl_region.py draws the map.
# It used to be 0.85..1.45 x 0.30..1.00, and both of the things holding it there turned out to
# be the solver rather than the letters:
#
#   * the B's cap-line trim left a STRAIGHT chord across a round band, and a straight line
#     across a round band is the one path that heads for the counter. It now follows the band
#     (set_bowl._bury_edge), so its clearance is the band's own thin side rather than a chord's
#     worst case: 13.30 units at the mark against 8.54, and it holds until ROUND_THIN itself
#     runs out, which is the real ceiling.
#   * _wedge_x searched UNDAMPED. From the counter's right extreme its first step jumped clean
#     past the solution, and at that x the arm's inner edge missed the counter altogether -- so
#     the B failed at low push not because there was no wedge but because the search stepped
#     over it. Damped like _bar_bowl and _arm_bowl already were.
#
# With those two the whole 63-glyph set builds over 0.60..2.00 x 0.30..1.00, and 0.70..2.00 at
# push 1.00. The rectangle below is 0.70..2.00, which holds at every push in range. What stops
# it now is genuine: at push 0.12 the counter has moved so far from the cap line that the arm's
# inner edge never reaches it and there is no wedge to solve for, and past weight 2.00 the
# bowl's outer circle and its horizontal's outer edge stop meeting at all.
WEIGHTS = [0.70, 0.85, 1.00, 1.20, 1.45, 2.00]
PUSHES  = [0.30, 0.65, 1.00]

# What the sliders will say. wght follows the CSS convention (100..900) so a browser's own
# font-weight can drive it; PUSH is its own axis in its own units.
def wght_of(w):     return round(400 * w)          # 400 at the mark, so wght reads conventionally
def push_of(p):     return round(p * 100)

NAMED = [
    ('Thin',         0.70, 1.00), ('Light',        0.85, 1.00),
    ('Regular',      1.00, 1.00), ('Medium',       1.20, 1.00),
    ('Bold',         1.45, 1.00), ('Black',        2.00, 1.00),
    ('Regular Flat', 1.00, 0.30), ('Regular Soft', 1.00, 0.65),
    ('Light Flat',   0.85, 0.30), ('Bold Flat',    1.45, 0.30),
    ('Black Flat',   2.00, 0.30),
]

def run_master(weight, push, out_otf):
    env = dict(os.environ, ORPHAN_WEIGHT=str(weight), ORPHAN_PUSH=str(push))
    subprocess.run([sys.executable, os.path.join(HERE, 'build_glyphs.py')],
                   check=True, env=env, cwd=HERE, capture_output=True)
    # compile_font needs the fontforge interpreter, not this venv
    subprocess.run(['/opt/homebrew/bin/python3', os.path.join(HERE, 'compile_font.py')],
                   check=True, env=env, cwd=HERE, capture_output=True)
    shutil.copyfile(os.path.join(BUILD, 'OrphanDisplay-Regular.otf'), out_otf)


def to_ttf_all(srcs, dsts):
    """Re-record every master's outlines as quadratic, ALL OF THEM AT ONCE, and save the TTFs.

    varLib merges `glyf` cleanly; merging CFF means merging HINTS, and fontforge picks
    different hints for different masters, which it refuses ("hintmask at index 5 differs from
    the default font hint type"). Hints are per-instance rendering advice, not shape, so the
    outlines are what should survive. Converting here rather than dropping the hints in place
    keeps one code path instead of two.

    The conversion has to see every master together.  Cu2QuPen picks however many quadratic
    points a given curve needs, and that count depends on the curve, so converting each master on
    its own gave the same glyph different point counts in different masters -- and varLib then
    silently drops those glyphs from `gvar`: "glyph A has incompatible masters; skipping".  It
    was skipping 42 of the 63.  The axes moved the 21 that happened to convert alike and left the
    rest frozen at the default, which is most of the alphabet.  Cu2QuMultiPen solves the whole
    set at once instead, so every master gets the same points in the same order and every glyph
    varies.
    """
    from fontTools.ttLib import TTFont, newTable
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.cu2quPen import Cu2QuMultiPen
    from fontTools.pens.recordingPen import RecordingPen

    fonts = [TTFont(s) for s in srcs]
    order = fonts[0].getGlyphOrder()
    for f in fonts:
        if f.getGlyphOrder() != order:
            raise SystemExit('masters disagree about the glyph order')
    sets = [f.getGlyphSet() for f in fonts]
    glyfs = []
    for f in fonts:
        g = newTable('glyf'); g.glyphOrder = order; g.glyphs = {}
        glyfs.append(g)
    from fontTools.pens.cu2quPen import Cu2QuPen
    incompatible = []
    for name in order:
        recs = []
        for gs in sets:
            rp = RecordingPen(); gs[name].draw(rp); recs.append(rp.value)
        if len({tuple(op for op, _ in r) for r in recs}) != 1:
            # A genuine incompatibility: this glyph's CONSTRUCTION changes shape with the knobs,
            # so no conversion can make its masters interpolate.  Convert each on its own and let
            # varLib freeze it, but say so rather than leaving it to a warning in the noise.
            incompatible.append(name)
            for gs, g in zip(sets, glyfs):
                pen = TTGlyphPen(None)
                gs[name].draw(Cu2QuPen(pen, MAX_ERR))
                g[name] = pen.glyph()
            continue
        pens = [TTGlyphPen(None) for _ in fonts]
        multi = Cu2QuMultiPen(pens, MAX_ERR)
        for ops in zip(*recs):
            op = ops[0][0]
            getattr(multi, op)([o[1] for o in ops]) if op not in ('closePath', 'endPath') \
                else getattr(multi, op)()
        for g, pen in zip(glyfs, pens):
            g[name] = pen.glyph()
    if incompatible:
        print(f'  {len(incompatible)} glyphs differ in construction between masters and cannot '
              f'interpolate: {" ".join(incompatible)}')
    for f, g, dst in zip(fonts, glyfs, dsts):
        _save_ttf(f, g, order, dst)


def _save_ttf(f, glyf, order, dst):
    from fontTools.ttLib import TTFont, newTable
    f['glyf'] = glyf
    f['loca'] = newTable('loca')
    maxp = newTable('maxp')
    maxp.tableVersion = 0x00010000
    maxp.numGlyphs = len(order)
    # maxp 1.0 carries the TrueType interpreter's limits. Nothing here is hinted, so they are
    # all zero -- but they must be present or the table will not compile.
    for field in ('maxZones', 'maxTwilightPoints', 'maxStorage', 'maxFunctionDefs',
                  'maxInstructionDefs', 'maxStackElements', 'maxSizeOfInstructions',
                  'maxComponentElements', 'maxComponentDepth', 'maxPoints', 'maxContours',
                  'maxCompositePoints', 'maxCompositeContours'):
        setattr(maxp, field, 0)
    f['maxp'] = maxp
    f['glyf'].glyphOrder = order
    for tag in ('CFF ', 'VORG'):
        if tag in f: del f[tag]
    f.sfntVersion = '\x00\x01\x00\x00'
    f.save(dst)
    # recalc the limits now that the outlines are in place
    g = TTFont(dst)
    g['maxp'].recalc(g)
    g.save(dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true', help='corners only')
    args = ap.parse_args()
    weights = [WEIGHTS[0], WEIGHTS[2], WEIGHTS[-1]] if args.quick else WEIGHTS
    pushes  = [PUSHES[0], PUSHES[-1]] if args.quick else PUSHES

    os.makedirs(MASTERS, exist_ok=True)
    made, otfs = [], []
    for w in weights:
        for p in pushes:
            stem = f'master-w{int(w*100):03d}-p{int(p*100):03d}'
            otf = os.path.join(MASTERS, stem + '.otf')
            ttf = os.path.join(MASTERS, stem + '.ttf')
            print(f'  building weight {w} push {p} -> {stem}.ttf')
            run_master(w, p, otf)
            otfs.append(otf)
            made.append((w, p, ttf))
    # One conversion for the whole set, so the masters stay interpolation-compatible.
    print(f'  converting {len(otfs)} masters to quadratic together')
    to_ttf_all(otfs, [f for _, _, f in made])
    for f in otfs:
        os.remove(f)

    ds = os.path.join(MASTERS, 'OrphanDisplay.designspace')
    write_designspace(ds, made, weights, pushes)
    print(f'  wrote {os.path.relpath(ds, HERE)}')

    from fontTools.designspaceLib import DesignSpaceDocument
    from fontTools.varLib import build as varbuild
    doc = DesignSpaceDocument.fromfile(ds)
    vf, _, _ = varbuild(doc)
    out = os.path.join(BUILD, 'OrphanDisplay-VF.ttf')
    vf.save(out)
    print(f'  wrote {os.path.relpath(out, HERE)}  ({os.path.getsize(out)//1024} KB)')

def write_designspace(path, made, weights, pushes):
    def src(w, p, f):
        loc = f'<location><dimension name="Weight" xvalue="{wght_of(w)}"/>' \
              f'<dimension name="Push" xvalue="{push_of(p)}"/></location>'
        is_default = (w == 1.00 and p == 1.00)
        return (f'  <source filename="{os.path.basename(f)}" name="w{int(w*100)}p{int(p*100)}"'
                f'{" copyLib=\'1\' copyInfo=\'1\'" if is_default else ""}>\n    {loc}\n  </source>')
    inst = "\n".join(
        f'  <instance name="Orphan Display {n}" familyname="Orphan Display" stylename="{n}">\n'
        f'    <location><dimension name="Weight" xvalue="{wght_of(w)}"/>'
        f'<dimension name="Push" xvalue="{push_of(p)}"/></location>\n  </instance>'
        for n, w, p in NAMED)
    open(path, 'w').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<designspace format="4.1">
 <axes>
  <axis tag="wght" name="Weight" minimum="{wght_of(min(weights))}" maximum="{wght_of(max(weights))}" default="{wght_of(1.00)}"/>
  <axis tag="PUSH" name="Push" minimum="{push_of(min(pushes))}" maximum="{push_of(max(pushes))}" default="{push_of(1.00)}"/>
 </axes>
 <sources>
{chr(10).join(src(w, p, f) for w, p, f in made)}
 </sources>
 <instances>
{inst}
 </instances>
</designspace>
''')

if __name__ == '__main__':
    main()
