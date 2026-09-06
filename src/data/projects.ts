// Single source of truth for the Projects section and the hero link-bar
// dropdown. Add a project here and it appears in both.
//
// `demo` is a live, playable URL. Projects with a demo also appear in the
// hero link-bar dropdown; those without are cards only.
//
// Note: /tanks/ and /ProjectileMotionSimulator/ are served by their own
// repos' GitHub Pages under the same apex domain — they are not built by
// this repo. Keep the trailing slash; /tanks 301-redirects to /tanks/.

export interface Project {
  title: string;
  description: string;
  tech: string[];
  /** Live playable demo. Present ⇒ listed in the link-bar dropdown. */
  demo?: string;
  /** Phosphor icon name (without the `ph-` prefix) for the dropdown entry. */
  icon?: string;
  repo?: string;
  /** Renders as the muted "explore more" card. */
  placeholder?: boolean;
}

export const projects: Project[] = [
  {
    title: 'Tanks!',
    description:
      'A deterministic top-down arena tank game with ricochets, mines, and tactical AI.',
    tech: ['TypeScript', 'three.js', 'Game Development', 'Deterministic Simulation'],
    demo: '/tanks/',
    /* strategy, not crosshair: the dropdown draws this at 15px, where a ringed
       dot collapses into a cursor. The chalkboard Xs and movement arc say
       "top-down, tactical" instead of "aim at something", and separated marks
       survive that size where concentric ones blur. Phosphor has no tank or
       explosion glyph at any version, so those were not options. */
    icon: 'strategy',
    repo: 'https://github.com/austinorphan/tanks',
  },
  {
    title: 'Projectile Motion Simulator',
    description:
      'Interactive physics simulation demonstrating projectile motion principles with real-time visualization and parameter controls for educational purposes.',
    tech: ['JavaScript', 'HTML5 Canvas', 'Physics', 'Education'],
    demo: '/ProjectileMotionSimulator/src/',
    icon: 'chart-line-up',
    repo: 'https://github.com/austinorphan/ProjectileMotionSimulator',
  },
  {
    title: 'Running App MVP',
    description:
      'A TypeScript-based running application MVP designed to track and analyze running performance with modern web technologies.',
    tech: ['TypeScript', 'Web Development', 'Fitness Tracking', 'MVP'],
    repo: 'https://github.com/austinorphan/running-app-mvp',
  },
  {
    title: 'MazeBot',
    description:
      'Maze navigating robot initially designed for my college robotics class. Implements pathfinding algorithms and sensor integration for autonomous navigation.',
    tech: ['Python', 'Robotics', 'Pathfinding', 'Algorithms'],
    repo: 'https://github.com/austinorphan/MazeBot',
  },
  {
    title: 'Explore More Projects',
    description:
      'Check out my GitHub profile for additional projects, contributions, and experimental work. Always building something new!',
    tech: ['C#', '.NET', 'AWS', 'Innovation'],
    repo: 'https://github.com/austinorphan',
    placeholder: true,
  },
];

/** Projects with a live demo, in display order. */
export const demoProjects = projects.filter((p) => p.demo);
