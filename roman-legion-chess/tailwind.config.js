/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx,html}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: '#D4AF37',
          bright: '#F0C850',
          dark: '#A88628',
        },
        crimson: {
          DEFAULT: '#C8102E',
          deep: '#8B0A1F',
        },
        marble: {
          DEFAULT: '#F5F1E8',
          vein: '#E8DCC4',
        },
        obsidian: {
          DEFAULT: '#1A1A2E',
          deep: '#0F0F17',
        },
      },
      fontFamily: {
        display: ['Cinzel', 'serif'],
        numeric: ['Orbitron', 'monospace'],
        body: ['system-ui', 'sans-serif'],
      },
      letterSpacing: {
        banner: '0.12em',
        button: '0.1em',
      },
      boxShadow: {
        'gold-soft': '0 0 12px rgba(212,175,55,0.45)',
        'gold-strong': '0 0 22px rgba(212,175,55,0.75)',
        'crimson-glow': '0 0 18px rgba(200,16,46,0.55)',
      },
      keyframes: {
        pulseGold: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(212,175,55,0.4)' },
          '50%': { boxShadow: '0 0 18px 3px rgba(212,175,55,0.85)' },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'pulse-gold': 'pulseGold 1.4s ease-in-out infinite',
        'fade-in': 'fadeIn 250ms ease-out both',
      },
    },
  },
  plugins: [],
};
