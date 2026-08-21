---
title: "{{title}}"
description: 
pubDate: "{{date:YYYY-MM-DD}}"
tags: []
publish: false
# slug: custom-url-override      # uncomment to set a non-default URL slug
# aliases: ["Other Name"]        # uncomment to let [[Other Name]] resolve here
---
%% ====================================================================
   Blog post template — fields above are read by scripts/sync-blog.mjs.

   Required:
     title        Shown on the post page, <title> tag, OG cards.
     description  One-line summary used by SEO, RSS, and link previews.
     pubDate      YYYY-MM-DD. Future dates schedule the post; daily cron
                  picks them up on/after the date.
     publish      false = stays private. Flip to true to ship.

   Optional:
     tags         Inline #tags in the body are merged into this list.
     slug         Override the default filename-derived URL slug.
     aliases      Wikilinks ([[Alt Name]]) and embeds (![[Alt Name]])
                  from other posts resolve here.

   Obsidian syntax that ships transformed:
     [[Note]]              → /blog/<slug>/  (or plain text if not published)
     [[Note|display]]      → [display](/blog/<slug>/)
     [[Note#Heading]]      → anchor link
     ![[image.png]]        → image, copied to /blog-assets/<slug>/
     ![[image.png|400]]    → image with width="400"
     ![[image.png|400x300]]→ image with width/height
     ![[Note]]             → link (transclusion → link, not inlined)
     > [!note] Title       → callout (note / warning / tip / etc.)
     #inline-tags          → merged into the tags array
     %% private comment %% → stripped from output

   Anything you write here in %% ... %% never reaches the site.
   ==================================================================== %%

## Section heading


