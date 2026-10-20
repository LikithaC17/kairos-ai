import axios from 'axios';

/**
 * Dynamic API Base URL resolution:
 * 1. Checks localStorage for operator override (NETSCOPE_API_URL configured in Settings)
 * 2. Checks VITE_API_URL (production environment variable specified for Vercel/cloud)
 * 3. Checks VITE_API_BASE_URL (backward compatibility)
 * 4. In production (import.meta.env.PROD), defaults to 'https://cyber-network-traffic.onrender.com'
 * 5. In development, defaults to '' (empty string) to utilize Vite's dev server proxy (/api -> backend)
 *
 * Notice: localhost:8000 and 127.0.0.1:8000 are NEVER hard-coded in the production frontend bundle.
 */
function resolveApiBaseUrl(): string {
  // 1. Operator override from SOC Settings page
  if (typeof window !== 'undefined' && window.localStorage) {
    const custom = window.localStorage.getItem('NETSCOPE_API_URL');
    if (custom && custom.trim()) {
      return sanitizeUrl(custom.trim());
    }
  }

  // 2. Environment variable (VITE_API_URL prioritized per specification)
  const envUrl = (
    import.meta.env.VITE_API_URL ||
    import.meta.env.VITE_API_BASE_URL ||
    ''
  ).trim();

  if (envUrl) {
    return sanitizeUrl(envUrl);
  }

  // 3. Fallback: In production, route directly to deployed Render backend
  if (import.meta.env.PROD) {
    return 'https://cyber-network-traffic.onrender.com';
  }

  // 4. In development, empty string leverages the Vite proxy
  return '';
}

function sanitizeUrl(url: string): string {
  let cleaned = url.replace(/\/+$/, '');
  // If env var contains a trailing /api, remove it since service calls start with /api/
  if (cleaned.endsWith('/api')) {
    cleaned = cleaned.slice(0, -4);
  }
  return cleaned;
}

export const API_BASE_URL = resolveApiBaseUrl();

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMsg =
      error.response?.data?.detail ||
      error.message ||
      'Network connection to backend API failed.';
    console.error('API Error:', errorMsg);
    return Promise.reject(error);
  }
);
