// The mark's paint layers, and the names for their combinations.
//
// Ink is always on. Outline and shadow are independent, which is two booleans and therefore
// four combinations. A `variant` is a NAME for one of them, not a mechanism: it resolves to
// the classes below, and anything wanting a combination directly -- the bench -- toggles
// those classes instead.
//
// This replaced a three-value enum, hero/plain/flat, over the same two booleans. Two of its
// values were the same drawing (plain and flat differed only in which colour the fill fell
// back to, and flat's accent default was never visible at its one real call site), and two
// of the four combinations had no name at all.
//
// A plain .ts module rather than exports from Logo.astro's frontmatter: Astro treats only
// getStaticPaths and prerender as special exports from a component, so a named export there
// is not importable. Same reason src/data/design-index.ts is a module.

export type LogoVariant = 'plain' | 'outlined' | 'shadowed' | 'hero';

export interface LogoLayers {
  outline: boolean;
  shadow: boolean;
}

/** Which extra passes each named variant turns on. Ink is not listed: it is always on. */
export const LOGO_LAYERS: Record<LogoVariant, LogoLayers> = {
  plain: { outline: false, shadow: false },
  outlined: { outline: true, shadow: false },
  shadowed: { outline: false, shadow: true },
  hero: { outline: true, shadow: true },
};

/** The layer classes a variant resolves to. Shared, so the two components cannot drift. */
export function layerClasses(variant: LogoVariant): string {
  const { outline, shadow } = LOGO_LAYERS[variant];
  return [outline && 'logo-layer-outline', shadow && 'logo-layer-shadow']
    .filter(Boolean)
    .join(' ');
}

/** Every variant name, in the order the bench and the docs list them. */
export const LOGO_VARIANTS = Object.keys(LOGO_LAYERS) as LogoVariant[];
