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
for tag pages — plus `src/pages/rss.xml.ts` for the feed.

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

- **Resume:** replace `public/AustinOrphanResume.pdf`; linked from
  `src/components/About.astro` and `src/pages/index.astro`
- **Social links / hero icons:** edit `#linkBar` in `src/pages/index.astro` and
  the matching CSS in `global.css`
- **Footer social links / copyright:** edit `src/components/Footer.astro` once;
  it is shared by the home page and every blog route
- **About / Projects / Contact content:** edit the component in
  `src/components/`
- **Blog posts:** authored in the Obsidian vault, not here — see Blog
  Publishing above

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
