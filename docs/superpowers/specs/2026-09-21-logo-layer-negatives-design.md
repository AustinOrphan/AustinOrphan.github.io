# Every layer, positive or negative, with a cut through any subset

**Date:** 2026-09-21
**Status:** drafted, awaiting review

## Problem

The mark has three paint layers — ink, shadow, outline — and one of them, ink, can currently
be rendered as a knockout: a field with the letterform punched out of it. The other two
cannot. The request is for any of the three to knock out, in any combination, plus a master
cut that can pass through any subset of them.

Each new treatment so far has cost a new element. `cut` added the band holder, `knock` added
the field, making the cut reach the shadow added a second offset copy. That is five ad-hoc
holders for four states, and the reason is structural:

**A `mask` is an attribute carrying a per-instance id, so CSS cannot toggle it.** Every
treatment therefore needs its own pre-rendered element, shown or hidden by class. Six more
booleans would mean a dozen more elements and a copy of the 3.3KB mark path in each.

## The mechanism

A mask's *contents* are ordinary SVG and can be styled. A shape painted white inside a mask
is a no-op; painted black it punches. So one masked rect per layer, with the mask's contents
driven by classes on the root, expresses every combination with no duplicated markup.

Each layer becomes exactly one `<rect>` filled in that layer's colour and masked by a mask
holding three things:

```
<mask class="lm lm-<layer>">
  <rect class="lm-field" />     <!-- black normally, white when the layer is a negative -->
  <shape class="lm-shape" />    <!-- white normally, black when the layer is a negative -->
  <glyph class="lm-cut" />      <!-- none normally, black when the cut passes through -->
</mask>
```

- **positive**: field black, shape white → the layer paints its own shape.
- **negative**: field white, shape black → the layer paints everything *except* its shape.
- **cut**: an extra black glyph at the home position → subtract the letterform as well.

The body then carries no copies of the path at all — only rects. Seven copies live in the
three masks, against five holders today.

## The layer model

| layer | its shape | colour |
| --- | --- | --- |
| ink | the glyph | `--logo-ink` |
| shadow | the glyph, offset and scaled by `--logo-shadow-t` | `--logo-shadow` |
| outline | the band: the stroke at `--logo-band` minus the glyph | `--logo-outline` |

Each gets two independent flags, `negative` and `cut`, so the region a layer paints is

```
region(L) = (negative ? BOX - shape(L) : shape(L)) - (cut ? glyph : nothing)
```

The band's shape needs two passes of its own inside the mask — stroke white, glyph black —
because the band is already a subtraction.

## Stacking

A shadow belongs **behind** a solid glyph and **on top of** a knocked-out field. That was
settled by hand once already, and it is not a preference: with a full-bleed field below it,
a shadow drawn underneath is invisible except through the hole, which makes the letterform a
window onto a coloured shape rather than a cut through the card.

SVG has no `z-index`, so the shadow and the band each get an **under** and an **over** slot
and exactly one of each pair is drawn, keyed on whether the ink layer is a negative. Five
rects in total:

```
shadow(under) · band(under) · ink · shadow(over) · band(over)
```

## Combinations that do nothing

A space this size has dead corners, and they should be named rather than discovered:

- **positive ink + cut** paints nothing. Cutting the glyph out of the glyph leaves an empty
  set. Correct, and useless.
- **positive band + cut** is a no-op. The band lies entirely outside the glyph, so the cut
  removes nothing from it. It only bites once the band is a negative.
- **negative anything + cut** is a no-op for that layer's own glyph-shaped region, which is
  already subtracted — except for the shadow, whose shape is offset, so the cut does bite.

The bench should grey these out rather than offer a control that changes nothing, the way it
already hides the band and shadow fieldsets when their layers are off.

## Export

This wants checking rather than assuming, and it is the most likely place for a surprise.

`serializeLogo` copies computed `fill` and `stroke`, and it walks into `<defs>`. The mask
contents are styled by CSS, so their fills should be read back and written on as attributes
exactly like any other paint — which would mean the export carries the right mask for free,
with no new code. `pruneUnusedDefs` keeps all three masks, since all three are referenced.

If that holds, this change costs the exporter nothing. If it does not, the fallback is to
write the mask fills explicitly the way `flattenPaintOrder` writes the outline.

## Bench

Per layer: **on**, **negative**, **cut**. Ink has no `on` — something must be painted — so
eight toggles in total, against the current four. Grouped by layer rather than by flag, so
each fieldset reads as one layer's full state.

The variant presets stay as they are: they name combinations of *on*, and say nothing about
negatives, which remain export treatments with no site use.

## What this replaces

`site-logo-knock-holder`, `site-logo-cut-holder`, `site-logo-shadow-holder`,
`site-logo-shadow-knocked`, `site-logo-shadow-offset` and their rules all go, along with the
`-cut`, `-knock` and `-knockvb` masks. The `cut` and `knock` props become `negative` flags
per layer; `layerClasses` grows to emit them.

`treatable` stays and means the same thing: ship the masks even when nothing uses them yet,
which only the bench needs.

## Risk

The combination space is 2^6 before the on/off flags. Verification should be a rendered grid
of every reachable combination over a checkerboard, not a spot check — the last two defects
here were both invisible at a glance and both needed a deliberately exaggerated parameter to
show up. The shadow's cut only became visible at a 140-unit throw.
