/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#1C2B3A', light: '#2A3F54', dark: '#111B25' },
        accent:  { DEFAULT: '#E05C2A', light: '#F07040', dark: '#C04A1E' },
        surface: '#FFFFFF',
        bg:      '#F5F4F0',
        muted:   '#8C8880',
        border:  '#E0DEDA',
        success: { DEFAULT: '#2E7D52', light: '#E8F5EE' },
        warning: { DEFAULT: '#C17A1A', light: '#FEF3E2' },
        danger:  { DEFAULT: '#B83232', light: '#FDEAEA' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs':   ['11px', { lineHeight: '1.5' }],
        'sm':   ['12px', { lineHeight: '1.5' }],
        'base': ['14px', { lineHeight: '1.6' }],
        'md':   ['15px', { lineHeight: '1.5' }],
        'lg':   ['16px', { lineHeight: '1.4' }],
        'xl':   ['18px', { lineHeight: '1.3' }],
        '2xl':  ['22px', { lineHeight: '1.2' }],
        '3xl':  ['28px', { lineHeight: '1.1' }],
      },
      borderRadius: {
        'sm': '6px', 'md': '8px', 'lg': '10px', 'xl': '14px',
      },
      boxShadow: {
        'card':     '0 1px 3px rgba(28,43,58,0.08)',
        'dropdown': '0 4px 16px rgba(28,43,58,0.12)',
        'modal':    '0 8px 32px rgba(28,43,58,0.16)',
      },
    },
  },
  plugins: [],
}
