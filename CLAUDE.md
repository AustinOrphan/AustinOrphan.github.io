# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Personal portfolio website for Austin Orphan, hosted on GitHub Pages at austinorphan.com. Multi-section site with a dynamic component loading system.

## Architecture

**Entry point:** `index.html` defines the page shell with a Hero section and empty `<div>` containers (`#about-container`, `#projects-container`, `#contact-container`, `#footer-container`). On load, `js/component-loader.js` fetches and injects the four HTML components from `components/` into those containers.

**Component system:** `js/component-loader.js` uses `fetch()` to load `components/{about,projects,contact,footer}.html`. This fails when opened via `file://` protocol due to CORS — always use an HTTP server for local development. The loader dispatches `componentLoaded` and `allComponentsLoaded` custom events that other scripts can listen to.

**CSS:** `styles/main.css` is the sole active stylesheet. It is organized by a numbered table of contents (font imports → variables → reset → animations → layout → sections → special modes → media queries). Backup files (`main_backup.css`, `main_backup_v2.css`, `main_original.css`) exist for reference only — do not edit them.

**Service worker:** `sw.js` caches core assets for offline support. Cache is versioned as `austin-orphan-portfolio-v1`; bump the version string when adding new cacheable assets.

**Git submodule:** `ProjectileMotionSimulator/` is a submodule pointing to `https://github.com/AustinOrphan/ProjectileMotionSimulator.git`. Clone with `--recurse-submodules` to populate it.

## Development Commands

```bash
# Local dev server (runs the vault sync first, then Astro)
npm run dev

# Type-check and build
npm run check
npm run build
npm run preview

# Clone with submodule
git clone --recurse-submodules <repo-url>
# or after a plain clone:
git submodule update --init
```

Note: `npm run check` currently reports pre-existing DOM typing errors in
`src/pages/index.astro`. They are unrelated to the build, which passes.

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

**Color variables** (defined in `:root` in `main.css`):
- `--color-background`: `#1D2B35`
- `--color-primary`: `#EEE5E9`
- `--color-accent`: `#2892D7`
- `--color-secondary`: `#D16666`

**Fonts:** Anta, Comfortaa, Source Sans Pro (main UI); Press Start 2P, VT323, Pixelify Sans (8-bit mode only, loaded in `index.html`).

**Responsive breakpoints** (mobile-first):
- Default: mobile (<600px) — absolute-positioned link bar, large touch targets
- 600px+: tablet
- 768px+: desktop — relative positioning, hover effects, `webkit-text-stroke` outlines
- 1024px+: large desktop

**8-bit mode:** A hidden easter egg toggled by a CSS class. Styles are in the "11. Special Modes" section of `main.css`.

**Icons:** Phosphor Icons (`ph-duotone` class prefix) loaded from CDN via `unpkg.com/@phosphor-icons/web@2.1.1`.

## Pending Configuration (TODO.md)

Two placeholders remain in `index.html` that need real values before the site is fully functional:
- **Formspree:** Replace `YOUR_FORM_ID` (contact form `action` URL in `components/contact.html`)
- **Google Analytics:** Replace `YOUR_GA_ID` in the `<head>` GA4 snippet

## Content Updates

- **Resume:** Replace `AustinOrphanResume.pdf` in root; also referenced in `components/about.html` and `components/contact.html`
- **Social links / hero icons:** Edit `#linkBar` in `index.html` and corresponding CSS in `main.css`
- **About/Projects/Contact content:** Edit the respective file in `components/`
- **Cached assets:** After adding new cacheable assets, update `urlsToCache` in `sw.js` and bump `CACHE_NAME`
