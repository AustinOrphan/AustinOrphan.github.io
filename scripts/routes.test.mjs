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
