# -*- coding: utf-8 -*-
{
    "name": "Liber Holdings Website Theme",
    "summary": "Enterprise Corporate Theme & RFQ Technical Catalog for Liber Holdings Group",
    "description": """
        Custom enterprise website theme for Liber Holdings group:
        - View-only corporate site: no catalog, product pages or product search; catalog URLs redirect (301) to the subsidiary and stay out of sitemap.xml
        - Centralized Request for Quote (RFQ) workflow connected to CRM lead generation
        - Dedicated /quote-received confirmation page and error-free form redirection
        - Showcase for Family of Operating Companies (RBC Industrial, Tooling Components, Globe Electric Supply)
        - Dedicated 'Brands We Represent' portfolio page
        - Company History and Vendor Credibility hub (Est. 2016, heritage since 1946)
        - Clean blog UI with suppressed duplicate title headers and hidden author metadata
        - Full compatibility with sibling themes (RBC Industrial and Tooling Components)
        - Scoped Liber Holdings visual identity (Liber Red #B8322A / Charcoal #1A1C1E)
    """,
    "category": "Theme/Ecommerce",
    "license": "LGPL-3",
    "version": "17.0.1.61",
    "author": "Axiom World",
    "website": "https://www.liberholdings.com",
    "depends": [
        "website",
        "website_blog",
        "website_sale",
        "website_crm",
    ],
    "data": [
        "data/product_tag_data.xml",
        "data/website_data.xml",
        "data/menu_order.xml",
        "data/product_zoom.xml",
        "views/templates_header.xml",
        "views/templates_footer.xml",
        "views/templates_homepage.xml",
        "views/templates_brands.xml",
        "views/templates_shop.xml",
        "views/templates_product.xml",
        "views/templates_quote.xml",
        "views/templates_blog.xml",
        "views/templates_seo.xml",
        "views/templates_catalog.xml",
        "data/about_timeline.xml",
        "data/company_links.xml",
        "data/assets_rebuild.xml",
        "data/content_corrections.xml",
        "data/diagnose_quote.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "liber_holdings_theme/static/src/css/theme.css",
            "liber_holdings_theme/static/src/css/catalog.css",
            "liber_holdings_theme/static/src/js/theme.js",
        ],
    },
    "images": [
        "home.png",
        "shop.png",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
}
