---
title: "Sync pipeline smoke test"
description: "Fixture post exercising every Obsidian transform: wikilinks, embeds, image dimensions, callouts, comments, aliases, GFM."
pubDate: 2026-05-10
tags: ["meta"]
publish: true
slug: sync-smoke-test
---

This post exists to verify the Obsidian → Astro sync pipeline. The
filename has spaces and capital letters; the `slug` frontmatter forces
the output to be `sync-smoke-test.md`.

%% This is an inline comment that should disappear from the rendered output. %%

%%
And this is a multi-line block comment.
It should also disappear entirely,
including [[fake wikilinks]] inside it.
%%

## Wikilinks

Link to a published post: [[The Next Obsession]]. Link with custom
display text: [[The Next Obsession|that essay about running]].

Link via alias: [[Obsession]] should resolve to the same post.
Another alias: [[Cocodona Essay|the trail-running piece]].

Link to a private note that should be stripped: [[Internal Brain Dump]]
(this should render as plain text "Internal Brain Dump").

## Note embeds (transclusion)

Embed a published note: ![[The Next Obsession]] — should render as a link.

Embed via alias: ![[Obsession|same essay, different name]].

Embed a private note: ![[Internal Brain Dump]] — plain text only.

Embed with .md extension: ![[The Next Obsession.md]].

## Image embeds

Plain image:

![[austin-test.png]]

With alt text:

![[austin-test.png|a small test square]]

With width only (Obsidian sizing):

![[austin-test.png|200]]

With width and height:

![[austin-test.png|200x100]]

## Unsupported attachment

Below is a PDF embed that should degrade gracefully with a warning:

![[my-resume.pdf]]

## Callouts

> [!note]
> Standard note callout.

> [!warning]
> A warning callout, slightly louder.

> [!tip] Custom title
> A tip with a custom title.

## GFM features

A strikethrough: ~~old idea~~. A task list:

- [x] Wire up the sync script
- [x] Strip Obsidian comments
- [ ] Write the real first post

A table:

| Feature      | Status |
|--------------|--------|
| Wikilinks    | ✓      |
| Embeds       | ✓      |
| Image dims   | ✓      |
| Footnotes    | ✓      |

A footnote[^1] in prose.

[^1]: This is the footnote body.

## Inline tags

This paragraph references #astro and #obsidian as inline tags. They
should be extracted into the post's tags array and stripped from the
rendered body.

Tags inside `code spans like #ignored` must be left alone. Same for
fenced code:

```text
#also-ignored
%% and a comment that should NOT be stripped (we're in a fence) %%
```

A trailing inline tag #closing-tag.
