# Globe Electric Supply Theme 17.0.1.0.0

Website for Globe Electric Supply Co Inc, built to the Axiom handoff of
9 October 2026 and to the standard of the RBC Industrial and Tooling Components
sites. Data only: installs through Apps > Import Module or the repository.

## Install order

1. liber_holdings_theme 17.0.1.49
2. rbc_industrial_theme 17.0.10.6.0
3. tooling_components_theme 17.0.8.6.0
4. globe_electric_theme 17.0.1.0.0

The first three were updated so that every "is this the Liber site?" check
recognises Globe as a sibling. Without that, the Liber header, footer and shop
logic would appear on the Globe site.

## What it builds on install

A company named like "Globe Electric" must exist (company id 7 on the live
database). The theme then finds or creates the Globe website, sets its flag,
builds the menu once (later builder edits are kept), creates 30 pages with a
" | Globe Electric Supply" title suffix, and writes robots.txt. It runs again on
every upgrade and from Website > Configuration > Globe: set up the website.

Then set, on the Globe website record: the domain (https://globelectric.com),
the Google Analytics key, and x_globe_gtm_id for Tag Manager.

## Test results

All four themes imported together through the frontend importer, Python
stripped, on a clean Odoo 17 database.

| Check | Result |
|---|---|
| Pages returning 200 | 30 of 30 |
| Exactly one H1 per page | 30 of 30 |
| Globe title suffix | 30 of 30 |
| Globe header and footer only, Liber layer off | 30 of 30 |
| Sitemap entries returning 200 and Globe content | 36 of 36 |
| "Veteran", "SDVOSB", "TX HUB", ISO certification | 0 anywhere |
| LeadConnector, "Tooling Components", the (814) number | 0 anywhere |
| DBE shown without implying federal-goal counting | yes |
| Quote form: lead in CRM under the Globe company | yes, with lane, spec, UTM and landing page in its notes, attachment kept |
| UTM fields visible to the visitor | 0 |
| UTM carried from landing page to the form | yes |
| GA4 generate_lead on /quote-received | fired once, lead_source and currency, no value field |
| Phone width (390 px) | Globe shown, nothing from Tooling, no sideways scroll |
| JSON-LD Organization and LocalBusiness, canonical, robots.txt | present |
| RBC, Tooling and Liber sites | unchanged, no Globe bleed |
| Render errors | 0 |

## Faults found and fixed during testing

* The Globe header and footer never rendered: the replacement landed inside
  RBC's branch. They now target the original elements and apply after RBC and
  Tooling.
* A menu method that does not exist in Odoo 17.
* The Liber footer, including "Veteran-Owned", appearing on Globe.
* Odoo's container clearfix taking the first cell of every grid.
* The quote button cut off on laptop widths.
* Liber's shared thank-you page indexed on every site (fixed in Liber 1.49).
* /brands and /contactus listed in Globe's sitemap from other sites: Globe now
  serves its manufacturers and contact pages at those addresses.
* Yellow text on light backgrounds, which fails contrast.

## Not done, and why

| Item | Reason |
|---|---|
| Built from the mockups and DESIGN.md | They are in the private repository; built from the handoff text |
| Tiles from tile_generator.py with INDUSTRIES['globe'] | That script is on the Hermes host; tiles are CSS in the brand |
| Manufacturer logos, photography | To be supplied |
| One page per manufacturer | Hub only in this version |
| /shop removed from the sitemap | Needs Python; robots.txt disallows it instead |
| UEI, CAGE, DUNS, Tax ID, NIGP, insurance, past performance | Not supplied; the page says "provided on request" rather than inventing them |
| Bulverde street address | Not supplied; shown as Bulverde, Texas |
| GSC redirect list | Needs Search Console access |

After deploying, delete the cached sitemap (it is kept up to 12 hours) or wait
for it to expire, and clear the website cache.

## 17.0.1.1.0 — second pass against the handoff

A line-by-line review of the handoff against 17.0.1.0.0 found these missing.
All are now built and tested.

| Handoff | Added |
|---|---|
| §5.4 Hub plus one page per brand | 12 manufacturer pages at /manufacturers/<brand>, each linked from the logo wall and pointing to its line-card families |
| §5.7 Knowledge base, 3 seed articles | A Globe Knowledge Base blog bound to the Globe website, with three seed articles in Globe's lanes (traffic signal LED modules, rail switch heaters, discontinued airfield lighting), **left unpublished** for Dale to review |
| §5.8 Ownership | About states Globe is a member of the Liber Holdings family, operating as its own company. No SDVOSB claim |
| §5.10 Map | Embedded map on Contact |
| §6 Globe favicon | Generated Globe favicon (yellow G on graphite), set only if none is uploaded |
| §7 /linecard/govt.html | 301 to /government |
| §7 BreadcrumbList on inner pages | Valid BreadcrumbList JSON-LD on every inner page |
| §8 step 2 brand tokens in the palette | Globe colours set in Odoo's own colour palette for this website, so blocks added in the builder stay on brand |
| §5.9 GTM | Tag Manager noscript fallback added beside the script |
| Meta | A meta description on every indexed page, taken from each page's own introduction |
| Terms | Moved to /terms-of-use: Odoo Accounting owns the /terms route, which was hiding the page |

Retested on the same four-theme database, imported through the frontend:
44 pages, all 200, one H1 each, Globe title, Globe header and footer, valid
breadcrumbs; meta descriptions on every indexed page; 50 sitemap URLs including
the 12 manufacturer pages; no excluded certification wording; no render errors.

## 17.0.2.0.0 — rebuilt to Dale's design files

Built against `design-tokens/globe-electric.DESIGN.md` and the three mockups in
`mockups/globe-electric/full-site/`, compared side by side with the mockups
rendered in the same browser at the same width.

| Area | Now |
|---|---|
| Header | Voltage Yellow bolt mark and "Globe Electric Supply Co." wordmark, the mockup's six menu items, phone in Voltage Yellow, 4px top rule. The menu is rebuilt once to these items on upgrade, then left alone |
| Homepage | Every section and every line of copy from index.html: hero with the yellow second line and note, dark stat band, four numbered pillars, six white solution tiles with image bands, the obsolete spotlight with its panel, the government band with white CERT — AGENCY badges, firmographics and NAICS table, the six-column manufacturer wall, knowledge cards, the Houston and Bulverde locations |
| Government | Every section of government.html: the four-column certification table with program and status, the DBE callout in Dale's wording, the Not claimed statement, identifiers (DUNS, UEI, CAGE, Tax ID, B2G), insurance and registration, six NAICS and four NIGP codes, agencies and commercial references |
| Quote | quote.html's layout: two-column fields, phone required, Dale's six lanes, the file field, hidden attribution including lead_source, and the three side panels |
| Footer | Company, Solutions and Contact columns, with DUNS, CAGE and UEI on every page |
| Typography | Oswald for H1 and H2 only; H3 and everything else Inter, as DESIGN.md specifies |
| About | Founded 1972, incorporated as Globe Electric Supply Co Inc in 1980, per DESIGN.md |
| Knowledge | The three seed articles are now Dale's three topics, tagged Cross-Reference, Obsolescence and Public Sector, still unpublished. The homepage shows Dale's three cards until articles are published, then the latest three |
| Favicon | The bolt mark |

### One conflict in Dale's files, resolved conservatively

The homepage and government mockups show **TX HUB as pending**. The handoff's
certification gate (§3) says TX HUB must **not** be rendered until it is issued,
and the acceptance criteria repeat that. The gate is followed: TX HUB appears
nowhere. Tick **Globe: Texas HUB certification issued** on the website the day
it is issued, and it appears as a verified row on Government and as a badge on
the homepage, with no deployment.

The **Not claimed** statement names SDVOSB, ISO and SCTRCA, as Dale wrote it in
government.html. It states they are not held; no certification badge for any of
them exists anywhere.

### Two deliberate departures from the mockups

* The mockup tiles carry a "Tile — …" placeholder label, and quote.html carries a
  grey developer note about hidden fields under the button. Both are notes for
  the builder, not content, so neither is shown to visitors.
* Quote's eyebrow reads "Same-Day Quotes" rather than the mockup's internal label
  "Primary Conversion".

### Verified

All four themes imported through the frontend, Python stripped:

| Check | Result |
|---|---|
| Pages: 200, one H1, Globe title, Globe header and footer, meta description, breadcrumbs | 44 of 44 each |
| Sitemap | 51 URLs, all 200 |
| TX HUB | 0 |
| Veteran, LeadConnector, Pennsylvania number | 0 |
| Government firmographics, codes and references | all present |
| Browser submission of the quote form | redirected to /quote-received; lead in CRM under Globe with lane, spec, UTM, lead_source, landing page and the attached BOM |
| GA4 generate_lead | fired once, no value field |
| Phone width | menu opens and closes, no sideways scroll |
| RBC, Tooling, Liber | unchanged, no bleed |
| Render errors | 0 |

## 17.0.2.1.0 — blog, printing, depth and links

| Reported | Fixed |
|---|---|
| Blog not like RBC and Tooling | Same base: Knowledge Base heading, list and card views, a "Technical brief" cover when a post has no picture, tags, dates, and the whole row clickable. Only Globe's own articles are listed; Odoo's blog switcher (which listed other sites' blogs) is hidden, search is kept |
| Not printable as a report | Compact post header with breadcrumbs and a Print / Save as PDF button. On paper: a Globe report header (bolt, wordmark, contact line, yellow rule), title block, the article on white, tables that flow across pages, headings kept with their text, and a footer line with address, DUNS and CAGE. Web chrome, sharing and "read next" do not print |
| "Everything I open shows the same thing" | The inner pages averaged 50–80 words and shared the same shell; manufacturer pages were 53% identical. All 37 inner pages are rebuilt with their own content: what we supply, what to send us, where it is used, related lanes and manufacturers. Pages are 2–3 times longer and repetition is down to 19–35%, mostly the shared header and footer |
| No Home at the top | Home is the first menu item (rebuilt once on upgrade) |
| Every term and link workable | Homepage badges, stat figures, pillars, spotlight points, NAICS rows and locations are links. Government: every certification and identifier links to a plain definition (MBE, SBE, WBE, DBE, NAICS, NIGP, DUNS, UEI, CAGE, B2G), agency names link to the agencies, SAM.gov links to SAM |
| Header | Seven items, wordmark and phone on one line at every width from 1024 to 1600 px |

Also found and fixed in testing: the Globe post header did not apply because RBC
and Tooling replace the same element first; it now targets the original. The
editor palette's light-background slot made blog pages grey; it is now Chalk.

Verified on the four-theme test database: 68 internal links and every in-page
anchor resolve; 22 external links; a click anywhere on an article row opens that
article; the printed PDF carries the Globe report header and footer.

**Note:** the three seed articles remain unpublished on install. They were
published in the test database only, to exercise the blog and printing.

## 17.0.2.2.0 - Dale, 14 Oct 2026 meeting

| Item | Change |
|---|---|
| "Built for buyers who de-risk on evidence" | Now "What you can expect from Globe" |
| "Lanes" | "The industries we supply", "View industry", "Product lines and industries", "Industries that use ..."; quote field "Product lane" is now "Industry" |
| View-only catalog ("like the Liber Holding") | Catalog menu item; products browsable; no add to cart, quantity, buy-now, price or shop boilerplate; Request a Quote on cards and product pages, pre-filling the product on /quote |
| Not indexed | `noindex, nofollow` on every catalog and product page; /shop left out of the sitemap (needs liber_holdings_theme 17.0.1.50); robots.txt no longer blocks /shop, so crawlers can see the noindex |
| JS error on every page | Odoo's auto-hide-menu script needs a `.top_menu` in the header; a hidden empty one is added |

Requires liber_holdings_theme 17.0.1.50. After deploying, delete the cached sitemap once (Odoo keeps it up to 12 hours).

## 17.0.2.3.0 - catalog like RBC / TC; Dale, 16 Oct 2026 meeting

| Item | Change |
|---|---|
| Catalog | Ported from the RBC / TC catalog, view-only: filter panel (categories + attribute filters showing only values in use, closed by default, value search), active-filter chips, dense table (Part No, Category, Specs, Description, Request Quote) and cards, row / card click opens the product, Globe styling; no price, stock or cart; Odoo's crowded category strip hidden |
| Resources page | Empty image areas on the six tiles replaced by compact icon headers |
