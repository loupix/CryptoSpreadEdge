import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';
import { createAppTheme, ThemeMode } from './theme';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

function Root() {
  const [mode, setMode] = React.useState<ThemeMode>(() => {
    const saved = localStorage.getItem('cryptospreadedge-theme');
    return (saved as ThemeMode) || 'dark';
  });
  const [primary, setPrimary] = React.useState<string | undefined>(() => {
    try {
      const raw = localStorage.getItem('cryptospreadedge-settings');
      if (!raw) return undefined;
      const parsed = JSON.parse(raw);
      return parsed?.primaryColor;
    } catch {
      return undefined;
    }
  });
  const [secondary, setSecondary] = React.useState<string | undefined>(() => {
    try {
      const raw = localStorage.getItem('cryptospreadedge-settings');
      if (!raw) return undefined;
      const parsed = JSON.parse(raw);
      return parsed?.secondaryColor;
    } catch {
      return undefined;
    }
  });

  React.useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === 'cryptospreadedge-theme' && e.newValue) {
        setMode(e.newValue as ThemeMode);
      }
      if (e.key === 'cryptospreadedge-settings' && e.newValue) {
        try {
          const parsed = JSON.parse(e.newValue);
          setPrimary(parsed?.primaryColor);
          setSecondary(parsed?.secondaryColor);
        } catch {}
      }
    };
    window.addEventListener('storage', handler);
    return () => window.removeEventListener('storage', handler);
  }, []);

  React.useEffect(() => {
    const onThemeChange = (event: any) => {
      if (event?.detail?.mode) setMode(event.detail.mode as ThemeMode);
      if (event?.detail?.primary) setPrimary(event.detail.primary);
      if (event?.detail?.secondary) setSecondary(event.detail.secondary);
    };
    window.addEventListener('cryptospreadedge-theme-change', onThemeChange as any);
    return () => window.removeEventListener('cryptospreadedge-theme-change', onThemeChange as any);
  }, []);

  const currentTheme = React.useMemo(() => createAppTheme(mode, { primary, secondary }), [mode, primary, secondary]);

  return (
    <BrowserRouter>
      <ThemeProvider theme={currentTheme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </BrowserRouter>
  );
}

root.render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);