---
title: "Hello World"
description: "First post on the new Astro-powered blog."
pubDate: 2026-05-08
tags: ["meta", "astro"]
draft: false
---

Welcome to the blog. This is a test post to verify the Astro content collection is working.

## What's New

The portfolio has been migrated from vanilla HTML to Astro. The blog is powered by Astro content collections — posts are markdown files committed directly to the repo.

## Writing

To publish a new post, create a `.md` file in `src/content/blog/` with the required frontmatter:

```yaml
---
title: "Your title"
description: "One-sentence summary"
pubDate: 2026-05-08
tags: ["tag1", "tag2"]
draft: false
---
```

Set `draft: true` to write locally without publishing.
