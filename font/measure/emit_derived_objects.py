"""Write an ai_objects-shaped description of the RE-DERIVED mark.

design/logo-animation/derive_geometry.py takes --ai and reads four things out of it: the ring's two
fitted circles, the A's six vertices, the hoop's path, and the swash's path.  Every geometric fact
in geometry.json comes from those, and the shipped path is used only to fit the transform -- which
is why re-deriving the mark left 251 of 256 values in geometry.json unchanged and the animation
still drawing the ARTWORK's weights underneath a heavier final layer.

Rather than teach derive_geometry about the font, this writes the same file shape with the
re-derived numbers in it, so `derive_geometry.py --ai <this>` produces animation geometry that
matches the mark the site actually draws.

What changes and what does not:

    ring.outer    unchanged -- R1 insets the counter and never moves the outer circle
    ring.inner    radius (r_out - r_in) * RING_GAIN in from the outer, displaced by the mark's
                  own offset also scaled by RING_GAIN, which is exactly what R1b does
    A.vertices    the font's A, mapped back into mark coordinates: the skeleton is unmoved but
                  the counter apex rises as the legs thicken
    bar.items     measure/hoop_derived's hoop, the artwork's outer edge with the inner edge moved
    white.items   measure/swash_derived's swash.  It is construction rather than ink, but it is
                  authored to span cut to cut -- head on the A's right foot cut, tail on the
                  hoop's hook face -- and both of those cuts moved, so leaving it alone would
                  have the write-on pen leave the foot 37% narrower than the foot it leaves

Writes design/logo-animation/ai_objects_derived.json.
"""
import json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'measure'))
import rules
from mark_derived import parts
from hoop_derived import derived_hoop_items
from swash_derived import derived_swash_items

SRC_PATH = os.path.join(HERE, 'source', 'ai_objects.json')
OUT = os.path.join(os.path.dirname(HERE), 'design', 'logo-animation', 'ai_objects_derived.json')


def contour_items(c):
    """A Contour back into the source's item format: ['c', p0, c1, c2, p3] / ['l', p0, p1]."""
    out, cur = [], c.start
    for sg in c.segs:
        if sg[0] == 'l':
            out.append(['l', list(cur), list(sg[1])]); cur = sg[1]
        else:
            out.append(['c', list(cur), list(sg[1]), list(sg[2]), list(sg[3])]); cur = sg[3]
    return out


def main():
    doc = json.load(open(SRC_PATH))
    page = doc['AO'][0]
    objs = {o['role']: o for o in page['objects']}
    a_poly, _o_out, _o_in, _hoop = parts()
    hoop_items, hoop_err = derived_hoop_items()
    g = rules.RING_GAIN

    ring = objs['ring']
    ox, oy, orad = ring['outer'][0], ring['outer'][1], ring['outer'][2]
    band = orad - ring['inner'][2]
    dx, dy = ring['inner'][0] - ox, ring['inner'][1] - oy
    new_inner = [ox + dx * g, oy + dy * g, orad - band * g] + list(ring['inner'][3:])

    verts = [list(a_poly.start)] + [list(s[-1]) for s in a_poly.segs]
    if len(verts) == 7 and verts[0] == verts[-1]:
        verts = verts[:6]
    swash_items, swash_rep = derived_swash_items(a_verts=verts, hoop_items=hoop_items)
    assert not swash_rep['gaps'], swash_rep['gaps']

    for o in page['objects']:
        if o['role'] == 'ring':
            o['inner'] = new_inner
        elif o['role'] == 'A':
            o['vertices'] = verts
            o['items'] = [['l', verts[i], verts[(i + 1) % len(verts)]] for i in range(len(verts))]
        elif o['role'] == 'bar':
            # the artwork's own 18-segment topology, because derive_geometry indexes the hoop by
            # position: bar[1:5] the top run, bar[5:7] the left hook, bar[7] its face, and so on
            o['items'] = hoop_items
        elif o['role'] == 'white':
            o['items'] = swash_items
    page['derived_from'] = dict(
        note='the mark re-derived from the typeface; see font/measure/emit_derived_objects.py',
        ring_gain=g, ring_band_mark_units=band * g, ring_offset_mark_units=(dx * g, dy * g),
        a_vertices=len(verts), bar_segments=len(hoop_items), hoop_fit_err=hoop_err,
        swash_head_cut_mark_units=swash_rep['head_cut'], swash_tail_face_mark_units=swash_rep['tail_face'])
    json.dump(doc, open(OUT, 'w'))
    print('  ring band  %.4f -> %.4f mark units  (gain %.4f)' % (band, band * g, g))
    print('  ring offset %.4f -> %.4f' % ((dx**2 + dy**2) ** .5, ((dx*g)**2 + (dy*g)**2) ** .5))
    print('  A vertices: %d, hoop segments: %d (worst single-cubic fit %.4f mark units)'
          % (len(verts), len(hoop_items), hoop_err))
    hc, tf = swash_rep['head_cut'], swash_rep['tail_face']
    print('  swash head cut  %.4f -> %.4f (x%.4f); tail face %.4f -> %.4f (x%.4f)'
          % (hc[0], hc[1], hc[1] / hc[0], tf[0], tf[1], tf[1] / tf[0]))
    print('  wrote %s' % os.path.relpath(OUT, os.path.dirname(HERE)))


if __name__ == '__main__':
    main()
