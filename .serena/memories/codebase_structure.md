# Codebase Structure

## Root Directory
```
/
├── index.html              # Main landing page
├── CNAME                   # Custom domain configuration
├── AustinOrphanResume.pdf  # Downloadable resume
├── about.txt               # Favicon attribution info
├── .gitignore              # Git ignore rules (macOS specific)
├── styles/                 # CSS stylesheets
│   ├── main.css            # Primary styles
│   └── second.css          # Secondary/alternate styles
└── [favicon files]         # Complete favicon package
```

## Key Files

### index.html
- Main entry point
- Single-page application structure
- Contains all content and links
- Responsive meta tags
- External font and icon imports

### styles/main.css
- Primary stylesheet
- Responsive design rules
- Custom color scheme
- Typography definitions
- Icon styling and hover effects

### styles/second.css
- Alternative stylesheet (appears unused in current index.html)
- Contains navigation and footer styles
- May be for future features or alternate layouts

## Assets
- **Favicon Package**: Complete set of favicon files for all platforms
- **Resume**: PDF file served directly from root
- **No Images**: Uses icon fonts instead of image files
- **No JavaScript**: Pure HTML/CSS implementation