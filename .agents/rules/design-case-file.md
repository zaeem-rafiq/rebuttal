---
trigger: always_on
description: "Design System Specification: The Case File (Direction A's structure in Direction B's material)"
---

# Design System Specification — The Case File

Decision: Direction A's organisation with Direction B's material. Not a compromise — one point of view: a dispute is a case file, and the screen is that file open on the desk. The agent is the paralegal who assembled it overnight; the merchant is the one who signs. Everything on screen is evidence, a decision, or a deadline. If an element is none of those, it goes.

---

## SPEC — The Case File (Verbatim)

**Canvas and ink.** Desk `#EDECE6`; the open file is a white sheet `#FFFFFF` (the paper may be white; nothing else may be). Ink `#111418`; secondary ink `#5C6370`; rules `#D4D4D8`; strong rule = ink. Chromatic colour is reserved for meaning and appears nowhere else: highlighter `#FFE96B` behind the one line that needs the owner; decision green `#14713A` and decision red `#B91C1C` only on recorded outcomes and passed deadlines (both pass AA on desk and sheet; B's `#15803D` did not on the desk). No blue anywhere. Links are ink, underlined.

**Type.** Space Grotesk for text, labels and headings; IBM Plex Mono for ids, amounts, timestamps, tracking numbers and reason codes. Scale 14 / 17.5 / 22 / 27 / 34 / 43 (ratio 1.25). `tabular-nums` on all numbers. Letter-spacing −0.02em at 27px and above. Sentence case everywhere; all-caps exists only inside the stamp. Narrative measure ≤75 characters, line-height 1.55.

**Structure.** Rules, not cards: 1px `#D4D4D8` between rows, 1px ink under section titles, 2px ink along the top edge of the open file. No shadows, gradients, blur or textures. Radius 0, except the stamp at 2px. Density: the roster is dense (40px rows); the open file is airy enough to read.

**Anatomy of the main screen ("the docket").**
- Open file, ~65% of the viewport: case header — reason code, amount as the headline (mono, 43px), customer, order, and "Respond by <date> (<n> days)" as the second-heaviest element; the brief — the agent's narrative written as a paralegal's memo, ending in "Recommend: fight" or "Recommend: concede" with confidence; exhibits — lettered A, B, C…, each with title, the Stripe evidence field it fills (mono, secondary ink), source (Shopify order, UPS tracking, Gmail thread…), one-line summary, and attached / missing; decision block — what was texted, to whom, when, and its state.
- Roster below: every other dispute as a ruled table — id (mono), amount (mono, right-aligned), reason, agent action, outcome (small stamp), respond-by; sorted by respond-by ascending; the open case is not repeated here.
- Scenario switcher: plain text in the header's right, "Scenario: S1 · S2 · S3", active one underlined. Not a pill toolbar.

**The stamp.** One component. Bordered 2px in the decision ink, all-caps mono, rotated at most −3°, content like `FOUGHT · 06 SEP 14:07 · BY AGENT` or `APPROVED · 06 SEP 14:09 · BY OWNER (SMS)`. It appears only where a real decision was recorded. Never decorative.

**The gate — the only thing that moves.** Awaiting reply: highlighter band behind "Awaiting your reply by SMS · sent 14:02 to +1 ••• 4471". Reply received: the stamp lands (scale 1.15→1, opacity 0→1, 250ms, ease-out). No load animations, no hover-lift, no scroll effects anywhere. `prefers-reduced-motion`: the stamp appears without animating.

**Quiet state.** When nothing is gated: "Nothing needs you." at 34px, then "12 disputes handled since Sep 1 — 9 fought, 3 conceded." and the roster. The clear desk is the product's promise made visible. Loading: skeleton rows in the roster, never spinners. Focus: 2px ink outline, 2px offset, on every interactive element.

**Never.** Cards, shadows, gradients, blur, rounded corners beyond 2px, blue, icons where a word will do, emoji, "→" on buttons, all-caps outside the stamp, paper textures, perforations, barcodes, seals, brass, hover-lift, scroll animations.

---

## Derived Concrete Tokens

### 1. Palette & Surface Tokens
```css
--desk: #EDECE6;            /* Canvas background (desk surface) */
--sheet: #FFFFFF;           /* Open file sheet only (no other white elements) */
--ink: #111418;             /* Primary text, strong rules, headings, links */
--ink-secondary: #5C6370;   /* Secondary text, metadata, labels, exhibit fields */
--rule: #D4D4D8;            /* 1px hairline dividers between rows & sections */
--rule-strong: #111418;     /* 1px under section titles, 2px top edge of open file */
--highlighter: #FFE96B;     /* Gated action line background */
--decision-green: #14713A;  /* Won, approved, fought outcomes & stamps (AA compliant on desk and sheet) */
--decision-red: #B91C1C;    /* Lost, conceded, passed deadline stamps (AA compliant on desk and sheet) */
```

### 2. Typography Scale (Ratio 1.25)
- Display & Body: `Space Grotesk`, -apple-system, BlinkMacSystemFont, sans-serif
- Monospace & Numbers: `IBM Plex Mono`, Menlo, monospace
- Font sizes:
  - `text-xs`: `14px` (line-height: 20px) — metadata, labels, table data
  - `text-sm`: `17.5px` (line-height: 27px) — body copy, exhibit descriptions, brief memo
  - `text-base`: `22px` (line-height: 30px) — card subheadings, claimant names
  - `text-lg`: `27px` (line-height: 34px, letter-spacing: -0.02em) — section headers
  - `text-xl`: `34px` (line-height: 42px, letter-spacing: -0.02em) — quiet state headline
  - `text-2xl`: `43px` (line-height: 50px, letter-spacing: -0.02em) — headline amount (mono)

### 3. Rules & Radii
- All element radii: `0px` (`rounded-none`)
- Stamp radius: `2px` (`rounded-[2px]`)
- No box-shadows, no drop-shadows, no backdrop-blur
- Focus ring: `outline: 2px solid #111418; outline-offset: 2px;`

### 4. Interactive & State Guards
- Hover: text-decoration or subtle ink shift; zero translateY/hover-lift
- Gate transition: 250ms scale(1.15 -> 1), opacity(0 -> 1) ease-out stamp stamp landing; instant with `prefers-reduced-motion`
- No blue (`#0000FF`, `#2563EB`, `#3B82F6`, `#38BDF8`, etc.) permitted anywhere in markup or styles.
