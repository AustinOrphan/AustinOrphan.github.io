# austinorphan.com — design language

This is a **styles-only** design system: colors, fonts, and CSS classes extracted from Austin Orphan's portfolio site (austinorphan.com). There is no component bundle — build every design from your own markup/components, styled with the vocabulary below. Everything ships via `styles.css` (which imports `tokens/tokens.css` and `fonts/fonts.css`) — read those files before styling; they are the truth.

## Look

Dark, warm, playful-technical. Solid dark-teal background, cream text, blue and red used sparingly as paired accents. Generous whitespace, rounded corners (3–12px), subtle glows instead of hard borders.

## Colors — use the CSS variables, never raw hex

- `var(--color-background)` `#1D2B35` — page and section background. Designs are dark-mode only.
- `var(--color-primary)` `#EEE5E9` — body text and headings.
- `var(--color-accent)` `#2892D7` — links, borders, highlights, interactive affordances.
- `var(--color-secondary)` `#D16666` — tags, hover fills, and the *second* layer of paired shadows/accents. Red never appears without blue nearby.
- Literal exceptions: `#0d1b24` for code-block backgrounds, `#aaa` for muted metadata. Card surfaces are `rgba(238, 229, 233, 0.02–0.08)` (cream at low alpha), not gray.

## Fonts — three families, fixed roles and weights

- **Anta** (400) — all headings and display text. Often uppercase with `letter-spacing: 0.08–0.1em` at small sizes.
- **Comfortaa** (700, the only weight shipped) — body copy, card titles, navigation.
- **Source Sans Pro** (900, the only weight shipped) — the base `html/body` font; fallback UI text.

## Class vocabulary (all defined in `styles.css`)

- `.hero-title` — Anta display treatment with the site's signature layered offset shadow (red under blue). Set your own `font-size`.
- `.page-title` — Anta section heading with a 2px accent underline.
- `.prose` — long-form content: Comfortaa body, accent-colored uppercase Anta `h2/h3`.
- `.meta` — muted metadata line (dates, reading time); `.reading-time` inside it goes accent.
- `.projects-grid` + `.project-card` — the card idiom: frosted translucent surface, 4px accent left border, 12px radius, lift-and-glow on hover. `.project-card.placeholder` = dashed red variant. Card `h3` is Comfortaa 24px.
- `.icon-button` — round floating icon button (accent tint, fills red on hover).
- `.tech-tag` — tiny uppercase outlined label, accent color, square corners.
- `.tag-badge` — outlined pill, secondary red, fills solid on hover.
- `.back-link` — quiet small accent link for navigation.
- `.scroll-reveal` (+ `.revealed`) — fade-up entrance; keyframes `fadeInUp`, `buttonFloat`, `gentleGlow`, `floating` are available for subtle motion.
- `.texture-overlay` — apply to a `position: relative/fixed` container to add the site's animated pixel-texture layer. Use on full-page shells only.

## Idiomatic snippet

```html
<div class="projects-grid">
  <article class="project-card">
    <h3>Projectile Motion Simulator</h3>
    <p class="prose">Interactive physics sandbox built with canvas.</p>
    <div style="display:flex; gap:10px; margin-top:16px;">
      <span class="tech-tag">TypeScript</span>
      <span class="tech-tag">Canvas</span>
    </div>
  </article>
</div>
```

Layout glue (grids, flex, spacing) is yours to write — keep spacing generous (20–40px gaps), keep everything on `var(--color-background)`, and reach for blue before red.
