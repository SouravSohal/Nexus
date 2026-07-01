/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Bloomberg/Palantir inspired HSL colors
        background: "hsl(222, 47%, 4%)",       // Deep Obsidian Black
        card: "hsl(222, 47%, 7%)",             // Muted Card Gray/Navy
        cardHover: "hsl(222, 47%, 11%)",       // Highlight state
        border: "hsl(222, 30%, 15%)",          // Sleek slate border
        textMuted: "hsl(215, 20%, 65%)",       // Secondary labels
        textDefault: "hsl(210, 40%, 98%)",     // Bright text
        
        // Dynamic Status Indicators
        status: {
          healthy: "hsl(142, 70%, 45%)",       // Pure Operational Green
          alert: "hsl(346, 80%, 50%)",         // High-Risk Red
          warning: "hsl(45, 93%, 47%)",        // Safety Stock Warning Amber
          standby: "hsl(217, 91%, 60%)",       // Standby Backup Blue
          gray: "hsl(215, 15%, 30%)"           // Inactive/Offline
        },
        
        brand: {
          primary: "hsl(217, 91%, 60%)",       // Electric Indigo
          glow: "rgba(59, 130, 246, 0.15)"     // Core Accent Glow
        }
      },
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"]
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
        "glass-glow": "0 0 20px 0 rgba(59, 130, 246, 0.2)"
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "border-glow": "borderGlow 4s linear infinite"
      },
      keyframes: {
        borderGlow: {
          "0%, 100%": { "border-color": "hsl(222, 30%, 15%)" },
          "50%": { "border-color": "hsl(217, 91%, 60%)" }
        }
      }
    },
  },
  plugins: [],
}
