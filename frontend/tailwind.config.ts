import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'navy-bg': '#0d1117',
        'navy-panel': '#1a1a2e',
        'accent-yellow': '#ecad0a',
        'blue-primary': '#209dd7',
        'purple-secondary': '#753991',
        'border-muted': '#2a2e3a',
        'up-green': '#26a65b',
        'down-red': '#e5484d',
      },
      animation: {
        'flash-green': 'flashGreen 500ms ease-out',
        'flash-red': 'flashRed 500ms ease-out',
      },
      keyframes: {
        flashGreen: {
          '0%': { backgroundColor: 'rgba(38, 166, 91, 0.45)' },
          '100%': { backgroundColor: 'transparent' },
        },
        flashRed: {
          '0%': { backgroundColor: 'rgba(229, 72, 77, 0.45)' },
          '100%': { backgroundColor: 'transparent' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
