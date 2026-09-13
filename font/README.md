# Orphan Display

A typeface derived from the AO mark. `SPEC.md` is the design record: what the
mark is, measured from its Illustrator source, and every decision made in
turning its two letters into glyphs. This file is the build manual.

```
font/
  SPEC.md            the design record; read this first
  source/            AO.ai, favicon.ai, and ai_objects.json extracted from them
  measure/           extraction and verification scripts, with evidence/
  lib/pen.py         font-space geometry: strokes, rings, arcs, cubic contours
  lib/metrics.py     the typographic constants the mark cannot supply
  glyphs/core.py     O and A, built from the source geometry
  glyphs/set_*.py    every other glyph, built to the rules in SPEC §5
  build_glyphs.py    glyph modules -> build/glyphs.json
  compile_font.py    build/glyphs.json -> build/OrphanDisplay-Regular.otf
  build_variable.py  18 masters -> build/OrphanDisplay-VF.ttf, and installs public/fonts/
  proof.py           specimen sheet and source overlay -> build/*.svg
```

## Building

Two interpreters are involved because the fontforge module ships with
Homebrew's Python while the geometry needs numpy and friends:

```bash
brew install fontforge                       # provides `python3 -c "import fontforge"`
python3 -m venv font/venv && font/venv/bin/pip install -r font/requirements.txt

font/venv/bin/python font/measure/extract_ai.py   # source/*.ai -> source/ai_objects.json
font/venv/bin/python font/build_glyphs.py         # -> build/glyphs.json
python3 font/compile_font.py                      # -> build/OrphanDisplay-Regular.otf
font/venv/bin/python font/proof.py --overlay      # -> build/proof.svg, build/overlay.svg
node font/measure/rasterize.mjs font/build/proof.svg font/build/overlay.svg
```

`rasterize.mjs` renders SVG through a Chrome listening on `CDP_PORT`
(default 9222); start one with `--remote-debugging-port=9222 --headless`.

## The variable font

The site's specimen at `/design/ao/typeface/` loads the variable font, not the
static one. It is built from the 18 masters on the WEIGHT x PUSH grid:

```bash
font/venv/bin/python font/build_variable.py            # ~6 min, 18 masters
font/venv/bin/python font/build_variable.py --quick    # corners only, for a smoke test
```

This writes `build/OrphanDisplay-VF.ttf` **and installs it** over
`public/fonts/OrphanDisplay-VF.{ttf,woff2}`, which is what the site serves. Do
not hand-copy it: that step used to be manual and was missed twice, shipping a
font whose weight axis moved 52 of 89 glyphs while the sources had long since
fixed all 89.

Before saving, `_freeze_unverified` instantiates the font at each master's own
location and drops the `gvar` entry of any glyph that does not come back
exactly. A frozen glyph is pinned at the default rather than wrong halfway along
the axis, so freezing is the safe outcome, not a build failure — but it does
mean that letter will not respond to the sliders. The build prints what it
froze; `measure/vf_roundtrip.py` runs the same check standalone. If a letter
stops responding to weight on the specimen page, that list is the first place to
look, and a stale `public/fonts/` copy is the second.

To work on one glyph module at a time, every step takes an input/output pair:

```bash
font/venv/bin/python font/build_glyphs.py --only core,set_round --out font/build/set_round.json
python3 font/compile_font.py --in font/build/set_round.json --out font/build/set_round.otf
font/venv/bin/python font/proof.py --in font/build/set_round.json --out font/build/proof_round.svg
```

## Verifying

- `measure/reconstruct.py` rebuilds the whole mark from the fitted parameters
  and scores it against the site's SVG path by intersection-over-union
  (currently 0.99). If a measurement is wrong, `evidence/reconstruct_diff.png`
  shows where.
- `proof.py`'s overlay maps the font's A and O back into the source frame and
  draws them over the source objects. Apart from the levelled left foot they
  must coincide.
