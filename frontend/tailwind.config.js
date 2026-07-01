/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // Nexus Intelligence Design System Colors
        border: "rgba(60, 73, 78, 0.5)",
        input: "#1a2123",
        ring: "rgba(0, 209, 255, 0.5)",
        background: "#0e1417",
        foreground: "#dde3e7",
        primary: {
          DEFAULT: "#a4e6ff",
          foreground: "#003543",
          container: "#00d1ff",
          fixed: "#b7eaff",
          "fixed-dim": "#4cd6ff",
        },
        secondary: {
          DEFAULT: "#d1bcff",
          foreground: "#3c0090",
          container: "#7000ff",
          fixed: "#e9ddff",
          "fixed-dim": "#d1bcff",
        },
        tertiary: {
          DEFAULT: "#ffd59c",
          foreground: "#442b00",
          container: "#feb127",
          fixed: "#ffddb1",
          "fixed-dim": "#ffba49",
        },
        destructive: {
          DEFAULT: "#93000a",
          foreground: "#ffdad6",
        },
        muted: {
          DEFAULT: "#2f3639",
          foreground: "#bbc9cf",
        },
        accent: {
          DEFAULT: "#242b2e",
          foreground: "#dde3e7",
        },
        popover: {
          DEFAULT: "#1a2123",
          foreground: "#dde3e7",
        },
        card: {
          DEFAULT: "#1a2123",
          foreground: "#dde3e7",
        },
        // Design System Surface Colors
        surface: {
          DEFAULT: "#0e1417",
          dim: "#0e1417",
          bright: "#333a3d",
          "container-lowest": "#090f12",
          "container-low": "#161d1f",
          container: "#1a2123",
          "container-high": "#242b2e",
          "container-highest": "#2f3639",
          glass: "rgba(26, 33, 35, 0.7)",
          base: "#0e1417",
        },
        outline: {
          DEFAULT: "#859399",
          variant: "#3c494e",
        },
        error: {
          DEFAULT: "#ffb4ab",
          foreground: "#690005",
          container: "#93000a",
        },
        success: {
          DEFAULT: "#feb127",
          glow: "#feb127",
        },
      },
      borderRadius: {
        lg: "0.5rem",
        md: "0.375rem",
        sm: "0.125rem",
        xl: "0.75rem",
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'display-lg': ['48px', { lineHeight: '56px', letterSpacing: '-0.02em', fontWeight: '700' }],
        'display-lg-mobile': ['32px', { lineHeight: '40px', letterSpacing: '-0.02em', fontWeight: '700' }],
        'headline-md': ['24px', { lineHeight: '32px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'body-lg': ['18px', { lineHeight: '28px', fontWeight: '400' }],
        'body-md': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'body-sm': ['14px', { lineHeight: '20px', fontWeight: '400' }],
        'label-caps': ['12px', { lineHeight: '16px', letterSpacing: '0.05em', fontWeight: '600' }],
        'mono-data': ['13px', { lineHeight: '18px', fontWeight: '400' }],
      },
      spacing: {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        '2xl': '48px',
        '3xl': '64px',
        'gutter': '24px',
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "pulse-cyan": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.5", transform: "scale(1.2)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "slide-in-right": {
          from: { transform: "translateX(100%)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
        "slide-in-left": {
          from: { transform: "translateX(-100%)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "pulse-cyan": "pulse-cyan 2s infinite",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-in-right": "slide-in-right 0.3s ease-out",
        "slide-in-left": "slide-in-left 0.3s ease-out",
      },
      backdropBlur: {
        glass: '12px',
      },
      boxShadow: {
        'glass': '0 0 20px rgba(0, 209, 255, 0.05)',
        'glass-hover': '0 0 20px rgba(0, 209, 255, 0.15)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
