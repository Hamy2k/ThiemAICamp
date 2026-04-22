import type { Config } from "tailwindcss";

/**
 * Tailwind v4 uses CSS-first config via @theme in globals.css.
 * This file exists to satisfy project-structure convention and hold
 * shared presets / plugins if needed in Phase 5+.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
};

export default config;
