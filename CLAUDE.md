# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Personal portfolio website for Austin Orphan, hosted on GitHub Pages at
austinorphan.com. Astro static site with a single-page portfolio and a blog
sourced from an Obsidian vault.

## Architecture

**Framework:** Astro 6, `output: 'static'`, deployed to GitHub Pages by
`.github/workflows/deploy.yml`. No UI framework integrations — plain `.astro`
components with inline `<script>` blocks.

**Pages:** `src/pages/index.astro` is the portfolio landing page, composing
section components from `src/components/` (`About`, `Projects`, `Contact`,
`Footer`, `ParticleSystem`, `KonamiEgg`). Blog routes live under
`src/pages/blog/` — an index, `[id].astro` for posts, and `tags/[tag].astro`
for tag pages — plus `src/pages/rss.xml.ts` for the feed. Design pages live
under `src/pages/design/ao/`, with `src/pages/lab.astro` listing the
unfinished ones; see Design Pages and /lab/ below.

**Layouts:** `src/layouts/BaseLayout.astro` provides the shared shell (head,
fonts, analytics, Phosphor icons). `BlogPost.astro` wraps individual posts.

**Footer:** `src/components/Footer.astro` serves every page. Its `variant` prop
picks the positioning: `"fixed"` (the default, home page) pins it to the
viewport bottom and parallax-reveals it past `#contact`; `"static"` (all blog
routes) puts it in normal flow at the end of the document, in the same 720px
column as the body text. Everything below the gradient rule — mark, social
links, copyright — is identical in both. Blog posts additionally pass
`prevPost` / `nextPost` to render the post navigation above the rule.

**CSS:** `src/styles/global.css` is the sole stylesheet (~2600 lines),
organized by a numbered table of contents at the top of the file: font imports
→ variables → reset → animations → layout → typography → hero → nav → sections
→ footer → special modes → utilities → media queries.

**Content:** the `blog` collection is defined in `src/content.config.ts` with a
Zod schema (`title`, `description`, `pubDate`, `tags`). Post files in
`src/content/blog/` are generated — see Blog Publishing below.

## Development Commands

```bash
# Local dev server (runs the vault sync first, then Astro)
npm run dev

# Type-check and build
npm run check
npm run build
npm run preview

# Build, then assert on the built dist/ (routing, robots, the merged logo page)
npm test

# Are the generated artifacts still in sync with the mark they come from?
npm run check:derived

# Same assertions without rebuilding first — only valid if dist/ is current
npm run test:routes
```

## Blog Publishing

Posts are authored in the Obsidian vault, not in this repo. `src/content/blog/`
and `public/blog-assets/` are generated build output and are gitignored — never
edit them by hand.

Pipeline: **vault → export repo → sync → Astro build**

The vault is never uploaded anywhere. `scripts/export-vault.mjs` copies only
notes marked `publish: true` (plus the images they embed) into a small private
repo, `AustinOrphan/blog-vault-export`, which CI checks out. A leak of that
repo would expose nothing beyond what is already on the website.

### Publishing a post

1. In Obsidian, give the note frontmatter with `title`, `description`,
   `pubDate`, and `publish: true`. A future `pubDate` holds it back until that
   date passes.
2. From this repo's root:
   ```bash
   npm run export -- --push
   ```
3. CI publishes on the next push to `master`, or on the daily 13:00 UTC cron —
   whichever comes first.

Step 2 is the only manual step; nothing on this machine runs on a schedule.
Omit `--push` for a dry run that writes files but leaves git alone.

Paths default to `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/00_MainBrain`
and `~/src/blog-vault-export`; override with `VAULT_PATH` / `EXPORT_PATH`.

### Scanned directories

The exporter only looks in a few vault directories, so a stray `publish: true`
in a journal or archived note can't reach the site. Defaults are in
`INCLUDE_DEFAULTS` in `scripts/export-vault.mjs`:

- `40_Journal/Blog`
- `10_Projects`

Override per-run with `VAULT_INCLUDE="40_Journal/Blog,20_Areas"`, or pass
`--all` to scan everything. When you start publishing from a new directory,
add it to `INCLUDE_DEFAULTS` rather than relying on `--all`.

Notes keep their vault folder structure in the export repo, but slugs come
from the filename — `10_Projects/homelab/Foo.md` publishes to `/blog/foo/`.
Nesting is organizational only.

### Safety behavior

- Aborts if zero published notes are found, so a botched frontmatter edit
  can't silently empty the site.
- Aborts on a slug collision between two published notes, naming both paths.
- Refuses an `EXPORT_PATH` inside the vault, and never touches `.git` when
  clearing the previous export.
- Notes with unparseable frontmatter are skipped with a warning, not fatally.

### CI setup

`.github/workflows/deploy.yml` checks out the export repo to `.vault` using a
read-only deploy key stored in the `VAULT_DEPLOY_KEY` secret, then builds with
`VAULT_PATH` pointed at it. The private half of that key lives at
`~/.ssh/id_ed25519_blog_vault` — on this machine and in the repo secret, and
nowhere else.

Local builds default to the `test-vault/` fixtures; set `VAULT_PATH` to build
from real content.

## Design Pages and /lab/

Pages documenting the design work, currently the AO mark and the typeface
derived from it. The organising idea is that **location and readiness are
separate concerns**:

- `/design/ao/<slug>/` is where a page permanently lives. Slugs name the
  *role* (`logo`, `typeface`), not the current state of the work, so renaming
  or rewriting a page never moves its URL.
- `/lab/` is a **view**, not a URL prefix. It lists the entries that are still
  unfinished, each linked at its own permanent URL. Nothing is ever served
  beneath `/lab/`, and a test asserts that.

Finishing a page therefore changes a status field, never a URL.

### The registry

`src/data/design-index.ts` is the single source of truth: one `DESIGN_ENTRIES`
record per page with `slug`, `title`, `blurb`, and `status` (`'wip' | 'ready'`).
It is a hand-maintained registry rather than something derived from the pages
because Astro treats only `getStaticPaths` and `prerender` as special exports
from `.astro` frontmatter — a top-level `const status` in a page is not
readable via `import.meta.glob`, so `/lab/` could not enumerate pages that way.

Three helpers consume it: `entryFor(slug)` (throws on an unknown slug, so a
typo fails the build loudly), `robotsFor(status)` (`wip` → `noindex, nofollow`),
and `wipEntries()` (what `/lab/` lists).

### Adding a page

1. Add its entry to `DESIGN_ENTRIES` with `status: 'wip'`.
2. Create `src/pages/design/ao/<slug>.astro`. In the frontmatter, look the
   entry up and pass its robots directive through to the layout:
   ```astro
   import WipBanner from '../../../components/WipBanner.astro';
   import { entryFor, robotsFor } from '../../../data/design-index';

   const entry = entryFor('<slug>');
   ---
   <BaseLayout title={entry.title} description={entry.blurb}
               robots={robotsFor(entry.status)}>
     {entry.status === 'wip' && <WipBanner />}
   ```
3. Add a case to `scripts/routes.test.mjs` so the route, its robots tag, and
   its banner are covered.

Both index pages (`design/ao/index.astro`, `lab.astro`) are infrastructure, not
entries: they never list themselves and carry no banner.

`src/components/WipBanner.astro` is the "unfinished and unlisted" notice, so
that a page reached by typing its URL explains itself instead of looking
broken. Its `<style is:global>` ships on every page that imports it.

### Graduating a page

Flip its `status` to `'ready'` in the registry. That alone makes it
`index,follow`, drops it off `/lab/`, drops its "in progress" tag on
`/design/ao/`, and drops its WIP banner. The URL is unchanged and no link
breaks.

The one thing the flag does not reach is `/design/ao/` itself, whose own
`noindex` is hardcoded because it has no status to derive one from. Flip that
by hand when the first entry graduates.

Today **every entry is `'wip'`** — all of these pages are `noindex` and
deliberately unlinked from the site nav, and the site has no sitemap, so a URL
typed by hand is the only way in.

### Redirects

The three former bench paths redirect via the `redirects` map in
`astro.config.mjs`; static output emits a meta-refresh stub per entry.

| Old | New |
| --- | --- |
| `/orphan-display` | `/design/ao/typeface/` |
| `/logo-animation` | `/design/ao/logo/` |
| `/logo-lab` | `/design/ao/logo/` |

All three were `noindex` and unlinked, so these exist for bookmarks and
history rather than for search engines.

### Load-bearing details on /design/ao/logo/

That page is a merge of the two former bench pages, and several of its oddities
are deliberate. Changing them reintroduces a bug that was already fixed once:

- **`<body>` carries both original body classes**
  (`bodyClass="logo-lab logo-anim-demo"`) so that both inherited
  `<style is:global>` blocks apply. Do not rewrite those selectors to a single
  scope.
- **The demo `<section class="la-demo">` is a sibling of `<main class="lab">`,
  not nested inside it**, because `.lab > section > h2` would otherwise capture
  the demo's "Download" heading. Since that leaves it outside the `main`
  landmark, it carries an `aria-label` so it is still a findable region.
- **The `<h1>` sits above the demo, styled by `.la-title`, not inside `.lab`.**
  The demo owns a "Download" `h2` and comes first in the document, so an `h1`
  inside `.lab` made the page open on a level-2 heading. Style it by its own
  class and never with a descendant selector: the in-situ panel renders the real
  `Hero`, whose own `h1` must keep the global hero treatment, and a `.lab h1`
  rule outranked it and shrank the wordmark to 24px.
- **The demo's replay queries `.la-demo .site-logo-anim`, not the bare class.**
  Document-wide it also caught the lab's six stage slots and three in-situ
  marks, which ship `autoplay={false}` deliberately, so Replay animated panels
  nobody clicked and restarted the lab's mark out from under its scrub slider.
- **The lab's size presets use `data-lab-size`, not `data-size`.** The lab wires
  them with a document-wide `querySelectorAll('[data-size]')`, and the demo's
  PNG download buttons carry `data-size="512"` / `"1024"`. Before the rename,
  clicking a download button also resized the lab stage.

### The global element rules bite every new page

`global.css` styles bare elements for the single-page portfolio, and those rules
reach any page that does not override them. A new page or component **must**
neutralise the ones it inherits, or it renders broken:

| Rule in `global.css` | What it does to an unsuspecting page |
| --- | --- |
| `a { display: flex; width: 100%; height: 100%; justify-content: center }` | Every link becomes a full-width centred block, shattering sentences and detaching list titles from their text |
| `h1 { font-size: 14vw; text-shadow: … }` plus `-webkit-text-stroke: .2vw` above 600px | A 24px heading gets a 2.8px stroke at 1400px and fills in solid |
| `p { color: var(--color-accent); font-size: 4vw }`, `1.5vw` above 600px | Body copy turns accent-coloured and swings from 15px to 10px to 21px with the viewport |

The established overrides are `display: inline; width: auto; height: auto` for
links (see `.post-card-title a`, `.tag-strip-more`), `-webkit-text-stroke: 0;
text-shadow: none` for headings, and an explicit `font-size` on any `<p>`. The
typeface page's `.od-head` block is the worked example.

The link case is the one that kept recurring, so `scripts/routes.test.mjs` now
guards it: a test walks the built pages for anchors inside a `<p>` and fails if
the winning `display` rule for one is the global `flex`. Anchors whose `<p>` is
itself a flex container are exempt — the typeface page's download pills are laid
out that way on purpose. It resolves the cascade by matching class tokens, which
works only because the stylesheet uses plain class-descendant selectors; if that
stops being true it should become a browser check rather than a cleverer parser.
Nothing guards the heading or paragraph cases — those are still on you.

### The export panel saves files, not screenshots

`src/components/logo-download.ts` lifts a rendered mark out of the page and writes it to a
file. A file has no page around it, and every assumption the page makes for free has broken
this at least once:

- **Paint is read back off `getComputedStyle` and written on as attributes.** `Logo.astro`
  gets its fill and stroke from CSS, so a node saved as-is arrives unpainted.
- **Anything a rule was HIDING comes back, and unpainted SVG is black.** Re-treating a mark by
  swapping its variant class leaves hero's offset copy in the markup with only
  `display: none` over it, so plain and flat both saved with a hard black shadow behind the
  letter. The serializer now drops `display: none` subtrees. Safe for the animated file too:
  nothing in `<defs>` is hidden that way — masks and clipPaths compute `display: inline`.
- **The markup's own comments are not valid XML.** `LogoAnimated.astro`'s notes use `--`
  freely, which HTML allows and XML does not, so the animated SVG and every baked video frame
  were files nothing could open. Comments are stripped from both.
- **`paint-order` is a promise design tools do not keep.** Hero paints its outline *under* its
  fill so only the outer half shows. Browsers honour the attribute — which is why the file
  looked right when checked in one — but Illustrator, Figma, Sketch and macOS Preview paint the
  stroke last, putting a red outline on top of the mark. The still export therefore writes the
  outline as its own stroke-only shape beneath a fill-only copy. The animated export keeps
  `paint-order`: there the outline is a `stroke-width` keyframe on that element, and a file
  carrying CSS animations is for a browser anyway.

- **Defs are pruned to what the file points at.** Both components ship the cut and knockout
  masks unconditionally, because a mark gets re-treated by swapping classes and cannot grow
  elements it did not ship with. Each mask holds its own copy of the 3.3KB mark path, so a
  file using neither was carrying about 13KB it never draws. One pass, not a fixed point:
  nothing currently defines a mask that references another def, and if that changes this has
  to iterate or it will drop a def whose only user it just removed.

The panel's own controls: **treatment** is a class swap, **ink/outline/shadow** are custom
properties, **speed** is `--la-speed`, and **size** feeds every button (the video caps at 1024;
frames are baked and rasterised up front).

### The layer model

`src/components/logo-layers.ts` is the table. Ink is always on; **outline** and **shadow** are
independent, which is two booleans and therefore four combinations, and all four are named:

| | outline | shadow |
| --- | --- | --- |
| `plain` | | |
| `outlined` | ✓ | |
| `shadowed` | | ✓ |
| `hero` | ✓ | ✓ |

A variant is a **name for a combination**, not the mechanism. It resolves to `logo-layer-*`
classes and the rules key on those, which is what lets the bench toggle a combination directly.
It replaced a three-value enum — `hero`, `plain`, `flat` — over the same two booleans, where
two values were the same drawing and two combinations had no name at all. `flat` is retired.

Two more layers exist that the variant table does not name, because they are **export
treatments rather than site ones**:

- **`cut`** hollows the outline: the fill goes and the band is cut out of the stroke with a
  mask, so the letterform is a hole and the ground shows through it. It is a *mode of the
  outline*, not a layer of its own — the same paint standing alone instead of sitting under
  the fill — so it needs `outline` and lives in that fieldset in the bench.
- **`knock`** is a field with the letterform punched out, bounded by the viewBox.

Both hide `.site-logo-mark`: with the outline hollowed there is no fill to draw, and with the
field knocked out the hole *is* the mark — painting the glyph back over it in the same ink made
the letterform invisible, off-white on off-white, which is the whole treatment undone.

Neither can be something the pen draws. The write-on lays **filled pieces**, and the band is a
property of their **union**: a piece's own edge includes boundaries interior to the finished
mark that get covered by whatever is drawn next. That is the same trap that made `LOGO_A_D`
necessary. So both apply to the finished mark, in the treatment beat that already exists.

**Band weight is `--logo-band`** and the shadow's placement is `--logo-shadow-dist` /
`-angle` / `-scale`, composed into `--logo-shadow-t` so the write-on's keyframe lands on
exactly that value. Defaults reproduce the old fixed `translate(30,30)` bit-for-bit.

### Robots directives

`BaseLayout.astro` owns the robots directive through its `robots` prop and emits
exactly **one** `<meta name="robots">`. A page that adds its own tag leaves two
conflicting directives in the head, which is how a deliberately private page
ends up advertising `index,follow`. That happened once; `scripts/routes.test.mjs`
now asserts one tag per route. Note that its `robotsOf()` helper reads only the
first match by design, which is exactly why the separate count assertion exists.

### Tests

`npm test` builds and then runs `scripts/routes.test.mjs`, which asserts on the
built `dist/` output rather than on module internals. It uses `node:test` and
`node:assert` only: no test framework is installed and none should be added.

## Derived Artifacts

Much of the brand is **generated from the mark**, not drawn: the icons, the social card, the
`@font-face` file, and the mark embedded in a few hand-maintained HTML/SVG files. The failure
mode is always the same — a generated file silently keeps showing the old thing after its
source changes, and nobody notices until it looks wrong. That has happened twice: the icons
after the mark was re-derived, and `public/fonts/` after the font sources were fixed.

The source of truth is `src/components/logo-mark.ts`:

- `LOGO_MARK_D` — the whole mark, the union of the A, the ring and the hoop
- `LOGO_A_D` — the A alone, used only for the write-on's leg pieces, because clipping the
  union to a leg region also catches the slivers of ring and hoop that cross it

- `LOGO_BAND_D` — the cut band: the outline with the letterform punched out, as a real filled
  path. On the page that shape is a mask, which is exact and needs no generator; this is the
  same shape flattened, for the same reason hero's outline is flattened on export.

The first two come from `font/measure/mark_derived.py`, the band from `band_derived.py`.
**Extract them by export name**, never by "the first long path in the file" — there are three
now.

The band is the one derived artifact with a **parameter**: it is `buffer(mark, 150) - mark`,
so the stroke width it was derived at is part of the derivation. `LOGO_BAND_WIDTH` records it
and `check:derived` asserts it still matches the `--logo-band` default in `global.css`. Two
representations of one shape is exactly how the icons and `public/fonts/` drifted; that
assertion is what makes carrying both safe.

300 was chosen against two measurements, not taste. The mark's own thinnest stroke is 191 path
units and the band's visible weight is half the stroke, so below 382 the band is lighter than
the lightest part of the mark. The tightest of the mark's 8 counters has a gap of 402, and the
band advances half its width from each side, so that counter seals at about 400 — confirmed by
rasterising, 8 counters open at 380 and 7 at 400. 300 sits 23% below that ceiling. 382 would
make the band exactly the mark's thinnest stroke and is 2% from failure, which a re-derivation
of the mark could cross.

The band's generator reads `LOGO_MARK_D` rather than the font, so re-deriving it does not need
the font sources — which is why it is its own script rather than another branch of
`mark_derived.py`. Both need `font/requirements.txt`; the band alone needs only `shapely`.

| Generator | Owns |
| --- | --- |
| `font/measure/mark_derived.py` | `LOGO_MARK_D`, `LOGO_A_D` (paste its `site_path` output in) |
| `font/measure/band_derived.py` | `LOGO_BAND_D`, `LOGO_BAND_WIDTH` — the cut band, `buffer(mark, 150) - mark` |
| `scripts/make-icons.mjs` | every icon in `public/`, plus `favicon.svg` and `safari-pinned-tab.svg` |
| `scripts/make-og-image.mjs` | `public/og-image.png` and the path inside `docs/og-image.html` |
| `font/build_variable.py` | `public/fonts/OrphanDisplay-VF.{ttf,woff2}` — **installs them itself** |
| *(none)* | `docs/repo-social-preview.html` — paste the path by hand |

`npm run check:derived` verifies all of it, and `.github/workflows/derived.yml` runs it on
every push. It is deliberately **not** part of `deploy.yml`'s build job: that job's 13:00 UTC
cron is what publishes a post once its `pubDate` arrives, and a stale favicon should not be
able to hold a post back.

The font is the one thing not checked — verifying it needs a six-minute rebuild. Instead
`build_variable.py` installs what it builds, so the hand-copy step that caused that drift is
gone. Running the font or mark generators needs `font/requirements.txt` installed.

## Design System

**Color variables** (defined in `:root` in `src/styles/global.css`):
- `--color-background`: `#1D2B35`
- `--color-primary`: `#EEE5E9`
- `--color-accent`: `#2892D7`
- `--color-secondary`: `#D16666`

**Fonts:** Anta, Comfortaa, Source Sans Pro (main UI); Press Start 2P, VT323,
Pixelify Sans (pixel mode only). All loaded in `BaseLayout.astro`.

**Responsive breakpoints** (mobile-first):
- Default: mobile (<600px) — absolute-positioned link bar, large touch targets
- 600px+: tablet
- 768px+: desktop — relative positioning, hover effects, `webkit-text-stroke` outlines
- 1024px+: large desktop

**Pixel mode:** a hidden easter egg. `src/components/KonamiEgg.astro` listens
for the Konami code and toggles the `pixel-mode` class on `<body>`; the styles
live in the "11. Special Modes" section of `global.css`.

**Icons:** Phosphor Icons (`ph-duotone` class prefix) loaded from CDN in
`BaseLayout.astro` via `unpkg.com/@phosphor-icons/web@2.1.1`.

## Content Updates

- **Resume:** authored as a Google Doc. Run the **Publish resume** workflow
  (Actions → Run workflow) to export it over `public/AustinOrphanResume.pdf`
  and push; that manual run is the publish gate, since the Doc is always live.
  Needs the `RESUME_DOC_ID` secret. `scripts/check-resume-pdf.mjs` refuses
  anything that is not a PDF, is under 10KB, lacks the name, or carries an
  address other than the one the site advertises. Dropping a file into
  `public/` by hand still works. Linked from `src/components/About.astro`,
  `src/components/Footer.astro` and `src/pages/index.astro`
- **Social links / hero icons:** edit `#linkBar` in `src/pages/index.astro` and
  the matching CSS in `global.css`
- **Footer social links / copyright:** edit `src/components/Footer.astro` once;
  it is shared by the home page and every blog route
- **About / Projects / Contact content:** edit the component in
  `src/components/`
- **Blog posts:** authored in the Obsidian vault, not here — see Blog
  Publishing above
- **Design pages:** edit the page under `src/pages/design/ao/`; its title,
  blurb and readiness come from `src/data/design-index.ts` — see Design Pages
  and /lab/ above

## Known Issues

None outstanding. `npm run check` is clean: 0 errors, 0 warnings.

It previously reported ~155 DOM typing errors, mostly `Property 'style' does
not exist on type 'Element'`. Those are fixed: element queries are typed with
`document.querySelector<HTMLElement>(...)`, the `Particle` class declares its
fields, and event handlers are annotated. Keep it at zero. The inline
`<script>` blocks in `.astro` files are TypeScript, so generics and type
annotations work there.

## Sibling Pages Sites

Some projects are served from their own repos' GitHub Pages, published into
subpaths of austinorphan.com rather than built by this repo:

- `/ProjectileMotionSimulator/` — from `AustinOrphan/ProjectileMotionSimulator`
  (`master`)
- `/tanks/` — from `AustinOrphan/tanks` (`main`)

They will not appear in this repo's `dist/`. Link to them with plain absolute
paths; note `/tanks` 301-redirects to `/tanks/`, so link the trailing-slash
form.
