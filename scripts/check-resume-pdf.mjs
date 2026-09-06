#!/usr/bin/env node
/**
 * Sanity-check a freshly exported resume before it is allowed to replace the
 * one on the site.
 *
 * The failure this exists for: Google's export URL answers 200 with an HTML
 * sign-in page when the document's sharing has drifted, so a job that trusts
 * the status code will happily commit a login screen as your CV.
 *
 *   node scripts/check-resume-pdf.mjs <file> [--expect-email <address>]
 *
 * The structural checks are dependency-free. The content checks need
 * `pdftotext` (poppler-utils) on PATH and are skipped with a warning without
 * it, because a Docs export draws its text with subsetted fonts and glyph
 * indices, so there is no readable string in the file to grep for.
 *
 * Exits non-zero with a reason on failure. Warnings do not fail the run.
 */
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const MIN_BYTES = 10_000; // the real resume is ~86KB; a stub or error page is far smaller

const args = process.argv.slice(2);
const file = args.find((a) => !a.startsWith('--'));
const expectEmail = args.includes('--expect-email')
  ? args[args.indexOf('--expect-email') + 1]
  : null;

if (!file) {
  console.error('usage: check-resume-pdf.mjs <file> [--expect-email <address>]');
  process.exit(2);
}

const fail = (msg) => {
  console.error(`FAIL  ${msg}`);
  process.exitCode = 1;
};
const warn = (msg) => console.warn(`WARN  ${msg}`);
const ok = (msg) => console.log(`ok    ${msg}`);

let buf;
try {
  buf = readFileSync(file);
} catch (err) {
  console.error(`FAIL  cannot read ${file}: ${err.message}`);
  process.exit(1);
}

// 1. It has to actually be a PDF. This is the check that catches a sign-in page.
const head = buf.subarray(0, 5).toString('latin1');
if (!head.startsWith('%PDF')) {
  fail(`not a PDF. First bytes: ${JSON.stringify(buf.subarray(0, 120).toString('latin1'))}`);
  console.error('      A 200 with HTML here almost always means the document is no longer');
  console.error('      shared with "anyone with the link".');
  process.exit(1);
}
ok(`starts with ${head.trim()}`);

// 2. Big enough to be the document rather than a stub or an error.
if (buf.length < MIN_BYTES) {
  fail(`only ${buf.length} bytes, expected at least ${MIN_BYTES}`);
} else {
  ok(`${buf.length} bytes`);
}

// 3. Content checks, if there is an extractor to do them with.
let text = null;
try {
  text = execFileSync('pdftotext', [file, '-'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });
} catch {
  warn('pdftotext not available; skipping the content checks');
  warn('install poppler-utils to check the name and the address');
}

if (text !== null) {
  const flat = text.replace(/\s+/g, ' ');

  // The name should be in there. If it is not, this is not the resume.
  if (/Austin\s*Orphan/i.test(flat)) {
    ok('contains "Austin Orphan"');
  } else {
    fail('does not contain "Austin Orphan" anywhere in its text');
  }

  // The address in the PDF has to match the one the site advertises, or the
  // site says one thing and the file downloaded from it says another.
  const addresses = [...new Set(
    (text.match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g) ?? [])
      .map((a) => a.toLowerCase()),
  )];
  if (addresses.length === 0) {
    warn('no email address found in the text');
  } else {
    ok(`addresses found: ${addresses.join(', ')}`);
  }
  if (expectEmail) {
    const want = expectEmail.toLowerCase();
    const stale = addresses.filter((a) => a !== want);
    if (!addresses.includes(want)) {
      fail(`the site advertises ${expectEmail}, which is not in the PDF`);
    } else {
      ok(`matches the site's address, ${expectEmail}`);
    }
    if (stale.length) {
      fail(`also still carries ${stale.join(', ')}`);
    }
  }
}

if (process.exitCode) {
  console.error('\nRefusing to publish this file.');
} else {
  console.log('\nLooks like the resume.');
}
