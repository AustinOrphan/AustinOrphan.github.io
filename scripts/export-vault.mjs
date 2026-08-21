#!/usr/bin/env node
// Export publish:true notes from an Obsidian vault into a small standalone
// repo that CI can check out.
//
// The vault itself never leaves your machine. Only notes explicitly marked
// `publish: true` — plus the attachments they reference — are copied into the
// export repo, so a leak of that repo exposes nothing beyond what is already
// destined for the website.
//
//   VAULT_PATH     source vault (required)
//   EXPORT_PATH    local clone of the export repo (required)
//   VAULT_INCLUDE  comma-separated vault-relative dirs to scan
//                  (optional; defaults to INCLUDE_DEFAULTS below)
//
//   node scripts/export-vault.mjs           # write files, leave git alone
//   node scripts/export-vault.mjs --push    # also commit and push
//   node scripts/export-vault.mjs --all     # scan the whole vault
//
// Scanning is scoped to a few directories rather than the whole vault: it
// keeps a stray `publish: true` in a journal or an archived note from
// reaching the site, and makes the blast radius of a bad frontmatter edit
// explicit. Add a directory here (or via VAULT_INCLUDE) when you start
// publishing from it.

import { readFile, writeFile, mkdir, readdir, copyFile, rm, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, basename, dirname, resolve, relative } from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import matter from 'gray-matter';

const run = promisify(execFile);

const INCLUDE_DEFAULTS = [
  '40_Journal/Blog',
  '10_Projects',
];

const VAULT_PATH = process.env.VAULT_PATH && resolve(process.env.VAULT_PATH);
const EXPORT_PATH = process.env.EXPORT_PATH && resolve(process.env.EXPORT_PATH);
const SHOULD_PUSH = process.argv.includes('--push');
const SCAN_ALL = process.argv.includes('--all');

const INCLUDE_DIRS = process.env.VAULT_INCLUDE
  ? process.env.VAULT_INCLUDE.split(',').map((s) => s.trim()).filter(Boolean)
  : INCLUDE_DEFAULTS;

const IMAGE_EXT = /\.(png|jpe?g|gif|webp|svg|avif)$/i;

function fail(msg) {
  console.error(`✘ ${msg}`);
  process.exit(1);
}

if (!VAULT_PATH) fail('VAULT_PATH is not set');
if (!EXPORT_PATH) fail('EXPORT_PATH is not set');
if (!existsSync(VAULT_PATH)) fail(`Vault not found: ${VAULT_PATH}`);
if (!existsSync(EXPORT_PATH)) fail(`Export repo not found: ${EXPORT_PATH}`);
if (!existsSync(join(EXPORT_PATH, '.git'))) {
  fail(`Export path is not a git repo: ${EXPORT_PATH}`);
}

// Guard against pointing the export at the vault itself, which would delete notes.
const rel = relative(VAULT_PATH, EXPORT_PATH);
if (rel === '' || (!rel.startsWith('..') && !resolve(rel).startsWith('/'))) {
  fail('EXPORT_PATH must not be inside VAULT_PATH');
}

// Mirrors slugify() in sync-blog.mjs — keep the two in step.
function slugify(s) {
  return s
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

async function walk(dir, predicate) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await walk(path, predicate)));
    else if (entry.isFile() && predicate(entry.name)) out.push(path);
  }
  return out;
}

console.log(`◆ Vault:  ${VAULT_PATH}`);
console.log(`◆ Export: ${EXPORT_PATH}`);

// Resolve the roots to scan for publishable notes.
const scanRoots = [];
if (SCAN_ALL) {
  console.log('◆ Scope:  entire vault (--all)');
  scanRoots.push(VAULT_PATH);
} else {
  for (const dir of INCLUDE_DIRS) {
    const abs = resolve(VAULT_PATH, dir);
    if (!abs.startsWith(VAULT_PATH)) fail(`Include path escapes the vault: ${dir}`);
    if (!existsSync(abs)) {
      console.warn(`  ⚠ include path does not exist, skipping: ${dir}`);
      continue;
    }
    if (!(await stat(abs)).isDirectory()) {
      console.warn(`  ⚠ include path is not a directory, skipping: ${dir}`);
      continue;
    }
    scanRoots.push(abs);
  }
  if (scanRoots.length === 0) fail('No valid include paths to scan');
  console.log(`◆ Scope:  ${INCLUDE_DIRS.join(', ')}`);
}

const mdPaths = [];
for (const root of scanRoots) {
  mdPaths.push(...(await walk(root, (n) => n.endsWith('.md'))));
}

// Attachments are resolved vault-wide by basename: Obsidian keeps images in a
// shared attachments folder, which usually sits outside the scanned dirs.
// Only images actually embedded by a published note are ever copied.
const imagePaths = await walk(VAULT_PATH, (n) => IMAGE_EXT.test(n));
const imageByBasename = new Map();
for (const p of imagePaths) imageByBasename.set(basename(p), p);

const published = [];
for (const path of mdPaths) {
  const raw = await readFile(path, 'utf8');
  let data;
  try {
    ({ data } = matter(raw));
  } catch (err) {
    console.warn(`  ⚠ unparseable frontmatter, skipping: ${basename(path)}`);
    continue;
  }
  if (data.publish === true) published.push({ path, raw, data });
}

if (published.length === 0) {
  fail(
    `No notes marked \`publish: true\` in: ${SCAN_ALL ? 'the vault' : INCLUDE_DIRS.join(', ')}\n` +
      '  Refusing to empty the export repo. Add a directory to VAULT_INCLUDE\n' +
      '  if you are publishing from somewhere new.'
  );
}

// Notes keep their vault-relative folder structure in the export repo.
// sync-blog.mjs walks recursively and derives each slug from the filename,
// so nesting is organizational only — it does not affect URLs. What it buys:
// readable diffs grouped by project, and no clobbering between same-named
// notes in different folders.
//
// Slugs are still global, so a collision is a real conflict regardless of
// folder. Catch it here with both paths named rather than letting the site
// build fail later with less context.
const seen = new Map();
for (const note of published) {
  const slug =
    typeof note.data.slug === 'string' && note.data.slug
      ? note.data.slug
      : slugify(basename(note.path, '.md'));
  const prior = seen.get(slug);
  if (prior) {
    fail(
      `Slug collision on "${slug}":\n    ${prior}\n    ${note.path}\n` +
        '  Rename one of the notes, or set a unique `slug` in its frontmatter.'
    );
  }
  seen.set(slug, note.path);
}

// Attachments referenced by published notes only.
const wanted = new Set();
for (const note of published) {
  for (const m of note.raw.matchAll(/!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]/g)) {
    const target = basename(m[1].trim());
    if (IMAGE_EXT.test(target)) wanted.add(target);
  }
}

// Clear previous export (tracked content only — never touch .git).
for (const entry of await readdir(EXPORT_PATH, { withFileTypes: true })) {
  if (entry.name === '.git') continue;
  await rm(join(EXPORT_PATH, entry.name), { recursive: true, force: true });
}

for (const note of published) {
  const dest = join(EXPORT_PATH, relative(VAULT_PATH, note.path));
  await mkdir(dirname(dest), { recursive: true });
  await writeFile(dest, note.raw);
}

let copied = 0;
let missing = 0;
if (wanted.size) {
  const attachDir = join(EXPORT_PATH, 'attachments');
  await mkdir(attachDir, { recursive: true });
  for (const name of wanted) {
    const src = imageByBasename.get(name);
    if (!src) {
      console.warn(`  ⚠ attachment not found in vault: ${name}`);
      missing++;
      continue;
    }
    await copyFile(src, join(attachDir, name));
    copied++;
  }
}

await writeFile(
  join(EXPORT_PATH, 'README.md'),
  [
    '# Blog vault export',
    '',
    'Generated by `scripts/export-vault.mjs` in the portfolio repo.',
    'Do not edit by hand — changes here are overwritten on the next export.',
    '',
    'Contains only notes marked `publish: true`, and the images they embed.',
    '',
  ].join('\n')
);

console.log(`✓ Exported ${published.length} note(s), ${copied} attachment(s)${missing ? `, ${missing} missing` : ''}`);

if (!SHOULD_PUSH) {
  console.log('  (dry run — pass --push to commit and push)');
  process.exit(0);
}

const git = (...args) => run('git', ['-C', EXPORT_PATH, ...args]);

const { stdout: status } = await git('status', '--porcelain');
if (!status.trim()) {
  console.log('✓ No changes to push');
  process.exit(0);
}

await git('add', '-A');
const stamp = new Date().toISOString().replace('T', ' ').slice(0, 16);
await git('commit', '-m', `content: export ${published.length} published note(s) — ${stamp}`);
await git('push');
console.log('✓ Pushed to export repo');
