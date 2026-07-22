/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },

      // ── RSUD Ajibarang Design Tokens ──
      // Filosofi: Wibawa medis (biru) + presisi arsitektur (planograph)

      colors: {
        // Canvas (60% — Dominan)
        canvas: {
          DEFAULT: "#F4F6FA",
          alt: "#EBEEF4",
          hover: "#E8EBF2",
        },
        // Surface (kartu, modal, dropdown)
        surface: {
          DEFAULT: "#FFFFFF",
          muted: "#F9FAFC",
          hover: "#F3F5F9",
          active: "#EFF1F6",
        },
        // Ink (teks, ikon)
        ink: {
          DEFAULT: "#0B1A2E",
          muted: "#54657E",
          subtle: "#8B9BB5",
          inverse: "#FFFFFF",
        },
        // Navy (30% — Sekunder / Struktur)
        // Warna biru medis untuk sidebar, header, container
        navy: {
          900: "#0A1628",
          800: "#0F1E36",
          700: "#152A4A",
          600: "#1C3A60",
          500: "#234D7A",
          400: "#3B6FA0",
          300: "#6B9BC6",
          200: "#A5C8E6",
          100: "#D6E4F2",
          50:  "#EDF3FA",
        },
        // Teal (10% — Aksen / Aksi)
        // Toska segar untuk tombol, link, indikator aktif
        teal: {
          700: "#0D7A6A",
          600: "#0F8F7D",
          500: "#12A892",
          400: "#2DC3AC",
          300: "#5FD9C5",
          200: "#A8EDE0",
          100: "#D6F7F0",
          50:  "#EDFBF7",
        },
        // Warna fungsional (hanya untuk arti — bukan dekorasi)
        danger: {
          DEFAULT: "#D92D2D",
          muted: "#FEF2F2",
          border: "#FEE2E2",
        },
        warning: {
          DEFAULT: "#D97706",
          muted: "#FFFBEB",
          border: "#FEF3C7",
        },
        success: {
          DEFAULT: "#059669",
          muted: "#ECFDF5",
          border: "#D1FAE5",
        },
      },

      borderRadius: {
        "plan-sm": "0.25rem",
        plan: "0.375rem",
        "plan-lg": "0.5rem",
        "plan-xl": "0.75rem",
      },

      // Planograph signature: shadow + thin border outline (0 0 0 1px)
      boxShadow: {
        "plan-sm":
          "0 1px 2px rgba(11, 26, 46, 0.06), 0 0 0 1px rgba(11, 26, 46, 0.04)",
        plan:
          "0 1px 3px rgba(11, 26, 46, 0.08), 0 0 0 1px rgba(11, 26, 46, 0.04)",
        "plan-md":
          "0 4px 6px -1px rgba(11, 26, 46, 0.08), 0 0 0 1px rgba(11, 26, 46, 0.04)",
        "plan-lg":
          "0 10px 15px -3px rgba(11, 26, 46, 0.08), 0 0 0 1px rgba(11, 26, 46, 0.04)",
      },

      spacing: {
        "plan-1": "0.25rem",
        "plan-2": "0.5rem",
        "plan-3": "0.75rem",
        "plan-4": "1rem",
        "plan-5": "1.5rem",
        "plan-6": "2rem",
        "plan-8": "3rem",
        "plan-10": "4rem",
        "plan-12": "5rem",
      },

      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "scale-in": "scaleIn 0.15s ease-out",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
      },
    },
  },
  plugins: [],
};
