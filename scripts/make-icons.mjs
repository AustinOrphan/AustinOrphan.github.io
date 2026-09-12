// Every icon in public/, rendered from the mark rather than drawn.
//
// The mark is derived (src/components/logo-mark.ts, from font/measure/mark_derived.py), so
// the icons have to be derived too -- otherwise re-deriving the typeface silently leaves
// fifteen files behind showing the old one, which is exactly what happened.
//
// The hero treatment here is not an invention: it is Logo.astro's, read off the component
// and its CSS. An accent-coloured copy offset by (22,22), then the mark filled in primary
// with a 300-unit secondary stroke under it (paint-order: stroke fill markers). Change it
// in one place and re-run this.
//
//   node scripts/make-icons.mjs          write every file
//   node scripts/make-icons.mjs --check  re-render and report drift, write nothing
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import sharp from 'sharp';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const PUB = join(ROOT, 'public');
const CHECK = process.argv.includes('--check');

const INK = '#EEE5E9';       // --color-primary
const OUTLINE = '#D16666';   // --color-secondary
const SHADOW = '#2892D7';    // --color-accent

const src = readFileSync(join(ROOT, 'src/components/logo-mark.ts'), 'utf8');
const D = src.match(/['"`]([Mm][^'"`]{200,})['"`]/)?.[1];
if (!D) throw new Error('LOGO_MARK_D not found in src/components/logo-mark.ts');

const INNER = 'translate(0.000000,1084.000000) scale(0.100000,-0.100000)';

/** Logo.astro's hero variant, as a standalone SVG. */
const heroSvg = (size, { pad = 0 } = {}) => {
  const vb = `${-70 - pad} ${-70 - pad} ${1246 + pad * 2} ${1246 + pad * 2}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb}" width="${size}" height="${size}">`
    + `<g transform="translate(22,22)"><g transform="${INNER}" fill="${SHADOW}"><path d="${D}"/></g></g>`
    + `<g transform="${INNER}" fill="${INK}" stroke="${OUTLINE}" stroke-width="300"`
    + ` stroke-linejoin="round" paint-order="stroke fill markers"><path d="${D}"/></g></svg>`;
};

/** A flat single-colour mark, for the Safari mask icon. */
const flatSvg = (fill) =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-70 -70 1246 1246" width="1246" height="1246">`
  + `<g transform="${INNER}" fill="${fill}"><path d="${D}"/></g></svg>`;

/** A minimal ICO container holding PNGs -- every browser since Vista reads these. */
function ico(pngs) {
  const dir = Buffer.alloc(6 + 16 * pngs.length);
  dir.writeUInt16LE(0, 0); dir.writeUInt16LE(1, 2); dir.writeUInt16LE(pngs.length, 4);
  let offset = dir.length;
  pngs.forEach(({ size, data }, i) => {
    const e = 6 + 16 * i;
    dir.writeUInt8(size >= 256 ? 0 : size, e);
    dir.writeUInt8(size >= 256 ? 0 : size, e + 1);
    dir.writeUInt16LE(1, e + 4); dir.writeUInt16LE(32, e + 6);
    dir.writeUInt32LE(data.length, e + 8); dir.writeUInt32LE(offset, e + 12);
    offset += data.length;
  });
  return Buffer.concat([dir, ...pngs.map((p) => p.data)]);
}

const drift = [];
const put = (name, buf) => {
  const path = join(PUB, name);
  let before = null;
  try { before = readFileSync(path); } catch { /* new file */ }
  const same = before && before.equals(buf);
  if (!CHECK) writeFileSync(path, buf);
  if (!same) drift.push(`${name}  ${before ? `${before.length} -> ${buf.length}` : 'new'}`);
  return same;
};

// Square PNGs, transparent ground, the same sizes the site already links.
const SQUARE = {
  'favicon.png': 180, 'favicon-16x16.png': 16, 'favicon-32x32.png': 32,
  'apple-touch-icon.png': 180,
  'android-chrome-192x192.png': 192, 'android-chrome-512x512.png': 512,
  'mstile-70x70.png': 70, 'mstile-144x144.png': 144,
  'mstile-150x150.png': 150, 'mstile-310x310.png': 310,
};

const png = (size, pad = 0) =>
  sharp(Buffer.from(heroSvg(size * 4, { pad })), { density: 384 })
    .resize(size, size).png({ compressionLevel: 9 }).toBuffer();

for (const [name, size] of Object.entries(SQUARE)) put(name, await png(size));

// The wide Windows tile: the same mark, centred on a transparent 310x150.
{
  const mark = await png(150);
  put('mstile-310x150.png', await sharp({
    create: { width: 310, height: 150, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } },
  }).composite([{ input: mark, left: 80, top: 0 }]).png({ compressionLevel: 9 }).toBuffer());
}

put('favicon.ico', ico(await Promise.all([16, 32, 48].map(async (size) =>
  ({ size, data: await png(size) })))));

put('favicon.svg', Buffer.from(heroSvg(512) + '\n'));
put('safari-pinned-tab.svg', Buffer.from(flatSvg('#000000') + '\n'));

if (!drift.length) console.log('  icons already match the mark');
else {
  console.log(`  ${CHECK ? 'would rewrite' : 'wrote'} ${drift.length} file(s):`);
  for (const d of drift) console.log(`    ${d}`);
  if (CHECK) process.exitCode = 1;
}
