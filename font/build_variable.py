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
from fontTools.varLib import instancer

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
    # Keep this master's own outlines too.  The OTF is the compiler's version of them, and
    # the compiler runs removeOverlap: a boolean whose output point count depends on the
    # geometry, so the same glyph comes back with 20 points at one weight and 18 at another
    # even when the source is identical in both.  That was the real reason two thirds of the
    # alphabet would not interpolate.  The VF is built from these instead.
    shutil.copyfile(os.path.join(BUILD, 'glyphs.json'), out_otf[:-4] + '.json')


def _split_contours(rec):
    """A recording as a list of contours, each [(op, args), ...] ending in closePath."""
    out, cur = [], []
    for op, args in rec:
        cur.append((op, args))
        if op in ('closePath', 'endPath'):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def _contour_key(con):
    """Where a contour sits and how big it is, for matching it across masters."""
    pts = [con[0][1][0]] + [a[-1] for op, a in con[1:-1] if a]
    n = len(pts) or 1
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    run = sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 for a, b in zip(pts, pts[1:]))
    return (cx, cy, run)


def _match_contours(cons, ref):
    """Reorder one master's contours onto the reference's, by position and size.

    The compiler does not promise an order.  Two masters of the same glyph can come back with
    their contours written in different sequences, and pairing them by index then compares a
    bowl against a stem -- which is what B looked like: 'llccclclcc' against 'cccclllcccccc'.
    """
    if len(cons) != len(ref):
        return None
    keys, rkeys = [_contour_key(c) for c in cons], [_contour_key(c) for c in ref]
    out, used = [None] * len(ref), set()
    for i, rk in enumerate(rkeys):
        best, bj = None, None
        for j, k in enumerate(keys):
            if j in used:
                continue
            d = ((k[0] - rk[0]) ** 2 + (k[1] - rk[1]) ** 2) ** 0.5 + abs(k[2] - rk[2])
            if best is None or d < best:
                best, bj = d, j
        out[i] = cons[bj]; used.add(bj)
    return out


def _poly(body, start, per=4):
    """The contour as a dense closed polyline, and the arc position of each segment end."""
    pts, marks, p = [start], [], start
    for op, args in body:
        if op == 'lineTo':
            pts.append(args[0]); p = args[0]
        elif op == 'curveTo':
            c1, c2, q = args
            for k in range(1, per + 1):
                t = k / float(per); m = 1 - t
                pts.append((m ** 3 * p[0] + 3 * m * m * t * c1[0] + 3 * m * t * t * c2[0] + t ** 3 * q[0],
                            m ** 3 * p[1] + 3 * m * m * t * c1[1] + 3 * m * t * t * c2[1] + t ** 3 * q[1]))
            p = q
        else:
            if args: pts.append(args[-1]); p = args[-1]
        marks.append(len(pts) - 1)
    return pts, marks


def _resample(pts, K=64):
    d = [0.0]
    for a_, b_ in zip(pts, pts[1:]):
        d.append(d[-1] + ((b_[0] - a_[0]) ** 2 + (b_[1] - a_[1]) ** 2) ** 0.5)
    total = d[-1] or 1.0
    out = []
    for i in range(K):
        want = total * i / K
        j = 0
        while j < len(d) - 2 and d[j + 1] < want:
            j += 1
        span = d[j + 1] - d[j] or 1.0
        t = (want - d[j]) / span
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t,
                    pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t))
    return out


def _rotate_onto(body, start, ref_body, ref_start):
    """The same closed contour, begun where the reference begins.

    A contour is a loop and nothing promises two masters begin it in the same place.  Align
    them as written and segment 0 of one is compared with segment 0 of the other although
    they are half the letter apart -- which is how B came back 700 units out, most of the cap
    height, with the point counts matching perfectly.

    The shift is chosen by resampling both contours evenly and taking the cyclic offset that
    puts them closest overall, not by finding the nearest single point: the nearest point is
    ambiguous wherever a letter is nearly symmetric, and picking it per-contour unfroze B and
    broke M.
    """
    K = 64
    A_ = _resample(_poly(ref_body, ref_start)[0], K)
    pts, marks = _poly(body, start)
    B_ = _resample(pts, K)
    best, bk = None, 0
    for k in range(K):
        c = sum((A_[i][0] - B_[(i + k) % K][0]) ** 2 + (A_[i][1] - B_[(i + k) % K][1]) ** 2
                for i in range(0, K, 2))
        if best is None or c < best:
            best, bk = c, k
    want = len(pts) * bk / float(K)                 # back to a real segment boundary
    j = min(range(len(marks)), key=lambda i: abs(marks[i] - want))
    if marks[j] == len(pts) - 1 or j == len(marks) - 1:
        return body, start
    return body[j + 1:] + body[:j + 1], pts[marks[j]]


def _positions(body, start):
    """Where each segment ENDS, as a fraction of the contour's own length.

    Straight-line distance between on-curve points is enough: it only has to say which
    segment of one master corresponds to which of another, not measure anything.
    """
    pts, p = [], start
    for op, args in body:
        p = args[-1] if args else p
        pts.append(p)
    d, run = [0.0], 0.0
    prev = start
    for q in pts:
        run += ((q[0] - prev[0]) ** 2 + (q[1] - prev[1]) ** 2) ** 0.5
        d.append(run); prev = q
    total = d[-1] or 1.0
    return [x / total for x in d[1:]]


def _embed(short, long_, ps, pl):
    """Which segment of `long_` each segment of `short` is, or None if it cannot be said.

    A short master is missing segments, not built differently, so its sequence should be a
    SUBSEQUENCE of the longest master's.  The alignment picks the embedding whose segments sit
    at the most similar places along the contour, so an inserted point lands where the master
    actually lacks one rather than wherever the kinds happen to line up.
    """
    n, m = len(short), len(long_)
    if n > m:
        return None
    INF = float('inf')
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    bt = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1]; bt[0][j] = 'skip'
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if short[i - 1][0] == long_[j - 1][0] and dp[i - 1][j - 1] < INF:
                c = dp[i - 1][j - 1] + abs(ps[i - 1] - pl[j - 1])
                if c < dp[i][j]: dp[i][j] = c; bt[i][j] = 'take'
            if dp[i][j - 1] < dp[i][j]:
                dp[i][j] = dp[i][j - 1]; bt[i][j] = 'skip'
    if dp[n][m] == INF:
        return None
    out, i, j = [None] * m, n, m
    while j > 0:
        if bt[i][j] == 'take':
            out[j - 1] = i - 1; i -= 1; j -= 1
        else:
            j -= 1
    if i != 0:
        return None          # some of the master's own segments were never placed
    # Every segment of the master must appear exactly once, in order: a skipped one is a
    # piece of the letter silently deleted, which is how B came back 700 units out with its
    # point counts matching perfectly.
    taken = [k for k in out if k is not None]
    if taken != list(range(n)):
        return None
    return out


def _as_curves(body, start):
    """Every segment as a curveTo, straight ones included.

    Some edges are a line in one master and a curve in another -- an arc that flattens, a cut
    that lands on a tangent -- and then neither sequence is a subsequence of the other, so
    there is nothing to align.  A straight line IS a cubic whose controls lie on it, at a
    third and two thirds, so rewriting them all as curves costs two points on the straight
    ones and makes every master's sequence the same kind the whole way down.  Only the
    counts are then left to reconcile.
    """
    out, p = [], start
    for op, args in body:
        if op == 'lineTo':
            q = args[0]
            c1 = (p[0] + (q[0] - p[0]) / 3.0, p[1] + (q[1] - p[1]) / 3.0)
            c2 = (p[0] + 2 * (q[0] - p[0]) / 3.0, p[1] + 2 * (q[1] - p[1]) / 3.0)
            out.append(('curveTo', (c1, c2, q))); p = q
        else:
            out.append((op, args)); p = args[-1]
    return out


def _degenerate(op, at):
    """A segment of the same kind that goes nowhere, sitting on the point we are already at."""
    if op == 'lineTo':
        return (op, (at,))
    if op == 'curveTo':
        return (op, (at, at, at))
    if op == 'qCurveTo':
        return (op, (at, at))
    return None


def align_masters(recs):
    """Make every master's recording of one glyph have the same segments, in the same order.

    Some outlines come back with a segment more or fewer depending on the knobs -- a cut that
    lands in a different segment, an arc that crosses a split boundary.  varLib cannot
    interpolate those and drops the glyph; twenty-four letters were frozen at the default.

    The shapes agree, so what is missing is points, not geometry.  This inserts ZERO-LENGTH
    segments where a master is short, which adds points without moving any edge: duplicate
    points are ordinary in interpolable outlines and invisible once filled.

    Returns the aligned recordings, or None if the masters really do differ in construction --
    a different number of contours, or a sequence that is not a subsequence of the longest.
    Alignment is verified by measure/vf_roundtrip.py, which rebuilds every master from the
    variable font at its own axis location: pair the points wrongly and it cannot come back.
    """
    why = os.environ.get('ORPHAN_ALIGN_DEBUG')
    splits = [_split_contours(r) for r in recs]
    if len({len(c) for c in splits}) != 1:
        if why: print('      contour COUNT differs: %s' % sorted({len(c) for c in splits}))
        return None
    # Pick the master with the most segments overall as the reference, then put every other
    # master's contours into its order before comparing anything.
    ref_m = max(range(len(splits)), key=lambda i: sum(len(c) for c in splits[i]))
    for mi in range(len(splits)):
        if mi == ref_m:
            continue
        m = _match_contours(splits[mi], splits[ref_m])
        if m is None:
            if why: print('      contour count differs after matching')
            return None
        splits[mi] = m

    out = [[] for _ in recs]
    for ci in range(len(splits[0])):
        cons = [sp[ci] for sp in splits]
        if any(c[0][0] != 'moveTo' for c in cons):
            return None
        bodies0 = [c[1:-1] for c in cons]
        tails = [c[-1] for c in cons]
        starts = [c[0][1][0] for c in cons]

        def attempt(bodies):
            """Every master's version of this contour, made the same length, or None."""
            ref = max(range(len(bodies)), key=lambda i: len(bodies[i]))
            pl = _positions(bodies[ref], starts[ref])
            built_all = []
            for mi, body in enumerate(bodies):
                if mi == ref:
                    built_all.append([cons[mi][0]] + list(body) + [tails[mi]]); continue
                emb = _embed(body, bodies[ref], _positions(body, starts[mi]), pl)
                if emb is None:
                    return None
                built, at = [cons[mi][0]], starts[mi]
                for j, take in enumerate(emb):
                    if take is None:
                        d = _degenerate(bodies[ref][j][0], at)
                        if d is None:
                            return None
                        built.append(d)
                    else:
                        built.append(body[take]); at = body[take][1][-1]
                built.append(tails[mi])
                built_all.append(built)
            return built_all

        got = attempt(bodies0)
        if got is None:
            # The masters disagree about which segments are straight.  Say it all in curves
            # and try once more -- promoting partway through would align the early masters
            # against one reference and the rest against another.
            got = attempt([_as_curves(b, st) for b, st in zip(bodies0, starts)])
        if got is None:
            if why:
                print('      contour %d cannot be aligned; kinds %s'
                      % (ci, sorted({''.join(o[0][0] for o in b) for b in bodies0})[:2]))
            return None
        for mi, built in enumerate(got):
            out[mi].append(built)
    return [[op for con in g for op in con] for g in out]


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
    sources = [json.load(open(s[:-4] + '.json'))['glyphs'] for s in srcs]
    for f in fonts:
        if f.getGlyphOrder() != order:
            raise SystemExit('masters disagree about the glyph order')
    sets = [f.getGlyphSet() for f in fonts]

    def draw_source(glyphs, name, pen):
        """Replay a glyph's own contours, unmerged, the way build_glyphs left them.

        Overlapping contours are fine in a variable font -- the rasteriser fills them with
        the non-zero rule and the spec has a flag to say so -- and they are the only version
        of the outline that is the same shape in every master.
        """
        g = glyphs.get(name) or glyphs.get(name.upper())
        if not g:
            return False
        for c in g['contours']:
            pen.moveTo(tuple(c['start']))
            for sg in c['segs']:
                if sg[0] == 'l':
                    pen.lineTo(tuple(sg[1]))
                else:
                    pen.curveTo(tuple(sg[1]), tuple(sg[2]), tuple(sg[3]))
            pen.closePath()
        return True
    glyfs = []
    for f in fonts:
        g = newTable('glyf'); g.glyphOrder = order; g.glyphs = {}
        glyfs.append(g)
    from fontTools.pens.cu2quPen import Cu2QuPen
    incompatible, aligned = [], []
    for name in order:
        recs = []
        for gs, glyphs in zip(sets, sources):
            rp = RecordingPen()
            if not draw_source(glyphs, name, rp):
                gs[name].draw(rp)                    # .notdef and space: no source of our own
            recs.append(rp.value)
        if len({tuple(op for op, _ in r) for r in recs}) != 1:
            if os.environ.get('ORPHAN_ALIGN_DEBUG'): print('    %s:' % name)
            fixed = align_masters(recs)
            if fixed is not None and len({tuple(op for op, _ in r) for r in fixed}) == 1:
                recs = fixed
                aligned.append(name)
        if len({tuple(op for op, _ in r) for r in recs}) != 1:
            # A genuine incompatibility: this glyph's CONSTRUCTION changes shape with the knobs,
            # so no conversion can make its masters interpolate.  Convert each on its own and let
            # varLib freeze it, but say so rather than leaving it to a warning in the noise.
            incompatible.append(name)
            for gs, g in zip(sets, glyfs):
                pen = TTGlyphPen(None, outputImpliedClosingLine=True)
                gs[name].draw(Cu2QuPen(pen, MAX_ERR))
                g[name] = pen.glyph()
            continue
            # outputImpliedClosingLine: the pen drops a contour's closing line when the last
            # point lands exactly on the first, because it is then redundant.  Whether it
            # lands exactly there is ROUNDING, so the point count stops being structural --
            # eight and six came out 182 points at most weights and 181 at three of them, and
            # varLib dropped them for it.  Emitting it always costs one point and makes the
            # count depend on the outline rather than on where the decimals fell.
        pens = [TTGlyphPen(None, outputImpliedClosingLine=True) for _ in fonts]
        multi = Cu2QuMultiPen(pens, MAX_ERR)
        for ops in zip(*recs):
            op = ops[0][0]
            getattr(multi, op)([o[1] for o in ops]) if op not in ('closePath', 'endPath') \
                else getattr(multi, op)()
        for g, pen in zip(glyfs, pens):
            g[name] = pen.glyph()
    if aligned:
        print(f'  {len(aligned)} glyphs had a segment inserted to make their masters line up: '
              f'{" ".join(aligned)}')
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
    # Put build/glyphs.json back to the default cut.  run_master calls build_glyphs.py without
    # --out, so every master overwrites it and the LAST one -- WEIGHT 2.00, PUSH 1.00 -- is what it
    # holds when this finishes.  Everything downstream reads that path and says nothing: the
    # specimen sheet was published as the Black master once already, and measure/axes.py carries
    # the same restore for the same reason.
    subprocess.run([sys.executable, os.path.join(HERE, 'build_glyphs.py')],
                   check=True, cwd=HERE, capture_output=True,
                   env={k: v for k, v in os.environ.items() if k not in ('ORPHAN_WEIGHT', 'ORPHAN_PUSH')})

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
    # The masters keep their overlaps -- that is the point of building from the sources
    # rather than the compiler's merged outlines -- so say so.  OVERLAP_SIMPLE tells a
    # rasteriser the contours may overlap and to fill them non-zero, which is what they all
    # do anyway; without it a conservative one is entitled to drop the overlaps out.
    from fontTools.ttLib.tables import _g_l_y_f as _glyf_mod
    flag = getattr(_glyf_mod, 'flagOverlapSimple', 0x40)
    glyf = vf['glyf']
    for gname in glyf.keys():
        g = glyf[gname]
        if g.numberOfContours > 0 and getattr(g, 'flags', None) is not None and len(g.flags):
            g.flags[0] |= flag

    out = os.path.join(BUILD, 'OrphanDisplay-VF.ttf')
    vf.save(out)
    if not os.environ.get('ORPHAN_NO_FREEZE'):
        _freeze_unverified(out, made)
    print(f'  wrote {os.path.relpath(out, HERE)}  ({os.path.getsize(out)//1024} KB)')


def _freeze_unverified(vf_path, made):
    """Drop the variations of any glyph the font cannot reproduce at a master's own location.

    align_masters inserts points to make masters compatible, and that is a HEURISTIC: it has
    to decide which segment of one master is which segment of another.  Get it wrong and the
    counts still match, varLib still builds, and the letter is quietly wrong somewhere in the
    middle of the axis -- the one failure nothing downstream would catch.

    So every glyph is checked, and any that does not come back exactly at each master's own
    location has its gvar entry removed.  That leaves it frozen at the default, which is
    where it already was; the font is never wrong, only sometimes less varied than hoped.
    measure/vf_roundtrip.py runs the same check standalone and prints what is still frozen.
    """
    sys.path.insert(0, os.path.join(HERE, 'measure'))
    import importlib
    rt = importlib.import_module('vf_roundtrip')
    from fontTools.ttLib import TTFont as _TT

    vf = _TT(vf_path)
    ax = rt.axis_map(vf)
    ws = sorted({w for w, _p, _f in made})
    ps = sorted({p for _w, p, _f in made})
    lerp = lambda v, lo, hi, a, b: a + (b - a) * (v - lo) / (hi - lo) if hi > lo else a
    bad = set()
    for w, p, ttf in made:
        loc = {'wght': lerp(w, ws[0], ws[-1], ax['wght'][0], ax['wght'][2]),
               'PUSH': lerp(p, ps[0], ps[-1], ax['PUSH'][0], ax['PUSH'][2])}
        inst = instancer.instantiateVariableFont(_TT(vf_path), loc)
        master = _TT(ttf)
        for name in master.getGlyphOrder():
            d = rt.compare(rt.outline(master, name), rt.outline(inst, name))
            if d is not None and d > rt.TOL:
                bad.add(name)
    if not bad:
        print('  every glyph reproduces its masters exactly')
        return
    gvar = vf['gvar'].variations
    for name in bad:
        gvar.pop(name, None)
    vf.save(vf_path)
    print(f'  {len(bad)} glyphs did not reproduce their masters and were left frozen: '
          f'{" ".join(sorted(bad))}')

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
