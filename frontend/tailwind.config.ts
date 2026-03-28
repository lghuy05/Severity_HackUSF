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
        ink: "#102033",
        mist: "#eef5fb",
        aqua: "#74d3c7",
        coral: "#ff8a72",
        alert: "#b3261e",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        panel: "0 24px 60px rgba(16, 32, 51, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
