# `/lab/` and `/design/ao/` URL Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the three hidden bench pages to permanent URLs under `/design/ao/`, merge the two logo pages into one, and add a `/lab/` index that lists whatever is currently unfinished.

**Architecture:** Location and readiness are separate. `/design/ao/<role>/` is where a page permanently lives; `/lab/` is a view over a registry listing entries whose `status` is `wip`. A page never moves when it becomes ready; only its `status` changes, which flips its `robots` meta and drops it off `/lab/`.

**Tech Stack:** Astro 7 (`output: 'static'`, `trailingSlash: 'ignore'`, default `build.format: 'directory'`), TypeScript, Node 24 with the built-in `node:test` runner. No new dependencies.

## Global Constraints

- **No new dependencies.** Tests use Node's built-in `node:test` and `node:assert/strict`.
- **Node 24.x.** `import.meta.dirname` is available and is the preferred way to locate `dist/`.
- **Every new page uses `BaseLayout.astro`** and passes `robots` through its prop. Never add a second `<meta name="robots">`; `BaseLayout.astro:99` already emits exactly one.
- **Paths are lowercase.** `/design/ao/`, never `/design/AO/`. GitHub Pages is case-sensitive.
- **Slug by role, not product name.** `typeface`, not `orphan-display`. Display names live in the `<h1>`.
- **Astro emits directory-style output.** A page at `src/pages/design/ao/logo.astro` builds to `dist/design/ao/logo/index.html` and serves at `/design/ao/logo/`.
- **`npm run build` runs `npm run sync` first**, which syncs from `test-vault/` fixtures locally. A build takes roughly 5 seconds and emits 15 pages today.
- Do not add a sitemap, do not link these pages from the site nav, and do not change any page's status to `ready`. All are out of scope.

---

### Task 1: Registry, WIP banner, test harness, and the typeface move

Creates the shared infrastructure every later task consumes, and proves it by moving the simplest of the three pages.

**Files:**
- Create: `src/data/design-index.ts`
- Create: `src/components/WipBanner.astro`
- Create: `scripts/routes.test.mjs`
- Create: `src/pages/design/ao/typeface.astro` (via `git mv` from `src/pages/orphan-display.astro`)
- Delete: `src/pages/orphan-display.astro`
- Modify: `package.json` (scripts block)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `DESIGN_ENTRIES: DesignEntry[]`, `type Status = 'wip' | 'ready'`, `interface DesignEntry { slug: string; title: string; blurb: string; status: Status }`
  - `entryFor(slug: string): DesignEntry` — throws if the slug is unknown.
  - `robotsFor(status: Status): string`
  - `wipEntries(): DesignEntry[]`
  - `<WipBanner />` — an Astro component taking no props.
  - `scripts/routes.test.mjs` helpers `pagePath(route)`, `html(route)`, `robotsOf(doc)`.

- [ ] **Step 1: Write the registry**

Create `src/data/design-index.ts`:

```ts
// Single source of truth for what lives under /design/ao/ and how finished it is.
//
// This is a registry rather than something derived from the pages themselves
// because Astro treats only `getStaticPaths` and `prerender` as special exports
// from `.astro` frontmatter. A top-level `const status` in a page is not
// readable via `import.meta.glob`, so /lab/ could not enumerate pages that way.

export type Status = 'wip' | 'ready';

export interface DesignEntry {
  /** Path segment under /design/ao/. Slugged by role, so renaming the work
   *  never moves the URL. */
  slug: string;
  /** Display name. Free to change without touching the URL. */
  title: string;
  /** One line, shown on the /design/ao/ and /lab/ index pages. */
  blurb: string;
  status: Status;
}

export const DESIGN_ENTRIES: DesignEntry[] = [
  {
    slug: 'logo',
    title: 'The AO mark',
    blurb: 'The animated mark, its three real site contexts, and the knobs behind it.',
    status: 'wip',
  },
  {
    slug: 'typeface',
    title: 'Orphan Display',
    blurb: 'A typeface derived from the AO mark, with its two axes live.',
    status: 'wip',
  },
];

/** Look up one entry. Throws rather than returning undefined so that a typo in
 *  a page's slug fails the build loudly instead of silently shipping a page
 *  with the wrong robots directive. */
export function entryFor(slug: string): DesignEntry {
  const entry = DESIGN_ENTRIES.find((e) => e.slug === slug);
  if (!entry) {
    throw new Error(
      `No design-index entry for slug "${slug}". Add one to DESIGN_ENTRIES in src/data/design-index.ts.`,
    );
  }
  return entry;
}

/** The robots directive a page carries for its status. `wip` pages stay out of
 *  search results; the site has no sitemap, so this and inbound links are the
 *  only two levers on discoverability. */
export function robotsFor(status: Status): string {
  return status === 'wip' ? 'noindex, nofollow' : 'index,follow';
}

export function wipEntries(): DesignEntry[] {
  return DESIGN_ENTRIES.filter((e) => e.status === 'wip');
}
```

- [ ] **Step 2: Write the WIP banner component**

Create `src/components/WipBanner.astro`:

```astro
---
// Shown on every `wip` page, so that a page found by typing its URL explains
// itself rather than looking broken or abandoned.
---
<p class="wip-banner">
  <strong>Work in progress.</strong> This page is unfinished and unlisted. It may
  change or break without warning. <a href="/lab/">See everything in progress</a>.
</p>

<style is:global>
  .wip-banner {
    max-width: 1180px;
    margin: 0 auto;
    padding: 10px 16px;
    border: 1px solid rgba(var(--color-primary-rgb), 0.28);
    border-radius: 8px;
    background: rgba(var(--color-primary-rgb), 0.05);
    color: rgba(var(--color-primary-rgb), 0.75);
    font-size: 0.84rem;
  }
  .wip-banner a {
    color: var(--color-accent);
  }
</style>
```

- [ ] **Step 3: Write the failing test**

Create `scripts/routes.test.mjs`:

```js
// Asserts on built output in dist/, so it exercises the real Astro build rather
// than module internals. Run `npm run build` first, or use `npm test` which
// chains both.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

const DIST = join(import.meta.dirname, '..', 'dist');

/** Built path for a route. Astro's default directory format means every page
 *  lands at <route>/index.html. Pass the route without leading or trailing
 *  slashes, e.g. 'design/ao/typeface'. */
export function pagePath(route) {
  return join(DIST, route, 'index.html');
}

export async function html(route) {
  return readFile(pagePath(route), 'utf8');
}

/** BaseLayout emits exactly one robots tag, in this exact shape. */
export function robotsOf(doc) {
  const m = doc.match(/<meta name="robots" content="([^"]*)">/);
  return m?.[1] ?? null;
}

test('/design/ao/typeface/ is built, noindex, and carries the WIP banner', async () => {
  const doc = await html('design/ao/typeface');
  assert.equal(robotsOf(doc), 'noindex, nofollow');
  assert.match(doc, /<title>Orphan Display/);
  assert.match(doc, /Work in progress\./);
});

test('the typeface page still renders its specimen controls', async () => {
  const doc = await html('design/ao/typeface');
  assert.match(doc, /Regular Flat/);
});
```

- [ ] **Step 4: Add the test scripts**

In `package.json`, add two entries to `"scripts"`, leaving the existing entries untouched:

```json
    "test:routes": "node --test scripts/routes.test.mjs",
    "test": "npm run build && node --test scripts/routes.test.mjs"
```

- [ ] **Step 5: Run the test to verify it fails**

Run: `npm run build && npm run test:routes`

Expected: FAIL. Two failing tests, both with `ENOENT: no such file or directory, open '.../dist/design/ao/typeface/index.html'`.

- [ ] **Step 6: Move the page**

```bash
mkdir -p src/pages/design/ao
git mv src/pages/orphan-display.astro src/pages/design/ao/typeface.astro
```

- [ ] **Step 7: Fix the import depth and wire up the registry**

In `src/pages/design/ao/typeface.astro`, the file moved three directories deeper, so its one import must gain two levels. Replace line 7:

```astro
import BaseLayout from '../layouts/BaseLayout.astro';
```

with:

```astro
import BaseLayout from '../../../layouts/BaseLayout.astro';
import WipBanner from '../../../components/WipBanner.astro';
import { entryFor, robotsFor } from '../../../data/design-index';

const entry = entryFor('typeface');
```

Then replace the opening `<BaseLayout ...>` tag (the line beginning `<BaseLayout title="Orphan Display"`) with:

```astro
<BaseLayout title={entry.title} description={entry.blurb}
            bodyClass="od-page" robots={robotsFor(entry.status)}>
```

Immediately after that opening tag, insert the banner as the first child:

```astro
  <WipBanner />
```

- [ ] **Step 8: Run the test to verify it passes**

Run: `npm run build && npm run test:routes`

Expected: PASS, 2 tests. The build log should list `/design/ao/typeface/index.html` and should no longer list `/orphan-display/index.html`.

- [ ] **Step 9: Commit**

```bash
git add src/data/design-index.ts src/components/WipBanner.astro scripts/routes.test.mjs package.json src/pages/design/ao/typeface.astro
git commit -m "feat(design): move the typeface page to its permanent URL

Adds the design-index registry, a WIP banner, and a dist-asserting test
harness built on node:test. /orphan-display/ becomes /design/ao/typeface/,
slugged by role so renaming the font never moves the URL."
```

---

### Task 2: Merge the two logo pages into `/design/ao/logo/`

**Files:**
- Create: `src/pages/design/ao/logo.astro`
- Delete: `src/pages/logo-animation.astro`, `src/pages/logo-lab.astro`
- Modify: `scripts/routes.test.mjs`

**Interfaces:**
- Consumes: `entryFor`, `robotsFor` from `src/data/design-index`; `WipBanner`; the test helpers `html` and `robotsOf` from Task 1.
- Produces: the route `/design/ao/logo/`. No new exported symbols.

**Background the implementer needs.** The two source pages are self-contained: markup, then `<style is:global>`, then `<script>`. Nothing in `src/styles/global.css` references their body classes, so nothing outside these files needs to change. Block boundaries today:

| File | Lines | `</BaseLayout>` | style blocks | script block |
|---|---|---|---|---|
| `logo-animation.astro` | 430 | 129 | 131–194, 328–430 | 196–326 |
| `logo-lab.astro` | 397 | 168 | 170–252 | 254–397 |

Two hazards, both real:

1. **Body-class-keyed CSS.** The style blocks are keyed on `.logo-anim-demo` and `.logo-lab` respectively. Do **not** rewrite those selectors. Put *both* classes on the body instead: `bodyClass="logo-lab logo-anim-demo"`. This keeps the merge a move rather than a CSS rewrite.
2. **A `data-size` collision that would ship a real bug.** `logo-lab.astro:356` wires its size presets with `document.querySelectorAll('[data-size]')`, a document-wide query. `logo-animation.astro:104-105` has PNG download buttons carrying `data-size="512"` and `data-size="1024"`. Merged as-is, clicking a download button would *also* resize the lab stage. `data-size` is the only data attribute the two files share, so renaming the lab's four buttons fixes it completely.

- [ ] **Step 1: Write the failing test**

Append to `scripts/routes.test.mjs`:

```js
test('/design/ao/logo/ is built, noindex, and carries the WIP banner', async () => {
  const doc = await html('design/ao/logo');
  assert.equal(robotsOf(doc), 'noindex, nofollow');
  assert.match(doc, /<title>The AO mark/);
  assert.match(doc, /Work in progress\./);
});

test('/design/ao/logo/ contains both the demo and the lab', async () => {
  const doc = await html('design/ao/logo');
  assert.match(doc, /data-la-replay/, 'the demo replay control is missing');
  assert.match(doc, /data-stage/, 'the lab stage is missing');
});

test('both body classes are present, so both style blocks apply', async () => {
  const doc = await html('design/ao/logo');
  assert.match(doc, /class="logo-lab logo-anim-demo"/);
});

test('the lab size presets no longer collide with the download buttons', async () => {
  const doc = await html('design/ao/logo');
  assert.match(doc, /data-lab-size="280"/, 'lab presets were not renamed');
  // The only bare data-size attributes left must be the two PNG download buttons.
  const bare = [...doc.matchAll(/data-size="(\d+)"/g)].map((m) => m[1]).sort();
  assert.deepEqual(bare, ['1024', '512']);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run build && npm run test:routes`

Expected: FAIL. Four new failures, all `ENOENT` on `dist/design/ao/logo/index.html`.

- [ ] **Step 3: Create the merged page**

```bash
git mv src/pages/logo-lab.astro src/pages/design/ao/logo.astro
```

Now edit `src/pages/design/ao/logo.astro`:

Replace its frontmatter (lines 1–18, the whole `---` block) with:

```astro
---
// The AO mark: the animated component beside its static twin, the three places
// the logo actually appears on the site at their real sizes, and every prop as
// a live control.
//
// The variant and trail props are build-time, so each (variant, trail) pair is
// rendered once and the controls show one and hide the rest. Everything else,
// size, speed and the three colours, is a custom property or an attribute set
// live on the chosen instance. That way the thing on screen is the real
// component's own output and not a mock-up of it.
//
// Merged from the former /logo-animation/ and /logo-lab/ pages. Both style
// blocks are keyed on their original body classes, so the body carries both.
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Logo from '../../../components/Logo.astro';
import LogoAnimated from '../../../components/LogoAnimated.astro';
import Hero from '../../../components/Hero.astro';
import WipBanner from '../../../components/WipBanner.astro';
import { entryFor, robotsFor } from '../../../data/design-index';

const entry = entryFor('logo');

const VARIANTS = ['hero', 'plain', 'flat'] as const;
const TRAILS = ['swash', 'stroke'] as const;
---
```

Replace the opening `<BaseLayout ...>` tag with:

```astro
<BaseLayout title={entry.title} description={entry.blurb}
            bodyClass="logo-lab logo-anim-demo" robots={robotsFor(entry.status)}>
  <WipBanner />
```

- [ ] **Step 4: Fold in the demo markup, styles and script**

From `src/pages/logo-animation.astro`, copy three regions into `src/pages/design/ao/logo.astro`:

1. Lines 9–128 (the `<main class="la-demo">` element, opening and closing tags included). Paste it inside the `<BaseLayout>`, immediately after `<WipBanner />` and *before* the existing `<main class="lab">`.
2. Lines 131–194 and 328–430 (both `<style is:global>` blocks, tags included). Paste both immediately after the lab's own `<style is:global>…</style>` block, which is the first style block in the destination file.
3. Lines 196–326 (the `<script>` block, tags included). Paste at the very end of the destination file, after the lab's own `<script>…</script>` block.

Locate the destination positions **structurally**, by finding the lab's existing `</style>` and `</script>` closing tags. Do not use line numbers from this plan for the destination file: Step 3 rewrote its frontmatter, so every line number below that point has shifted. The source line ranges above are accurate, because `logo-animation.astro` is untouched until Step 4 completes.

Astro bundles each `<script>` tag as its own module, so the two scripts' top-level declarations cannot collide.

Then delete the now-empty source file:

```bash
git rm src/pages/logo-animation.astro
```

- [ ] **Step 5: Fix the `data-size` collision**

In `src/pages/design/ao/logo.astro`, rename the lab's four size preset buttons (originally `logo-lab.astro:61-64`) from `data-size` to `data-lab-size`:

```astro
            <button type="button" data-lab-size="26">26 blog nav</button>
            <button type="button" data-lab-size="44">44 footer</button>
            <button type="button" data-lab-size="120">120</button>
            <button type="button" data-lab-size="280">280</button>
```

And in the lab's script, replace this loop (originally `logo-lab.astro:356-361`) in full:

```ts
  for (const b of document.querySelectorAll<HTMLButtonElement>('[data-size]')) {
    b.addEventListener('click', () => {
      state.size = Number(b.dataset.size);
      $<HTMLInputElement>('input[name="size"]').value = String(state.size); apply();
    });
  }
```

with:

```ts
  for (const b of document.querySelectorAll<HTMLButtonElement>('[data-lab-size]')) {
    b.addEventListener('click', () => {
      state.size = Number(b.dataset.labSize);
      $<HTMLInputElement>('input[name="size"]').value = String(state.size); apply();
    });
  }
```

Note the dataset key changes too: `data-lab-size` reads as `b.dataset.labSize`. The adjacent `[data-speed]` loop is untouched; `data-speed` appears in only one of the two source files.

- [ ] **Step 6: Run the test to verify it passes**

Run: `npm run build && npm run test:routes`

Expected: PASS, 6 tests. The build log lists `/design/ao/logo/index.html` and no longer lists `/logo-lab/index.html` or `/logo-animation/index.html`.

- [ ] **Step 7: Verify both control sets work in a browser**

The static tests cannot prove the scripts still drive the page. Run `npm run dev`, open `http://localhost:4321/design/ao/logo/`, and confirm all four:

1. The demo's **Replay** button restarts the animation.
2. The demo's **Scrub** slider moves the animation.
3. The lab's **variant** and **trail** radios swap the displayed mark.
4. Clicking a PNG download button (**512** or **1024**) downloads a file and does **not** change the lab stage's size. This is the collision regression; check it explicitly.

- [ ] **Step 8: Commit**

```bash
git add -A src/pages/design/ao/logo.astro scripts/routes.test.mjs
git commit -m "feat(design): merge the logo demo and bench into one page

/logo-animation/ and /logo-lab/ become /design/ao/logo/. The body carries
both original classes so neither is:global style block needs rewriting.

Renames the lab's size presets to data-lab-size: the lab wired its presets
with a document-wide [data-size] query, which after the merge would also
have matched the PNG download buttons and resized the stage on download."
```

---

### Task 3: The `/design/ao/` index

**Files:**
- Create: `src/pages/design/ao/index.astro`
- Modify: `scripts/routes.test.mjs`

**Interfaces:**
- Consumes: `DESIGN_ENTRIES` from `src/data/design-index`.
- Produces: the route `/design/ao/`.

This page is **not** a registry entry. It carries no WIP banner and never lists itself. It ships `noindex, nofollow` and unlinked while every entry is `wip`.

- [ ] **Step 1: Write the failing test**

Append to `scripts/routes.test.mjs`:

```js
test('/design/ao/ lists every entry and is itself noindex', async () => {
  const doc = await html('design/ao');
  assert.equal(robotsOf(doc), 'noindex, nofollow');
  assert.match(doc, /href="\/design\/ao\/logo\/"/);
  assert.match(doc, /href="\/design\/ao\/typeface\/"/);
});

test('/design/ao/ does not list itself and carries no WIP banner', async () => {
  const doc = await html('design/ao');
  assert.doesNotMatch(doc, /href="\/design\/ao\/"/);
  assert.doesNotMatch(doc, /Work in progress\./);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run build && npm run test:routes`

Expected: FAIL, two `ENOENT` errors on `dist/design/ao/index.html`.

- [ ] **Step 3: Create the index page**

Create `src/pages/design/ao/index.astro`:

```astro
---
// The AO identity system: everything derived from the mark.
//
// Not a design-index entry itself. Index pages are infrastructure, so this one
// never lists itself and carries no WIP banner. It stays noindex and unlinked
// until the first entry reaches `ready`.
import BaseLayout from '../../../layouts/BaseLayout.astro';
import { DESIGN_ENTRIES } from '../../../data/design-index';
---
<BaseLayout title="AO — Austin Orphan" description="The AO identity system: the mark, the typeface, and the work behind them."
            bodyClass="design-index" robots="noindex, nofollow">
  <main class="dx">
    <h1>AO</h1>
    <p class="dx-lede">The mark, the typeface, and the work behind them.</p>
    <ul class="dx-list">
      {DESIGN_ENTRIES.map((e) => (
        <li class="dx-item">
          <a href={`/design/ao/${e.slug}/`}>{e.title}</a>
          {e.status === 'wip' && <span class="dx-tag">in progress</span>}
          <p class="dx-blurb">{e.blurb}</p>
        </li>
      ))}
    </ul>
  </main>
</BaseLayout>

<style is:global>
  .design-index { background: var(--color-background); color: var(--color-primary); }
  .dx { max-width: 1180px; margin: 0 auto; padding: 84px 24px 96px; }
  .dx > h1 { margin: 0 0 8px; font-size: 1.5rem; letter-spacing: 0.02em; }
  .dx-lede { margin: 0 0 40px; color: rgba(var(--color-primary-rgb), 0.6); }
  .dx-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 26px; }
  .dx-item a { color: var(--color-primary); font-size: 1.05rem; text-decoration: none; }
  .dx-item a:hover { color: var(--color-accent); }
  .dx-tag {
    margin-left: 10px;
    padding: 2px 8px;
    border: 1px solid rgba(var(--color-primary-rgb), 0.28);
    border-radius: 999px;
    color: rgba(var(--color-primary-rgb), 0.55);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .dx-blurb { margin: 6px 0 0; color: rgba(var(--color-primary-rgb), 0.6); font-size: 0.88rem; }
</style>
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run build && npm run test:routes`

Expected: PASS, 8 tests.

- [ ] **Step 5: Commit**

```bash
git add src/pages/design/ao/index.astro scripts/routes.test.mjs
git commit -m "feat(design): add the /design/ao/ index

Lists every design-index entry with an in-progress tag. Not an entry itself,
so it never lists itself and carries no WIP banner."
```

---

### Task 4: The `/lab/` index

**Files:**
- Create: `src/pages/lab.astro`
- Modify: `scripts/routes.test.mjs`

**Interfaces:**
- Consumes: `wipEntries` from `src/data/design-index`.
- Produces: the route `/lab/`.

`/lab/` is a **view**, not a location. Nothing lives under it, and it is not a registry entry.

- [ ] **Step 1: Write the failing test**

Append to `scripts/routes.test.mjs`:

```js
test('/lab/ lists only wip entries, at their permanent URLs', async () => {
  const doc = await html('lab');
  assert.equal(robotsOf(doc), 'noindex, nofollow');
  assert.match(doc, /href="\/design\/ao\/logo\/"/);
  assert.match(doc, /href="\/design\/ao\/typeface\/"/);
});

test('/lab/ is not a URL prefix: no page is built beneath it', async () => {
  const { existsSync } = await import('node:fs');
  assert.ok(!existsSync(pagePath('lab/typeface')));
  assert.ok(!existsSync(pagePath('lab/logo')));
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run build && npm run test:routes`

Expected: FAIL. The first test errors with `ENOENT` on `dist/lab/index.html`. The second already passes, which is correct: it is a guard against a future regression, not a driver of this task.

- [ ] **Step 3: Create the lab index**

Create `src/pages/lab.astro`:

```astro
---
// A view, not a location. Nothing lives under /lab/; this lists entries whose
// status is `wip`, each linked at its own permanent URL. An entry leaves this
// page by becoming `ready` in src/data/design-index.ts, which never moves it.
//
// Not a design-index entry itself, so it carries no WIP banner.
import BaseLayout from '../layouts/BaseLayout.astro';
import { wipEntries } from '../data/design-index';

const entries = wipEntries();
---
<BaseLayout title="Lab — Austin Orphan" description="Work in progress: unfinished and unlisted pages."
            bodyClass="lab-index" robots="noindex, nofollow">
  <main class="lx">
    <h1>Lab</h1>
    <p class="lx-lede">
      Unfinished work, each at the URL it will keep when it is done. Things
      here may change or break without warning.
    </p>
    {entries.length === 0 ? (
      <p class="lx-empty">Nothing in progress right now.</p>
    ) : (
      <ul class="lx-list">
        {entries.map((e) => (
          <li class="lx-item">
            <a href={`/design/ao/${e.slug}/`}>{e.title}</a>
            <p class="lx-blurb">{e.blurb}</p>
          </li>
        ))}
      </ul>
    )}
  </main>
</BaseLayout>

<style is:global>
  .lab-index { background: var(--color-background); color: var(--color-primary); }
  .lx { max-width: 1180px; margin: 0 auto; padding: 84px 24px 96px; }
  .lx > h1 { margin: 0 0 8px; font-size: 1.5rem; letter-spacing: 0.02em; }
  .lx-lede { margin: 0 0 40px; max-width: 56ch; color: rgba(var(--color-primary-rgb), 0.6); }
  .lx-empty { color: rgba(var(--color-primary-rgb), 0.5); }
  .lx-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 26px; }
  .lx-item a { color: var(--color-primary); font-size: 1.05rem; text-decoration: none; }
  .lx-item a:hover { color: var(--color-accent); }
  .lx-blurb { margin: 6px 0 0; color: rgba(var(--color-primary-rgb), 0.6); font-size: 0.88rem; }
</style>
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run build && npm run test:routes`

Expected: PASS, 10 tests.

- [ ] **Step 5: Commit**

```bash
git add src/pages/lab.astro scripts/routes.test.mjs
git commit -m "feat(lab): add /lab/, a view over everything unfinished

Lists wip entries at their permanent URLs. /lab/ is never a path prefix, so
an entry graduating changes only its status, never its URL."
```

---

### Task 5: Redirect the three old paths

**Files:**
- Modify: `astro.config.mjs`
- Modify: `scripts/routes.test.mjs`

**Interfaces:**
- Consumes: the routes built in Tasks 1 and 2.
- Produces: redirect stubs at the three former paths.

The old paths are `noindex`, unlinked, and have zero inbound links anywhere in `src/`, so nothing breaks without this. It is cheap insurance for existing browser history and bookmarks.

- [ ] **Step 1: Write the failing test**

Append to `scripts/routes.test.mjs`:

```js
for (const [from, to] of [
  ['orphan-display', '/design/ao/typeface/'],
  ['logo-animation', '/design/ao/logo/'],
  ['logo-lab', '/design/ao/logo/'],
]) {
  test(`/${from}/ redirects to ${to}`, async () => {
    const doc = await html(from);
    assert.match(doc, /http-equiv="refresh"/i, 'no meta refresh emitted');
    assert.ok(doc.includes(to), `stub does not point at ${to}`);
  });
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run build && npm run test:routes`

Expected: FAIL, three `ENOENT` errors on `dist/orphan-display/index.html`, `dist/logo-animation/index.html` and `dist/logo-lab/index.html`.

- [ ] **Step 3: Add the redirects**

In `astro.config.mjs`, add a `redirects` key inside `defineConfig`, after `trailingSlash`:

```js
  // The three former bench paths. All were noindex and unlinked, so this is for
  // existing bookmarks and history rather than for search engines. Static output
  // emits a meta-refresh stub per entry.
  redirects: {
    '/orphan-display': '/design/ao/typeface/',
    '/logo-animation': '/design/ao/logo/',
    '/logo-lab': '/design/ao/logo/',
  },
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run build && npm run test:routes`

Expected: PASS, 13 tests.

If a test fails on the `http-equiv="refresh"` assertion rather than on `ENOENT`, the stub was emitted but in a different shape. Inspect the real output with `cat dist/logo-lab/index.html` and relax that one assertion to match what Astro actually emits. Keep the `doc.includes(to)` assertion either way: the destination path must appear.

- [ ] **Step 5: Commit**

```bash
git add astro.config.mjs scripts/routes.test.mjs
git commit -m "feat(design): redirect the three former bench paths

Covers existing bookmarks and history. The old paths were noindex and
unlinked, so no search ranking or inbound links are at stake."
```

---

## Final verification

- [ ] Run the full suite: `npm test`. Expected: PASS, 13 tests.
- [ ] Run `npm run check`. Expected: the roughly 155 pre-existing DOM typing errors documented in `CLAUDE.md`, and **no new errors** in `src/data/design-index.ts`, `src/components/WipBanner.astro`, or any page under `src/pages/design/`. Compare against `git stash`-ing the branch if unsure of the baseline count.
- [ ] Confirm the build emits exactly these routes and no stale ones:

```bash
npm run build 2>&1 | grep -E "design/ao|/lab/|orphan-display|logo-lab|logo-animation"
```

Expected: `/design/ao/index.html`, `/design/ao/logo/index.html`, `/design/ao/typeface/index.html`, `/lab/index.html`, plus the three redirect stubs.

- [ ] Open `npm run dev` and walk `/lab/` → `/design/ao/typeface/` → back, and `/lab/` → `/design/ao/logo/` → back. Every link resolves, no 404s.
- [ ] Confirm nothing links to these pages from the live site: `grep -rn "design/ao\|/lab/" src/components src/layouts src/pages/index.astro` should return only `WipBanner.astro`'s own `/lab/` link.
