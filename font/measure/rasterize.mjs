// svg -> png through the Chrome already listening on CDP_PORT. Usage: node rasterize.mjs a.svg b.svg ...
import { readFileSync, writeFileSync } from 'node:fs';
const PORT = Number(process.env.CDP_PORT || 9222);
const t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r); ws.addEventListener('error', j); });
let id = 0; const pending = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise(r => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
await send('Page.enable');
for (const f of process.argv.slice(2)) {
  const svg = readFileSync(f, 'utf8');
  const w = Number(svg.match(/width="([\d.]+)"/)[1]), h = Number(svg.match(/height="([\d.]+)"/)[1]);
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: 'data:text/html;charset=utf-8,' + encodeURIComponent(`<body style="margin:0;background:#1D2B35">${svg}</body>`) });
  await new Promise(r => setTimeout(r, 400));
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  const out = f.replace(/\.svg$/, '.png');
  writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
  console.log('  ' + out.split('/').pop());
}
await fetch(`http://127.0.0.1:${PORT}/json/close/${t.id}`); ws.close();
