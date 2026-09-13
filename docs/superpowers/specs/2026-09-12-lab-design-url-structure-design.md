# `/lab/` and `/design/ao/`: a URL structure for unfinished work

**Date:** 2026-09-12
**Status:** approved, not yet implemented

## Problem

Three pages exist that are live but deliberately hidden: `/logo-lab/`,
`/logo-animation/` and `/orphan-display/`. Each is `noindex, nofollow`, absent
from every nav, and linked from nowhere in `src/`. They sit at root paths
alongside `/blog/`, so nothing about their location says "not ready", and
nothing groups them.

Two organising ideas were on the table: a `/lab/` path for work that is not
ready, and a `/fonts/` path for typeface and logo work. They sort on different
axes. `/lab/` sorts by readiness, `/fonts/` sorts by subject, and those axes
cross: the typeface page is both a font thing and an unfinished thing, so the
two rules disagree about where it belongs.

## Decisions

### 1. Location and readiness are separate concerns

`/design/ao/` is a **location**: where a page permanently lives.
`/lab/` is a **view**: an index listing whatever is currently unfinished.

Nothing lives *in* `/lab/`. It is a lens over pages that live elsewhere. This
is what allows every URL to be permanent, and it is the resolution of the
crossed axes above.

### 2. Permanent URLs from day one

A page ships at the URL it will keep forever. Readiness is metadata, never a
path segment. Graduating from private to public changes a status field, not a
URL.

This is safe here specifically because the pages are `noindex` and unlinked, so
none has accumulated inbound links or search ranking that a later move would
squander.

### 3. `/design/` rather than `/brand/` or `/fonts/`

Chosen on an asymmetry: `/design/` holding brand work reads fine, because a
typeface and a logo are design. `/brand/` holding non-brand work reads wrong.
`/design/` therefore cannot become inaccurate later, while `/brand/` can.
Renaming costs redirects; choosing the broader word costs nothing.

`/fonts/` is rejected outright. It already serves
`public/fonts/OrphanDisplay-VF.woff2` and `.ttf`. A page there would build and
serve correctly, but it would mix a human-readable page into a folder of font
binaries.

`ao` is the user's standing shorthand for the personal brand.

### 4. Lowercase paths

`/design/ao/`, not `/design/AO/`. GitHub Pages URLs are case-sensitive, so the
two are different paths and only one resolves. Lowercase matches every
hand-authored route on the site. "AO" still renders capitalised in page titles
and headings.

### 5. Slug by role, not by product name

`/design/ao/typeface/`, not `/design/ao/orphan-display/`. The typeface name is
not settled, and baking an unsettled name into a URL contradicts decision 2.
Roles are stable; names are not. The display name lives in the `<h1>`, free to
change.

Once the name is locked, add `/design/ao/<name>/` as an alias onto the
role-based path. Deferred until then.

## URL map

| Today | Becomes | Initial status |
|---|---|---|
| `/orphan-display/` | `/design/ao/typeface/` | wip |
| `/logo-animation/` | `/design/ao/logo/` | wip, merged |
| `/logo-lab/` | `/design/ao/logo/` | wip, merged |
| new | `/design/ao/` | index page, `noindex` (see below) |
| new | `/lab/` | index page, `noindex` (see below) |

`/design/ao/` and `/lab/` are index pages, not content. They are **not**
registry entries, they carry no WIP banner, and they never list themselves or
each other. They ship `noindex, nofollow` and unlinked while every entry is
`wip`, and become indexable and nav-linked once the first entry reaches
`ready`.

Unchanged: `/`, `/blog/`, `/blog/tags/`, `/blog/tags/<tag>/`, `/rss.xml`, and
the `/fonts/*` binaries.

## Readiness mechanism

The site has **no sitemap**. There is no `@astrojs/sitemap` in `package.json`
and `/sitemap-index.xml` returns 404. Readiness therefore has exactly two
levers:

1. The `robots` meta value. `BaseLayout.astro` already accepts a `robots` prop
   defaulting to `'index,follow'`, so no new plumbing is needed. A `wip` page
   passes `'noindex, nofollow'`.
2. Whether anything links to the page.

A `wip` page also renders a visible banner, so that a page found by typing its
URL explains itself rather than looking broken or abandoned.

| Status | robots | Linked from nav | Appears in `/lab/` |
|---|---|---|---|
| `wip` | `noindex, nofollow` | no | yes |
| `ready` | `index,follow` (default) | yes | no |

## Single source of truth

A registry at `src/data/design-index.ts`, an array of
`{ slug, title, blurb, status: 'wip' | 'ready' }`.

- Each page imports its own entry and derives its `robots` value and banner.
- `/lab/` filters `status === 'wip'`.
- `/design/ao/` lists every entry.

A registry is required rather than globbing the pages for a status export.
Astro treats only `getStaticPaths` and `prerender` as special exports from
`.astro` frontmatter, so a top-level `const status` in a page is not readable
via `import.meta.glob`. The registry is also what prevents `/lab/` drifting out
of sync with what is genuinely unfinished.

## Merging the two logo pages

`/design/ao/logo/` carries the demo from `logo-animation.astro` and the knobs
from `logo-lab.astro` on one page. The knobs stay as a public interactive toy
rather than being stripped on graduation.

Whether the knobs sit open or behind a toggle is an implementation detail, to
be settled while building the merged page.

## Redirects

The three current paths are `noindex`, unlinked, and have zero inbound links
anywhere in `src/`, so no redirect is strictly required. Add them regardless,
as three entries in `redirects` in `astro.config.mjs`, to cover existing
browser history and bookmarks. Astro's static output emits meta-refresh stubs.

- `/orphan-display/` → `/design/ao/typeface/`
- `/logo-animation/` → `/design/ao/logo/`
- `/logo-lab/` → `/design/ao/logo/`

## Out of scope

- Adding a sitemap.
- Linking `/lab/` or `/design/ao/` from the site nav. Both ship `noindex` and
  unlinked, because every registry entry starts `wip`.
- Graduating any page to `ready`.
- The `/design/ao/<name>/` alias, which waits on the typeface name.
- Moving the sibling Pages sites (`/tanks/`, `/ProjectileMotionSimulator/`).
  They are published from their own repos and are not affected.
