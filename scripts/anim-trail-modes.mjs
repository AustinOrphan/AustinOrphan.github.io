#!/usr/bin/env node
// The two pen-trail treatments side by side, at three times through the sweep.
//
// Loads the demo page (/logo-animation/) in a Chrome already listening on
// CDP_PORT, pauses the animations inside the two marks the page renders with
// `trail="swash"` and `trail="stroke"`, seeks both to each time, and lays the
// captures out as one labelled sheet: a row per treatment, a column per time.
//
//   BASE_URL  a running preview of this site (default http://localhost:4321;
//             astro preview binds [::1], so use localhost, not 127.0.0.1)
//   CDP_PORT  Chrome remote debugging port (default 9222)
//   TIMES     comma-separated seconds (default 0.60,0.72,0.85)
//   OUT       sheet destination (default design/logo-animation/trail-modes.png)
//
//   npm run build && npm run preview -- --port 4620 &
//   chrome --headless --remote-debugging-port=9222 &
//   BASE_URL=http://localhost:4620 node scripts/anim-trail-modes.mjs

import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';
import { connect, evaluate, setViewport, shoot, sleep } from './lib/cdp.mjs';

const BASE = (process.env.BASE_URL || 'http://localhost:4321').replace(/\/$/, '');
const PORT = Number(process.env.CDP_PORT || 9222);
const OUT = process.env.OUT || 'design/logo-animation/trail-modes.png';
const TIMES = (process.env.TIMES || '0.60,0.72,0.85').split(',').map(Number);
const CAPTURE = 400; // CSS px each mark is rendered at
const TILE = 300; // px per tile on the sheet
const MODES = [
  { sel: '.la-mode-swash', label: 'trail="swash" — the Illustrator swash, filled and swept (default)' },
  { sel: '.la-mode-stroke', label: 'trail="stroke" — a uniform 380-unit line on the same centre-line (the clip)' },
];

// Size both marks, restart them together, then pause and expose a seek.
const PREPARE = `(() => {
  const sels = ${JSON.stringify(MODES.map((m) => m.sel))};
  const svgs = sels.map(sel => document.querySelector(sel));
  if (svgs.some(s => !s)) return { error: 'missing ' + sels.filter((sel, i) => !svgs[i]).join(', ') };
  for (const s of svgs) { s.style.width = s.style.height = '${CAPTURE}px'; }
  window.scrollTo(0, 0);
  window.__laReplay?.();
  const anims = document.getAnimations().filter(a => {
    const t = a.effect && a.effect.target;
    return t instanceof Element && svgs.some(s => s.contains(t));
  });
  for (const a of anims) a.pause();
  window.__laSeek = (ms) => { for (const a of anims) a.currentTime = ms; return anims.length; };
  return { ok: true, count: anims.length,
    rects: svgs.map(s => { const r = s.getBoundingClientRect();
      return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height }; }) };
})()`;

const COMPOSE = (shots) => `(async () => {
  const shots = ${JSON.stringify(shots)};
  const modes = ${JSON.stringify(MODES.map((m) => m.label))};
  const times = ${JSON.stringify(TIMES)};
  const TILE = ${TILE}, GAP = 10, PAD = 16, HEAD = 30, ROWLABEL = 22;
  const load = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
  const W = PAD * 2 + times.length * TILE + (times.length - 1) * GAP;
  const H = PAD * 2 + HEAD + modes.length * (TILE + ROWLABEL + GAP);
  const cvs = document.createElement('canvas'); cvs.width = W; cvs.height = H;
  Object.assign(cvs.style, { position: 'fixed', left: '0', top: '0' });
  document.body.appendChild(cvs);
  const g = cvs.getContext('2d');
  g.fillStyle = '#0b1218'; g.fillRect(0, 0, W, H);
  g.fillStyle = '#eee5e9'; g.font = 'bold 15px system-ui, sans-serif';
  g.fillText('AO write-on: the two pen-trail treatments through the sweep', PAD, PAD + 14);
  for (let r = 0; r < modes.length; r++) {
    const y = PAD + HEAD + r * (TILE + ROWLABEL + GAP);
    g.fillStyle = '#eee5e9'; g.font = 'bold 13px system-ui, sans-serif';
    g.fillText(modes[r], PAD, y + 15);
    for (let c = 0; c < times.length; c++) {
      const x = PAD + c * (TILE + GAP);
      const img = await load(shots[r][c]);
      g.fillStyle = '#1d2b35'; g.fillRect(x, y + ROWLABEL, TILE, TILE);
      g.drawImage(img, 0, 0, img.width, img.height, x, y + ROWLABEL, TILE, TILE);
      g.fillStyle = '#96aab9'; g.font = '12px system-ui, sans-serif';
      g.fillText(times[c].toFixed(2) + 's', x + 6, y + ROWLABEL + 16);
      g.strokeStyle = '#2c3a46'; g.strokeRect(x + 0.5, y + ROWLABEL + 0.5, TILE - 1, TILE - 1);
    }
  }
  return { W, H };
})()`;

const { cdp, close } = await connect(PORT);
try {
  await setViewport(cdp, 1400, 1400);
  await cdp.send('Page.navigate', { url: BASE + '/logo-animation/' });
  await sleep(1500);
  const prep = await evaluate(cdp, PREPARE);
  if (prep?.error) throw new Error(prep.error + ' at ' + BASE + '/logo-animation/');
  console.log(`  ${prep.count} animations paused across ${MODES.length} marks`);

  const shots = MODES.map(() => []);
  for (const t of TIMES) {
    await evaluate(cdp, `window.__laSeek(${Math.round(t * 1000)})`);
    await sleep(40);
    for (let m = 0; m < MODES.length; m++) shots[m].push(await shoot(cdp, prep.rects[m]));
  }

  await cdp.send('Page.navigate', { url: 'data:text/html;charset=utf-8,<body style="margin:0;background:%230b1218">' });
  await sleep(300);
  const size = await evaluate(cdp, COMPOSE(shots));
  await setViewport(cdp, size.W, size.H);
  await sleep(100);
  const sheet = await shoot(cdp, { x: 0, y: 0, width: size.W, height: size.H });
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, Buffer.from(sheet.split(',')[1], 'base64'));
  console.log(`  wrote ${OUT} (${size.W}x${size.H})`);
} finally {
  await close();
}
