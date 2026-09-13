#!/usr/bin/env node
// Every file that carries the mark by hand, checked against the one source of truth.
//
// This repo has shipped a stale derived artifact twice. The icons showed the old mark after
// the mark was re-derived -- make-icons.mjs' own header says "which is exactly what happened"
// -- and public/fonts/ lagged its sources by a day and served a font whose weight axis moved
// almost nothing. Both were found by a person noticing something looked wrong.
//
// The mark's outline is embedded verbatim as text in every hand-maintained copy, so one string
// compare covers that whole class with no dependencies, no Chrome and no npm install. It runs
// in milliseconds, which is the point: it can run on every push without being in the way.
//
// What this does NOT cover: the rendered PNGs and the .ico, which are binary and need sharp --
// scripts/make-icons.mjs --check covers those and CI runs it alongside this. Nor the variable
// font, which would need a six-minute rebuild to verify; build_variable.py installs what it
// builds now, so the hand-copy step that caused that one is gone.
//
//   node scripts/check-derived.mjs
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, relative } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const rel = (p) => relative(ROOT, p);

/** A named path export out of logo-mark.ts.
 *
 *  Anchored to the export name, not to "the first long quoted string in the file". That file
 *  holds more than one path now, and a positional match silently picks whichever happens to be
 *  first -- which is exactly the kind of quiet wrong answer this script exists to catch. */
function pathExport(src, name) {
  const m = src.match(new RegExp(`export const ${name}\\s*=\\s*['"\`]([^'"\`]+)['"\`]`));
  if (!m) throw new Error(`${name} not found in src/components/logo-mark.ts`);
  return m[1];
}

const markTs = join(ROOT, 'src/components/logo-mark.ts');
if (!existsSync(markTs)) throw new Error('src/components/logo-mark.ts is missing');
const src = readFileSync(markTs, 'utf8');
const MARK = pathExport(src, 'LOGO_MARK_D');

// Files that embed the mark's outline as literal text. A missing file is a failure, not a skip:
// a rename must not make this pass by having nothing left to check.
const CARRIERS = [
  'public/favicon.svg',
  'public/safari-pinned-tab.svg',
  'docs/og-image.html',
  'docs/repo-social-preview.html',
];

const stale = [];
for (const f of CARRIERS) {
  const p = join(ROOT, f);
  if (!existsSync(p)) throw new Error(`${f} is listed as carrying the mark but does not exist`);
  if (!readFileSync(p, 'utf8').includes(MARK)) stale.push(f);
}

if (stale.length) {
  console.error(`  ${stale.length} file(s) carry a mark that is not the derived one:`);
  for (const f of stale) console.error(`    ${f}`);
  console.error('\n  The mark lives in src/components/logo-mark.ts (LOGO_MARK_D), derived by');
  console.error('  font/measure/mark_derived.py. Re-run the generator that owns each file:');
  console.error('    node scripts/make-icons.mjs        public/favicon.svg, public/safari-pinned-tab.svg');
  console.error('    node scripts/make-og-image.mjs     docs/og-image.html');
  console.error('    docs/repo-social-preview.html has no generator; paste the path in by hand.');
  process.exitCode = 1;
} else {
  console.log(`  ${CARRIERS.length} carriers all hold the derived mark (${MARK.length} chars)`);
}
