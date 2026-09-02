# Liber Website Theme — Design Requirements & Sources

## Overview
Custom Odoo v17 theme module for Liber Holdings subsidiaries (ToolingComponents, RBC Industrial, Globe Electric). B2B/industrial aesthetic — clarity over cleverness, grid-based information architecture, content-oriented layout, trust signals throughout.

---

## Design Principles (from Requirement Analysis)

| Principle | Implementation | Rationale |
|-----------|---------------|-----------|
| **Clarity over cleverness** | Bold headings, clean card layouts, immediate value prop per page | B2B buyers decide on trust + clarity, not flash |
| **Grid-based IA** | CSS Grid blog cards (3-col, responsive), consistent card dimensions | Engineers & procurement compare specs fast |
| **Content-oriented design** | 720px centered reading column, 1.8 line-height, generous margins | Blog posts tell a story, not fill a template |
| **Trust signals everywhere** | Author credentials, certifications, breadcrumbs with JSON-LD schema | Industrial buyers de-risk at every touchpoint |

## Target Visual Aesthetic

**Industrial editorial** — inspired by industrial B2B leaders:
- Deep navy primary (#1a3c5e) — conveys trust, stability
- Clean whitespace with light gray (#f0f2f5) card backgrounds
- Inter font family (300–700 weight range)
- 6px border radius on cards (not too sharp, not too round)
- 600px × 400px locked aspect ratio on blog cover images (3:2)
- Subtle shadows (0 2px 8px rgba(0,0,0,0.08)) on cards

## Color Palette

```scss
// Primary CTAs — deep industrial blue
'o-color-1': #1a3c5e
// Secondary actions — muted utilitarian gray
'o-color-2': #6c757d
// Light backgrounds, card borders
'o-color-3': #f0f2f5
// White — clean space
'o-color-4': #ffffff
// Text — deep charcoal for contrast
'o-color-5': #1a1a2e
```

## Typography

| Element | Spec |
|---------|------|
| Body font | Inter (variable), fallback -apple-system |
| H1 | 2.5rem / 700 weight |
| H2 | 2rem / 600 weight |
| H3 | 1.5rem / 600 weight |
| Body | 1rem / 400 weight, 1.8 line-height |
| Lead | 1.1rem / text-muted |
| Small | 0.875rem / text-muted |

## SCSS Bundle Architecture (Odoo v17 Critical)

**Three separate bundles — never mix Odoo and Bootstrap variables:**

| Bundle | File | Purpose |
|--------|------|---------|
| `web._assets_primary_variables` | `primary_variables.scss` | Odoo color palette, theme fonts, heading sizes |
| `web._assets_frontend_helpers` | `bootstrap_overridden.scss` | Bootstrap $font-size-base, $spacer, $container-max-widths, $border-radius, $btn-padding |
| `web.assets_frontend` | `_blog.scss`, `_typography.scss`, `_components.scss`, `style.scss`, `theme.js` | Custom component styles + JS |

## Template Overrides

### Blog List Page (`blog_list_template.xml`)
- Inherits: `website_blog.blog_post_short`
- Full replacement of blog post list container
- CSS Grid system: 1-col mobile → 2-col tablet → 3-col desktop
- Card component per post with:
  - Fixed 3:2 aspect ratio cover image (600×400)
  - Category badge tags
  - Title as stretched link
  - Teaser excerpt
  - Author name + published date row
  - Subtle hover lift: translateY(-2px) + shadow enhancement

### Blog Post Detail (`blog_post_template.xml`)
- Inherits: `website_blog.blog_post_complete`
- Centered reading column locked at 720px max-width
- Breadcrumb trail with JSON-LD schema (Organization > Blog > Category > Post)
- Cover image: full-width, 3:2 ratio, object-fit cover
- Author bio card: name, avatar, credentials
- Related posts section at bottom (3-col card grid)
- CTAs positioned: post-intro, mid-content, post-closing

### Custom Snippets (`snippets.xml`)
Registered in Website Builder sidebar:
- **Trust Badge** — certification/credential display block
- **CTA Section** — contextual call-to-action with headline, body, button
- **Blog Card** — reusable blog card for landing pages

## JavaScript Features (`theme.js`)

- **Reading progress indicator** — thin bar at top of blog posts tracking scroll depth
- **Smooth scroll to comments** — anchor navigation
- **Blog cover parallax** — subtle parallax on scroll (if resources permit)

## Sources & Research

| Source | What It Informed |
|--------|-----------------|
| **Windmill Strategy** — B2B industrial digital playbook | Card-based grids, trust signals, content hierarchy |
| **SRH Agency** — industrial website portfolio | Color palette psychology, industrial typography choices |
| **Grafit** — industrial branding guides | Layout density, utilitarian spacing |
| **ThunderClap** — B2B web design case studies | CTA placement patterns, reading column width research |
| **Odoo v17 Theme Docs** — odoo.com/documentation | SCSS bundle architecture, asset declaration, template inheritance |
| **Cybrosys Odoo Theme Guide** — cybrosys.com | Module structure, snippet registration, Odoo.sh deployment |
| **Odoo v17 SCSS Architecture Docs** | `web._assets_primary_variables` vs `web._assets_frontend_helpers` separation |
| **NotebookLM** — notebooklm.google.com/d09824d0-df50-43b5-8c40-6a986fbad067 | Consolidated research synthesis, competitive analysis |

## Module Structure Built

```
liber-odoo-customizations/
├── liber_website_theme/           # Website redesign module
│   ├── __manifest__.py
│   ├── static/src/scss/
│   │   ├── primary_variables.scss     # Odoo color palette + typography
│   │   ├── bootstrap_overridden.scss  # Bootstrap container/spacing overrides
│   │   ├── _blog.scss                 # Blog card grid, detail layout
│   │   ├── _typography.scss           # Font hierarchy, readability
│   │   ├── _components.scss           # Cards, buttons, navigation, trust badges
│   │   └── style.scss                 # Entry point
│   ├── static/src/js/theme.js         # Reading progress indicator
│   ├── views/
│   │   ├── blog_list_template.xml     # Card-based blog listing
│   │   ├── blog_post_template.xml     # Centered reading column + breadcrumbs
│   │   └── snippets.xml               # Custom drag-drop components
│   └── static/description/icon.png
├── liber_employee_dashboard/      # Performance dashboard module
│   ├── ... (dashboard model, views, security)
├── .gitignore
└── README.md
```

## Deployment Target

- **GitHub:** `github.com/dalebetz/liber-odoo-customizations`
- **Odoo.sh:** `liber.odoo.com` (project: liber)
- **Staging:** `staging--liber.odoo.com`
- **Branch:** `main` → Odoo.sh staging build
