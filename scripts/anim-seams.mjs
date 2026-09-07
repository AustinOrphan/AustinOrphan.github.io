#!/usr/bin/env node
// Seek the write-on to the four seams the timing fixes touch and lay the frames out.
//
//   npm run build && npm run preview -- --port 4620 &
//   chrome --headless --remote-debugging-port=9222 &
//   BASE_URL=http://localhost:4620 node scripts/anim-seams.mjs
import { writeFileSync } from 'node:fs';
import { connect, evaluate, setViewport, sleep } from './lib/cdp.mjs';

const BASE = (process.env.BASE_URL || 'http://localhost:4620').replace(/\/$/, '');
const PORT = Number(process.env.CDP_PORT || 9222);
const OUT  = process.env.OUT || 'design/logo-animation/seams.png';
const CAP  = 300;

// times in ms, grouped by the seam each one interrogates
const SEAMS = [
  ['right leg lands, trail leaves', [460, 480, 495, 510, 540]],
  ['trail head arrives, bar starts', [780, 800, 815, 830, 860]],
  ['ring finishes, hand-off, treatment', [1040, 1080, 1100, 1110, 1140, 1180, 1220, 1360]],
];

const PREPARE = `(() => {
  const svg = document.querySelector('.site-logo-anim');
  if (!svg) return { error: 'no .site-logo-anim' };
  svg.style.width = svg.style.height = '${CAP}px';
  window.scrollTo(0, 0);
  window.__laReplay?.();
  const anims = document.getAnimations().filter(a => {
    const t = a.effect && a.effect.target;
    return t instanceof Element && svg.contains(t);
  });
  for (const a of anims) a.pause();
  window.__laSeek = (ms) => { for (const a of anims) a.currentTime = ms; return anims.length; };
  const r = svg.getBoundingClientRect();
  return { ok: true, count: anims.length, names: [...new Set(anims.map(a => a.animationName))].sort(),
           rect: { x: r.left, y: r.top, width: r.width, height: r.height } };
})()`;

const { cdp, close } = await connect(PORT);
await setViewport(cdp, 1400, 1100);
await cdp.send('Page.navigate', { url: BASE + '/logo-animation/' });
await sleep(1800);
const prep = await evaluate(cdp, PREPARE);
if (prep?.error) throw new Error(prep.error + ' at ' + BASE + '/logo-animation/');
console.log(`  ${prep.count} animations: ${prep.names.join(', ')}`);

const rows = [];
for (const [title, times] of SEAMS) {
  const shots = [];
  for (const t of times) {
    await evaluate(cdp, `window.__laSeek(${t})`);
    await sleep(40);
    const s = await cdp.send('Page.captureScreenshot', {
      format: 'png',
      clip: { x: prep.rect.x, y: prep.rect.y, width: prep.rect.width, height: prep.rect.height, scale: 1 },
    });
    shots.push({ t, url: 'data:image/png;base64,' + s.data });
  }
  rows.push({ title, shots });
}

const PAD = 16, LBL = 26, HEAD = 30;
const W = PAD + Math.max(...rows.map(r => r.shots.length)) * (CAP + PAD);
const H = PAD + rows.length * (HEAD + CAP + LBL + PAD);
let y = PAD, svg = '';
for (const r of rows) {
  svg += `<text x="${PAD}" y="${y + 18}" fill="#2892D7" font-family="monospace" font-size="15">${r.title}</text>`;
  y += HEAD;
  let x = PAD;
  for (const s of r.shots) {
    svg += `<image x="${x}" y="${y}" width="${CAP}" height="${CAP}" href="${s.url}"/>`;
    svg += `<text x="${x}" y="${y + CAP + 18}" fill="#8b9fac" font-family="monospace" font-size="13">${(s.t/1000).toFixed(3)}s</text>`;
    x += CAP + PAD;
  }
  y += CAP + LBL + PAD;
}
writeFileSync(OUT.replace(/\.png$/, '.svg'),
  `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${W}" height="${H}">` +
  `<rect width="${W}" height="${H}" fill="#1D2B35"/>${svg}</svg>`);
console.log(`  wrote ${OUT.replace(/\.png$/, '.svg')}  ${W}x${H}`);
await close();
