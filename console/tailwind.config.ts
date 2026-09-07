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
        desk: "#EDECE6",
        sheet: "#FFFFFF",
        ink: {
          DEFAULT: "#111418",
          secondary: "#5C6370",
        },
        "secondary-ink": "#5C6370",
        rule: {
          DEFAULT: "#D4D4D8",
          strong: "#111418",
        },
        highlighter: {
          DEFAULT: "#FFE96B",
        },
        decision: {
          green: "#14713A",
          red: "#B91C1C",
        },
      },
      fontSize: {
        xs: ["14px", { lineHeight: "20px" }],
        sm: ["17.5px", { lineHeight: "27px" }],
        base: ["17.5px", { lineHeight: "27px" }],
        md: ["22px", { lineHeight: "30px" }],
        lg: ["27px", { lineHeight: "34px", letterSpacing: "-0.02em" }],
        xl: ["34px", { lineHeight: "42px", letterSpacing: "-0.02em" }],
        "2xl": ["43px", { lineHeight: "50px", letterSpacing: "-0.02em" }],
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Space Grotesk", "-apple-system", "sans-serif"],
        mono: ["var(--font-mono)", "IBM Plex Mono", "Courier", "monospace"],
      },
      borderRadius: {
        none: "0px",
        DEFAULT: "0px",
        xs: "0px",
        sm: "0px",
        md: "0px",
        lg: "0px",
        xl: "0px",
        full: "0px",
        stamp: "2px",
      },
      boxShadow: {
        none: "none",
        xs: "none",
        sm: "none",
        DEFAULT: "none",
        md: "none",
        lg: "none",
        xl: "none",
        "2xl": "none",
      },
    },
  },
  plugins: [],
};
export default config;
