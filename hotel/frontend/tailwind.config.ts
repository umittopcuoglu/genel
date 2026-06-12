import type { Config } from "tailwindcss";

/**
 * HotelOps tasarım token'ları — docs/03_FRONTEND_TASARIM.md §1.2 paleti.
 * Light/Dark değerleri globals.css'teki CSS değişkenlerinden gelir.
 */
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "rgb(var(--color-primary) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        sidebar: "rgb(var(--sidebar-bg) / <alpha-value>)",
        success: "rgb(var(--color-success) / <alpha-value>)",
        warning: "rgb(var(--color-warning) / <alpha-value>)",
        danger: "rgb(var(--color-danger) / <alpha-value>)",
        info: "rgb(var(--color-info) / <alpha-value>)",
        bg: "rgb(var(--color-bg) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        line: "rgb(var(--color-border) / <alpha-value>)",
        "text-1": "rgb(var(--color-text-1) / <alpha-value>)",
        "text-2": "rgb(var(--color-text-2) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
