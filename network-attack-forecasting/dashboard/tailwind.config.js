/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        soc: {
          bg: '#080d1a',
          surface: '#0f172a',
          card: '#131e33',
          cardHover: '#182642',
          border: '#1e293b',
          borderLight: '#334155',
          textMuted: '#94a3b8',
          textBright: '#f8fafc',
          normal: '#10b981',    // green
          warning: '#f59e0b',   // yellow
          suspicious: '#f97316',// orange
          critical: '#ef4444',  // red
          prediction: '#3b82f6',// blue
          ai: '#8b5cf6',        // purple
          cyan: '#06b6d4',      // cyan
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
