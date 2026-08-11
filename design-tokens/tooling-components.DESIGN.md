---
version: alpha
name: Forged & Molded
description: "Tooling Components: the premier partner for heavy-duty manufacturing. Modular tooling solutions bridging raw physical force with high-precision engineering. Authoritative, technical, grounded voice. 60-30-10 color rule."
colors:
  primary: "#1A1A24"
  secondary: "#D5CABD"
  accent: "#E65F2B"
  neutral: "#F8F9FA"
typography:
  h1:
    fontFamily: Barlow Condensed
    fontSize: 3.5rem
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "0.05em"
    textTransform: uppercase
  h2:
    fontFamily: Barlow Condensed
    fontSize: 2.25rem
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "0.03em"
    textTransform: uppercase
  h3:
    fontFamily: Inter
    fontSize: 1.25rem
    fontWeight: 600
    lineHeight: 1.3
  subheading:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 500
    lineHeight: 1.4
    textTransform: uppercase
    letterSpacing: "0.1em"
  body-lg:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: 400
    lineHeight: 1.7
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.6
  data:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: 500
    lineHeight: 1.4
  label:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: 600
    letterSpacing: "0.08em"
    textTransform: uppercase
rounded:
  sm: 2px
  md: 4px
  lg: 6px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 32px
  xl: 48px
  section: 80px
shadows:
  card: "0 1px 4px rgba(26, 26, 36, 0.12)"
  elevated: "0 4px 16px rgba(26, 26, 36, 0.18)"
  heavy: "0 8px 32px rgba(26, 26, 36, 0.25)"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 14px 32px
    typography: "{typography.subheading}"
  button-primary-hover:
    backgroundColor: "#CC4F1E"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 14px 32px
    border: "1.5px solid {colors.primary}"
  card-product:
    backgroundColor: "#FFFFFF"
    rounded: "{rounded.md}"
    border: "1px solid {colors.secondary}"
    padding: 20px
  nav-header:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
  status-ready:
    backgroundColor: "#E8F5E9"
    textColor: "#2E7D32"
    rounded: "{rounded.sm}"
    padding: 2px 8px
    typography: "{typography.label}"
  status-low:
    backgroundColor: "#FFF3E0"
    textColor: "{colors.accent}"
    rounded: "{rounded.sm}"
    padding: 2px 8px
    typography: "{typography.label}"
  data-table:
    backgroundColor: "{colors.neutral}"
    rounded: "{rounded.md}"
    border: "1px solid {colors.secondary}"
---

## Overview

Tooling Components is the premier partner for heavy-duty manufacturing, providing modular tooling solutions that bridge raw physical force with high-precision engineering. The identity is built on structural durability, process-driven excellence, and an unwavering commitment to industrial progress.

**Brand pillars:**
- **Trust & Heavy-Duty Reliability:** Components designed to withstand extreme stress, heavy cycles, and unforgiving industrial environments.
- **Precision Engineering:** Micrometric tolerances ensuring modular compatibility across complex assemblies.
- **Energy & Innovation:** Raw manufacturing energy (forging, molding, casting) integrated with smart, digital-first management systems.

**Voice:** Authoritative, technical, grounded. Speak directly to engineers, plant managers, and procurement officers. Use industry-standard technical terms. Emphasize durability and efficiency metrics. Never use flowery language or casual slang.

**Core theme:** "Forged & Molded" — process-driven, robust tooling partner.

## Colors

The brand operates on a strict **60-30-10 Rule:**

- **Primary (#1A1A24 — Dark Gunmetal, 60%):** The foundation. Primary text, structural layouts, navigation, footer. Represents the weight, raw strength, and industrial integrity of tooling solutions.
- **Secondary (#D5CABD — Industrial Sand, 30%):** The sophisticated neutral. Subheadings, container backgrounds, section dividers. Represents unworked raw materials, concrete industrial floors, precision-milled surfaces.
- **Accent (#E65F2B — Molten Amber, 10%):** Extreme heat, raw kinetic force, the energy of the forge. Used exclusively to guide attention — buttons, alerts, key specs, active states, safety-critical elements. Never use for body text or large surfaces.
- **Neutral (#F8F9FA — Alabaster):** Clean backdrop for crisp contrast against dark typography. Prevents muddy tones in technical manuals and digital dashboards.

## Typography

Two-font system with clear hierarchy:

- **Barlow Condensed:** All headings (H1, H2). All caps, bold, tracked wide (+50 to +100). Solid geometric structure. Communicates industrial authority from the first glance.
- **Inter:** Everything else — body, data tables, labels, UI. Clean, unobstructed letterforms for technical legibility. Regular for body, Semibold for labels/UI, Medium for data.

Headings are always Dark Gunmetal on Alabaster, or inverted (Alabaster on Dark Gunmetal) for dark sections.

## Shapes & Surfaces

- **Sharp corners** (2–4px radius) — machined precision, not consumer-soft. No pill shapes.
- **Hard borders** (1–1.5px) on cards and data tables using Industrial Sand.
- **Flat surfaces** — no gradients, no glassmorphism. Tonal depth over soft shadows.
- **Grid overlay:** 32px grid at #1A1A2405 on technical pages — subtle reference to engineering blueprints.

## Components

`button-primary` is the sole high-emphasis action. Molten Amber on white — it demands attention. Exactly one per viewport section.

`card-product` uses a hard Industrial Sand border with clean white fill — like a precision-machined part sitting on a workbench. Specs displayed in Inter Medium with metric precision formatting.

`status-ready` and `status-low` are stock-status badges used on product cards and data tables. Green for ready-to-ship, amber for low stock — immediate visual triage for procurement officers.

`data-table` is the signature TC component: dense technical tables with Alabaster backgrounds, Industrial Sand borders, and Dark Gunmetal data. Stock status badges provide instant scanability. This is the McMaster-Carr pattern adapted for tooling components.

## Brand Assets

- Logo: Stylized geometric monogram representing interlocking tooling blocks/forging paths with clean bold typography
- Color variants: Full color (Dark Gunmetal + Molten Amber on Alabaster), Inverted (Molten Amber on Dark Gunmetal), Monochrome (solid for engraving)
- Clear space: Equal to the height of the letter "N" in the logo badge
- Contact:
  ```
  Tooling Components LLC
  8349 West High St., Union City, PA 16438
  Phone: 814-438-7657
  Email: sales@toolingcomponent.com
  ```