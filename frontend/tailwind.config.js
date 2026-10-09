/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        aquashield: {
          bg: "#0B132B",          // Deep Charcoal Navy background
          card: "#131D38",        // Dark Blue-Slate card surface
          cardBorder: "#1E293B",  // Card borders
          cyan: "#06B6D4",        // Active highlight electric cyan
          cyanHover: "#0891B2",
          red: "#EF4444",         // Critical hazard
          amber: "#F59E0B",       // Warning hazard
          emerald: "#10B981",     // Safe status
          slateText: "#94A3B8",   // Subtext
          glass: "rgba(19, 29, 56, 0.85)",
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
