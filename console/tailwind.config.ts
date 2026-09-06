import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#0b0f17",
        surface: {
          DEFAULT: "#111827",
          elevated: "#161f30",
          highlight: "#1a2436",
          hover: "#1e293b",
          subtle: "#0d131f",
        },
        border: {
          DEFAULT: "#1f2937",
          subtle: "#161e2e",
          strong: "#374151",
        },
        brand: {
          DEFAULT: "#2563eb",
          hover: "#1d4ed8",
          subtle: "rgba(37, 99, 235, 0.12)",
          border: "rgba(37, 99, 235, 0.35)",
        },
        status: {
          won: "#10b981",
          "won-subtle": "rgba(16, 185, 129, 0.12)",
          "won-border": "rgba(16, 185, 129, 0.3)",
          pending: "#f59e0b",
          "pending-subtle": "rgba(245, 158, 11, 0.12)",
          "pending-border": "rgba(245, 158, 11, 0.3)",
          action: "#f43f5e",
          "action-subtle": "rgba(244, 63, 94, 0.12)",
          "action-border": "rgba(244, 63, 94, 0.3)",
          inquiry: "#eab308",
          "inquiry-subtle": "rgba(234, 179, 8, 0.12)",
          "inquiry-border": "rgba(234, 179, 8, 0.3)",
          review: "#38bdf8",
          "review-subtle": "rgba(56, 189, 248, 0.12)",
          "review-border": "rgba(56, 189, 248, 0.3)",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
