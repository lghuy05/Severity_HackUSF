import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0b0f14",
        mist: "#111827",
        aqua: "#38bdf8",
        coral: "#6366f1",
        alert: "#ef4444",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        panel: "0 24px 80px rgba(2, 6, 23, 0.38)",
      },
    },
  },
  plugins: [],
};

export default config;
