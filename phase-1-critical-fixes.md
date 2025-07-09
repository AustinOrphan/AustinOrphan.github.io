# Phase 1: Critical Fixes

High-priority fixes that address immediate functionality and accessibility issues.

## 1. Fix Broken Favicon References

**Issue:** Lines 19-20 in `index.html` reference non-existent favicon files.

**Current Code:**
```html
<link rel="icon" type="image/svg+xml" href="/assets/images/favicon.svg">
<link rel="icon" type="image/png" href="/assets/images/favicon.png">
```

**Solution:** Remove these lines since the files don't exist.

**Implementation Steps:**
1. Open `index.html`
2. Locate lines 19-20
3. Delete both lines
4. Verify existing favicon files work:
   - `/favicon.ico`
   - `/favicon-16x16.png`
   - `/favicon-32x32.png`
   - `/apple-touch-icon.png`

**Testing:**
- Load page and check browser console for 404 errors
- Verify favicon displays correctly in browser tab
- Test across different browsers

**Estimated Time:** 15 minutes

---

## 2. Add Proper Accessibility Labels

**Issue:** All social media links use icon-only navigation without accessible labels.

**Current Code:**
```html
<a href="https://github.com/austinorphan" target="_blank" rel="noopener noreferrer">
    <i class="icon ph-duotone ph-github-logo"></i>
</a>
```

**Solution:** Add `aria-label` attributes to all links.

**Implementation Steps:**
1. Open `index.html`
2. Locate each social media link in `#linkBar`
3. Add appropriate `aria-label` attributes:

**Updated Code:**
```html
<div id="linkBar">
    <a href="https://github.com/austinorphan" target="_blank" rel="noopener noreferrer" aria-label="GitHub Profile">
        <i class="icon ph-duotone ph-github-logo"></i>
    </a>
    <a href="https://www.linkedin.com/in/austinorphan/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn Profile">
        <i class="icon ph-duotone ph-linkedin-logo"></i>
    </a>
    <a href="AustinOrphanResume.pdf" download aria-label="Download Resume">
        <i class="icon ph-duotone ph-read-cv-logo"></i>
    </a>
    <a href="mailto:AustinGOrphan@gmail.com" aria-label="Email Contact">
        <i class="icon ph-duotone ph-envelope-simple"></i>
    </a>
    <a href="/ProjectileMotionSimulator/src/" aria-label="Projectile Motion Simulator Project">
        <i class="icon ph-duotone ph-meteor"></i>
    </a>
</div>
```

**Testing:**
- Use screen reader to verify labels are announced
- Test keyboard navigation (Tab key)
- Verify labels are descriptive and clear

**Estimated Time:** 30 minutes

---

## 3. Fix CSS Syntax Error

**Issue:** Invalid space in `calc()` function in `main.css:22`.

**Current Code:**
```css
height: calc (100vh - 80px);
```

**Solution:** Remove the space in the `calc()` function.

**Implementation Steps:**
1. Open `styles/main.css`
2. Locate line 22 in `.page-wrapper`
3. Fix the syntax error
4. Also check line 31 in `.content-wrapper` for the same issue

**Updated Code:**
```css
.page-wrapper {
    display: flex;
    width: 100%;
    height: calc(100vh - 80px);
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.content-wrapper {
    display: flex;
    width: 100%;
    height: calc(100% - 80px);
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 0 0 80px 0;
}
```

**Testing:**
- Validate CSS using browser developer tools
- Check that layout renders correctly
- Verify no console errors

**Estimated Time:** 15 minutes

---

## Phase 1 Success Criteria

✅ **Favicon References Fixed**
- ✅ No 404 errors in browser console
- ✅ Favicon displays correctly in browser tab

✅ **Accessibility Labels Added**
- ✅ All interactive elements have descriptive labels
- ✅ Screen reader announces link purposes clearly
- ✅ Keyboard navigation works properly

✅ **CSS Syntax Corrected**
- ✅ CSS validates without errors
- ✅ Layout renders correctly
- ✅ No console errors related to CSS

## Phase 1 Status: ✅ COMPLETED

**Completion Date:** July 9, 2025
**Total Time:** 1 hour
**Git Branch:** `phase-1-critical-fixes` (merged to master)
**Commit:** `d630d36` - Apply Phase 1 fixes on master branch

All Phase 1 critical fixes have been successfully implemented and tested. Ready to proceed to Phase 2 code quality improvements.