// Single source of truth for what lives under /design/ao/ and how finished it is.
//
// This is a registry rather than something derived from the pages themselves
// because Astro treats only `getStaticPaths` and `prerender` as special exports
// from `.astro` frontmatter. A top-level `const status` in a page is not
// readable via `import.meta.glob`, so /lab/ could not enumerate pages that way.

export type Status = 'wip' | 'ready';

export interface DesignEntry {
  /** Path segment under /design/ao/. Slugged by role, so renaming the work
   *  never moves the URL. */
  slug: string;
  /** Display name. Free to change without touching the URL. */
  title: string;
  /** One line, shown on the /design/ao/ and /lab/ index pages. */
  blurb: string;
  status: Status;
}

export const DESIGN_ENTRIES: DesignEntry[] = [
  {
    slug: 'logo',
    title: 'The AO mark',
    blurb: 'The animated mark, every treatment it wears, and the three places it already sits.',
    status: 'wip',
  },
  {
    // Slugged by ROLE, like every entry: this is the instrument, and it stays the
    // instrument however finished it gets. /design/ao/logo/ is the page about the mark.
    slug: 'logo-bench',
    title: 'The AO mark bench',
    blurb: 'Every layer and parameter as a live control, and the exporter.',
    status: 'wip',
  },
  {
    slug: 'typeface',
    title: 'Orphan Display',
    blurb: 'A typeface derived from the AO mark, with its two axes live.',
    status: 'wip',
  },
];

/** Look up one entry. Throws rather than returning undefined so that a typo in
 *  a page's slug fails the build loudly instead of silently shipping a page
 *  with the wrong robots directive. */
export function entryFor(slug: string): DesignEntry {
  const entry = DESIGN_ENTRIES.find((e) => e.slug === slug);
  if (!entry) {
    throw new Error(
      `No design-index entry for slug "${slug}". Add one to DESIGN_ENTRIES in src/data/design-index.ts.`,
    );
  }
  return entry;
}

/** The robots directive a page carries for its status. `wip` pages stay out of
 *  search results; the site has no sitemap, so this and inbound links are the
 *  only two levers on discoverability. */
export function robotsFor(status: Status): string {
  return status === 'wip' ? 'noindex, nofollow' : 'index,follow';
}

export function wipEntries(): DesignEntry[] {
  return DESIGN_ENTRIES.filter((e) => e.status === 'wip');
}
