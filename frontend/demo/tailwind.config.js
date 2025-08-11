/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './strategic-dashboard/**/*.{js,ts,jsx,tsx,mdx}',
    './intelligence-panels/**/*.{js,ts,jsx,tsx,mdx}',
    './shared-components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Jarvis Theme Colors
        'jarvis': {
          50: '#E5F9FF',
          100: '#B3F0FF',
          200: '#80E6FF',
          300: '#4DDDFF',
          400: '#1AD3FF',
          500: '#00D4FF', // Primary Jarvis Blue
          600: '#00B4D8',
          700: '#0094B3',
          800: '#00748C',
          900: '#005466',
        },
        'stark': {
          50: '#F8FAFC',
          100: '#F1F5F9',
          200: '#E2E8F0',
          300: '#CBD5E1',
          400: '#94A3B8',
          500: '#64748B',
          600: '#475569',
          700: '#334155',
          800: '#1E293B',
          900: '#0F172A', // Primary Dark Background
          950: '#0A1628', // Stark Navy
        },
        'arc-reactor': '#00B4D8',
        'critical-alert': '#FF6B6B',
        'opportunity': '#4ECDC4',
        'warning': '#FFE66D',
        'success': '#A8E6CF',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px #00D4FF' },
          '100%': { boxShadow: '0 0 20px #00D4FF, 0 0 30px #00D4FF' },
        },
      },
      boxShadow: {
        'jarvis': '0 0 20px rgba(0, 212, 255, 0.3)',
        'jarvis-lg': '0 0 40px rgba(0, 212, 255, 0.4)',
        'inner-glow': 'inset 0 0 10px rgba(0, 212, 255, 0.2)',
      },
      backdropBlur: {
        'xs': '2px',
      },
      screens: {
        'xs': '475px',
        '3xl': '1600px',
      },
    },
  },
  plugins: [],
}