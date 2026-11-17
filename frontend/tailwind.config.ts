import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fbf7ee',
          100: '#f5ebd2',
          500: '#b48135',
          600: '#946324',
          700: '#754b1c',
          800: '#5c3917',
          900: '#472b12',
          950: '#2c1809',
        }
      }
    },
  },
  plugins: [],
};
export default config;
