import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // BrewIQ amber accent.
        brew: {
          500: "#d97706",
          600: "#b45309",
        },
      },
    },
  },
  plugins: [],
};

export default config;
