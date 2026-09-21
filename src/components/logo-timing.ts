// When the write-on is over, derived rather than restated.
//
// logo-choreography.ts is generated from the speed law, so the clip's length is whatever
// falls out of the geometry and moves whenever the mark does. Anything that needs to know
// it -- a scrub slider's range, a duration readout, a caption -- has to compute it from
// those constants, or it silently describes a choreography that no longer exists.
//
// It had drifted. The lab used 1300ms for hero and 1100ms for the others; the real ends are
// 1360ms and 1160ms, so the scrub could not reach the last 60ms, which is exactly where the
// hero treatment settles, and every readout on the page was wrong.
//
// Note this is the last instant anything is still MOVING, not AFTER.done. `done` (1.380) is
// the component's own note that everything is over, and it drives no animation -- nothing
// references the `--la-t-done` it emits. Seeking a scrub past 1.360 would do nothing, so the
// end of motion is the number a control wants.
// Imported with its extension, unlike the component's own extensionless imports, so that
// scripts/routes.test.mjs can pull this in under plain Node the way it already pulls in
// design-index.ts. Astro's base tsconfig sets allowImportingTsExtensions, so both resolve it.
import { AFTER, BEATS } from './logo-choreography.ts';
import { LOGO_LAYERS, type LogoVariant } from './logo-layers.ts';

/** The draw itself: every beat, plus the moment the drawn pieces switch off. */
const drawEnd = Math.max(
  AFTER.pieces,
  ...Object.values(BEATS).map((b) => b.t + b.d),
);

/** Hero only: the outline and the offset copy grow in once the mark has landed. */
const treatEnd = AFTER.treatT + AFTER.treatD;

/** Seconds at speed 1, by whether the variant carries the hero treatment. */
export const CHOREOGRAPHY_END = {
  treated: Math.max(drawEnd, treatEnd),
  untreated: drawEnd,
} as const;

/**
 * A mark runs the treatment beat if it has any layer to settle in, which is what the outline
 * and shadow animations key on. Only `plain` ends when the draw does.
 *
 * This used to test `variant === 'hero'`, which was right while hero was the only variant with
 * either layer. `outlined` and `shadowed` broke that assumption the moment they existed, and
 * they would have reported 1160ms while actually running to 1360.
 */
export function endSeconds(variant: string, speed = 1): number {
  const layers = LOGO_LAYERS[variant as LogoVariant];
  const treated = layers ? layers.outline || layers.shadow : true;
  return (treated ? CHOREOGRAPHY_END.treated : CHOREOGRAPHY_END.untreated) / speed;
}

/**
 * The same question asked by LAYER rather than by variant name.
 *
 * Any layer that settles in after the draw runs the treatment beat: the outline's width, the
 * shadow's offset, and now the cut and knockout cross-fades, which land the solid mark and
 * then take the treatment over that same window. `cut` and `knock` are not in the variant
 * table -- they are export treatments -- so a caller holding raw layer state has to ask this
 * way or it reports 1160ms for a mark that runs to 1360.
 */
export function endMsForLayers(
  layers: { outline?: boolean; shadow?: boolean; cut?: boolean; knock?: boolean },
  speed = 1,
): number {
  const treated = !!(layers.outline || layers.shadow || layers.cut || layers.knock);
  const end = treated ? CHOREOGRAPHY_END.treated : CHOREOGRAPHY_END.untreated;
  return Math.round((end / speed) * 1000);
}

/** The same, in whole milliseconds, which is what a range input wants. */
export function endMs(variant: string, speed = 1): number {
  return Math.round(endSeconds(variant, speed) * 1000);
}
