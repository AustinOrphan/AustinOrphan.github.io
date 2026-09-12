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
