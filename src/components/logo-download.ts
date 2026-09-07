// Turn a rendered mark into a file you can keep.
//
// The mark's geometry is all attributes, but its COLOUR is not: Logo.astro sets fill and
// stroke from `.site-logo-<variant> .site-logo-mark` rules that resolve custom properties
// against the theme. A node lifted straight out of the page and saved would arrive with no
// paint at all, so the paint is read back off getComputedStyle and written on as attributes.
//
// The animated download keeps its classes instead, and carries the component's own rules with
// it, so the file plays on its own when opened.

// Only fill and stroke come from CSS. stroke-width, stroke-linejoin and paint-order are
// already attributes in Logo.astro, so cloneNode carries them and copying the COMPUTED value
// would only corrupt them -- it rewrites 300 as "300px" and "stroke fill markers" as "stroke".
const PAINT = ['fill', 'stroke'];

/** The theme values the component's rules fall back to, needed by the animated download. */
const THEME = ['--color-primary', '--color-secondary', '--color-accent', '--color-background',
               '--logo-ink', '--logo-outline', '--logo-shadow'];

/** SVG's own initial values, so an element that just inherits them writes nothing. */
const INITIAL: Record<string, string> = { fill: 'rgb(0, 0, 0)', stroke: 'none' };

function paintAll(src: Element, dst: Element, inherited: Record<string, string> = INITIAL): void {
  const cs = getComputedStyle(src);
  const own: Record<string, string> = { ...inherited };
  for (const prop of PAINT) {
    const v = cs.getPropertyValue(prop).trim();
    if (!v) continue;
    own[prop] = v;
    // Only write what actually differs from what this element would inherit anyway, so the
    // file carries the paint once, on the element that changes it, and nowhere else.
    if (v !== inherited[prop]) dst.setAttribute(prop, v);
  }
  const sk = Array.from(src.children);
  const dk = Array.from(dst.children);
  for (let i = 0; i < sk.length && i < dk.length; i++) paintAll(sk[i], dk[i], own);
}

/** The component's own classes. A rule is the animation's if it targets one of these. */
const OWN = /(^|[\s.,>+~])(site-logo-anim|la-(play|pieces|final|ring|leg|bar|mask|trail))/;
/** Layout classes on the demo page that merely start with the same two letters. */
const PAGE = /\.la-(demo|dl)\b/;

function wanted(sel: string): boolean {
  return OWN.test(sel) && !PAGE.test(sel);
}

/**
 * Every rule in the document that belongs to the animation, @media wrappers preserved.
 *
 * Matching on the text "la-" is not enough in either direction. It misses the rule that
 * DEFINES the timeline -- `.site-logo-anim { --la-t-...: ... }`, whose selector has no ".la-"
 * at all -- and without those custom properties every `animation` shorthand that references
 * them is invalid, so the saved file renders blank. It also catches the demo page's own
 * `.la-demo` layout. So match selectors against the component's classes instead.
 */
function animationCss(): string {
  const out: string[] = [];
  const visit = (rules: CSSRuleList): void => {
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSKeyframesRule) {
        if (rule.name.startsWith('la-')) out.push(rule.cssText);
      } else if (rule instanceof CSSMediaRule) {
        const inner: string[] = [];
        for (const r of Array.from(rule.cssRules)) {
          if (r instanceof CSSStyleRule && wanted(r.selectorText)) inner.push(r.cssText);
          else if (r instanceof CSSKeyframesRule && r.name.startsWith('la-')) inner.push(r.cssText);
        }
        if (inner.length) out.push(`@media ${rule.conditionText} {\n${inner.join('\n')}\n}`);
      } else if (rule instanceof CSSStyleRule) {
        if (wanted(rule.selectorText)) out.push(rule.cssText);
      }
    }
  };
  for (const sheet of Array.from(document.styleSheets)) {
    try { visit((sheet as CSSStyleSheet).cssRules); } catch { /* cross-origin */ }
  }
  return out.join('\n');
}

export interface SerializeOptions {
  /** Keep the classes, embed the animation's own CSS, and start it playing. */
  animated?: boolean;
  /** Square pixel size written onto the root; the viewBox is unchanged either way. */
  size?: number;
}

export function serializeLogo(svg: SVGSVGElement, opts: SerializeOptions = {}): string {
  const { animated = false, size } = opts;
  const clone = svg.cloneNode(true) as SVGSVGElement;
  paintAll(svg, clone);

  if (animated) {
    const cs = getComputedStyle(svg);
    for (const v of THEME) {
      const val = cs.getPropertyValue(v).trim();
      if (val) clone.style.setProperty(v, val);
    }
    clone.classList.add('la-play');
    const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
    style.textContent = animationCss();
    clone.insertBefore(style, clone.firstChild);
  } else {
    // paint is on the attributes now, so the classes would only be dead weight
    clone.removeAttribute('class');
    clone.querySelectorAll('[class]').forEach((el) => el.removeAttribute('class'));
  }

  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  // the page's id would collide with anything the file is later pasted into
  clone.removeAttribute('id');
  // demo-page classes are not part of the mark; drop them so the file carries only its own
  clone.classList.remove(...Array.from(clone.classList).filter((c) => PAGE.test('.' + c)));
  clone.removeAttribute('aria-hidden');
  clone.removeAttribute('focusable');
  clone.setAttribute('role', 'img');
  // A downloaded mark should not inherit the preview's on-page size. The viewBox makes it
  // scale, and a square intrinsic size keeps it sane where one is required.
  const px = size ?? 512;
  clone.setAttribute('width', String(px));
  clone.setAttribute('height', String(px));
  return '<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(clone);
}

function save(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // revoke on the next turn: Safari reads the blob after click() returns
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function downloadSvg(svg: SVGSVGElement, filename: string, opts: SerializeOptions = {}): void {
  save(new Blob([serializeLogo(svg, opts)], { type: 'image/svg+xml' }), filename);
}

/** Rasterise through an <img>, which needs the SVG as a data URL rather than a blob URL. */
export function downloadPng(svg: SVGSVGElement, filename: string, size = 1024): Promise<void> {
  const text = serializeLogo(svg, { size });
  const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(text);
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = canvas.height = size;
      const ctx = canvas.getContext('2d');
      if (!ctx) { reject(new Error('no 2d context')); return; }
      ctx.drawImage(img, 0, 0, size, size);
      canvas.toBlob((blob) => {
        if (!blob) { reject(new Error('toBlob failed')); return; }
        save(blob, filename);
        resolve();
      }, 'image/png');
    };
    img.onerror = () => reject(new Error('the serialised SVG did not load'));
    img.src = url;
  });
}

// ---------------------------------------------------------------------------------------
// Video.
//
// Drawing an animating SVG into a canvas does not work: an <img> holding an SVG paints one
// static state, and the animation inside it never advances. So each frame is BAKED instead --
// the animations are seeked to that instant and every property they touch is read back and
// written on as an inline style, giving a still SVG of that moment, which does rasterise.

// The properties the write-on animates, plus the paint they sit on, plus `display` -- a baked
// frame is a STANDALONE svg with no stylesheet, so anything a rule was hiding comes back. The
// re-treated mark keeps hero's shadow group in its markup, and unpainted SVG is black, so
// without this a hard black copy of the mark sat behind every frame, offset by 22 units, which
// read as the circle being doubled.
const FRAME_PROPS = ['display', 'stroke-dasharray', 'stroke-dashoffset', 'r', 'opacity',
                     'transform', 'stroke-width', 'fill', 'stroke'];
/** `none` is the meaningful value for these three, not the one to skip. */
const KEEP_NONE = new Set(['display', 'fill', 'stroke']);

function bake(src: Element, dst: Element): void {
  const cs = getComputedStyle(src);
  const style = (dst as SVGElement).style;
  for (const prop of FRAME_PROPS) {
    const v = cs.getPropertyValue(prop).trim();
    if (!v || v === 'auto') continue;
    if (v === 'none' && !KEEP_NONE.has(prop)) continue;
    style.setProperty(prop, v);
    if (prop === 'display' && v === 'none') return;   // nothing under it matters
  }
  const sk = Array.from(src.children);
  const dk = Array.from(dst.children);
  for (let i = 0; i < sk.length && i < dk.length; i++) bake(sk[i], dk[i]);
}

function animationsOf(svg: SVGSVGElement): Animation[] {
  return document.getAnimations().filter((a) => {
    // `target` lives on KeyframeEffect, not on the AnimationEffect base
    const eff = a.effect;
    const t = eff instanceof KeyframeEffect ? eff.target : null;
    return t instanceof Element && svg.contains(t);
  });
}

/** How long the whole choreography runs, in ms, read off the animations themselves. */
export function animationDuration(svg: SVGSVGElement): number {
  let end = 0;
  for (const a of animationsOf(svg)) {
    const t = a.effect?.getComputedTiming();
    if (!t) continue;
    end = Math.max(end, Number(t.delay || 0) + Number(t.activeDuration || 0));
  }
  return end;
}

/** A still SVG of this instant, with the animated values written in. */
function frameAt(svg: SVGSVGElement, anims: Animation[], ms: number, size: number): string {
  for (const a of anims) a.currentTime = ms;
  const clone = svg.cloneNode(true) as SVGSVGElement;
  bake(svg, clone);

  // Resolve the hand-off instead of freezing it. The write-on ends by cross-fading the drawn
  // pieces for the finished mark, and the two are not the same drawing: the pieces are masked
  // strokes, the mark is the real outline with its R5 feet and its unioned overlaps. Live, that
  // difference passes in 80ms and is invisible. Baked, a frame taken mid-fade holds the true
  // mark at partial opacity over the approximation, and everywhere they differ -- the A's leg
  // feet, the bar's ends, the thick lower-left of the ring -- shows as a grey ghost.
  // So a frame is either before the hand-off or after it, never between.
  const fin = clone.querySelector<SVGElement>('.la-final');
  const pieces = clone.querySelector<SVGElement>('.la-pieces');
  if (fin && pieces) {
    const handed = parseFloat(getComputedStyle(svg.querySelector('.la-final') as Element).opacity) >= 0.5;
    fin.style.opacity = handed ? '1' : '0';
    pieces.style.opacity = handed ? '0' : '1';
  }
  clone.classList.remove('la-play');           // the values are baked; no animation wanted
  clone.removeAttribute('id');
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('width', String(size));
  clone.setAttribute('height', String(size));
  return new XMLSerializer().serializeToString(clone);
}

function load(text: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('frame did not load'));
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(text);
  });
}

/** The best container this browser will record, or null if it will record none. */
export function videoMimeType(): string | null {
  if (typeof MediaRecorder === 'undefined') return null;
  for (const t of ['video/mp4;codecs=avc1', 'video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm']) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return null;
}

export interface VideoOptions {
  fps?: number;
  size?: number;
  /** Slow the playback down; 1 is real time, 4 is quarter speed. */
  slow?: number;
  background?: string;
  /** Bits per second. A flat-colour mark is all hard edges, which is the worst case for an
   *  inter-frame codec: at the default rate h264 rings around them, and the artefact is
   *  clearest on the still tail, where it reads as a faint crescent inside the ring. */
  bitrate?: number;
  onProgress?: (done: number, total: number) => void;
}

/**
 * Record the write-on to a video Blob.
 *
 * MediaRecorder timestamps by WALL CLOCK, so the frames have to be fed at the pace they should
 * play back at; the recording therefore takes about as long as the clip it produces.
 */
export async function recordVideo(svg: SVGSVGElement, opts: VideoOptions = {}): Promise<Blob> {
  const { fps = 30, size = 512, slow = 1, background = '', bitrate = 24_000_000, onProgress } = opts;
  const mimeType = videoMimeType();
  if (!mimeType) throw new Error('this browser cannot record video');

  // The page drops `la-play` once the write-on settles, which takes the animations with it,
  // so by the time anyone clicks there is usually nothing to record. Start it again.
  let anims = animationsOf(svg);
  if (!anims.length) {
    svg.classList.remove('la-play');
    void svg.getBoundingClientRect();          // force a reflow so the restart takes
    svg.classList.add('la-play');
    anims = animationsOf(svg);
  }
  if (!anims.length) throw new Error('the mark has no animation to record');
  const wasPlaying = anims.map((a) => a.playState);
  const total = animationDuration(svg) || 1400;
  const count = Math.max(2, Math.round((total / 1000) * fps));

  // bake every frame up front: rasterising is far slower than the frame interval
  const frames: HTMLImageElement[] = [];
  for (const a of anims) a.pause();
  for (let i = 0; i < count; i++) {
    frames.push(await load(frameAt(svg, anims, (i / (count - 1)) * total, size)));
    onProgress?.(i + 1, count);
  }

  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('no 2d context');

  const stream = canvas.captureStream(0);
  const track = stream.getVideoTracks()[0] as CanvasCaptureMediaStreamTrack;
  const chunks: Blob[] = [];
  const rec = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: bitrate });
  rec.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
  const done = new Promise<void>((resolve) => { rec.onstop = () => resolve(); });
  rec.start();

  const step = (1000 / fps) * slow;
  for (const img of frames) {
    ctx.clearRect(0, 0, size, size);
    if (background) { ctx.fillStyle = background; ctx.fillRect(0, 0, size, size); }
    ctx.drawImage(img, 0, 0, size, size);
    track.requestFrame();
    await new Promise((r) => setTimeout(r, step));
  }
  rec.stop();
  await done;

  // leave the mark as it was found
  anims.forEach((a, i) => { if (wasPlaying[i] === 'running') a.play(); });
  return new Blob(chunks, { type: mimeType });
}

export async function downloadVideo(svg: SVGSVGElement, name: string, opts: VideoOptions = {}): Promise<void> {
  const blob = await recordVideo(svg, opts);
  const ext = blob.type.includes('mp4') ? 'mp4' : 'webm';
  save(blob, `${name}.${ext}`);
}
