// Design tokens for Financial Terminal aesthetic

export const colors = {
  terminal: {
    bg: '#0a0e14',
    surface: '#151922',
    border: '#2a2f3a',
    borderLight: '#3a3f4a',
  },
  amber: {
    DEFAULT: '#f59e0b',
    light: '#fbbf24',
    dark: '#d97706',
    glow: 'rgba(251, 191, 36, 0.15)',
  },
  cyan: {
    DEFAULT: '#06b6d4',
    light: '#22d3ee',
    dark: '#0891b2',
    glow: 'rgba(34, 211, 238, 0.15)',
  },
  success: '#10b981',
  error: '#ef4444',
  warning: '#f59e0b',
  text: {
    primary: '#e5e7eb',
    secondary: '#9ca3af',
    muted: '#6b7280',
  },
} as const;

export const spacing = {
  xs: '0.25rem',    // 4px
  sm: '0.5rem',     // 8px
  md: '1rem',       // 16px
  lg: '1.5rem',     // 24px
  xl: '2rem',       // 32px
  '2xl': '3rem',    // 48px
} as const;

export const transitions = {
  fast: '150ms ease-in-out',
  base: '300ms ease-in-out',
  slow: '400ms ease-in-out',
} as const;

export const typography = {
  fontFamily: {
    mono: '"IBM Plex Mono", Menlo, Monaco, monospace',
    serif: '"Crimson Pro", Georgia, serif',
    sans: 'system-ui, -apple-system, sans-serif',
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
  },
} as const;

export const layout = {
  sidebarWidth: '280px',
  sourcesWidth: '400px',
  headerHeight: '48px',
  borderWidth: '1px',
} as const;

export const animation = {
  stagger: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4, ease: 'easeOut' },
  },
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3 },
  },
  slideUp: {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3, ease: 'easeOut' },
  },
} as const;

// Quality score color mapping
export const getScoreColor = (score: number): string => {
  if (score >= 8) return colors.success;
  if (score >= 6) return colors.cyan.DEFAULT;
  if (score >= 4) return colors.amber.DEFAULT;
  return colors.error;
};

// Format timestamp in terminal style: YYYY.MM.DD HH:MM
export const formatTerminalTimestamp = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${year}.${month}.${day} ${hours}:${minutes}`;
};
