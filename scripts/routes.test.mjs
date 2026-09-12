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

test('the merged logo page has exactly one <main> and an h1 matching its title', async () => {
  const doc = await html('design/ao/logo');
  assert.equal((doc.match(/<main[\s>]/g) ?? []).length, 1, 'merging left two <main> elements');
  assert.match(doc, /<h1>The AO mark<\/h1>/);
});

// BaseLayout owns the robots directive. A page that adds its own tag leaves two
// conflicting directives in one document, which is how a deliberately-private
// page ends up advertising index,follow. Caught one of these by hand; now it is
// enforced for every route the site builds.
for (const route of ['design/ao', 'design/ao/logo', 'design/ao/typeface', 'lab']) {
  test(`/${route}/ emits exactly one robots tag, and it is noindex`, async () => {
    const doc = await html(route);
    const tags = doc.match(/<meta name="robots"[^>]*>/g) ?? [];
    assert.equal(tags.length, 1, `expected one robots tag, found ${tags.length}: ${tags.join(' | ')}`);
    assert.equal(robotsOf(doc), 'noindex, nofollow');
  });
}

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
