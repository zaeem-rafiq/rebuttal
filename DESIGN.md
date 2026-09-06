---
name: Rebuttal
description: Autonomous chargeback defense command center for independent Stripe merchants
colors:
  canvas: "#090a0f"
  surface: "#0f172a"
  surface-hover: "#1e293b"
  border-default: "#1e293b"
  border-subtle: "rgba(51, 65, 85, 0.4)"
  text-primary: "#f8fafc"
  text-secondary: "#94a3b8"
  text-muted: "#64748b"
  accent: "#6366f1"
  accent-subtle: "rgba(99, 102, 241, 0.12)"
  status-won: "#10b981"
  status-won-bg: "rgba(6, 78, 59, 0.4)"
  status-pending: "#f59e0b"
  status-pending-bg: "rgba(120, 53, 15, 0.4)"
  status-conceded: "#f43f5e"
  status-conceded-bg: "rgba(136, 19, 55, 0.4)"
  status-inquiry: "#eab308"
  status-inquiry-bg: "rgba(113, 63, 18, 0.4)"
typography:
  fontFamily:
    sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    mono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace'
  scale:
    h1: "24px"
    h2: "18px"
    body: "14px"
    caption: "12px"
    micro: "10px"
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xl}"
    padding: "20px"
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
  status-chip:
    rounded: "{rounded.pill}"
    padding: "2px 10px"
---

# Design System

<!-- impeccable:design-schema 1 -->

## Overview

Rebuttal's visual design system communicates institutional financial authority, speed, and algorithmic rigor. Built for small merchants under dispute stress, the interface balances clear automated actions with high-contrast evidentiary proof.

The visual language eschews generic SaaS decoration in favor of dense, information-rich risk surfaces: dark canvas grounding, monospaced financial figures, unambiguous status indicators, and clear distinction between autonomous agent acts and human-in-the-loop decisions.

## Colors

The color palette is built on a high-contrast dark theme optimized for sustained monitoring and alert legibility.

### Canvas & Surfaces
- **Canvas (`#090a0f`):** Ultra-dark slate background providing high-contrast separation for cards and modals.
- **Surface (`#0f172a` · `slate-900`):** Primary card and panel surface, rendered with 80-90% opacity and subtle backdrop blur.
- **Surface Elevated (`#1e293b` · `slate-800`):** Hover states, input backgrounds, and sub-card containers.
- **Borders (`#1e293b` / `rgba(51, 65, 85, 0.8)`):** Structural hairline borders delineating cards, tables, and headers.

### Text Hierarchy
- **Text Primary (`#f8fafc` · `slate-50`):** High-contrast headlines, monetary values, and active dispute IDs.
- **Text Secondary (`#94a3b8` · `slate-400`):** Descriptions, labels, and timestamps.
- **Text Muted (`#64748b` · `slate-500`):** Inactive meta tags, breadcrumbs, and placeholder copy.

### Semantic Status Indicators
- **Won / Protected (`#10b981` · `emerald-400`):** Successfully defended disputes and confirmed carrier delivery receipts.
- **Pending / Action Needed (`#f59e0b` · `amber-400`):** Paused at ApprovalGate or awaiting merchant intervention.
- **Conceded / Lost (`#f43f5e` · `rose-400`):** Voluntarily conceded disputes (to protect VIP relationships) or lost chargebacks.
- **Inquiry / Pre-dispute (`#eab308` · `yellow-400`):** Early cancellation or fraud inquiries resolved prior to formal dispute filing.

## Typography

Typography prioritizes fast numerical parsing and clear evidentiary hierarchy.

- **Body & Headings:** System sans-serif stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`). Clean, legible, with zero web-font rendering latency.
- **Monospace Elements:** Monospace font stack (`ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`) applied to:
  - Dispute IDs (`dp_S1`, `du_1UCchu...`)
  - Order numbers (`ORD-1001`)
  - Monetary values and cents calculations (`$48.00`, `22%`)
  - Tracking numbers and cryptographic hashes
  - Telemetry timestamps and audit log JSON payloads

### Typographic Hierarchy
- **Level 1 (Console Title):** `text-xl font-bold tracking-tight text-white`
- **Level 2 (Section Headers):** `text-sm font-semibold uppercase tracking-wider text-slate-300`
- **Level 3 (Card Titles):** `text-base font-semibold text-slate-200`
- **Body Text:** `text-xs leading-relaxed text-slate-300`
- **Badges & Meta:** `text-[11px] font-medium`

## Layout

- **Container:** Centered max-width container (`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6`).
- **Metric Banners:** 4-column responsive grid (`grid-cols-2 lg:grid-cols-4 gap-4`) summarizing total disputes, win rate, protected revenue, and pending actions.
- **Case Detail View:** Split-screen layout:
  - **Left Column (Primary):** Strategy Card, Case Feed, Evidence Packet, and Audit Timeline.
  - **Right Column (Simulation):** Fixed-width mobile chassis container (`max-w-[340px]`) displaying the interactive two-way SMS approval stream.
- **Rhythm:** Consistent vertical rhythm using `space-y-6` between major landmarks and `space-y-3` inside card clusters.

## Elevation & Depth

- **Depth Strategy:** Tonal elevation rather than heavy drop shadows. Layering proceeds from `#090a0f` (page body) -> `#0f172a` (card container) -> `#020617` (code blocks and audit payloads).
- **Edge Definition:** Hairline 1px border (`border-slate-800/80`) on all container cards to maintain sharp boundary definition on OLED and high-DPI screens.
- **Vignette:** Fixed radial background gradient (`bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.12),rgba(255,255,255,0))]`) provides atmospheric depth without impeding contrast.

## Shapes

- **Containers:** `rounded-2xl` (16px) for major cards, scenario toolbar, and feed wrappers.
- **Interactive Controls:** `rounded-xl` (12px) for primary buttons, input fields, and metric cards.
- **Badges & Chips:** `rounded-full` pills (`px-2.5 py-1 text-xs`) for status chips.
- **Phone Hardware Simulation:** `rounded-[44px]` chassis with `rounded-[34px]` inner display screen and centered dynamic island notch.

## Components

### 1. Header (`Header.tsx`)
- Displays project branding, active environment pill ("Judge Console"), and live agent status indicator ("AgentCore Live" with pulsing green LED).
- Displays real-time polling countdown (`Polling: Xs`) and manual refresh action with spin feedback.

### 2. Scenario Injector (`InjectToolbar.tsx`)
- Controls for triggering automated end-to-end test scenarios (`S1 Delivery`, `S2 Fraud`, `S3 Inquiry`).
- Manages 60-second cooldown states with visual countdown badges and inline execution feedback banners.

### 3. Status Chip (`StatusChip.tsx`)
- Normalized pill badges combining Lucide icons (`CheckCircle2`, `AlertTriangle`, `XCircle`, `Clock`) with semantic background tints.

### 4. Strategy Card (`StrategyCard.tsx`)
- Displays Bedrock AgentCore multi-agent synthesis: Recommended Action, Customer Tier, Win Probability meter, Expected Value, and Executive Summary.

### 5. Simulated Phone (`SimulatedPhone.tsx`)
- Interactive smartphone mockup showcasing the Twilio SMS human-in-the-loop approval workflow.
- Supports instant one-tap quick replies (`1 Fight`, `2 Concede`, `3 Hold`) and custom text input dispatched directly to webhook handlers.

### 6. Evidence Packet (`EvidencePacket.tsx`)
- Evidentiary dossier displaying linked orders, customer profiles, line items, carrier tracking numbers, and verified delivery signatures.

### 7. Audit Timeline (`AuditTimeline.tsx`)
- Chronological, vertical timeline tracking every agent tool call, Stripe webhook, SMS dispatch, and Bedrock AgentCore memory update with expandable JSON payloads.

## Do's and Don'ts

### Do's
- **DO** use monospaced fonts for all currencies, IDs, tracking numbers, and timestamps.
- **DO** maintain strict WCAG AA contrast (≥ 4.5:1 for body copy against `#090a0f` and `#0f172a`).
- **DO** keep semantic status colors consistent across all cards, chips, and phone alert bubbles.
- **DO** ensure touch targets on mobile and the phone chassis meet minimum 44x44px requirements.
- **DO** preserve instant feedback states during API interactions (spinners, countdowns, and alert banners).

### Don'ts
- **DON'T** use generic AI purple/violet/pink gradient backgrounds on buttons and cards.
- **DON'T** use low-contrast gray text (`text-slate-500` or `text-slate-600`) on dark canvas for readable labels.
- **DON'T** hide evidence or decision rationale behind opaque, unexplained AI scores.
- **DON'T** introduce heavy animations that fail to respect `prefers-reduced-motion`.
- **DON'T** disrupt the 3-scenario toolbar (S1, S2, S3) or simulated phone interactive fixtures.
