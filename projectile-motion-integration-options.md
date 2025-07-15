# Projectile Motion Simulator Integration Options

This document outlines different approaches for integrating the ProjectileMotionSimulator repository into the main portfolio site while keeping it up to date.

## Current Status
The projectile motion simulator is currently live at `https://austinorphan.com/ProjectileMotionSimulator/src/index.html`. The simulator code exists in a separate GitHub repository: `https://github.com/austinorphan/ProjectileMotionSimulator`. The portfolio was previously referencing a broken relative path `/ProjectileMotionSimulator/src/` which has been fixed to point to the working live URL.

## Integration Options

### Option 1: GitHub Pages + Direct Link (Recommended - Simplest)
**Implementation:**
```html
<a href="https://austinorphan.github.io/ProjectileMotionSimulator/" target="_blank">
```

**Pros:**
- ✅ Always up to date automatically
- ✅ Zero maintenance required
- ✅ Simple implementation
- ✅ No repository bloat

**Cons:**
- ❌ No CSS control over simulator appearance
- ❌ Takes user away from portfolio site
- ❌ Separate page experience

**Setup Required:**
1. Enable GitHub Pages on ProjectileMotionSimulator repository
2. Update portfolio link to GitHub Pages URL

---

### Option 2: GitHub Pages + Iframe Embed
**Implementation:**
```html
<iframe src="https://austinorphan.github.io/ProjectileMotionSimulator/" 
        width="100%" height="600px" 
        frameborder="0"
        title="Projectile Motion Simulator">
</iframe>
```

**Pros:**
- ✅ Always up to date automatically
- ✅ Stays within portfolio site
- ✅ Embedded user experience

**Cons:**
- ⚠️ **No CSS override possible** (same-origin policy)
- ⚠️ Mobile responsiveness depends on simulator's design
- ⚠️ Fixed height iframe limitations
- ⚠️ Potential loading performance impact

**Setup Required:**
1. Enable GitHub Pages on ProjectileMotionSimulator repository
2. Add iframe embed in projects component
3. Handle responsive design considerations

---

### Option 3: Git Submodules (Best for CSS Control)
**Implementation:**
```bash
git submodule add https://github.com/austinorphan/ProjectileMotionSimulator.git ProjectileMotionSimulator
git submodule update --remote  # Updates to latest
```

**Pros:**
- ✅ Full CSS control and theming integration
- ✅ Can be updated with single command
- ✅ Files become part of portfolio site
- ✅ Complete customization possible
- ✅ No external dependencies for users

**Cons:**
- ❌ Manual updates required (`git submodule update --remote`)
- ❌ Repository size increases
- ❌ More complex Git workflow
- ❌ Deployment complexity

**Setup Required:**
1. Add simulator as Git submodule
2. Configure build/deployment to include submodule
3. Document update process for future maintenance

---

### Option 4: GitHub Actions Auto-Sync (Most Automated)
**Implementation:**
```yaml
# .github/workflows/sync-simulator.yml
name: Sync Projectile Motion Simulator
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  workflow_dispatch:  # Manual trigger
  repository_dispatch:  # Triggered by simulator repo

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          submodules: true
      
      - name: Update submodule
        run: |
          git submodule update --remote ProjectileMotionSimulator
          git add ProjectileMotionSimulator
          git commit -m "Auto-update ProjectileMotionSimulator" || exit 0
          git push
```

**Pros:**
- ✅ Fully automated updates
- ✅ Complete CSS control and integration
- ✅ Integrated into portfolio site
- ✅ Can be triggered by simulator repo changes

**Cons:**
- ⚠️ More complex setup and maintenance
- ⚠️ Requires GitHub Actions knowledge
- ⚠️ Potential for automated commits
- ⚠️ Repository size increases

**Setup Required:**
1. Set up Git submodule
2. Create GitHub Actions workflow
3. Configure repository secrets if needed
4. Set up repository dispatch triggers (optional)

---

### Option 5: CDN/External Hosting
**Implementation:**
```html
<a href="https://your-cdn.com/projectile-motion-simulator/" target="_blank">
```

**Pros:**
- ✅ Can use custom domain
- ✅ Potentially better performance
- ✅ Always up to date

**Cons:**
- ❌ Additional hosting costs
- ❌ More infrastructure to maintain
- ❌ Still no CSS control if iframed

---

## Recommendation

**Start with Option 1 (GitHub Pages + Direct Link)** for the following reasons:

1. **Immediate solution** - Can be implemented in minutes
2. **Zero maintenance** - Automatically stays up to date
3. **Simple and reliable** - No complex dependencies
4. **Professional appearance** - Clean external link experience
5. **Easy to upgrade** - Can switch to other options later

## Implementation Status

- [ ] **Current Implementation**: Using Option 1 (GitHub Pages + Direct Link)
- [ ] Enable GitHub Pages on ProjectileMotionSimulator repository
- [ ] Update portfolio project link to: `https://austinorphan.github.io/ProjectileMotionSimulator/`
- [ ] Test link functionality
- [ ] Consider future upgrade to Option 2 (iframe) or Option 3 (submodules) if deeper integration needed

## Future Considerations

- If theming/CSS control becomes important → Consider Option 3 (Git Submodules)
- If embedded experience is preferred → Consider Option 2 (Iframe Embed)
- If maximum automation is desired → Consider Option 4 (GitHub Actions)

---

*Last Updated: July 2025*
*Related PR: [Link to PR when created]*