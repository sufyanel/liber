# liber_holdings_theme 17.0.1.49 — Liber Holdings is a view-only site (Dale, 9 October 2026)

Dale: "I don't need the products to be shown at all ... I don't want it to compete with the other companies for rankings."

| Change | Detail |
|---|---|
| Catalog URLs redirect (301) | /shop and category pages go to the Family of Companies section. A product page goes to the same product on RBC Industrial or Tooling Components when it belongs to that site (by website, public category website, or company); otherwise to Family of Companies. Its ranking passes to the subsidiary. |
| Out of sitemap.xml | No /shop URL in the Liber Holdings sitemap. RBC and TC sitemaps unchanged. |
| No product search | Header search removed on Liber Holdings. /website/search and any /shop page carry noindex, nofollow. |
| Menus | Catalog entries removed from the Liber Holdings menu on every upgrade. Sibling menus untouched. |
| Home page | The catalog band is replaced by "Order Through Our Operating Companies" (RBC Industrial, Tooling Components, Contact). |
| Quote received | On Liber Holdings the "Browse Parts Catalog" button becomes "Our Operating Companies". |
| Cart / checkout | Redirect to /quote for everyone on Liber Holdings, signed in or not. |

Liber Holdings is identified as a website whose name contains "Liber", not "Industrial", and that no sibling theme
claims, so a future Liber Industrial website is not affected. Python changes (controllers/main.py,
models/ir_http.py, models/website.py): deploy through the repository.
