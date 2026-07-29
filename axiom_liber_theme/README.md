# Liber Web Design Layer — `axiom_liber_theme`

Implements **Variant 003 (The Hybrid Builder)** from *Website Redesign Research —
Sources & Design Decisions (v1.1)* for the two Liber Holdings Odoo websites:

- **Tooling Components** — `www.toolingcomponent.com` (website id **3**)
- **RBC Industrial** — `www.rbc-industrial.com` (website id **4**)

Both are eCommerce + Blog sites in the **same** Odoo database, which is exactly why a
single module with per-website palettes is the right shape.

This is a **regular Website module**, *not* an Odoo "Theme". It **layers on top of** your
current sites — it does not replace or deactivate your existing theme. Installing and
uninstalling it is non-destructive to your current design.

---

## What it does

| Research item | Delivered by this module | How |
|---|---|---|
| Brand colour compliance (Section 7 — the biggest gap) | Two palettes, `tooling` + `rbc` | `primary_variables.scss` → pick per site in **Edit ▸ Theme ▸ Colors** |
| Brand fonts (Inter for Tooling; distinct headings for RBC) | Font configs in the picker | `primary_variables.scss` |
| Trust signals everywhere (Principle 4) | **Trust Badges** snippet | drag from **Add block** |
| Contextual CTAs, 3Ps (Section 8) | **Conversion CTA** snippet | drag from **Add block** |
| Spec tables (Section 9) | **Spec Table** snippet | drag from **Add block** |
| Cross-brand compatibility (Section 9, P0 competitive gap) | **Cross-Brand Compatibility** snippet | drag from **Add block** |
| Author E-E-A-T (Section 4) | **Author Bio** snippet | drag from **Add block** |
| Product rich results — Product/Offer/MPN (Section 9, P0) | schema.org Product JSON-LD on every shop product page | `product_jsonld.xml` + `models/product_template.py` |
| Breadcrumb rich results | schema.org BreadcrumbList JSON-LD on every page | `breadcrumb_jsonld.js` |
| Centred 720px reading column | `o_liber_reading` utility class | add the class to a post's content section |

Blog **card grid / cover / teaser / tags / author / sidebar** are native Odoo options —
turn them on per the functional guide; this module supplies the brand palette they inherit
plus the snippets to drop into posts.

---

## Install (Odoo.sh — staging first)

1. Commit the `axiom_liber_theme/` folder to a **staging branch** of your Odoo.sh repo
   (or upload the zip to a custom-addons path).
2. In Odoo: **Apps ▸ Update Apps List**, search *Liber Web Design Layer*, click **Install**.
   - It depends on `website`, `website_blog`, `website_sale` — all already installed on
     both sites, so it installs cleanly.
3. Verify on the staging URL (see checklist below), then **merge to production**.

> Installing on staging first is the whole point of Odoo.sh and removes all upgrade risk.
> If anything in the "Version compatibility" note below applies, you'll see it on staging,
> not in front of customers.

---

## Configure (functional — no code)

### 1. Set each site's brand colours (do this first)
1. Open the **exact hex codes** from the brand guides in the vault.
2. Edit `static/src/scss/primary_variables.scss` and replace the placeholder hex in the
   `tooling` and `rbc` palettes (5 colours each, plus the 2 CTA-button accents). This is
   the **only** file you touch to re-brand.
3. Redeploy. Then on each site: **Edit ▸ Theme ▸ Colors ▸ palette picker** → choose
   `tooling` on Tooling Components, `rbc` on RBC Industrial.

*(You can also just pick the palettes now with the placeholder colours to see it working,
then drop in the real hex later.)*

### 2. Set fonts
**Edit ▸ Theme ▸ Paragraph / Headings ▸ Font Family** → choose **Inter** (Tooling) and
your RBC heading font. Both are pre-loaded by this module.

### 3. Use the snippets
**Edit ▸ Add block** → the five snippets appear in the **Structure** group. Drag them onto
any page or blog post and edit the text inline. They automatically take the active site's
brand colours.

### 4. Reading column on articles
Open a blog post, select its content section, **Add class** `o_liber_reading` (or enable the
native **Increase Readability** option).

---

## Post-install verification checklist (run on staging)

- [ ] Both sites still render exactly as before (this module is additive).
- [ ] **Edit ▸ Theme ▸ Colors** shows `tooling` and `rbc` in the palette list.
- [ ] Selecting a palette recolours buttons/links to the brand colour.
- [ ] **Inter** (and the RBC heading font) appear in the font picker.
- [ ] **Add block ▸ Structure** shows the five Liber snippets with thumbnails.
- [ ] Each snippet drops in and its text is editable.
- [ ] Open any product page → **View source** → a `<script type="application/ld+json">`
      with `"@type":"Product"` is present. Paste the page URL into Google's Rich Results
      Test to confirm it validates.
- [ ] Open a blog post or shop category → **View source** → a `BreadcrumbList` JSON-LD
      block is present.

---

## Version compatibility

Built and validated against **Odoo 17.0**. The mechanisms used are stable across 17.0–19.0:

- **Palettes & fonts** (`$o-color-palettes` map-merge, `$o-theme-font-configs`,
  `_assets_primary_variables`) — identical API 15.0 → 19.0. No change needed.
- **Product JSON-LD** — inherits `website_sale.product` (a stable id) and appends with
  xpath `.` `position="inside"`, which is structure-agnostic. No change needed.
- **Breadcrumb JSON-LD** — reads the rendered DOM, so it is version-independent.
- **Component SCSS** — cosmetic only; harmless if a targeted class is absent.

**One thing to check if you are on Odoo 19.0:** the snippets panel (`website.snippets`)
was reorganised in 19.0. If, on a 19.0 staging build, the module errors on the
`snippets_register.xml` inheritance, or the five snippets don't show in **Add block**, the
fix is a one-line anchor change in `views/snippets_register.xml` (point the xpath at the
19.0 snippet-group container). Everything else in the module is unaffected. If you are on
17.0 or 18.0 (most likely — the research validated template ids against v17), no change is
needed.

To confirm your version: **Settings ▸ (scroll to bottom)** or the Odoo.sh branch build log.

---

## Uninstall

Apps ▸ *Liber Web Design Layer* ▸ Uninstall. Palettes, fonts, snippets and schema are
removed; your existing theme and content are untouched. Any snippet blocks you already
placed on pages will remain as static HTML.

---

*Authored by Axiom World for Liber Holdings. Companion to the Functional Implementation
Guide and the v1.1 research document.*
