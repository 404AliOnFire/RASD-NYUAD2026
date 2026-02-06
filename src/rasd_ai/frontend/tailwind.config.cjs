/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "neon-cyan": "#00f0ff",
        "neon-purple": "#a855f7",
        "neon-pink": "#ff4fd8",
        "panel": "#0b1020",
        "panel-soft": "#111833",
        "grid": "#1b2342"
      },
      boxShadow: {
        glow: "0 0 25px rgba(0, 240, 255, 0.25)",
        pink: "0 0 25px rgba(255, 79, 216, 0.25)"
      }
    }
  },
  plugins: []
};
