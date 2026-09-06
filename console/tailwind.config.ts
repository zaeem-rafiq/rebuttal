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
        canvas: "#0A0D12",
        docket: {
          gold: "#D4A359",
          "gold-light": "#E5B86E",
          "gold-subtle": "rgba(212, 163, 89, 0.12)",
          "gold-border": "rgba(212, 163, 89, 0.35)",
          text: "#F5F2EC",
          "text-secondary": "#C5CBD3",
          "text-muted": "#8C96A5",
          "text-subtle": "#64748B",
        },
        surface: {
          DEFAULT: "#121820",
          elevated: "#18202A",
          highlight: "#1E2836",
          hover: "#1C2533",
          subtle: "#0E131A",
          plaque: "#11161D",
        },
        border: {
          DEFAULT: "#232D3B",
          subtle: "#1A222D",
          strong: "#334155",
          brass: "#D4A359",
        },
        status: {
          won: "#10B981",
          "won-subtle": "rgba(16, 185, 129, 0.12)",
          "won-border": "rgba(16, 185, 129, 0.3)",
          pending: "#F59E0B",
          "pending-subtle": "rgba(245, 158, 11, 0.12)",
          "pending-border": "rgba(245, 158, 11, 0.3)",
          action: "#EF4444",
          "action-subtle": "rgba(239, 68, 68, 0.12)",
          "action-border": "rgba(239, 68, 68, 0.3)",
          conceded: "#94A3B8",
          "conceded-subtle": "rgba(148, 163, 184, 0.12)",
          "conceded-border": "rgba(148, 163, 184, 0.3)",
          inquiry: "#EAB308",
          "inquiry-subtle": "rgba(234, 179, 8, 0.12)",
          "inquiry-border": "rgba(234, 179, 8, 0.3)",
          review: "#38BDF8",
          "review-subtle": "rgba(56, 189, 248, 0.12)",
          "review-border": "rgba(56, 189, 248, 0.3)",
        },
      },
      borderRadius: {
        none: "0px",
        xs: "1px",
        sm: "2px",
        DEFAULT: "3px",
        md: "4px",
        lg: "6px",
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Newsreader", "Georgia", "serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
        sans: ["var(--font-sans)", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
