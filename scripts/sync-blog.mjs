#!/usr/bin/env node
import { readFile, writeFile, mkdir, readdir, copyFile, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, basename, extname, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import matter from 'gray-matter';

const SITE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const VAULT_PATH = resolve(process.env.VAULT_PATH ?? join(SITE_ROOT, 'test-vault'));
const CONTENT_DIR = join(SITE_ROOT, 'src/content/blog');
const ASSETS_DIR = join(SITE_ROOT, 'public/blog-assets');

const IMAGE_EXT = /\.(png|jpe?g|gif|webp|svg|avif)$/i;

if (!existsSync(VAULT_PATH)) {
  console.error(`✘ Vault path not found: ${VAULT_PATH}`);
  console.error('  Set VAULT_PATH or place a vault at ./test-vault');
  process.exit(1);
}

console.log(`◆ Syncing from ${VAULT_PATH}`);

async function walk(dir, predicate) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...await walk(path, predicate));
    } else if (entry.isFile() && predicate(entry.name)) {
      out.push(path);
    }
  }
  return out;
}

const mdPaths = await walk(VAULT_PATH, (n) => n.endsWith('.md'));
const imagePaths = await walk(VAULT_PATH, (n) => IMAGE_EXT.test(n));

const imageByBasename = new Map();
for (const path of imagePaths) imageByBasename.set(basename(path), path);

const notes = await Promise.all(
  mdPaths.map(async (path) => {
    const raw = await readFile(path, 'utf8');
    const parsed = matter(raw);
    return { path, data: parsed.data, body: parsed.content };
  })
);

function slugify(s) {
  return s
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

const now = new Date();
const publishable = [];
let skippedFuture = 0;
let unpublished = 0;

for (const note of notes) {
  const { data, path } = note;
  if (data.publish !== true) {
    unpublished++;
    continue;
  }
  if (!data.pubDate) {
    console.warn(`  ⚠ ${basename(path)} has publish: true but no pubDate — skipping`);
    continue;
  }
  if (new Date(data.pubDate) > now) {
    skippedFuture++;
    continue;
  }
  note.slug = typeof data.slug === 'string' && data.slug ? data.slug : slugify(basename(path, '.md'));
  publishable.push(note);
}

const slugByKey = new Map();
for (const note of publishable) {
  if (note.data.title) slugByKey.set(note.data.title.toLowerCase(), note.slug);
  slugByKey.set(basename(note.path, '.md').toLowerCase(), note.slug);
  const aliases = note.data.aliases ?? note.data.alias;
  if (Array.isArray(aliases)) {
    for (const a of aliases) {
      if (typeof a === 'string' && a.trim()) slugByKey.set(a.trim().toLowerCase(), note.slug);
    }
  } else if (typeof aliases === 'string' && aliases.trim()) {
    slugByKey.set(aliases.trim().toLowerCase(), note.slug);
  }
}

// Split markdown into alternating fenced-code and prose segments so multi-line
// transforms (e.g. block comments) can operate freely on prose without touching
// fenced code.
function splitByFence(md) {
  const segments = [];
  let buffer = [];
  let kind = 'prose';
  for (const line of md.split('\n')) {
    if (/^\s*```/.test(line)) {
      if (kind === 'fence') {
        buffer.push(line);
        segments.push({ kind, text: buffer.join('\n') });
        buffer = [];
        kind = 'prose';
      } else {
        if (buffer.length) segments.push({ kind, text: buffer.join('\n') });
        buffer = [line];
        kind = 'fence';
      }
    } else {
      buffer.push(line);
    }
  }
  if (buffer.length) segments.push({ kind, text: buffer.join('\n') });
  return segments;
}

function transformProse(md, fn) {
  return splitByFence(md).map((s) => (s.kind === 'fence' ? s.text : fn(s.text))).join('\n');
}

// Like transformProse, but also escapes inline `code spans` line-by-line.
function transformOutsideCode(md, fn) {
  return transformProse(md, (prose) =>
    prose
      .split('\n')
      .map((line) => {
        const parts = line.split('`');
        for (let i = 0; i < parts.length; i++) {
          if (i % 2 === 0) parts[i] = fn(parts[i]);
        }
        return parts.join('`');
      })
      .join('\n')
  );
}

const copyJobs = [];

function stripObsidianComments(md) {
  // %%...%% (can span lines, but only in prose segments — fenced code untouched)
  return transformProse(md, (prose) => prose.replace(/%%[\s\S]*?%%/g, ''));
}

function renderImageEmbed(slug, target, param, fallback) {
  const name = basename(target);
  const src = imageByBasename.get(name);
  if (!src) {
    console.warn(`  ⚠ image not found for ${slug}: ${target}`);
    return fallback;
  }
  copyJobs.push({ src, slug, name });
  const url = `/blog-assets/${slug}/${name}`;

  // Obsidian image-pipe heuristic: pure digits or NxN ⇒ dimensions; else alt text.
  const dim = param.match(/^(\d+)(?:x(\d+))?$/);
  if (dim) {
    const [, w, h] = dim;
    const hAttr = h ? ` height="${h}"` : '';
    return `<img src="${url}" alt="" width="${w}"${hAttr} />`;
  }
  return `![${param}](${url})`;
}

function transformEmbeds(slug, md) {
  return transformOutsideCode(md, (segment) =>
    segment.replace(/!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]/g, (match, target, param) => {
      const targetTrimmed = target.trim();
      const paramTrimmed = (param ?? '').trim();

      if (IMAGE_EXT.test(targetTrimmed)) {
        return renderImageEmbed(slug, targetTrimmed, paramTrimmed, match);
      }

      // Note transclusion: ![[Note]] or ![[Note#Heading]] or ![[Note.md]]
      // We don't truly inline the other note's content (recursion/cycles are a
      // can of worms). Instead, render a link to the note — same behavior as a
      // plain wikilink, since the embed semantics map cleanly to "go read it."
      const [pathPart, heading] = targetTrimmed.split('#');
      const stripped = pathPart.replace(/\.md$/i, '');
      const ext = extname(stripped);
      if (ext) {
        // Unknown attachment type (PDF, mp4, etc.) — warn and emit display text.
        console.warn(`  ⚠ unsupported attachment for ${slug}: ${target}`);
        return paramTrimmed || basename(stripped);
      }
      const key = stripped.trim().toLowerCase();
      const linkSlug = slugByKey.get(key);
      const display = paramTrimmed || stripped;
      if (!linkSlug) return display;
      const anchor = heading ? `#${slugify(heading)}` : '';
      return `[${display}](/blog/${linkSlug}/${anchor})`;
    })
  );
}

function transformWikilinks(md) {
  return transformOutsideCode(md, (segment) =>
    segment.replace(/(?<!!)\[\[([^\]|]+)(?:\|([^\]]*))?\]\]/g, (_match, target, display) => {
      const [notePart, heading] = target.split('#');
      const key = notePart.trim().toLowerCase();
      const text = ((display ?? notePart) || '').trim();
      const slug = slugByKey.get(key);
      if (!slug) return text;
      const anchor = heading ? `#${slugify(heading)}` : '';
      return `[${text}](/blog/${slug}/${anchor})`;
    })
  );
}

function extractInlineTags(md, frontmatterTags) {
  const tags = new Set(Array.isArray(frontmatterTags) ? frontmatterTags : []);
  const rx = /(^|\s)#([a-zA-Z][\w/-]*)(?=$|[\s.,;:!?)\]])/g;
  const isHexColor = (s) => /^[0-9a-fA-F]+$/.test(s) && [3, 6, 8].includes(s.length);
  const cleaned = transformOutsideCode(md, (segment) =>
    segment.replace(rx, (match, prefix, tag) => {
      if (isHexColor(tag)) return match;
      tags.add(tag);
      return prefix;
    })
  );
  return { body: cleaned, tags: [...tags] };
}

const slugSources = new Map();
for (const note of publishable) {
  const prior = slugSources.get(note.slug);
  if (prior) {
    console.error(`✘ Slug collision on "${note.slug}":`);
    console.error(`    ${prior}`);
    console.error(`    ${note.path}`);
    console.error('  Set a unique frontmatter `slug` or rename one of the notes.');
    process.exit(1);
  }
  slugSources.set(note.slug, note.path);
}

await rm(CONTENT_DIR, { recursive: true, force: true });
await rm(ASSETS_DIR, { recursive: true, force: true });
await mkdir(CONTENT_DIR, { recursive: true });

for (const note of publishable) {
  let body = note.body;
  body = stripObsidianComments(body);
  body = transformEmbeds(note.slug, body);
  body = transformWikilinks(body);
  const { body: stripped, tags } = extractInlineTags(body, note.data.tags);

  const frontmatter = {
    title: note.data.title,
    description: note.data.description,
    pubDate: note.data.pubDate,
    tags,
  };

  const output = matter.stringify(stripped, frontmatter);
  await writeFile(join(CONTENT_DIR, `${note.slug}.md`), output);
}

for (const { src, slug, name } of copyJobs) {
  const dir = join(ASSETS_DIR, slug);
  await mkdir(dir, { recursive: true });
  await copyFile(src, join(dir, name));
}

console.log(
  `✓ Published ${publishable.length}, skipped ${skippedFuture} future-dated, ${unpublished} unpublished`
);
