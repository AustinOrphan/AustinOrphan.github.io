# Astro Blog Migration — Design Spec

**Date:** 2026-05-08  
**Status:** Approved  
**Scope:** Full Astro migration (portfolio + blog) for austinorphan.com

---

## Overview

Migrate the existing vanilla HTML/CSS/JS portfolio site to Astro, adding a blog with RSS, tags, and reading time. The existing design (colors, fonts, 8-bit easter egg) is preserved exactly. Markdown files in the repo serve as the CMS — no external services required.

---

## Architecture

### Project Structure

```
src/
  components/
    About.astro
    Projects.astro
    Contact.astro
    Footer.astro
    EightBitToggle.astro
  content/
    blog/          ← markdown post files
    config.ts      ← Zod schema for blog collection
  layouts/
    BaseLayout.astro
    BlogPost.astro
  pages/
    index.astro          ← portfolio home
    blog/
      index.astro        ← post list
      [slug].astro       ← individual post
      tags/
        [tag].astro      ← posts filtered by tag
    rss.xml.ts           ← RSS feed endpoint
  styles/
    global.css           ← main.css transplanted verbatim
public/
  AustinOrphanResume.pdf
  sw.js                  ← service worker (moved from root)
  CNAME                  ← moved from repo root
  favicon.ico, *.png, site.webmanifest, browserconfig.xml
astro.config.mjs
package.json
```

### Key Architectural Decisions

- **No component loader.** The fetch-based `js/component-loader.js` is replaced by Astro's build-time static rendering. HTML components become `.astro` components imported directly into `index.astro`. This eliminates the `file://` CORS limitation entirely.
- **Single CSS file.** `main.css` moves to `src/styles/global.css` with no content changes. It is imported once in `BaseLayout.astro` and applies globally.
- **Astro static output.** `output: 'static'` in `astro.config.mjs`. No server required — output is a flat `dist/` directory deployed to GitHub Pages.
- **8-bit easter egg preserved.** `EightBitToggle.astro` uses `client:load` to hydrate the toggle button client-side. It toggles the `.eight-bit` class on `<body>`, exactly as today.

---

## Blog Content Schema

### `src/content/config.ts`

```ts
import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
```

### Post Frontmatter

```yaml
---
title: "Post title"
description: "One-sentence summary for post list and RSS"
pubDate: 2026-05-08
tags: ["projects", "javascript"]
draft: false
---
```

- `draft: true` excludes a post from the list, RSS feed, and tag pages. During `npm run dev` the post is accessible at its URL directly; in the production build it is not generated at all (filtered at the `getStaticPaths` / `getCollection` call level).
- No `updatedDate` field in initial scope — can be added later without schema breakage.

---

## Blog Features

### Reading Time
Calculated at build time from word count (approx. 200 wpm). Displayed on post cards in the list view and below the title on post pages. No frontmatter field needed — derived from rendered content.

### Tags
- `tags` array in frontmatter drives everything.
- Tag filter bar on `/blog` — clicking a tag navigates to `/blog/tags/[tag]`.
- Each tag page lists all non-draft posts with that tag, sorted by `pubDate` descending.
- Tags rendered as styled badges using `--color-secondary` (`#D16666`) to distinguish from the `--color-accent` (`#2892D7`) used for links.

### RSS Feed
- Endpoint: `/rss.xml`
- Generated at build time via `src/pages/rss.xml.ts` using Astro's `@astrojs/rss` package.
- Includes all non-draft posts with `title`, `description`, `pubDate`, and post URL.
- Link to feed shown at the bottom of `/blog`.

### Draft Posts
Excluded from: post list, RSS feed, tag pages, tag filter bar counts. They build locally so `npm run dev` can preview them, but the production build omits them.

---

## Blog UI Design

Uses the existing design system throughout — no new colors, fonts, or spacing scales introduced.

### `/blog` — Post List Page
- Anta font for page title "BLOG", accent underline in `--color-accent`
- Tag filter bar below title — active tag filled `--color-accent`, inactive outlined
- Post cards: thin border in `rgba(--color-accent, 0.3)`, brightens to full accent on hover
- Each card shows: title (Anta), date · reading time, description excerpt, tag badges
- RSS link at page bottom

### `/blog/[slug]` — Post Page
- Back link (`← back to blog`) at top
- Title (Anta), date · reading time, tag badges
- Horizontal rule separating metadata from body
- Body prose in Comfortaa, `--color-primary` (`#EEE5E9`), `line-height: 1.8`
- Code blocks: dark background (`#0d1b24`), left border in `--color-accent`
- Headings in body use Anta, uppercased, with `--color-accent` color

### `/blog/tags/[tag]` — Tag Page
- Minimal: tag name as page title, same post card layout as `/blog`
- Back link to `/blog`

---

## Layouts

### `BaseLayout.astro`
Replaces `index.html`'s `<head>` and shell. Responsible for:
- `<meta>` tags, GA4 snippet (with `YOUR_GA_ID` placeholder preserved)
- Global CSS import
- Phosphor Icons CDN (`unpkg.com/@phosphor-icons/web@2.1.1`)
- 8-bit mode fonts (Press Start 2P, VT323, Pixelify Sans)
- `<slot />` for page content

### `BlogPost.astro`
Wraps `BaseLayout.astro` (Astro layout nesting via import, not inheritance). Adds:
- Open graph `<meta>` tags populated from post frontmatter (`title`, `description`, `pubDate`)
- Structured article markup around `<slot />`

---

## Deployment

### GitHub Actions — `.github/workflows/deploy.yml`

Trigger: push to `master`

Steps:
1. Checkout repo (with submodules, for `ProjectileMotionSimulator/`)
2. Setup Node 24
3. `npm ci`
4. `npm run build` → outputs to `dist/`
5. Deploy `dist/` using GitHub's official Pages action (`actions/upload-pages-artifact` + `actions/deploy-pages`). No separate `gh-pages` branch needed — Pages is configured to deploy from Actions in the repo settings.

### What Changes
| | Before | After |
|---|---|---|
| Local dev | `python3 -m http.server 8000` | `npm run dev` |
| Publish | Push HTML directly to `master` | Push source; Actions builds and deploys |
| CNAME | In repo root | In `public/CNAME` |
| Service worker | `sw.js` in root | `public/sw.js` |

### What Stays the Same
- URL: `austinorphan.com`
- GitHub Pages hosting
- All favicons, manifest, browserconfig
- Service worker behavior (cache version string may need a bump after migration)

---

## Out of Scope (Future)

The following features were noted as desirable but are explicitly deferred:

- Search (Pagefind)
- Comments (Giscus / GitHub Discussions)
- Social share OG image generation
- MDX support (can be added to `astro.config.mjs` later without restructuring)
- `updatedDate` frontmatter field

---

## Open Placeholders (Carry Over From Current Site)

These exist in the current codebase and remain unresolved — they should be preserved as-is in the migrated code:

- `YOUR_FORM_ID` in the contact form action URL (`components/contact.html` → `Contact.astro`)
- `YOUR_GA_ID` in the GA4 snippet (`BaseLayout.astro`)
