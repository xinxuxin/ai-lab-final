/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mist: "#eef4ff",
        glow: "#8ec5ff",
        coral: "#ff8a72",
        lime: "#c6ff7f",
        sand: "#f7f1e8",
      },
      fontFamily: {
        sans: ["'DM Sans'", "sans-serif"],
        display: ["'Space Grotesk'", "sans-serif"],
      },
      boxShadow: {
        float: "0 20px 60px rgba(15, 23, 42, 0.16)",
      },
      backgroundImage: {
        mesh: "radial-gradient(circle at top left, rgba(142, 197, 255, 0.55), transparent 35%), radial-gradient(circle at bottom right, rgba(255, 138, 114, 0.28), transparent 30%)",
      },
    },
  },
  plugins: [],
};

