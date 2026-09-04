#!/usr/bin/env node
// Chart and verify the hero backdrop's two animation loops.
//
// The backdrop mark runs two CSS animations at once, on deliberately different
// periods: `heroLogoBreathe` drives opacity on a 160s four-swell loop, and
// `heroLogoTint` drives fill on a 120s three-swell loop. Four against three
// gives a 480s super-period, so the loud swell arrives in a different colour
// each time it comes round.
//
// That arrangement rests on one assumption worth checking rather than eyeballing:
// every colour change must finish inside the 2s window where opacity is zero.
// If it does not, the mark visibly shifts hue mid-swell. This script measures it.
//
//   BASE_URL   site to sample (default: http://127.0.0.1:4321)
//   CDP_PORT   Chrome remote debugging port (default: 9222)
//   OUT        chart destination (default: docs/hero-backdrop-curve.png)
//
// Start Chrome with remote debugging and serve a build, then:
//
//   npm run build && npm run preview &
//   node scripts/plot-hero-backdrop-curve.mjs
//
// Exits non-zero if any colour change would be visible, so it can gate a change
// to the keyframe timings.

import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

const BASE = process.env.BASE_URL || 'http://127.0.0.1:4321';
const PORT = Number(process.env.CDP_PORT || 9222);
const OUT = process.env.OUT || 'docs/hero-backdrop-curve.png';

const BREATHE_MS = 160_000;
const TINT_MS = 120_000;
const SWELL_MS = 40_000;
const SWELLS = 12; // 480s super-period / 40s

// The three colours the mark cycles through, as computed-style strings.
const PALETTE = {
  'rgb(238, 229, 233)': 'primary',
  'rgb(40, 146, 215)': 'accent',
  'rgb(209, 102, 102)': 'secondary',
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class CDP {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    ws.addEventListener('message', (e) => {
      const m = JSON.parse(e.data);
      if (!m.id || !this.pending.has(m.id)) return;
      const { resolve, reject } = this.pending.get(m.id);
      this.pending.delete(m.id);
      m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result);
    });
  }

  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
      setTimeout(() => {
        if (!this.pending.has(id)) return;
        this.pending.delete(id);
        reject(new Error(`timeout: ${method}`));
      }, 120_000);
    });
  }
}

async function connect() {
  let target;
  try {
    const res = await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' });
    target = await res.json();
  } catch {
    throw new Error(
      `No Chrome on port ${PORT}. Start one with --remote-debugging-port=${PORT}.`
    );
  }
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve);
    ws.addEventListener('error', reject);
  });
  const cdp = new CDP(ws);
  for (const domain of ['Page', 'Runtime', 'Network']) await cdp.send(`${domain}.enable`);
  // The service worker is network-first for documents but still caches; bypass
  // it so a stale build cannot be measured instead of the current one.
  await cdp.send('Network.setBypassServiceWorker', { bypass: true });
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: 1440, height: 900, deviceScaleFactor: 1, mobile: false,
  });
  return { cdp, ws, targetId: target.id };
}

const evaluate = (cdp, expression) =>
  cdp
    .send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
    .then((r) => r.result?.value);

// Pause both animations so they can be scrubbed to an exact time. Everything is
// read back through getComputedStyle, so what is measured is what the browser
// would actually paint, not a re-implementation of the keyframes.
const PREPARE = `(() => {
  const backdrop = document.querySelector('.hero-logo-backdrop');
  if (!backdrop) return { error: 'no .hero-logo-backdrop on the page' };
  const mark = backdrop.querySelector('.site-logo-mark');
  const breathe = document.getAnimations().find(a => a.animationName === 'heroLogoBreathe');
  const tint = document.getAnimations().find(a => a.animationName === 'heroLogoTint');
  if (!breathe || !tint) {
    return { error: 'missing ' + (!breathe ? 'heroLogoBreathe ' : '') + (!tint ? 'heroLogoTint' : '') };
  }
  breathe.pause();
  tint.pause();
  window.__seek = (ms) => {
    breathe.currentTime = ((ms % ${BREATHE_MS}) + ${BREATHE_MS}) % ${BREATHE_MS};
    tint.currentTime = ((ms % ${TINT_MS}) + ${TINT_MS}) % ${TINT_MS};
    return [Number(getComputedStyle(backdrop).opacity), getComputedStyle(mark).fill];
  };
  return { ok: true };
})()`;

// Walk each swell boundary finely enough to catch a crossfade that leaks into a
// visible frame. Reports how many intermediate colours were seen so a pass
// cannot be vacuous: zero intermediates would mean the window was never sampled.
const AUDIT = `(() => {
  const exact = new Set(${JSON.stringify(Object.keys(PALETTE))});
  const results = [];
  for (let swell = 0; swell < ${SWELLS}; swell++) {
    const boundary = swell * ${SWELL_MS};
    let intermediates = 0, worstOpacity = 0, worstAt = null;
    let crossfadeEnd = null, firstVisible = null;
    for (let ms = boundary - 1000; ms <= boundary + 3000; ms += 20) {
      const [opacity, fill] = window.__seek(ms);
      if (!exact.has(fill)) {
        intermediates++;
        crossfadeEnd = ms;
        if (opacity > worstOpacity) { worstOpacity = opacity; worstAt = ms; }
      }
      if (firstVisible === null && opacity > 0 && ms >= boundary) firstVisible = ms;
    }
    results.push({
      swell: swell + 1, boundary, intermediates, worstOpacity, worstAt,
      crossfadeEnd, firstVisible,
      marginMs: firstVisible !== null && crossfadeEnd !== null ? firstVisible - crossfadeEnd : null,
    });
  }
  return results;
})()`;

// Draw the chart in the page itself and screenshot it, so the script needs no
// image library. The line is tinted with the fill in effect at each sample.
const CHART = (series) => `(() => {
  const series = ${JSON.stringify(series)};
  const W = 1400, H = 660, top = 92, bot = H - 78, left = 74, right = W - 26;
  const cvs = document.createElement('canvas');
  cvs.width = W; cvs.height = H;
  Object.assign(cvs.style, { position: 'fixed', inset: '0', zIndex: '2147483647' });
  document.body.appendChild(cvs);
  const g = cvs.getContext('2d');
  const MAX = 0.33;
  g.fillStyle = '#11181e'; g.fillRect(0, 0, W, H);

  g.fillStyle = '#eee5e9'; g.font = 'bold 21px system-ui, sans-serif';
  g.fillText('Hero backdrop: one 160s brightness loop, line tinted by the live fill', left, 38);
  g.fillStyle = '#96aab9'; g.font = '15px system-ui, sans-serif';
  g.fillText('Each swell: 2s dark / 4s up to 5% / 4s shelf / 20s to peak / 2s held / 8s out.'
    + '  Every fourth peaks at 30%; the tint cycles on threes.', left, 64);

  const y = v => bot - (v / MAX) * (bot - top);
  const x = t => left + (t / 160) * (right - left);
  for (const [v, label] of [[0, '0%'], [0.05, '5%'], [0.15, '15%'], [0.3, '30%']]) {
    g.strokeStyle = '#2c3a46'; g.beginPath(); g.moveTo(left, y(v)); g.lineTo(right, y(v)); g.stroke();
    g.fillStyle = '#8ca0af'; g.font = '14px system-ui, sans-serif';
    g.fillText(label, 26, y(v) + 5);
  }
  g.lineWidth = 3; g.lineCap = 'round';
  for (let i = 1; i < series.length; i++) {
    g.strokeStyle = series[i][2];
    g.beginPath(); g.moveTo(x(series[i - 1][0]), y(series[i - 1][1]));
    g.lineTo(x(series[i][0]), y(series[i][1])); g.stroke();
  }
  g.fillStyle = '#6e8494'; g.font = '14px system-ui, sans-serif';
  for (let s = 0; s <= 160; s += 20) {
    g.strokeStyle = '#5a6e7c'; g.beginPath(); g.moveTo(x(s), bot); g.lineTo(x(s), bot + 5); g.stroke();
    g.fillText(s + 's', x(s) - 11, bot + 24);
  }
  return [W, H];
})()`;

const { cdp, ws, targetId } = await connect();
await cdp.send('Page.navigate', { url: BASE + '/' });
await sleep(2400);

const prepared = await evaluate(cdp, PREPARE);
if (prepared?.error) {
  console.error(`  ${prepared.error}`);
  console.error('  Is BASE_URL serving a build that includes the hero backdrop?');
  process.exit(1);
}

// One brightness loop at 250ms, enough to render a smooth line.
const series = await evaluate(
  cdp,
  `(() => { const out = [];
    for (let ms = 0; ms <= ${BREATHE_MS}; ms += 250) {
      const [opacity, fill] = window.__seek(ms);
      out.push([ms / 1000, opacity, fill]);
    }
    return out; })()`
);

const audit = await evaluate(cdp, AUDIT);
const visible = audit.filter((a) => a.worstOpacity > 0);
const vacuous = audit.filter((a) => a.intermediates === 0);

console.log(`  sampled ${series.length} points across the 160s brightness loop`);
console.log(`  audited ${SWELLS} swell boundaries at 20ms resolution\n`);
for (const a of audit) {
  const margin = a.marginMs === null ? 'n/a' : `${(a.marginMs / 1000).toFixed(2)}s`;
  console.log(
    `    swell ${String(a.swell).padStart(2)} @ ${String(a.boundary / 1000).padStart(3)}s` +
      `  ${String(a.intermediates).padStart(3)} mid-crossfade samples` +
      `  max opacity while fading ${a.worstOpacity.toFixed(4)}` +
      `  margin ${margin}`
  );
}

const peaks = [];
for (let i = 1; i < series.length - 1; i++) {
  const [t, v, fill] = series[i];
  if (v > series[i - 1][1] && v >= series[i + 1][1] && v > 0.06) {
    peaks.push(`${t}s ${v.toFixed(2)} ${PALETTE[fill] || fill}`);
  }
}
console.log(`\n  peaks in this loop: ${peaks.join(' | ')}`);

const size = await evaluate(cdp, CHART(series));
const shot = await cdp.send('Page.captureScreenshot', {
  format: 'png',
  clip: { x: 0, y: 0, width: size[0], height: size[1], scale: 2 },
});
mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, Buffer.from(shot.data, 'base64'));
console.log(`  wrote ${OUT}`);

await fetch(`http://127.0.0.1:${PORT}/json/close/${targetId}`);
ws.close();

if (vacuous.length) {
  console.error(`\n  FAIL: ${vacuous.length} boundaries saw no crossfade at all; the audit proves nothing.`);
  process.exit(1);
}
if (visible.length) {
  console.error(`\n  FAIL: ${visible.length} boundaries change colour while the mark is visible.`);
  for (const a of visible) {
    console.error(`    swell ${a.swell}: opacity ${a.worstOpacity.toFixed(4)} at ${a.worstAt / 1000}s`);
  }
  process.exit(1);
}
console.log('\n  PASS: every colour change completes while the mark is fully dark.');
process.exit(0);
