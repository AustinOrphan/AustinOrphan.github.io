# Phase 2: Code Quality Improvements

Medium-priority tasks focused on maintainability, SEO, and user experience enhancements.

## 4. Implement CSS Custom Properties

**Issue:** Colors are hardcoded throughout the stylesheet, making theme changes difficult.

**Benefits:**
- Easier theme management
- Consistent color usage
- Better maintainability

**Implementation Steps:**

### Step 1: Add CSS Custom Properties
Add to the beginning of `styles/main.css`:

```css
:root {
    --color-background: #1D2B35;
    --color-text: #EEE5E9;
    --color-accent-coral: #D16666;
    --color-accent-blue: #2892D7;
    --color-shadow-coral: #D16666;
    --color-shadow-blue: #2892D7;
    --color-hover-background: #D16666;
    --color-hover-text: #1D2B35;
    --color-hover-shadow: #2892D7;
}
```

### Step 2: Update Color References
Replace all hardcoded colors with CSS custom properties:

**Body and HTML:**
```css
html,
body {
    background-color: var(--color-background);
    /* ... other properties ... */
}
```

**Typography:**
```css
h1 {
    color: var(--color-text);
    text-shadow: .1vw .1vw 0 var(--color-shadow-coral), .2vw .2vw 0 var(--color-shadow-blue);
}

p {
    color: var(--color-accent-blue);
}

#cbar {
    color: var(--color-accent-coral);
}

.divider {
    color: var(--color-accent-blue);
}
```

**Icons and Links:**
```css
.icon {
    color: var(--color-text);
}

.icon:hover {
    color: var(--color-hover-text);
    background-color: var(--color-hover-background);
    box-shadow: .3vw .3vw 0 var(--color-hover-shadow);
}
```

**Desktop Styles:**
```css
@media screen and (min-width: 600px) {
    h1 {
        text-shadow: .2vw .2vw 0 var(--color-shadow-blue);
        -webkit-text-stroke-color: var(--color-accent-coral);
    }
}
```

**Testing:**
- Verify all colors render correctly
- Test color consistency across all elements
- Validate CSS syntax

**Estimated Time:** 45 minutes

---

## 5. Remove Unused Code

**Issue:** `second.css` contains navigation/footer components not used by `index.html`.

**Analysis:** The file contains:
- Navigation components (`.topnav`)
- Footer components (`.footerbar`, `.footerlogo`)
- Background image styles (`.bgsvg`)

**Solution:** Remove `second.css` since it's not used.

**Implementation Steps:**
1. Verify `second.css` is not referenced in `index.html`
2. Check if any styles are actually needed
3. Delete `styles/second.css`
4. Clean up any references

**Alternative:** If keeping for future use, rename to `_unused.css` and add comment explaining purpose.

**Testing:**
- Verify website loads correctly without `second.css`
- Check for any missing styles
- Validate no broken references

**Estimated Time:** 30 minutes

---

## 6. Add SEO Meta Tags

**Issue:** Missing essential meta tags for search engines and social media.

**Current Head Section:**
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Austin Orphan</title>
    <!-- favicon and other links -->
</head>
```

**Implementation Steps:**

### Step 1: Add Basic SEO Meta Tags
Add after the viewport meta tag:

```html
<meta name="description" content="Austin Orphan - Creative, Competitive, Curious. Portfolio and contact information for software developer and technical professional.">
<meta name="keywords" content="Austin Orphan, portfolio, software developer, creative, competitive, curious">
<meta name="author" content="Austin Orphan">
```

### Step 2: Add Open Graph Tags
```html
<!-- Open Graph / Facebook -->
<meta property="og:type" content="website">
<meta property="og:title" content="Austin Orphan - Creative, Competitive, Curious">
<meta property="og:description" content="Portfolio and contact information for Austin Orphan, software developer and technical professional.">
<meta property="og:url" content="https://austinorphan.com">
<meta property="og:site_name" content="Austin Orphan">
<meta property="og:locale" content="en_US">
```

### Step 3: Add Twitter Card Tags
```html
<!-- Twitter -->
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Austin Orphan - Creative, Competitive, Curious">
<meta name="twitter:description" content="Portfolio and contact information for Austin Orphan, software developer and technical professional.">
<meta name="twitter:url" content="https://austinorphan.com">
```

### Step 4: Add Additional SEO Tags
```html
<!-- Additional SEO -->
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://austinorphan.com">
```

**Testing:**
- Validate with Facebook Sharing Debugger
- Test with Twitter Card Validator
- Check with Google Rich Results Test
- Verify meta tags appear in page source

**Estimated Time:** 30 minutes

---

## 7. Implement Proper Focus Management

**Issue:** No visible focus indicators for keyboard navigation.

**Research from WCAG:** Focus indicators must:
- Have 3:1 contrast ratio with background
- Be visible for keyboard users
- Use `:focus-visible` for keyboard-only display

**Implementation Steps:**

### Step 1: Add Focus Indicator Styles
Add to `styles/main.css`:

```css
/* Focus indicators for accessibility */
*:focus {
    outline: none; /* Remove default outline */
}

*:focus-visible {
    /* Two-color focus indicator following WCAG guidelines */
    outline: 2px solid var(--color-text);
    outline-offset: 2px;
    box-shadow: 0 0 0 4px var(--color-accent-blue);
}

/* Specific focus styles for icons */
.icon:focus-visible {
    outline: 2px solid var(--color-text);
    outline-offset: 2px;
    box-shadow: 0 0 0 4px var(--color-accent-blue);
}

/* Focus for links */
a:focus-visible {
    outline: 2px solid var(--color-text);
    outline-offset: 2px;
    box-shadow: 0 0 0 4px var(--color-accent-blue);
}
```

### Step 2: Ensure Keyboard Navigation Order
Verify tab order follows logical flow:
1. Social media links (GitHub, LinkedIn, Resume, Email, Project)

### Step 3: Test Focus Indicators
- Tab through all interactive elements
- Verify focus indicators are visible
- Test with keyboard-only navigation
- Check contrast ratios meet WCAG standards

**Testing:**
- Use Tab key to navigate through all links
- Verify focus indicators are clearly visible
- Test with screen reader
- Check contrast ratios with accessibility tools

**Estimated Time:** 60 minutes

---

## Phase 2 Success Criteria

✅ **CSS Custom Properties Implemented**
- All colors use CSS custom properties
- Color consistency maintained
- Easy theme management enabled

✅ **Unused Code Removed**
- `second.css` removed or properly organized
- No broken references
- Cleaner codebase

✅ **SEO Meta Tags Added**
- All essential meta tags present
- Open Graph and Twitter Card tags functional
- Search engine optimization improved

✅ **Focus Management Implemented**
- Visible focus indicators for keyboard users
- WCAG-compliant contrast ratios
- Proper keyboard navigation order

## Total Phase 2 Time: 2-3 hours

After completing Phase 2, proceed to Phase 3 enhancements.