# Project: Rebuttal Merchant Console UI Hardening & Production Polish

## Architecture
The Rebuttal Merchant Console is a Next.js 14 App Router application deployed in static export mode. It communicates with Supabase (real-time Postgres changes and fallback REST polling) and an AWS Lambda endpoint for demo scenario injection.

The UI implements The Case File design system:
- **Canvas / Desk**: #EDECE6
- **Open Case File Sheet**: #FFFFFF (top ~65% viewport)
- **Docket Roster**: Ruled table of pending disputes (40px row height, excluding the currently open dispute)
- **Exhibit Inspector & Dossiers**: Deep evidence inspector revealing carrier tracking timelines, signed delivery slips, Stripe Radar risk indicators, checkout terms timestamps/IP logs, and customer communications
- **Decision Stamp**: 2px border in decision green (#14713A) or decision red (#B91C1C), rotated -2deg/-3deg, landing animation (250ms scale 1.15->1 ease-out, instant under prefers-reduced-motion)
- **Real-Time State & Resilience**: WebSocket Supabase channel with 5s polling fallback, offline/reconnecting indicator, React Error Boundary
- **Keyboard Navigation**: ArrowUp / ArrowDown roving row selection, Enter/Space activation, Esc drawer dismissal

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Carrier Tracking Timeline | Step-by-step carrier tracking events (dates, carrier, locations, delivery confirmation) | M1 | Survey R1 |
| 2 | Signed Delivery Slip | Digital/physical signature verification slip (signer name, timestamp, location) | M1 | Survey R1 |
| 3 | Stripe Radar Risk Indicators | Risk score (e.g. 12/100), 3DS authentication status, AVS match, CVC match details | M1 | Survey R1 |
| 4 | Checkout Terms Timestamp & IP | Terms acceptance timestamp, customer IP address log, consent checkbox proof | M1 | Survey R1 |
| 5 | Customer Communication Snippets | Thread history of customer emails/messages (MSG-001 through MSG-006) | M1 | Survey R1 |
| 6 | Interactive Exhibit Disclosure | Click or keyboard disclosure to inspect exhibit dossier inline or in focused sheet drawer | M1 | Survey R1 |
| 7 | Supabase Real-Time Streaming | Supabase postgres_changes channel subscription on disputes table | M1 | Survey R2 |
| 8 | Polling Fallback & Resilience | 5-second polling fallback with jitter when disconnected or streaming fails | M1 | Survey R2 |
| 9 | Connection Status Indicator | Visual indicator for online / reconnecting / offline state adhering to palette | M1 | Survey R2 |
| 10 | React Error Boundary | Next.js app error.tsx boundary preventing full UI crashes | M1 | Survey R2 |
| 11 | Stamp Landing Animation | 250ms scale(1.15 -> 1) ease-out gate-to-stamp transition | M1 | Survey R2 |
| 12 | Prefers-Reduced-Motion Override | Instant stamp appearance under prefers-reduced-motion media query | M1 | Survey R2 |
| 13 | Arrow-Key Roster Navigation | ArrowUp / ArrowDown navigation through dispute rows in CaseFeed | M1 | Survey R3 |
| 14 | Enter/Space Row Activation | Enter / Space keypress promotes focused dispute row to open case file | M1 | Survey R3 |
| 15 | Esc Key Dismissal | Esc key dismisses opened exhibit inspector / drawer and restores focus | M1 | Survey R3 |
| 16 | Strict 2px Focus Outlines | outline: 2px solid #111418; outline-offset: 2px; on all interactive elements | M1 | Survey R3 |
| 17 | WCAG AA Contrast Compliance | All typography satisfies AA contrast on both #EDECE6 and #FFFFFF surfaces | M1 | Survey R3 |
| 18 | Responsive Layout Adaptation | Desktop split view down to tablet and mobile screens | M1 | Survey R4 |
| 19 | 40px Dense Roster Rows | CaseFeed rows maintain exactly 40px height across viewports | M1 | Survey R4 |
| 20 | 1px Hairline Dividers | Hairline rules strictly #D4D4D8 between rows and sections | M1 | Survey R4 |
| 21 | 2px Top Ink Rule | 2px #111418 rule along top edge of open file sheet | M1 | Survey R4 |
| 22 | Narrative Measure Constraint | Max 75 character measure on narrative brief, zero horizontal scrollbar | M1 | Survey R4 |
| 23 | Strict Color Palette | Desk #EDECE6, Sheet #FFFFFF, Ink #111418, Secondary #5C6370, Highlighter #FFE96B, Green #14713A, Red #B91C1C | M1 | Survey R5 |
| 24 | Zero Prohibited Blue Colors | 0 instances of blue hex codes (#0000FF, #2563EB, #3B82F6, etc.) or Tailwind blue | M1 | Survey R5 |
| 25 | 0px Border Radii (Stamp 2px only) | All elements rounded-none; Stamp strictly rounded-[2px] | M1 | Survey R5 |
| 26 | Zero Cards / Shadows / Gradients | No drop shadows, box shadows, gradients, or glassmorphism blur | M1 | Survey R5 |
| 27 | Zero Emojis / Arrow Glyphs | Remove arrow character ? in CaseDetailsClient; no decorative emoji | M1 | Survey R5 |
| 28 | Sentence Case Everywhere | Strict sentence case for all headings and text; all-caps inside stamp only | M1 | Survey R5 |
| 29 | Space Grotesk & IBM Plex Mono | Space Grotesk for prose; IBM Plex Mono with tabular-nums for financial/ID | M1 | Survey R5 |
| 30 | ESLint Clean Pass | npm run lint passes with 0 errors and 0 warnings | M1 | Survey AC |
| 31 | Next.js Build Clean Pass | npm run build compiles cleanly with 0 TypeScript/layout errors | M1 | Survey AC |
| 32 | All Demo Scenarios Functional | S1 (PNR), S2 (Fraud VIP), S3 (Subscription) switch and display correctly | M1 | Survey AC |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Console UI Hardening & Production Polish | Implement all 32 features (R1-R5) across console components, ESLint, exhibits, real-time, keyboard nav, and styling | None | DONE |
| M2 | Verification, Adversarial Testing & Forensic Audit | Reviewers, Challengers, and Forensic Auditor verification pass | M1 | DONE |

## Interface Contracts
### Exhibit Inspector & Dossiers
- Input: Exhibit object with id, letter ('A', 'B', 'C'), title, stripeField, source, summary, attached (boolean), and optional dossier object.
- dossier payload types:
  - carrierTimeline: { trackingNumber: string, carrier: string, events: Array<{ timestamp: string, location: string, status: string, details?: string }> }
  - deliverySlip: { signerName: string, signatureTimestamp: string, deliveryAddress: string, signedUrl?: string }
  - 
adarIndicators: { riskScore: number, riskLevel: string, avsCheck: string, cvcCheck: string, threeDSecure: string }
  - 	ermsAcceptance: { acceptedAt: string, ipAddress: string, userAgent: string, version: string }
  - customerMessages: Array<{ id: string, sender: 'customer' | 'merchant', timestamp: string, subject?: string, body: string }>
- Action: click / Enter / Space triggers modal sheet or inline expandable drawer with focus trapped; Esc key dismisses drawer.

### Supabase Real-Time Client
- useDisputesSync hook: provides { disputes, openDispute, isReconnecting, isOffline, refresh }
- Manages supabase.channel('public:disputes') subscription with automatic fallback to 5-second polling interval when disconnected.

## Code Layout
- console/package.json: Dependencies and scripts
- console/.eslintrc.json: ESLint configuration extending next/core-web-vitals
- console/src/app/globals.css: Case File CSS tokens, stamp physics, focus outlines
- console/src/app/page.tsx: Main docket and case file view with scenario switcher
- console/src/app/case/[id]/CaseDetailsClient.tsx: Individual case details view
- console/src/app/error.tsx: Next.js Error Boundary
- console/src/components/ExhibitInspector.tsx: Interactive evidence dossier component
- console/src/components/CaseFeed.tsx: 40px row docket table with keyboard navigation
- console/src/components/Stamp.tsx: Decision stamp component
- console/src/components/Header.tsx: Scenario switcher and connection status
- console/src/lib/types.ts & console/src/lib/disputes.ts: Types, memo generator, and dossier data
