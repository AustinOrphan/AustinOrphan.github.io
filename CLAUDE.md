# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal portfolio website for Austin Orphan, hosted on GitHub Pages with a custom domain (austinorphan.com). It's a minimalist, single-page static site showcasing contact information and social links.

## Architecture

**Static Site Structure:**
- `index.html` - Main entry point with semantic HTML5 structure
- `styles/main.css` - Primary stylesheet with responsive design
- `styles/second.css` - Alternative stylesheet (contains navigation/footer components not currently used)
- `CNAME` - Custom domain configuration for GitHub Pages
- Favicon package and resume PDF in root directory

**Design System:**
- Mobile-first responsive design using CSS Grid and Flexbox
- Viewport-based typography (vw units) for fluid scaling
- Three-color palette: #1D2B35 (background), #EEE5E9 (text), #D16666 (coral), #2892D7 (blue)
- External dependencies: Google Fonts (Anta, Comfortaa, Source Sans Pro) and Phosphor Icons

## Development Commands

**Local Development:**
```bash
# Serve locally for testing
python -m http.server 8000
# or
python3 -m http.server 8000

# Then visit http://localhost:8000
```

**Deployment:**
```bash
# Deploy to GitHub Pages (automatic)
git add .
git commit -m "Update site"
git push origin master
```

## Key Implementation Details

**CSS Architecture:**
- `main.css` contains the active design system with mobile-first approach
- `second.css` imports main.css and extends it with navigation/footer components (legacy/future use)
- Media query breakpoint at 600px for desktop styles
- Uses webkit-text-stroke for text outline effects on desktop

**HTML Structure:**
- Semantic wrapper classes: `.page-wrapper` → `.content-wrapper`
- Social links in `#linkBar` using CSS Grid (5 columns)
- Phosphor Icons loaded from CDN with `ph-duotone` classes
- Complete favicon implementation for all platforms

**Responsive Behavior:**
- Mobile: Absolute positioning for link bar, larger touch targets
- Desktop: Relative positioning, hover effects with transitions, smaller compact layout

## Common Tasks

**Content Updates:**
- Update resume: Replace `AustinOrphanResume.pdf`
- Add social links: Update `index.html` and corresponding CSS in `styles/main.css`
- Design changes: Modify color variables and layout in `styles/main.css`

**Domain Configuration:**
- Custom domain managed through `CNAME` file
- GitHub Pages automatically serves from master branch