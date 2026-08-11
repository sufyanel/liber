# Odoo Liber — Axiom Design Handoff

Design specifications, brand tokens, mockups, and Odoo theme module for the Liber Holdings website redesign. **Brand colors now applied — Axiom pulls and deploys.**

**Subsidiaries:** RBC Industrial | Tooling Components

---

## Repo Structure

```
├── design-tokens/              # Machine-readable brand specs (DESIGN.md format)
│   ├── rbc-industrial.DESIGN.md
│   └── tooling-components.DESIGN.md
├── mockups/                    # Visual design references
│   ├── rbc-industrial/
│   │   └── blog-listing.html          # Brand-correct HTML — open in any browser
│   ├── tooling-components/
│   │   ├── blog-listing.html          # Brand-correct HTML — open in any browser
│   │   ├── bordignon-springs-landing.html
│   │   ├── ejector_pins_landing.html
│   │   └── leader_pins_bushings_landing.html
│   └── sketches/                      # Original design exploration (generic navy — reference only)
├── odoo-theme-module/          # Odoo v17 theme module (brand colors applied)
│   └── liber_website_theme/    # SCSS with CSS custom properties per website
├── DESIGN_REQUIREMENTS.md      # Original design brief & research sources
├── Liber-Website-Design-Research-and-Decisions.html
└── README.md
```

---

## Brand Summary

| | RBC Industrial | Tooling Components |
|---|---|---|
| **Domain** | rbc-industrial.com | toolingcomponent.com |
| **Theme** | Mission Critical Industrial | Forged & Molded |
| **Primary** | Gear Brown `#4A352C` | Dark Gunmetal `#1A1A24` |
| **Accent** | Rotational Gold `#FED37E` | Molten Amber `#E65F2B` |
| **Headings** | Montserrat (bold) | Barlow Condensed (all caps) |
| **Body** | Inter | Inter |
| **Odoo website_id** | 4 | 3 |

---

## How the Theme Module Works

The theme uses **CSS custom properties** scoped to Odoo's per-website body classes:

```scss
// Tooling Components — .o_website_3
.o_website_3 {
    --brand-primary: #1A1A24;     // Dark Gunmetal
    --brand-accent: #E65F2B;      // Molten Amber
    --font-heading: 'Barlow Condensed', sans-serif;
}

// RBC Industrial — .o_website_4
.o_website_4 {
    --brand-primary: #4A352C;     // Gear Brown
    --brand-accent: #FED37E;      // Rotational Gold
    --font-heading: 'Montserrat', sans-serif;
}
```

All components (_blog, _components, _typography) reference these variables — no hardcoded colors. One theme module serves both brands.

### Brand-specific features baked into SCSS:

**RBC Industrial (`.o_website_4`):**
- Emergency notification bar (Gear Brown bg, Rotational Gold text, pulsing red status dot)
- SDVOSB + Texas HUB certification badges
- Gold CTA buttons with dark text
- Montserrat 800-weight H1s

**Tooling Components (`.o_website_3`):**
- All-caps Barlow Condensed headings with wide tracking
- Stock status badges (READY TO SHIP / LOW STOCK)
- Hard 1px Industrial Sand borders on all cards
- Molten Amber CTAs on white

---

## HTML Mockups — Visual Verification

Open these in any browser to see the finished design direction:

- `mockups/tooling-components/blog-listing.html` — TC blog grid with stock badges, Barlow Condensed headings
- `mockups/rbc-industrial/blog-listing.html` — RBC blog grid with emergency bar, Montserrat headings, gold CTAs

These are standalone files using the exact same CSS custom property tokens as the Odoo theme module.

---

## What Axiom Needs to Do

1. **Deploy via Odoo.sh** — add this repo as a submodule per Odoo.sh submodule workflow
2. **Install theme module** — Apps → search "Liber Website Theme" → Install
3. **Verify per-website switching** — check `.o_website_3` (TC) and `.o_website_4` (RBC) render correctly
4. **Product page templates** (out of scope for this module) — the theme covers blog listing + blog post detail. Product catalog pages need separate template work.

---

## Source Designs (Google Stitch)
- **RBC Industrial:** [stitch.withgoogle.com/projects/1201256666952181348](https://stitch.withgoogle.com/projects/1201256666952181348)
- **Tooling Components:** [stitch.withgoogle.com/projects/10822840095499997532](https://stitch.withgoogle.com/projects/10822840095499997532)

## Technical Notes
- **Odoo version:** 17 (community + website_blog)
- **SCSS bundles:** Odoo variables (`primary_variables.scss`) and Bootstrap overrides (`bootstrap_overridden.scss`) must remain in separate bundles
- **Template IDs:** Blog list = `website_blog.blog_post_short`, Blog detail = `website_blog.blog_post_complete`
- **No wildcards** in `__manifest__.py` — Odoo.sh requires explicit file listing