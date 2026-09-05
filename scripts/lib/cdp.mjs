// Minimal Chrome DevTools Protocol client for the design capture scripts
// (scripts/anim-frames.mjs, scripts/anim-trail-modes.mjs). Talks to a Chrome
// that is already listening on a remote-debugging port; opens its own tab and
// closes it again.

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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

/** Open a fresh tab and enable the domains the capture scripts use. */
export async function connect(port) {
  let target;
  try {
    const res = await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' });
    target = await res.json();
  } catch {
    throw new Error(`No Chrome on port ${port}. Start one with --remote-debugging-port=${port}.`);
  }
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve);
    ws.addEventListener('error', reject);
  });
  const cdp = new CDP(ws);
  for (const domain of ['Page', 'Runtime', 'Network']) await cdp.send(`${domain}.enable`);
  await cdp.send('Network.setBypassServiceWorker', { bypass: true });
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  const close = async () => {
    await fetch(`http://127.0.0.1:${port}/json/close/${target.id}`).catch(() => {});
    ws.close();
  };
  return { cdp, ws, targetId: target.id, close };
}

/** Evaluate an expression in the page, awaiting promises, throwing page errors. */
export const evaluate = (cdp, expression) =>
  cdp
    .send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
    .then((r) => {
      if (r.exceptionDetails) {
        throw new Error(r.exceptionDetails.text + ' ' + JSON.stringify(r.exceptionDetails.exception));
      }
      return r.result?.value;
    });

export const setViewport = (cdp, width, height) =>
  cdp.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });

/** Screenshot a rectangle of the page as a PNG data URL. The clip is in
 *  document coordinates and may lie below the fold. */
export const shoot = async (cdp, clip) => {
  const shot = await cdp.send('Page.captureScreenshot', {
    format: 'png', captureBeyondViewport: true, clip: { scale: 1, ...clip },
  });
  return 'data:image/png;base64,' + shot.data;
};
