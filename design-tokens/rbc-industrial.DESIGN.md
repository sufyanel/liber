---
version: alpha
name: Mission Critical Industrial
description: "RBC Industrial: premium, service-disabled veteran-owned MRO distributor. Grounded industrial earth tones reflecting stability, machinery, and energy. Strategic Partner voice: competent, analytical, deeply knowledgeable."
colors:
  primary: "#4A352C"
  secondary: "#FED37E"
  tertiary: "#9DE3FF"
  neutral: "#181818"
  light: "#E9E8E8"
  gold-medium: "#C4A063"
  warm-gray: "#B2ADAC"
  stone-gray: "#736C69"
  bronze: "#876A47"
typography:
  h1:
    fontFamily: Montserrat
    fontSize: 3rem
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  h2:
    fontFamily: Montserrat
    fontSize: 2.25rem
    fontWeight: 700
    lineHeight: 1.2
  h3:
    fontFamily: Montserrat
    fontSize: 1.5rem
    fontWeight: 600
    lineHeight: 1.3
  body-lg:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: 400
    lineHeight: 1.8
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.8
  label:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: 600
    letterSpacing: "0.05em"
    textTransform: uppercase
rounded:
  sm: 4px
  md: 6px
  lg: 8px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  section: 80px
shadows:
  card: "0 2px 8px rgba(24, 24, 24, 0.12)"
  elevated: "0 8px 24px rgba(24, 24, 24, 0.18)"
components:
  button-primary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.neutral}"
    rounded: "{rounded.md}"
    padding: 12px 28px
    typography: "{typography.label}"
  button-primary-hover:
    backgroundColor: "{colors.gold-medium}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    rounded: "{rounded.md}"
    padding: 12px 28px
    border: "2px solid {colors.secondary}"
  card-default:
    backgroundColor: "{colors.light}"
    rounded: "{rounded.md}"
    padding: 24px
  nav-header:
    backgroundColor: "{colors.neutral}"
    textColor: "#FFFFFF"
  emergency-bar:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.secondary}"
    padding: 8px 16px
---

## Overview

RBC Industrial (historically the Roger Brown Co., est. 1946) is a premium, service-disabled veteran-owned distributor of mechanical power transmission equipment, bearings, and industrial MRO supplies. Founded by a WWII Naval Engineering Officer, the brand carries a legacy of military precision, elite technical problem-solving, and quiet dependability.

**Core slogan:** "Delivering the right product at the right time, every time."

**Value proposition:** Unlike massive broadline distributors, RBC Industrial's sales team consists entirely of trained engineers who reverse-engineer obsolete parts, optimize mechanical designs, and provide agnostic, high-performance sourcing across mechanical, hydraulic, electrical, and pneumatic systems.

**Voice persona:** Strategic Partner — competent, analytical, earnest, and deeply knowledgeable. No superficial marketing jargon. Technical clarity and executive-level precision.

## Colors

- **Primary (#4A352C — Gear Brown):** Secondary typography, structural headers, logo iconography silhouettes. Represents industrial stability and machinery.
- **Secondary (#FED37E — Rotational Gold/Amber):** Core accents, primary logo highlights, high-visibility branding components. The signature color — use sparingly for maximum impact. CTAs, active states, critical indicators.
- **Tertiary (#9DE3FF):** Cooling contrast — used for informational badges, secondary data highlights, technical callouts.
- **Neutral (#181818 — Near Black):** Footer backgrounds, strong contrast elements, dark-mode surfaces.
- **Light (#E9E8E8 — Light Gray):** Page backgrounds, clean spaces, card surfaces.
- **Gold Medium (#C4A063):** Alternative accent for premium highlights, hover states.
- **Warm Gray (#B2ADAC):** Secondary text, borders, muted UI elements.
- **Stone Gray (#736C69):** Tertiary text, placeholder copy.
- **Bronze (#876A47):** Complementary accent for depth and warmth.

## Typography

Montserrat is the headline font — bold, clean, high-impact sans-serif. Inter handles everything else: body copy, labels, data tables, UI. The pairing creates a clear hierarchy: authoritative headlines with highly readable supporting text.

- **H1–H3:** Montserrat, bold weight range (600–800), tight line-height
- **Body:** Inter Regular, 1.8 line-height for comfortable reading in long-form content
- **Labels:** Inter Semibold, uppercase, tracked wide — for certification badges, category tags, KPI labels

## Components

`button-primary` is the sole high-emphasis action. Gold on dark — unmistakable. Never use more than one per viewport section. `button-secondary` provides a transparent alt path with border.

`emergency-bar` is a signature RBC component: a thin notification bar at the top of every page with a live status indicator (pulsing red dot), announcing "LINE DOWN EMERGENCY? SAME-DAY DELIVERY." It uses Gear Brown background with Rotational Gold text.

Cards use Light Gray backgrounds with subtle shadows — never pure white on this brand.

## Brand Assets

- Logo: Industrial gear silhouette + rising sun motif
- Horizontal variant: `Logo_RBC Industrial_Horizontal.png`
- Certifications must always display: SDVOSB + Texas HUB Certified badges
- Standard contact block:
  ```
  RBC Industrial LLC
  3950 Doniphan Dr. Ste P, El Paso, Texas 79922
  Phone: 915-845-8188 | Fax: 915-845-8183
  Sales: Sales@rbc-industrial.com
  www.rbc-industrial.com
  ```