# Splitting `/design/ao/logo/`: a publication and an instrument

**Date:** 2026-09-20
**Status:** drafted, awaiting review

## Problem

`/design/ao/logo/` does two unrelated jobs in one document. It explains the
mark to a reader, and it is the bench the mark is configured and exported
from. The two have different audiences, different readiness, and opposite
answers to whether they should ever be public.

The cost is measurable. The built page is 647KB, carrying 25 rendered marks
and 134 masks. It is also where five separate hazards live, each documented in
CLAUDE.md under "Load-bearing details", and every one of them exists *because*
two pages were merged into one document:

| Hazard | Why it exists |
| --- | --- |
| `<body>` carries both original body classes | two `<style is:global>` blocks keyed to their old bodies |
| the demo sits outside `<main>` | `.lab > section > h2` would capture the demo's heading |
| the `<h1>` sits above the demo, styled by its own class | the demo owns an `h2` and comes first |
| replay queries `.la-demo .site-logo-anim` | document-wide it caught the lab's slots and the in-situ marks |
| the lab's size presets are `data-lab-size` | the lab's document-wide `[data-size]` caught the download buttons |

Four of the five dissolve on a split. They are not hazards of the work; they
are hazards of the merge.

The page was merged from `/logo-animation/` and `/logo-lab/`, which is why
this document proposes splitting something that was deliberately joined. The
seam is different. The old seam was *demo versus lab*, two views of the same
audience. The new seam is *publication versus instrument*, which is where the
audiences actually part.

## Decisions

### 1. Split on audience, not on content type

`/design/ao/logo/` becomes the page about the mark: what it is, the three
treatments, the write-on, and the three places on the site it already sits.
A reader, eventually a public one.

`/design/ao/logo-bench/` becomes the instrument: the lab stage with its
controls, and the export panel. One user, who is the author.

The download panel currently sits inside the demo section. It is an
instrument, and it moves.

### 2. The publication keeps the URL

The registry slugs by role, and "the AO mark" is the role the write-up fills.
Keeping `logo` preserves the URL, the registry entry, the three redirects, and
anything bookmarked. The instrument is the new thing, so the instrument gets
the new slug.

`logo-bench` rather than a nested `/design/ao/bench/logo/`: the registry's
`slug` is a single path segment, and `/lab/` is deliberately a view rather than
a prefix, with a test asserting nothing is served beneath it. Introducing a
second prefix would contradict that. A flat slug also generalises, since the
typeface page will want `typeface-bench` on the same day.

### 3. The registry will need a third status, but not yet

This split exposes a flaw in `DesignEntry.status`: it conflates whether the
work is finished with whether the page should be indexed. That held while every
entry was unfinished private work. It breaks on a bench.

A finished bench is **done and still private**. It is an instrument, not a
publication, and it should never be indexed however polished it gets. With
today's two statuses the only way to keep it out of the index is to call it
`wip` forever, which is a lie that also pins it to `/lab/`'s list of unfinished
work permanently.

The resolution is a third status:

```ts
export type Status = 'wip' | 'ready' | 'tool';
```

with `robotsFor` mapping `wip` and `tool` both to `noindex, nofollow`,
`wipEntries()` unchanged so `/lab/` keeps listing only unfinished work, and
`/design/ao/` grouping tools separately.

**This change does not add it.** On landing the bench is genuinely `wip`,
because step 3 is a rework of it, so `wip` is accurate rather than a
workaround. Adding a status nothing uses would be speculation, and it would
contradict decision 4. It belongs in step 3, when the bench is finished and
the lie would start.

Recorded here because the flaw is real now even though the fix is not due yet,
and because whoever does step 3 should not have to rediscover it.

### 4. The split is a pure move

No new prose, no behaviour change, no layer work. Markup moves between two
files and the shared CSS is divided along the body classes it is already keyed
to. Anything that breaks is then unambiguously the move.

This is deliberate restraint. The write-up wants real writing before it earns
`ready`, and the bench wants the layer model and the band slider. Both are
real work. Neither is this change, and bundling either makes the split
unreviewable.

`status` for both stays `wip` on landing, which is accurate: the write-up is
unwritten and the bench is about to be reworked. The write-up graduates to
`ready` when it is written. The bench becomes `tool` in step 3, per decision 3.

### 5. The redirects get more honest

| Old | Today | After |
| --- | --- | --- |
| `/logo-animation` | `/design/ao/logo/` | `/design/ao/logo/` |
| `/logo-lab` | `/design/ao/logo/` | `/design/ao/logo-bench/` |

`/logo-lab` currently lands on the merged page, which is only half right. The
split restores the destination it originally had.

## What moves

**`/design/ao/logo/`** keeps: the `h1`, the WipBanner, `LogoAnimated` beside
`Logo`, the replay and scrub controls, the 44/28/120 size row, the three
treatment figures, the speed comparison, the trail comparison, and the whole
in-situ section. `bodyClass="logo-anim-demo"`.

**`/design/ao/logo-bench/`** takes: the lab stage with all six slots, the
control fieldsets, and the export panel with its own script. Its own `h1` and
WipBanner. `bodyClass="logo-lab"`.

The lab's `<style is:global>` block and the demo's move with their markup.
Each page then carries one body class, and the class-collision hazard is gone
rather than documented.

## What this dissolves

Of the five hazards, four stop existing:

- **Both body classes.** Each page carries one.
- **Demo outside `<main>`.** The write-up's sections are all one kind, so it
  gets a normal `<main>` with a normal heading order.
- **`h1` above the demo, styled by `.la-title`.** Each page opens on its own
  `h1`. The write-up's can be styled normally, though the warning about never
  using a descendant selector still holds, because the in-situ panel renders
  the real `Hero` and its `h1` must keep the global treatment.
- **`data-lab-size`.** The collision needed both in one document. The rename
  stays, since it is also just a better name, and its test stays as a guard
  against a bare `data-size` reappearing.

The fifth survives in weakened form. Replay must still be scoped, because the
write-up keeps both the demo marks and the in-situ marks, and the in-situ ones
ship `autoplay={false}` deliberately. The existing `.la-demo` scope and its
test carry over unchanged.

## Tests

`scripts/routes.test.mjs` asserts against the merged page in several places.
Each assertion moves to whichever route now owns it:

- the WipBanner, title and robots tests fork into two, one per route
- `contains both the demo and the lab` becomes two tests: `data-la-replay` on
  the write-up, `data-stage` on the bench
- `both body classes are present` inverts into its opposite: each page carries
  exactly one, and neither carries the other's
- the `data-lab-size` and bare-`data-size` guard moves to the bench
- the replay-scoping test moves to the write-up
- `exactly one <main>, and its h1 leads the document` runs on both
- the one-robots-tag loop and the registry round-trip pick up `logo-bench`
- `every built page under /design/ao/ is in the registry` catches a missing
  entry for free
- the `/logo-lab` redirect test asserts the new destination
- the two duration tests from PR #85 split: the demo's scrub stays with the
  write-up, the lab's scrub moves to the bench, and the speed-caption test
  stays with the write-up

`robotsFor` keeps its two-status test. The third arrives with `tool` in step 3.

## Open questions

Two things I decided rather than asked, flagged because they are the reviewable
calls in this document:

1. **`logo-bench` as the slug.** Alternatives are `logo-lab` (matches the old
   URL and the body class, but "lab" now means the `/lab/` view, and reusing
   the word across two meanings is what made the original naming confusing) and
   `logo-tool`. I picked `bench` because it is already the word used for these
   pages in CLAUDE.md's redirect table: "the three former bench paths".

2. **No new writing in this change.** If the write-up should arrive written
   rather than as the moved gallery, that is a larger piece of work and should
   be its own spec, after this.

## Sequence

This spec covers step 1 only.

1. **The page split.** This document.
2. **The layer model.** Retire `flat`; `variant` becomes named presets over
   independent layers: ink, outline, shadow, cut, knock. Band becomes
   `--logo-band`. Shadow gains scale, distance and angle. One line changes in
   `Hero.astro`.
3. **The bench rework.** Expose every layer and parameter as a control, so the
   numbers get chosen by eye rather than guessed in code.
4. *Use the bench.* Settle the canonical band width and the shadow parameters.
5. **The derived band path.** `mark_derived.py` emits `LOGO_BAND_D` for the
   settled width; `check:derived` asserts the baked path's recorded width
   matches the live default, so the two representations cannot drift.

Step 2 carries one known trap worth recording here, because it has caught this
codebase three times: **a parameter that moves from a markup attribute to CSS
has to be added to what `serializeLogo` reads back.** It copies `fill` and
`stroke` only. The shadow's offset is safe today precisely because it is the
attribute `transform="translate(30,30)"`. Parameterising it into a computed CSS
transform without touching the exporter would silently drop the offset from
every downloaded mark.
