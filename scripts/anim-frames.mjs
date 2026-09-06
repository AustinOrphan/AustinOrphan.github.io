#!/usr/bin/env node
// Compare the LogoAnimated write-on against the reference clip, frame by frame.
//
// Loads the demo page (/logo-animation/) in a Chrome that is already listening
// on CDP_PORT, pauses every animation inside the animated mark, seeks them all
// to each video frame time for f4..f36, screenshots the mark, and lays the
// captures next to the matching video frames on one labelled sheet.
//
//   BASE_URL    a running preview of this site (default http://localhost:4321;
//               astro preview binds [::1], so use localhost, not 127.0.0.1)
//   CDP_PORT    Chrome remote debugging port (default 9222)
//   CLIP        the reference clip (default design/logo-animation/comp.mp4)
//   FRAMES_DIR  pre-extracted frames; skips ffmpeg when set (contract below)
//   OUT         sheet destination (default design/logo-animation/compare.png)
//   FIRST/LAST  frame range (default 4..36)
//
// Frame-file contract: frame numbers are 0-based and time = frame / 29.97.
// FILES ARE 1-BASED, as ffmpeg's image2 muxer names them: frame n is
// f{n+1:03d}.png, so f001.png is frame 0 and frame 8 (the first inked frame,
// 0.267 s) is f009.png. Both the ffmpeg extraction here and FRAMES_DIR follow
// that rule, so the video tile and the SVG capture for a frame number are
// the same instant. As a guard, the run aborts unless the first tile with
// ink is frame 8.
//
// One-command rerun (needs ffmpeg on PATH unless FRAMES_DIR is given):
//
//   npm run build && npm run preview -- --port 4620 &
//   chrome --headless --remote-debugging-port=9222 &
//   BASE_URL=http://localhost:4620 node scripts/anim-frames.mjs
//
// The video is registered to the SVG automatically: the mark's white bbox in
// the last frame is mapped onto the mark's known extents in viewBox units, so
// each video tile shows exactly the SVG's viewBox window.

import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { connect, evaluate, setViewport, sleep } from './lib/cdp.mjs';

const BASE = (process.env.BASE_URL || 'http://localhost:4321').replace(/\/$/, '');
const PORT = Number(process.env.CDP_PORT || 9222);
const CLIP = process.env.CLIP || 'design/logo-animation/comp.mp4';
const OUT = process.env.OUT || 'design/logo-animation/compare.png';
const FIRST = Number(process.env.FIRST || 4);
const LAST = Number(process.env.LAST || 36);
const FPS = 30000 / 1001;
const FIRST_INKED_FRAME = 8; // the clip's first frame with ink (0.267 s)
const INK = 128; // pixel threshold for "inked", the same one the sheet uses to register
const CAPTURE = 480; // CSS px, the animated mark's rendered size on the demo page
const TILE = 240; // px per tile on the sheet
const PER_ROW = 3; // frame pairs per sheet row

// The mark's extents inside Logo.astro's viewBox ("-70 -70 1246 1246"), in
// viewBox units: path x 44..10798 and y 194..10247 (tenths, y-up, translated
// by 1084) -> x 4.4..1079.8, y 59.3..1064.6.
const MARK_VB = { x0: 4.4, x1: 1079.8, y0: 59.3, y1: 1064.6 };
const VB = { x: -70, y: -70, w: 1246, h: 1246 };

// ---- video frames -----------------------------------------------------------

function frameFiles() {
  let dir = process.env.FRAMES_DIR;
  if (!dir) {
    if (!existsSync(CLIP)) throw new Error(`no clip at ${CLIP}`);
    dir = mkdtempSync(join(tmpdir(), 'ao-frames-'));
    // Frame n -> f{n+1:03d}.png, the 1-based file contract described above.
    execFileSync(
      'ffmpeg',
      ['-v', 'error', '-y', '-i', CLIP, '-vf', `select='between(n,${FIRST},${LAST})'`,
        '-fps_mode', 'passthrough', '-start_number', String(FIRST + 1), join(dir, 'f%03d.png')],
      { stdio: 'inherit' }
    );
  }
  const files = [];
  for (let f = FIRST; f <= LAST; f++) {
    const p = join(dir, frameFile(f));
    if (!existsSync(p)) throw new Error(`missing frame ${f}: ${p}`);
    files.push({ frame: f, t: f / FPS, dataUrl: 'data:image/png;base64,' + readFileSync(p).toString('base64') });
  }
  return files;
}

// frame n (0-based) lives in the 1-based file f{n+1:03d}.png
const frameFile = (n) => `f${String(n + 1).padStart(3, '0')}.png`;

// ---- capture the SVG at each frame time ---------------------------------------

// Pause every animation that targets a node inside the first animated mark and
// expose a seek. Restarting via the demo's replay first makes the start times
// coincide even if the page was loaded a while ago.
const PREPARE = `(() => {
  const svg = document.querySelector('.site-logo-anim');
  if (!svg) return { error: 'no .site-logo-anim on the page' };
  svg.style.width = svg.style.height = '${CAPTURE}px';
  window.scrollTo(0, 0);
  window.__laReplay?.();
  const anims = document.getAnimations().filter(a => {
    const t = a.effect && a.effect.target;
    return t instanceof Element && svg.contains(t);
  });
  for (const a of anims) a.pause();
  window.__laSeek = (ms) => { for (const a of anims) a.currentTime = ms; return anims.length; };
  const r = svg.getBoundingClientRect();
  return { ok: true, count: anims.length, names: [...new Set(anims.map(a => a.animationName))],
    rect: { x: r.left, y: r.top, width: r.width, height: r.height } };
})()`;

async function captureFrames(cdp, frames) {
  await setViewport(cdp, 1400, 1100);
  await cdp.send('Page.navigate', { url: BASE + '/logo-animation/' });
  await sleep(1500);
  const prep = await evaluate(cdp, PREPARE);
  if (prep?.error) throw new Error(prep.error + ' at ' + BASE + '/logo-animation/');
  console.log(`  ${prep.count} animations paused: ${prep.names.join(', ')}`);
  const out = [];
  for (const f of frames) {
    await evaluate(cdp, `window.__laSeek(${Math.round(f.t * 1000)})`);
    await sleep(30);
    const shot = await cdp.send('Page.captureScreenshot', {
      format: 'png',
      clip: { x: prep.rect.x, y: prep.rect.y, width: prep.rect.width, height: prep.rect.height, scale: 1 },
    });
    out.push({ ...f, svgDataUrl: 'data:image/png;base64,' + shot.data });
  }
  return out;
}

// ---- compose the sheet ----------------------------------------------------------

const COMPOSE = (frames) => `(async () => {
  const frames = ${JSON.stringify(frames)};
  const TILE = ${TILE}, PER_ROW = ${PER_ROW}, GAP = 10, PAIR_GAP = 4, LABEL = 22, PAD = 16;
  const load = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
  const scratch = document.createElement('canvas'), sg = scratch.getContext('2d', { willReadFrequently: true });
  const hasInk = (img) => {
    scratch.width = img.width; scratch.height = img.height; sg.drawImage(img, 0, 0);
    const px = sg.getImageData(0, 0, img.width, img.height).data;
    for (let i = 0; i < px.length; i += 4) if (px[i] > ${INK}) return true;
    return false;
  };
  let firstInked = null;

  // Register the video to the viewBox from the mark's bbox in the last frame.
  const ref = await load(frames[frames.length - 1].videoDataUrl);
  const c0 = document.createElement('canvas'); c0.width = ref.width; c0.height = ref.height;
  const g0 = c0.getContext('2d', { willReadFrequently: true }); g0.drawImage(ref, 0, 0);
  const d = g0.getImageData(0, 0, ref.width, ref.height).data;
  let bx0 = 1e9, by0 = 1e9, bx1 = -1, by1 = -1;
  for (let y = 0; y < ref.height; y++) for (let x = 0; x < ref.width; x++) {
    if (d[(y * ref.width + x) * 4] > ${INK}) {
      if (x < bx0) bx0 = x; if (x > bx1) bx1 = x; if (y < by0) by0 = y; if (y > by1) by1 = y;
    }
  }
  const M = ${JSON.stringify(MARK_VB)}, V = ${JSON.stringify(VB)};
  const scale = ((bx1 - bx0 + 1) / (M.x1 - M.x0) + (by1 - by0 + 1) / (M.y1 - M.y0)) / 2;
  const crop = { x: bx0 - (M.x0 - V.x) * scale, y: by0 - (M.y0 - V.y) * scale, w: V.w * scale, h: V.h * scale };

  const rows = Math.ceil(frames.length / PER_ROW);
  const pairW = TILE * 2 + PAIR_GAP;
  const W = PAD * 2 + PER_ROW * pairW + (PER_ROW - 1) * GAP;
  const H = PAD * 2 + 30 + rows * (TILE + LABEL + GAP);
  const cvs = document.createElement('canvas'); cvs.width = W; cvs.height = H;
  Object.assign(cvs.style, { position: 'fixed', left: '0', top: '0' });
  document.body.appendChild(cvs);
  const g = cvs.getContext('2d');
  g.fillStyle = '#0b1218'; g.fillRect(0, 0, W, H);
  g.fillStyle = '#eee5e9'; g.font = 'bold 15px system-ui, sans-serif';
  g.fillText('AO write-on: reference clip (left) vs LogoAnimated seeked to the same time (right)', PAD, PAD + 14);
  g.font = '12px system-ui, sans-serif'; g.fillStyle = '#96aab9';
  g.fillText('video crop = the SVG viewBox window, registered on the mark bbox (scale ' + scale.toFixed(3) + ' px/unit)', PAD + 640, PAD + 14);

  for (let i = 0; i < frames.length; i++) {
    const f = frames[i];
    const col = i % PER_ROW, row = Math.floor(i / PER_ROW);
    const x = PAD + col * (pairW + GAP), y = PAD + 30 + row * (TILE + LABEL + GAP);
    const vid = await load(f.videoDataUrl), svg = await load(f.svgDataUrl);
    if (firstInked === null && hasInk(vid)) firstInked = f.frame;
    g.fillStyle = '#000'; g.fillRect(x, y + LABEL, TILE, TILE);
    g.drawImage(vid, crop.x, crop.y, crop.w, crop.h, x, y + LABEL, TILE, TILE);
    g.drawImage(svg, 0, 0, svg.width, svg.height, x + TILE + PAIR_GAP, y + LABEL, TILE, TILE);
    g.fillStyle = '#eee5e9'; g.font = 'bold 13px system-ui, sans-serif';
    g.fillText('f' + f.frame + '  ' + f.t.toFixed(3) + 's', x, y + 15);
    g.fillStyle = '#6e8494'; g.font = '11px system-ui, sans-serif';
    g.fillText('video', x + TILE - 34, y + 15); g.fillText('svg', x + TILE * 2 + PAIR_GAP - 22, y + 15);
    g.strokeStyle = '#2c3a46'; g.strokeRect(x + 0.5, y + LABEL + 0.5, TILE - 1, TILE - 1);
    g.strokeRect(x + TILE + PAIR_GAP + 0.5, y + LABEL + 0.5, TILE - 1, TILE - 1);
  }
  return { W, H, bbox: [bx0, by0, bx1, by1], scale, firstInked };
})()`;

// ---- main -----------------------------------------------------------------------

const frames = frameFiles().map((f) => ({ frame: f.frame, t: f.t, videoDataUrl: f.dataUrl }));
console.log(`  ${frames.length} video frames f${FIRST}..f${LAST}`);

const { cdp, close } = await connect(PORT);
try {
  const captured = await captureFrames(cdp, frames);
  await cdp.send('Page.navigate', { url: 'data:text/html;charset=utf-8,<body style="margin:0;background:%230b1218">' });
  await sleep(300);
  const size = await evaluate(cdp, COMPOSE(captured));
  if (FIRST <= FIRST_INKED_FRAME && size.firstInked !== FIRST_INKED_FRAME) {
    throw new Error(
      `frame files are off: the first video tile with ink is frame ${size.firstInked}, expected ${FIRST_INKED_FRAME}. ` +
      `Frame n must be ${frameFile(0).replace('001', '{n+1:03d}')} (1-based files); check FRAMES_DIR.`
    );
  }
  console.log(`  first inked video tile: frame ${size.firstInked} (expected ${FIRST_INKED_FRAME})`);
  console.log(`  video mark bbox ${size.bbox.join(',')}  scale ${size.scale.toFixed(3)} px per viewBox unit`);
  await setViewport(cdp, size.W, size.H);
  await sleep(100);
  const shot = await cdp.send('Page.captureScreenshot', {
    format: 'png', captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: size.W, height: size.H, scale: 1 },
  });
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, Buffer.from(shot.data, 'base64'));
  console.log(`  wrote ${OUT} (${size.W}x${size.H})`);
} finally {
  await close();
}
