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
