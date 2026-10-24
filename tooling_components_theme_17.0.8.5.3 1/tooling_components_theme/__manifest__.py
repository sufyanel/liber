{
    "name": "Tooling Components Website Theme",
    "summary": "Forged & Molded design for the Tooling Components website (import-safe)",
    "description": """
Tooling Components website design (Mission Critical Industrial brand): emergency
line-down bar, SDVOSB / Texas HUB badges, engineer-dense product catalog
(part number, description, category, top-4 specs, price, stock), compact
filters, spec-sheet product page with JSON-LD, compact Knowledge Base, contact /
quote forms creating CRM leads. Data-only: installable from Apps > Import Module.
Everything is scoped to the Tooling Components website only.
    """,
    "category": "Website/Website",
    "license": "LGPL-3",
    "version": "17.0.8.5.3",
    "author": "Axiom World",
    "website": "https://www.tc-industrial.com",
    "depends": [
        "website",
        "website_blog",
        "website_sale",
        "website_sale_stock",
        "website_crm",
        "liber_holdings_theme",
    ],
    "data": [
        "data/fields.xml",
        "views/layout.xml",
        "views/pages.xml",
        "views/shop.xml",
        "views/product.xml",
        "views/blog.xml",
        "views/website_form.xml",
        "views/liber_scope.xml",
        "views/ga4_lead.xml",
        "data/website_data.xml",
        "data/translations_es_mx.xml",
        "data/variant_documents.xml",
        "data/claims_fix.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "tooling_components_theme/static/src/js/product_translate_es.js",
        ],
        "web.assets_frontend": [
            "tooling_components_theme/static/src/css/theme.css",
            "tooling_components_theme/static/src/js/catalog.js",
            "tooling_components_theme/static/src/js/notification_compat.js",
        ],
    },
    "installable": True,
    "application": False,
}
