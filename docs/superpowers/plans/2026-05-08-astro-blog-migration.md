# Astro Blog Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the existing vanilla HTML/CSS/JS portfolio to Astro and add a blog with RSS, tags, and reading time — all at `austinorphan.com` on GitHub Pages.

**Architecture:** Full static Astro build (`output: 'static'`). Existing HTML components become `.astro` components rendered at build time — eliminating the fetch-based component loader and its CORS limitation. Blog posts are markdown files in `src/content/blog/` using Astro content collections. GitHub Actions builds and deploys `dist/` on every push to `master`.

**Tech Stack:** Astro (static), `@astrojs/rss`, TypeScript (Zod schemas), GitHub Actions (`actions/deploy-pages`)

---

## File Map

### Created
| File | Responsibility |
|---|---|
| `package.json` | Astro scripts, dependencies |
| `astro.config.mjs` | Site URL, static output config |
| `tsconfig.json` | TypeScript config (extends astro/strict) |
| `src/styles/global.css` | Transplant of `styles/main.css` verbatim |
| `src/layouts/BaseLayout.astro` | `<head>`, fonts, icons CDN, SW registration |
| `src/layouts/BlogPost.astro` | Wraps BaseLayout, adds OG meta for blog posts |
| `src/components/About.astro` | About section HTML + content |
| `src/components/Projects.astro` | Projects section HTML + content |
| `src/components/Contact.astro` | Contact section HTML + form validation JS |
| `src/components/Footer.astro` | Footer HTML + parallax/back-to-top JS |
| `src/components/KonamiEgg.astro` | Konami code easter egg (pixel-mode toggle) |
| `src/components/ParticleSystem.astro` | Particle canvas system |
| `src/pages/index.astro` | Portfolio home: hero + components + scroll/nav JS |
| `src/content/config.ts` | Blog collection Zod schema |
| `src/utils/reading-time.ts` | Word-count-based reading time helper |
| `src/pages/blog/index.astro` | Blog post list with tag filter bar |
| `src/pages/blog/[slug].astro` | Individual post page |
| `src/pages/blog/tags/[tag].astro` | Posts filtered by tag |
| `src/pages/rss.xml.ts` | RSS feed endpoint |
| `src/content/blog/hello-world.md` | Sample post to verify the blog works |
| `public/CNAME` | Custom domain (moved from root) |
| `public/sw.js` | Service worker (moved from root, cache version bumped) |
| `public/AustinOrphanResume.pdf` | Resume (moved from root) |
| `public/` | All favicon files, `site.webmanifest`, `browserconfig.xml` (moved from root) |
| `.github/workflows/deploy.yml` | CI/CD: build + deploy to GitHub Pages |

### Deleted (after migration verified)
- `index.html`
- `js/component-loader.js` (and `js/` directory)
- `styles/main.css` (and `styles/` directory)
- `components/about.html`, `components/projects.html`, `components/contact.html`, `components/footer.html` (and `components/` directory)
- `sw.js` (root — moved to `public/`)
- `CNAME` (root — moved to `public/`)
- All favicon files at root (moved to `public/`)

---

## Task 1: Scaffold Astro

**Files:**
- Create: `package.json`
- Create: `astro.config.mjs`
- Create: `tsconfig.json`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "austinorphan-portfolio",
  "type": "module",
  "version": "1.0.0",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "check": "astro check"
  }
}
```

- [ ] **Step 2: Add `node_modules/` and `.astro/` to `.gitignore`**

Append to the existing `.gitignore` (it already has `.superpowers/` from a previous commit):

```bash
echo "node_modules/" >> .gitignore
echo ".astro/" >> .gitignore
```

- [ ] **Step 3: Install Astro and RSS package**

```bash
npm install astro @astrojs/rss
```

Expected: `node_modules/` created, `package-lock.json` created, no errors.

- [ ] **Step 3: Create `astro.config.mjs`**

```js
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://austinorphan.com',
  output: 'static',
});
```

- [ ] **Step 4: Create `tsconfig.json`**

```json
{
  "extends": "astro/tsconfigs/strict"
}
```

- [ ] **Step 5: Create a minimal `src/pages/index.astro` to verify the dev server starts**

```astro
---
---
<html><body><h1>test</h1></body></html>
```

- [ ] **Step 6: Run dev server to verify it starts**

```bash
npm run dev
```

Expected output includes: `astro  v[version] ready` and `Local: http://localhost:4321/`. Visit `http://localhost:4321` in browser — should show "test". Stop the server with Ctrl+C.

- [ ] **Step 7: Commit**

```bash
git add package.json package-lock.json astro.config.mjs tsconfig.json src/pages/index.astro
git commit -m "chore: scaffold Astro project"
```

---

## Task 2: Global CSS

**Files:**
- Create: `src/styles/global.css`

- [ ] **Step 1: Copy `styles/main.css` to `src/styles/global.css` verbatim**

```bash
mkdir -p src/styles
cp styles/main.css src/styles/global.css
```

- [ ] **Step 2: Verify the copy**

```bash
diff styles/main.css src/styles/global.css
```

Expected: no output (files are identical).

- [ ] **Step 3: Commit**

```bash
git add src/styles/global.css
git commit -m "chore: transplant main.css to src/styles/global.css"
```

---

## Task 3: BaseLayout

**Files:**
- Create: `src/layouts/BaseLayout.astro`

`BaseLayout.astro` owns the `<head>`, all global imports, and the service worker registration. Every page in the site uses this layout.

- [ ] **Step 1: Create `src/layouts/BaseLayout.astro`**

```astro
---
import '../styles/global.css';

interface Props {
  title?: string;
  description?: string;
}

const {
  title = 'Austin Orphan',
  description = 'Austin Orphan - Creative, Competitive, and Curious developer and designer.',
} = Astro.props;
---
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Anta&family=Comfortaa:wght@700&family=Source+Sans+Pro:wght@900&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&family=Pixelify+Sans:wght@400;700&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/@phosphor-icons/web@2.1.1" defer></script>

  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="mask-icon" href="/safari-pinned-tab.svg" color="#6ee5e3">
  <meta name="msapplication-TileColor" content="#00aba9">
  <meta name="theme-color" content="#000000">

  <meta name="description" content={description}>
  <meta name="author" content="Austin Orphan">
  <meta name="robots" content="index,follow">

  <meta property="og:url" content="https://austinorphan.com/">
  <meta property="og:type" content="website">
  <meta property="og:title" content={title}>
  <meta property="og:description" content={description}>
  <meta property="og:image" content="https://austinorphan.com/apple-touch-icon.png">
  <meta property="og:site_name" content="Austin Orphan Portfolio">

  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content={title}>
  <meta name="twitter:description" content={description}>
  <meta name="twitter:image" content="https://austinorphan.com/apple-touch-icon.png">

  <link rel="canonical" href="https://austinorphan.com/">

  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "Austin Orphan",
    "url": "https://austinorphan.com",
    "sameAs": [
      "https://github.com/austinorphan",
      "https://www.linkedin.com/in/austinorphan/"
    ],
    "jobTitle": "Developer & Designer",
    "description": "Creative, Competitive, and Curious developer and designer.",
    "email": "AustinGOrphan@gmail.com",
    "knowsAbout": ["Web Development", "JavaScript", "Python", "UI/UX Design", "React", "Node.js"],
    "mainEntityOfPage": {
      "@type": "WebSite",
      "@id": "https://austinorphan.com"
    }
  }
  </script>

  <script>
    const GA_ID = 'YOUR_GA_ID';
  </script>
  <script async src="https://www.googletagmanager.com/gtag/js?id=YOUR_GA_ID"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'YOUR_GA_ID', {
      page_title: document.title,
      page_location: window.location.href
    });
  </script>

  <slot name="head" />
</head>
<body>
  <slot />

  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
      });
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: Update `src/pages/index.astro` to use the layout and verify it compiles**

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
---
<BaseLayout>
  <h1>test</h1>
</BaseLayout>
```

- [ ] **Step 3: Run build to verify it compiles**

```bash
npm run build
```

Expected: build completes with no errors. `dist/index.html` exists.

- [ ] **Step 4: Commit**

```bash
git add src/layouts/BaseLayout.astro src/pages/index.astro
git commit -m "feat: add BaseLayout with head, fonts, icons, and SW registration"
```

---

## Task 4: Konami Egg and Particle System

**Files:**
- Create: `src/components/KonamiEgg.astro`
- Create: `src/components/ParticleSystem.astro`

These are self-contained components with client-side `<script>` tags. They are included in `index.astro` (portfolio home only).

- [ ] **Step 1: Create `src/components/KonamiEgg.astro`**

```astro
---
---
<script>
  (function() {
    const konamiCode = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a'];
    let konamiIndex = 0;

    document.addEventListener('keydown', function(e) {
      if (e.key === konamiCode[konamiIndex]) {
        konamiIndex++;
        if (konamiIndex === konamiCode.length) {
          activatePixelMode();
          konamiIndex = 0;
        }
      } else {
        konamiIndex = 0;
      }
    });

    function activatePixelMode() {
      const isPixelMode = document.body.classList.contains('pixel-mode');
      document.body.classList.toggle('pixel-mode');

      const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSpy0Ey9diMFl2+z5cp2Jhgse8DvpnAfBTF6w+zcrWoiC0ix1Out8embMwsYbNDzn5NW+8XN0eWQXAmjebrq13hDjPvl8N/AghgKGHzN8cuiRBQMVGLp5cd/zOfs9eS2XwgBa3bBAAAtAAAAAAAAAAAA');
      audio.play().catch(() => {});

      const existing = document.querySelector('.pixel-notification');
      if (existing) existing.remove();

      const notification = document.createElement('div');
      notification.className = 'pixel-notification';
      notification.textContent = isPixelMode ? '8-BIT MODE DEACTIVATED!' : '8-BIT MODE ACTIVATED!';
      document.body.appendChild(notification);
      setTimeout(() => notification.remove(), 3000);
    }
  })();
</script>
```

- [ ] **Step 2: Create `src/components/ParticleSystem.astro`**

```astro
---
---
<canvas id="particle-canvas" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 999;"></canvas>

<script>
  (function() {
    const canvas = document.getElementById('particle-canvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    let particleMode = 'off';
    let particlesEnabled = false;
    let mouseX = 0;
    let mouseY = 0;

    function resizeCanvas() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    class Particle {
      constructor(x, y, options = {}) {
        this.x = x;
        this.y = y;
        this.vx = options.vx || (Math.random() - 0.5) * 4;
        this.vy = options.vy || (Math.random() - 0.5) * 4;
        this.radius = options.radius || Math.random() * 3 + 1;
        this.color = options.color || `hsl(${Math.random() * 360}, 100%, 50%)`;
        this.life = options.life || 1;
        this.decay = options.decay || 0.01;
        this.gravity = options.gravity || 0;
        this.bounce = options.bounce || 0;
      }
      update() {
        this.x += this.vx;
        this.y += this.vy;
        this.vy += this.gravity;
        this.life = Math.max(0, Math.min(1, this.life - this.decay));
        if (this.bounce > 0) {
          if (this.x <= this.radius || this.x >= canvas.width - this.radius) this.vx *= -this.bounce;
          if (this.y >= canvas.height - this.radius) { this.vy *= -this.bounce; this.y = canvas.height - this.radius; }
        }
      }
      draw() {
        if (this.life <= 0) return;
        ctx.save();
        ctx.globalAlpha = this.life;
        const is8Bit = document.body.classList.contains('pixel-mode');
        if (is8Bit) {
          ctx.fillStyle = this.color;
          const ps = Math.round(this.radius * 2);
          ctx.fillRect(Math.round(this.x - ps/2), Math.round(this.y - ps/2), ps, ps);
        } else {
          ctx.fillStyle = this.color;
          ctx.beginPath();
          ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }
    }

    function get8BitColor() {
      return ['#00ff00','#00ffff','#ff00ff','#ffff00','#ff0000','#0080ff','#ff8000'][Math.floor(Math.random()*7)];
    }

    function createBurst(x, y, count = 30, options = {}) {
      if (!particlesEnabled) return;
      for (let i = 0; i < count; i++) {
        const angle = (Math.PI * 2 * i) / count;
        const speed = Math.random() * 5 + 2;
        particles.push(new Particle(x, y, { vx: Math.cos(angle)*speed, vy: Math.sin(angle)*speed, ...options }));
      }
    }

    function createFirework(x, y) {
      if (!particlesEnabled) return;
      const is8Bit = document.body.classList.contains('pixel-mode');
      const color = is8Bit ? get8BitColor() : `hsl(${Math.random()*360}, 100%, 50%)`;
      createBurst(x, y, is8Bit ? 30 : 50, { color, decay: 0.02, gravity: is8Bit ? 0.15 : 0.1, radius: is8Bit ? 2 : null });
    }

    function createConfetti() {
      if (!particlesEnabled) return;
      const is8Bit = document.body.classList.contains('pixel-mode');
      for (let i = 0; i < (is8Bit ? 50 : 100); i++) {
        particles.push(new Particle(Math.random()*canvas.width, -10, {
          vx: (Math.random()-0.5)*2, vy: Math.random()*3+1,
          color: is8Bit ? get8BitColor() : `hsl(${Math.random()*360},100%,50%)`,
          radius: is8Bit ? 3 : Math.random()*4+2, decay: 0.001, gravity: 0.05, bounce: 0.8
        }));
      }
    }

    function createMouseTrail() {
      if (!particlesEnabled || particleMode !== 'trail') return;
      const is8Bit = document.body.classList.contains('pixel-mode');
      particles.push(new Particle(mouseX, mouseY, {
        vx: (Math.random()-0.5)*2, vy: (Math.random()-0.5)*2,
        radius: is8Bit ? 2 : Math.random()*2+1,
        color: is8Bit ? get8BitColor() : `hsl(${Date.now()*0.1%360},100%,50%)`,
        decay: 0.02
      }));
    }

    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles = particles.filter(p => { p.update(); p.draw(); return p.life > 0; });
      createMouseTrail();
      requestAnimationFrame(animate);
    }
    animate();

    document.addEventListener('mousemove', e => { mouseX = e.clientX; mouseY = e.clientY; });

    function showNotification(message, subtitle = '') {
      const n = document.createElement('div');
      n.innerHTML = `<div style="font-size:18px;margin-bottom:${subtitle?'8px':'0'};font-weight:bold">${message}</div>${subtitle?`<div style="font-size:14px;opacity:.9">${subtitle}</div>`:''}`;
      n.style.cssText = `position:fixed;top:-100px;right:20px;width:300px;background:rgba(0,0,0,.95);color:white;padding:16px 20px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,.3);z-index:10000;border-left:4px solid var(--color-accent);animation:dropdownSlide 4s ease-in-out forwards;backdrop-filter:blur(10px)`;
      document.body.appendChild(n);
      setTimeout(() => n.remove(), 4000);
    }

    const style = document.createElement('style');
    style.textContent = `@keyframes dropdownSlide{0%{top:-100px;opacity:0;transform:translateY(-20px)}15%{top:20px;opacity:1;transform:translateY(0)}85%{top:20px;opacity:1;transform:translateY(0)}100%{top:-100px;opacity:0;transform:translateY(-20px)}}`;
    document.head.appendChild(style);

    function createDisableButton() {
      const btn = document.createElement('button');
      btn.id = 'particle-disable-btn';
      btn.innerHTML = '✕ Disable Particles';
      btn.style.cssText = `position:fixed;top:20px;right:20px;background:rgba(0,0,0,.8);color:white;border:2px solid var(--color-accent);padding:10px 15px;border-radius:8px;font-size:14px;cursor:pointer;z-index:10001;transition:all .3s ease;font-family:inherit`;
      btn.addEventListener('mouseover', () => { btn.style.background = 'var(--color-accent)'; btn.style.color = 'var(--color-background)'; });
      btn.addEventListener('mouseout', () => { btn.style.background = 'rgba(0,0,0,.8)'; btn.style.color = 'white'; });
      btn.addEventListener('click', () => { particlesEnabled=false; particles=[]; particleMode='off'; btn.remove(); showNotification('❌ Particle System Disabled'); });
      document.body.appendChild(btn);
    }

    let keySequence = [];
    document.addEventListener('keydown', e => {
      keySequence.push(e.key.toLowerCase());
      if (keySequence.length > 5) keySequence.shift();
      const seq = keySequence.join('');
      if (!particlesEnabled && seq.endsWith('party')) {
        particlesEnabled = true; createDisableButton(); createConfetti();
        showNotification('🎉 Party Mode Activated!', 'Click the ✕ button to disable');
        keySequence = [];
      } else if (particlesEnabled) {
        if (seq.endsWith('fun')) { createConfetti(); }
        else if (seq.endsWith('trail')) { particleMode = particleMode==='trail'?'off':'trail'; showNotification(particleMode==='trail'?'✨ Mouse Trail On':'✨ Mouse Trail Off'); }
        else if (seq.endsWith('clear')) { particles=[]; particleMode='off'; showNotification('🧹 Particles Cleared'); }
      }
    });

    let nameClicks = 0;
    const nameEl = document.querySelector('h1');
    if (nameEl) {
      nameEl.style.cursor = 'pointer';
      nameEl.addEventListener('click', e => {
        if (!particlesEnabled) return;
        nameClicks++;
        if (nameClicks >= 3) { createFirework(e.clientX, e.clientY); }
        if (nameClicks >= 5) { createConfetti(); nameClicks = 0; }
      });
    }

    document.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', e => {
        if (!particlesEnabled) return;
        createBurst(e.clientX, e.clientY, 20, {
          color: getComputedStyle(document.documentElement).getPropertyValue('--color-accent'),
          decay: 0.03, radius: 2
        });
      });
    });
  })();
</script>
```

- [ ] **Step 3: Build to verify no errors**

```bash
npm run build
```

Expected: build completes with no errors.

- [ ] **Step 4: Commit**

```bash
git add src/components/KonamiEgg.astro src/components/ParticleSystem.astro
git commit -m "feat: add Konami code easter egg and particle system components"
```

---

## Task 5: Portfolio Components

**Files:**
- Create: `src/components/About.astro`
- Create: `src/components/Projects.astro`
- Create: `src/components/Contact.astro`
- Create: `src/components/Footer.astro`

Each component is the existing HTML wrapped in Astro frontmatter delimiters. The contact form JS and footer JS move into their respective components.

- [ ] **Step 1: Create `src/components/About.astro`**

```astro
---
---
<section id="about" class="about-section">
    <div class="section-container">
        <h2>About Me</h2>
        <div class="about-content">
            <div class="about-text">
                <div class="about-intro">
                    <p>I'm Austin Orphan, a passionate software developer who embodies the philosophy of being <strong>Creative</strong>, <strong>Competitive</strong>, and <strong>Curious</strong>. With a background in computer science and expertise in technologies like C#, .NET, and AWS, I love building solutions that make a real difference—whether that's crafting intuitive user interfaces or architecting scalable backend systems.</p>
                    <p>When I'm not coding, you might find me playing drums, guitar, or shooting hoops on the basketball court. I believe the best solutions come from diverse experiences and perspectives.</p>
                </div>
                <div class="about-details">
                    <div class="detail-section">
                        <h3><i class="ph-duotone ph-lightbulb"></i> Creative</h3>
                        <p>I approach every project with a creative mindset, finding innovative solutions to complex problems. Whether it's designing efficient workflows, building interactive applications, or optimizing existing systems, I strive to create something both functional and elegant.</p>
                    </div>
                    <div class="detail-section">
                        <h3><i class="ph-duotone ph-trophy"></i> Competitive</h3>
                        <p>I thrive in challenging environments and constantly push myself to improve. This competitive spirit drives me to write cleaner code, learn new technologies, and deliver solutions that exceed expectations. I believe healthy competition brings out the best in everyone.</p>
                    </div>
                    <div class="detail-section">
                        <h3><i class="ph-duotone ph-question"></i> Curious</h3>
                        <p>My curiosity is what led me from computer science into exploring management principles, from traditional databases to cloud architectures, and from solo projects to collaborative team environments. I'm always asking "what if?" and "how can we do this better?"</p>
                    </div>
                </div>
            </div>
            <div class="about-sidebar">
                <div class="skills-section">
                    <h3>Technical Skills</h3>
                    <div class="skills-grid">
                        <div class="skill-category">
                            <h4>Core Languages</h4>
                            <div class="skill-tags">
                                <span class="skill-tag">C#</span>
                                <span class="skill-tag">Python</span>
                                <span class="skill-tag">SQL</span>
                                <span class="skill-tag">JavaScript</span>
                                <span class="skill-tag">Java</span>
                                <span class="skill-tag">C++</span>
                            </div>
                        </div>
                        <div class="skill-category">
                            <h4>Frameworks & Technologies</h4>
                            <div class="skill-tags">
                                <span class="skill-tag">.NET</span>
                                <span class="skill-tag">ASP.NET</span>
                                <span class="skill-tag">AWS</span>
                                <span class="skill-tag">SQL Server</span>
                                <span class="skill-tag">Snowflake</span>
                                <span class="skill-tag">MySQL</span>
                            </div>
                        </div>
                        <div class="skill-category">
                            <h4>Tools & Platforms</h4>
                            <div class="skill-tags">
                                <span class="skill-tag">Looker</span>
                                <span class="skill-tag">LookML</span>
                                <span class="skill-tag">AWS Athena</span>
                                <span class="skill-tag">Git</span>
                                <span class="skill-tag">HTML5</span>
                                <span class="skill-tag">CSS3</span>
                            </div>
                        </div>
                        <div class="skill-category">
                            <h4>Creative Skills</h4>
                            <div class="skill-tags">
                                <span class="skill-tag">CAD</span>
                                <span class="skill-tag">Photoshop</span>
                                <span class="skill-tag">Illustrator</span>
                                <span class="skill-tag">UI/UX Design</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="experience-section">
                    <h3>Professional Journey</h3>
                    <div class="experience-item">
                        <h4>Software Developer</h4>
                        <p class="experience-period">OSM Worldwide • Nov 2023 - Present</p>
                        <p class="experience-description">Building scalable .NET applications and diving deep into AWS cloud architecture. I love the fast-paced environment where I can quickly iterate on solutions based on real user feedback.</p>
                    </div>
                    <div class="experience-item">
                        <h4>Customer Excellence Engineer</h4>
                        <p class="experience-period">Integral Ad Science • 2020 - 2023</p>
                        <p class="experience-description">Became the go-to person for complex data challenges, working with everything from SQL optimization to mentoring team members. This role taught me how technology impacts real business outcomes.</p>
                    </div>
                    <div class="experience-item">
                        <h4>Continuous Learning</h4>
                        <p class="experience-period">Currently pursuing M.S. in Management</p>
                        <p class="experience-description">Bridging the gap between technical expertise and business strategy at University of Illinois, while building on my Computer Science foundation from Aurora University.</p>
                    </div>
                </div>
                <div class="download-section">
                    <a href="/AustinOrphanResume.pdf" download class="download-resume">
                        <i class="ph-duotone ph-download"></i>
                        Download Resume
                    </a>
                </div>
            </div>
        </div>
    </div>
</section>
```

- [ ] **Step 2: Create `src/components/Projects.astro`**

```astro
---
---
<section id="projects" class="projects-section">
    <div class="section-container">
        <h2>Projects</h2>
        <div class="projects-grid">
            <div class="project-card">
                <div class="project-header">
                    <h3>Running App MVP</h3>
                    <div class="project-links">
                        <a href="https://github.com/austinorphan/running-app-mvp" target="_blank" rel="noopener noreferrer" aria-label="View GitHub Repository"><i class="ph-duotone ph-github-logo"></i></a>
                    </div>
                </div>
                <div class="project-description"><p>A TypeScript-based running application MVP designed to track and analyze running performance with modern web technologies.</p></div>
                <div class="project-tech">
                    <span class="tech-tag">TypeScript</span><span class="tech-tag">Web Development</span><span class="tech-tag">Fitness Tracking</span><span class="tech-tag">MVP</span>
                </div>
            </div>
            <div class="project-card">
                <div class="project-header">
                    <h3>MazeBot</h3>
                    <div class="project-links">
                        <a href="https://github.com/austinorphan/MazeBot" target="_blank" rel="noopener noreferrer" aria-label="View GitHub Repository"><i class="ph-duotone ph-github-logo"></i></a>
                    </div>
                </div>
                <div class="project-description"><p>Maze navigating robot initially designed for my college robotics class. Implements pathfinding algorithms and sensor integration for autonomous navigation.</p></div>
                <div class="project-tech">
                    <span class="tech-tag">Python</span><span class="tech-tag">Robotics</span><span class="tech-tag">Pathfinding</span><span class="tech-tag">Algorithms</span>
                </div>
            </div>
            <div class="project-card">
                <div class="project-header">
                    <h3>Projectile Motion Simulator</h3>
                    <div class="project-links">
                        <a href="/ProjectileMotionSimulator/src/" target="_blank" rel="noopener noreferrer" aria-label="View Live Demo"><i class="ph-duotone ph-play-circle"></i></a>
                        <a href="https://github.com/austinorphan/ProjectileMotionSimulator" target="_blank" rel="noopener noreferrer" aria-label="View GitHub Repository"><i class="ph-duotone ph-github-logo"></i></a>
                    </div>
                </div>
                <div class="project-description"><p>Interactive physics simulation demonstrating projectile motion principles with real-time visualization and parameter controls for educational purposes.</p></div>
                <div class="project-tech">
                    <span class="tech-tag">JavaScript</span><span class="tech-tag">HTML5 Canvas</span><span class="tech-tag">Physics</span><span class="tech-tag">Education</span>
                </div>
            </div>
            <div class="project-card">
                <div class="project-header">
                    <h3>PyFun Games</h3>
                    <div class="project-links">
                        <a href="https://github.com/austinorphan/PyFun" target="_blank" rel="noopener noreferrer" aria-label="View GitHub Repository"><i class="ph-duotone ph-github-logo"></i></a>
                    </div>
                </div>
                <div class="project-description"><p>Simple collection of games built in Python showcasing fundamental programming concepts and game development principles through interactive entertainment.</p></div>
                <div class="project-tech">
                    <span class="tech-tag">Python</span><span class="tech-tag">Game Development</span><span class="tech-tag">Object-Oriented</span><span class="tech-tag">Interactive</span>
                </div>
            </div>
            <div class="project-card placeholder">
                <div class="project-header">
                    <h3>Explore More Projects</h3>
                    <div class="project-links">
                        <a href="https://github.com/austinorphan" target="_blank" rel="noopener noreferrer" aria-label="View GitHub Profile"><i class="ph-duotone ph-github-logo"></i></a>
                    </div>
                </div>
                <div class="project-description"><p>Check out my GitHub profile for additional projects, contributions, and experimental work. Always building something new!</p></div>
                <div class="project-tech">
                    <span class="tech-tag">C#</span><span class="tech-tag">.NET</span><span class="tech-tag">AWS</span><span class="tech-tag">Innovation</span>
                </div>
            </div>
        </div>
    </div>
</section>
```

- [ ] **Step 3: Create `src/components/Contact.astro`**

```astro
---
---
<section id="contact" class="contact-section">
    <div class="section-container">
        <h2>Get In Touch</h2>
        <div class="contact-content">
            <div class="contact-info">
                <div class="contact-intro">
                    <p>I'm always interested in new opportunities, collaborations, and interesting projects. Whether you have a question, want to discuss a project, or just want to say hello, I'd love to hear from you!</p>
                </div>
                <div class="contact-methods">
                    <div class="contact-method">
                        <i class="ph-duotone ph-envelope"></i>
                        <div><h3>Email</h3><a href="mailto:AustinGOrphan@gmail.com">AustinGOrphan@gmail.com</a></div>
                    </div>
                    <div class="contact-method">
                        <i class="ph-duotone ph-linkedin-logo"></i>
                        <div><h3>LinkedIn</h3><a href="https://www.linkedin.com/in/austinorphan/" target="_blank" rel="noopener noreferrer">linkedin.com/in/austinorphan</a></div>
                    </div>
                    <div class="contact-method">
                        <i class="ph-duotone ph-github-logo"></i>
                        <div><h3>GitHub</h3><a href="https://github.com/austinorphan" target="_blank" rel="noopener noreferrer">github.com/austinorphan</a></div>
                    </div>
                </div>
            </div>
            <div class="contact-form-container">
                <form class="contact-form" action="https://formspree.io/f/YOUR_FORM_ID" method="POST" novalidate>
                    <div class="form-group">
                        <label for="name">Name *</label>
                        <input type="text" id="name" name="name" required aria-describedby="name-error">
                        <span class="error-message" id="name-error" role="alert"></span>
                    </div>
                    <div class="form-group">
                        <label for="email">Email *</label>
                        <input type="email" id="email" name="email" required aria-describedby="email-error">
                        <span class="error-message" id="email-error" role="alert"></span>
                    </div>
                    <div class="form-group">
                        <label for="subject">Subject</label>
                        <input type="text" id="subject" name="subject">
                    </div>
                    <div class="form-group">
                        <label for="message">Message *</label>
                        <textarea id="message" name="message" rows="5" required aria-describedby="message-error" placeholder="Tell me about your project or just say hello!"></textarea>
                        <span class="error-message" id="message-error" role="alert"></span>
                    </div>
                    <button type="submit" class="submit-btn">
                        <i class="ph-duotone ph-paper-plane-tilt"></i>
                        Send Message
                    </button>
                </form>
                <div class="form-status" id="form-status" role="alert" aria-live="polite"></div>
            </div>
        </div>
    </div>
</section>

<script>
  (function() {
    const form = document.querySelector('.contact-form');
    const statusDiv = document.getElementById('form-status');
    if (!form) return;

    function validateName(v) { return v.trim().length >= 2; }
    function validateEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()); }
    function validateMessage(v) { return v.trim().length >= 10; }

    function showError(id, msg) {
      const err = document.getElementById(id + '-error');
      const field = document.getElementById(id);
      if (err) { err.textContent = msg; err.style.display = 'block'; }
      if (field) field.classList.add('error');
    }
    function clearError(id) {
      const err = document.getElementById(id + '-error');
      const field = document.getElementById(id);
      if (err) { err.textContent = ''; err.style.display = 'none'; }
      if (field) field.classList.remove('error');
    }
    function showStatus(msg, type) {
      statusDiv.textContent = msg;
      statusDiv.className = 'form-status ' + type;
      statusDiv.style.display = 'block';
      if (type === 'success') setTimeout(() => { statusDiv.style.display = 'none'; }, 5000);
    }

    document.getElementById('name')?.addEventListener('blur', function() {
      validateName(this.value) ? clearError('name') : showError('name', 'Name must be at least 2 characters long');
    });
    document.getElementById('email')?.addEventListener('blur', function() {
      validateEmail(this.value) ? clearError('email') : showError('email', 'Please enter a valid email address');
    });
    document.getElementById('message')?.addEventListener('blur', function() {
      validateMessage(this.value) ? clearError('message') : showError('message', 'Message must be at least 10 characters long');
    });

    form.addEventListener('submit', function(e) {
      e.preventDefault();
      statusDiv.style.display = 'none';
      const data = new FormData(form);
      const name = data.get('name');
      const email = data.get('email');
      const message = data.get('message');
      let valid = true;

      if (!validateName(name)) { showError('name', 'Name must be at least 2 characters long'); valid = false; } else clearError('name');
      if (!validateEmail(email)) { showError('email', 'Please enter a valid email address'); valid = false; } else clearError('email');
      if (!validateMessage(message)) { showError('message', 'Message must be at least 10 characters long'); valid = false; } else clearError('message');
      if (!valid) { showStatus('Please fix the errors above and try again.', 'error'); return; }

      const btn = form.querySelector('.submit-btn');
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="ph-duotone ph-spinner"></i> Sending...';
      btn.disabled = true;

      fetch(form.action, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
        .then(r => {
          if (r.ok) { form.reset(); showStatus("Thank you! Your message has been sent successfully. I'll get back to you soon!", 'success'); }
          else throw new Error();
        })
        .catch(() => showStatus('Sorry, there was an issue. Please email me directly at AustinGOrphan@gmail.com', 'error'))
        .finally(() => { btn.innerHTML = orig; btn.disabled = false; });
    });
  })();
</script>
```

- [ ] **Step 4: Create `src/components/Footer.astro`**

```astro
---
---
<footer class="site-footer">
    <div class="footer-top">
        <button class="back-to-top" aria-label="Back to top">
            <i class="ph-duotone ph-arrow-up"></i>
            <span>Top</span>
        </button>
    </div>
    <div class="footer-decoration">
        <div class="decoration-line-full"></div>
    </div>
    <div class="footer-content">
        <div class="footer-left">
            <p class="copyright">© 2024 Austin Orphan</p>
        </div>
        <div class="footer-center">
            <div class="footer-social">
                <a href="https://github.com/austinorphan" target="_blank" rel="noopener noreferrer" aria-label="GitHub" class="footer-social-link"><i class="ph-duotone ph-github-logo"></i></a>
                <a href="https://www.linkedin.com/in/austinorphan/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn" class="footer-social-link"><i class="ph-duotone ph-linkedin-logo"></i></a>
                <a href="mailto:AustinGOrphan@gmail.com" aria-label="Email" class="footer-social-link"><i class="ph-duotone ph-envelope-simple"></i></a>
            </div>
        </div>
        <div class="footer-right"></div>
    </div>
</footer>

<script>
  (function() {
    const backToTopBtn = document.querySelector('.back-to-top');
    if (backToTopBtn) {
      backToTopBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    }

    const footer = document.querySelector('.site-footer');
    const contactSection = document.querySelector('#contact');
    if (footer && contactSection) {
      footer.style.transition = 'transform 0.1s ease-out, opacity 0.1s ease-out';
      footer.style.willChange = 'transform, opacity';
      let ticking = false;

      function updateFooterParallax() {
        const scrollPosition = window.pageYOffset + window.innerHeight;
        const contactBottom = contactSection.offsetTop + contactSection.offsetHeight;
        if (scrollPosition > contactBottom) {
          const progress = Math.min(1, (scrollPosition - contactBottom) / 120);
          footer.style.transform = `translateY(${(1 - progress) * 30}px)`;
          footer.style.opacity = progress;
          footer.style.zIndex = '10000';
        } else {
          footer.style.transform = 'translateY(50px)';
          footer.style.opacity = '0';
          footer.style.zIndex = '-1';
        }
        ticking = false;
      }

      window.addEventListener('scroll', () => {
        if (!ticking) { requestAnimationFrame(updateFooterParallax); ticking = true; }
      }, { passive: true });
      updateFooterParallax();
    }
  })();
</script>
```

- [ ] **Step 5: Build to verify all four components compile**

```bash
npm run build
```

Expected: build completes with no errors.

- [ ] **Step 6: Commit**

```bash
git add src/components/
git commit -m "feat: add About, Projects, Contact, Footer Astro components"
```

---

## Task 6: Portfolio Home Page

**Files:**
- Modify: `src/pages/index.astro`

Replaces the temporary test page. Composes all portfolio components, includes the hero section and all inline JS from `index.html` (scroll animations, section nav).

- [ ] **Step 1: Replace `src/pages/index.astro` with the full portfolio page**

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import About from '../components/About.astro';
import Projects from '../components/Projects.astro';
import Contact from '../components/Contact.astro';
import Footer from '../components/Footer.astro';
import KonamiEgg from '../components/KonamiEgg.astro';
import ParticleSystem from '../components/ParticleSystem.astro';
---
<BaseLayout>
  <!-- Hero Section -->
  <section id="hero" class="hero-section">
    <div class="page-wrapper">
      <div class="content-wrapper">
        <h1>Austin Orphan</h1>
        <p id="cbar">
          Creative <span class="divider"> | </span>Competitive <span class="divider"> | </span> Curious
        </p>
        <div id="linkBar">
          <a href="https://github.com/austinorphan" target="_blank" rel="noopener noreferrer" aria-label="GitHub Profile">
            <i class="icon ph-duotone ph-github-logo"></i>
          </a>
          <a href="https://www.linkedin.com/in/austinorphan/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn Profile">
            <i class="icon ph-duotone ph-linkedin-logo"></i>
          </a>
          <a href="/AustinOrphanResume.pdf" download aria-label="Download Resume">
            <i class="icon ph-duotone ph-read-cv-logo"></i>
          </a>
          <a href="mailto:AustinGOrphan@gmail.com" aria-label="Email Contact">
            <i class="icon ph-duotone ph-envelope-simple"></i>
          </a>
          <a href="#projects" aria-label="View Projects">
            <i class="icon ph-duotone ph-meteor"></i>
          </a>
        </div>
      </div>
      <div class="scroll-indicator">
        <a href="#about" aria-label="Scroll to About">
          <i class="ph-duotone ph-arrow-down"></i>
        </a>
      </div>
    </div>
  </section>

  <About />
  <Projects />
  <Contact />
  <Footer />

  <!-- Navigation -->
  <nav class="section-nav">
    <a href="#hero" aria-label="Go to Hero Section"><i class="ph-duotone ph-house"></i></a>
    <a href="#about" aria-label="Go to About Section"><i class="ph-duotone ph-user"></i></a>
    <a href="#projects" aria-label="Go to Projects Section"><i class="ph-duotone ph-folder-open"></i></a>
    <a href="#contact" aria-label="Go to Contact Section"><i class="ph-duotone ph-envelope"></i></a>
  </nav>

  <KonamiEgg />
  <ParticleSystem />

  <script>
    // Scroll animations and section nav — runs after page load
    (function() {
      const projectCards = document.querySelectorAll('.project-card');
      const aboutElements = document.querySelectorAll('.detail-section, .skill-category');
      const contactElements = document.querySelectorAll('.contact-method, .experience-item');

      projectCards.forEach((el, i) => { el.classList.add('scroll-reveal'); el.style.transitionDelay = `${i * 0.1}s`; });
      aboutElements.forEach((el, i) => { el.classList.add('scroll-reveal'); el.style.transitionDelay = `${i * 0.08}s`; });
      contactElements.forEach((el, i) => { el.classList.add('scroll-reveal'); el.style.transitionDelay = `${i * 0.08}s`; });

      let lastScrollY = window.pageYOffset;
      let scrollSpeed = 0;
      let speedTimeout;

      function calcScrollSpeed() {
        const cur = window.pageYOffset;
        scrollSpeed = Math.abs(cur - lastScrollY);
        lastScrollY = cur;
        clearTimeout(speedTimeout);
        speedTimeout = setTimeout(() => { scrollSpeed = 0; }, 150);
      }

      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            if (scrollSpeed > 30) entry.target.classList.add('fast-reveal');
            requestAnimationFrame(() => entry.target.classList.add('revealed'));
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

      [...projectCards, ...aboutElements, ...contactElements].forEach(el => observer.observe(el));

      const DESKTOP_MQ = window.matchMedia('(min-width: 600px)');
      let isDesktop = DESKTOP_MQ.matches;
      DESKTOP_MQ.addEventListener('change', e => { isDesktop = e.matches; });

      const heroContent = document.querySelector('.content-wrapper');
      const linkBar = document.querySelector('#linkBar');

      let ticking = false;
      function updateOnScroll() {
        const scrolled = window.pageYOffset;
        const heroHeight = window.innerHeight;
        calcScrollSpeed();
        if (scrolled < heroHeight) {
          if (heroContent && isDesktop) heroContent.style.transform = `translateY(${scrolled * 0.25}px)`;
          if (linkBar) {
            if (isDesktop) {
              linkBar.style.transform = `translateY(${scrolled * 0.1}px)`;
            } else {
              linkBar.style.opacity = Math.max(0, 1 - scrolled / heroHeight);
            }
          }
        } else {
          if (heroContent && isDesktop) heroContent.style.transform = '';
          if (linkBar) {
            if (isDesktop) linkBar.style.transform = '';
            else linkBar.style.opacity = '0';
          }
        }
        ticking = false;
      }
      window.addEventListener('scroll', () => {
        if (!ticking) { requestAnimationFrame(updateOnScroll); ticking = true; }
      }, { passive: true });

      setTimeout(() => {
        const h1 = document.querySelector('h1');
        const cbar = document.querySelector('#cbar');
        if (h1) h1.style.animation = 'slideInScale 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards';
        if (cbar) cbar.style.animation = 'slideInScale 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94) 0.2s forwards';
        if (linkBar) {
          linkBar.style.animation = isDesktop
            ? 'slideInScale 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94) 0.4s forwards'
            : 'fadeInOnly 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94) 0.4s forwards';
        }
      }, 300);

      // Random red flash on project buttons
      const projectButtons = document.querySelectorAll('.project-links a');
      function triggerRandomFlash() {
        const num = Math.floor(Math.random() * 3) + 1;
        const shuffled = Array.from(projectButtons).sort(() => Math.random() - 0.5);
        for (let i = 0; i < num && i < shuffled.length; i++) {
          const delay = i * 0.5 + Math.random() * 2;
          const btn = shuffled[i];
          setTimeout(() => {
            btn.classList.add('flashing');
            setTimeout(() => btn.classList.remove('flashing'), 2000);
          }, delay * 1000);
        }
        setTimeout(triggerRandomFlash, 5000 + Math.random() * 10000);
      }
      setTimeout(triggerRandomFlash, 3000);

      // Section nav active state
      const sections = document.querySelectorAll('section[id]');
      const navLinks = document.querySelectorAll('.section-nav a');
      const sectionNav = document.querySelector('.section-nav');
      let scrollTimeout;

      function updateActiveSection() {
        const pos = window.scrollY + window.innerHeight / 2;
        sections.forEach((section, i) => {
          if (pos >= section.offsetTop && pos < section.offsetTop + section.offsetHeight) {
            navLinks.forEach(l => l.classList.remove('active'));
            navLinks[i]?.classList.add('active');
          }
        });
      }

      window.addEventListener('scroll', () => {
        sectionNav?.classList.add('show-on-scroll');
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => sectionNav?.classList.remove('show-on-scroll'), 3000);
        updateActiveSection();
      });

      document.addEventListener('mousemove', e => {
        if (window.innerWidth - e.clientX <= 80) {
          sectionNav?.classList.add('show-on-scroll');
        } else if (!sectionNav?.matches(':hover')) {
          sectionNav?.classList.remove('show-on-scroll');
        }
      });

      navLinks.forEach(link => link.addEventListener('click', () => setTimeout(updateActiveSection, 100)));
      updateActiveSection();
    })();
  </script>
</BaseLayout>
```

- [ ] **Step 2: Build and verify the portfolio compiles**

```bash
npm run build
```

Expected: build completes with no errors. Check `dist/index.html` exists and contains the hero section HTML.

- [ ] **Step 3: Move public assets so the dev server can serve them (needed before dev test)**

```bash
mkdir -p public
cp AustinOrphanResume.pdf public/
cp apple-touch-icon.png android-chrome-192x192.png android-chrome-512x512.png favicon-16x16.png favicon-32x32.png favicon.ico favicon.png favicon.svg mstile-70x70.png mstile-144x144.png mstile-150x150.png mstile-310x150.png mstile-310x310.png safari-pinned-tab.svg site.webmanifest browserconfig.xml public/
cp CNAME public/
```

- [ ] **Step 4: Run dev server and verify the portfolio looks correct in browser**

```bash
npm run dev
```

Visit `http://localhost:4321`. Verify:
- Hero section renders with name, tagline, icon links
- Scrolling loads About, Projects, Contact sections
- Footer appears at bottom
- Section nav appears on scroll
- Phosphor icons are visible

Stop the server.

- [ ] **Step 5: Commit**

```bash
git add src/pages/index.astro public/
git commit -m "feat: add portfolio home page with hero, components, and scroll animations"
```

---

## Task 7: Blog Content Schema and Reading Time Utility

**Files:**
- Create: `src/content/config.ts`
- Create: `src/utils/reading-time.ts`
- Create: `src/content/blog/hello-world.md` (sample post for testing)

- [ ] **Step 1: Create `src/content/config.ts`**

```ts
import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
```

- [ ] **Step 2: Create `src/utils/reading-time.ts`**

```ts
export function getReadingTime(content: string): string {
  const words = content.trim().split(/\s+/).length;
  const minutes = Math.ceil(words / 200);
  return `${minutes} min read`;
}
```

- [ ] **Step 3: Create `src/content/blog/hello-world.md`**

```markdown
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
```

- [ ] **Step 4: Run Astro type check to verify the schema is valid**

```bash
npm run check
```

Expected: no type errors. If you see "Cannot find module 'astro:content'" errors, that's resolved by the next build step.

- [ ] **Step 5: Build to verify content collection is recognized**

```bash
npm run build
```

Expected: build completes with no errors.

- [ ] **Step 6: Commit**

```bash
git add src/content/ src/utils/
git commit -m "feat: add blog content collection schema and reading time utility"
```

---

## Task 8: Blog Post Layout

**Files:**
- Create: `src/layouts/BlogPost.astro`

- [ ] **Step 1: Create `src/layouts/BlogPost.astro`**

```astro
---
import BaseLayout from './BaseLayout.astro';
import { getReadingTime } from '../utils/reading-time';

interface Props {
  title: string;
  description: string;
  pubDate: Date;
  tags: string[];
  rawContent: string;
}

const { title, description, pubDate, tags, rawContent } = Astro.props;
const readingTime = getReadingTime(rawContent);
const formattedDate = pubDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
---
<BaseLayout title={`${title} — Austin Orphan`} description={description}>
  <Fragment slot="head">
    <meta property="og:type" content="article" />
    <meta property="og:title" content={title} />
    <meta property="og:description" content={description} />
    <meta property="article:published_time" content={pubDate.toISOString()} />
  </Fragment>

  <article class="blog-post">
    <div class="blog-post-header">
      <a href="/blog" class="back-link">← back to blog</a>
      <h1 class="blog-post-title">{title}</h1>
      <div class="blog-post-meta">
        <time datetime={pubDate.toISOString()}>{formattedDate}</time>
        <span class="meta-separator">·</span>
        <span class="reading-time">{readingTime}</span>
      </div>
      {tags.length > 0 && (
        <div class="blog-post-tags">
          {tags.map(tag => (
            <a href={`/blog/tags/${tag}`} class="tag-badge">{tag}</a>
          ))}
        </div>
      )}
    </div>

    <div class="blog-post-body">
      <slot />
    </div>
  </article>
</BaseLayout>
```

- [ ] **Step 2: Add blog post styles to `src/styles/global.css`**

Append the following to the end of `src/styles/global.css`:

```css
/* ============================================
   12. Blog Styles
   ============================================ */

.blog-post {
  max-width: 720px;
  margin: 0 auto;
  padding: 4rem 2rem;
}

.blog-post-header {
  margin-bottom: 3rem;
  border-bottom: 1px solid rgba(238, 229, 233, 0.15);
  padding-bottom: 2rem;
}

.back-link {
  display: inline-block;
  color: var(--color-accent);
  text-decoration: none;
  font-size: 0.85rem;
  margin-bottom: 1.5rem;
  transition: opacity 0.2s;
}
.back-link:hover { opacity: 0.75; }

.blog-post-title {
  font-family: 'Anta', sans-serif;
  color: var(--color-primary);
  font-size: clamp(1.4rem, 4vw, 2rem);
  line-height: 1.3;
  margin: 0 0 0.75rem;
  letter-spacing: 0.05em;
}

.blog-post-meta {
  color: #aaa;
  font-size: 0.8rem;
  margin-bottom: 0.75rem;
}
.blog-post-meta .reading-time { color: var(--color-accent); }
.meta-separator { margin: 0 0.4rem; }

.blog-post-tags {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.tag-badge {
  border: 1px solid var(--color-secondary);
  color: var(--color-secondary);
  padding: 0.1rem 0.5rem;
  border-radius: 3px;
  font-size: 0.72rem;
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
}
.tag-badge:hover {
  background: var(--color-secondary);
  color: var(--color-background);
}

.blog-post-body {
  color: var(--color-primary);
  font-family: 'Comfortaa', sans-serif;
  font-size: 1rem;
  line-height: 1.8;
}
.blog-post-body h2,
.blog-post-body h3 {
  font-family: 'Anta', sans-serif;
  color: var(--color-accent);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 2rem 0 0.75rem;
}
.blog-post-body a { color: var(--color-accent); }
.blog-post-body code {
  background: #0d1b24;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-size: 0.88em;
}
.blog-post-body pre {
  background: #0d1b24;
  border-left: 3px solid var(--color-accent);
  padding: 1rem 1.25rem;
  border-radius: 4px;
  overflow-x: auto;
  margin: 1.5rem 0;
}
.blog-post-body pre code {
  background: none;
  padding: 0;
}

/* Blog list page */
.blog-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 4rem 2rem;
}

.blog-page-title {
  font-family: 'Anta', sans-serif;
  color: var(--color-primary);
  font-size: 1.8rem;
  letter-spacing: 0.1em;
  margin: 0 0 0.25rem;
  border-bottom: 2px solid var(--color-accent);
  padding-bottom: 0.75rem;
}

.blog-page-subtitle {
  color: var(--color-accent);
  font-size: 0.82rem;
  margin-bottom: 2rem;
}

/* Tag filter bar */
.tag-filter {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 2rem;
}

.tag-filter-link {
  border: 1px solid var(--color-accent);
  color: var(--color-accent);
  padding: 0.2rem 0.6rem;
  border-radius: 3px;
  font-size: 0.75rem;
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
}
.tag-filter-link:hover,
.tag-filter-link.active {
  background: var(--color-accent);
  color: var(--color-background);
}

/* Post card */
.post-card {
  border: 1px solid rgba(40, 146, 215, 0.3);
  border-radius: 4px;
  padding: 1.25rem;
  margin-bottom: 1rem;
  text-decoration: none;
  display: block;
  transition: border-color 0.2s;
}
.post-card:hover { border-color: var(--color-accent); }

.post-card-title {
  font-family: 'Anta', sans-serif;
  color: var(--color-primary);
  font-size: 1rem;
  margin: 0 0 0.35rem;
}

.post-card-meta {
  color: #aaa;
  font-size: 0.75rem;
  margin-bottom: 0.5rem;
}
.post-card-meta .reading-time { color: var(--color-accent); }

.post-card-description {
  color: #ccc;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
  line-height: 1.6;
}

.post-card-tags {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.rss-link {
  display: block;
  text-align: center;
  margin-top: 2rem;
  color: var(--color-accent);
  font-size: 0.8rem;
  text-decoration: none;
}
.rss-link:hover { text-decoration: underline; }
```

- [ ] **Step 3: Build to verify no errors**

```bash
npm run build
```

Expected: build completes with no errors.

- [ ] **Step 4: Commit**

```bash
git add src/layouts/BlogPost.astro src/styles/global.css
git commit -m "feat: add BlogPost layout and blog CSS"
```

---

## Task 9: Blog List Page

**Files:**
- Create: `src/pages/blog/index.astro`

- [ ] **Step 1: Create `src/pages/blog/index.astro`**

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';
import { getReadingTime } from '../../utils/reading-time';

const allPosts = await getCollection('blog', ({ data }) => {
  return import.meta.env.PROD ? !data.draft : true;
});

const posts = allPosts.sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());

const allTags = [...new Set(posts.flatMap(p => p.data.tags))].sort();
---
<BaseLayout title="Blog — Austin Orphan" description="Thoughts, projects, and technical notes from Austin Orphan.">
  <div class="blog-page">
    <h1 class="blog-page-title">BLOG</h1>
    <p class="blog-page-subtitle">thoughts, projects, and technical notes</p>

    <nav class="tag-filter" aria-label="Filter by tag">
      <a href="/blog" class="tag-filter-link active">all</a>
      {allTags.map(tag => (
        <a href={`/blog/tags/${tag}`} class="tag-filter-link">{tag}</a>
      ))}
    </nav>

    {posts.map(post => (
      <a href={`/blog/${post.slug}`} class="post-card">
        <h2 class="post-card-title">{post.data.title}</h2>
        <div class="post-card-meta">
          <time datetime={post.data.pubDate.toISOString()}>
            {post.data.pubDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </time>
          <span class="meta-separator">·</span>
          <span class="reading-time">{getReadingTime(post.body)}</span>
        </div>
        <p class="post-card-description">{post.data.description}</p>
        {post.data.tags.length > 0 && (
          <div class="post-card-tags">
            {post.data.tags.map(tag => (
              <span class="tag-badge">{tag}</span>
            ))}
          </div>
        )}
      </a>
    ))}

    <a href="/rss.xml" class="rss-link">↗ RSS feed</a>
  </div>
</BaseLayout>
```

- [ ] **Step 2: Build and verify the blog list page generates**

```bash
npm run build
```

Expected: `dist/blog/index.html` exists. No build errors.

- [ ] **Step 3: Run dev server and verify the blog list page in browser**

```bash
npm run dev
```

Visit `http://localhost:4321/blog`. Verify:
- "BLOG" heading appears
- The hello-world sample post is listed with its date and reading time
- Tags filter bar shows "all", "meta", "astro"
- Clicking a post card navigates to the post URL

Stop the server.

- [ ] **Step 4: Commit**

```bash
git add src/pages/blog/index.astro
git commit -m "feat: add blog post list page"
```

---

## Task 10: Individual Post Page

**Files:**
- Create: `src/pages/blog/[slug].astro`

- [ ] **Step 1: Create `src/pages/blog/[slug].astro`**

```astro
---
import BlogPost from '../../layouts/BlogPost.astro';
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const posts = await getCollection('blog', ({ data }) => {
    return import.meta.env.PROD ? !data.draft : true;
  });
  return posts.map(post => ({
    params: { slug: post.slug },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await post.render();
---
<BlogPost
  title={post.data.title}
  description={post.data.description}
  pubDate={post.data.pubDate}
  tags={post.data.tags}
  rawContent={post.body}
>
  <Content />
</BlogPost>
```

- [ ] **Step 2: Build and verify the post page generates**

```bash
npm run build
```

Expected: `dist/blog/hello-world/index.html` exists. No build errors.

- [ ] **Step 3: Run dev server and verify the post page renders**

```bash
npm run dev
```

Visit `http://localhost:4321/blog/hello-world`. Verify:
- Back link appears and returns to `/blog`
- Title, date, reading time, and tags display correctly
- Markdown body renders with proper styling (headings in Anta, body in Comfortaa)
- Code block in the sample post has the dark background + left accent border

Stop the server.

- [ ] **Step 4: Commit**

```bash
git add src/pages/blog/[slug].astro
git commit -m "feat: add individual blog post page"
```

---

## Task 11: Tag Pages

**Files:**
- Create: `src/pages/blog/tags/[tag].astro`

- [ ] **Step 1: Create `src/pages/blog/tags/[tag].astro`**

```astro
---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';
import { getReadingTime } from '../../../utils/reading-time';

export async function getStaticPaths() {
  const allPosts = await getCollection('blog', ({ data }) => !data.draft);
  const allTags = [...new Set(allPosts.flatMap(p => p.data.tags))];

  return allTags.map(tag => ({
    params: { tag },
    props: {
      posts: allPosts
        .filter(p => p.data.tags.includes(tag))
        .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()),
      allTags,
      tag,
    },
  }));
}

const { posts, allTags, tag } = Astro.props;
---
<BaseLayout
  title={`#${tag} — Austin Orphan Blog`}
  description={`Blog posts tagged "${tag}" by Austin Orphan.`}
>
  <div class="blog-page">
    <h1 class="blog-page-title">#{tag}</h1>
    <p class="blog-page-subtitle">{posts.length} post{posts.length !== 1 ? 's' : ''}</p>

    <nav class="tag-filter" aria-label="Filter by tag">
      <a href="/blog" class="tag-filter-link">all</a>
      {allTags.map(t => (
        <a href={`/blog/tags/${t}`} class={`tag-filter-link${t === tag ? ' active' : ''}`}>{t}</a>
      ))}
    </nav>

    {posts.map(post => (
      <a href={`/blog/${post.slug}`} class="post-card">
        <h2 class="post-card-title">{post.data.title}</h2>
        <div class="post-card-meta">
          <time datetime={post.data.pubDate.toISOString()}>
            {post.data.pubDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </time>
          <span class="meta-separator">·</span>
          <span class="reading-time">{getReadingTime(post.body)}</span>
        </div>
        <p class="post-card-description">{post.data.description}</p>
        {post.data.tags.length > 0 && (
          <div class="post-card-tags">
            {post.data.tags.map(t => (
              <span class="tag-badge">{t}</span>
            ))}
          </div>
        )}
      </a>
    ))}

    <a href="/blog" class="rss-link">← all posts</a>
  </div>
</BaseLayout>
```

- [ ] **Step 2: Build and verify tag pages generate**

```bash
npm run build
```

Expected: `dist/blog/tags/meta/index.html` and `dist/blog/tags/astro/index.html` exist. No build errors.

- [ ] **Step 3: Verify in browser**

```bash
npm run dev
```

Visit `http://localhost:4321/blog/tags/meta`. Verify:
- Heading shows `#meta`
- Post count is correct
- Tag filter bar highlights `meta` as active
- Posts list matches

Stop the server.

- [ ] **Step 4: Commit**

```bash
git add src/pages/blog/tags/
git commit -m "feat: add blog tag filter pages"
```

---

## Task 12: RSS Feed

**Files:**
- Create: `src/pages/rss.xml.ts`

- [ ] **Step 1: Create `src/pages/rss.xml.ts`**

```ts
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  const sorted = posts.sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());

  return rss({
    title: 'Austin Orphan Blog',
    description: 'Thoughts, projects, and technical notes from Austin Orphan.',
    site: context.site!,
    items: sorted.map(post => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.pubDate,
      link: `/blog/${post.slug}/`,
    })),
  });
}
```

- [ ] **Step 2: Build and verify the RSS file generates**

```bash
npm run build
```

Expected: `dist/rss.xml` exists and contains the hello-world post entry. No build errors.

- [ ] **Step 3: Verify RSS is valid XML**

```bash
cat dist/rss.xml | head -30
```

Expected: starts with `<?xml` and contains `<channel>`, `<title>Austin Orphan Blog</title>`, and an `<item>` entry.

- [ ] **Step 4: Commit**

```bash
git add src/pages/rss.xml.ts
git commit -m "feat: add RSS feed endpoint"
```

---

## Task 13: Move Service Worker and Update Cache

**Files:**
- Create: `public/sw.js`

The service worker moves to `public/` so Astro copies it to `dist/` verbatim. The cache version is bumped to bust any stale caches from the old site.

- [ ] **Step 1: Create `public/sw.js`**

```js
const CACHE_NAME = 'austin-orphan-portfolio-v2';
const urlsToCache = [
  '/',
  '/blog',
  '/rss.xml',
  'https://fonts.googleapis.com/css2?family=Anta&family=Comfortaa:wght@700&family=Source+Sans+Pro:wght@900&display=swap',
  'https://unpkg.com/@phosphor-icons/web@2.1.1'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      );
    })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    })
  );
});
```

- [ ] **Step 2: Build and verify `dist/sw.js` exists**

```bash
npm run build && ls dist/sw.js
```

Expected: `dist/sw.js` listed.

- [ ] **Step 3: Commit**

```bash
git add public/sw.js
git commit -m "feat: move service worker to public/ and bump cache to v2"
```

---

## Task 14: GitHub Actions Deployment

**Files:**
- Create: `.github/workflows/deploy.yml`

Before creating the workflow, you must change GitHub Pages source in the repo settings from "Deploy from a branch" to "GitHub Actions" (Settings → Pages → Source → GitHub Actions).

- [ ] **Step 1: Change GitHub Pages source to GitHub Actions**

In your browser: go to `https://github.com/AustinOrphan/AustinOrphan.github.io` → Settings → Pages → under "Source", select **GitHub Actions**. Save.

- [ ] **Step 2: Create `.github/workflows/deploy.yml`**

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [master]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - uses: actions/setup-node@v4
        with:
          node-version: '24'
          cache: npm

      - run: npm ci

      - run: npm run build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

- [ ] **Step 3: Commit and push**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add GitHub Actions deploy workflow"
git push origin master
```

- [ ] **Step 4: Verify the Actions workflow runs successfully**

Go to `https://github.com/AustinOrphan/AustinOrphan.github.io/actions`. Wait for the "Deploy to GitHub Pages" workflow to complete (green checkmark). Then visit `https://austinorphan.com` and verify the portfolio loads.

---

## Task 15: Clean Up Old Files

Only do this after Task 14's deployment is verified working at `austinorphan.com`.

**Files deleted:**
- `index.html`
- `js/component-loader.js` + `js/` directory
- `styles/main.css` + `styles/` directory
- `components/about.html`, `components/projects.html`, `components/contact.html`, `components/footer.html` + `components/` directory
- `sw.js` (root — now in `public/`)
- `CNAME` (root — now in `public/`)
- All favicon/icon files at root (now in `public/`)

- [ ] **Step 1: Delete old files**

```bash
rm index.html
rm -rf js/ styles/ components/
rm sw.js CNAME
rm apple-touch-icon.png android-chrome-192x192.png android-chrome-512x512.png
rm favicon-16x16.png favicon-32x32.png favicon.ico favicon.png favicon.svg
rm mstile-70x70.png mstile-144x144.png mstile-150x150.png mstile-310x150.png mstile-310x310.png
rm safari-pinned-tab.svg site.webmanifest browserconfig.xml
rm AustinOrphanResume.pdf
```

- [ ] **Step 2: Build one final time to verify nothing broke**

```bash
npm run build
```

Expected: build completes with no errors. Verify key files in `dist/`:

```bash
ls dist/
ls dist/blog/
ls dist/blog/tags/
ls dist/rss.xml
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: remove pre-Astro source files"
git push origin master
```

- [ ] **Step 4: Verify final deployment**

Wait for the Actions workflow to complete, then verify:
- `https://austinorphan.com` — portfolio loads correctly
- `https://austinorphan.com/blog` — blog list with sample post
- `https://austinorphan.com/blog/hello-world` — sample post renders
- `https://austinorphan.com/blog/tags/meta` — tag page renders
- `https://austinorphan.com/rss.xml` — RSS feed is valid XML
- Konami code (↑↑↓↓←→←→BA) toggles pixel mode
- Type "party" to trigger particle system
