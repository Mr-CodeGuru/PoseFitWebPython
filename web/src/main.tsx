import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { injectSpeedInsights } from '@vercel/speed-insights';
import { inject as injectAnalytics } from '@vercel/analytics';
import './index.css';
import App from './App.tsx';

// Offline mode compliance: Only inject telemetry if running on remote Vercel domain
if (typeof window !== 'undefined' && window.location.hostname.endsWith('vercel.app')) {
  injectSpeedInsights();
  injectAnalytics();
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
