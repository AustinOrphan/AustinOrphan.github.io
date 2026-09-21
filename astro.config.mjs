import { defineConfig } from 'astro/config';
import remarkGfm from 'remark-gfm';
import rehypeCallouts from 'rehype-callouts';

export default defineConfig({
  site: 'https://austinorphan.com',
  output: 'static',
  trailingSlash: 'ignore',
  // The three former bench paths. All were noindex and unlinked, so this is for
  // existing bookmarks and history rather than for search engines. Static output
  // emits a meta-refresh stub per entry.
  redirects: {
    '/orphan-display': '/design/ao/typeface/',
    '/logo-animation': '/design/ao/logo/',
    // Honest again after the split: /logo-lab WAS the lab, and the lab is the bench.
    // It had been pointing at the merged page, which was only half right.
    '/logo-lab': '/design/ao/logo-bench/',
  },
  markdown: {
    remarkPlugins: [remarkGfm],
    rehypePlugins: [rehypeCallouts],
  },
});
