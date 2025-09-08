import { createTheme } from '@mui/material/styles';

export type ThemeMode = 'light' | 'dark';

export const createAppTheme = (mode: ThemeMode, opts?: { primary?: string; secondary?: string }) =>
  createTheme({
    palette: {
      mode,
      primary: {
        main: opts?.primary || (mode === 'dark' ? '#00e19d' : '#0b7a5f'),
        dark: mode === 'dark' ? '#00b37a' : '#075845',
        light: mode === 'dark' ? '#4dffbf' : '#4dc9a8',
      },
      secondary: {
        main: opts?.secondary || (mode === 'dark' ? '#7aa2f7' : '#1e40af'),
        dark: mode === 'dark' ? '#3b6ed8' : '#1e3a8a',
        light: mode === 'dark' ? '#a7c2fb' : '#93c5fd',
      },
      background: {
        default: mode === 'dark' ? '#0b0e11' : '#f7fafc',
        paper: mode === 'dark' ? '#111418' : '#ffffff',
      },
      divider: mode === 'dark' ? '#1f2430' : '#e5e7eb',
      text: {
        primary: mode === 'dark' ? '#e6eaf2' : '#0f172a',
        secondary: mode === 'dark' ? '#9aa4b2' : '#475569',
      },
      success: { main: '#22c55e' },
      error: { main: '#ef4444' },
      warning: { main: '#f59e0b' },
      info: { main: '#38bdf8' },
    },
    shape: {
      borderRadius: 10,
    },
    typography: {
      fontFamily: 'Inter, Roboto, Helvetica, Arial, sans-serif',
      h1: { fontSize: '2.2rem', fontWeight: 700, letterSpacing: '-0.01em' },
      h2: { fontSize: '1.8rem', fontWeight: 700, letterSpacing: '-0.01em' },
      h3: { fontSize: '1.4rem', fontWeight: 600 },
      h4: { fontSize: '1.2rem', fontWeight: 600 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundImage:
              mode === 'dark'
                ? 'radial-gradient(1000px 400px at 5% 0%, rgba(0, 225, 157, 0.06) 0%, rgba(0,0,0,0) 60%), radial-gradient(800px 300px at 95% 10%, rgba(122,162,247,0.06) 0%, rgba(0,0,0,0) 60%)'
                : 'radial-gradient(1000px 400px at 5% 0%, rgba(14,165,233,0.08) 0%, rgba(255,255,255,0) 60%), radial-gradient(800px 300px at 95% 10%, rgba(16,185,129,0.08) 0%, rgba(255,255,255,0) 60%)',
          },
          '*': {
            scrollbarColor: mode === 'dark' ? '#333 #111' : '#cbd5e1 #ffffff',
          },
        },
      },
      MuiButtonBase: {
        defaultProps: {
          disableRipple: false,
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundColor: mode === 'dark' ? '#111418' : '#ffffff',
            border: `1px solid ${mode === 'dark' ? '#1f2430' : '#e5e7eb'}`,
            transition: 'transform 120ms ease, box-shadow 120ms ease',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: mode === 'dark' ? '0 8px 24px rgba(0,0,0,0.3)' : '0 8px 24px rgba(0,0,0,0.08)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            transition: 'transform 120ms ease, box-shadow 120ms ease',
            '&:hover': {
              transform: 'translateY(-1px)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
            },
            '&:focus-visible': {
              boxShadow: `0 0 0 3px ${mode === 'dark' ? 'rgba(0,225,157,0.35)' : 'rgba(14,165,233,0.35)'}`,
            },
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: mode === 'dark' ? '#111418' : '#ffffff',
            borderBottom: `1px solid ${mode === 'dark' ? '#1f2430' : '#e5e7eb'}`,
          },
        },
      },
    },
  });

// Default export remains dark theme for backward compatibility
const defaultTheme = createAppTheme('dark');
export default defaultTheme;

