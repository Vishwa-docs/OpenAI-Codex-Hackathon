import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      boxShadow: {
        glow: "0 20px 60px -20px rgba(59, 130, 246, 0.4)"
      },
      colors: {
        ink: {
          50: "#f6f8fc",
          100: "#e8eef9",
          200: "#ced9ef",
          300: "#a7b7db",
          400: "#7c94c5",
          500: "#4f6ba8",
          600: "#395284",
          700: "#283c62",
          800: "#182843",
          900: "#0d1728",
          950: "#07111d"
        }
      },
      backgroundImage: {
        "radial-grid":
          "radial-gradient(circle at 1px 1px, rgba(148,163,184,0.16) 1px, transparent 0)"
      }
    }
  },
  plugins: []
};

export default config;
