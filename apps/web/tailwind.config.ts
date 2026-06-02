import type { Config } from "tailwindcss";

// RTL handled natively via <html dir="rtl"> + logical properties (ms-/me-/ps-/pe-),
// which Tailwind 3.3+ supports out of the box. No directional ml-/mr- in components.
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1a1d23",
        paper: "#fafaf7",
        burgundy: "#8b1538",
        gold: "#a67c2e",
      },
      fontFamily: {
        display: ["var(--font-frank-ruhl)", "serif"],
        body: ["var(--font-heebo)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
