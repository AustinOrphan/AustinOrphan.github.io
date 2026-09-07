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
