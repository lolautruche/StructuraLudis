import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Couleurs de base Structura Ludis
        ludis: {
          dark: "#0F172A",    // Slate 900
          card: "#1E293B",    // Slate 800
          primary: "#3B82F6", // Blue 500
          accent: "#8B5CF6",  // Violet 500 (RPG vibe)
          success: "#10B981", // Emerald 500 (Safety & Check-in)
        }
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
export default config;
