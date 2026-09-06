# Restraint Pass Audit — Phase 3, Step 4

## Screen 1: Main Dashboard (`src/app/page.tsx`)
- **Removed (Carried No Meaning):** The generic 4-box horizontal KPI card row across the top of the screen. Merchants don't need four oversized numbers repeating what the ledger already proves; it created glance fatigue and competed with the real work.
- **The One Bold Move:** The **Primary Case Dossier** occupying the upper viewport for the single urgent claim requiring human intervention (`dp_S2`, $340 VIP fraud), giving 2× visual weight to "Authorize & Submit Counter-Evidence".
- **Everything Else Quiet:** Scenario ribbon reduced to a slim 1-line benchmark bar; secondary dispute stream housed in a disciplined, unadorned docket table.

## Screen 2: Case Dossier Detail Screen (`src/app/case/[id]/CaseDetailsClient.tsx`)
- **Removed (Carried No Meaning):** Superfluous colored status pills, glowing icons, and decorative background gradient overlays.
- **The One Bold Move:** The **Magistrate Arbitration Strategy Card** with rigorous Expected Value mathematical model and synthesized Claude 3.5 Bedrock brief.
- **Everything Else Quiet:** Carrier tracking exhibits and audit telemetry follow a clean, monochrome hairline ledger hierarchy with restrained brass accents.
