import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Primary palette
        primary: 'var(--color-primary)',
        'primary-fixed': 'var(--color-primary-fixed)',
        'primary-fixed-dim': 'var(--color-primary-fixed-dim)',
        'primary-container': 'var(--color-primary-container)',
        'on-primary': 'var(--color-on-primary)',
        'on-primary-fixed': 'var(--color-on-primary-fixed)',
        'on-primary-fixed-variant': 'var(--color-on-primary-fixed-variant)',
        'on-primary-container': 'var(--color-on-primary-container)',
        // Secondary palette
        secondary: 'var(--color-secondary)',
        'secondary-fixed': 'var(--color-secondary-fixed)',
        'secondary-fixed-dim': 'var(--color-secondary-fixed-dim)',
        'secondary-container': 'var(--color-secondary-container)',
        'on-secondary': 'var(--color-on-secondary)',
        'on-secondary-fixed': 'var(--color-on-secondary-fixed)',
        'on-secondary-fixed-variant': 'var(--color-on-secondary-fixed-variant)',
        'on-secondary-container': 'var(--color-on-secondary-container)',
        // Tertiary palette
        tertiary: 'var(--color-tertiary)',
        'tertiary-fixed': 'var(--color-tertiary-fixed)',
        'tertiary-fixed-dim': 'var(--color-tertiary-fixed-dim)',
        'tertiary-container': 'var(--color-tertiary-container)',
        'on-tertiary': 'var(--color-on-tertiary)',
        'on-tertiary-fixed': 'var(--color-on-tertiary-fixed)',
        'on-tertiary-fixed-variant': 'var(--color-on-tertiary-fixed-variant)',
        'on-tertiary-container': 'var(--color-on-tertiary-container)',
        // Error palette
        error: 'var(--color-error)',
        'error-container': 'var(--color-error-container)',
        'on-error': 'var(--color-on-error)',
        'on-error-container': 'var(--color-on-error-container)',
        // Background & Surface
        background: 'var(--color-background)',
        'on-background': 'var(--color-on-background)',
        surface: 'var(--color-surface)',
        'on-surface': 'var(--color-on-surface)',
        'on-surface-variant': 'var(--color-on-surface-variant)',
        'inverse-surface': 'var(--color-inverse-surface)',
        'inverse-on-surface': 'var(--color-inverse-on-surface)',
        'inverse-primary': 'var(--color-inverse-primary)',
        'surface-dim': 'var(--color-surface-dim)',
        'surface-bright': 'var(--color-surface-bright)',
        'surface-container-lowest': 'var(--color-surface-container-lowest)',
        'surface-container-low': 'var(--color-surface-container-low)',
        'surface-container': 'var(--color-surface-container)',
        'surface-container-high': 'var(--color-surface-container-high)',
        'surface-container-highest': 'var(--color-surface-container-highest)',
        'surface-variant': 'var(--color-surface-variant)',
        'surface-tint': 'var(--color-surface-tint)',
        // Outline & Border
        outline: 'var(--color-outline)',
        'outline-variant': 'var(--color-outline-variant)',
        border: 'var(--color-border)',
      },
      fontFamily: {
        sans: ['var(--font-family-sans, system-ui, sans-serif)'],
        serif: ['var(--font-family-serif, serif)'],
        mono: ['var(--font-family-mono, monospace)'],
      },
      borderRadius: {
        none: 'var(--border-radius-none, 0)',
        DEFAULT: 'var(--border-radius-sm, 0.125rem)',
        md: 'var(--border-radius-md, 0.375rem)',
        lg: 'var(--border-radius-lg, 0.5rem)',
        xl: 'var(--border-radius-xl, 0.75rem)',
        full: 'var(--border-radius-full, 9999px)',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
      },
      transitionDuration: {
        fast: 'var(--transition-fast, 100ms)',
        normal: 'var(--transition-normal, 150ms)',
        slow: 'var(--transition-slow, 300ms)',
      },
      letterSpacing: {
        tighter: 'var(--letter-spacing-tighter, -0.05em)',
        tight: 'var(--letter-spacing-tight, -0.025em)',
        normal: 'var(--letter-spacing-normal, 0em)',
        wide: 'var(--letter-spacing-wide, 0.025em)',
        wider: 'var(--letter-spacing-wider, 0.05em)',
        widest: 'var(--letter-spacing-widest, 0.1em)',
      },
    },
  },
  plugins: [],
};
export default config;
