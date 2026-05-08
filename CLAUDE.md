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
# Local dev (required — file:// breaks component loading)
python3 -m http.server 8000
# visit http://localhost:8000

# Clone with submodule
git clone --recurse-submodules <repo-url>
# or after a plain clone:
git submodule update --init
```

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
