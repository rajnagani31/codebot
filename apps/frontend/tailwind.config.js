/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        nero: {
          ivory: "#FFFDF2",
          cream: "#FBFAF0",
          "light-cream": "#F7F8EF",
          "soft-cream": "#F4F3E8",
          "very-light-green": "#F1F7F2",
          soft: "#E7F3EA",
          "soft-border": "#C8E6D0",
          green: "#087A55",
          dark: "#075B49",
          "dark-alt": "#064F42",
          deepest: "#071B14",
          bright: "#18A85F",
          "dot-green": "#58C98A",
          "active-border": "#57C98A",
          "active-bg": "#F4FAF5",
          panel: "#101411",
          "panel-border": "#1D2921",
          "panel-code": "#E4ECE6",
          "panel-muted": "#7D8B82",
          "panel-green": "#31C77A",
          border: "#DDE5DD",
          "border-security": "#DADFD7",
          text: "#111512",
          "text-secondary": "#68706D",
          "text-muted": "#929892",
          footer: "#071B14",
          "footer-text": "#F2F7F3",
          "footer-muted": "#9AAFA4",
          "footer-links": "#C7D8CF",
          "footer-hover": "#35C77A",
        },
      },
      fontFamily: {
        sans: ["Inter", "Geist", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        subtle: "0 12px 40px rgba(20, 40, 25, 0.045)",
        btn: "0 6px 20px rgba(8, 122, 85, 0.12)",
        card: "0 12px 40px rgba(20, 40, 25, 0.045)",
        float: "0 24px 48px -12px rgba(7, 27, 20, 0.2)",
        "green-glow": "0 0 24px rgba(8, 122, 85, 0.12)",
      },
      keyframes: {
        pulseGreen: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.6", transform: "scale(1.05)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
      animation: {
        "pulse-green": "pulseGreen 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-up": "slideUp 0.3s ease-out forwards",
        "fade-in": "fadeIn 0.2s ease-out forwards",
      },
    },
  },
  plugins: [],
};
