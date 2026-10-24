# liber_holdings_theme 17.0.1.50 - brands page and company facts, rev 4 (Dale, 2026-10-15)

Source: `handoff/liber-group-brands/04-consolidated-corrections.md` (PR #10). Applied to the module source
**and** to the live views of Liber Holdings (site 1) and Liber Industrial (site 7) by the server action in
`data/content_corrections.xml` on every install / upgrade. It is a server action (not Python), so it also runs
when the module is installed through Apps > Import Module. Idempotent;
never touches Tooling Components, RBC Industrial or Globe Electric views.

| Area | Change |
|---|---|
| Liber Holdings hero | `Est. 2016 • Veteran-Owned Enterprise`; H1 `Industrial Distribution & Precision Component Sourcing`; "operating heritage since 1946" |
| Liber Industrial hero (same shared view, per-site) | `Est. 2018 • Liber Holdings Group`; H1 `Liber Industrial company overview`; Bulverde MRO / specialty-chemical copy |
| Metrics | LH `2016 / Established / Heritage Since 1946`; LI `2018 / Established`; veteran metric attributed `CVE-certified SDVOSB · Liber Holdings LLC` |
| Certification line | `Veteran-Owned · Service-Disabled Veteran-Owned (CVE Certified) · TX HUB · SAM Registered` / `Liber Holdings LLC · UEI UAM8RE2L11U8 · CAGE 24H34 · verify in SBA VetCert` |
| RBC card (both homepages) | `RBC Industrial • El Paso, TX`; `Established 1946`; `Timken, SKF, Sealmaster, Browning` |
| Email | LH `AP@liberholding.com` (homepage, contact cards); LI keeps `sales@liberindustrial.com` |
| Footer | per-site brand, badge and line; "heritage since 1946"; no "manufacturing" |
| About + timeline | 2016 formation / Aug 2016 acquisition of RBC (founded 1946); RBC founding node year 1987 -> 1946; Liber Industrial node: Bulverde + closed school line as history |
| Brands grid | Dodge (ABB) and Baldor-Reliance removed; Sealmaster `Mounted Bearings`; Rexnord `Mounted Bearings & Couplings`; added `Diamond Chain (Timken)` and `Leeson · Marathon · Techtop` |
| Vocabulary | "manufacturer/manufacturing" removed from Liber copy and meta |

Kept on purpose (corrections section 3): founder names `Roger Brown, Sr./Jr.`; the historical acquisition
sentence ("... Roger Brown Co ... which was founded in 1946"); the 2025 rebrand note; structured-data alternate names.

**Dale's exact 12-card block** (`01-brands-section.html`, PR #10, private) is not yet included: the grid holds the
8 cards the corrections confirm. Once the file is supplied it goes into the action as a drop-in replacement.

## Globe Electric recognised as a sibling site (Dale, 14 Oct 2026 meeting)

The uploaded 1.49 did not know the Globe flag, so Liber's styling, product call-to-action and `/quote`,
`/quote-received` and `/brands` controllers answered on the Globe website.

| Change | Effect |
|---|---|
| `x_globe_theme_active` added to both sibling lists and to all 14 template checks | Liber styling and catalog logic stay off the Globe site |
| `/quote`, `/quote-received`, `/brands`: a sibling site that has its own page keeps it | Globe's quote form, thank-you page (GA4 `generate_lead`) and manufacturers page are served |
| Sitemap: `/shop` left out for the Globe site too | Globe's view-only catalog is not listed (it also carries `noindex`) |

## 17.0.1.51 - Dale, 16 Oct 2026 meeting

| Item | Change |
|---|---|
| Liber Industrial badge and metric | "Liber Holdings Group" removed: `Est. 2018 • SDVOSB · Service-Disabled Veteran-Owned Small Business`; metric `SDVOSB · CVE Certified` (attributed to Liber Holdings LLC in the certification line) |
| "Regionally" | "Distributed nationwide via ..." on the brands page |
| Liber Industrial contact page | Leads with Liber Industrial's own details (Bulverde, (832) 764-7979, sales@liberindustrial.com) |
| Import Module | All live corrections run as a server action, so they apply when the module is imported |

## 17.0.1.52 - Dale's 01-brands-section.html (rev 3 grid, unchanged in rev 4)

The whole "Bearings, Seals & Power Transmission" group is replaced on both /brands pages (Liber Holdings and
Liber Industrial) and in the module template by Dale's block: 12 cards in promotion order - SKF, Timken,
Sealmaster, Rexnord, Browning, ContiTech · Bando, Martin Sprocket, Diamond Chain (Timken), Grove Gear,
SEW-Eurodrive · Nord, Leeson · Marathon · Techtop, McGill. No Dodge, no Baldor.

Applied on top of the file, per rev 4 and the 16 Oct meeting: "Distributed nationwide via RBC Industrial"
(the file said "regionally" and "RBC Industrial (Roger Brown Co.)"). `&middot;` written as "·" because the
HTML entity is not valid in an Odoo view. Idempotent; other websites untouched.

## 17.0.1.53 - footer overlap and /quote 404

| Issue | Fix |
|---|---|
| Footer badge ran into the "Operating Subsidiaries" column (both sites) | The badge wraps inside its column |
| Liber Industrial footer showed the El Paso HQ address and phone | Liber Industrial: 30131 Bulverde Ln, #370, Bulverde, TX 78163 - +1 (832) 764-7979 |
| liberindustrial.com/quote returned 404 when the module is imported (Import Module never loads the Python route) | /quote and /quote-received are created as pages on both Liber sites from the module's quote templates; a repository deploy keeps using the route |

## 17.0.1.54 - quote page hardened (product lookup sudo-safe, numeric ids only)
## 17.0.1.55 - "Liber: diagnose /quote" server action (Settings > Technical > Server Actions > Run): lists every
/quote page and quote template per website and how the module is installed, so a stale copy on a live database
can be identified. Changes nothing.

## 17.0.1.56 - Dale's emails (17 / 24 / 28 Sep, Search Console findings)

| Item | Change |
|---|---|
| /sitemap.xml 500 on all four sites | Backstop: a route in another module overridden without @http.route() is skipped instead of crashing the whole sitemap (Python - repository deploy). The root cause still has to be fixed in that module: search the Odoo.sh log for "not decorated by @route" |
| /shop/wishlist indexed | noindex on every site (template) |
| Product links carried ?category= / ?page= (about 522 URL variants per product per language) | Every product card links to the clean product URL on every site (template) |
| Shop / category <title> "Industrial Spare Parts Shop" on sites 2 and 3 | Edited per-website copies of products_shop_meta still holding the hard-coded title are reset to the module version (server action) |

## 17.0.1.57 - Liber Holdings / Liber Industrial shop like RBC / Tooling Components (view-only)

| Item | Change |
|---|---|
| Catalog | Same design as RBC / TC in Liber colours: filter panel (categories + attribute filters showing only values in use, value search), active-filter chips, table and card views, row / card click opens the product, "Don't see your part number?" band. No add to cart; Request Quote on every product |
| Product page | Category chip and part number, variant-aware spec table (switches with the selected variant), Variant Sales Description, long description below the call to action, Sourcing & Equivalents box; Liber's Request a Quote box stays; no buy buttons |
| Liber Holdings /shop | Catalog shown again (the 301 to RBC / TC is switched off); still noindex and out of the sitemap so it does not compete with the subsidiaries |
| Menu | "Shop" added to the top menu of both Liber sites (server action, once per site) |
| Product JSON-LD | Built in the template instead of a Python method, so product pages no longer fail when only the XML is loaded |
| Duplicate H1 | The older "Technical Reference Catalog" header block is switched off on the Liber sites |

Deploy: push to the repository AND import the same zip (Apps > Import Module) - the RBC / TC themes call
Liber's Python methods on every product page, and the imported copy carries the templates and CSS / JS.
