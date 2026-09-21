// Asserts on built output in dist/, so it exercises the real Astro build rather
// than module internals. Run `npm run build` first, or use `npm test` which
// chains both. The first test below fails loudly if dist/ is older than the
// sources, so `npm run test:routes` on a stale build cannot report a false pass.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir, stat } from 'node:fs/promises';
import { existsSync, readdirSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
// Node strips the types natively, so the registry is testable with no build step
// and no dependency.
import { DESIGN_ENTRIES, entryFor, robotsFor, wipEntries } from '../src/data/design-index.ts';
import { endMs } from '../src/components/logo-timing.ts';

const ROOT = join(import.meta.dirname, '..');
const DIST = join(ROOT, 'dist');

/** Built path for a route. Astro's default directory format means every page
 *  lands at <route>/index.html. Pass the route without leading or trailing
 *  slashes, e.g. 'design/ao/typeface'. */
export function pagePath(route) {
  return join(DIST, route, 'index.html');
}

export async function html(route) {
  return readFile(pagePath(route), 'utf8');
}

/** BaseLayout emits exactly one robots tag, in this exact shape. Deliberately
 *  reads only the first match; `robotsTags` below is what proves there is one. */
export function robotsOf(doc) {
  const m = doc.match(/<meta name="robots" content="([^"]*)">/);
  return m?.[1] ?? null;
}

export function robotsTags(doc) {
  return doc.match(/<meta name="robots"[^>]*>/g) ?? [];
}

/** The document with every <script> body blanked. An assertion about markup must
 *  run against this: `/data-stage/` is otherwise satisfied by the selector string
 *  inside the lab's own script, so the test passes with the element deleted. */
export function markup(doc) {
  return doc.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '<script></script>');
}

/** '/design/ao/logo/' -> 'design/ao/logo' */
const routeOf = (href) => href.replace(/^\/+|\/+$/g, '');

/** All JavaScript a route actually loads: its inline scripts plus every local
 *  module it pulls from /_astro/. Astro bundles a page's <script> blocks out to
 *  those files, so an assertion about page behaviour has to read them too. */
export async function scriptsOf(route) {
  const doc = await html(route);
  const inline = [...doc.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map((m) => m[1]);
  const srcs = [...doc.matchAll(/<script\b[^>]*\bsrc="(\/_astro\/[^"]+)"/gi)].map((m) => m[1]);
  const bundled = await Promise.all(srcs.map((s) => readFile(join(DIST, s), 'utf8')));
  return [...inline, ...bundled].join('\n');
}

/** Every built page, as a route string. */
function builtRoutes() {
  const out = [];
  const walk = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      const p = join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name === 'index.html') {
        const r = relative(DIST, dir).split(sep).join('/');
        out.push(r === '' ? '' : r);
      }
    }
  };
  walk(DIST);
  return out.sort();
}

const newest = async (dir, acc = { mtime: 0, file: '' }) => {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    if (e.name === 'node_modules' || e.name.startsWith('.')) continue;
    const p = join(dir, e.name);
    if (e.isDirectory()) await newest(p, acc);
    else {
      const { mtimeMs } = await stat(p);
      if (mtimeMs > acc.mtime) { acc.mtime = mtimeMs; acc.file = p; }
    }
  }
  return acc;
};

// Everything below asserts on dist/. If dist/ predates the sources -- a plain
// `npm run test:routes`, or a branch switch without a rebuild -- those assertions
// describe some other build, and a green run means nothing.
test('dist/ is newer than the sources it is built from', async () => {
  assert.ok(existsSync(pagePath('')), 'dist/ has no index.html; run `npm run build`');
  const built = (await stat(pagePath(''))).mtimeMs;
  const src = await newest(join(ROOT, 'src'));
  const cfg = (await stat(join(ROOT, 'astro.config.mjs'))).mtimeMs;
  const newestSrc = cfg > src.mtime ? { mtime: cfg, file: 'astro.config.mjs' } : src;
  assert.ok(
    built >= newestSrc.mtime,
    `dist/ is stale: ${relative(ROOT, newestSrc.file)} changed ` +
      `${Math.round((newestSrc.mtime - built) / 1000)}s after the last build. Run \`npm run build\`.`,
  );
});

test('/design/ao/typeface/ is built, noindex, and carries the WIP banner', async () => {
  const doc = await html('design/ao/typeface');
  assert.equal(robotsOf(doc), 'noindex, nofollow');
  assert.match(doc, /<title>Orphan Display<\/title>/, 'the typeface page title drifted from the registry');
  assert.match(doc, /Work in progress\./, '/design/ao/typeface/ lost its WipBanner');
});

test('the typeface page still renders its specimen controls', async () => {
  const doc = markup(await html('design/ao/typeface'));
  assert.match(doc, /Regular Flat/, 'the typeface specimen presets are missing');
});

test('/design/ao/logo/ is built, noindex, and carries the WIP banner', async () => {
  const doc = await html('design/ao/logo');
  assert.equal(robotsOf(doc), 'noindex, nofollow');
  assert.match(doc, /<title>The AO mark<\/title>/, 'the logo page title drifted from the registry');
  assert.match(doc, /Work in progress\./, '/design/ao/logo/ lost its WipBanner');
});

test('/design/ao/logo/ contains both the demo and the lab', async () => {
  // Against markup(), not the raw file: both of these strings also occur inside
  // the page's scripts, so the raw document would pass with the elements gone.
  const doc = markup(await html('design/ao/logo'));
  assert.match(doc, /data-la-replay/, 'the demo replay control is missing');
  assert.match(doc, /data-stage/, 'the lab stage is missing');
});

test('both body classes are present, so both style blocks apply', async () => {
  const doc = await html('design/ao/logo');
  assert.match(
    doc,
    /<body class="logo-lab logo-anim-demo">/,
    'body lost one of the two classes the merged style blocks are keyed to',
  );
});

test('the lab size presets no longer collide with the download panel', async () => {
  const doc = markup(await html('design/ao/logo'));
  assert.match(doc, /data-lab-size="280"/, 'lab presets were not renamed');
  assert.match(doc, /data-dl-size/, 'the download panel lost its size control');
  // The download panel's fixed 512/1024 PNG buttons are gone -- one `data-dl-size` select
  // drives every download now -- so no bare `data-size` should remain anywhere. The lab wires
  // its presets with a document-wide querySelectorAll, which is what made the collision.
  const bare = [...doc.matchAll(/data-size="(\d+)"/g)].map((m) => m[1]).sort();
  assert.deepEqual(bare, [], 'a data-size reappeared; the lab presets would pick it up');
});

// The page used to state 1300ms for hero and 1100ms where the choreography actually ends at
// 1360 and 1160, so the scrub stopped 60ms short -- precisely where the hero treatment settles
// -- and every caption lied. Both numbers now come from logo-timing.ts, which derives them from
// the generated logo-choreography.ts. Asserted against the derivation rather than a literal, so
// retiming the mark moves the page and this test together.
// Both scrubs, because the lab's is server-rendered too: its initial max is what the page
// shows before any script runs, and it held the stale 1300 long after the demo's did.
test('both scrubs span the whole write-on, derived rather than remembered', async () => {
  const doc = markup(await html('design/ao/logo'));
  const scrubs = {
    demo: doc.match(/<input[^>]*data-la-scrub[^>]*>/)?.[0],
    lab: doc.match(/<input[^>]*name="scrub"[^>]*>/)?.[0],
  };
  for (const [which, input] of Object.entries(scrubs)) {
    assert.ok(input, `the ${which} scrub is missing`);
    assert.equal(
      Number(input.match(/max="(\d+)"/)?.[1]),
      endMs('hero'),
      `the ${which} scrub no longer spans the write-on; it is restating a duration instead of deriving it`,
    );
  }
});

test('the speed captions state the choreography they actually run at', async () => {
  const doc = markup(await html('design/ao/logo'));
  for (const speed of [0.5, 1, 2]) {
    const caption = `speed=${speed} — ${(endMs('hero', speed) / 1000).toFixed(2)}s`;
    assert.ok(doc.includes(caption), `the demo is missing or misstates "${caption}"`);
  }
});

test('the demo replay is scoped to the demo, not to the whole document', async () => {
  // Document-wide, the demo's mark list also caught the lab's six stage slots and
  // three in-situ marks, which ship autoplay={false} on purpose, so Replay animated
  // panels nobody clicked. Asserted against the page's own scripts rather than the
  // markup; the minifier picks its own quote characters, so match the selector text.
  const js = await scriptsOf('design/ao/logo');
  assert.match(js, /\.la-demo\s+\.site-logo-anim/, "the demo's mark list lost its .la-demo scope");
});

test('the merged logo page has exactly one <main>, and its h1 leads the document', async () => {
  const doc = markup(await html('design/ao/logo'));
  assert.equal((doc.match(/<main[\s>]/g) ?? []).length, 1, 'merging left two <main> elements');
  assert.match(doc, /<h1 class="la-title">The AO mark<\/h1>/, 'the page title is missing or renamed');
  // The demo owns a "Download" h2 and sits before <main>, so the h1 has to come
  // first in the document or the page opens on a level-2 heading.
  const headings = [...doc.matchAll(/<(h[1-6])[\s>]/g)].map((m) => m[1]);
  assert.equal(headings[0], 'h1', `first heading is ${headings[0]}, not h1`);
});

// BaseLayout owns the robots directive. A page that adds its own tag leaves two
// conflicting directives in one document, which is how a deliberately-private
// page ends up advertising index,follow. Caught one of these by hand; now it is
// enforced for every route the site builds.
for (const route of ['design/ao', 'design/ao/logo', 'design/ao/typeface', 'lab']) {
  test(`/${route}/ emits exactly one robots tag, and it is noindex`, async () => {
    const doc = await html(route);
    const tags = robotsTags(doc);
    assert.equal(tags.length, 1, `expected one robots tag, found ${tags.length}: ${tags.join(' | ')}`);
    assert.equal(robotsOf(doc), 'noindex, nofollow');
  });
}

// The loop above names its routes, so it cannot see a page added later. This one
// reads the built tree, so a new page under /design/ao/ is covered the day it
// appears -- including one whose author forgot a registry entry and so shipped
// BaseLayout's index,follow default.
test('every built page under /design/ao/ is in the registry and is noindex', async () => {
  const slugs = readdirSync(join(DIST, 'design', 'ao'), { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);
  const known = new Set(DESIGN_ENTRIES.map((e) => e.slug));
  for (const slug of slugs) {
    assert.ok(known.has(slug), `/design/ao/${slug}/ is built but has no DESIGN_ENTRIES entry`);
    const doc = await html(`design/ao/${slug}`);
    assert.equal(robotsTags(doc).length, 1, `/design/ao/${slug}/ does not emit exactly one robots tag`);
    assert.equal(robotsOf(doc), robotsFor(entryFor(slug).status), `/design/ao/${slug}/ robots does not match its status`);
  }
  assert.ok(slugs.length >= DESIGN_ENTRIES.length, 'a registry entry has no built page');
});

// The other direction: an entry with no page makes /design/ao/ and /lab/ link a 404.
for (const e of DESIGN_ENTRIES) {
  test(`registry entry "${e.slug}" has a page at /design/ao/${e.slug}/`, () => {
    assert.ok(
      existsSync(pagePath(`design/ao/${e.slug}`)),
      `DESIGN_ENTRIES lists "${e.slug}" but dist/design/ao/${e.slug}/index.html does not exist`,
    );
  });
}

test('/design/ao/ lists every entry and is itself noindex', async () => {
  const doc = await html('design/ao');
  assert.equal(robotsOf(doc), 'noindex, nofollow');
  for (const e of DESIGN_ENTRIES) {
    assert.match(doc, new RegExp(`href="/design/ao/${e.slug}/"`), `/design/ao/ does not link ${e.slug}`);
  }
});

test('/design/ao/ does not list itself and carries no WIP banner', async () => {
  const doc = await html('design/ao');
  assert.doesNotMatch(doc, /href="\/design\/ao\/"/, '/design/ao/ links itself');
  assert.doesNotMatch(doc, /Work in progress\./, '/design/ao/ should not carry the WIP banner');
});

test('/lab/ lists only wip entries, at their permanent URLs', async () => {
  const doc = await html('lab');
  assert.equal(robotsOf(doc), 'noindex, nofollow');
  const linked = [...doc.matchAll(/href="\/design\/ao\/([^/"]+)\/"/g)].map((m) => m[1]).sort();
  assert.deepEqual(linked, wipEntries().map((e) => e.slug).sort(), '/lab/ listing drifted from wipEntries()');
});

test('every link /lab/ and /design/ao/ emit resolves to a built page', async () => {
  for (const route of ['lab', 'design/ao']) {
    const doc = await html(route);
    for (const m of doc.matchAll(/href="(\/design\/ao\/[^"]*)"/g)) {
      assert.ok(existsSync(pagePath(routeOf(m[1]))), `/${route}/ links ${m[1]}, which is not built`);
    }
  }
});

test('/lab/ is not a URL prefix: no page is built beneath it', () => {
  for (const e of DESIGN_ENTRIES) {
    assert.ok(!existsSync(pagePath(`lab/${e.slug}`)), `/lab/${e.slug}/ was built; /lab/ must stay a view`);
  }
});

for (const [from, to] of [
  ['orphan-display', '/design/ao/typeface/'],
  ['logo-animation', '/design/ao/logo/'],
  ['logo-lab', '/design/ao/logo/'],
]) {
  test(`/${from}/ meta-refreshes to exactly ${to}, which is built`, async () => {
    const doc = await html(from);
    const m = doc.match(/http-equiv="refresh" content="0;url=([^"]+)"/i);
    assert.ok(m, 'no meta refresh emitted');
    // includes() would pass for a stub pointing anywhere that merely contains
    // this string, and would not notice the target being deleted.
    assert.equal(m[1], to, `stub points at ${m[1]}`);
    assert.ok(existsSync(pagePath(routeOf(to))), `${to} is not built, so the redirect lands on a 404`);
  });
}

// The restructure must not have changed the robots directive anywhere else, and
// this doubles as proof that the home page and the blog still build at all.
test('no page outside /design/ao/ and /lab/ became noindex', async () => {
  const noindex = new Set(['lab', 'design/ao', ...DESIGN_ENTRIES.map((e) => `design/ao/${e.slug}`)]);
  const stubs = new Set(['orphan-display', 'logo-animation', 'logo-lab']);
  const routes = builtRoutes();
  assert.ok(routes.includes(''), 'the home page was not built');
  assert.ok(routes.includes('blog'), 'the blog index was not built');
  for (const r of routes) {
    const doc = await html(r);
    if (stubs.has(r)) continue; // Astro writes its own noindex on redirect stubs
    const tags = robotsTags(doc);
    assert.equal(tags.length, 1, `/${r}/ emits ${tags.length} robots tags: ${tags.join(' | ')}`);
    assert.equal(robotsOf(doc), noindex.has(r) ? 'noindex, nofollow' : 'index,follow', `/${r}/ has the wrong robots directive`);
  }
});

// The registry helpers, directly. robotsFor('ready') and entryFor()'s throw are
// the graduation path, which no built page exercises while every entry is wip.
test('robotsFor maps both statuses', () => {
  assert.equal(robotsFor('wip'), 'noindex, nofollow');
  assert.equal(robotsFor('ready'), 'index,follow');
});

test('wipEntries returns exactly the wip entries', () => {
  assert.deepEqual(
    wipEntries().map((e) => e.slug),
    DESIGN_ENTRIES.filter((e) => e.status === 'wip').map((e) => e.slug),
  );
});

test('entryFor throws on an unknown slug rather than returning undefined', () => {
  assert.throws(() => entryFor('no-such-page'), /No design-index entry for slug "no-such-page"/);
});

// ---------------------------------------------------------------------------
// global.css gives every anchor `display: flex; width: 100%; justify-content:
// center`, which the hero link bar wants and running prose very much does not:
// an unguarded link takes the whole column and centres itself on its own line,
// so the sentence around it breaks into three pieces. Four components have been
// caught by eye this way -- the WIP banner, both index pages, and the blog body
// -- each found only because someone looked at the page.
//
// Resolving this properly means computing styles, which needs a browser. It is
// tractable statically here only because the stylesheet uses plain
// class-descendant selectors, so "does a rule match this anchor" is a question
// about class tokens. If that stops being true, this should become a browser
// check rather than a cleverer parser.

/** Every rule that sets `display`, as {tokens, tag, display}. Reads minified
 *  output, so selectors arrive without whitespace to spare. */
function displayRules(css) {
  const out = [];
  for (const m of css.matchAll(/([^{}@]+)\{([^{}]*)\}/g)) {
    const d = /display:\s*([a-z-]+)/.exec(m[2]);
    if (!d) continue;
    for (const sel of m[1].split(',')) {
      const s = sel.trim();
      if (!s || s.includes('[') || s.includes('(')) continue;
      const last = s.split(/\s+|>/).filter(Boolean).pop() ?? '';
      out.push({
        tokens: [...s.matchAll(/\.([A-Za-z0-9_-]+)/g)].map((c) => c[1]),
        tag: /^[a-z]/.test(last) ? last.split(/[.:]/)[0] : null,
        display: d[1],
      });
    }
  }
  return out;
}

/** All CSS a page actually applies: its linked stylesheets plus its inline
 *  <style> blocks. Astro inlines the small ones, and the component overrides
 *  this test is about are exactly the small ones. */
async function cssOf(route) {
  const doc = await html(route);
  const hrefs = [...doc.matchAll(/<link[^>]+rel="stylesheet"[^>]+href="(\/_astro\/[^"]+)"/g)].map((m) => m[1]);
  const linked = await Promise.all(hrefs.map((h) => readFile(join(DIST, h), 'utf8')));
  const inline = [...doc.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => m[1]);
  return [...linked, ...inline].join('\n');
}

/** Anchors sitting inside a <p>, with the class chain of their ancestors.
 *  A <p> is the marker for running text; nav lists and link bars are not it. */
function anchorsInProse(doc) {
  const body = doc.slice(doc.indexOf('<body'));
  const VOID = new Set(['meta', 'link', 'img', 'br', 'hr', 'input', 'source', 'path', 'use', 'circle', 'rect', 'stop']);
  const stack = [];
  const found = [];
  for (const m of body.matchAll(/<(\/?)([a-zA-Z][a-zA-Z0-9-]*)([^>]*?)(\/?)>/g)) {
    const [, closing, rawTag, attrs, selfClose] = m;
    const tag = rawTag.toLowerCase();
    if (closing) {
      for (let i = stack.length - 1; i >= 0; i--) {
        if (stack[i].tag === tag) { stack.length = i; break; }
      }
      continue;
    }
    const classes = (/class="([^"]*)"/.exec(attrs)?.[1] ?? '').split(/\s+/).filter(Boolean);
    if (tag === 'a') {
      const p = stack[stack.length - 1];
      if (p && p.tag === 'p') {
        found.push({ own: classes, parent: p, chain: stack.flatMap((s) => s.classes) });
      }
    }
    if (!VOID.has(tag) && !selfClose) stack.push({ tag, classes });
  }
  return found;
}

const matches = (rule, chain, own, tag) =>
  (rule.tag === null || rule.tag === tag) && rule.tokens.every((t) => chain.includes(t) || own.includes(t));

test('no link in running prose inherits the global full-width flex reset', async () => {
  const offenders = [];
  for (const route of builtRoutes()) {
    const doc = await html(route);
    const anchors = anchorsInProse(doc);
    if (!anchors.length) continue;
    const rules = displayRules(await cssOf(route));
    const anchorRules = rules.filter((r) => r.tag === 'a');
    for (const a of anchors) {
      // A <p> that is itself a flex container means these anchors are flex items
      // on purpose -- the typeface page's download pills are laid out that way.
      const parentIsFlex = rules.some(
        (r) => r.display === 'flex' && r.tag !== 'a' && r.tokens.length
          && r.tokens.every((t) => a.parent.classes.includes(t)),
      );
      if (parentIsFlex) continue;
      const winner = anchorRules.filter((r) => matches(r, a.chain, a.own, 'a')).pop();
      if (winner && winner.display === 'flex') {
        offenders.push(`/${route || ''} <p class="${a.parent.classes.join(' ')}">`);
      }
    }
  }
  assert.deepEqual(
    [...new Set(offenders)],
    [],
    'these prose links render as full-width centred flex blocks; add `display: inline; width: auto; height: auto`',
  );
});
