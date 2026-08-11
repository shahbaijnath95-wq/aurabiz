/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Light taste palette
        void: { DEFAULT: "#faf9f7", 50: "#ffffff", 100: "#faf9f7", 200: "#f4f1ea", 300: "#e8e4db" },
        bone: { DEFAULT: "#05060a", 50: "#f8f8f8", 100: "#1a1a1a", 200: "#2a2a2a", 300: "#3a3a3a" },
        gold: { DEFAULT: "#e67a00", 50: "#fff8ed", 100: "#ffedc7", 200: "#ffdb8a", 300: "#ffc554", 400: "#ffb24d", 500: "#e67a00", 600: "#cc6600", 700: "#994d00", 800: "#663300" },
        ember: { DEFAULT: "#cc5500", 50: "#fff4e6", 100: "#ffe0b3", 200: "#ffcc80", 300: "#ff9933", 400: "#ff7a18", 500: "#cc5500" },
        crystal: { violet: "#7c5ce0", cyan: "#3db8e8", magenta: "#e055a0" },
        // Functional
        primary: { 50: "#fff8ed", 100: "#ffedc7", 200: "#ffdb8a", 300: "#ffc554", 400: "#ffb24d", 500: "#e67a00", 600: "#cc6600", 700: "#994d00", 800: "#663300", 900: "#331a00" },
        surface: { DEFAULT: "#ffffff", 50: "#ffffff", 100: "#faf9f7", 200: "#f4f1ea", 300: "#e8e2d9", 400: "#d5d0c5", 500: "#c0bab0", 600: "#8b8275", 700: "#5e564a", 800: "#3a342b", 900: "#2a251f" },
        muted: { DEFAULT: "#6b7280", 100: "#374151", 200: "#6b7280", 300: "#9ca3af" },
        success: { 50: "#ecfdf5", 100: "#d1fae5", 300: "#6ee7b7", 400: "#34d399", 500: "#10b981", 600: "#059669", 700: "#065f46" },
        danger: { 50: "#fef2f2", 100: "#fee2e2", 300: "#fca5a5", 400: "#f87171", 500: "#ef4444", 600: "#dc2626", 700: "#b91c1c" },
        error: { 50: "#fef2f2", 100: "#fee2e2", 300: "#fca5a5", 400: "#f87171", 500: "#ef4444", 600: "#dc2626", 700: "#b91c1c" },
        info: { 50: "#eff6ff", 100: "#dbeafe", 300: "#93c5fd", 400: "#60a5fa", 500: "#3b82f6", 600: "#2563eb", 700: "#1d4ed8" },
        warning: { 50: "#fffbeb", 100: "#fef3c7", 300: "#fcd34d", 400: "#fbbf24", 500: "#f59e1b", 600: "#d97706", 700: "#b45309" },
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      boxShadow: {
        glow: "0 0 20px rgba(230, 122, 0, 0.1)",
        "glow-lg": "0 0 40px rgba(230, 122, 0, 0.15)",
        "gold-sm": "0 2px 8px rgba(230, 122, 0, 0.18)",
        gold: "0 0 30px rgba(230, 122, 0, 0.15)",
        "gold-lg": "0 0 40px rgba(230, 122, 0, 0.2)",
        crystal: "0 0 30px rgba(124, 92, 224, 0.1)",
        "inner-glow": "inset 0 1px 0 rgba(255, 255, 255, 0.8)",
        soft: "0 1px 3px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.04)",
        card: "0 1px 2px rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.03)",
      },
      backgroundImage: {
        "gradient-gold": "linear-gradient(135deg, #ffb24d, #e67a00)",
        "gradient-crystal": "linear-gradient(135deg, #7c5ce0, #3db8e8, #e055a0)",
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        "float-slow": "float 8s ease-in-out infinite",
        glow: "glow 2s ease-in-out infinite alternate",
        "slide-up": "slideUp 0.5s ease-out forwards",
        "fade-in": "fadeIn 0.4s ease-out forwards",
      },
      keyframes: {
        float: { "0%, 100%": { transform: "translateY(0px)" }, "50%": { transform: "translateY(-10px)" } },
        glow: { "0%": { boxShadow: "0 0 20px rgba(230,122,0,0.08)" }, "100%": { boxShadow: "0 0 40px rgba(230,122,0,0.18)" } },
        slideUp: { "0%": { opacity: "0", transform: "translateY(20px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
      },
    },
  },
  plugins: [],
};
