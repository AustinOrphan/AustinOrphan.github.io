// public/og-image.png, re-shot from docs/og-image.html with the current mark in it.
//
// The social card is a composition -- wordmark, tagline, link bar, domain -- so it cannot be
// rendered from the mark the way the icons can. What it does carry is the mark, at 5% behind
// the content, and that has to follow the typeface like everything else. This rewrites the
// backdrop path in docs/og-image.html from src/components/logo-mark.ts and screenshots the
// page, so the saved HTML stays the source of truth rather than drifting from the PNG.
//
// Needs a Chrome listening on CDP_PORT (9222 by default), because the card uses the site's
// webfonts and a real browser is the only thing that will lay them out correctly:
//   chrome --headless --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-og
//
//   node scripts/make-og-image.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const HTML = join(ROOT, 'docs/og-image.html');
const OUT = join(ROOT, 'public/og-image.png');
const PORT = Number(process.env.CDP_PORT || 9222);
const W = 1200;
const H = 630;

const D = readFileSync(join(ROOT, 'src/components/logo-mark.ts'), 'utf8')
  .match(/['"`]([Mm][^'"`]{200,})['"`]/)?.[1];
if (!D) throw new Error('LOGO_MARK_D not found in src/components/logo-mark.ts');

// One <path> lives inside .markwrap; replace its d and leave the rest of the card alone.
let html = readFileSync(HTML, 'utf8');
const before = html;
html = html.replace(
  /(<div class="markwrap">[\s\S]*?<path d=")[\s\S]*?("\s*\/?>)/,
  (_, head, tail) => head + D + tail,
);
if (html === before) throw new Error('backdrop path not found in docs/og-image.html');
writeFileSync(HTML, html);

const res = await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })
  .catch(() => { throw new Error(`no Chrome on CDP port ${PORT}; see the header of this file`); });
const target = await res.json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  ws.addEventListener('open', resolve);
  ws.addEventListener('error', reject);
});
let id = 0;
const pending = new Map();
ws.addEventListener('message', (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
});
const send = (method, params = {}) =>
  new Promise((resolve) => { pending.set(++id, resolve); ws.send(JSON.stringify({ id, method, params })); });

await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: 'file://' + HTML });
// Webfonts have to be in before the shot, or the wordmark renders in a fallback.
for (let i = 0; i < 40; i++) {
  const r = await send('Runtime.evaluate', {
    expression: 'document.fonts.status === "loaded" && document.readyState === "complete"',
    returnByValue: true,
  });
  if (r.result?.result?.value) break;
  await new Promise((r2) => setTimeout(r2, 100));
}
await new Promise((r) => setTimeout(r, 300));
const shot = await send('Page.captureScreenshot', {
  format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 }, captureBeyondViewport: true,
});
const buf = Buffer.from(shot.result.data, 'base64');
let prev = 0;
try { prev = readFileSync(OUT).length; } catch { /* new */ }
writeFileSync(OUT, buf);
console.log(`  og-image.png  ${prev} -> ${buf.length} bytes  (${W}x${H})`);
ws.close();
process.exit(0);
