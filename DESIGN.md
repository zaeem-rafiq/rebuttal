---
name: Rebuttal
description: Autonomous chargeback defense command center for independent Stripe merchants
colors:
  desk: "#EDECE6"
  sheet: "#FFFFFF"
  ink: "#111418"
  ink-secondary: "#5C6370"
  rule: "#D4D4D8"
  rule-strong: "#111418"
  highlighter: "#FFE96B"
  decision-green: "#14713A"
  decision-red: "#B91C1C"
typography:
  display:
    fontFamily: "IBM Plex Mono, Menlo, monospace"
    fontSize: "43px"
    lineHeight: 1.16
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Space Grotesk, -apple-system, sans-serif"
    fontSize: "34px"
    lineHeight: 1.24
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Space Grotesk, -apple-system, sans-serif"
    fontSize: "27px"
    lineHeight: 1.26
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Space Grotesk, -apple-system, sans-serif"
    fontSize: "17.5px"
    lineHeight: 1.55
  label:
    fontFamily: "IBM Plex Mono, Menlo, monospace"
    fontSize: "14px"
    lineHeight: 1.43
rounded:
  none: "0px"
  stamp: "2px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  stamp-approved:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.decision-green}"
    rounded: "{rounded.stamp}"
    padding: "4px 10px"
  stamp-conceded:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.decision-red}"
    rounded: "{rounded.stamp}"
    padding: "4px 10px"
  file-sheet:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "32px"
  gate-banner:
    backgroundColor: "{colors.highlighter}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "8px 12px"
---

# Design System: Rebuttal

<!-- impeccable:design-schema 1 -->

## Overview

**Creative North Star: "The Case File"**

Rebuttal rejects generic SaaS dashboards, synthetic gradients, and playful card decks. A dispute is a legal and financial case file, and the screen is that physical file open on the merchant's desk. The autonomous AI agent is the paralegal who investigated, cross-referenced orders and carrier tracking scans, and assembled the evidentiary dossier overnight; the merchant is the principal who signs off.

Everything on screen is evidence, a decision, or a deadline. If an element is none of those, it is excised. Surfaces are physical paper on a wooden desk: canvas desk (`#EDECE6`), open file sheet (`#FFFFFF`), primary ink (`#111418`), and secondary carbon ink (`#5C6370`). Hairline ruled lines structure the docket, replacing cards, elevation shadows, and artificial box boundaries.

**Key Characteristics:**
- **Canvas and Ink:** Warm paper and desk tones with strict zero-blue palette discipline.
- **Evidentiary Typography:** Dual font hierarchy pairing proportional Space Grotesk narrative text with tabular IBM Plex Mono financial and cryptographic values.
- **Physical Decision Stamps:** Rubber outcome stamps (`FOUGHT`, `APPROVED`, `CONCEDED`) replacing decorative status pills.
- **Aesthetic Restraint:** Rules instead of cards; 0px radius everywhere except 2px on stamps; zero drop shadows, blurs, or gradients.

## Colors

Chromatic color is strictly reserved for meaning and appears nowhere else in the interface.

### Primary
- **Primary Ink** (`#111418`): Used for primary headlines, claimant names, strong rules, link text, and the top anchor edge of the open dossier.
- **Secondary Ink** (`#5C6370`): Metadata labels, Stripe evidence field mapping keys, timestamps, and exhibit sources.

### Neutral
- **Desk Surface** (`#EDECE6`): Canvas background representing the physical desk upon which the dossier rests.
- **File Sheet** (`#FFFFFF`): Reserved exclusively for the open case file sheet. No other surface or container may be pure white.
- **Divider Rule** (`#D4D4D8`): 1px hairline horizontal rules separating docket table rows and exhibit items.
- **Strong Rule** (`#111418`): 1px rule under section titles and 2px rule anchoring the top edge of the open sheet.

### Semantic
- **Action Highlighter** (`#FFE96B`): Applied as a background highlighter band behind the single pending action line awaiting merchant input.
- **Decision Green** (`#14713A`): Recorded wins, evidence submissions, and approvals. Passes WCAG AA contrast against both desk and sheet.
- **Decision Red** (`#B91C1C`): Recorded losses, conceded disputes, and passed deadlines. Passes WCAG AA contrast against both desk and sheet.

### Named Rules
**The No-Blue Rule.** Zero blue permitted anywhere in the system (`#0000FF`, `#2563EB`, `#3B82F6`, `#38BDF8`). Links are primary ink (`#111418`) and underlined with a 3px text offset.

**The Chromatic Meaning Rule.** Chromatic color may only signify a human-in-the-loop gate (`#FFE96B`) or a verified financial outcome (`#14713A`, `#B91C1C`). It is never decorative.

## Typography

**Display/Headline Font:** Space Grotesk (with system sans fallback)  
**Body Font:** Space Grotesk (with system sans fallback)  
**Label/Mono Font:** IBM Plex Mono (with Menlo, monospace fallback)

**Character:** High-contrast editorial clarity meeting rigorous evidentiary record-keeping. Narrative briefs read as formal paralegal memoranda, while all IDs, monetary sums, tracking numbers, and timestamps are rendered in tabular monospace.

### Hierarchy
- **Display Amount** (IBM Plex Mono, Bold, `43px`, line-height `50px`, letter-spacing `-0.02em`): The headline dispute amount at the top of the open case file.
- **Headline Title** (Space Grotesk, Regular, `34px`, line-height `42px`, letter-spacing `-0.02em`): Quiet state headline ("Nothing needs you.").
- **Section Title** (Space Grotesk, Medium, `27px`, line-height `34px`, letter-spacing `-0.02em`): Major section titles and brand heading.
- **Subheading / Name** (Space Grotesk, Medium, `22px`, line-height `30px`): Customer claimant name and key landmark subtitles.
- **Body / Brief** (Space Grotesk, Regular, `17.5px`, line-height `27px`): Case memo narrative, exhibit summaries, and explanatory copy. Narrative measure is constrained to $\le 75$ characters.
- **Label / Metadata** (IBM Plex Mono, Regular, `14px`, line-height `20px`): Dispute IDs, reason codes, respond-by countdowns, table metadata.

### Named Rules
**The Tabular Numbers Rule.** All monetary amounts, dates, percentages, and tracking numbers must enable tabular numerals (`tabular-nums` / `tnum`) to ensure perfect vertical alignment across docket rows.

**The Sentence Case Rule.** Sentence case is enforced everywhere across headings, labels, and descriptions. All-caps exists exclusively inside the rubber decision stamps.

## Layout

The interface is divided into the active open dossier and the historical docket table:

- **The Open Case File (~65% Viewport):** A pure white sheet (`#FFFFFF`) with a 2px ink top edge sitting on the desk canvas. Contains the case header, headline monetary amount, respond-by deadline, the agent's paralegal brief, lettered evidentiary exhibits (A, B, C...), and the SMS approval block.
- **The Docket Roster:** Positioned below the open file. A dense ruled table (40px row height) listing every other dispute sorted by respond-by ascending. The currently open case is not duplicated in the roster.
- **Scenario Switcher:** Positioned in the header's right corner as plain text (`Scenario: S1 · S2 · S3`) with the active item underlined. Never rendered as a pill toolbar or segmented button.
- **Quiet State:** When no disputes are gated or require merchant intervention, the open file recedes, displaying the quiet headline `"Nothing needs you."` followed by aggregate resolution metrics and the historical docket table.

## Elevation & Depth

Rebuttal employs zero drop shadows, zero box shadows, zero backdrop blur, and zero elevation gradients.

Depth is communicated entirely through material and tonal contrast: the white sheet (`#FFFFFF`) layered directly over the desk canvas (`#EDECE6`), anchored by hairline and 2px solid ink structural rules.

### Named Rules
**The Flat-Paper Rule.** Surfaces are strictly flat. Interactive elements never lift, translate in Y-space, or cast shadows on hover. Focus is designated solely by a `2px solid #111418` outline with `2px offset`.

## Shapes

- **All Elements:** Border radius is strictly `0px` (`rounded-none`). No rounded cards, badges, inputs, or containers.
- **The Stamp Exception:** The rubber decision stamp is the sole element permitted a border radius: `2px` (`rounded-[2px]`).

## Components

### The Open File Sheet
- **Shape:** Rectangular sheet, `0px` radius, `border-t-2 border-[#111418]`.
- **Background:** Sheet white (`#FFFFFF`) on desk (`#EDECE6`).
- **Internal Padding:** `p-6 sm:p-8`.

### The Decision Stamp
- **Shape:** `rounded-[2px]` with a `2px` solid border in decision green (`#14713A`), decision red (`#B91C1C`), or ink (`#111418`).
- **Typography:** IBM Plex Mono, bold, all-caps, tracking-wider, rotated at $-2^\circ$ to $-3^\circ$.
- **Content Format:** `[ACTION] · [DD MMM HH:MM] · BY [ACTOR] ([CHANNEL])` (e.g. `FOUGHT · 06 SEP 14:07 · BY AGENT` or `APPROVED · 06 SEP 14:09 · BY OWNER (SMS)`).
- **Semantics:** Appears only when an immutable, real-world decision has been executed. Never decorative.

### The Gate (Action Line)
- **Visual:** Background highlighter band (`#FFE96B`) behind the active instruction: `"Awaiting your reply by SMS · sent 14:02 to +1 ••• 4471"`.
- **Motion:** When the merchant replies, the stamp lands over the gate (`scale(1.15) -> scale(1)`, `opacity(0) -> opacity(1)`, `250ms ease-out`). This is the only animated transition in the application.

### Evidentiary Exhibits
- **Structure:** Lettered sequentially (`Exhibit A`, `Exhibit B`, `Exhibit C`...).
- **Content:** Title, Stripe evidence field mapping (IBM Plex Mono, secondary ink), source system (Shopify, UPS, Gmail, Stripe Radar), one-line factual summary, and attachment status (`attached` or `missing`).

### The Docket Table
- **Density:** 40px row height separated by 1px hairline rules (`#D4D4D8`).
- **Columns:** Dispute ID (mono), Amount (mono, right-aligned), Reason Code, Agent Action, Outcome Stamp, Respond-by date.

## Do's and Don'ts

### Do:
- **Do** keep the canvas background strictly desk `#EDECE6` and the open file strictly sheet `#FFFFFF`.
- **Do** use IBM Plex Mono for all amounts, timestamps, IDs, tracking numbers, and reason codes with `tabular-nums`.
- **Do** keep all element radii at `0px` except the decision stamp at `2px`.
- **Do** limit chromatic color strictly to highlighter `#FFE96B`, decision green `#14713A`, and decision red `#B91C1C`.
- **Do** format the decision stamp with verified timestamp and actor provenance (e.g. `· BY AGENT`, `· BY OWNER (SMS)`).
- **Do** provide skeleton loading rows in the docket rather than spinning wheels.

### Don't:
- **Don't** use blue anywhere in the interface (`#0000FF`, `#2563EB`, `#3B82F6`, etc.). Links are ink and underlined.
- **Don't** use cards, drop shadows, box shadows, gradients, or backdrop blur.
- **Don't** use icons where plain words will do.
- **Don't** use emoji or "→" on buttons and links.
- **Don't** use all-caps text outside of the rubber stamp.
- **Don't** introduce hover-lift (`translateY`) or page scroll animations.
- **Don't** add artificial paper textures, skeuomorphic brass fasteners, perforations, or barcodes.
