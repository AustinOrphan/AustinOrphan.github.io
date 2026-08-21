import { defineConfig } from 'astro/config';
import remarkGfm from 'remark-gfm';
import rehypeCallouts from 'rehype-callouts';

export default defineConfig({
  site: 'https://austinorphan.com',
  output: 'static',
  trailingSlash: 'ignore',
  markdown: {
    remarkPlugins: [remarkGfm],
    rehypePlugins: [rehypeCallouts],
  },
});
