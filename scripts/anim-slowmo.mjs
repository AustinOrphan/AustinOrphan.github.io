#!/usr/bin/env node
// Capture the write-on densely and write the frames out for ffmpeg to assemble.
//
//   BASE_URL=http://localhost:4620 node scripts/anim-slowmo.mjs
//
// STEP is the real-time gap between captures; the playback rate ffmpeg is given
// decides the slow-motion factor, so the frames themselves are the ground truth.
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { connect, evaluate, setViewport, sleep } from './lib/cdp.mjs';

const BASE = (process.env.BASE_URL || 'http://localhost:4620').replace(/\/$/, '');
const PORT = Number(process.env.CDP_PORT || 9222);
const DIR  = process.env.DIR || '/tmp/la-slowmo';
const STEP = Number(process.env.STEP || 20);      // ms of real animation per frame
const END  = Number(process.env.END || 1420);
const CAP  = Number(process.env.CAP || 460);

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
  return { ok: true, count: anims.length, rect: { x: r.left, y: r.top, width: r.width, height: r.height } };
})()`;

rmSync(DIR, { recursive: true, force: true });
mkdirSync(DIR, { recursive: true });

const { cdp, close } = await connect(PORT);
await setViewport(cdp, 1200, 900);
await cdp.send('Page.navigate', { url: BASE + '/logo-animation/' });
await sleep(1800);
const prep = await evaluate(cdp, PREPARE);
if (prep?.error) throw new Error(prep.error);
console.log(`  ${prep.count} animations paused`);

let n = 0;
for (let t = 0; t <= END; t += STEP) {
  await evaluate(cdp, `window.__laSeek(${t})`);
  await sleep(25);
  const s = await cdp.send('Page.captureScreenshot', {
    format: 'png',
    clip: { x: prep.rect.x, y: prep.rect.y, width: prep.rect.width, height: prep.rect.height, scale: 1 },
  });
  writeFileSync(`${DIR}/f${String(n).padStart(4, '0')}.png`, Buffer.from(s.data, 'base64'));
  n++;
}
console.log(`  wrote ${n} frames to ${DIR} at ${STEP}ms of animation each`);
await close();
