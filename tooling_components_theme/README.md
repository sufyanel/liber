# Tooling Components Website Theme (17.0.2.1.0, import-safe)

Install from Apps > Import Module (no Python). Scoped to the website named **Tooling Components**
(flag: Website > Configuration > Websites > Tooling Components > "Tooling Components Theme").
Nothing renders on other websites.

## Dale's requests implemented (meetings 24 Jul, 21 Aug, 11 Sep, 18 Sep 2026)
| Request | Implementation |
|---|---|
| Catalog: Part No = product name (no internal ref), Description = sales description, Category, Spec = top 4 attributes | Dense table (list layout default) + compact cards (grid) |
| Add to Cart (prices listed); RFQ only for custom / no-price | RFQ when tagged "Request Quote", no price, or not sellable |
| Guest checkout | Login only required on Liber Holdings website (liber_holdings_theme controller) |
| Compact filters, smaller blocks/fonts, exact brand colours | Filter card, dense CSS, palette via ir.asset |
| Blog: list view, no grey cover band, no author bar | Knowledge Base list (default) / cards (?view=cards); compact post header; Read Next band off |
| Contact: clean 1-2 columns | Methods + quote form, two columns |
| Logo instead of text | Website record > TC Header Logo |
| Line card download | Website record > TC Line Card URL (footer link hidden while empty) |
| Product page: image, short desc, price, long desc (description_ecommerce), attributes | Reordered + spec table + Product JSON-LD |
| Local SEO (Union City) | LocalBusiness JSON-LD |

## Quote / contact form
Odoo website form -> CRM lead. Part number and urgency are stored under "Other Information".
Can be replaced by a GoHighLevel embed later.

## Guest checkout
Needs the patched `liber_holdings_theme` (Python controller) deployed through the repository:
an imported module cannot change the login-only routes of the Liber theme.

## Pages (TC website only)
`/`, `/about-us`, `/contactus`, `/quote` - each a website-specific page wrapping a module template.

## 17.0.8.2.0 — requested by Dale on 7 October 2026

Two changes only. Nothing else in the theme was touched.

### 1. Tiles are a consistent size

A long label such as "Press Die Components" made its tile taller than the
others in the row. Labels now hold two lines and every tile in a row shares one
height, on the category tiles and on the solution tiles.

Style only: no markup, no data, no behaviour changed. The rules are appended at
the end of theme.css and scoped to `html[data-tc-theme="1"]`, so the sibling
sites are unaffected.

### 2. The SEO Description can be hidden on product pages

Dale is migrating brand specific text out of the SEO Description and into the
variant field, because text mentioning Raymond was showing on Bordignon
variants. The description had to stay visible until that migration finished, so
hiding it is a switch rather than a deletion:

**Website → Configuration → Settings → Hide SEO Description on product pages**

Off, which is the default, keeps today's behaviour exactly. On, the product page
stops falling back to the SEO Description and shows only the eCommerce
description and the variant text. Flip it the day Dale confirms the migration is
complete; no deployment needed.

### Verified on a clean Odoo 17 database

All three themes installed together: liber_holdings_theme 17.0.1.34,
rbc_industrial_theme 17.0.10.2.0, tooling_components_theme 17.0.8.2.0.

| Check | Result |
|---|---|
| All three install with no errors | yes |
| Product page, catalog, homepage, Contact Us | 200 |
| Theme flag present on its own site | yes |
| Compile or render errors in the log | none |
| Switch present on the website record | yes, default off |

## 17.0.8.3.0 — header alignment across languages

The English and Spanish headers did not line up. The cause was a rule in this
theme's own stylesheet that hid the certification badges whenever the page
language began with "es", presumably because the longer Spanish wording pushed
the row out of shape.

Hiding them meant the two languages had different headers. The badges now
appear in both, and the row gives back the space instead:

* the badges stay visible in Spanish
* in Spanish they are slightly smaller and sit closer together
* the Request a Quote button is a little tighter and never wraps
* the menu may shrink, the badges and the button may not
* both languages drop the badges at the same width, 1400 pixels, rather than at
  different points

Style only, appended at the end of theme.css and scoped to this theme. Verified
in the served stylesheet: the new rule comes after the old one in the cascade,
so it wins, and the shared breakpoint is present.

## 17.0.8.4.0 — blog printing fixed

Found by printing a real long article (text, a 40-row table, a checklist) to PDF
exactly as the Print / Save as PDF button does, then reading every page.

| Fault | Fix |
|---|---|
| The brand header printed twice on page 1 | The fallback copy is dropped whenever the real post header is present |
| A grey panel printed behind the whole article | The article prints on white paper |
| A table jumped to a new page, leaving the page before it half empty, then sprawled over four pages with cells so padded that "Value 1-1" broke across two lines | Tables flow on from the text, rows stay whole, cells are compact and on one line, and a header row repeats on each page when the table has one |
| A heading could sit alone at the foot of a page | Kept with the text that follows |

Result on the same article: 7 pages before, 5 after, verified on both RBC
Industrial and Tooling Components.

Print rules only, appended last so they take precedence. Nothing on screen changes.

## 17.0.8.5.0 — Dale's 7 and 9 October 2026 meetings

| Request | What changed |
|---|---|
| Stop using the SEO Description ("we're not using SEO anymore") | The product page no longer falls back to the SEO Description, and the "Hide SEO Description" website switch is removed. The field is hidden on product forms and lists; it stays visible in developer mode, and in Export, so its text can still be moved. Its data is not touched. |
| Variant Sales Description must not override the Sales Description | The Sales Description always stays visible. The selected variant's text shows under it and changes with the selection. |
| Brand text for every product, including single-variant ones (8312, XH012) | Variant text now shows for products with one variant too (before: 2 to 60 only). The default variant's text is rendered in the page, so search engines index it. Line breaks are kept. |
| Brand on the delivery ticket | The delivery slip prints a "Brand: ..." line plus the Variant Sales Description, on ready, done, backorder and serial/lot layouts. Odoo leaves the brand out of the product name when a product has only one brand, as on XH012. |
| Brand on every document | Quotation / sales order and invoice print "Brand: ..." when the line text does not already show it. |
| GA4 lead tracking on /quote-received ("lines 82 to 86") | A generate_lead event with currency USD and no value: value 0 recorded every lead as $0. The lead value comes from GA4 > Admin > Key events > generate_lead > Set default value. Hardcoded, so updates keep it. Counted once per visit. |

Records for the variant field, forms and documents are keyed (liber_variant_docs.*) and identical in
rbc_industrial_theme and tooling_components_theme, so importing both is harmless.
Tested on Odoo 17 by upgrading from 17.0.8.4.0 together with the other two themes.

### .5.1 — import fix
The .5.0 import stopped with "cannot be located in parent view": on the live database the delivery slip
is customised, so the standard anchor for the brand line did not exist. Every view this theme adds is now
tried against several anchors inside a savepoint; a report or form that matches none of them is skipped and
never blocks the import. Result per document: Settings > Technical > System Parameters >
liber_variant_docs.report. Tested by importing through Apps > Import Module onto a database with a
customised delivery slip, and onto a standard one.

### .5.2 — SEO Description removed from product screens
The SEO Description is no longer shown on any product form or list, developer mode included, to avoid a third, inconsistent description. Its stored text is not deleted (still available in Export).
